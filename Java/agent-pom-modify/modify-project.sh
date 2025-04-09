#!/bin/bash

if [[ $1 == "" ]]; then
    echo "arg1 - the path to the project, where high-level pom.xml is"
    exit
fi

project_path=$1

# Check whether passed in argument is in the list of options
list="jacoco"
if [[ $2 == "" || ! $list =~ (^|[[:space:]])$2($|[[:space:]]) ]]; then
    echo "arg2 - configuration option for how to modify; options include [jacoco]"
    exit
fi
flag=$2

crnt=`pwd`
working_dir=`dirname $0`

cd ${project_path}
project_path=`pwd`
cd - > /dev/null

cd ${working_dir}

javac PomFile.java
find ${project_path} -name pom.xml | grep -v "src/" | java PomFile ${flag}
rm -f PomFile.class

cd ${crnt}
