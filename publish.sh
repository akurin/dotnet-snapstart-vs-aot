#!/bin/bash

set -euo pipefail

mkdir -p bin

# Publish LambdaNet8 project and package it into a zip file
dotnet publish LambdaNet8 --configuration Release --framework net8.0 --runtime linux-x64
zip -j bin/LambdaNet8.zip LambdaNet8/bin/Release/net8.0/linux-x64/publish/*

# Publish LambdaNet8Aot project and package it into a zip file
dotnet publish LambdaNet8Aot --configuration Release --framework net8.0 --runtime linux-x64
temp_dir=$(mktemp -d /tmp/bootstrap.XXXXXX)
temp_file="$temp_dir/bootstrap"
cp LambdaNet8Aot/bin/Release/net8.0/linux-x64/publish/LambdaNet8Aot "$temp_file"
zip -j bin/LambdaNet8Aot.zip "$temp_file"
rm -rf "$temp_dir"
