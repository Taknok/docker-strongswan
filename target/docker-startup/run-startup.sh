#!/bin/bash

# determine the absolute path of the executing script and the directory it is in
SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIRECTORY_PATH=$(dirname "$SCRIPT_PATH")

# call startup scripts
for script_dir in `find "$SCRIPT_DIRECTORY_PATH" -type d -iname "*.startup" | sort -f`; do
    script="$script_dir/startup"
    if [ -f "$script" ]; then
        chmod ug+x "$script"
        "$script" "$@"
        exit_code=$?
        if [ $exit_code -ne 0 ]; then
            exit $exit_code
        fi
    fi
done
