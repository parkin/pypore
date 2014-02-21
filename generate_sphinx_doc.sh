#!/bin/bash

## This cleans the current sphinx documentation and autogenerates
## new sphinx documentation.

set -ex

SPHINX_DIR=website/sphinx-docs
SPHINX_SOURCE_DIR=$SPHINX_DIR/source
SPHINX_AUTODOC_DIR=$SPHINX_SOURCE_DIR/autodocs
SOURCE_DIR=src

# remove previous autodocs
rm -rf $SPHINX_AUTODOC_DIR/*

# generate the autodoc stuff
sphinx-apidoc -o $SPHINX_AUTODOC_DIR $SOURCE_DIR -f

# cd to the sphinx dir, clean, then build html
cd $SPHINX_DIR
make clean
make html
