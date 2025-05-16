#!/usr/bin/env bash
#bash re-run_baseline.sh ../data/talank_with_test_id_idoft.csv results
if [[ $1 == "" || $2 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    echo "arg2 - relative path to the output file (eg. Result/output.csv)"
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

logs="$currentDir/rerun-logs"

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
    id=$(echo $line | cut -d',' -f1)
    slug=$(echo $line | cut -d',' -f2)
    sha=$(echo $line | cut -d',' -f3)
    module=$(echo $line | cut -d',' -f4)
    testName=$(echo $line | cut -d',' -f5)
    #testName="${testName_with_dot%.*}#${testName_with_dot##*.}"
    testClass="$(echo $testName | rev | cut -d'.' -f2 | rev)"
    
    rootProj=$(echo "$slug" | cut -d/ -f 1)
    subProj=$(echo "$slug" | cut -d/ -f 2)
    if [[ ! -d ${inputProj}/${slug} ]]; then
        git clone "https://github.com/$slug" $inputProj/$slug
    fi
    
    cd $inputProj/$slug
    git checkout ${sha}

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
    echo -n "${slug},${sha},${module},${testName}," >> "$currentDir/$outputDir/Re-run-Baseline-Result.csv"
    
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
    slug_with_underscore="${slug//\//_}"
    module_with_underscore="${module//\//_}"
    echo "$slug_with_underscore"
   
    start=$(date +%s.%N)
    for i in {1..5}; do
        echo "mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName"
        #exit
        mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName >  "$logs/$id-$testName-$i.txt"

        bugCount=$(grep -ic -E 'Errors: 1|Failures: 1' "$logs/$id-$testName-$i.txt")
        if [[ $bugCount -gt 0  ]]; then
            echo -n "${bugCount};" >> "$currentDir/$outputDir/Re-run-Baseline-Result.csv"
            echo "Failure found."
        else
            echo -n "${bugCount};" >> "$currentDir/$outputDir/Re-run-Baseline-Result.csv"
            echo "Failure not found."
        fi
    done
    end=$(date +%s.%N)
    take=$(echo "scale=2; ${end} - ${start}" | bc)
    take=$(echo $take | awk '{printf("%.2f\n", $1) }')
    echo ",$take" >> "$currentDir/$outputDir/Re-run-Baseline-Result.csv"
    exit
done < $1
