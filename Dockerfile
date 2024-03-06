FROM ubuntu:22.04

LABEL org.opencontainers.image.source=https://github.com/Sage-Bionetworks-Workflows/nf-synapse-challenge

#install apt-get dependencies
RUN apt-get update -y && apt-get upgrade -y && apt-get install -y \
    bash \
    curl \
    gpg \
    python3 \
    python3-pip

#Add the official Docker (apt-get) repository
RUN mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
RUN echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    focal stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null

#install docker
RUN apt-get update -y && apt-get install -y \
    docker-ce

# Install Python libraries using pip
RUN pip3 install \
    docker \
    synapseclient
