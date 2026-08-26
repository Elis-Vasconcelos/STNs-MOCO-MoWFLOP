#!/bin/bash

r=("0.05" "0.1" "0.25" "0.5" "1.0")

instance="${1:-A}"

for R in "${r[@]}"; do
    echo "Executing adaptative_walk_decomposition with: $instance $R"

    log_file="../dataset/$instance/decomposition_based/adaptative_walk/r${R}/log.txt"
        
    {
        echo "============================== LOG =============================="

        { time ./exe/adaptative_walk_decomposition "$instance" "$R"; } 2>&1

        echo "================================================================="
    } > "$log_file" 2>&1
done
