#!/bin/bash
if [[ $1 == "" || $2 == "" ]]; then
    echo "please provide the arguments"
    exit
fi

test_name=$(echo $1 | rev |cut -d'/' -f1 | cut -d'.' -f2- |  rev)
result="Results-Minimizer/${test_name}_Actual_Location.csv"


#result="Results-Minimizer/$1_Actual_Location.csv"
#echo "slug,sha,module,test,total_line_number,lines_seperated_with_semicolon,delay"
while read line 
do
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    fi
    tt=$(echo $line | cut -d',' -f1-4)
    testName=$(echo $line | cut -d',' -f4)
    loc=$(echo $line | rev | cut -d',' -f2 | rev)
    echo -n $tt >> "$result"
    #echo ",$loc" >> "Result/all_tests_actual_minimized_locations.csv"
    loc_arr=($(echo $loc | cut -d'[' -f1))
    len="${#loc_arr[@]}"
    echo $len
    flag=0
    line_count_flag=0 
    if [[ $len -gt 0 ]]; then
        delay=$(echo $loc | cut -d':' -f1 | cut -d'=' -f2)
    fi  
    sign=","
    for (( i=0; i<$len; i++)); 
    do  
        testName=$(echo $testName | sed 's;\[;\\[;g')
        filename=$(find "$2" -name "Locations-*${testName}-FlakeDelay-Run-1-*.txt")
        if [[ $filename == "" ]]; then
            echo "file name not found= $filename"
            echo ",location_file_not_found" >> $result 
            break
        else
            flag=1
            total_line_in_a_file=$(cat $filename | wc -l) 
            if [[ $line_count_flag -eq 0 ]]; then
                echo -n ",$total_line_in_a_file" >> $result
                line_count_flag=$(( $line_count_flag + 1))
            fi  
            echo -n "$sign"$(sed -n "${loc_arr[$i]}"p $filename) >> "$result"
            sign=";"
        fi  
    done
    if [[ $flag -eq 1 ]]; then
        echo ",$delay" >> "$result"
    fi  
done < "$1"
