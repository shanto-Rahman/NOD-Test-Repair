#$1=data.csv
while read line; do
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    fi
    proj_name=$(echo $line | cut -d',' -f1)
    git_link=$(echo $line | cut -d',' -f2)
    rest_proj_line=$(echo $line | cut -d',' -f3)
    commit_line=$(grep "$proj_name" "proj_commit.csv")
    commit=$(echo $commit_line | cut -d',' -f2)
    echo $proj_name,$git_link,$commit,$rest_proj_line >> data_with_sha.csv
    #exit
done < $1
