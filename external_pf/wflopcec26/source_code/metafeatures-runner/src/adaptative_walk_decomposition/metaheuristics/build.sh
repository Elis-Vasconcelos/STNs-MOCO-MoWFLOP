#!/bin/bash

mkdir dataset

for D in {A..J}; do
    mkdir dataset/$D
    mkdir dataset/$D/decomposition_based
    mkdir dataset/$D/decomposition_based/random_walk
    mkdir dataset/$D/decomposition_based/adaptative_walk
    mkdir dataset/$D/pareto_based
    mkdir dataset/$D/pareto_based/random_walk
    mkdir dataset/$D/pareto_based/adaptative_walk
done

r=(0.05 0.1 0.25 0.5 1.0)
l=(5 10 25 50 100)

# Create subdirectories for decomposition_based/adaptative_walk
for D in {A..J}; do
    for L in "${l[@]}"; do
        mkdir dataset/$D/decomposition_based/adaptative_walk/l$L
    done
done

# Create subdirectories for decomposition_based/random_walk
for D in {A..J}; do
    for L in "${l[@]}"; do
        for R in "${r[@]}"; do
            mkdir dataset/$D/decomposition_based/random_walk/l$L_r$R
        done
    done
done

# Create subdirectories for pareto_based/adaptative_walk
for D in {A..J}; do
    for L in "${l[@]}"; do
        mkdir dataset/$D/pareto_based/adaptative_walk/l$L
    done
done

# Create subdirectories for pareto_based/random_walk
for D in {A..J}; do
    for L in "${l[@]}"; do
        for R in "${r[@]}"; do
            mkdir dataset/$D/pareto_based/random_walk/l$L_r$R
        done
    done
done

echo "Directory structure created successfully!"

for D in {A..J}; do
    for L in "${l[@]}"; do
        for R in "${r[@]}"; do
            echo "Executing RW_decomposition_main with: A $L $R"
            # Here, you would execute your command:
            ./RW_decomposition_main A $L $R
        done
    done
done

read -p "Press Enter to continue..."