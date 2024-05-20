"""FWI example."""
import sys
import numpy as np
import os
import h5py
import json
import time
from dask_cluster import DaskCluster
from utils import save_model
 
# appending a path
sys.path.append('/app/nlopt-2.7.1/install/lib/python3.10/site-packages')

import nlopt

# Define a global variable
count = 0

class ControlInversion:
    "Class to control the gradient-based inversion using NLopt"

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

        x = 1.0 / (v0.reshape(-1).astype(np.float32))**2
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

        def myfunc(x, grad):
            global count
            if count == 0:
                print("%10s %15s %15s" % ("Iteration", "Function Val", "norm(g)"))
            if grad.size > 0:
                fcost, grad[:] = dc.gen_grad_cluster(x)
            count += 1
            print("{:10d} {:15.5e} {:15.5e}".format(count, fcost, np.linalg.norm(grad)))
            return np.float64(fcost)

        opt = nlopt.opt(nlopt.LD_LBFGS, int(np.prod(shape)))
        opt.set_lower_bounds(lb)
        opt.set_upper_bounds(ub)
        opt.set_min_objective(myfunc)
        opt.set_maxeval(35)
        opt.set_vector_storage(10)
        grad = np.zeros_like(x, dtype=np.float32)

        global count 
        count = 0 # Reset count
        start_time = time.time()
        # Optimization
        minx =  opt.optimize(x)
        elapsed_time = time.time() - start_time
        time_format = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        print("Iterative inversion took :- {}".format(time_format))

        # Helpful console writings
        print('END OF TEST')
        #print(opt.__dict__)
        #print(dir(opt))
        print("minimum value = ", opt.last_optimum_value())
        print("result code = ", opt.last_optimize_result())
        s ='vp_final_result_NLoptLD_LBFGS'

        # Save final model/image
        x = 1./np.sqrt(minx)
        g = open(results_path+s+'.file', 'wb')
        X = x.reshape(-1, shape[1]).astype('float32').
        X.tofile(g)
        save_model(results_path+s+'.h5', 'vp', X, metadata)

        del dc
