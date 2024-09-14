#!/usr/bin/env bash
#if [[ $1 == "" ]]; then
#    echo "arg1 - full path to the data file (eg. Results/850_tests.csv or 1079 tests.csv)" 
#    exit
#fi

currentDir_bedrock=$(pwd)

proj=$1
fm=$2
test_method=$3
# test_method="test_get_table" #test_name of old commit
test_file_path=$4
old_commit=$5
new_commit=$6
fm_file_path=$7
echo $fm_file_path

test_class_name=$( echo $test_file_path | cut -d'/' -f2-)
echo $test_class_name
# inputProj="/home/ec2-user/change_aware_utg/test_analysis/projects"
inputProj="/home/sr53282/utg/change_aware_utg/test_analysis/projects"
outputDir="out"
if [ ! -d "$inputProj" ] 
then
    mkdir ${inputProj}
fi

if [ ! -d "logs" ] 
then
    mkdir "logs"
fi

if [ ! -d "Results" ] 
then
    mkdir "Results"
fi
count=0

outputFile="$currentDir_bedrock/Results/Real_data_with_Old_Test.csv"
if [ ! -s "$outputFile" ]; then
    echo "#proj_name,git_link,python_file_path,test_method_name,claude_result,Static_Analysis_Result,fm_source_file_by_static_analysis,Findings,All_Api_List,fm_source_file_by_dynamic_analysis,covered_methods,coverage_percentage,test_pass/fail" >> "$outputFile"
fi
#while read line
#do 
   
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with the hash $line"
        continue
    fi
    echo $proj
    
    cd $inputProj/$proj
    # git stash
    # git checkout $new_commit
    # currentDir_test_analysis="/home/ec2-user/change_aware_utg/test_analysis/"
    currentDir_test_analysis="/home/sr53282/utg/change_aware_utg/test_analysis"
    python3 $currentDir_test_analysis/modify_tox_to_get_cov.py
    echo "$(pwd)"
    # exit
    if [[ $proj == "graphene-django" ]]; then
        tox -e py39 -- "graphene-django/"${test_class_name}::${test_method}

    elif [[ $proj == "h11" ]]; then 

        tox -e py39 -- "h11/"${test_class_name}::${test_method} > "$currentDir_bedrock/logs/log_${proj}_${test_method}_${old_commit}"

    elif [[ $proj == "cssselect" ]]; then
        tox -e py39 -- ${test_class_name}::${test_method} > "$currentDir_bedrock/logs/log_${proj}_${test_method}_${old_commit}" 2>&1

    elif [[ $proj == "eemeter" ]]; then
        tox -e py39 -- ${test_class_name}::${test_method} > "$currentDir_bedrock/logs/log_${proj}_${test_method}_${old_commit}" 2>&1
    else
        tox -e py39 -- ${test_class_name}::${test_method} > "$currentDir_bedrock/logs/log_${proj}_${test_method}_${old_commit}" 2>&1
    fi
    echo "tox -e py39 -- ${test_class_name}::${test_method}"
    #Now I will collect all the python files available in the coverage file 
    #echo "jaccard focal meth=,${jaccard_focal_method}"
    echo "python3 $currentDir_test_analysis/collect_coverage_info.py ${fm}"
    exit
    output=$(python3 $currentDir_test_analysis/collect_coverage_info.py ${fm})
    echo "output from bash= $output"
    ##python3 parse_code_coverage.py     

    ## Split the output into filename and covered methods
    file_name=$(echo $output | cut -d '#' -f 1)
    covered_percentage=$(echo $output | rev | cut -d '#' -f 1 | rev)
    covered_methods=$(echo $output | cut -d '#' -f 2- | cut -d'#' -f1)
    
    ## Use the output in your Bash script
    echo "Filename: $file_name"
    echo "Covered Methods: $covered_methods"
    echo "covered_percentage: $covered_percentage"

    #tox -e py312  | tee $currentDir_bedrock/logs/log_$proj
    count_pass=$(grep "passed" "$currentDir_bedrock/logs/log_${proj}_${test_method}_${old_commit}" | wc -l)
    #echo $count_pass
    if [[ ${count_pass} -gt 0 ]]; then
        #echo $proj,$git_link,$test_class_name,$test_method,$count_pass >> "$currentDir_bedrock/Results/Passed_Proj_test.csv" 
        # echo "$line,$file_name,$covered_methods,$covered_percentage,test_pass" >> "$outputFile" 
        echo "$proj,$test_file_path,$test_method,$fm_file_path,$fm,$old_commit,$new_commit,$covered_methods,$covered_percentage,test_pass" >> "$outputFile" 
    else
        count_skipped=$(grep "skipped" "$currentDir_bedrock/logs/log_${proj}_${test_method}_${old_commit}" | wc -l)
        if [[ ${count_skipped} -gt 0 ]]; then
            # echo "$line,$file_name,$covered_methods,$covered_percentage,test_skip" >> "$outputFile"
            echo "$proj,$test_file_path,$test_method,$fm_file_path,$fm,$old_commit,$new_commit,$covered_methods,$covered_percentage,test_skip" >> "$outputFile" 
        else
            # echo "$line,$file_name,$covered_methods,$covered_percentage,test_fail" >> "$outputFile"
            echo "$proj,$test_file_path,$test_method,$fm_file_path,$fm,$old_commit,$new_commit,$covered_methods,$covered_percentage,test_fail" >> "$outputFile" 
        fi
    fi    
    exit
    ##echo $(pwd)
    if [[ -f coverage.xml ]]; then 
        rm "coverage.xml" 
    fi
    ##rm "testreport/report.json"
    # git checkout "tox.ini"
    #git checkout $new_commit
    git stash
    cd $currentDir_bedrock
    #rm -rf $inputProj/$proj
#done < $1


