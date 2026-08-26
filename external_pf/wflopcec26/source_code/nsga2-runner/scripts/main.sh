#!/bin/bash

script2="./smaller_scripts/nsga2.sh"

batch=("$@")

if [ ${#batch[@]} -eq 0 ]; then
  echo "Error: No instances provided. Pass instances as arguments."
  exit 1
fi

echo "Using batch: ${batch[@]}"

for instance in "${batch[@]}"; do

  for i in {1..20}; do
    log_file="./logs/${instance}.txt"

    echo "Using instance: $instance, Run: $i"
    echo "Appending to log file: $log_file"

    # Appending logs to the file
    {
      echo "Running NSGA-II with instance $instance, Run: $i"
      bash "$script2" "$instance" "$i"

      echo "NSGA-II has been executed for instance: $instance, Run: $i."
      echo "---------------------------------------------"
    } >> "$log_file" 2>&1

    echo "Finished instance: $instance, Run: $i. Logs appended to $log_file."
  done
done

echo "All instances in the batch have been processed."
