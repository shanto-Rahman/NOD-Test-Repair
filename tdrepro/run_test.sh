#!/usr/bin/env bash
#export JAVA_HOME=/home/sr53282/Java/jdk1.8.0_451
if [[ $1 == "" || $2 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    echo "arg2 - relative path to the output file (eg. Result/output.csv)"
    exit
fi

rm -rf ~/.m2/repository/info/archinnov/*
currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

inputProj=$currentDir"/projects"
trace_dir="$currentDir/traces"
slug=$1
module=$2
testName_with_dot=$3
testName="${testName_with_dot%.*}#${testName_with_dot##*.}"
id=$4
#cosine_weight=$5
dir=$5
log_dir="$currentDir/$dir"
if [[ ! -d $log_dir ]]; then
mkdir $log_dir
fi
#echo "$currentDir/logs-to-reproduce/${cosine_weight}/$testName-con-after-changedCode-$id.txt"
#echo "cosine_weight=$cosine_weight"
#JMVNOPTIONS="-Dcassandra.start_native_transport=false \
#             -Dsigar.sigar_enabled=false"
JMVNOPTIONS=""
if [[ $slug == "apache/dubbo" ]]; then
    JMVNOPTIONS="-pl dubbo-dependencies-bom"
fi
cd $inputProj/$slug
if [[ $slug == "javadelight/delight-nashorn-sandbox" ]]; then
    mvn -Dmaven.javadoc.skip=true clean install -pl $module  -am -DskipTests
else
    mvn clean install -pl $module  -am -DskipTests
fi
#echo "mvn clean install -pl $module  -am -DskipTests"
#echo "mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName -Dcheckstyle.skip=true"
timeout 10m mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName -Dcheckstyle.skip=true >  "${log_dir}/$testName-con-after-changedCode-$id.txt" 2>/dev/null
bugCount=$(grep -ic -E 'Errors: 1|Failures: 1' "${log_dir}/$testName-con-after-changedCode-$id.txt")

if [[ $bugCount -gt 0  ]]; then
    git checkout -- '**/*.java'
    echo "Failure found."
    exit 1
else
    echo "Failure not found."
    #git stash
    #git checkout $(find -name "*.java")
    git checkout -- '**/*.java'
    exit 0 
fi

