#!/usr/bin/env bash

if [ -e build_tmp ] ; then
  echo "build_tmp exists"
  exit
fi
mkdir build_tmp
echo cp manifest.json build_tmp
cp manifest.json build_tmp
cd build_tmp
echo fw gear upload
fw gear upload
cd ..
rm -rf build_tmp
