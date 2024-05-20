# from https://stackoverflow.com/a/52582319
# Choose and name our temporary image
FROM continuumio/miniconda3:23.3.1-0 as intermediate
LABEL stage=intermediate

# Take an SSH key as a build argument.
ARG SSH_KEY

# 1. Create the SSH directory.
# 2. Populate the private key file.
# 3. Set the required permissions.
# 4. Add github to our list of known hosts for ssh.
RUN mkdir -p /root/.ssh/ && \
    echo "$SSH_KEY" > /root/.ssh/id_rsa && \
    chmod -R 600 /root/.ssh/ && \
    ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts
    
# Clone devito repository 
RUN git clone https://github.com/devitocodes/devito.git \
    && cd devito \
    && git branch specific-commit-branch e6cd0b0ab \
    && git switch specific-commit-branch
    
# Choose the base image for our final image
FROM continuumio/miniconda3:23.3.1-0

# Install dependencies in one go to reduce the number of layers
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y \
        sudo gcc g++ gfortran make unzip libhdf5-dev libpcre2-dev liblapack-dev libblas-dev cmake pkgconf wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    
# Install SWIG and clean up unnecessary files
RUN wget --no-check-certificate 'https://sourceforge.net/projects/swig/files/latest/download/swig-4.2.1.tar.gz' -O swig-4.2.1.tar.gz && \
    unzip swig-4.2.1.tar.gz && \
    cd swigwin-4.2.1 && \
    ./configure --prefix=/usr/local && \
    make && \
    sudo make install && \
    cd .. && \
    rm -rf swigwin-4.2.1 swig-4.2.1.tar.gz

# Copy devito folder from our `intermediate` container
COPY --from=intermediate /devito .

RUN cd devito

SHELL ["/bin/bash", "-c"]

# create conda environment with Devito, scipy and sotb-wrapper
RUN conda --version \
    && conda init bash \
    && conda create --name devito_e6cd0b0ab \
    && source activate devito_e6cd0b0ab \
    && pip install -e . pytest scipy matplotlib \
    && pip install dask_jobqueue segyio sotb_wrapper h5py \
    && cd
    
# Create and configure the conda environment in one layer
#RUN conda create --name devito_e6cd0b0ab python=3.8 -y && \
#    conda init bash && \
#    echo "source activate devito_e6cd0b0ab" > ~/.bashrc && \
#    /bin/bash -c "source ~/.bashrc && \
#        pip install -e . pytest scipy matplotlib dask_jobqueue segyio sotb_wrapper h5py"

# Install NLopt
RUN wget --no-check-certificate 'https://github.com/stevengj/nlopt/archive/v2.7.1.tar.gz' \
    && tar -xvf v2.7.1.tar.gz \
    && cd nlopt-2.7.1 \
    && cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr/local -DPython_EXECUTABLE=$CONDA_DIR/envs/devito_e6cd0b0ab/bin/python -DSWIG_DIR:string=/usr/local/share/swig/4.2.1 -DSWIG_EXECUTABLE:string=/usr/local/bin/swig -DNLOPT_GUILE=OFF -DNLOPT_MATLAB=OFF -DNLOPT_OCTAVE=OFF \
    && cmake --build build \
    && cmake --install build \
    && cd \
    && rm -rf nlopt-2.7.1 nlopt-2.7.1.tar.gz

# Install PyROL
RUN wget --no-check-certificate "https://www.sandia.gov/app/uploads/sites/232/2024/02/pyrol-0.0.1.tar.gz" \
    && tar -xvf pyrol-0.0.1.tar.gz \
    && cd pyrol-0.0.1 \
    && pip install . \
    && cd \
    && rm -rf pyrol-0.0.1 pyrol-0.0.1.tar.gz

# Set the working directory in the container
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . $APP_HOME