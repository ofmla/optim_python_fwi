# inversion_script.py
import argparse
import importlib
import yaml
from yaml import SafeDumper
from generate_shot_data import model_to_dict

# Ensure SafeDumper handles None values properly
SafeDumper.add_representer(
    type(None),
    lambda dumper, value: dumper.represent_scalar(u'tag:yaml.org,2002:null', '')
)

def inversion_setup(yaml_file, fpeak):
    '''
    Read the config.yaml file, and update it as needed. We took advantage
    of the already defined cluster configuration in the file.
    '''
    directory = './marmousi2/shots/'
    with open(yaml_file, 'r') as infile:
        data = yaml.full_load(infile)

        data['forward'] = False
        cfg = model_to_dict('marmousi2')

        data['fwi'] = True
        data['vmin'] = 1.377
        data['vmax'] = 4.688
        data['mute_depth'] = 47
        # solver parameters
        cfg['solver_params']['f0'] = fpeak
        cfg['solver_params']['shotfile_path'] = f"{directory}{int(fpeak*1e3)}Hz/"
        data['solver_params'] = cfg['solver_params']
        data['solver_params']['parfile_path'] = "./marmousi2/parameters_hdf5/"

    with open(yaml_file, 'w') as outfile:
        yaml.safe_dump(data, outfile, default_flow_style=None)

def main():
    parser = argparse.ArgumentParser(description="Run control inversion.")
    parser.add_argument(
        'module', 
        choices=['shot_control_inversion_sotb',
                 'shot_control_inversion_nlopt',
                 'shot_control_inversion_scipy'], 
        help='The module to import the ControlInversion class from.'
    )
    parser.add_argument('fpeak', type=float, help='dominant frequency in Hz')
    args = parser.parse_args()
    
    inversion_setup("./config/config.yaml", args.fpeak/1e3)
    
    # Dynamically import the module and the ControlInversion class
    module_name = args.module
    module = importlib.import_module(module_name)
    ControlInversion = getattr(module, 'ControlInversion')
    
    control_inv = ControlInversion()
    control_inv.run_inversion()

if __name__ == "__main__":
    main()

