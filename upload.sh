#!/bin/bash -ex

python3 -m twine upload --repository pypi dist/*
