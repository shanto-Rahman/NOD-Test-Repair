#!/usr/bin/env bash
if [[ $1 == "" || $2 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    echo "arg2 - relative path to the output file (eg. Result/output.csv)"
    exit
fi

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

inputProj=$currentDir"/projects-For-Delta"
outputDir="$2"

if [ ! -d "$currentDir/$outputDir" ] 
then
    mkdir "$currentDir/$outputDir"
fi

if [ ! -d "$inputProj" ] 
then
    mkdir ${inputProj}
fi

if [ ! -d "$currentDir/logs" ] 
then
    mkdir "$currentDir/logs"
fi

if [ ! -d "$currentDir/Locations" ] 
then
    mkdir "$currentDir/Locations"
fi

echo "Project-Name,SHA,Module,Test-Name,Failure-Found,Runtime,#Thread" >> "$currentDir/$outputDir/Isolation-Result.csv"

while IFS= read -r line
    do
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    fi
    slug=$(echo $line | cut -d',' -f1)
    sha=$(echo $line | cut -d',' -f2)
    module=$(echo $line | cut -d',' -f3)
    testName=$(echo $line | cut -d',' -f4)
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
    elif [[ $slug == "apache/dubbo" ]]; then
        JMVNOPTIONS="-pl dubbo-dependencies-bom"
    fi  

    echo -n "${slug},${sha},${module},${testName}" >> "$currentDir/$outputDir/Isolation-Result.csv"
    
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
    find -name "*.class" | grep -v Tests | sed 's;.*target/classes/;;'| sed 's;/;.;g' | sed 's;.class$;;' > whitelist.txt
    #To remove the test-classes
    sed -i '/test-classes/d' whitelist.txt   
    if [[ "$slug" == "TooTallNate/Java-WebSocket" ]]; then
        sed -i '/org.java_websocket.server.WebSocketServer/d' "whitelist.txt"
    fi
   
    if [[ "$slug" == "square/okhttp" ]]; then
        sed -i '/com.squareup.okhttp.Request/d' "whitelist.txt"
    fi

    if [[ "$slug" == "alibaba/fastjson" ]]; then
        sed -i '/com.alibaba.json.bvt.parser.deser.AbstractSerializeTest/d' "whitelist.txt"
    fi


    if [[ "$slug" == "square/okhttp" ]]; then
        sed -i '/com.squareup.okhttp.Request/d' "whitelist.txt"
        sed -i '/com.squareup.okhttp.internal.spdy.SpdyConnection/d' "whitelist.txt"
        
    fi  
    
    if [[ "$slug" == "apache/httpcore" ]]; then
        sed -i '/org.apache.http.message.BasicLineParser/d' "whitelist.txt"
        sed -i '/org.apache.http.message.BasicLineFormatter/d' "whitelist.txt"
        sed -i '/org.apache.http.message.BasicHeaderValueParser/d' "whitelist.txt"
    fi 
   
    if [[ "$slug" == "Alluxio/alluxio" ]]; then
        sed -i '/org.eclipse.jetty.server.nio.SelectChannelConnector/d' "whitelist.txt"
    fi

    cp whitelist.txt "$currentDir/Locations/whitelist-$projName.txt"
    surefire_exists=$(grep -r "surefire-plugin" pom.xml | wc -l)
    cd $currentDir"/agent-pom-modify"
    bash modify-project.sh $inputProj/$slug $surefire_exists "minimizer"
    cd $inputProj/$slug

    delayArray=(100 200 400 800 1600 3200 6400 12800 25600)
    flag=1
    iteration_linkage_error=0
    touch "concurrentmethodswhitelist.txt"
    for run in {1..1}; do
        while :
        do
            mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName >  "$currentDir/logs/$testName-con.txt"
            linkage_error=$(grep -r "attempted  duplicate class definition for name"  "$currentDir/logs/$testName-con.txt")
            if [[ $linkage_error == "" ]]; then
                flag=0
                break
            fi
            iteration_linkage_error=$((iteration_linkage_error +1))
            echo "linkage_error= $linkage_error"
            class_name=$(echo $linkage_error | rev | cut -d':' -f1 | rev |  tr -d '"' | sed 's;\/;.;g')
            echo $class_name >> "$currentDir/../flakeDelay-core/src/main/resources/blacklist.txt"
            cd "$currentDir/../"
            mvn clean install
            cd -
        done
        echo "iteration_linkage_error= $iteration_linkage_error"

        if [ -f "$(find . -name "ResultMethods.txt")" ]; then
            resultMethods=$(find . -name "ResultMethods.txt") 
            cp $resultMethods "concurrentmethodswhitelist-$projName-FlakeDelay-Run-$run.txt"
            cat "concurrentmethodswhitelist-$projName-FlakeDelay-Run-$run.txt" >> "concurrentmethodswhitelist.txt"
        fi
    done
    sort -u -o "concurrentmethodswhitelist.txt" "concurrentmethodswhitelist.txt"
    cp  "concurrentmethodswhitelist.txt" "$currentDir/Locations/ConcurrentMethodsWhiteList-$projName.txt"
    if [ -f "$(find . -name "ThreadCountList.txt")" ];then
        threadCount=$(cat $(find -name "ThreadCountList.txt"))
    else
        threadCount="EmptyConcurrentMethod"
    fi
    
    if [ -s "$currentDir/Locations/ConcurrentMethodsWhiteList-$projName.txt" ]
    then    
        properDelay=100
        for d in ${delayArray[@]}; do
            echo "delay === $d"
            timeout 2h mvn test $JMVNOPTIONS  -pl $module -Dconcurrentmethods="$currentDir/Locations/ConcurrentMethodsWhiteList-$projName.txt" -Dwhitelist="$currentDir/Locations/whitelist-$projName.txt" -Dtest=$testName -Ddelay=$d > "$currentDir/logs/$projName-$d.txt"

            bugCount=$(grep -ic -E 'Errors: 1|Failures: 1' "$currentDir/logs/$projName-$d.txt")
            echo "$bugCount ****************"
            if [[ $bugCount -gt 0  ]]; then
                properDelay=$d
                break
            fi
        done
        for run in {1..1}; do
            bugCount=0
            start=$(date +%s.%N)
            echo "Running flakedelay in a loc..."
            timeout 2h mvn test $JMVNOPTIONS  -pl $module -Dconcurrentmethods="$currentDir/Locations/ConcurrentMethodsWhiteList-$projName.txt" -Dwhitelist="$currentDir/Locations/whitelist-$projName.txt" -Dtest=$testName -Ddelay=$properDelay > "$currentDir/logs/$projName-FlakeDelay-Run-$run-$properDelay.txt"
            end=$(date +%s.%N)
            bugCount=$(grep -ic -E 'Errors: 1|Failures: 1' "$currentDir/logs/$projName-FlakeDelay-Run-$run-$properDelay.txt")

            take=$(echo "scale=2; ${end} - ${start}" | bc)
            take=$(echo $take | awk '{printf("%.2f\n", $1) }')
            resultLocations=$(find . -name "ResultLocations.txt") 
            cp $resultLocations "$currentDir/Locations/Locations-$projName-FlakeDelay-Run-$run-$properDelay.txt"
            if [[ $bugCount -gt 0  ]]; then
                echo -n ",1" >> "$currentDir/$outputDir/Isolation-Result.csv"
            else
                echo -n ",0" >> "$currentDir/$outputDir/Isolation-Result.csv"
            fi
            echo -n ",${take}" >> "$currentDir/$outputDir/Isolation-Result.csv"
        done
    else
        echo  ",no concurrent method list" >> "$currentDir/$outputDir/Isolation-Result.csv"
    fi
    git stash
    echo -n ",$threadCount" >> "$currentDir/$outputDir/Isolation-Result.csv"
    echo "" >> "$currentDir/$outputDir/Isolation-Result.csv"
    cd $currentDir
    rm -rf "$inputProj/$rootProj"
done < $1
bash  $currentDir/run-delta-debugging.sh "$currentDir/$outputDir/Isolation-Result.csv" $currentDir/Locations/ $currentDir/Results-Minimizer

