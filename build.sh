#!/bin/bash

DOCKERHUB=false
DOCKER_BUILD_OPTIONS=""
STRGSW_BUILD_OPTIONS=""

#======================================================================#

# if published to dockerhub, squash image into one layer
if $DOCKERHUB; then
  DOCKER_BUILD_OPTIONS=$DOCKER_BUILD_OPTIONS" --squash"
fi

# if CPU support AES-NI use AES-NI plugin
if grep aes /proc/cpuinfo >> /dev/null; then 
  STRGSW_BUILD_OPTIONS=$STRGSW_BUILD_OPTIONS"--enable-aesni"
fi

docker build $DOCKER_OPTIONS --build-arg BUILD_OPTIONS="$STRGSW_BUILD_OPTIONS" -t griffinplus/strongswan .
