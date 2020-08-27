FROM ubuntu:16.04

RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install nose

ADD ./ /project

WORKDIR /project

RUN pip3 install -e .

CMD python3 -m nose -s -v tests
