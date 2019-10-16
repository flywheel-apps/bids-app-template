#!/bin/bash

# This is a test script that populates the output_directory with touched files
output_dir=$1

mkdir -p $output_dir/{Direct1/sub1,Direct2/sub1/sub2,Direct3/sub1/sub2/sub3}

cd $output_dir

for dir in Direct1/sub1 Direct2/sub1/sub2 Direct3/sub1/sub2/sub3; do
    touch $dir/file.txt
done

for t in 1 1 1 1 0.5 0.25; do
    sleep $t 
    echo "that was $t seconds"
done

echo "ls "
ls

if [ -f "input/make_me_barf" ]; then
    echo "input/make_me_barf exists, so now I generate an error"
    cd no_such_directory
fi


echo "test.sh is done"
