#!/bin/bash

set -euo pipefail

mkdir -p bin

# Publish LambdaNet8 project and package it into a zip file
dotnet publish LambdaNet8 --configuration Release --framework net8.0 --runtime linux-x64
zip -j bin/LambdaNet8.zip LambdaNet8/bin/Release/net8.0/linux-x64/publish/*

#publish_and_package() {
#	local lambda_project="$1"
#	local output_zip="$2"
#
#	dotnet publish "$lambda_project" --configuration "Release" --framework "net8.0" --runtime linux-x64
#	rm -f "bin/release/net8.0/$output_zip"
#	temp_dir=$(mktemp -d /tmp/bootstrap.XXXXXX)
#	temp_file="$temp_dir/bootstrap"
#	cp "src/$lambda_project/bin/Release/net8.0/linux-x64/publish/$lambda_project" "$temp_file"
#	mkdir -p bin
#	zip "bin/$output_zip" -j "$temp_file"
#	rm -rf "$temp_dir"
#}
#
#publish_and_package \
#	"LambdaNet8" \
#	"authorizer.zip"
