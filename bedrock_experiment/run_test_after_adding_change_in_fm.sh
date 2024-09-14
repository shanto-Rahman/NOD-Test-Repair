#!/usr/bin/env bash
if [[ $1 == "" ]]; then
    echo "arg1 - full path to the data file (eg. proj)" 
    exit
fi

currentDir_bedrock=$(pwd)
logs_dir="test_run_logs_after_fm_changed"
if [ ! -d "$logs_dir" ] 
then
    mkdir "$logs_dir"
fi

if [ ! -d "Results" ] 
then
    mkdir "Results"
fi
count=0

#outputFile="$currentDir_bedrock/Results/690_tests_with_Focal_Methods.csv"

proj=$1
fm=$2
test_method=$3
test_file_path=$4
changed_fm=$5
outputFile="$currentDir_bedrock/$6"
feedback_count=$7
llm_name=$8
changes_types=${9}
fm_file_name=${10}
objective=${11}

if [ ! -s "$outputFile" ]; then
        echo "#proj_name,test_filename,test_method,fm_filename,fm_method,changed_fm,covered_lines,coverage_percentage,test_pass/fail,aim_of_fm_change,change_type,COT" >> "$outputFile"
fi
test_class_name=$(echo "$test_file_path" | sed -n "s|.*$proj/\(.*\)|\1|p")

cd "$currentDir_bedrock/../test_analysis/"

currentDir=$(pwd)
cd "projects/${proj}"
python3 $currentDir/modify_tox_to_get_cov.py
#echo "modified tox.ini"
#echo "python3 $currentDir/modify_tox_to_get_cov.py"
log_file="$currentDir_bedrock/$logs_dir/log_${proj}_${test_method}_${fm}_${objective}_${llm_name}_${feedback_count}"
if [[ $proj == "graphene-django" ]]; then
    cd "graphene_django/"
    tox -e py39 -- "graphene-django/"${test_class_name}::${test_method}

elif [[ $proj == "h11" ]]; then 
    tox -e py39 -- "h11/"${test_class_name}::${test_method} > "${log_file}" 2>&1

elif [[ $proj == "cssselect" ]]; then
    tox -e py39 -- ${test_class_name}::${test_method} > "${log_file}" 2>&1 

elif [[ $proj == "eemeter" ]]; then
    #tox -e py39
    tox -e py39 -- ${test_class_name}::${test_method} > "${log_file}" 2>&1 
else
    tox -e py39 -- "${test_class_name}"::"${test_method}" > "${log_file}" 2>&1
fi

escaped_changed_fm=$(echo "$changed_fm" | sed 's/"/""/g')
if [[ ${objective} == "CC" ||  ${objective} == "Reproduce_CC" ]]; then #CC is used for change curation
    #Now I will collect all the python files available in the coverage file 
    output=$(python3 $currentDir/collect_coverage_info.py ${fm})
    coverage_percentage=$(echo $output | rev | cut -d '#' -f 1 | rev)
    covered_lines=$(echo $output | cut -d '#' -f 2- | cut -d'#' -f1)
    #echo "output= $output"
    #echo "coverage_percentage=$coverage_percentage"
    #exit
    #count_pass=$(grep "passed" "${log_file}" 2>&1 | wc -l)
    echo "log_file_name=$log_file"
    cd $currentDir_bedrock 
    output=$(python3 -c "
import sys
from change_curation_helper import read_log_file

log_file_path = '${log_file}'
objective = '${objective}'
try:
    print('*******Bash script Test Results Summary:')
    log_content, test_results = read_log_file(log_file_path, objective)
    print(f'Test Results:\n{test_results}')  # Debugging line
except Exception as e:
    sys.stderr.write(f'Error occurred: {str(e)}\n')
    sys.exit(1)
")

    # Ensure the output is not empty
    if [ -z "$output" ]; then
        echo "Error: No output from Python script"
        exit 1
    fi
    
    # Echo the output for debugging
    echo "***** out_for_pass= ${output}"
    
    # Extract values from the printed dictionary using grep and awk
    test_pass_count=$(echo "$output" | grep -oP "(?<=\'passed\': )\d+")
    failed_count=$(echo "$output" | grep -oP "(?<=\'failed\': )\d+")
    errors_count=$(echo "$output" | grep -oP "(?<=\'errors\': )\d+")
    skipped_count=$(echo "$output" | grep -oP "(?<=\'skipped\': )\d+")
    
    # Print the extracted values
    echo "out= $errors_count , $failed_count, $passed_count, $skipped_count"
    cd "$currentDir/projects/${proj}"
    
    if [[ $errors_count -eq 0 && $failed_count -eq 0 && $skipped_count -eq 0 && ${test_pass_count} -gt 0 ]]; then
    
        echo "ENTERNING reduce coverage*****"
        #if [[ ${count_pass} -gt 0 ]]; then
            echo "coverage_percentage: $coverage_percentage"
            if (( $(echo "$coverage_percentage == 100.0" | bc -l) )); then
    	    echo "Not 100% coverage"
            else
                echo "$proj,$test_file_path,$test_method,$fm_file_name,$fm,\"\"\"$escaped_changed_fm\"\"\",\"$covered_lines\",$coverage_percentage,test_pass,${objective},\"${changes_types}\",${feedback_count}" >> "$outputFile" 
            fi
        fi
    
    elif [[ ${objective} == "AF"  ]]; then

    count_syntax_error=$(grep "SyntaxError" "${log_file}" | wc -l)
    count_assertion_error=$(grep "AssertionError" "${log_file}" | wc -l)
    count_attribute_error=$(grep "AttributeError" "${log_file}" | wc -l)
    echo FROM test run =========""
    if [[ $count_syntax_error -gt 0 ]]; then 
        echo "Syntax error found ***"
    elif [[ ${count_assertion_error} -gt 0 ]]; then 
        echo "${log_file}, Assertion error found.=========="
        echo "$proj,$test_file_path,$test_method,$fm_file_name,$fm,\"\"\"$escaped_changed_fm\"\"\",\"$covered_lines\",$coverage_percentage,assertion_fail,${objective},\"${changes_types}\",${feedback_count}" >> "$outputFile" 
    elif [[ ${count_attribute_error} -gt 0 ]]; then 
        echo "${log_file}, Attribute error found.=========="
        echo "$proj,$test_file_path,$test_method,$fm_file_name,$fm,\"\"\"$escaped_changed_fm\"\"\",\"$covered_lines\",$coverage_percentage,attribute_error,${objective},\"${changes_types}\",${feedback_count}" >> "$outputFile" 
    fi    
fi

#For collecting dynamic code coverage if it is reproduce-AF or reproduce-CC
if [[ ${objective} == "Reproduce-AF" || ${objective} == "Reproduce_CC" ]]; then
   #print("Reproduce something ****")
   #python3  "$currentDir_bedrock/collect_coverage_info.py"
   dynamic_meth_trace_json_output=$(python3  "$currentDir_bedrock/collect_coverage_info.py" "$fm" "$fm_file_name")
   echo "Dynamic_Trace:$dynamic_meth_trace_json_output"
fi

rm "coverage.xml" 
git checkout "tox.ini"
#exit
#To look for what are the modified files
if [[ "${objective}" == "AF" || "${objective}" == "CC" ]]; then
    echo "doing git stash"
    git stash
fi
cd $currentDir_bedrock
