#!/usr/bin/env bash

mkdir build_tmp
cp manifest.json build_tmp
cd build_tmp
fw gear upload
cd ..
rm -rf build_tmp
