# Use the requested NVIDIA CUDA base
FROM nvidia/cuda:12.0.1-cudnn8-devel-ubuntu22.04

# Avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install Java 8 (OpenJDK) and dependencies
RUN apt-get update && apt-get install -y \
    openjdk-8-jdk \
    wget \
    git \
    ca-certificates \
    curl \
    python3 \
    python3-pip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Maven 3.6.3 manually
# We download the binary to ensure it's exactly 3.6.3 and set the home path
RUN wget https://archive.apache.org/dist/maven/maven-3/3.6.3/binaries/apache-maven-3.6.3-bin.tar.gz -P /tmp \
    && tar xf /tmp/apache-maven-3.6.3-bin.tar.gz -C /usr/share \
    && mv /usr/share/apache-maven-3.6.3 /usr/share/maven \
    && ln -s /usr/share/maven/bin/mvn /usr/bin/mvn

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p /opt/conda && \
        rm miniconda.sh 
 
ENV PATH="/opt/conda/bin:$PATH"


RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

# Create a Conda environment for Python 3.8.5, as per your README
# We'll then use pip within this environment.
RUN conda create -n tdrepro python=3.8.5 -y && \
    conda clean --all -f -y

# 3. Set Environment Variables
ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
ENV MAVEN_HOME=/usr/share/maven
ENV PATH="${MAVEN_HOME}/bin:${PATH}"

# 4. Install Python requirements
# Assuming requirements.txt is in the same directory as the Dockerfile during build
COPY requirements.txt /tmp/requirements.txt
#RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
RUN conda run -n tdrepro pip install --no-cache-dir -r /tmp/requirements.txt

# Set the working directory inside the container
WORKDIR /NOD-Test-Repair

# Verify installations
RUN java -version && mvn -version
