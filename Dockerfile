FROM ubuntu:24.04@sha256:04f510bf1f2528604dc2ff46b517dbdbb85c262d62eacc4aa4d3629783036096

# Prevent prompts while installing via Apt
ENV DEBIAN_FRONTEND="noninteractive"

# Allow us to install via PIP
ENV PIP_BREAK_SYSTEM_PACKAGES=1

RUN apt-get update && apt-get install -y python3 python3-pip

ADD ./ /project

WORKDIR /project

RUN ["pip3", "install", "-e", "."]
RUN ["pip3", "install", "-r", "requirements-testing.txt"]

CMD ["python3", "-m", "nose", "-s", "-v", "tests"]
