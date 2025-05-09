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

    slug_with_underscore="${slug//\//_}"
    module_with_underscore="${module//\//_}"
    echo "$slug_with_underscore"

    if [[ $slug == "apache/incubator-uniffle" ]]; then
        incl_package="org.apache.uniffle.*;"

    elif [[ $slug == "TooTallNate/Java-WebSocket" ]]; then
        incl_package="org.java_websocket.*;"
    
    elif [[ $slug == "Accenture/mercury" ]]; then
        incl_package="org.platformlambda.*;excl=org.platformlambda.core.util.CryptoApi"

    elif [[ $slug == "Alluxio/alluxio" ]]; then
        testClass_with_full_path="$(echo $testName_with_dot | rev | cut -d'.' -f2- | rev)"
        echo $testClass_with_full_path
        #incl_package="tachyon.*;excl=tachyon.conf.*,tachyon.CommonUtils,tachyon.Log4jFileAppender"
        #incl_package="tachyon.*;excl=excl=tachyon.Master,tachyon.LocalTachyonCluster,tachyon.CommonUtils"
        incl_package="$testClass_with_full_path,$testClass_with_full_path\$*;"
        
    elif [[ $slug == "activiti/activiti" ]]; then #Not possible to run
        incl_package="org.activiti.*;"

    elif [[ $slug == "alibaba/wasp" ]]; then #Not found dynamic call-graph
        incl_package="com.alibaba.wasp.engine.*,com.alibaba.wasp.store.*"

    elif [[ $slug == "apache/dubbo" ]]; then
        incl_package="org.apache.dubbo.*;"

    elif [[ $slug == "apache/httpcore" ]]; then
        incl_package="org.apache.http.*,excl=.*\\$\\$EnhancerBy.*;"

    elif [[ $slug == "davidmoten/rxjava2-extras" ]]; then
        incl_package="com.github.davidmoten.*;"
        
    elif [[ $slug == "doanduyhai/Achilles" ]]; then
        incl_package="info.archinnov.achilles.*;"

    elif [[ $slug == "elasticjob/elastic-job-lite" ]]; then
        incl_package="org.apache.shardingsphere.*;"

    elif [[ $slug == "feroult/yawp" ]]; then
        incl_package="io.yawp.*;"

    elif [[ $slug == "flaxsearch/luwak" ]]; then
        incl_package="uk.co.flax.luwak.*;"

    elif [[ $slug == "fluent/fluent-logger-java" ]]; then
        incl_package="org.fluentd.*;"

    elif [[ $slug == "javadelight/delight-nashorn-sandbox" ]]; then
        incl_package="delight.nashornsandbox.*;"

    elif [[ $slug == "kagkarlsson/db-scheduler" ]]; then
        incl_package="com.github.kagkarlsson.*;"

    elif [[ $slug == "nlighten/tomcat_exporter" ]]; then
        incl_package="nl.nlighten.prometheus.*;"

    elif [[ $slug == "qos-ch/logback" ]]; then
        incl_package="ch.qos.logback.*;"
        
    elif [[ $slug == "square/okhttp" ]]; then
        incl_package="com.squareup.okhttp.*;"

    elif [[ $slug == "undertow-io/undertow" ]]; then
        incl_package="io.undertow.*;"

    elif [[ $slug == "vmware/admiral" ]]; then
        incl_package="com.vmware.*;"
    fi
    #mvn test-compile -pl $module -am
    ##mvn dependency:build-classpath -pl $module -am -Dmdep.outputFile=$(pwd)/cp.txt
    #mvn  -pl $module -DargLine="-javaagent:$currentDir/java-callgraph/target/javacg-0.1-SNAPSHOT-dycg-agent.jar=incl=${incl_package}" test -Dtest=${testName}

    #echo "mvn -pl $module -am -DargLine="-javaagent:$currentDir/java-callgraph/target/javacg-0.1-SNAPSHOT-dycg-agent.jar=incl=${incl_package}" test -Dtest=${testName}"
    #if [[ -f "$module/calltrace.txt" ]]; then
    #    mv "$module/calltrace.txt" "$currentDir/traces/${slug_with_underscore}_${module_with_underscore}_${testName}_dynamic_calltrace.txt"
    #else #do static analysis
        #find all method-calls from test-method
        #cd $currentDir
        #python3 find_helper_meth_in_test.py projects/TooTallNate/Java-WebSocket/src/test/java/org/java_websocket/issues/Issue580Test.java "runNoCloseBlockingTestScenario2" 

        module_jar_name=$(find ${module}/target -name "*.jar")
        echo "module_jar_name= $module_jar_name"
        java -jar ../../../java-callgraph/target/javacg-0.1-SNAPSHOT-static.jar ${module_jar_name}  > "callgraph_on_module_jar.txt" # static-trace
        grep '^M:' callgraph_on_module_jar.txt > method_calls.txt
        cd $module/target/test-classes
        jar cf $inputProj/$slug/test-classes.jar *
        cd -
        java -jar ../../../java-callgraph/target/javacg-0.1-SNAPSHOT-static.jar test-classes.jar > "callgraph_on_test_classes.txt" # static-trace
        grep '^M:' callgraph_on_test_classes.txt >> method_calls.txt

        cd $currentDir
        python3 find_helper_meth_in_test.py $inputProj/$slug/method_calls.txt "org.java_websocket.issues.Issue580Test:runNoCloseBlockingTestScenario2()"

    #fi
    echo $(pwd)
    exit

    #cp whitelist.txt "$currentDir/Locations/whitelist-$projName.txt"
    surefire_exists=$(grep -r "surefire-plugin" pom.xml | wc -l)

    cd $currentDir"/agent-pom-modify" 
    #echo "bash modify-project.sh $inputProj/$slug $surefire_exists "minimizer""
    
    bash modify-project.sh $inputProj/$slug "jacoco"
    cd $inputProj/$slug
    #mvn clean install -pl $module -am -DskipTests
    mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName >  "$currentDir/logs/$testName-con.txt"
     
    cp $currentDir/jacococli.jar .
    java -jar jacococli.jar report $module/target/jacoco.exec \
      --classfiles $module/target/classes \
        --sourcefiles $module/src/main/java \
          --xml $module/target/coverage.xml
 
    python3 $currentDir/collect_executed_meths.py "$module" "$testName" "$slug"
    echo python3 $currentDir/collect_executed_meths.py "$module" "$testName" "$slug"
    test_class_full_path=$(find $module -name "${testClass}.java")
    #matched_calls=$(
    python3 $currentDir/collect_test_meth_body.py "$module" "$testName" "$slug" "$test_class_full_path" $currentDir #)
    echo "matched_calls===$matched_calls"
    python3 $currentDir/collect_method_body.py "$module" "$testName" "$slug"


    mv "${slug_with_underscore}_${module_with_underscore}_${testName}_executed_methods.csv" "$trace_dir/"
    mv "${slug_with_underscore}_${module_with_underscore}_${testName}_executed_method_bodies.csv" "$trace_dir/"
    base_package=$(python3 $currentDir/finding_base_package.py "$trace_dir/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_methods.csv")

    echo "$base_package"
    cd $inputProj/$slug
    git stash
    echo "" >> "$currentDir/$outputDir/Isolation-Result.csv"

    cd $currentDir

    python3 ff.py traces/${slug_with_underscore}_${module_with_underscore}_${testName}_dynamic_calltrace.txt "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_method_bodies.csv" "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_with_call_depth.csv"

done < $1
#bash  $currentDir/run-delta-debugging.sh "$currentDir/$outputDir/Isolation-Result.csv" "Locations/" "Results-Minimizer"

