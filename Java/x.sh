#bash runAll.sh ../data/talank_with_test_id_idoft.csv results/ "static"
#bash runAll.sh ../data/tmp.csv results/ "dynamic"
#bash search_for_failure_reproducing.sh ../data/talank_with_test_id_idoft.csv idoft
bash runAll.sh ../data/talank_with_test_id_idoft.csv results/ 
bash search_for_failure_reproducing.sh ../data/talank_with_test_id_flakerake.csv flakerake
