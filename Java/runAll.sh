#!/usr/bin/env bash
if [[ $1 == "" || $2 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    echo "arg2 - relative path to the output file (eg. Result/output.csv)"
    exit
fi

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

inputProj=$currentDir"/projects"
trace_dir="$currentDir/traces"
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

if [ ! -d "$trace_dir" ] 
then
    mkdir "$trace_dir"
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
    testName_with_dot=$(echo $line | cut -d',' -f4)
    #package_class_name=$(echo $testName_with_dot| rev | cut -d'.' -f2- | rev)
    testName="${testName_with_dot%.*}#${testName_with_dot##*.}"
    echo "$testName"
    testClass="$(echo $testName_with_dot | rev | cut -d'.' -f2 | rev)"
    echo "$testClass"
    

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

    #cp whitelist.txt "$currentDir/Locations/whitelist-$projName.txt"
    surefire_exists=$(grep -r "surefire-plugin" pom.xml | wc -l)

    cd $currentDir"/agent-pom-modify" 
    #echo "bash modify-project.sh $inputProj/$slug $surefire_exists "minimizer""
    
    bash modify-project.sh $inputProj/$slug "jacoco"
    #mvn clean install -pl $module -am -DskipTests
    cd $inputProj/$slug
    #echo "mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName" -DargLine="-javaagent:/home/shanto/Latest/ICSE-Artifact/FlakeSync_Artifact_Full/scripts/NOD-Test-Repair/Java/java-callgraph/target/javacg-0.1-SNAPSHOT-dycg-agent.jar"
    #echo "mvn test   -pl common   -Dtest=org.apache.uniffle.common.rpc.GrpcServerTest#testGrpcExecutorPool   -DargLine="-javaagent:/home/shanto/Latest/ICSE-Artifact/FlakeSync_Artifact_Full/scripts/NOD-Test-Repair/Java/java-callgraph/target/javacg-0.1-SNAPSHOT-dycg-agent.jar=incl=org.apache.uniffle.*;""

    mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName >  "$currentDir/logs/$testName-con.txt"
    
    cp $currentDir/jacococli.jar .
    #if [[ $module == "." ]]; then
    #    java -jar jacococli.jar report target/jacoco.exec \
    #      --classfiles $module/target/classes \
    #        --sourcefiles $module/src/main/java \
    #          --xml $module/target/coverage.xml
    #else
        java -jar jacococli.jar report $module/target/jacoco.exec \
          --classfiles $module/target/classes \
            --sourcefiles $module/src/main/java \
              --xml $module/target/coverage.xml
    #fi
    python3 $currentDir/collect_executed_meths.py "$module" "$testName" "$slug"
    test_class_full_path=$(find $module -name "${testClass}.java")
    python3 $currentDir/collect_test_meth_body.py "$moduel" "$testName" "$slug" "$test_class_full_path"
    exit
    python3 $currentDir/collect_method_body.py "$module" "$testName" "$slug"
    slug_with_underscore="${slug//\//_}"
    module_with_underscore="${module//\//_}"
    echo "$slug_with_underscore"


    mv "${slug_with_underscore}_${module_with_underscore}_${testName}_executed_methods.csv" "$trace_dir/"
    mv "${slug_with_underscore}_${module_with_underscore}_${testName}_executed_method_bodies.csv" "$trace_dir/"
    base_package=$(python3 $currentDir/finding_base_package.py "$trace_dir/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_methods.csv")

    echo "$base_package"
    #git stash

    #mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName  -DargLine="-javaagent:/home/shanto/Latest/ICSE-Artifact/FlakeSync_Artifact_Full/scripts/NOD-Test-Repair/Java/java-callgraph/target/javacg-0.1-SNAPSHOT-dycg-agent.jar=incl=${base_package}.*;" >  "$currentDir/logs/$testName.txt"

    #echo "mvn test -pl $module  -Dtest=$testName  -DargLine="-javaagent:/home/shanto/Latest/ICSE-Artifact/FlakeSync_Artifact_Full/scripts/NOD-Test-Repair/Java/java-callgraph/target/javacg-0.1-SNAPSHOT-dycg-agent.jar=incl=${base_package}.*;""

    #mv "${slug_with_underscore}_${module_with_underscore}_${testName}_executed_method_bodies.csv" "$trace_dir/"
    #exit
    #How to get the api call by the test-code


    #exit
    cd $inputProj/$slug
    echo "" >> "$currentDir/$outputDir/Isolation-Result.csv"
    cd $currentDir
    #rm -rf "$inputProj/$rootProj"
done < $1
#bash  $currentDir/run-delta-debugging.sh "$currentDir/$outputDir/Isolation-Result.csv" "Locations/" "Results-Minimizer"

