#!/bin/bash -e

# keep track of the last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting
trap '{ err=$?; >&2 echo "ERROR \"${last_command}\" command failed with exit code $err."; exit $err; } ' EXIT


if [ -f input/make_me_barf ]; then
    echo "input/make_me_barf exists, so now I generate an error"
    cd no_such_directory
else
    echo "I will not generate an error"
fi

# This is a test script that populates the output_directory with touched files
output_dir=$1

mkdir -p $output_dir/{Direct1/sub1,Direct2/sub1/sub2,Direct3/sub1/sub2/sub3}

cd $output_dir

for dir in Direct1/sub1 Direct2/sub1/sub2 Direct3/sub1/sub2/sub3; do
    touch $dir/file.txt
done

for t in 1 1 1 1 1 1 1 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 ; do
    sleep $(( $t * 15 ))
    echo "that was $(( $t * 15 )) seconds"
    /bin/date
    echo "this goes to stderr" >&2
done

echo "ls "
ls


echo "test.sh is done"
