#!/usr/bin/env bash
if [[ $1 == "" || $2 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    echo "arg2 - relative path to the output file (eg. Result/output.csv)"
    exit
fi

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

inputProj=$currentDir"/projects"
trace_dir="$currentDir/traces"
slug=$1
module=$2
testName_with_dot=$3
testName="${testName_with_dot%.*}#${testName_with_dot##*.}"
id=$4
#JMVNOPTIONS="-Dcassandra.start_native_transport=false \
#             -Dsigar.sigar_enabled=false"
JMVNOPTIONS=""
cd $inputProj/$slug
mvn clean install -pl $module  -am -DskipTests
timeout 10m mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName -Dcheckstyle.skip=true >  "$currentDir/logs-to-reproduce/$testName-con-after-changedCode-$id.txt" 2>/dev/null
bugCount=$(grep -ic -E 'Errors: 1|Failures: 1' "$currentDir/logs-to-reproduce/$testName-con-after-changedCode-$id.txt")
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

