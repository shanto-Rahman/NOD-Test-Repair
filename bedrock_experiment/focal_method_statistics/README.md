To get the focal methods if they truely exists (by find command, need to run). This will output Results/FM_details.csv
#bash collect_focal_method_statistics.sh ../Results/Static_Analysis_and_Claude_comparison.csv
bash collect_focal_method_statistics.sh ../../test_analysis/Results/Updated_1079_tests_with_Focal_Methods.csv

To get the cyclomatic_complexity, and other properties of the FM, run the following command. This will output  Results/
bash fm_statistics.sh Results/FM_details.csv 
