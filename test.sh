#!/bin/bash

# This is a test script that populates the output_directory with touched files
output_dir=$1

mkdir -p $output_dir/{Direct1/sub1,Direct2/sub1/sub2,Direct3/sub1/sub2/sub3}

cd $output_dir

for dir in Direct1/sub1 Direct2/sub1/sub2 Direct3/sub1/sub2/sub3; do
    touch $dir/file.txt
done