if [[ $1 == "" ]]; then
    echo "give fm path name (e.g., focal_method_statistics/Results)"
    exit
fi
currentDir=$(pwd)
find $1 -name "*_cyclomatic_complexity.csv" | sort > "$currentDir/tmp_all_files_fm.csv"
echo "proj_name,test_filename,test_method,test_line_num,fm_filename,fm_method,fm_line_num" > "$currentDir/Results/Combined_result_of_fm_and_tests.csv"
while read file; do
    csv_name=$(echo $file | rev | cut -d'/' -f1 | rev)
    file_found_in_test_dir=$(find "../test_analysis/Results/" -name "$csv_name")
    if [[ $file_found_in_test_dir == "" ]]; then
        continue
    fi
    while read line; do
        proj_name=$(echo $line | cut -d',' -f1)
        if [[ $proj_name == "proj_name" ]]; then
            continue
        fi
        fm_file_name=$(echo $line | cut -d',' -f2)   
        test_file_name=$(echo $line | cut -d',' -f3)   
        test_method=$(echo $line | cut -d',' -f4)   
        fm_method=$(echo $line | cut -d',' -f5)   
        fm_line_num=$(echo $line | rev | cut -d',' -f1-2 | rev | sed 's/,/-/')
        echo $fm_line_num
        #exit
        test_not_skipped=$(grep ",$test_file_name,$test_method," "../test_analysis/Results/690_passed_tests_with_fm.csv" | wc -l)
        if [[ $test_not_skipped -gt 0 ]]; then #skipped tests are not putting here
            output_from_test_file=$(grep ",$test_file_name,$test_method," "../test_analysis/Results/$csv_name")
            test_line_number=$(echo $output_from_test_file | rev | cut -d',' -f1-2 | rev | sed 's/,/-/')
            echo "$proj_name,$test_file_name,$test_method,$test_line_number,$fm_file_name,$fm_method,$fm_line_num" >> "$currentDir/Results/Combined_result_of_fm_and_tests.csv"
            echo $line_number
        fi
    done < $file 
    #exit
done < "$currentDir/tmp_all_files_fm.csv"


#tmp_all_files_fm.csv
    #focal_method_statistics/Results/airtable-python-wrapper_cyclomatic_complexity.csv
    #focal_method_statistics/Results/combined_cyclomatic_complexity.csv
    #focal_method_statistics/Results/ddlparse_cyclomatic_complexity.csv
    #focal_method_statistics/Results/deprecated_cyclomatic_complexity.csv
    #focal_method_statistics/Results/django-enumfields_cyclomatic_complexity.csv
    #focal_method_statistics/Results/django-environ_cyclomatic_complexity.csv
    #focal_method_statistics/Results/eemeter_cyclomatic_complexity.csv
    #focal_method_statistics/Results/freezegun_cyclomatic_complexity.csv
    #focal_method_statistics/Results/gunicorn_cyclomatic_complexity.csv
    #focal_method_statistics/Results/h2_cyclomatic_complexity.csv
    #focal_method_statistics/Results/hpack_cyclomatic_complexity.csv
    #focal_method_statistics/Results/hupper_cyclomatic_complexity.csv
    #focal_method_statistics/Results/hyperframe_cyclomatic_complexity.csv
    #focal_method_statistics/Results/intervals_cyclomatic_complexity.csv
    #focal_method_statistics/Results/oauthlib_cyclomatic_complexity.csv
    #focal_method_statistics/Results/pastedeploy_cyclomatic_complexity.csv
    #focal_method_statistics/Results/pid_cyclomatic_complexity.csv
    #focal_method_statistics/Results/priority_cyclomatic_complexity.csv
    #focal_method_statistics/Results/pyairtable_cyclomatic_complexity.csv
    #focal_method_statistics/Results/scrapyd-client_cyclomatic_complexity.csv
    #focal_method_statistics/Results/virtualenv-clone_cyclomatic_complexity.csv
    #focal_method_statistics/Results/waitress_cyclomatic_complexity.csv
    #focal_method_statistics/Results/wsproto_cyclomatic_complexity.csv
    #
