import pandas as pd
import matplotlib.pyplot as plt 
import os

class focal_method:
    def __init__(self, project, repo, commit_id, focal_file_path, focal_method_name):
        self.Project         = project
        self.Repository      = repo
        self.CommitId        = commit_id
        self.FocalFilePath   = focal_file_path
        self.FocalMethodName = focal_method_name
        
        			
    def set_fm_static_characteristic(self, focal_start_line, focal_end_line, number_of_lines,\
                                      no_of_parameters, no_of_branches, no_of_calls, cyclomatic_complexity):
        self.FocalStartLine  = focal_start_line
        self.FocalEndLine    = focal_end_line
        self.NumberOfLines   = number_of_lines
        self.NumberOfParameters       = no_of_parameters
        self.NumberOfBranches	      = no_of_branches
        self.NumberOfCalls	          = no_of_calls
        self.CyclomaticComplexity     = cyclomatic_complexity

    def set_fm_test_characteristic(self, no_of_tests, test_framework):
        self.NumberOfTests            = no_of_tests
        self.TestFramework            = test_framework
       

 

    

def main():
    #Core Files consolidating all the data  
    PROJECT_PATH = "/Users/rabaisha/GitLab/change_aware_utg"
    BENCHMARK_PATH = os.path.join(PROJECT_PATH, "UTG_python_external_benchmark_light")

    fm_stat="bedrock_experiment/focal_method_statistics/Results/properties_of_fm.csv"
    #Similar to the previous result, I also keep all cyclomatic complexity and line numbers in the project specific csv.
    #https://gitlab.aws.dev/rabaisha/change_aware_utg/-/tree/master/bedrock_experiment/focal_method_statistics/Results?ref_type=heads
    test_stat="test_analysis/Results/1072_tests_with_Focal_Methods_with_code_coverage.csv"
    #test_stat="~/Downloads/1072_tests_with_Focal_Methods_with_code_coverage.csv"
    fm_test_stat="bedrock_experiment/Results/Combined_result_of_fm_and_tests.csv" 

    fm_stat_path = os.path.join(PROJECT_PATH,fm_stat) 
    test_stat_path = os.path.join(PROJECT_PATH,test_stat) 
    fm_test_stat_path = os.path.join(PROJECT_PATH,fm_test_stat) 

    df_fm   = pd.read_csv(fm_stat_path)
    df_test = pd.read_csv(test_stat_path)
    df_both = pd.read_csv(fm_test_stat_path)

    print(df_fm.columns)