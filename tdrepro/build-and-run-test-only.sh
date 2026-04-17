#!/usr/bin/env bash 
# data=isolated_reruns_from_flakerake_artifacts.csv
if [[ $1 == "" || $2 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    echo "arg2 - relative path to the output file (eg. results)"
    exit
fi

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

inputProj="$currentDir/tmp-projects"
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

logs="$currentDir/tmp-logs"

if [ ! -d "$logs" ] 
then
    mkdir "$logs"
fi


echo "Project-Name,SHA,Module,Test-Name,Failure-Found,Time" > "$currentDir/$outputDir/Re-run-Baseline-Result.csv"

while read line
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
    #file_meth_line_to_inject_delay=$(echo $line | cut -d',' -f5)
    #if [[ $file_meth_line_to_inject_delay == "" ]]; then
    #    echo "No solutions found before"
    #    continue
    #fi
    #file_path=$(echo $file_meth_line_to_inject_delay | cut -d':' -f1 | cut -d'$' -f1)
    #method_name=$(echo $file_meth_line_to_inject_delay | cut -d':' -f2)
    #method_descriptor=$(echo $file_meth_line_to_inject_delay | cut -d':' -f3)
    #line_number=$(echo $file_meth_line_to_inject_delay | cut -d':' -f4 | cut -d' ' -f1)
    #code_line=$(echo $file_meth_line_to_inject_delay | cut -d':' -f4 | cut -d' ' -f2-)

    if [[ ! -d ${inputProj}/${slug} ]]; then
        git clone "https://github.com/$slug" $inputProj/$slug
    fi
    
    cd $inputProj/$slug
    git checkout ${sha}

    echo "test=$testName"
    #testName_with_hash=$(echo "$testName" | sed 's/\(.*\)\./\1#/') 
    #testName="${testName_with_dot%.*}#${testName_with_dot##*.}"
    #echo "testName=, $testName_with_hash"
    testClass="$(echo $testName | rev | cut -d'.' -f1 | rev)"
    
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
    echo -n "${id},${slug},${sha},${module},${testName}," >> "$currentDir/$outputDir/Isolated-Result-for-flakerake.csv"
    
    if [[ $module != "." ]]; then
        projName=$(sed 's;/;.;g' <<< $module-$testName)
     else   
        projName=$(sed 's;/;.;g' <<< $subProj-$testName)
    fi

    module_with_underscore=$(echo "$module" | sed 's|/|_|g')
    echo $module_with_underscore

    if [[ $slug == "Accenture/mercury" ]]; then
        mvn install -pl $module -am -Dmaven.test.skip=true > "${logs}/${rootProj}_${subProj}_${module_with_underscore}"
    else
        mvn install -pl $module -am -DskipTests > "$logs/${rootProj}_${subProj}_${module_with_underscore}"
    fi
    #slug_with_underscore="${slug//\//_}"
    #module_with_underscore="${module//\//_}"
    #echo "$slug_with_underscore"

    echo "$file_path"
    echo "$method_name"
    echo "$method_descriptor"
    echo "line_number=$line_number"
    echo "$code_line"
    #cd $currentDir
    #python3 run_injection.py "$file_path" "$line_number" "$method_name" "$method_descriptor" "$code_line" "$slug" "$module"
    #cd -
    #mvn clean install -pl $module -am -DskipTests
    build_fail_count=$(grep -r "BUILD FAILURE" "$logs/${rootProj}_${subProj}_${module_with_underscore}" | wc -l)
    build_success_count=$(grep -r "BUILD SUCCESS" "$logs/${rootProj}_${subProj}_${module_with_underscore}" | wc -l)

    start=$(date +%s.%N)
    if [[ $build_success_count -gt 0 ]]; then
        if [[ ${build_fail_count} -gt 0 ]]; then
            echo -n "BUILD FAIL," >> "$currentDir/$outputDir/Isolated-Result-for-flakerake.csv"
            echo BUILD FAIL""
        else
            for i in {1..1}; do
                echo "mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName"
                #exit
                mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName >  "$logs/$testName-$i.txt"

                bugCount=$(grep -ic -E 'Errors: 1|Failures: 1' "$logs/$testName-$i.txt")
                if [[ $bugCount -gt 0  ]]; then
                    echo -n "1;" >> "$currentDir/$outputDir/Isolated-Result-for-flakerake.csv"
                    echo "Failure found."
                else
                    echo -n "0;" >> "$currentDir/$outputDir/Isolated-Result-for-flakerake.csv"
                    echo "Failure not found."
                fi
            done
        fi
    else
        echo -n "BUILD FAIL," >> "$currentDir/$outputDir/Isolated-Result-for-flakerake.csv"
        echo BUILD FAIL""
    fi

    end=$(date +%s.%N)
    take=$(echo "scale=2; ${end} - ${start}" | bc)
    take=$(echo $take | awk '{printf("%.2f\n", $1) }')
    echo ",$take" >> "$currentDir/$outputDir/Isolated-Result-for-flakerake.csv"
    git stash #checkout -- '**/*.java'
done < $1
