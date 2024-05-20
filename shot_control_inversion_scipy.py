"""FWI example."""
import numpy as np
import os
import h5py
import json
import time
from dask_cluster import DaskCluster
from scipy.optimize import minimize, Bounds
from utils import save_model


class ControlInversion:
    "Class to control the gradient-based inversion using scipy.minimize"

    def run_inversion(self):
        "Run the inversion workflow"
        dc = DaskCluster()

        lb = None  # lower bound constraint
        ub = None  # upper bound constraint

        parfile_path = dc.config_values['solver_params']['parfile_path']

        # Read initial guess and metadata from hdf5 file
        with h5py.File(parfile_path + 'vp_start.h5', 'r') as f:
            v0 = f['vp_start'][()]
            metadata = json.loads(f['metadata'][()])

        dc.config_values['solver_params']['origin'] = (*metadata['origin'],)
        dc.config_values['solver_params']['spacing'] = (*metadata['spacing'],)
        shape = dc.config_values['solver_params']['shape'] = (*metadata['shape'],)

        X = 1.0 / (v0.reshape(-1).astype(np.float32))**2
        # Define physical constraints on velocity - we know the
        # maximum and minimum velocities we are expecting
        vmax = dc.config_values['vmax']
        vmin = dc.config_values['vmin']
        lb = np.ones((np.prod(shape),), dtype=np.float32)*1.0/vmax**2  # in [s^2/km^2]
        ub = np.ones((np.prod(shape),), dtype=np.float32)*1.0/vmin**2  # in [s^2/km^2]

        bounds = Bounds(lb, ub)

        # Check whether the specified path exists or not
        results_path = parfile_path+'../results/'
        isExist = os.path.exists(results_path)
        if not isExist:
            # Create a new directory because it does not exist
            os.makedirs(results_path)

        start_time = time.time()
        # Optimization loop
        solution_object = minimize(dc.gen_grad_cluster,
                                   X, jac=True, method='L-BFGS-B',
                                   bounds=bounds,
                                   options={'disp': True, 'maxiter': 20})
        elapsed_time = time.time() - start_time
        time_format = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        print("Iterative inversion took :- {}".format(time_format))
        s = 'vp_final_result_scipy_LBFGSB'

        # Save final model/image
        X = 1./np.sqrt(solution_object.x)
        g = open(results_path+s+'.file', 'wb')
        X = X.reshape(-1, shape[1]).astype('float32')
        X.tofile(g)
        save_model(results_path+s+'.h5', 'vp', X, metadata)

        #del dc
