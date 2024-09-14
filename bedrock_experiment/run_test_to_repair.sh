#!/usr/bin/env bash
#if [[ $1 == "" || $2 == "" || $3 == "" || $4 == "" || $5 == "" || $6 == "" || $11 == "" || $12 == "" || $13 == "" || $14 == "" || $15 == "" || $16 == "" ]]; then
#    echo "arg1 - full path to the data file (eg. proj)" 
#    exit
#fi
if [ "$#" -ne 20 ]; then
    echo "You must enter exactly 19 arguments"
    exit 1
fi
set -x 
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
refined_test=$5
#objective=$6
outputFile="$currentDir_bedrock/$7"
feedback_count=$8
llm_name=$9
changes_types=${10}
fm_file_name=${11}
objective=${12}
diff_fm=${13}
changed_fm=${14}
diff_test=${15}
error_type=${16}
dynamic_trace_found=${17}
original_unit_test_name=${18}
changed_line_numbers=${19}
start_time=${20}

#echo "I AM FROM run_test_to_repair.sh"
echo "I am from bash scrip= $proj, $fm, $test_method, $test_file_path, $refined_test, $objective, $outputFile, $feedback_count, $llm_name, $changes_types, $fm_file_name, $objective, $diff_fm, $changed_fm, $diff_test, $error_type, $dynamic_trace_found, $original_unit_test_name, $changed_line_numbers,$start_time"
#exit
if [ ! -s "$outputFile" ]; then
    if [[ ${objective} == "Refine_CC" || ${objective} == "Normal_Test_Run" ]]; then  
        echo "#proj_name,test_filename,test_method,fm_filename,fm_method,repaired_test,covered_lines,coverage_percentage,test_pass/fail,aim_of_test_change,change_type,Dynamic_trace_found,COT,#Test_That_can_Cover_100%_Lines,Runtime" >> "$outputFile"
    else
        echo "#proj_name,test_filename,test_method,fm_filename,fm_method,repaired_test,diff_test,changed_fm,diff_fm,covered_lines,coverage_percentage,test_pass/fail,aim_of_test_change,change_type,Dynamic_trace_found,COT,Runtime" >> "$outputFile"
    fi
fi
test_class_name=$(echo "$test_file_path" | sed -n "s|.*$proj/\(.*\)|\1|p")

cd "$currentDir_bedrock/../test_analysis/"

currentDir=$(pwd)
cd "projects/${proj}"
python3 $currentDir/modify_tox_to_get_cov.py
#echo "modified tox.ini"
#echo "python3 $currentDir/modify_tox_to_get_cov.py"
log_file="$currentDir_bedrock/$logs_dir/log_${proj}_${test_method}_${fm}_${objective}_${llm_name}_${feedback_count}"
#echo "I AM HERE, $log_file"
if [[ $proj == "graphene-django" ]]; then
    cd "graphene_django/"
    timeout 5m tox -e py39 -- "graphene-django/"${test_class_name}::${test_method} 

elif [[ $proj == "h11" ]]; then 
    timeout 5m tox -e py39 -- "h11/"${test_class_name}::${test_method} -vv > "${log_file}" 2>&1

elif [[ $proj == "cssselect" ]]; then
    timeout 5m tox -e py39 -- ${test_class_name}::${test_method} -vv > "${log_file}" 2>&1 

elif [[ $proj == "eemeter" ]]; then
    #tox -e py39
    timeout 5m tox -e py39 -- ${test_class_name}::${test_method} -vv > "${log_file}" 2>&1 
else

    #echo "tox -e py39 -- "${test_class_name}"::"${test_method}""
    #exit
    timeout 5m tox -e py39 -- "${test_class_name}"::"${test_method}" -vv > "${log_file}" 2>&1
fi
echo "tox -e py39 -- "${test_class_name}"::"${test_method}""
# Split the output into filename and covered methods
#tox -e py312  | tee $currentDir/logs/log_$proj
#objective_trimmed=$(echo "${objective}" | tr -d '\n' | xargs)

#echo "INTENTION=${intention_of_changed_fm_trimmed}"
#echo "${intention_of_changed_fm_trimmed}" | od -c
escaped_refine_test=$(echo "$refined_test" | sed 's/"/""/g')
escaped_diff_test=$(echo "$diff_test" | sed 's/"/""/g')
escaped_changed_fm=$(echo "$changed_fm" | sed 's/"/""/g')
escaped_diff_fm=$(echo "$diff_fm" | sed 's/"/""/g')

if [[ "${objective}" == "Refine_AF" || "${objective}" == "Refine_CC" || "${objective}" == "Reproduce_CC" || "${objective}" == "Normal_Test_Run" ]]; then
    cd $currentDir_bedrock
    output=$(python3 -c "
import sys
from change_curation_helper import read_log_file

log_file_path = '${log_file}'
objective = '${objective}'

try:
    print('*******Bash script Test Results Summary:')
    log_content, test_results = read_log_file(log_file_path, objective)
    print(f'Test Results:\n{test_results}')

except Exception as e:
    sys.stderr.write(f'Error occurred: {str(e)}\n')
    sys.exit(1)
")
    # Ensure the output is not empty
    if [ -z "$output" ]; then
        echo "Error: No output from Python script"
        exit 1
    fi
    #echo "OUTPUT FROM BASH SCRIPT*****", $output
    #echo "***** out_for_pass= ${output}"
    
    # Extract values from the printed dictionary using grep and awk
    test_pass_count=$(echo "$output" | grep -oP "(?<=\'passed\': )\d+")
    failed_count=$(echo "$output" | grep -oP "(?<=\'failed\': )\d+")
    errors_count=$(echo "$output" | grep -oP "(?<=\'errors\': )\d+")
    syntax_errors=$(echo "$output" | grep -oP "(?<=\'sytanx\': )\d+")
    skipped_count=$(echo "$output" | grep -oP "(?<=\'sytanx\': )\d+")
    
    # Print the extracted values
    #echo "out= $errors_count , $failed_count, $test_pass_count, $syntax_errors"
    #if [[ $errors_count -eq 0 && $failed_count -eq 0 && $syntax_errors -eq 0 && ${skipped_count} -eq 0 && ${test_pass_count} -gt 0 ]]; then
        end_time=$(date +%s.%N)
        runtime=$(echo "$end_time - $start_time" | bc) 
        echo "****The total runtime is $runtime seconds"
	#echo "Entering test_pass_count***"
        if [[ ${objective} == "Refine_CC" || ${objective} == "Reproduce_CC" || ${objective} == "Normal_Test_Run" ]]; then
            #Now I will collect all the python files available in the coverage file 

            cd "$currentDir/projects/${proj}"
            #output_coverage=$(python3 $currentDir/collect_coverage_info.py ${fm})
            echo "*********** GOING TO CALL collect_diff_coverage_info.py ***********"
	    echo "===: fm= $fm"
	    #echo "====: changed_fm= $changed_fm"
	    #echo "====: diff_fm= $diff_fm"
	    echo "====:changed_line_numbers= $changed_line_numbers"
	    #diff_text=$(git diff $fm_file_name)
            output_coverage=$(python3 $currentDir/collect_diff_coverage_info.py ${fm} ${changed_line_numbers} 2>&1) 
	    #echo "*** test pass from run_test_to_repair.sh and coverage output= $output_coverage"
            coverage_percentage=$(echo $output_coverage | rev | cut -d '#' -f 1 | rev)
            covered_lines=$(echo $output_coverage | cut -d '#' -f 2- | cut -d'#' -f1)
            echo "****coverage_percentage: $coverage_percentage" 
	    echo "****covered_lines: $covered_lines"

            #if (( $(echo "$coverage_percentage == 100.0" | bc -l) )); then
                if [[ ${objective} == "Refine_CC" || ${objective} == "Normal_Test_Run" ]]; then 
                    echo "$proj,$test_file_path,$original_unit_test_name,$fm_file_name,$fm,\"\"\"$escaped_refine_test\"\"\",\"$covered_lines\",$coverage_percentage,test_pass,${objective},\"${changes_types}\","${dynamic_trace_found}",${feedback_count}",1,$runtime >> "$outputFile"  #If a test passes, and alone can make 100.0% coverage, then the last column will be 1
                    
                    cd "$currentDir/projects/${proj}"
                    git stash 
                fi
            #fi
        else # Refine_AF        
            echo "$proj,$test_file_path,$test_method,$fm_file_name,$fm,\"\"\"$escaped_refine_test\"\"\",\"\"\"$escaped_diff_test\"\"\",\"\"\"$escaped_changed_fm\"\"\",\"\"\"$escaped_diff_fm\"\"\",\"$covered_lines\",$coverage_percentage,test_pass,${objective},\"${changes_types}\","${dynamic_trace_found}",${feedback_count},$runtime" >> "$outputFile" 
            cd "$currentDir/projects/${proj}"
            git stash 
        fi
    #else #jodi test_pass na hoy
    #    cd "$currentDir/projects/${proj}"
    #fi

    #exit 
fi

if [[ "${objective}" != "Refine_CC" || "${objective}" != "Reproduce_CC" ]]; then
    echo "removing coverage.xml***, $(pwd)"
    rm "coverage.xml" 
    git checkout "tox.ini"
fi

#To look for what are the modified files
if [[ "${objective}" == "Refine_AF" || "${objective}" == "Refine_CC" ]]; then
    modified_files=$(git status --porcelain | grep '^ M' | awk '{print $2}')
    if [ ! -z "$modified_files" ]; then
    
       filtered_files=$(echo "$modified_files" | grep -E '^tests/|^test/')
       if [ ! -z "$filtered_files" ]; then #checkout the files that are within tests directory
           echo "filetered_files= $filtered_files"    
           while IFS= read -r file; do
                if [ -f "$file" ]; then
                    echo "CHECKING OUT******* $file"
                    git checkout $file #checking out test file
               fi
           done <<< "$filtered_files"
       fi
    
    #else
    #  echo "No modified files found."
    fi
fi
cd $currentDir_bedrock
