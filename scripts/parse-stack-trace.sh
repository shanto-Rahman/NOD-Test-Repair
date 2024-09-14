#!/bin/bash
if [[ $1 == "" || $2 == ""  || $3 == "" ]]; then
    echo "arg1 - slug (the location where stacktrace exists(e.g.,projects/TooTallNate/Java-WebSocket))"
    echo "arg2 - Flag to generate/update result"
    echo "arg3 - projName to save file"
    exit
fi
projName=$3
currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

arr=()
flag=0
if [ -f "$currentDir/Locations/stackTraced-parsed-$projName" ]; then
    rm "$currentDir/Locations/stackTraced-parsed-$projName"  #Removing file if it already exists
echo "HI"
fi

while read line 
do
    findEnd=$(echo $line | cut -d',' -f2)
    if [[ $findEnd =~ "END" ]]; then
        if [[ $flag  -eq 1 ]]; then
            threadId=$(echo $line | cut -d',' -f1)
            arr+=("$threadId")
            echo "From parseScript, Arr =  ${arr[@]}"
            arr_without_space=$( printf "%s" "${arr[@]}" )
            # Need to check arr_
            x1=${arr_without_space[@]}
            echo "${x1}" >>  "$currentDir/Locations/stackTraced-parsed-$projName" # Adding thread Id at the end of each line of Locations.x.txt
            arr=()
        fi
    else
        fullClassName=$(echo $line | cut -d',' -f2)
        beforeBracket=$(echo $fullClassName | cut -d'(' -f1) # Cut by '('
        className=$(echo $beforeBracket | rev | cut -d'/' -f2- | rev)
        removeDollarSignFromOnlyClassName=$(echo $className | rev | cut -d'/' -f1 | rev | cut -d'$' -f1)
        flag=1
        withinBracket=$(echo "$fullClassName" | sed -n 's/.*\(([^()]*)\).*/\1/p')
        replaceParanthesis=$(echo $withinBracket | sed -re 's/[()]//g')
        lineNumber=$(echo $replaceParanthesis | cut -d':' -f2)
        if [[ $lineNumber == "Native Method" ]]; then
            properFormat=""
        else
            properFormat="${className}#${lineNumber},"
        fi
        if [[ $2 =~ "1" ]]; then
            arr+=("$properFormat")
        fi
    fi
done < $1
#To sort this "$currentDir/Locations/stackTraced-parsed-$projName"
FILE="$currentDir/Locations/stackTraced-parsed-$projName"
touch $FILE
if test -f "$FILE"; then
    sort -r "$currentDir/Locations/stackTraced-parsed-$projName" | uniq | sort > "tmp.csv"
    cp "tmp.csv"  "$currentDir/Locations/stackTraced-parsed-$projName" 
    rm "tmp.csv"
fi
    


#sed -i 's/\,$//' "$currentDir/Locations/x.txt"

