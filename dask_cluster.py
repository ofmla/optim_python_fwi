#!/usr/bin/env python
# coding: utf-8

# basic imports.
import os
import errno
import numpy as np
import time
import yaml
import json
import h5py
import gc

from dask_jobqueue import SLURMCluster
from dask.distributed import Client, LocalCluster

from devito import Function, TimeFunction, Inc, Eq, Operator, Grid, configuration
from examples.seismic import AcquisitionGeometry, TimeAxis, Receiver, SeismicModel
from examples.seismic.acoustic import AcousticWaveSolver
from examples.seismic.acoustic.operators import iso_stencil

from utils import segy_write, make_lookup_table, load_shot, humanbytes, expand_array
import cloudpickle as pickle
#import dask

#dask.config.set({'logging.distributed': 'error'})
configuration['log-level'] = 'ERROR' #'DEBUG' or 'INFO'


class DaskCluster:
    '''
    Class for using dask tasks to parallelize forward modeling and gradients calculation.
    '''

    def __init__(self):
        #dask.config.set({'logging.distributed': 'error'})
        config_file = os.path.join(os.getcwd(), "config", "config.yaml")
        if not os.path.isfile(config_file):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), config_file)
        with open(config_file) as file:
            self.config_values = yaml.load(file, Loader=yaml.FullLoader)
        if "queue" not in self.config_values:
            self.config_values["queue"] = "queue_name"
        if "project" not in self.config_values:
            self.config_values["project"] = "project_name"
        if "n_workers" not in self.config_values:
            self.config_values["n_workers"] = 4
        if "cores" not in self.config_values:
            self.config_values["cores"] = 36
        if "processes" not in self.config_values:
            self.config_values["processes"] = 1
        if "memory" not in self.config_values:
            self.config_values["memory"] = 320
        if "job_extra" not in self.config_values:
            self.config_values["job_extra"] = ['-e slurm-%j.err', '-o slurm-%j.out',
                                               '--job-name="dask_task"']

        are_true = (self.config_values["forward"] and self.config_values["fwi"])
        if are_true:
            raise ValueError("Both forward and fwi cannot be True simultaneously.")
        are_false = (not self.config_values["forward"] and not self.config_values["fwi"])
        if are_false:
            raise ValueError("At least one of 'forward' or 'fwi' must be True.")
        fwi = self.config_values["fwi"]
        print("Running fwi ...") if fwi else print("Running Forward modeling ...")

        if self.config_values["use_local_cluster"]:
            # single-threaded execution, as this is actually best for the workload
            cluster = LocalCluster(n_workers=self.config_values["n_workers"],
                                   threads_per_worker=1,
                                   memory_limit='5GB', death_timeout=60,
                                   resources={'process': 1})
        else:
            cluster = SLURMCluster(queue=self.config_values["queue"],
                                   account=self.config_values["project"],
                                   cores=self.config_values["cores"],
                                   processes=self.config_values["processes"],
                                   memory=str(self.config_values["memory"])+"GB",
                                   death_timeout='60',
                                   interface='ib0',
                                   worker_extra_args=['--resources "process=1"'],
                                   job_extra_directives=self.config_values["job_extra"])

            # Scale cluster to n_workers
            cluster.scale(jobs=self.config_values["n_workers"])

        # Wait for cluster to start
        time.sleep(10)
        self.client = Client(cluster)
        # initialize tasks dictionary
        self._set_tasks_from_files()

    def __del__(self):
        self.client.close()

    def _set_tasks_from_files(self):
        '''
        Creates a dict which contains the tasks to be run.
        '''

        if self.config_values["forward"]:
            nshots = self.config_values['nshots']
            nrecs = self.config_values['nrecs']
            model_size = self.config_values['model_size']
            # Define acquisition geometry: receivers
            # First, sources position
            src_coord = np.empty((nshots, 2))
            src_coord[:, 0] = np.linspace(0., model_size, num=nshots)
            src_coord[:, -1] = self.config_values['src_depth']
            # Initialize receivers for synthetic and imaging data
            rec_coord = np.empty((nrecs, 2))
            rec_coord[:, 0] = np.linspace(0, model_size, num=nrecs)
            rec_coord[:, 1] = self.config_values['rec_depth']

            self.tasks_dict = {i: {'Source': src_coord[i],
                                   'Receivers': rec_coord} for i in range(nshots)}
        else:
            # Read chunk of shots
            segy_dir_files = self.config_values['solver_params']['shotfile_path']
            segy_files = [f for f in os.listdir(segy_dir_files) if f.endswith('.segy')]
            segy_files = [segy_dir_files + sub for sub in segy_files]

            # Create a dictionary of shots
            self.tasks_dict = {}
            for count, sfile in enumerate(segy_files, start=1):
                self.tasks_dict.update({str(count) if k == 1 else k: v
                                       for k, v in make_lookup_table(sfile).items()})

    def create_break_list(self):
        ''''
        Converts task_dict dictionary into list of dictionaries and breaks the list into
        sublists. Each dictionary stores information about the geometry of a single shot.

        Returns:
            break_list (list): List with sublists (smaller lists) of dictionaries
        '''
        shot_master_list = [(lambda d: d.update(id=key) or d)(val)
                            for (key, val) in self.tasks_dict.items()]
        # Share work roughly evenly between processes. Original list of shots is break up
        # into many lists. In other words a list of lists will be divided up among the
        # processes. 

        if self.config_values["use_local_cluster"]:
            p = self.config_values["n_workers"]
        else:
            p = self.config_values["n_workers"]*self.config_values["processes"]

        # Note that we assume that the number of shots is greater than the number
        # of processes

        c = len(shot_master_list)//p
        r = len(shot_master_list) % p
        # How many elements break_list should have
        break_list = [shot_master_list[i*(c+1):i*(c+1)+c+1] if i < r else
                      shot_master_list[i*c+r:i*c+r+c] for i in range(0, p)]

        return break_list

    def bcast_data(self):
        '''
        Adds multiple devito Operators to config_values dictionary. A scatter operation
        is used to move a new dictionary with unpacked items from config_values to all
        workers (broadcast=True). It is useful as Operators are used in many computations

        Returns:
            par (dask future): future pointing to dictionary with devito Operators
        '''
        model = DaskCluster.get_model(self.config_values['solver_params'])
        t0 = self.config_values['solver_params']['t0']
        tn = self.config_values['solver_params']['tn']
        f0 = self.config_values['solver_params']['f0']
        space_order = self.config_values['solver_params']['space_order']
        src_coordinates = np.empty((1, model.dim), dtype=np.float32)
        rec_coordinates = np.empty((self.config_values['nrecs'], model.dim),
                                   dtype=np.float32)
        geometry = AcquisitionGeometry(model, rec_coordinates, src_coordinates,
                                       t0=t0, tn=tn, src_type='Ricker', f0=f0)
        solver = AcousticWaveSolver(model, geometry, space_order=space_order)

        src_illum = Function(name='src_illum', grid=model.grid)
        grad = Function(name='grad', grid=model.grid)
        dtype = self.config_values['solver_params']['dtype']
        eps = np.finfo(dtype).eps

        rev_op = DaskCluster.ImagingOperator(geometry, model, grad, src_illum,
                                             space_order, save=True)
        eq = Eq(src_illum, grad/(src_illum+eps))
        pointwise_op = Operator(eq)

        self.config_values['solver_params']['rev_op'] = rev_op
        self.config_values['solver_params']['pointwise_op'] = pointwise_op
        self.config_values['solver_params']['solver'] = solver
        # send data to all workers
        my_dict= {**self.config_values['solver_params']}
        par = self.client.scatter(my_dict, broadcast=True)

        return par

    def gen_shots_cluster(self):
        '''
        Forward modeling for all the shots in parallel in a dask cluster.

        Raises:
            Exception: Raises an exception if some shot was not generated correctly.

        '''
        start_time = time.time()
        model = DaskCluster.get_model(self.config_values['solver_params'])
        t0 = self.config_values['solver_params']['t0']
        tn = self.config_values['solver_params']['tn']
        f0 = self.config_values['solver_params']['f0']
        space_order = self.config_values['solver_params']['space_order']
        src_coordinates = np.empty((1, model.dim), dtype=np.float32)
        rec_coordinates = np.empty((self.config_values['nrecs'], model.dim),
                                   dtype=np.float32)
        geometry = AcquisitionGeometry(model, rec_coordinates, src_coordinates,
                                       t0=t0, tn=tn, src_type='Ricker', f0=f0)
        solver = AcousticWaveSolver(model, geometry, space_order=space_order)

        self.config_values['solver_params']['solver'] = solver
        par = self.client.scatter({**self.config_values['solver_params']},
                                  broadcast=True)
        break_list = self.create_break_list()
        shot_futures = self.client.map(DaskCluster.gen_shot_in_worker,
                                       break_list,
                                       solver_params=par,
                                       resources={'process': 1})
        all_shot_results = self.client.gather(shot_futures)
        elapsed_time = time.time() - start_time
        time_format = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

        if all(all_shot_results):
            print("Forward modeling took :- {}".format(time_format))
            print("Successfully generated {0:d} shots".format(len(self.tasks_dict)))
        else:
            raise Exception("Some error occurred. Please check logs")

    def gen_grad_cluster(self, X):
        '''
        Gradient computing for all the shots in parallel in a dask cluster

        Args:
            X (np.ndarray): Updated physical parameter (i.e., vp)

        Returns:
            objective (float): objective function value
            grad (np.ndarray): gradient for all shots
        '''
        DaskCluster.gen_grad_cluster.counter += 1
        shot_futures = []
        shape = self.config_values['solver_params']['shape']
        spacing = self.config_values['solver_params']['spacing']
        if DaskCluster.gen_grad_cluster.counter == 1:
            func = DaskCluster.grad_fwi_in_worker
            par = self.bcast_data()
            break_list = self.create_break_list()
            if not hasattr(DaskCluster.gen_grad_cluster, "func"):
                DaskCluster.gen_grad_cluster.func = func
            if not hasattr(DaskCluster.gen_grad_cluster, "par"):
                DaskCluster.gen_grad_cluster.par = par
            if not hasattr(DaskCluster.gen_grad_cluster, "bl"):
                DaskCluster.gen_grad_cluster.bl = break_list

        model = DaskCluster.get_model(self.config_values['solver_params'])
        nbl = self.config_values['solver_params']['nbl']
        large_X = expand_array(np.reshape(X, shape), nbl)
        model.update('vp', 1.0/np.sqrt(large_X))
        pickle.dump({'model': model}, open('model0.p', "wb"))

        start_time = time.time()
        shot_futures = self.client.map(DaskCluster.gen_grad_cluster.func,
                                       DaskCluster.gen_grad_cluster.bl,
                                       solver_params=DaskCluster.gen_grad_cluster.par,
                                       resources={'process': 1})
        all_shot_results = self.client.gather(shot_futures)

        if len(shape) == 2:
            domain_size = ((shape[0] - 1) * spacing[0], (shape[1] - 1) * spacing[1])
        else:
            domain_size = ((shape[0] - 1) * spacing[0], (shape[1] - 1) * spacing[1],
                           (shape[2] - 1) * spacing[2])

        grid = Grid(shape=shape, extent=domain_size)
        f = Function(name='f', grid=grid)
        grad = Function(name='g', grid=grid)
        grad_update = Inc(grad, f)
        op_grad = Operator([grad_update])

        grad.data[:] = all_shot_results[0][0]
        objective = all_shot_results[0][1]
        i = 1

        # Iterating using while loop
        while i < len(all_shot_results):
            f.data[:] = all_shot_results[i][0]
            op_grad.apply()
            objective += all_shot_results[i][1]
            i += 1

        mute_depth = self.config_values['mute_depth']
        if mute_depth is not None:
            grad.data[:, 0:mute_depth] = 0.

        elapsed_time = time.time() - start_time
        print("Cost_fcn eval took {0:8.2f} sec - Cost_fcn={1:10.3E}".format(elapsed_time,
                                                                            objective))
        del op_grad
        return objective, grad.data.flatten().astype(np.float32)
    gen_grad_cluster.counter = 0

    @staticmethod
    def gen_shot_in_worker(shot_dict, solver_params):
        '''
        Serial Forward modeling function.

        Args:
            shot_dict (dict): Dictionary containing informations about a single shot.
            solver_params (dict): Dictionary containing diverse informations about
                 adjoint simulation.

        Returns:
            bool: indicator for forward modeling sucess.
        '''

        model = DaskCluster.get_model(solver_params)
        shape = model.shape
        space_order = solver_params['space_order']
        dt = solver_params['dt']
        t0 = solver_params['t0']
        tn = solver_params['tn']
        model_name = solver_params['model_name']
        solver = solver_params['solver']

        # Geometry for current shot
        src = solver.geometry.src
        dobs = solver.geometry.rec

        # Define the wavefield(s) with the size of the model and the time dimension
        u = TimeFunction(name="u", grid=model.grid, time_order=2,
                         space_order=space_order)
        autotune = ('aggressive', 'runtime') if len(shape) == 3 else False

        if not type(shot_dict) is list:
            shot_dict = [shot_dict]

        for d in shot_dict:
            u.data[:] = 0.
            src.coordinates.data[:] = np.array(d['Source']).reshape((1, len(shape)))
            dobs.coordinates.data[:] = np.array(d['Receivers'])
            solver.forward(src=src, rec=dobs, u=u, autotune=autotune)

            print('Shot with time interval of {} ms'.format(model.critical_dt))

            str_shot = str(d['id']).zfill(3)
            filename = '{}_{}_suheader_{}.segy'.format('shot', str_shot, model_name)
            filename = solver_params['shotfile_path'] + filename
            if dt is not None:
                nsamples = int((tn-t0)/dt + 1)
                data = dobs.resample(num=nsamples)
            else:
                dt = model.critical_dt
                data = dobs
            # Save shot in segy format
            if len(shape) == 3:
                segy_write(data.data[:], [src.coordinates.data[0, 0]],
                           [src.coordinates.data[0, -1]],
                           data.coordinates.data[:, 0],
                           data.coordinates.data[:, -1], dt, filename,
                           sourceY=[src.coordinates.data[0, 1]],
                           groupY=data.coordinates.data[:, -1])
            else:
                segy_write(data.data[:], [src.coordinates.data[0, 0]],
                           [src.coordinates.data[0, -1]],
                           data.coordinates.data[:, 0],
                           data.coordinates.data[:, -1], dt, filename)
            data = None
        del solver
        return True

    @staticmethod
    def gen_shot_in_worker_rol(shot_dict, solver_params):
        '''
        Serial Forward modeling function (ROL).

        Args:
            shot_dict (dict): Dictionary containing informations about a single shot.
            solver_params (dict): Dictionary containing diverse informations about
                 adjoint simulation.

        Returns:
            objective (float): objective function value
        '''
        space_order = solver_params['space_order']
        # Set up solver    
        solver = solver_params['solver']

        # Get the current model
        pkl = pickle.load(open('model0.p', "rb"))
        model = pkl['model']
        solver.geometry.resample(model.critical_dt)

        # Geometry for current shot
        src = solver.geometry.src
        rec = solver.geometry.rec
        slices = tuple(slice(model.nbl, -model.nbl) for _ in range(model.dim))

        # Here we assume that there is enough memory
        residual = Receiver(name='residual', grid=model.grid,
                            time_range=solver.geometry.time_axis,
                            coordinates=rec.coordinates)
        u = TimeFunction(name='u', grid=model.grid, time_order=2,
                         space_order=space_order)

        # loop over the shots
        if not type(shot_dict) is list:
            shot_dict = [shot_dict]
        objective =0.
        for d in shot_dict:
            # Get a single shot as a numpy array
            retrieved_shot, tn, dt = load_shot(d['filename'],
                                               d['Trace_Position'],
                                               d['Num_Traces'])

            if model.dim == 3:
                src_coord = np.array(d['Source']).reshape((1, 3))
                rec_coord = np.array(d['Receivers'])
            else:
                src_coord = np.array([d['Source'][0],
                                      d['Source'][-1]]).reshape((1, 2))
                rec_coord = np.array([(r[0], r[-1]) for r in d['Receivers']])
            u.data[:] = 0.
            src.coordinates.data[:] = src_coord
            residual.coordinates.data[:] = rec.coordinates.data[:] = rec_coord
            time_range = TimeAxis(start=0, stop=tn, step=dt)
            dobs = Receiver(name='dobs', grid=solver.model.grid, time_range=time_range,
                            coordinates=rec_coord)
            dobs.data[:] = retrieved_shot[:]
            dobs = dobs.resample(num=solver.geometry.nt)
            solver.forward(src=src, rec=rec, u=u, vp=model.vp,
                           dt=model.critical_dt, save=False)

            residual.data[:] = rec.data - dobs.data
            objective += .5*np.linalg.norm(residual.data.ravel())**2
            dobs = None
        solver = None
        gc.collect()

        return objective

    @staticmethod
    def grad_fwi_in_worker(shot_dict, solver_params, return_tuple=True):
        '''
        Serial fwi gradient computation function

        Args:
            shot_dict (dict): Dictionary containing informations about a single shot
            solver_params (dict): Dictionary containing diverse informations about
                 adjoint simulation
            return_tuple (bool): If True, return a tuple with additional information.
                Default is True.
        Returns:
            The gradient for the given shot or a tuple containing the gradient and
            objective function value.
            objective (float): objective function value
            copied_grad (np.ndarray): gradient for the given shot
        '''
        space_order = solver_params['space_order']
        solver = solver_params['solver']
        rev_op = solver_params['rev_op']
        pointwise_op = solver_params['pointwise_op']

        # Get the current model
        pkl = pickle.load(open('model0.p', "rb"))
        model = pkl['model']
        solver.geometry.resample(model.critical_dt)

        # Geometry for current shot
        src = solver.geometry.src
        rec = solver.geometry.rec
        objective = 0.
        slices = tuple(slice(model.nbl, -model.nbl) for _ in range(model.dim))

        # Here we assume that there is enough memory
        residual = Receiver(name='residual', grid=model.grid,
                            time_range=solver.geometry.time_axis,
                            coordinates=rec.coordinates)
        src_illum = Function(name='src_illum', grid=model.grid)
        grad = Function(name='grad', grid=model.grid)
        gradsum = Function(name='gradsum', grid=model.grid)
        du = TimeFunction(name='du', grid=model.grid, time_order=2,
                          space_order=space_order)
        u = TimeFunction(name='u', grid=model.grid, time_order=2,
                         space_order=space_order, save=solver.geometry.nt)

        # loop over the shots
        if not type(shot_dict) is list:
            shot_dict = [shot_dict]
        for d in shot_dict:
            # Get a single shot as a numpy array
            retrieved_shot, tn, dt = load_shot(d['filename'],
                                               d['Trace_Position'],
                                               d['Num_Traces'])

            if model.dim == 3:
                src_coord = np.array(d['Source']).reshape((1, 3))
                rec_coord = np.array(d['Receivers'])
            else:
                src_coord = np.array([d['Source'][0],
                                     d['Source'][-1]]).reshape((1, 2))
                rec_coord = np.array([(r[0], r[-1]) for r in d['Receivers']])
            u.data[:] = 0.
            du.data[:] = 0.
            grad.data[:] = 0.
            src_illum.data[:] = 0.
            src.coordinates.data[:] = src_coord
            residual.coordinates.data[:] = rec.coordinates.data[:] = rec_coord
            time_range = TimeAxis(start=0, stop=tn, step=dt)
            dobs = Receiver(name='dobs', grid=solver.model.grid, time_range=time_range,
                            coordinates=rec_coord)
            dobs.data[:] = retrieved_shot[:]
            dobs = dobs.resample(num=solver.geometry.nt)

            solver.forward(src=src, rec=rec, u=u, vp=model.vp,
                           dt=model.critical_dt, save=True)

            residual.data[:] = rec.data - dobs.data
            objective += .5*np.linalg.norm(residual.data.ravel())**2

            rev_op(u0=u, du=du, vp=model.vp, dt=model.critical_dt,
                   time_size=solver.geometry.nt, time_M=solver.geometry.nt-2,
                   grad=grad, src_illum=src_illum, rec=residual)

            pointwise_op.apply(grad=grad, src_illum=src_illum)
            gradsum.data[:] += src_illum.data[:]
            dobs = None

        u = None
        copied_grad = gradsum.data[slices].copy()
        gc.collect()
        if return_tuple:
            return copied_grad, objective
        else:
            return copied_grad
        return 

    def ImagingOperator(geometry, model, image, src_illum, space_order,
                        save=True):
        '''
        Creates an adjoint + crosscorrelation Operator. It is used to
        compute the gradient in the functions set out above.

        Args:
            geometry (examples.seismic.utils.AcquisitionGeometry): object that encapsules
                the geometry of an acquisition
            model (examples.seismic.model.SeismicModel): object that encapsules all
                physical parameters
            image (devito.types.Function): Image function
            src_illum (devito.types.Function): Source illumination function
            space_order (int): Discretisation order for space derivatives
            save (bool, optional): Whether or not all forward states for all times
                must be saved. Default True

        Returns:
            devito.operator.operator.Operator: adjoint + crosscorrelation Operator
        '''
        dt = model.grid.stepping_dim.spacing
        time_order = 2

        rec = Receiver(name='rec', grid=model.grid, time_range=geometry.time_axis,
                       npoint=geometry.nrec)

        # Gradient symbol and wavefield symbols
        u0 = TimeFunction(name='u0', grid=model.grid, save=geometry.nt if save
                          else None, time_order=time_order, space_order=space_order)
        du = TimeFunction(name="du", grid=model.grid, save=None,
                          time_order=time_order, space_order=space_order)

        # Define the wave equation, but with a negated damping term
        eqn = iso_stencil(du, model, kernel='OT2', forward=False)

        # Define residual injection at the location of the forward receivers
        res_term = rec.inject(field=du.backward, expr=rec * dt**2 / model.m)

        # Correlate u and v for the current time step and add it to the image
        image_update = Inc(image, - u0.dt2 * du)
        src_illum_updt = Eq(src_illum, src_illum + u0**2)

        return Operator(eqn + res_term + [image_update] +
                        [src_illum_updt], name='Gradient', subs=model.spacing_map)

    @staticmethod
    def get_model(par_dict):
        '''
        Read physical parameters from hdf5 file and
        create a Model instance
        '''
        dtype = par_dict['dtype']

        if dtype == 'float32':
            dtype = np.float32
        elif dtype == 'float64':
            dtype = np.float64
        else:
            raise ValueError("Invalid dtype")

        # Metadata from hdf5 file
        with h5py.File(par_dict['parfile_path']+'vp.h5', 'r') as f:
            metadata = json.loads(f['metadata'][()])
            #
            origin = (*metadata['origin'],)
            shape = (*metadata['shape'],)
            spacing = (*metadata['spacing'],)
            vp = np.empty(shape)
            f['vp'].read_direct(vp)

        space_order = par_dict['space_order']
        nbl = par_dict['nbl']

        return SeismicModel(vp=vp, origin=origin, shape=shape,
                            spacing=spacing, space_order=space_order,
                            nbl=nbl, bcs="damp", dtype=dtype)
