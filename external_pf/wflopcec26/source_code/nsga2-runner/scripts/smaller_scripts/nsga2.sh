#!/bin/bash

instance="${1:-A}" 
run="${2:-1}"

echo "Executing NSGA-II with: Instance=$instance, Run=$run"

log_dir="../dataset/nsga2/$instance/$run"
log_file="$log_dir/log.txt"

path="../dataset/nsga2/$instance/$run/"

mkdir -p "$log_dir"

{
    echo "============================== LOG =============================="
    echo "Instance: $instance"
    echo "Run: $run"
    echo "Metaheuristic: NSGA-II"
    echo "Execution started at: $(date)"

    { time ./exe/nsga2 "$instance" "$path"; } 2>&1

    echo "Execution ended at: $(date)"
    echo "================================================================="
} > "$log_file" 2>&1
