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

cd $inputProj/$slug
#echo "mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName -Dcheckstyle.skip=true"
#exit
timeout 5m mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName -Dcheckstyle.skip=true >  "$currentDir/logs-to-reproduce/$testName-con-after-changedCode-$id.txt"
bugCount=$(grep -ic -E 'Errors: 1|Failures: 1' "$currentDir/logs-to-reproduce/$testName-con-after-changedCode-$id.txt")
if [[ $bugCount -gt 0  ]]; then
    echo "Failure found."
else
    echo "Failure not found."
    #git stash
    #git checkout $(find -name "*.java")
    git checkout -- '**/*.java'

fi

