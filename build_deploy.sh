#!/bin/bash

rm -rf build dist kraky.egg-info

python setup.py sdist bdist_wheel

twine check dist/*

twine upload --repository testpypi dist/*

twine upload dist/*