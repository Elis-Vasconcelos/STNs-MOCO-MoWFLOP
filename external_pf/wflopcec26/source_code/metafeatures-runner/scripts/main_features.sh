#!/bin/bash

script1="./smaller_scripts/create_folders.sh"
script2="./smaller_scripts/random_walk_pareto.sh"
script3="./smaller_scripts/random_walk_decomposition.sh"
script4="./smaller_scripts/adaptative_walk_pareto.sh"
script5="./smaller_scripts/adaptative_walk_decomposition.sh"

batch=("$@")

if [ ${#batch[@]} -eq 0 ]; then
  echo "Error: No instances provided. Pass instances as arguments."
  exit 1
fi

for instance in "${batch[@]}"; do
  log_file="./logs/${instance}.log"

  echo "Using instance: $instance"
  echo "Creating log file: $log_file"

  {
    echo "Running script 2 = random_walk_pareto.sh with instance $instance"
    bash "$script2" "$instance"

    echo "Running script 3 = random_walk_decomposition.sh with instance $instance"
    bash "$script3" "$instance"

    echo "Running script 4 = adaptative_walk_pareto.sh with instance $instance"
    bash "$script4" "$instance"

    echo "Running script 5 = adaptive_walk_decomposition.sh with instance $instance"
    bash "$script5" "$instance"

    echo "All scripts have been executed for instance: $instance."
    echo "---------------------------------------------"
  } &> "$log_file"

  echo "Finished instance: $instance. Logs saved to $log_file."
done

echo "All instances in the batch have been processed."
