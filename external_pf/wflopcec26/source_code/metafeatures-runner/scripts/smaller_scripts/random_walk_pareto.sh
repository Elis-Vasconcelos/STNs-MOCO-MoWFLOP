#!/bin/bash

r=("0.05" "0.1" "0.25" "0.5" "1.0")
l=("5" "10" "25" "50" "100")

instance="${1:-A}"

for L in "${l[@]}"; do
    for R in "${r[@]}"; do
        echo "Executing random_walk_pareto with: $instance $L $R"

        log_file="../dataset/$instance/pareto_based/random_walk/l${L}_r${R}/log.txt"
        
        {
            echo "============================== LOG =============================="

            { time ./exe/random_walk_pareto "$instance" "$L" "$R"; } 2>&1

            echo "================================================================="
        } > "$log_file" 2>&1
    done
done
