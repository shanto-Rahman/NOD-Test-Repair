import os
import sys

class unit_test_case:
    def __init__(self, project, test_file_path, test_method_name, \
                 test_start_line, test_end_line, number_of_lines):
        self.Project = project
        self.TestFilePath = test_file_path
        self.TestMethodName = test_method_name
        self.TestStartLine = test_start_line
        self.TestEndLine = test_end_line
        self.NumberOfLines        = number_of_lines

    def set_focal_method(self, focal_file_path, focal_method_name, focal_start_line, focal_end_line):
        self.FocalFilePath = focal_file_path
        self.FocalMethodName = focal_method_name
        self.FocalStartLine = focal_start_line
        self.FocalEndLine = focal_end_line
        
        
    def set_test_static_characteristic(self, NumberOfLines, NumberOfArguments, NumberOfBranches, NumberOfCalls, Mocked, CyclomaticComplexity, Framework):
        
        self.NumberOfArguments    = NumberOfArguments
        self.NumberOfBranches	  = NumberOfBranches
        self.NumberOfCalls	      = NumberOfCalls
        self.Mocked	              = Mocked
        self.CyclomaticComplexity = CyclomaticComplexity
        self.Framework            = Framework

    def set_test_dynamic_characteristic(self, NumberOfAssertions, NumberOfFailures, NumberOfErrors, ExecutionTime):
        self.NumberOfAssertions = NumberOfAssertions
        self.NumberOfFailures   = NumberOfFailures
        self.NumberOfErrors     = NumberOfErrors
        self.ExecutionTime      = ExecutionTime

    

