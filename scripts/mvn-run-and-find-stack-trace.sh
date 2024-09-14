#!/usr/bin/env bash
if [[ $1 == "" || $2 == "" || $3 == "" || $4 == "" || $5 == "" || $6 == "" || $7 == "" ]]; then
    echo "arg1 - full path to the project Directory(e.g., projects/TooTallNate/Java-WebSocket)"
    echo "arg2 - path to the script directory (e.g., $currentDir)"
    echo "arg3 - delay amount"
    echo "arg4 - Test Name"
    echo "arg5 - proj Name"
    echo "arg6- module Name"
    echo "arg7- Location"
    exit
fi
currentDir=$2
projName=$5
module=$6
#start=$(date +%s.%N)
#cat "$currentDir/Locations/$projName"
#echo "Okay"
#echo $(pwd)
#echo $module
#echo "test=$4"
#echr "delay=$3"
#echo "location=$7"
mvn test -pl $module -Dtest=$4  -Ddelay=$3  -Dlocations=$7 >  "$currentDir/logs/$projName-FlakeDelay.txt"

tt_file=$(echo $4 | sed 's;\[;\\[;g') 

stack_trace_location=$(find . -name "StackTrace-${tt_file}.txt") # Find Stacktrace.txt specifically for multi-module projects 
echo $stack_trace_location
if [[ $8 == "1st" ]]; then # Execute this one only for once
    if [[ $stack_trace_location != "" ]]; then
        echo "I am from mvn-run-and-find-stack-trace"
        mv $stack_trace_location "$currentDir/Locations"
    fi
else # Removing stacktrace if it is not coming from 1st mvn-test run
     rm $stack_trace_location   
fi
