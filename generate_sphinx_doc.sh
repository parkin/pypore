#!/bin/bash

set -ex

SPHINX_DIR=website/sphinx-docs
SPHINX_SOURCE_DIR=$SPHINX_DIR/source
SPHINX_AUTODOC_DIR=$SPHINX_SOURCE_DIR/autodocs
SOURCE_DIR=src

# remove previous autodocs
rm -
