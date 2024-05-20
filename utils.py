#!/usr/bin/env python
# coding: utf-8

# basic imports.
import numpy as np
import segyio as so
import h5py
import json


def expand_array(arr, nbl):
    """
    Expand a 2D NumPy array by copying values along its borders.

    Args:
        arr (numpy.ndarray): The input 2D NumPy array to be expanded.
        nbl (int): The number of border layers to add.

    Returns:
        numpy.ndarray: The expanded 2D NumPy array.
    """
    shape = arr.shape
    new_shape = tuple(x + 2 * nbl for x in shape)
    large_X = np.zeros(new_shape, dtype=arr.dtype)

    # Copy the inner part of the original array to the center of the expanded array
    slices = tuple(slice(nbl, -nbl) for _ in range(len(shape)))
    large_X[slices] = arr

    # Copy values to the left and right borders
    large_X[nbl:-nbl, -nbl:] = arr[:, -1][:, np.newaxis]
    large_X[nbl:-nbl, :nbl] = arr[:, 0][:, np.newaxis]

    # Copy values to the top and bottom borders
    large_X[:nbl, :] = large_X[nbl, :]
    large_X[-nbl:, :] = large_X[-nbl-1, :]

    return large_X


def humanbytes(B):
    """
    Convert the given number of bytes to a human-friendly string representation.

    Args:
        B (int): The number of bytes to be converted.

    Returns:
        str: A string representation of the input bytes in KB, MB, GB, or TB format.
    """
    B = float(B)
    KB = float(1024)
    MB = float(KB ** 2)  # 1,048,576
    GB = float(KB ** 3)  # 1,073,741,824
    TB = float(KB ** 4)  # 1,099,511,627,776

    if B < KB:
        return '{0} {1}'.format(B, 'Bytes' if 0 == B > 1 else 'Byte')
    elif KB <= B < MB:
        return '{0:.2f} KB'.format(B/KB)
    elif MB <= B < GB:
        return '{0:.2f} MB'.format(B/MB)
    elif GB <= B < TB:
        return '{0:.2f} GB'.format(B/GB)
    elif TB <= B:
        return '{0:.2f} TB'.format(B/TB)


def segy_write(data, sourceX, sourceZ, groupX, groupZ, dt, filename, sourceY=None,
               groupY=None, elevScalar=-1000, coordScalar=-1000):
    """
    Write seismic data to a SEG-Y file with associated headers.

    Args:
        data (numpy.ndarray): 2D array of seismic data, where rows represent time samples
                             and columns represent receivers.
        sourceX (float): X-coordinate of the seismic source.
        sourceZ (float): Z-coordinate of the seismic source.
        groupX (numpy.ndarray): X-coordinates of receiver groups.
        groupZ (numpy.ndarray): Z-coordinates of receiver groups.
        dt (float): Time sample interval in seconds.
        filename (str): Name of the output SEG-Y file.
        sourceY (float, optional): Y-coordinate of the seismic source (default is None).
        groupY (numpy.ndarray, optional): Y-coordinates of receiver groups
                                          (default is None).
        elevScalar (int, optional): Elevation scalar for coordinate scaling
                                    (default is -1000).
        coordScalar (int, optional): Coordinate scalar for coordinate scaling
                                     (default is -1000).

    Returns:
        None
    """
    nt = data.shape[0]
    nxrec = len(groupX)

    if sourceY is None and groupY is None:
        sourceY = np.zeros(1, dtype='int')
        groupY = np.zeros(nxrec, dtype='int')

    # Create spec object
    spec = so.spec()
    spec.ilines = np.arange(nxrec)    # dummy trace count
    spec.xlines = np.zeros(1, dtype='int')  # assume coords are already vectorized for 3D
    spec.samples = range(nt)
    spec.format = 1
    spec.sorting = 1
    with so.create(filename, spec) as segyfile:
        for i in range(nxrec):
            segyfile.bin = {
                so.BinField.Samples: data.shape[0],
                so.BinField.Traces: data.shape[1],
                so.BinField.Interval: int(dt*1e3)
            }
            segyfile.header[i] = {
                so.su.tracl: i+1,
                so.su.tracr: i+1,
                so.su.fldr: 1,
                so.su.tracf: i+1,
                so.su.sx: int(np.round(sourceX[0] * np.abs(coordScalar))),
                so.su.sy: int(np.round(sourceY[0] * np.abs(coordScalar))),
                so.su.selev: int(np.round(sourceZ[0] * np.abs(elevScalar))),
                so.su.gx: int(np.round(groupX[i] * np.abs(coordScalar))),
                so.su.gy: int(np.round(groupY[i] * np.abs(coordScalar))),
                so.su.gelev: int(np.round(groupZ[i] * np.abs(elevScalar))),
                so.su.dt: int(dt*1e3),
                so.su.scalel: int(elevScalar),
                so.su.scalco: int(coordScalar)
            }
            segyfile.trace[i] = data[:, i]
        segyfile.dt = int(dt*1e3)
    return


def segy_read(filename, ndims=2):
    """
    Read seismic data from a SEG-Y file.

    This function reads seismic data from a SEG-Y file and extracts relevant
    information such as source and receiver coordinates, sampling parameters,
    and seismic traces.

    Args:
        filename (str): Path to the SEG-Y file to be read.
        ndims (int, optional): The dimensionality of the data (2 or 3). Defaults to 2.

    Returns:
        tuple: A tuple containing the following elements:
            - data (numpy.ndarray): Seismic data as a 2D array (time, receivers).
            - source_coords (numpy.ndarray): Source coordinates as appropriate
              for the specified dimensionality (X, Z) for 2D or (X, Y, Z) for 3D.
            - receiver_coords (numpy.ndarray): Receiver coordinates as appropriate
              for the specified dimensionality (X, Z) for 2D or (X, Y, Z) for 3D.
            - tmax (float): Maximum time in seconds.
            - dt (float): Time sampling interval in seconds.
            - nt (int): Number of time samples.
    """
    with so.open(filename, "r", ignore_geometry=True) as segyfile:
        segyfile.mmap()

        # Assume input data is for single common shot gather
        sourceX = segyfile.attributes(so.TraceField.SourceX)[0]
        sourceY = segyfile.attributes(so.TraceField.SourceY)[0]
        sourceZ = segyfile.attributes(so.TraceField.SourceSurfaceElevation)[0]
        groupX = segyfile.attributes(so.TraceField.GroupX)[:]
        groupY = segyfile.attributes(so.TraceField.GroupY)[:]
        groupZ = segyfile.attributes(so.TraceField.ReceiverGroupElevation)[:]
        dt = so.dt(segyfile)/1e3

        # Apply scaling
        elevSc = segyfile.attributes(so.TraceField.ElevationScalar)[0]
        coordSc = segyfile.attributes(so.TraceField.SourceGroupScalar)[0]

        if coordSc < 0.:
            sourceX = sourceX / np.abs(coordSc)
            sourceY = sourceY / np.abs(coordSc)
            sourceZ = sourceZ / np.abs(elevSc)
            groupX = groupX / np.abs(coordSc)
            groupY = groupY / np.abs(coordSc)
        elif coordSc > 0.:
            sourceX = sourceX * np.abs(coordSc)
            sourceY = sourceY * np.abs(coordSc)
            sourceZ = sourceZ * np.abs(elevSc)
            groupX = groupX * np.abs(coordSc)
            groupY = groupY / np.abs(coordSc)

        if elevSc < 0.:
            groupZ = groupZ / np.abs(elevSc)
        elif elevSc > 0.:
            groupZ = groupZ * np.abs(elevSc)

        nrec = len(groupX)
        nt = len(segyfile.trace[0])

        # Extract data
        data = np.zeros(shape=(nt, nrec), dtype='float32')
        for i in range(nrec):
            data[:, i] = segyfile.trace[i]
        tmax = (nt-1)*dt

    if ndims == 2:
        return data, np.vstack((sourceX, sourceZ)).T,
        np.vstack((groupX, groupZ)).T, tmax, dt, nt
    else:
        return data, np.vstack((sourceX, sourceY, sourceZ)).T,
        np.vstack((groupX, groupY, groupZ)).T, tmax, dt, nt


def make_lookup_table(sgy_file):
    """
    Create a lookup table of shot records based on SEG-Y header information.

    This function scans a SEG-Y file and organizes shot records into a dictionary
    where the keys are the unique shot record IDs, and the values are dictionaries
    containing information about each shot record.

    Args:
        sgy_file (str): The path to the SEG-Y file to process.

    Returns:
        dict: A dictionary containing shot record information with shot IDs as keys.
              Each entry includes the filename, trace position, number of traces, source
              coordinates, and receiver coordinates for the corresponding shot record.

    Example:
        >>> sgy_lookup = make_lookup_table('data.segy')
        >>> shot_info = sgy_lookup[1]
        >>> print(f"Shot ID: 1\nSource Coordinates: {shot_info['Source']}\n"
        ...       f"Number of Traces: {shot_info['Num_Traces']}")

    """
    tbl = {}
    with so.open(sgy_file, ignore_geometry=True) as f:
        f.mmap()
        idx = None
        pos_in_file = 0
        for hdr in f.header:
            if int(hdr[so.TraceField.SourceGroupScalar]) < 0:
                scalco = abs(1./hdr[so.TraceField.SourceGroupScalar])
            else:
                scalco = hdr[so.TraceField.SourceGroupScalar]
            if int(hdr[so.TraceField.ElevationScalar]) < 0:
                scalel = abs(1./hdr[so.TraceField.ElevationScalar])
            else:
                scalel = hdr[so.TraceField.ElevationScalar]
            # Check to see if we're in a new shot
            if idx != hdr[so.TraceField.FieldRecord]:
                idx = hdr[so.TraceField.FieldRecord]
                tbl[idx] = {}
                tbl[idx]['filename'] = sgy_file
                tbl[idx]['Trace_Position'] = pos_in_file
                tbl[idx]['Num_Traces'] = 1
                tbl[idx]['Source'] = (hdr[so.TraceField.SourceX]*scalco,
                                      hdr[so.TraceField.SourceY]*scalco,
                                      hdr[so.TraceField.SourceSurfaceElevation] *
                                      scalel)
                tbl[idx]['Receivers'] = []
            else:  # Not in a new shot, so increase the number of traces in the shot by 1
                tbl[idx]['Num_Traces'] += 1
            tbl[idx]['Receivers'].append((hdr[so.TraceField.GroupX]*scalco,
                                         hdr[so.TraceField.GroupY]*scalco,
                                         hdr[so.TraceField.ReceiverGroupElevation] *
                                         scalel))
            pos_in_file += 1

    return tbl


def save_model(model_name, datakey, data, metadata, dtype=np.float32):
    """
    Save model data and associated metadata to an HDF5 file.

    This function takes the provided model data, metadata, and data type
    and saves them to an HDF5 file with the specified `model_name`. The
    model data is stored in a dataset identified by `datakey`, while the
    metadata is stored in a separate dataset named 'metadata'.

    Args:
        model_name (str): The name of the HDF5 file to be created or
            overwritten.
        datakey (str): The key to identify the model data in the HDF5 file.
        data (numpy.ndarray): The model data to be saved.
        metadata (dict): Metadata associated with the model.
        dtype (numpy.dtype, optional): The data type for the model data.
            Defaults to numpy.float32.

    Returns:
        None
    """
    with h5py.File(model_name, 'w') as f:
        f.create_dataset(datakey, data=data, dtype=dtype)
        f.create_dataset('metadata', data=json.dumps(metadata))


def load_shot(filename, position, traces_in_shot):
    """
    Load a shot record from a SEG-Y file and return shot data, maximum time,
    and sample interval.

    Args:
        filename (str): The path to the SEG-Y file containing the shot record.
        position (int): The position of the first trace of the shot in the file.
        traces_in_shot (int): The number of traces in the shot.

    Returns:
        tuple: A tuple containing the following elements:
            - numpy.ndarray: Shot data as a 2D NumPy array with shape (nsamples, traces).
            - float: Maximum time (tmax) in seconds.
            - float: Sample interval (samp_int) in milliseconds.

    Raises:
        RuntimeError: If an exception occurs while reading the SEG-Y file.

    """
    try:
        with so.open(filename, ignore_geometry=True) as f:
            num_samples = len(f.samples)
            samp_int = f.bin[so.BinField.Interval] / 1000.
            retrieved_shot = np.zeros((num_samples, traces_in_shot))
            shot_traces = f.trace[position:position + traces_in_shot]
            for i, trace in enumerate(shot_traces):
                retrieved_shot[:, i] = trace

        tmax = (num_samples - 1) * samp_int

        return retrieved_shot, tmax, samp_int
    except RuntimeError as e:
        print("Caught an exception:", e)