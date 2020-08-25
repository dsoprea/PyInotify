#!/bin/bash -ex

python -m nose -s -v --with-coverage --cover-package=workflow `pwd`/tests
