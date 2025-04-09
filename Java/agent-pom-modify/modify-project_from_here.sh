#!/bin/bash

if [[ $1 == "" || $2 == "" || $3 == "" ]]; then
	echo "arg1 - the slug of the project"
    echo "arg2-surefire exists or not in the original program"
    echo "arg3- mention the module name (minimizer/boundaryPoint/barrier)"
	exit
fi

project_path=$1

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [[ $3 == "minimizer" ]]; then
    THE_PATH_TO_AGENT_JAR="/home/$USER/.m2/repository/edu/utexas/ece/flakeDelay-core/0.1-SNAPSHOT"
    ARG_LINE="-javaagent:$THE_PATH_TO_AGENT_JAR/flakeDelay-core-0.1-SNAPSHOT.jar"
elif [[ $3 == "boundaryPoint" ]]; then
    THE_PATH_TO_AGENT_JAR="/home/$USER/.m2/repository/edu/utexas/ece/localization-core/0.1-SNAPSHOT"
    ARG_LINE="-javaagent:$THE_PATH_TO_AGENT_JAR/localization-core-0.1-SNAPSHOT.jar"
elif [[ $3 == "barrier" ]]; then
    THE_PATH_TO_AGENT_JAR="/home/$USER/.m2/repository/edu/utexas/ece/barrierSearch-core/0.1-SNAPSHOT"
    ARG_LINE="-javaagent:$THE_PATH_TO_AGENT_JAR/barrierSearch-core-0.1-SNAPSHOT.jar"
fi

#crnt=`pwd`
#working_dir=`dirname $0`
##project_path=$1
#
#cd ${project_path}
#echo $ARG_LINE
#echo "project_path=${project_path}"
#project_path=`pwd`
#cd - > /dev/null
#
#cd ${working_dir}
#
#surefire_exists="$2"  #$(grep -ic -E 'maven-surefire-plugin' "${project_path}/pom.xml")
#echo "currentDir=$(pwd) to look for PomFile.java"
#javac PomFile.java
#echo "currentDir=$(pwd) to look for PomFile.java; project_path= ${project_path}"
#echo "find ${project_path} -name pom.xml | grep -v "src/" | java PomFile ${ARG_LINE} ${surefire_exists}"
#find ${project_path} -name pom.xml | grep -v "src/" | java PomFile ${ARG_LINE} ${surefire_exists}
#exit
#rm -f PomFile.class
#
#cd ${crnt}


#project_path=$1

currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
THE_PATH_TO_AGENT_JAR="/home/$USER/.m2/repository/edu/utexas/ece/flakeDelay-core/0.1-SNAPSHOT"
ARG_LINE="-javaagent:$THE_PATH_TO_AGENT_JAR/flakeDelay-core-0.1-SNAPSHOT.jar"

crnt=`pwd`
working_dir=`dirname $0`
#project_path=$1

cd ${project_path}
project_path=`pwd`
cd - > /dev/null

cd ${working_dir}

surefire_exists="$2"  #$(grep -ic -E 'maven-surefire-plugin' "${project_path}/pom.xml")

javac PomFile.java
find ${project_path} -name pom.xml | grep -v "src/" | java PomFile ${ARG_LINE} ${surefire_exists}
rm -f PomFile.class

cd ${crnt}
