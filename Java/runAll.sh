#!/usr/bin/env bash
if [[ $1 == "" || $2 == "" ]]; then
    echo "arg1 - full path to the test file (eg. tmp.csv)"
    echo "arg2 - relative path to the output file (eg. Result/output.csv)"
    exit
fi
#baseline_all_flaky_tests_after_10k_runs.csv

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

inputProj=$currentDir"/projects"
trace_dir="$currentDir/traces"
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

if [ ! -d "$currentDir/logs" ] 
then
    mkdir "$currentDir/logs"
fi

if [ ! -d "$trace_dir" ] 
then
    mkdir "$trace_dir"
fi

test_specific_stat="$currentDir/$outputDir/Test-Specific-Stat.csv"
echo "Project-Name,SHA,Module,Test-Name,Failure-Found,Runtime,#Thread" > "$currentDir/$outputDir/Isolation-Result.csv"

echo "Project-Name,SHA,Module,Test-Name,Total-Executed-Meth,Total-tokens" >> "$test_specific_stat"
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

    testName=$(echo $line | cut -d',' -f5) #"${testName_with_dot%.*}#${testName_with_dot##*.}"
    testName_with_dot="${testName//#/.}"
    #testName_with_dot=$(echo $line | cut -d',' -f5)
    #package_class_name=$(echo $testName_with_dot| rev | cut -d'.' -f2- | rev)
    #testName="${testName_with_dot%.*}#${testName_with_dot##*.}"
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
        git stash 
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
       git stash
       sed -i '/<build>/,/<\/build>/ {
       /<plugins>/a\
         <plugin>\n\
           <groupId>org.apache.maven.plugins</groupId>\n\
           <artifactId>maven-surefire-plugin</artifactId>\n\
           <version>2.22.1</version>\n\
         </plugin>
     }' pom.xml
 
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
    #if [[ $trace_collection_way == "dynamic" ]]; then
    #    if [[ $slug == "apache/incubator-uniffle" ]]; then
    #        incl_package="org.apache.uniffle.*;"

    #    elif [[ $slug == "TooTallNate/Java-WebSocket" ]]; then
    #        incl_package="org.java_websocket.*;"
    #    
    #    elif [[ $slug == "Accenture/mercury" ]]; then
    #        incl_package="org.platformlambda.*;excl=org.platformlambda.core.util.CryptoApi"

    #    elif [[ $slug == "Alluxio/alluxio" ]]; then
    #        testClass_with_full_path="$(echo $testName_with_dot | rev | cut -d'.' -f2- | rev)"
    #        echo $testClass_with_full_path
    #        #incl_package="tachyon.*;excl=tachyon.conf.*,tachyon.CommonUtils,tachyon.Log4jFileAppender"
    #        #incl_package="tachyon.*;excl=excl=tachyon.Master,tachyon.LocalTachyonCluster,tachyon.CommonUtils"
    #        incl_package="$testClass_with_full_path,$testClass_with_full_path\$*;"
    #        
    #    elif [[ $slug == "activiti/activiti" ]]; then #Not possible to run
    #        incl_package="org.activiti.*;"

    #    elif [[ $slug == "alibaba/wasp" ]]; then #Not found dynamic call-graph
    #        incl_package="com.alibaba.wasp.engine.*,com.alibaba.wasp.store.*"

    #    elif [[ $slug == "apache/dubbo" ]]; then
    #        incl_package="org.apache.dubbo.*;"

    #    elif [[ $slug == "apache/httpcore" ]]; then
    #        incl_package="org.apache.http.*,excl=.*\\$\\$EnhancerBy.*;"

    #    elif [[ $slug == "davidmoten/rxjava2-extras" ]]; then
    #        incl_package="com.github.davidmoten.*;"
    #        
    #    elif [[ $slug == "doanduyhai/Achilles" ]]; then
    #        incl_package="info.archinnov.achilles.*;"

    #    elif [[ $slug == "elasticjob/elastic-job-lite" ]]; then
    #        incl_package="org.apache.shardingsphere.*;"

    #    elif [[ $slug == "feroult/yawp" ]]; then
    #        incl_package="io.yawp.*;"

    #    elif [[ $slug == "flaxsearch/luwak" ]]; then
    #        incl_package="uk.co.flax.luwak.*;"

    #    elif [[ $slug == "fluent/fluent-logger-java" ]]; then
    #        incl_package="org.fluentd.*;"

    #    elif [[ $slug == "javadelight/delight-nashorn-sandbox" ]]; then
    #        incl_package="delight.nashornsandbox.*;"

    #    elif [[ $slug == "kagkarlsson/db-scheduler" ]]; then
    #        incl_package="com.github.kagkarlsson.*;"

    #    elif [[ $slug == "nlighten/tomcat_exporter" ]]; then
    #        incl_package="nl.nlighten.prometheus.*;"

    #    elif [[ $slug == "qos-ch/logback" ]]; then
    #        incl_package="ch.qos.logback.*;"
    #        
    #    elif [[ $slug == "square/okhttp" ]]; then
    #        incl_package="com.squareup.okhttp.*;"

    #    elif [[ $slug == "undertow-io/undertow" ]]; then
    #        incl_package="io.undertow.*;"

    #    elif [[ $slug == "vmware/admiral" ]]; then
    #        incl_package="com.vmware.*;"
    #    fi
    #    mvn test-compile -pl $module -am
    #    #mvn dependency:build-classpath -pl $module -am -Dmdep.outputFile=$(pwd)/cp.txt
    #    mvn test -pl $module -DargLine="-javaagent:$currentDir/java-callgraph/target/javacg-0.1-SNAPSHOT-dycg-agent.jar=incl=${incl_package}" -Dtest=${testName}

    #    echo "mvn test -pl $module -am -DargLine="-javaagent:$currentDir/java-callgraph/target/javacg-0.1-SNAPSHOT-dycg-agent.jar=incl=${incl_package}" -Dtest=${testName}"
    #    if [[ -f "$module/calltrace.txt" ]]; then
    #        mv "$module/calltrace.txt" "$currentDir/traces/${slug_with_underscore}_${module_with_underscore}_${testName}_dynamic_calltrace.txt"
    #    fi

    #elif [[ $trace_collection_way == "static" ]]; then #do static analysis
    #    if [[ $slug == "apache/incubator-uniffle" ]]; then
    #        module_jar_name="$module/target/rss-common-0.8.0-SNAPSHOT.jar" #module=common

    #    elif [[ $slug == "TooTallNate/Java-WebSocket" ]]; then
    #        module_jar_name="target/Java-WebSocket-1.4.0-SNAPSHOT.jar"  #module=.

    #    elif [[ $slug == "alibaba/wasp" ]]; then #Not found dynamic call-graph
    #        module_jar_name="target/wasp-0.11.jar"

    #    elif [[ $slug == "apache/dubbo" && $module == "dubbo-remoting/dubbo-remoting-netty" ]]; then
    #        module_jar_name="$module/target/dubbo-remoting-netty-2.7.0-SNAPSHOT.jar"

    #    elif [[ $slug == "apache/dubbo" && $module == "dubbo-rpc/dubbo-rpc-dubbo" ]]; then
    #        module_jar_name="$module/target/dubbo-rpc-dubbo-2.7.0-SNAPSHOT.jar"

    #    elif [[ $slug == "apache/httpcore" && $module == "httpcore" ]]; then
    #        module_jar_name="$module/target/httpcore-4.2-alpha2-SNAPSHOT.jar"

    #    elif [[ $slug == "apache/httpcore" &&  $module == "httpcore-nio" ]]; then
    #        module_jar_name="$module/target/httpcore-nio-4.2-alpha2-SNAPSHOT.jar"

    #    elif [[ $slug == "davidmoten/rxjava2-extras" ]]; then
    #        module_jar_name="target/rxjava2-extras-0.2.3-SNAPSHOT.jar"


    #    elif [[ $slug == "doanduyhai/Achilles" &&  $module == "integration-test-2_1" ]]; then
    #        module_jar_name="$module/target/integration-test-2_1.jar"

    #    elif [[ $slug == "doanduyhai/Achilles" &&  $module == "integration-test-2_2" ]]; then
    #        module_jar_name="$module/target/integration-test-2_2.jar"

    #    elif [[ $slug == "doanduyhai/Achilles" &&  $module == "integration-test-3_10" ]]; then
    #        module_jar_name="$module/target/integration-test-3_10.jar"

    #    elif [[ $slug == "doanduyhai/Achilles" &&  $module == "integration-test-3_7" ]]; then
    #        module_jar_name="$module/target/integration-test-3_7.jar"
    #    
    #    elif [[ $slug == "elasticjob/elastic-job-lite" &&  $module == "elasticjob-infra/elasticjob-infra-common" ]]; then
    #        module_jar_name="$module/target/apache-shardingsphere-elasticjob-3.1.0-SNAPSHOT.jar"

    #    elif [[ $slug == "feroult/yawp" &&  $module == "yawp-testing/yawp-testing-appengine" ]]; then
    #        module_jar_name="$module/target/yawp-testing-2.0.4alpha.jar"

    #    elif [[ $slug == "flaxsearch/luwak" &&  $module == "luwak" ]]; then
    #        module_jar_name="$module/target/luwak-1.6.0-SNAPSHOT.jar"

    #    elif [[ $slug == "fluent/fluent-logger-java" ]]; then 
    #        module_jar_name="target/fluent-logger-0.3.5-SNAPSHOT.jar"

    #    elif [[ $slug == "javadelight/delight-nashorn-sandbox" ]]; then 
    #        module_jar_name="target/delight-nashorn-sandbox-0.1.19-SNAPSHOT.jar"        
    #     
    #    elif [[ $slug == "kagkarlsson/db-scheduler" ]]; then
    #        module_jar_name="target/db-scheduler-4.2-SNAPSHOT.jar"

    #    elif [[ $slug == "nlighten/tomcat_exporter" && $module == "client" ]]; then
    #        module_jar_name="$module/target/tomcat_exporter_client-0.0.18-SNAPSHOT.jar"

    #    elif [[ $slug == "qos-ch/logback" && $module == "logback-classic" ]]; then
    #        module_jar_name="$module/target/logback-classic-2.0.0-SNAPSHOT.jar"

    #    elif [[ $slug == "qos-ch/logback" && $module == "logback-core" ]]; then
    #        module_jar_name="$module/target/logback-core-2.0.0-SNAPSHOT.jar"

    #    elif [[ $slug == "square/okhttp" && $module == "okhttp-tests" ]]; then
    #        module_jar_name="$module/target/okhttp-tests-2.0.0-SNAPSHOT.jar"

    #    elif [[ $slug == "undertow-io/undertow" && $module == "websockets-jsr" ]]; then
    #        module_jar_name="$module/target/undertow-websockets-jsr-2.0.14.Final-SNAPSHOT.jar"

    #    elif [[ $slug == "vmware/admiral" && $module == "adapter/registry" ]]; then
    #        module_jar_name="$module/target/admiral-adapter-registry-1.5.0-SNAPSHOT.jar"

    #    elif [[ $slug == "Alluxio/alluxio" ]]; then
    #        module_jar_name="$module/target/tachyon-0.3.0-SNAPSHOT.jar"
    #    fi
    #    #echo "module_jar_name= $module_jar_name"
    #    #echo "java -jar ../../../java-callgraph/target/javacg-0.1-SNAPSHOT-static.jar ${module_jar_name} "

    #    java -jar ../../../java-callgraph/target/javacg-0.1-SNAPSHOT-static.jar ${module_jar_name}  > "callgraph_on_module_jar.txt" # static-trace
    #    grep '^M:' callgraph_on_module_jar.txt > method_calls.txt

    #    mkdir -p merged_classes
    #    # Copy .class files from all related modules (excluding test classes)
    #    #for mod in $(find . -type d -name classes | grep -v test-classes); do
    #    #    cp -rn "$mod"/* merged_classes/ 2>/dev/null
    #    #done
    #    find . -type d -name classes | grep -v test-classes | while read mod; do
    #        rsync -a "$mod/" merged_classes/
    #    done
    #    
    #    # Add test classes from the main module
    #    cp -r "$module/target/test-classes/"* merged_classes/ 2>/dev/null

    #    # Create merged jar
    #    jar cf merged-all-classes.jar -C merged_classes .

    #    ## Gather all built JARs including the main module
    #    #jars=$(find . -type f -path '*/target/*.jar' \
    #    #  ! -name '*-sources.jar' \
    #    #  ! -name '*-javadoc.jar' \
    #    #  | tr '\n' ' ')
    #    #echo "$jars"
    #    #echo " java -jar ../../../java-callgraph/target/javacg-0.1-SNAPSHOT-static.jar $jars"
    #    #java -jar ../../../java-callgraph/target/javacg-0.1-SNAPSHOT-static.jar $jars > "callgraph_on_test_classes.txt" # static-trace

    #    java -jar ../../../java-callgraph/target/javacg-0.1-SNAPSHOT-static.jar merged-all-classes.jar > "callgraph_on_test_classes.txt" # static-trace

    #    grep '^M:' "callgraph_on_test_classes.txt" >> method_calls.txt
    #    sort method_calls.txt | uniq > method_calls_deduped.txt
    #    mv method_calls_deduped.txt method_calls.txt
    #    rm "callgraph_on_module_jar.txt"
    #    rm "callgraph_on_test_classes.txt"
    #    cd $currentDir
    #    #$inputProj/$slug/method_calls.txt traces/${slug_with_underscore}_${module_with_underscore}_${testName}_static_method_calls.csv
    #    testName_colon="${testName_with_dot%.*}:${testName_with_dot##*.}()"
    #    #echo "$testName_colon"
    #    python3 find_helper_meth_in_test.py $inputProj/$slug/method_calls.txt ${testName_colon} traces/${slug_with_underscore}_${module_with_underscore}_${testName}_static_callgraphs.csv
    #    #exit
    #    rm $inputProj/$slug/method_calls.txt
    #fi
    #echo $(pwd)
    cd $inputProj/$slug
    #cp whitelist.txt "$currentDir/Locations/whitelist-$projName.txt"
    surefire_exists=$(grep -r "surefire-plugin" pom.xml | wc -l)

    cd $currentDir"/agent-pom-modify" 
    #echo "bash modify-project.sh $inputProj/$slug $surefire_exists "minimizer""
    
    bash modify-project.sh $inputProj/$slug "jacoco"
    cd $inputProj/$slug
    mvn clean install -pl $module -am -DskipTests
    mvn test $JMVNOPTIONS  -pl $module  -Dtest=$testName >  "$currentDir/logs/$testName-con.txt"
     
    cp $currentDir/jacococli.jar .
    echo "cp $currentDir/jacococli.jar $(pwd)"

    #java -jar jacococli.jar report $module/target/jacoco.exec \
    #  --classfiles $module/target/classes \
    #    --sourcefiles $module/src/main/java \
    #      --xml $module/target/coverage.xml
    # Assume this is the root of your multi-module project
    CLASSFILES=""
    SOURCEFILES=""
    
    for mod in $(find . -name target -type d -prune); do
      base_module=$(dirname "$mod")

      # Skip integration-test-2_1 if module is integration-test-2_2
      #if [[ "$module" == "integration-test-2_2" && "$base_module" == "./integration-test-2_1" ]]; then
      #  continue
      #fi
      # Skip all integration-test-* modules except the one matching $module
      if [[ "$slug" == "doanduyhai/Achilles" && "$base_module" == ./integration-test-* && "$base_module" != ./$module ]]; then
        continue
      fi

      if [ -d "$mod/classes" ]; then
        CLASSFILES+="--classfiles $mod/classes "
      fi
      if [ -d "$base_module/src/main/java" ]; then
        SOURCEFILES+="--sourcefiles $base_module/src/main/java "
      fi
      #if [ -d "$mod/classes" ]; then
      #  CLASSFILES+="--classfiles $mod/classes "
      #fi
      #if [ -d "$(dirname "$mod")/src/main/java" ]; then
      #  SOURCEFILES+="--sourcefiles $(dirname "$mod")/src/main/java "
      #fi
    done
    
    java -jar jacococli.jar report $module/target/jacoco.exec \
      $CLASSFILES \
      $SOURCEFILES \
      --xml $module/target/coverage.xml
    echo "java -jar jacococli.jar report $module/target/jacoco.exec \
      $CLASSFILES \
      $SOURCEFILES \
      --xml $module/target/coverage.xml"
    #executed_methods_count_and_total_token_count=$(
    python3 $currentDir/collect_executed_meths.py "$module" "$testName" "$slug" 
    #)
    #executed_methods=$(echo "$executed_methods_count_and_total_token_count" | cut -d'=' -f2 | cut -d':' -f1 | tr -d ' ')
    #total_tokens_desc=$(echo "$executed_methods_count_and_total_token_count" | cut -d'=' -f3 | tr -d ' ')

    echo python3 $currentDir/collect_executed_meths.py "$module" "$testName" "$slug"
    test_class_full_path=$(find $module -name "${testClass}.java")
    echo "test_class_full_path=$test_class_full_path"

    if [[ $testName == "io.undertow.websockets.jsr.test.JsrWebSocketServer08Test#testErrorHandling" || $testName == "io.undertow.websockets.jsr.test.JsrWebSocketServer13Test#testErrorHandling" ]]; then #These classes extend JsrWebSocketServer07Test.java, and the actual method is JsrWebSocketServer07Test.java
        test_class_full_path="websockets-jsr/src/test/java/io/undertow/websockets/jsr/test/JsrWebSocketServer07Test.java"
    elif [[ $testName == "uk.co.flax.luwak.matchers.TestPartitionMatcher#testParallelSlowLog" || $testName == "uk.co.flax.luwak.matchers.TestParallelMatcher#testParallelSlowLog" ]]; then
        test_class_full_path="luwak/src/test/java/uk/co/flax/luwak/matchers/ConcurrentMatcherTestBase.java"
    elif [[ $testName == "com.github.kagkarlsson.scheduler.compatibility.HsqlCompatibilityTest#test_compatibility" ]]; then
        test_class_full_path="src/test/java/com/github/kagkarlsson/scheduler/compatibility/CompatibilityTest.java"
    fi
    python3 $currentDir/collect_test_meth_body.py "$module" "$testName" "$slug" "$test_class_full_path" $currentDir #) # Might need if later we want to do the repair
    echo "python3 $currentDir/collect_test_meth_body.py "$module" "$testName" "$slug" "$test_class_full_path" $currentDir"
    echo $(pwd)

    #exit
    #echo "matched_calls===$matched_calls"

    #python3 $currentDir/collect_method_body.py "$module" "$testName" "$slug"
    #all_dependent_modules_including_the_main_module=$(find . -type d -name target | sed 's|/target||' | sed 's|^\./||' | sort -u)  #$(find . -type d -name target | sed 's|/target||' | sort -u)
    #all_dependent_modules_including_the_main_module=$(find . -type d -name target -prune | sed 's|/target$||' | sed 's|^\./||' | sort -u)
    readarray -t modules_array < <(find . -type d -name target -prune | sed 's|/target$||' | sed 's|^\./||' | sort -u)


    #echo $all_dependent_modules_including_the_main_module

    echo " python3 $currentDir/collect_method_body.py $module $testName $slug ${modules_array[@]}"
    result=$(python3 $currentDir/collect_method_body.py $module   "$testName" "$slug" "${modules_array[@]}")
    echo "result=$result"
    executed_methods=$(echo "$result" | cut -d'=' -f2 | cut -d':' -f1)
    total_tokens=$(echo "$result" | cut -d'=' -f3)

    echo "Executed methods: $executed_methods"
    echo "Total tokens:      $total_tokens"
    #exit


    echo "$slug,$sha,$module,$testName,$executed_methods,$total_tokens" >> $test_specific_stat
    mv "${slug_with_underscore}_${module_with_underscore}_${testName}_executed_methods.csv" "$trace_dir/"
    mv "${slug_with_underscore}_${module_with_underscore}_${testName}_executed_method_bodies.csv" "$trace_dir/"
    base_package=$(python3 $currentDir/finding_base_package.py "$trace_dir/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_methods.csv")
    echo "$base_package"
    cd $inputProj/$slug
    #exit
    if [[ $trace_collection_way == "static" ]]; then
        git stash
        #git checkout $(find -name "*.java")
        rm -rf $(find -name "target")
        #rm test-classes.jar 
        rm -rf merged_classes/
        rm merged-all-classes.jar
        echo "" >> "$currentDir/$outputDir/Isolation-Result.csv"
    fi
    cd $currentDir

    #if [[ $trace_collection_way == "dynamic" ]]; then
    #    python3 ff.py traces/${slug_with_underscore}_${module_with_underscore}_${testName}_dynamic_calltrace.txt "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_method_bodies.csv" "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_with_call_depth.csv"

    #elif [[ $trace_collection_way == "static" ]]; then
    #    python3 mapping_static_callgraph_to_executed_meth.py traces/${slug_with_underscore}_${module_with_underscore}_${testName}_static_callgraphs.csv "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_method_bodies.csv" "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_with_static_call_depth.csv"

    #    echo "python3 mapping_static_callgraph_to_executed_meth.py traces/${slug_with_underscore}_${module_with_underscore}_${testName}_static_callgraphs.csv "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_method_bodies.csv" "traces/${slug_with_underscore}_${module_with_underscore}_${testName}_executed_with_static_call_depth.csv""

    #fi
    #exit
done < $1
#bash  $currentDir/run-delta-debugging.sh "$currentDir/$outputDir/Isolation-Result.csv" "Locations/" "Results-Minimizer"

