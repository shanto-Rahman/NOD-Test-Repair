#!/usr/bin/env bash
#bash re-run_baseline.sh ../data/talank_with_test_id_idoft.csv results
if [[ $1 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)" #tdrepro.csv
    #echo "arg2 - relative path to the output file (eg. results)" #result
    #echo "arg3- test-type(idoft/flakerake)" #"idoft"
    exit
fi

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

inputProj=$currentDir"/projects"
outputDir="$currentDir/results"
#trace_collection_way="$3"

if [ ! -d "$outputDir" ] 
then
    mkdir "$outputDir"
fi

if [ ! -d "$inputProj" ] 
then
    mkdir ${inputProj}
fi

logs="$currentDir/logs-rq2"

if [ ! -d "$logs" ] 
then
    mkdir "$logs"
fi


echo "id,Project-Name,SHA,Module,Test-Name,Failure-Found,Time" >> "$outputDir/RQ2-Result.csv"

while IFS= read -r line
    do
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    fi
    id=$(echo $line | cut -d',' -f1)
    slug=$(echo $line | cut -d',' -f2)
    sha=$(echo $line | cut -d',' -f3)
    module=$(echo $line | cut -d',' -f4)
    testName=$(echo $line | cut -d',' -f5)
    fifth_field=$(echo "$line" | awk -v FPAT='([^,]*)|("[^"]*")' '{print $5}')
    file_meth_line_to_inject_delay=$(echo $line | cut -d',' -f6)

    echo "file_meth_line_to_inject_delay=, $file_meth_line_to_inject_delay"
    if [[ $file_meth_line_to_inject_delay == "" ]]; then
        echo "No solutions found before"
        continue
    fi
    class_name=$(echo $file_meth_line_to_inject_delay | cut -d':' -f1 | cut -d'$' -f1 | rev | cut -d'.' -f1 | rev)
    method_name=$(echo $file_meth_line_to_inject_delay | cut -d':' -f2)
    method_descriptor=$(echo $file_meth_line_to_inject_delay | cut -d':' -f3)
    line_number=$(echo $file_meth_line_to_inject_delay | cut -d':' -f4 | cut -d' ' -f1)
    echo "$file_meth_line_to_inject_delay"
    code_line=$(echo $file_meth_line_to_inject_delay | cut -d':' -f4 | cut -d' ' -f2- | sed 's/^(//; s/)$//')

    echo "$class_name"
    echo "$method_name"
    echo "$method_descriptor"
    echo "line_number=$line_number"
    echo "code_line=$code_line"

    echo "test=$testName"
    testName_with_hash=$(echo "$testName" | sed 's/\(.*\)\./\1#/') 
    echo "testName= $testName_with_hash"

    if [[ ! -d ${inputProj}/${slug} ]]; then
        git clone "https://github.com/$slug" $inputProj/$slug
    fi
    
    cd $inputProj/$slug
    git checkout ${sha}

    #testName="${testName_with_dot%.*}#${testName_with_dot##*.}"
    testClass="$(echo $testName | rev | cut -d'.' -f2 | rev)"
    
    rootProj=$(echo "$slug" | cut -d/ -f 1)
    subProj=$(echo "$slug" | cut -d/ -f 2)
    
    JMVNOPTIONS=""
    echo -n "${id},${slug},${sha},${module},${testName}," >> "$outputDir/RQ2-Result.csv"
     
    cd $currentDir
    python3 run_injection.py "$class_name" "$line_number" "$method_name" "$method_descriptor" "$code_line" "$slug" "$module"
    #exit

    module_with_dot=${module//\//.}
    proj_name_only=$(echo $slug | cut -d'/' -f2)
    #python3 find_failure_message_and_save.py "RQ2" "$slug" "$sha" "$module" "$testName_with_hash" "$log_search_csv" "$module_with_dot" "$proj_name_only"
    ##id_arg, slug, sha, module_org, testName= ID  fa3909c391195178ccf5a92d4ac342a30ae247c8 . org.java_websocket.issues.Issue580Test#runNoCloseBlockingTestScenario0

    if [[ $module_org == "." ]]; then
        fail_log_csv_name="$currentDir/logs/${id}_${proj_name_only}_${testName_with_hash}_stacktrace.csv"
    else
        fail_log_csv_name="$currentDir/logs/${id}_${module_with_dot}_${testName_with_hash}_stacktrace.csv"
    fi

    #echo "fail_log_csv_name=$fail_log_csv_name"
    #org_fail_csv=$(find $currentDir/logs -name "*$fail_log_csv_name")
    cd -
    mvn clean install -pl $module -am -DskipTests
    start=$(date +%s.%N)
    for i in {1..100}; do
        echo "mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName_with_hash"
        mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName_with_hash >  "$logs/$testName-$i.txt"

        bugCount=$(grep -ic -E 'Errors: 1|Failures: 1' "$logs/$testName-$i.txt")
        if [[ $bugCount -gt 0  ]]; then
            result=$(python3 "$currentDir/log_similarity_init.py" "$fail_log_csv_name" "$logs/$testName-$i.txt"  "$testName") #python3 get_similarity_score_stacktrace
            #result=$(echo "$result" | xargs)  # removes leading/trailing whitespace
            echo "$result"
	        echo "Comparing "$org_fail_csv" and "$logs/$testName-$i.txt""
            if [[ "$result" == *MisMatched* ]] ; then
                echo -n "2;" >> "$outputDir/RQ2-Result.csv"
                echo "MisMatched Failure found."
            #elif [[ "$result" == *Matched* ]] ; then
            else
               echo -n "1;" >> "$outputDir/RQ2-Result.csv" #Mismatched
               echo "$result Matched Failure found."
	    fi
        else
            echo -n "0;" >> "$outputDir/RQ2-Result.csv" #No fail
            echo "Failure not found."
        fi
    done
    end=$(date +%s.%N)
    take=$(echo "scale=2; ${end} - ${start}" | bc)
    take=$(echo $take | awk '{printf("%.2f\n", $1) }')
    echo ",$take" >> "$outputDir/RQ2-Result.csv"
    git checkout -- '**/*.java'
    #git stash
done < $1
