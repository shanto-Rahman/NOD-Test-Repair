#!/usr/bin/env bash
#bash re-run_baseline.sh ../data/talank_with_test_id_idoft.csv results
if [[ $1 == "" || $2 == "" || $3 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    echo "arg2 - relative path to the output file (eg. results)"
    echo "arg3- test-type(idoft/flakerake)"
    exit
fi

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

inputProj=$currentDir"/projects"
outputDir="$2"
trace_collection_way="$3"

if [ ! -d "$currentDir/$outputDir" ] 
then
    mkdir "$currentDir/$outputDir"
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


echo "Project-Name,SHA,Module,Test-Name,Failure-Found,Time" > "$currentDir/$outputDir/Re-run-Baseline-Result.csv"

while IFS= read -r line
    do
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    fi
    #id=$(echo $line | cut -d',' -f1)
    slug=$(echo $line | cut -d',' -f1)
    sha=$(echo $line | cut -d',' -f2)
    module=$(echo $line | cut -d',' -f3)
    testName=$(echo $line | cut -d',' -f4)
    #file_meth_line_to_inject_delay=$(echo $line | cut -d',' -f5)
    file_meth_line_to_inject_delay=$(awk -v FPAT='([^,]*)|("[^"]+")' '{print $5}' <<< "$line" | sed 's/^"//;s/"$//')
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
    if [[ ! -d ${inputProj}/${slug} ]]; then
        git clone "https://github.com/$slug" $inputProj/$slug
    fi
    
    cd $inputProj/$slug
    git checkout ${sha}

    echo "test=$testName"
    testName_with_hash=$(echo "$testName" | sed 's/\(.*\)\./\1#/') 
    #testName="${testName_with_dot%.*}#${testName_with_dot##*.}"
    echo "testName=, $testName_with_hash"
    testClass="$(echo $testName | rev | cut -d'.' -f2 | rev)"
    
    rootProj=$(echo "$slug" | cut -d/ -f 1)
    subProj=$(echo "$slug" | cut -d/ -f 2)
    
    	JMVNOPTIONS=""
    if [[ "$slug" == "doanduyhai/Achilles" ]]; then
        sed -i 's~http://repo1.maven.org/maven2~https://repo1.maven.org/maven2~g' pom.xml
        sed -i '/<plugin>/,/<\/plugin>/ {
         /<groupId>org.apache.felix<\/groupId>/ {
           N
           /<artifactId>maven-bundle-plugin<\/artifactId>/ {
             a\
             <version>${felix.version}</version>
           }
         }
       }' pom.xml

    elif [[ $slug == "apache/dubbo" ]]; then
        JMVNOPTIONS="-pl dubbo-dependencies-bom"

    elif [[ $slug == "apache/httpcore" ]]; then
       sed -i '/<build>/,/<\/build>/ {
       /<plugins>/a\
         <plugin>\n\
           <groupId>org.apache.maven.plugins</groupId>\n\
           <artifactId>maven-surefire-plugin</artifactId>\n\
           <version>2.22.1</version>\n\
         </plugin>
     }' pom.xml
 
    fi  
    echo -n "${slug},${sha},${module},${testName}," >> "$currentDir/$outputDir/RQ2-Result.csv"
    
    if [[ $module != "." ]]; then
        projName=$(sed 's;/;.;g' <<< $module-$testName)
     else   
        projName=$(sed 's;/;.;g' <<< $subProj-$testName)
    fi
    
    if [[ $slug == "Accenture/mercury" ]]; then
        mvn install -pl $module -am -Dmaven.test.skip=true
    else
        mvn install -pl $module -am -DskipTests
    fi
    #slug_with_underscore="${slug//\//_}"
    #module_with_underscore="${module//\//_}"
    #echo "$slug_with_underscore"

    echo "$class_name"
    echo "$method_name"
    echo "$method_descriptor"
    echo "line_number=$line_number"
    echo "$code_line"
    cd $currentDir
    python3 run_injection.py "$class_name" "$line_number" "$method_name" "$method_descriptor" "$code_line" "$slug" "$module"
    #log for baseline
    log_search_csv=""
    if [[ $3 == "flakerake" ]]; then #will read failure message from, and save that into a txt file similar to the name of idoft unique_failures_10K_reruns_flakerake_775.csv
        log_search_csv="../Results/unique_failures_10K_reruns_flakerake_775.csv"
    elif [[ $3 == "idoft" ]]; then #../Results/unique_failures_10K_reruns_181_unique_only.csv
        log_search_csv="../Results/unique_failures_10K_reruns_181_unique_only.csv"
    fi

    module_with_dot=${module//\//.}
    proj_name_only=$(echo $slug | cut -d'/' -f2)
    python3 find_failure_message_and_save.py "ID" "$slug" "$sha" "$module" "$testName_with_hash" "$log_search_csv" "$module_with_dot" "$proj_name_only"
    #id_arg, slug, sha, module_org, testName= ID  fa3909c391195178ccf5a92d4ac342a30ae247c8 . org.java_websocket.issues.Issue580Test#runNoCloseBlockingTestScenario0

    if [[ $module == "." ]]; then
        fail_log_csv_name="$currentDir/logs/ID_${proj_name_only}_${testName_with_hash}_stacktrace.csv"
    else
        fail_log_csv_name="$currentDir/logs/ID_${module_with_dot}_${testName_with_hash}_stacktrace.csv"
    fi
    cd -
    mvn clean install -pl $module -am -DskipTests
    start=$(date +%s.%N)
    for i in {1..100}; do
        echo "mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName_with_hash"
        mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName_with_hash >  "$logs/$testName-$i.txt"
        #exit

        bugCount=$(grep -ic -E 'Errors: 1|Failures: 1' "$logs/$testName-$i.txt")
        if [[ $bugCount -gt 0  ]]; then
            result=$(python3 "$currentDir/log_similarity_init.py" "$fail_log_csv_name" "$logs/$testName-$i.txt"  "$testName") #python3 get_similarity_score_stacktrace
            echo "$result"
            if [[ "$result" == "MisMatched" ]] ; then
                echo "$fail_log_csv_name"
                echo -n "2;" >> "$currentDir/$outputDir/RQ2-Result.csv"
                echo "Failure found."
            else
                echo -n "1;" >> "$currentDir/$outputDir/RQ2-Result.csv" #Mismatched
                echo "Matched Failure found."
            fi
        else
            echo -n "0;" >> "$currentDir/$outputDir/RQ2-Result.csv" #No fail
            echo "Failure not found."
        fi
    done
    end=$(date +%s.%N)
    take=$(echo "scale=2; ${end} - ${start}" | bc)
    take=$(echo $take | awk '{printf("%.2f\n", $1) }')
    echo ",$take" >> "$currentDir/$outputDir/RQ2-Result.csv"

    #git checkout -- '**/*.java'
    git stash

done < $1
