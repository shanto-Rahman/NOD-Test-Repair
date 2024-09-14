#!/bin/bash
#$1=data_list/input.csv
bash runAll.sh $1 Results-Minimizer
#For Delta-Debugging
#bash run-delta-debugging.sh $1 Locations/ Results-Minimizer

#bash find-actual-line-to-delay-inject.sh Result-Delta/Delta-Result.csv Locations/
