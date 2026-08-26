#!/bin/bash

main_dir="../dataset/comolsd"

if [[ -d "$main_dir" ]]; then
    echo "The directory structure has already been created."
    exit 0
fi

mkdir -p "$main_dir"

echo "------------- Creating the directory structure... -------------"

for D in A; do
    for subdir in {1..20}; do
        mkdir -p "$main_dir/$D/$subdir"
    done
done

echo "---------- Directory structure created successfully! ----------"
