# Open-source numerical optimization python libraries for full-waveform inversion: A Review.
This repository contains the implementation to reproduce the numerical experiments of the Geoscience Letters paper: Open-source numerical optimization python
libraries for full-waveform inversion: A Review.

## Requirements

This code runs on CPUs only. Make sure all of the packages below are installed.
```bash
python 3.10
devito 4.8.2+92.ge6cd0b0ab
dask-jobqueue 0.8.5
scipy 1.13.0
matplotlib 3.8.0
segyio 1.9.12
sotb_wrapper 2.0.2
h5py 3.10.0
pyrol 0.0.1
```
## Usage: 
```
make -f mymakefile
```
This should run all the experiments and regenerate all plots used in the paper. 

To find your way around the code, the Makefile is the recommended starting point. 

## Todo

- [ ] Dockerfile   
