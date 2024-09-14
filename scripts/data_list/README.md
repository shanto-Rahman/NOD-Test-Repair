cut -d',' -f1 input-process.csv | sort -u > uniq-projectList.csv
cut -d',' -f4 input-process.csv | sort -u | cut -d'#' -f1 | sort -u > uniq-projectClassList.csv
