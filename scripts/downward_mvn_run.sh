#!/bin/bash
#$1=${ordered_content[@]}
module=$1
testName=$2
starting_boundary=$3
currentDir=$4
line=$5 #Only to outting 
delay=$6
threshold=$7
echo "threshold=$threshold"

test_class_name=$(echo $starting_boundary | rev | cut -d'#' -f2 | cut -d'$' -f2 | cut -d'/' -f1 | rev)
test_class=$(find -name "${test_class_name}.java")
#echo $1,$2,$3,$4,$5,$6,$7
flag=0
#Yielding_dir="$currentDir/YIELDING_Point_StackTrace"
logs_dir="$currentDir/logs"
Results="$currentDir/Results-Barrier"

mvn test -pl $module -Dtest="$testName" -DsearchMethodEndLine="search" -DCodeToIntroduceVariable="$starting_boundary"  &> "$logs_dir/log_searchForMethodEndLine_${testName}" # For getting the END line-number of a method
sml_file=$(find $module -name "SearchedMethodEndLine.txt")
#echo ${sml_file}
containing_method_name=$(cat ${sml_file}) #to get methodName and lineNumber
#echo "$yield_item,$containing_method_name"
echo "$line,containing method-name=$containing_method_name" >> "$currentDir/Containing-Method.csv"
if [[ $containing_method_name == "null" ]]; then
    continue
fi


#echo $starting_boundary
end_line=$(echo $containing_method_name | cut -d'#' -f2)
delay_update_yield_flag=0
cls=$(echo "$starting_boundary" | cut -d'#' -f1)
starting_line=$(($(echo "$starting_boundary" | cut -d'#' -f2) + 1))
#
#method_only=$(echo $containing_method_name | cut -d'#' -f1 | rev | cut -d'.' -f1 | rev)
#if [[ $containing_method_name == "run" ]]; then
    #IFS=',' read -r outer_method_name start_line end_line <<< $(python3 find_outer_meth.py "$test_class" "$starting_line")
    #
    ## Use the captured values
    #echo "Outer method name: $outer_method_name"
    #echo "Start line: $start_line"
    #echo "End line: $end_line"
#fi
#exit
starting_line=443
end_line=446
echo $starting_line, $end_line

#break
for ((ln=$starting_line; ln <= $end_line; ln++)); do  # Going backward
    each_line_of_yield_item="$cls#$ln"  
    echo "mvn test -pl $module -Dtest="$testName" -Ddelay=$delay -DCodeToIntroduceVariable=$starting_boundary -DYieldingPoint="$each_line_of_yield_item""
    timeout 3m mvn test -pl $module -Dtest="$testName" -Ddelay=$delay -DCodeToIntroduceVariable=$starting_boundary -DYieldingPoint="$each_line_of_yield_item" -Dthreshold="$threshold"  &> "$logs_dir/log_${testName}_${each_line_of_yield_item}"
    duy_file=$(find $module -name "FlagDelayANDUpdateANDYielding.txt")
    echo "each_line_of_yield_item=$each_line_of_yield_item,${duy_file}"
    delay_happens=$(grep -r  "Delay=true"  $duy_file | wc -l)
    update_happens=$(grep -r "Update=true" $duy_file | wc -l)
    yield_happens=$(grep -r "Yield=true" $duy_file | wc -l)
    if [[ ${delay_happens} -gt 0 &&  ${update_happens} -gt 0  &&  ${yield_happens} -gt 0 ]]; then # because we should not consider any test pass if we do not inject delay, update and yield together. If anything is missing, that is not a accurate fixing.
        delay_update_yield_flag=1
        no_fail_count=$(grep -r "Tests run: 1, Failures: 0, Errors: 0" "$logs_dir/log_${testName}_${each_line_of_yield_item}" | wc -l)
         
        if [[ ${no_fail_count} -gt 0 ]]; then
            echo -n "$(echo $line | cut -d',' -f1-5),$each_line_of_yield_item,$threshold" >> "$Results/Result.csv"
            flag=1
            break
        fi
   fi
done
echo "flag=$flag"
