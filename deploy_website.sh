#!/bin/bash

set -ex

REPO="https://github.com/parkin1/pypore.git"

DIR=temp-pages-clone
WEBSITE_DIR=website

# update the sphinx documentation
./autogen_sphinx_apidoc.sh

# Delete any existing temporary website clone
rm -rf $DIR

# Clone the current repo into temp folder
git clone $REPO $DIR

# Move working directory into temp folder
cd $DIR

# Checkout and track the gh-pages branch
git checkout -t origin/gh-pages

# Delete everything
rm -rf *

# Copy website files from real repo
cp -R ../$WEBSITE_DIR/* .

# Stage all files in git and create a commit
git add .
git add -u
git commit -m "Website at $(date)"

# Push the new files up to GitHub
git push origin gh-pages

# Delete our temp folder
cd ..
rm -rf $DIR
