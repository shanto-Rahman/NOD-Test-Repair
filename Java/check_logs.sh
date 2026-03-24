#$1= ../data/new_70_tests.csv
#tdrepro logs are in logs-to-reproduce

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
logs_dir="$currentDir/logs-to-reproduce"
outputDir="$currentDir/results"


while IFS= read -r inputline
    do
    id=$(echo $inputline | cut -d',' -f1)
    slug_org=$(echo $inputline | cut -d',' -f2)
    slug=${slug_org//\//_}
    proj_name_only=$(echo $slug_org | cut -d'/' -f2)
    sha=$(echo $inputline | cut -d',' -f3)
    module_org=$(echo $inputline | cut -d',' -f4)

    testName=$(echo $inputline | cut -d',' -f5)
    echo $module_org
    module_with_dot=${module_org//\//.}
    module_with_underscore=${module_org//\//_}

    #echo $original_log_csv
    if [[ ${module_with_dot} == "." ]]; then
        original_log_csv="$currentDir/logs/${id}_${proj_name_only}_${testName}_stacktrace.csv"
    else
        original_log_csv="$currentDir/logs/${id}_${module_with_dot}_${testName}_stacktrace.csv"
    fi
    echo $original_log_csv
    matched=0
    mismatched=0
    mapfile -t files < <(find $logs_dir -name ${testName}*.txt | sort -Vr | head -n 5)
    for tdrepro_log_file in "${files[@]}"; do
        echo "Processing ${tdrepro_log_file}"
        echo "python3 "$currentDir/log_similarity_init.py" "$original_log_csv" "${tdrepro_log_file}"  "$testName""
        result=$(python3 "$currentDir/log_similarity_init.py" "$original_log_csv" "${tdrepro_log_file}"  "$testName") #python3 get_similarity_score_stacktrace
        echo "***$result***"
        if [[ "$result" == *MisMatched* ]] ; then
		    mismatched=$((mismatched + 1))
        else
		    matched=$((matched + 1))
            #echo -n "$id,$slug,$sha,$module,$testName,matched" >> "$outputDir/tdrepro_detection_failure_matched.csv"
            #break
        fi
        #cat "$file"
    done
    echo "$id,$slug,$sha,$module,$testName,${matched},${mismatched}" >> "$outputDir/tdrepro_detection_failure_matched.csv" #if no match found atleast once, then output the result as a mismatched one
done < $1 



#result=$(python3 "$currentDir/log_similarity_init.py" "$fail_log_csv_name" "$logs/$testName-$i.txt"  "$testName") #python3 get_similarity_score_stacktrace
