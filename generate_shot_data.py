import os
import errno
import yaml
import argparse

from forward_script import main
from pathlib import Path
import numpy as np

def model_to_dict(argument):
    '''
    Get forward modeling configurations of the model. Model name
    is looked up against the switcher dictionary mapping.
    '''
    switcher = {
        'marmousi2': {'src_depth': 40.0, 'rec_depth': 80.0,
                      'nrecs': 426, 'nshots': 16, 'model_size': 17000.0,
                      'solver_params': {
                          'shotfile_path': './marmousi2/shots/',
                          'parfile_path': './marmousi2/parameters_hdf5/',
                          't0': 0.0, 'tn': 5000.0,
                          'dt': 4.0, 'f0': 0.004, 'model_name': 'marmousi2',
                          'nbl': 50, 'space_order': 8, 'dtype': 'float32'}},
    }

    return switcher.get(argument)


def forward_setup(yaml_file, model_name):
    '''
    Read the config.yaml file, and update it as needed. We took advantage
    of the already defined cluster configuration in the file.
    '''
    current_dir = Path.cwd()
    with open(yaml_file, 'r') as infile:
        data = yaml.full_load(infile)
        data['forward'] = True
        data['fwi'] = False
        cfg = model_to_dict(model_name)
        # geometry
        src_depth = data['src_depth'] = cfg['src_depth']
        rec_depth = data['rec_depth'] = cfg['rec_depth']
        nrecs = data['nrecs'] = cfg['nrecs']
        nshots = data['nshots'] = cfg['nshots']
        model_size = data['model_size'] = cfg['model_size']

        # solver parameters
        data['solver_params'] = cfg['solver_params']

    print("Solver parameters are being substituted with the following new values:")
    for key, value in data.get("solver_params").items():
        print(f"Key: {key:<14} Value: {value}")

    with open(yaml_file, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=None)


def make_sure_path_exists(path):
    '''Create a folder within a given path.'''
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('model', type=str, help='Name of the model')
    args = parser.parse_args()

    if args.model != 'marmousi2':
        raise ValueError("Model name must be 'marmousi2'.")

    make_sure_path_exists(f"./{args.model}/shots")
    forward_setup("./config/config.yaml", args.model)
    main()
