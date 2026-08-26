#!/bin/bash

main_dir="../dataset/moead"

if [[ -d "$main_dir" ]]; then
    echo "The directory structure has already been created."
    exit 0
fi

mkdir -p "$main_dir"

echo "------------- Creating the directory structure... -------------"

for D in {A..J} {0..500} {501..505}; do
    for subdir in {1..20}; do
        mkdir -p "$main_dir/$D/$subdir"
    done
done

echo "---------- Directory structure created successfully! ----------"
