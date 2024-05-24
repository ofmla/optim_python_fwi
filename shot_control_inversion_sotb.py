"""FWI example."""
import numpy as np
import os
import time
import h5py
import json
from dask_cluster import DaskCluster
from sotb_wrapper import interface
from utils import save_model


class ControlInversion:
    "Class to control the gradient-based inversion using sotb-wrapper"

    def run_inversion(self):
        "Run the inversion workflow"
        dc = DaskCluster()

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

        # Check whether the specified path exists or not
        results_path = parfile_path+'../results/'
        isExist = os.path.exists(results_path)
        if not isExist:
            # Create a new directory because it does not exist
            os.makedirs(results_path)

        g = open(results_path+'gradient_zero.file', 'wb')

        # Create an instance of the SEISCOPE optimization toolbox (sotb) Class.
        sotb = interface.sotb_wrapper()

        n = np.prod(shape)  # dimension
        flag = 0  # first flag

        print_flag = 1  # print info in output files
        debug = 0  # level of details for output files
        niter_max = 20  # maximum iteration number
        nls_max = 20  # maximum line-search number

        # computation of the cost and gradient associated
        # with the initial guess
        fcost, grad = dc.gen_grad_cluster(X)

        # Set some fields of the UserDefined derived type in Fortran (ctype structure).
        # parameter initialization
        sotb.set_inputs(
            fcost,
            niter_max,
            nls_max=nls_max,
            print_flag=print_flag,
            debug=debug,
        )

        # Save first gradient/image
        grad.reshape(-1, shape[1]).astype('float32').tofile(g)

        start_time = time.time()
        # Optimization loop
        while (flag != 2 and flag != 4):
            flag = sotb.LBFGS(n, X, fcost, grad, flag, lb, ub)
            if (flag == 1):
                # compute cost and gradient at point x
                fcost, grad = dc.gen_grad_cluster(X)
        elapsed_time = time.time() - start_time
        time_format = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        print("Iterative inversion took :- {}".format(time_format))

        # Helpful console writings
        print('END OF TEST')
        print('FINAL iterate is : ', X)
        print('See the convergence history in iterate_LBFGS.dat')
        s = 'vp_final_result_LB'

        # Save final model/image
        X = 1./np.sqrt(X)
        g = open(results_path+s+'.file', 'wb')
        X = X.reshape(-1, shape[1]).astype('float32')
        X.tofile(g)
        save_model(results_path+s+'.h5', 'vp', X, metadata)

        del dc
