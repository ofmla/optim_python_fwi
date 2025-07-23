"""FWI example."""
import numpy as np
import os
import h5py
import json

from pyrol import getCout, Objective, Problem, Solver, Bounds
from pyrol.pyrol.Teuchos import ParameterList
from pyrol.vectors import NumPyVector

from dask_cluster import DaskCluster
import cloudpickle as pickle
from utils import expand_array, save_model
from inversion_script import inversion_setup


def elementwise_sum(arrays):
    """
    Perform element-wise addition of NumPy arrays in a list.

    Args:
        arrays (list of np.ndarray): List of NumPy arrays to be summed.

    Returns:
        np.ndarray: Element-wise sum of the arrays.
    """
    # Perform element-wise addition using np.add.reduce
    result = np.add.reduce(arrays, axis=0)
    return result

class Objective(Objective):
    def __init__(self, metadata):
        self.dc = DaskCluster()
        self.dc.config_values['solver_params']['origin'] = (*metadata['origin'],)
        self.dc.config_values['solver_params']['spacing'] = (*metadata['spacing'],)
        self.dc.config_values['solver_params']['shape'] = (*metadata['shape'],)
        self.par = self.dc.bcast_data()
        self.bl = self.dc.create_break_list()

        super().__init__()

    def value(self, x, tol):
        """Compute the functional"""
        model = DaskCluster.get_model(self.dc.config_values['solver_params'])
        shape = self.dc.config_values['solver_params']['shape']
        nbl = self.dc.config_values['solver_params']['nbl']
        large_x = expand_array(np.reshape(x.array, shape), nbl)
        model.update('vp', 1.0/np.sqrt(large_x))
        with open('model0.p', 'wb') as file:
            pickle.dump({'model': model}, file)
        misfits = self.dc.client.map(DaskCluster.gen_shot_in_worker_rol,
                                     self.bl,
                                     solver_params=self.par,
                                     resources={'process': 1})
        total = self.dc.client.submit(sum, misfits)
        return total.result()

    def gradient(self, g, x, tol):
        """Compute the gradient of the functional"""
        model = DaskCluster.get_model(self.dc.config_values['solver_params'])
        shape = self.dc.config_values['solver_params']['shape']
        nbl = self.dc.config_values['solver_params']['nbl']
        large_x = expand_array(np.reshape(x.array, shape), nbl)
        model.update('vp', 1.0/np.sqrt(large_x))
        with open('model0.p', 'wb') as file:
            pickle.dump({'model': model}, file)
        gs = self.dc.client.map(DaskCluster.grad_fwi_in_worker,
                                self.bl,
                                solver_params=self.par,
                                return_tuple=False,
                                resources={'process': 1})
        gradient = self.dc.client.submit(elementwise_sum, gs)
        gsum = gradient.result()
        mute_depth = self.dc.config_values['mute_depth']
        if mute_depth is not None:
            gsum[:, 0:mute_depth] = 0.
        g[:] = gsum.flatten().astype(np.float32)
        return 


def main():
    """
    A basic FWI implementation. It uses the ROL package for the optimization.
    """
    # Read initial guess and metadata from hdf5 file
    with h5py.File('./marmousi2/parameters_hdf5/vp_start.h5', 'r') as f:
        v0 = f['vp_start'][()]
        metadata = json.loads(f['metadata'][()])

    shape = (*metadata['shape'],)

    # Check whether the specified path exists or not
    results_path = './marmousi2/results/'
    isExist = os.path.exists(results_path)
    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(results_path)

    # Initial guess
    x = NumPyVector(np.array(1.0 / (v0.reshape(-1).astype(np.float32)) ** 2))

    # Box contraints
    vmax = 4.688
    vmin = 1.377
    n = np.prod(shape)
    lower = NumPyVector(np.full(n, 1./vmax**2 , dtype=np.float32))
    upper = NumPyVector(np.full(n, 1./vmin**2 , dtype=np.float32))

    # Configure parameter list.  ################
    # L-Secant-B Line-Search Method (Type B, Bound Constraints)
    params = ParameterList()
    params['General'] =  ParameterList()
    params['General']['Output Level'] = 1
    params['Step'] = ParameterList()
    params['Step']['Type'] = 'Line Search'
    params['Step']['Line Search'] = ParameterList()
    params['Step']['Line Search']['Descent Method']= ParameterList()
    params['Step']['Line Search']['Descent Method']['Type']= "Quasi-Newton Method"
    params['Status Test'] = ParameterList()
    params['Status Test']['Iteration Limit'] = 20

    # Set the output stream. 
    stream = getCout()

    # Set up the FWI problem.  ######################
    objective = Objective(metadata)
    bnd = Bounds(lower, upper)
    problem = Problem(objective, x)
    problem.addBoundConstraint(bnd)

    # Solve.  ###################################
    solver = Solver(problem, params)
    solver.solve(stream)
    del objective.dc

    # Save FWI result
    vp = 1.0 / np.sqrt(x.array.reshape(shape))
    with h5py.File('./marmousi2/results/vp_final_result_pyrol_LBFGS.h5', 'w') as f:
        f.create_dataset('vp', data=vp.astype('float32'))
        f.create_dataset('metadata', data=json.dumps(metadata))


if __name__ == "__main__":
    r"""
    This script demonstrates how we can set up a basic FWI framework
    with gradient-based optimization algorithms from the Rapid Optimization
    Library (ROL). The script is basically a copy
    of the devito FWI tutorial (https://github.com/devitocodes/devito/
    blob/master/examples/seismic/tutorials/04_dask.ipynb) with SciPy optimize
    being replaced by ROL. It uses a simple toy example for validation of the
    code.
    """
    inversion_setup("./config/config.yaml")
    main()
