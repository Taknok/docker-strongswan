#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
# set -e

if [ "$1" = 'run' ]; then
    /docker-startup/run-startup.sh "$@"
    if [ $? -ne 0 ]; then exit $?; fi
    chmod 750 /docker-startup/run-app.sh
    exec /docker-startup/run-app.sh
elif [ "$1" = 'run-and-enter' ]; then
    /docker-startup/run-startup.sh "$@"
    if [ $? -ne 0 ]; then exit $?; fi
    chmod 750 /docker-startup/run-app.sh
    export RUN_DOCKER_APP=1
    exec /bin/bash
elif [ $# -gt 0 ]; then
    # parameters were specified
    # => let startup scripts try to process the arguments
    /docker-startup/run-startup.sh "$@"
    rc=$?
    if [ $rc -eq 127 ]; then
        # command not found => try to interpret parameters as regular command
        exec "$@"
    elif [ $rc -ne 0 ]; then
        exit $rc
    fi
fi

