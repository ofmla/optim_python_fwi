# from https://stackoverflow.com/a/52582319
# Choose and name our temporary image
FROM continuumio/miniconda3:23.3.1-0 as intermediate
LABEL stage=intermediate

COPY get_devito.sh /opt/src/scripts/get_devito.sh
RUN /opt/src/scripts/get_devito.sh
    
# Choose the base image for our final image
FROM continuumio/miniconda3:23.3.1-0

# Install dependencies in one go to reduce the number of layers
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y \
        sudo gcc g++ gfortran make unzip libhdf5-dev libpcre2-dev liblapack-dev libblas-dev cmake pkgconf wget vim && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
   
# Install SWIG and clean up unnecessary files
RUN wget --no-check-certificate 'https://sourceforge.net/projects/swig/files/swig/swig-4.2.1/swig-4.2.1.tar.gz' -O swig-4.2.1.tar.gz && \
    tar -xvf swig-4.2.1.tar.gz && \
    cd swig-4.2.1 && \
    ./configure --prefix=/usr/local && \
    make -j4 && \
    sudo make install && \
    cd .. && \
    rm -rf swig-4.2.1 swig-4.2.1.tar.gz

# Set the working directory in the container
ENV APP_HOME /app
WORKDIR $APP_HOME
RUN mkdir devito

# Copy the contents of devito/ from our `intermediate` container
# and install python packages (devito is installed in development mode)
COPY --from=intermediate /devito/ ./devito
RUN cd devito && sed -i '8c codepy>=2019.1,<2025' requirements.txt \
    && pip install -e . pytest scipy==1.14.1 matplotlib \
    && pip install dask_jobqueue segyio sotb_wrapper h5py PyYAML --no-compile --no-cache-dir --config-settings="build_ext=-j4" \
    && pip cache purge \
    && cd ..

# Install NLopt
RUN wget --no-check-certificate 'https://github.com/stevengj/nlopt/archive/v2.7.1.tar.gz' \
    && tar -xvf v2.7.1.tar.gz \
    && cd nlopt-2.7.1 \
    && cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr/local -DPython_EXECUTABLE=$CONDA_DIR/envs/base/bin/python -DSWIG_DIR:string=/usr/local/share/swig/4.2.1 -DSWIG_EXECUTABLE:string=/usr/local/bin/swig -DNLOPT_GUILE=OFF -DNLOPT_MATLAB=OFF -DNLOPT_OCTAVE=OFF \
    && cmake --build build -j4 \
    && cmake --install build \
    && cd \
    && rm -rf nlopt-2.7.1 nlopt-2.7.1.tar.gz

# Install PyROL
RUN wget --no-check-certificate "https://www.sandia.gov/app/uploads/sites/232/2024/12/pyrol-2024.9.13.13.29develop.4795e2b0.tar.gz" \
    && tar -xvf pyrol-2024.9.13.13.29develop.4795e2b0.tar.gz \
    && cd pyrol-2024.9.13.13.29+develop.4795e2b0 \
    && pip install . -v --config-settings=build.tool-args=-j4 \
    && cd \
    && rm -rf pyrol-2024.9.13.13.29+develop.4795e2b0 pyrol-2024.9.13.13.29develop.4795e2b0.tar.gz

# Copy all files and directories from the build context (.) into the app directory
COPY . $APP_HOME
