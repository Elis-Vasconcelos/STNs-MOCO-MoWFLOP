#!/bin/bash

directories=(
    "./src/comolsd"
)

output_files=(
    "comolsd"
)

destination="./scripts/exe"

mkdir -p "$destination"

for i in "${!directories[@]}"; do
    dir="${directories[$i]}"
    output_file="${output_files[$i]}"

    echo "Accessing directory: $dir"
    cd "$dir" || { echo "Error accessing directory $dir"; exit 1; }

    echo "Running 'make rebuild' on $dir"
    make rebuild || { echo "Error running 'make rebuild' on $dir"; exit 1; }

    echo "Moving generated file ($output_file) to $destination"
    cd ../.. || { echo "Error returning to project root"; exit 1; }
    mv "$dir/$output_file" "$destination" || { echo "Error moving $output_file"; exit 1; }

    echo "File $output_file successfully moved to $destination."
done

echo "Applying executable permissions to executables in $destination"
cd "$destination" || { echo "Error accessing directory $destination"; exit 1; }
for executable in "${output_files[@]}"; do
    if [ -f "$executable" ]; then
        chmod +x "$executable"
        echo "Permissions set for: $executable"
    else
        echo "Executable not found: $executable"
    fi
done

cd .. || { echo "Error returning to './scripts'"; exit 1; }
scripts_dir="./smaller_scripts"
scripts=(
    "create_folders.sh"
    "comolsd.sh"
)

if [[ ! -d "$scripts_dir" ]]; then
    echo "Error: Directory $scripts_dir does not exist."
    exit 1
fi

echo "Applying executable permissions to executables in $scripts_dir"
cd "$scripts_dir" || { echo "Error accessing directory $scripts_dir"; exit 1; }
for script in "${scripts[@]}"; do
    if [[ -f "$script" ]]; then
        chmod +x "$script"
        echo "Permissions set for: $script"
    else
        echo "File not found: $script"
    fi
done

cd .. || { echo "Error returning to './scripts'"; exit 1; }
chmod +x main.sh
echo "Permissions set for: main.sh"

chmod +x batch.sh
echo "Permissions set for: batch.sh"

echo "Make All: Process completed successfully!"
