#!/bin/bash
#$1=${ordered_content[@]}
module=$2
testName=$3
upper_boundary=$4
currentDir=$5
line=$6
delay=$7
threshold=$8
JMVNOPTIONS="$9"
#echo "threshold=$threshold"
flag=0
Yielding_dir="$currentDir/YIELDING_Point_StackTrace"
logs_dir="$currentDir/logs"
Results="$currentDir/Results-Barrier"
#echo "filename,all yield_items=$1"
ordered_content=($(cat "$1"))
#yield_item_flag=0
if [[ -f "$Yielding_dir/already_yielding_point.csv" ]]; then # Removing if already exists
    rm "$Yielding_dir/already_yielding_point.csv"
fi
touch "$Yielding_dir/already_yielding_point.csv"
#echo ${ordered_content[@]}

for yield_item in ${ordered_content[@]}; do #all ordered_items are stacktrace item that found from failure-log
    exists=$(grep -r "$yield_item" "$Yielding_dir/already_yielding_point.csv" | wc -l) 
    if [[ $exists -eq 0 ]]; then #This will indicate that this line is not considered as Yielding point yet, This line will only be executed if to get containing method
        yield_item_flag=1
        #export YIELDING_POINT="$yield_item"  
        echo "$yield_item" >> "$Yielding_dir/already_yielding_point.csv"
        #echo "mvn test -pl $module -Dtest="$testName" -DsearchForMethodName="search" -DCodeToIntroduceVariable="$upper_boundary" -DYieldingPoint="$yield_item""
        #exit
        mvn test ${JMVNOPTIONS} -pl $module -Dtest="$testName" -DsearchForMethodName="search" -DCodeToIntroduceVariable="$upper_boundary" -DYieldingPoint="$yield_item"  &> "$logs_dir/log_searchForMethod_${testName}_${yield_item}" # For getting starting line-number of a method
        sml_file=$(find $module -name "SearchedMethodANDLine.txt")
        #echo ${sml_file}
        containing_method_name=$(cat ${sml_file}) #to get methodName and lineNumber
        #echo "$yield_item,$containing_method_name"
        echo "$line,containing method-name=$containing_method_name" >> "$currentDir/Containing-Method.csv"
        if [[ $containing_method_name == "null" ]]; then
            continue
        fi
        
        start_line=$(echo $containing_method_name | cut -d'#' -f2)
        #echo "StackTrace item=$yield_item,START LINE, st=====$start_line, $yield_item"
        cls=$(echo $yield_item | cut -d'#' -f1) 
        max_line=$(echo $yield_item | cut -d'#' -f2) 
        delay_update_yield_flag=0
        for ((ln=$max_line; ln >= $start_line; ln--)); do  # Going backward
            each_line_of_yield_item="$cls#$ln"  
            timeout 5m mvn test ${JMVNOPTIONS} -pl $module -Dtest="$testName" -Ddelay=$delay -DCodeToIntroduceVariable=$upper_boundary -DYieldingPoint="$each_line_of_yield_item" -Dthreshold="$threshold"  &> "$logs_dir/log_${testName}_${each_line_of_yield_item}_${threshold}"
            duy_file=$(find $module -name "FlagDelayANDUpdateANDYielding.txt")
            #echo ${duy_file}
            delay_happens=$(grep -r  "Delay=true"  $duy_file | wc -l)
            update_happens=$(grep -r "Update=true" $duy_file | wc -l)
            yield_happens=$(grep -r "Yield=true" $duy_file | wc -l)
            if [[ ${delay_happens} -gt 0 &&  ${update_happens} -gt 0  &&  ${yield_happens} -gt 0 ]]; then # because we should not consider any test pass if we do not inject delay, update and yield together. If anything is missing, that is not a accurate fixing.
                delay_update_yield_flag=1
                test_pass=$(grep -r "Tests run: 1, Failures: 0, Errors: 0" "$logs_dir/log_${testName}_${each_line_of_yield_item}_${threshold}" | wc -l)
                 
                if [[ ${test_pass} -gt 0 ]]; then
                    echo -n "$(echo $line | cut -d',' -f1-4),${upper_boundary},$each_line_of_yield_item,$threshold" >> "$Results/Result.csv"
                    flag=1
                    break
                fi
            fi
        done
        if [[ $flag == 1 ]]; then # Indicates that we already find test-pass for a Yielding point; So, we can stop, do not look for other statements of that method 
            break
        fi
    fi
done
echo "flag=$flag"
