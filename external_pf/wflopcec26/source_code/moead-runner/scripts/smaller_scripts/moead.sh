#!/bin/bash

instance="${1:-A}" 
run="${2:-1}"

echo "Executing moead with: Instance=$instance, Run=$run"

log_dir="../dataset/moead/$instance/$run"
log_file="$log_dir/log.txt"

path="../dataset/moead/$instance/$run/"

mkdir -p "$log_dir"

{
    echo "============================== LOG =============================="
    echo "Instance: $instance"
    echo "Run: $run"
    echo "Metaheuristic: MOEA/D"
    echo "Execution started at: $(date)"

    { time ./exe/moead "$instance" "$path"; } 2>&1

    echo "Execution ended at: $(date)"
    echo "================================================================="
} > "$log_file" 2>&1
