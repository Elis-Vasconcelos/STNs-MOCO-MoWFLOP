#!/bin/bash

main_dir="../dataset"

if [[ -d "$main_dir" ]]; then
    echo "The directory structure has already been created."
    exit 0
fi

mkdir -p "$main_dir"

r=("0.05" "0.1" "0.25" "0.5" "1.0")
l=("5" "10" "25" "50" "100")

echo "---------- Creating the directory structure... ----------"

for D in {A..J} {0..500} {501..505}; do

    mkdir -p "$main_dir/$D/decomposition_based/random_walk"
    mkdir -p "$main_dir/$D/decomposition_based/adaptative_walk"
    mkdir -p "$main_dir/$D/pareto_based/random_walk"
    mkdir -p "$main_dir/$D/pareto_based/adaptative_walk"

    for R in "${r[@]}"; do
        mkdir -p "$main_dir/$D/decomposition_based/adaptative_walk/r$R"
    done

    for L in "${l[@]}"; do
        for R in "${r[@]}"; do
            mkdir -p "$main_dir/$D/decomposition_based/random_walk/l${L}_r${R}"
        done
    done

    for R in "${r[@]}"; do
        mkdir -p "$main_dir/$D/pareto_based/adaptative_walk/r$R"
    done

    for L in "${l[@]}"; do
        for R in "${r[@]}"; do
            mkdir -p "$main_dir/$D/pareto_based/random_walk/l${L}_r${R}"
        done
    done
done

echo "---------- Directory structure created successfully! ----------"
