if [[ $1 == "" ]]; then
    echo "give input file (../Results/Static_Analysis_and_Claude_comparison.csv)"
    exit
fi
currentDir=$(pwd)
if [[ ! -d "Results" ]]; then
    mkdir "Results"
else
    rm "$currentDir/Results/FM_details.csv"
    rm "$currentDir/Results/Problem_details.csv"

    echo "#proj,test_name,fm_by_jaccard,fm_1st_covered_line,fm_filename,test_filename,dir_name_only" >> "$currentDir/Results/FM_details.csv"
fi
 
while read proj_line
do

    if [[ ${proj_line} =~ ^\# ]]; then
        echo "Line starts with Hash ${proj_line}"
        continue
    fi
    proj=$(echo $proj_line | cut -d',' -f1)
    fm_first_covered_line=$(echo $proj_line | cut -d'[' -f2 | cut -d',' -f1 | cut -d']' -f1)
    test_filename=$(echo $proj_line | cut -d',' -f3)
    test_name=$(echo $proj_line | cut -d',' -f4)
    suggested_fm_and_num_of_arg_by_jaccard=$(echo $proj_line | cut -d',' -f6)
    fm_by_jaccard=$(echo $suggested_fm_and_num_of_arg_by_jaccard | cut -d'#' -f1)
    num_args_of_fm_by_jaccard=$(echo $suggested_fm_and_num_of_arg_by_jaccard | cut -d'#' -f2)
    suggested_classname_of_fm_by_jaccard=$(echo $proj_line | cut -d',' -f7)
    suggested_classname_of_fm_by_dynamic=$(echo $proj_line | cut -d'{' -f1 | rev | cut -d',' -f2 | rev)
    echo $suggested_classname_of_fm_by_dynamic
   
    dir_name_only=$(echo "$suggested_classname_of_fm_by_dynamic" | rev | cut -d'/' -f2- | rev) # |sed 's/\./\//g')
#exit
    #if [[ $suggested_classname_of_fm_by_jaccard == "" ]]; then # This will indicate that we get both the focal method and the class name
    #    continue
    #fi
    #echo "$proj,$suggested_fm_and_num_of_arg_by_jaccard,$fm_by_jaccard,$num_args_of_fm_by_jaccard,$suggested_classname_of_fm_by_jaccard"
    #cd  "../../test_analysis/projects/$proj"
    #count_dot_in_class_name=$(echo ${suggested_classname_of_fm_by_jaccard} | grep -o '\.' | wc -l)
    #echo "count_dot_in_class_name=$count_dot_in_class_name"
    #if [[ ${count_dot_in_class_name} -gt 0 ]]; then #it indicates we need to split to get the single filename
    #    file_name=$(python3 $currentDir/find_valid_file.py ${suggested_classname_of_fm_by_jaccard})
    #    file_name=$(echo $file_name | sed 's/\./\//g')
    #    echo "file_name=$file_name"
    #    file_name_only=$(echo "$file_name" | rev | cut -d'/' -f1 | rev)
    #    dir_name_only=$(echo "$file_name" | rev | cut -d'/' -f2- | rev) # |sed 's/\./\//g')

    #    if [[ $file_name_only == "$fm_by_jaccard" ]]; then #because sometimes we get from pyairtable.testing import fake_meta, fake_record fake_record#2,pyairtable.testing.fake_record            "matched found ***"
    #        file_name_only=$(echo "$file_name" | rev | cut -d'/' -f2 | rev)
    #        dir_name_only=$(echo "$file_name" | rev | cut -d'/' -f3- | rev) # |sed 's/\./\//g')
    #    fi

    #    echo "$file_name, $file_name_only, $dir_name_only, $fm_by_jaccard ======="
    #    #exit
    #    #echo "$dir_name_only"
    #else
    #    file_name_only=$suggested_classname_of_fm_by_jaccard #$(echo "$file_name" | rev | cut -d'.' -f1 | rev)
    #    dir_name_only="."
    #fi
    #echo $(pwd)
    #echo "dir_name= $dir_name_only"
    #exit 
    #if [[ ! -d "${dir_name_only}" ]]; then 
    #    echo "$proj,$test_name,$fm_by_jaccard,$file,$dir_name_only" >> "$currentDir/Results/Problem_details.csv"
    #    cd $currentDir
    #    continue
    #fi  
    #obtained_file_name=$(find -name "${file_name_only}.py")
    #echo $obtained_file_name
    #for file in $obtained_file_name; do
        if [[ $file =~ .*/\.tox/.* ]]; then
            continue
        fi
        echo "$proj,$test_name,${fm_by_jaccard},${fm_first_covered_line},${suggested_classname_of_fm_by_dynamic},${test_filename},${dir_name_only}" >> "$currentDir/Results/FM_details.csv"
    #done
    cd $currentDir
    #exit 

done < $1
