# Open-source numerical optimization python libraries for full-waveform inversion: A Review.
This repository contains the implementation to reproduce the numerical experiments of the Geoscience Letters paper: Open-source numerical optimization python
libraries for full-waveform inversion: A Review.

👉 To find your way around the code, the `mymakefile` file is the recommended starting point. 

## Dokerization

Along with the code a `Dockerfile` from which you can build a docker image for our Python application is provided.

### Build the docker image

You can build the docker image, named myapp, with the following commands

```shell
MY_KEY=$(cat ~/.ssh/id_rsa)
docker build --build-arg SSH_KEY="$MY_KEY" --tag myapp .
```

… then wait for docker to build an image for our app (it might tight a take for downloading and update it the packages list).

> Make sure Docker is installed on your machine (www.docker.com).

### Run the container

To run all the experiments used in the paper from the docker image use

```shell
docker run --rm -ti myapp make -f mymakefile
```
This execute the `make` command with the specified Makefile (mymakefile), which invoke python scripts for `forward` modeling and `fwi`. When `make -f mymakefile` is run, `forward` will be executed first, followed by `fwi`. You also can run `fwi` with each one of the frameworks individually, i.e., `docker run --rm -ti myapp make -f mymakefile scipy`, will be execute `fwi` using `scipy`, `forward` will be executed first if it has not been executed yet

The command above should outputs:

```shell
python3 generate_shot_data.py marmousi2
Solver parameters are being substituted with the following new values:
Key: shotfile_path  Value: ./marmousi2/shots/
Key: parfile_path   Value: ./marmousi2/parameters_hdf5/
Key: t0             Value: 0.0
Key: tn             Value: 5000.0
Key: dt             Value: 4.0
Key: f0             Value: 0.004
Key: model_name     Value: marmousi2
Key: nbl            Value: 50
Key: space_order    Value: 8
Key: dtype          Value: float32
Running Forward modeling ...
Shot with time interval of 4.427000045776367 ms
Shot with time interval of 4.427000045776367 ms
/opt/conda/lib/python3.10/site-packages/segyio/utils.py:18: RuntimeWarning: Implicit conversion to contiguous array
  warnings.warn(msg, RuntimeWarning)
/opt/conda/lib/python3.10/site-packages/segyio/utils.py:18: RuntimeWarning: Implicit conversion to contiguous array
  warnings.warn(msg, RuntimeWarning)
Shot with time interval of 4.427000045776367 ms
Shot with time interval of 4.427000045776367 ms
Shot with time interval of 4.427000045776367 ms
Shot with time interval of 4.427000045776367 ms
/opt/conda/lib/python3.10/site-packages/segyio/utils.py:18: RuntimeWarning: Implicit conversion to contiguous array
  warnings.warn(msg, RuntimeWarning)
/opt/conda/lib/python3.10/site-packages/segyio/utils.py:18: RuntimeWarning: Implicit conversion to contiguous array
  warnings.warn(msg, RuntimeWarning)
Shot with time interval of 4.427000045776367 ms
Shot with time interval of 4.427000045776367 ms
Shot with time interval of 4.427000045776367 ms
Shot with time interval of 4.427000045776367 ms
Shot with time interval of 4.427000045776367 ms
Shot with time interval of 4.427000045776367 ms
Shot with time interval of 4.427000045776367 ms
Shot with time interval of 4.427000045776367 ms
Shot with time interval of 4.427000045776367 ms
Shot with time interval of 4.427000045776367 ms
Forward modeling took :- 00:00:11
Successfully generated 16 shots
python3 inversion_script.py shot_control_inversion_scipy || true
Running fwi ...
Cost_fcn eval took     9.91 sec - Cost_fcn= 9.732E+06
RUNNING THE L-BFGS-B CODE

           * * *

Machine precision = 2.220D-16
 N =        37488     M =           10

At X0         0 variables are exactly at the bounds

At iterate    0    f=  9.73176D+06    |proj g|=  4.73626D-01
Cost_fcn eval took     6.68 sec - Cost_fcn= 1.040E+08
Cost_fcn eval took     6.52 sec - Cost_fcn= 9.728E+06
Cost_fcn eval took     6.44 sec - Cost_fcn= 6.844E+07
Cost_fcn eval took     6.53 sec - Cost_fcn= 9.726E+06
Cost_fcn eval took     6.82 sec - Cost_fcn= 9.726E+06
Cost_fcn eval took     7.48 sec - Cost_fcn= 4.857E+07
Cost_fcn eval took     6.67 sec - Cost_fcn= 9.725E+06
Cost_fcn eval took     6.39 sec - Cost_fcn= 9.725E+06
Cost_fcn eval took     7.47 sec - Cost_fcn= 3.793E+07
Cost_fcn eval took     6.66 sec - Cost_fcn= 9.725E+06
Cost_fcn eval took     6.58 sec - Cost_fcn= 9.725E+06
Cost_fcn eval took     8.09 sec - Cost_fcn= 9.725E+06

At iterate    1    f=  9.72502D+06    |proj g|=  4.73615D-01
Cost_fcn eval took     7.13 sec - Cost_fcn= 7.310E+06

At iterate    2    f=  7.30998D+06    |proj g|=  4.52688D-01
Cost_fcn eval took     6.82 sec - Cost_fcn= 6.161E+06

At iterate    3    f=  6.16079D+06    |proj g|=  4.36160D-01
Cost_fcn eval took     7.25 sec - Cost_fcn= 3.737E+06

At iterate    4    f=  3.73665D+06    |proj g|=  4.30242D-01
Cost_fcn eval took     6.48 sec - Cost_fcn= 3.480E+06

At iterate    5    f=  3.47960D+06    |proj g|=  4.81889D-01
Cost_fcn eval took     6.72 sec - Cost_fcn= 2.547E+06

At iterate    6    f=  2.54710D+06    |proj g|=  4.80780D-01
Cost_fcn eval took     6.70 sec - Cost_fcn= 1.881E+06

At iterate    7    f=  1.88058D+06    |proj g|=  4.76792D-01
Cost_fcn eval took     6.80 sec - Cost_fcn= 1.486E+06

At iterate    8    f=  1.48559D+06    |proj g|=  4.66920D-01
Cost_fcn eval took     6.76 sec - Cost_fcn= 1.049E+06

At iterate    9    f=  1.04919D+06    |proj g|=  4.67158D-01
Cost_fcn eval took     7.47 sec - Cost_fcn= 8.699E+05

At iterate   10    f=  8.69897D+05    |proj g|=  4.53396D-01
Cost_fcn eval took     6.72 sec - Cost_fcn= 7.248E+05

At iterate   11    f=  7.24834D+05    |proj g|=  4.16026D-01
Cost_fcn eval took     6.67 sec - Cost_fcn= 6.062E+05

At iterate   12    f=  6.06211D+05    |proj g|=  3.86073D-01
Cost_fcn eval took     6.63 sec - Cost_fcn= 5.101E+05

At iterate   13    f=  5.10105D+05    |proj g|=  3.64190D-01
Cost_fcn eval took     8.07 sec - Cost_fcn= 3.670E+05

At iterate   14    f=  3.67021D+05    |proj g|=  4.57874D-01
Cost_fcn eval took     6.98 sec - Cost_fcn= 3.197E+05

At iterate   15    f=  3.19696D+05    |proj g|=  3.77206D-01
Cost_fcn eval took     7.10 sec - Cost_fcn= 2.863E+05

At iterate   16    f=  2.86255D+05    |proj g|=  3.50054D-01
Cost_fcn eval took     7.40 sec - Cost_fcn= 2.714E+05

At iterate   17    f=  2.71439D+05    |proj g|=  2.27850D-01
Cost_fcn eval took     7.36 sec - Cost_fcn= 2.471E+05

At iterate   18    f=  2.47064D+05    |proj g|=  3.08305D-01
Cost_fcn eval took     6.76 sec - Cost_fcn= 2.070E+05

At iterate   19    f=  2.06996D+05    |proj g|=  3.35145D-01
Cost_fcn eval took     6.63 sec - Cost_fcn= 1.551E+05

At iterate   20    f=  1.55079D+05    |proj g|=  3.55766D-01

           * * *

Tit   = total number of iterations
Tnf   = total number of function evaluations
Tnint = total number of segments explored during Cauchy searches
Skip  = number of BFGS updates skipped
Nact  = number of active bounds at final generalized Cauchy point
Projg = norm of the final projected gradient
F     = final function value

           * * *

   N    Tit     Tnf  Tnint  Skip  Nact     Projg        F
37488     20     32  22796     0    76   3.558D-01   1.551D+05
  F =   155079.33658362224     

STOP: TOTAL NO. of ITERATIONS REACHED LIMIT                 
Iterative inversion took :- 00:04:30
2024-05-24 12:38:58,076 - distributed.scheduler - ERROR - Removing worker 'tcp://127.0.0.1:46207' caused the cluster to lose scattered data, which can't be recovered: {'t0', 'shape', 'tn', 'model_name', 'dt', 'f0', 'origin', 'parfile_path', 'shotfile_path', 'spacing', 'nbl', 'dtype', 'rev_op', 'pointwise_op', 'solver', 'space_order'} (stimulus_id='handle-worker-cleanup-1716554338.0766315')
python3 fwi_marmousi2_pyrol_trillinos_daskcluster.py
Running fwi ...

L-Secant-B Line-Search Method (Type B, Bound Constraints)
  iter  value          gnorm          snorm          LSpar          #fval     #grad     #proj     iterCG    flagCG    
  0     9.731758e+06   5.290107e+01   ---            1.000000e+00   1         1         2         ---       ---       
  1     8.409304e+06   2.966844e+01   4.831089e-01   7.812500e-03   9         2         11        0         0         
  2     7.392617e+06   3.098177e+01   1.836908e-01   1.000000e+00   10        3         22        1         0         
  3     6.072640e+06   3.763823e+01   3.350746e-01   1.000000e+00   11        4         27        1         0         
  4     4.824638e+06   4.469295e+01   4.384678e-01   1.000000e+00   12        5         32        1         2         
  5     4.370995e+06   2.716177e+01   1.252939e-01   1.000000e+00   13        6         37        1         2         
  6     4.128030e+06   3.081551e+01   8.103123e-02   1.000000e+00   14        7         42        1         2         
  7     2.719162e+06   2.643041e+01   5.977432e-01   1.000000e+00   15        8         48        1         2         
  8     2.410463e+06   2.931974e+01   1.335843e-01   1.000000e+00   16        9         52        1         2         
  9     2.268405e+06   2.334232e+01   6.713458e-02   1.000000e+00   17        10        57        1         2         
  10    2.087515e+06   2.255981e+01   9.248706e-02   1.000000e+00   18        11        62        1         2         
  11    1.547560e+06   3.068538e+01   3.342841e-01   1.000000e+00   19        12        68        1         2         
  12    1.466858e+06   1.777505e+01   4.734497e-02   1.000000e+00   20        13        72        1         2         
  13    1.406804e+06   1.850941e+01   4.150382e-02   1.000000e+00   21        14        77        1         2         
  14    1.118984e+06   2.296888e+01   2.381057e-01   1.000000e+00   22        15        83        1         2         
  15    1.072215e+06   2.146037e+01   4.733508e-02   1.000000e+00   23        16        87        1         2         
  16    1.040634e+06   1.485732e+01   2.652437e-02   1.000000e+00   24        17        92        1         2         
  17    1.013475e+06   1.468449e+01   2.328420e-02   1.000000e+00   25        18        97        1         2         
  18    8.250006e+05   1.873156e+01   1.802607e-01   1.000000e+00   26        19        103       1         2         
  19    8.022595e+05   1.683758e+01   3.220533e-02   1.000000e+00   27        20        107       1         2         
  20    7.755471e+05   1.198507e+01   2.535021e-02   1.000000e+00   28        21        112       1         2         
Optimization Terminated with Status: Iteration Limit Exceeded
python3 inversion_script.py shot_control_inversion_sotb
Running fwi ...
Cost_fcn eval took     9.50 sec - Cost_fcn= 9.732E+06
Cost_fcn eval took     6.70 sec - Cost_fcn= 1.040E+08
Cost_fcn eval took     6.60 sec - Cost_fcn= 9.994E+07
Cost_fcn eval took     6.59 sec - Cost_fcn= 9.161E+07
Cost_fcn eval took     6.99 sec - Cost_fcn= 7.360E+07
Cost_fcn eval took     7.03 sec - Cost_fcn= 5.343E+07
Cost_fcn eval took     6.67 sec - Cost_fcn= 4.047E+07
Cost_fcn eval took     6.82 sec - Cost_fcn= 2.542E+07
Cost_fcn eval took     7.02 sec - Cost_fcn= 1.440E+07
Cost_fcn eval took     6.95 sec - Cost_fcn= 8.016E+06
Cost_fcn eval took     6.81 sec - Cost_fcn= 8.005E+06
Cost_fcn eval took     6.70 sec - Cost_fcn= 7.914E+06
Cost_fcn eval took     6.84 sec - Cost_fcn= 7.309E+06
Cost_fcn eval took     6.94 sec - Cost_fcn= 5.941E+06
Cost_fcn eval took     6.90 sec - Cost_fcn= 5.692E+06
Cost_fcn eval took     6.74 sec - Cost_fcn= 6.512E+06
Cost_fcn eval took     6.21 sec - Cost_fcn= 4.761E+06
Cost_fcn eval took     6.51 sec - Cost_fcn= 4.121E+06
Cost_fcn eval took     6.61 sec - Cost_fcn= 3.400E+06
Cost_fcn eval took     6.73 sec - Cost_fcn= 2.596E+06
Cost_fcn eval took     6.72 sec - Cost_fcn= 1.733E+06
Cost_fcn eval took     6.46 sec - Cost_fcn= 1.349E+06
Cost_fcn eval took     6.22 sec - Cost_fcn= 1.288E+06
Cost_fcn eval took     6.50 sec - Cost_fcn= 1.183E+06
Cost_fcn eval took     6.58 sec - Cost_fcn= 1.173E+06
Cost_fcn eval took     6.71 sec - Cost_fcn= 1.162E+06
Cost_fcn eval took     7.06 sec - Cost_fcn= 1.209E+06
Cost_fcn eval took     7.02 sec - Cost_fcn= 7.589E+05
Cost_fcn eval took     7.06 sec - Cost_fcn= 7.129E+05
Cost_fcn eval took     7.02 sec - Cost_fcn= 4.281E+05
Cost_fcn eval took     7.20 sec - Cost_fcn= 5.054E+05
Cost_fcn eval took     6.42 sec - Cost_fcn= 3.990E+05
Cost_fcn eval took     7.31 sec - Cost_fcn= 3.794E+05
Cost_fcn eval took     6.96 sec - Cost_fcn= 3.601E+05
Cost_fcn eval took     6.75 sec - Cost_fcn= 3.378E+05
Iterative inversion took :- 00:04:33
END OF TEST
FINAL iterate is :  [0.44444445 0.44444445 0.44444445 ... 0.0743812  0.07149379 0.06978292]
See the convergence history in iterate_LBFGS.dat
python3 inversion_script.py shot_control_inversion_nlopt
Running fwi ...
 Iteration    Function Val         norm(g)
Cost_fcn eval took     9.38 sec - Cost_fcn= 9.732E+06
         1     9.73176e+06     1.84245e+02
Cost_fcn eval took     6.61 sec - Cost_fcn= 2.303E+07
         2     2.30265e+07     4.06681e+02
Cost_fcn eval took     6.85 sec - Cost_fcn= 9.227E+06
         3     9.22650e+06     1.89238e+02
Cost_fcn eval took     6.67 sec - Cost_fcn= 3.064E+07
         4     3.06386e+07     4.38373e+02
Cost_fcn eval took     6.37 sec - Cost_fcn= 9.338E+06
         5     9.33806e+06     1.61961e+02
Cost_fcn eval took     6.00 sec - Cost_fcn= 9.225E+06
         6     9.22467e+06     1.89086e+02
Cost_fcn eval took     6.70 sec - Cost_fcn= 6.797E+06
         7     6.79651e+06     1.61567e+02
Cost_fcn eval took     6.65 sec - Cost_fcn= 6.406E+06
         8     6.40554e+06     2.18455e+02
Cost_fcn eval took     6.96 sec - Cost_fcn= 5.882E+06
         9     5.88231e+06     1.77999e+02
Cost_fcn eval took     7.08 sec - Cost_fcn= 4.255E+06
        10     4.25493e+06     1.02999e+02
Cost_fcn eval took     7.13 sec - Cost_fcn= 4.240E+06
        11     4.24012e+06     1.02416e+02
Cost_fcn eval took     7.12 sec - Cost_fcn= 3.858E+06
        12     3.85843e+06     9.05354e+01
Cost_fcn eval took     7.57 sec - Cost_fcn= 3.697E+06
        13     3.69661e+06     8.60576e+01
Cost_fcn eval took     6.96 sec - Cost_fcn= 3.626E+06
        14     3.62589e+06     8.45011e+01
Cost_fcn eval took     7.57 sec - Cost_fcn= 3.620E+06
        15     3.62012e+06     8.43682e+01
Cost_fcn eval took     8.44 sec - Cost_fcn= 3.482E+06
        16     3.48191e+06     8.17255e+01
Cost_fcn eval took     6.92 sec - Cost_fcn= 3.410E+06
        17     3.41048e+06     8.03531e+01
Cost_fcn eval took     7.29 sec - Cost_fcn= 3.231E+06
        18     3.23117e+06     7.72018e+01
Cost_fcn eval took     7.24 sec - Cost_fcn= 3.096E+06
        19     3.09552e+06     7.49269e+01
Cost_fcn eval took     6.55 sec - Cost_fcn= 2.832E+06
        20     2.83249e+06     7.04207e+01
Cost_fcn eval took     6.78 sec - Cost_fcn= 2.697E+06
        21     2.69723e+06     6.81168e+01
Cost_fcn eval took     7.23 sec - Cost_fcn= 2.650E+06
        22     2.64997e+06     6.72629e+01
Cost_fcn eval took     7.22 sec - Cost_fcn= 2.593E+06
        23     2.59312e+06     6.62590e+01
Cost_fcn eval took     7.05 sec - Cost_fcn= 2.557E+06
        24     2.55732e+06     6.57444e+01
Cost_fcn eval took     6.81 sec - Cost_fcn= 2.515E+06
        25     2.51548e+06     6.49666e+01
Cost_fcn eval took     7.38 sec - Cost_fcn= 2.400E+06
        26     2.40029e+06     6.36432e+01
Cost_fcn eval took     8.37 sec - Cost_fcn= 2.346E+06
        27     2.34640e+06     6.24542e+01
Cost_fcn eval took     6.92 sec - Cost_fcn= 2.281E+06
        28     2.28138e+06     6.14875e+01
Cost_fcn eval took     6.88 sec - Cost_fcn= 2.173E+06
        29     2.17303e+06     6.00497e+01
Cost_fcn eval took     7.09 sec - Cost_fcn= 2.152E+06
        30     2.15206e+06     5.96543e+01
Cost_fcn eval took     6.88 sec - Cost_fcn= 2.142E+06
        31     2.14197e+06     5.95280e+01
Cost_fcn eval took     6.47 sec - Cost_fcn= 2.118E+06
        32     2.11807e+06     5.90464e+01
Cost_fcn eval took     7.01 sec - Cost_fcn= 2.114E+06
        33     2.11441e+06     5.90031e+01
Cost_fcn eval took     6.86 sec - Cost_fcn= 2.102E+06
        34     2.10188e+06     5.87821e+01
Cost_fcn eval took     6.77 sec - Cost_fcn= 2.024E+06
        35     2.02366e+06     5.76671e+01
Iterative inversion took :- 00:04:56
END OF TEST
minimum value =  2023663.4048203537
result code =  5
```

There you have it ✌️ 

## Data

This repository uses data from the SEG Open Data collection, specifically the [Elastic Marmousi model](https://wiki.seg.org/wiki/AGL_Elastic_Marmousi). The data has been resampled for use in this project. The original data is provided by the Allied Geophysical Laboratory of the University of Houston and it is licensed under the Creative Commons Attribution 4.0 International License. You can download the original data from the following link:

[Elastic Marmousi Model Data](https://s3.amazonaws.com/open.source.geoscience/open_data/elastic-marmousi/elastic-marmousi-model.tar.gz)

## License Information
Data License

The resampled data used in this repository is derived from the Elastic Marmousi model data, which is licensed under the Creative Commons Attribution 4.0 International License. For more information about the license, please visit: [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/)

Code License

The code in this repository is licensed under the Apache License 2.0. You are free to use, modify, and distribute the code under the terms of this license. For the full text of the license, please visit: [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
