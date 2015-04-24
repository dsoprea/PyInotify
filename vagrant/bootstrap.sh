#!/bin/bash

apt-get update
apt-get install -y python-pip

cd /inotify
python setup.py develop
