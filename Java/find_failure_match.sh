#results/tdrepro.csv
currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
while read line
    do
    slug=$(echo $line | cut -d',' -f1)
    sha=$(echo $line | cut -d',' -f2)
    module=$(echo $line | cut -d',' -f3)
    testName=$(echo $line | cut -d',' -f4)
    testName_with_hash=$(echo "$testName" | sed 's/\(.*\)\./\1#/') 
    test_not_failed=$(echo $line | cut -d',' -f5)
    id_to_get_the_test_failure=$(echo $line | rev | cut -d',' -f2 | rev)
    echo "$slug"
    echo $test_not_failed
    if [[ ${test_not_failed} == "" ]]; then
        echo "test not failed"
        echo "$slug,$sha,$module,$testName_with_hash,NA" >> "$currentDir/results/Reliable-Failure-Result-RQ1.csv"
        continue
    else
        echo "Test failed"
    fi

    if [[ $2 == "idoft" ]]; then
        rerun_log="../Results/unique_failures_10K_reruns_181_unique_only.csv"
    elif [[ $2 == "flakerake" ]]; then
        rerun_log="../Results/unique_failures_10K_reruns_flakerake_775.csv"
    fi
    #echo "python3 extracting_log_from_rerun.py $slug $sha $module $testName_with_hash $rerun_log"
    #exit

    python3 extracting_log_from_rerun.py $slug $sha $module $testName_with_hash "$rerun_log" # this will output a csv that would contain the failure log saved during rerun
    #tdrepro_failure_log_file="$currentDir/logs-to-reproduce-by-tdrepro/"+testName_with_hash+"-con-after-changedCode-"+id_to_get_the_test_failure+ ".txt" # This contains the text beyond the failure log only
    tdrepro_failure_log_file="$currentDir/logs-to-reproduce-by-tdrepro/${testName_with_hash}-con-after-changedCode-${id_to_get_the_test_failure}_0.txt"
    echo "python3 $currentDir/log_similarity_init.py "tmp.txt" $tdrepro_failure_log_file  $testName"
    if [[ -f "tmp.txt" ]]; then
        result=$(python3 "$currentDir/log_similarity_init.py" "tmp.txt" "$tdrepro_failure_log_file"  "$testName") #python3 get_similarity_score_stacktrace
        result=$(echo "$result" | xargs)  # removes leading/trailing whitespace
        #echo "$result"
        #exit
        if [[ "$result" == *"MisMatched"* ]] ; then
            #echo "**** $fail_log_csv_name"
            echo "$slug,$sha,$module,$testName_with_hash,0" >> "$currentDir/results/Reliable-Failure-Result-RQ1.csv"
            #echo "MisMatched Failure found."
        else # [[ "$result" == "Matched" ]] ; then
            #echo "PPPPPPPPPp"
            echo "$slug,$sha,$module,$testName_with_hash,1" >> "$currentDir/results/Reliable-Failure-Result-RQ1.csv"
            #echo "$result Failure found."
        fi
        #echo "$tdrepro_failure_log_file"
        rm tmp.txt
   else
       echo "$slug,$sha,$module,$testName_with_hash,not_idoft" >> "$currentDir/results/Reliable-Failure-Result-RQ1.csv"
   fi
done < $1

#python3 aggregate_last_col.py "$currentDir/results/Reliable-Failure-Result-RQ1.csv" > grouped.csv

