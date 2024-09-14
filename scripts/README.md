# Purpose
This is the README for the artifact for "FlakeSync: Automatically Repairing Async Flaky Tests." FlakeSync is a tool for repairing async flaky tests by identifying the critical points and barrier points during the test execution and then synchronizing them as to prevent flaky test failures. The primary purpose of this artifact is to provide the code for FlakeSync as well as the scripts and execution environment in which to run FlakeSync on example flaky tests. By executing the scripts, a user should be able to obtain the results relating to critical points, barrier points, and the final patches for input flaky tests. In this submission, we are applying for two badges: "Available" and "Reusable." The artifact is available through a link on Zenodo, and the scripts are executable through the artifact, allowing somebody to replicate the same results from our work, making it reusable.

# Provenance
The artifact can be obtained from https://zenodo.org/records/10460139 in the form of a Docker image. Note that the size of our Docker image including the dataset is about 1.5GB, so please prepare sufficient disk space

# Setup
The artifact needs to be run from Docker. After downloading the Docker image `flakesync-artifact_latest.tar.gz` from the link, you can install the image by the following command:
```shell
docker load < flakesync-artifact_latest.tar.gz
```

To start a Docker container, use the following command:
```shell
docker run -it --rm --cpus=4 --memory=8g --user java8-flakesync flakesync-artifact bash
```
You will then enter a running Docker container, which contains the code and scripts needed for running our experiments. All subsequent commands should be run within this Docker container.

We evaluated our artifact on our end using Docker version 20.10.21, build 20.10.21-0ubuntu1~20.04.2.

# Usage
Use the following instructions to run FlakeSync through our artifact on an example flaky test.

## End-To-End Results
To run FlakeSync end-to-end, from CritSearch to BarrierSearch, on an example test, run the following command:

```shell
cd /home/java8-flakesync/scripts/
bash end_to_end_flakesync.sh data_list/input.csv
```
Here, `data_list/input.csv` contains the line `alibaba/wasp,b2593d8,.,com.alibaba.wasp.executor.TestExecutorService#testExecutorService`, meaning the command will run FlakeSync on the test `com.alibaba.wasp.executor.TestExecutorService#testExecutorService` from project `alibaba/wasp` on commit `b2593d8`.

This script effectively runs the steps Delay Injection, Minimizing Delay Locations, Root Method Search, Identifying Critical Point, and Identifying Barrier Point from the paper. The main outputs are three directories: `Results-Minimizer/`, `Results-Boundary/`, and `Results-Barrier/`.

This command takes roughly 5-10 minutes to finish.

### Results-Minimizer/
This directory is located at `/home/java8-flakesync/scripts/Results-Minimizer` in the Docker container.
The directory contains three CSV files, corresponding to the test that FlakeSync ran on.

`Isolation-Result.csv` contains the results of delay injection. The expected contents of the file is something like:
```
Project-Name,SHA,Module,Test-Name,Failure-Found,Runtime,#Thread
alibaba/wasp,b2593d8,.,com.alibaba.wasp.executor.TestExecutorService#testExecutorService,1,13.14,6
```
where the most relevant information is the fifth column `Failure-Found` that indicates whether the test passed or failed (1 means failed). If the test is confirmed to fail using delay injection, the command runs later scripts to determine the minimized delay location(s). The values for `Runtime` and `#Thread` may differ due to nondeterminism in execution.

`com.alibaba.wasp.executor.TestExecutorService#testExecutorService.csv` contains the results of the subsequent scripts for the test `com.alibaba.wasp.executor.TestExecutorService#testExecutorService` (note that the file uses the name of the test). The expected contents of the file is something like:
```
alibaba/wasp,b2593d8,.,com.alibaba.wasp.executor.TestExecutorService#testExecutorService,55[delay=100:Time=38.07],38.08
```
which lists out the project name, commit SHA, module name, test name, and line number (55 in this example) corresponding to the line in the file containing all the concurrent methods found when running the test (indicating the concurrent method call for which to inject delay to reproduce the failure); this list of concurrent methods for this test is generated and stored at `/home/java8-flakesync/scripts/Locations/ConcurrentMethodsWhiteList-wasp-com.alibaba.wasp.executor.TestExecutorService#testExecutorService.txt`. The `delay` is the amount of delay (in milliseconds) to inject at a delay location (100 milliseconds in this example) while the final time is the amount of time (in seconds) needed to perform the delta-debugging that determines the minimal delay locations (38.08 seconds in this example). Note that exact runtime may differ from run to run.

`com.alibaba.wasp.executor.TestExecutorService#testExecutorService_Actual_Location.csv` contains similar information, with the contents of the file looking something like:
```
alibaba/wasp,b2593d8,.,com.alibaba.wasp.executor.TestExecutorService#testExecutorService,55,com/alibaba/wasp/executor/ExecutorService$TrackingThreadPoolExecutor#308,100
```
The main difference is that this file explicitly lists out the line where the delay is actually injected (the minimal delay location), which in this example is `com/alibaba/wasp/executor/ExecutorService$TrackingThreadPoolExecutor#308` (line 308 of within the file containing class `com.alibaba.wasp.executor.ExecutorService$TrackingThreadPoolExecutor`).

### Results-Boundary/
This directory is located at `/home/java8-flakesync/scripts/Results-Boundary` in the Docker container.
The relevant results files from this directory are two CSV files, corresponding to the test that FlakeSync ran on.

`com.alibaba.wasp.executor.TestExecutorService#testExecutorService-Result.csv` (named after the test), presents the root method. The contents of the file after running should be:
```
#Project-Name,SHA,Module,Test-Name,Thred-ID,Location[delay],Time
alibaba/wasp,b2593d8,.,com.alibaba.wasp.executor.TestExecutorService#testExecutorService,10,com/alibaba/wasp/executor/ExecutorService$TrackingThreadPoolExecutor/beforeExecute(ExecutorService/java:308)[100],37.51
```
which, aside from the standard project name, commit SHA, module name, and test name, includes the running thread id and the location in which the delay should be injected (with value 100 milliseconds). The final value (37.51 seconds in this example) is the time FlakeSync takes to find the root method. Note that exact runtime may differ from run to run.

`Boundary-com.alibaba.wasp.executor.TestExecutorService#testExecutorService-Result.csv` contains information about the specific boundaries, representing the critical points, within the code-under-test and the delay amount to apply within the boundary to make the test fail. The contents of the file is something like: 
```
#Project-Name,SHA,Module,Test-Name,Boundary-Point(s),Anywhere-of-method(1)/Part-of-method(0),#Boundary-Point,Reaches-to-end(TRUE/FALSE)
alibaba/wasp,b2593d8,.,com.alibaba.wasp.executor.TestExecutorService#testExecutorService,com/alibaba/wasp/executor/ExecutorService$TrackingThreadPoolExecutor#308~com/alibaba/wasp/executor/ExecutorService$TrackingThreadPoolExecutor#308[100];com/alibaba/wasp/executor/ExecutorService$TrackingThreadPoolExecutor#310~com/alibaba/wasp/executor/ExecutorService$TrackingThreadPoolExecutor#310[100];,0,2,FALSE
```
which, aside from the standard project name, commit SHA, module name, and test name, shows the `Boundary-Point(s)` that represents two boundaries indicating the lines on which a delay can be injected and still result in reproducing the failure; in this example, the early boundary is line 308 of class `ExecutorService$TrackingThreadPoolExecutor` while the later boundary is `ExecutorService$TrackingThreadPoolExecutor#310`, indicating that by injecting a 100 millisecond delay before line 310 can result in a test failure. This boundary represents the critical point, where the test should not proceed further until some later barrier point has been reached.

The remaining metrics are internal metrics we use to better understand characteristics of the critical points. The value 0 means injecting delay anywhere in this method cannot make it fail. The value 2 represents the number of boundary points we find for this test (the early and the later). The final value FALSE indicates the boundaries cannot reach the last statement of the method.

### Results-Barrier/
This directory is located at `/home/java8-flakesync/scripts/Results-Barrier` in the Docker container.
This directly contains a single CSV file, `Result.csv`.

`Result.csv` presents the barrier points that FlakeSync identifies for the test. After running on the example test, the file contents should look like the following:
```
Project-Name,SHA,Module,Test-Name,Boundary-Point,Barrier-Point,Threshold,Time
alibaba/wasp,b2593d8,.,com.alibaba.wasp.executor.TestExecutorService#testExecutorService,com/alibaba/wasp/executor/EventHandler#193~com/alibaba/wasp/executor/EventHandler#193[100],com.alibaba.wasp.executor.TestExecutorService#82,1,120.130214532
```
which shows for the test the location of the critical points indicating the boundary (`com/alibaba/wasp/executor/EventHandler#193~com/alibaba/wasp/executor/EventHandler#193[100]`, where `[100]` is the amount of delay in milliseconds applied there), location of the barrier point (`com.alibaba.wasp.executor.TestExecutorService#82`) and a threshold value that represents the number of times the critical point needs to be executed before proceeding past the barrier point (just 1 in this case). The final column's time indicates the amount of time (in seconds) FlakeSync used to find the barrier point for the critical point (120.130214532 seconds).


## Component-Wise Results
You can run different components of FlakeSync individually, each component using some pre-computed values we provide as part of the artifact. Each of these components corresponds to generating one of the directories as described above for the end-to-end run. They should be run in order since later scripts rely on the outputs of previous ones.

To inject delay and get minimized location that makes test fail, use the following command:
```shell
cd /home/java8-flakesync/scripts/
bash delay_injection_and_minimized_locations.sh data_list/input.csv
```

This command outputs the three CSV files within `Results-Minimizer/` described before.

To get the root method and critical points, run the following command:
```shell
cd /home/java8-flakesync/scripts/
bash root_method_and_critical_point_search.sh Results-Minimizer/com.alibaba.wasp.executor.TestExecutorService#testExecutorService_Actual_Location.csv output
```
This command uses the results from `Results-Minimizer/` and outputs the two CSV files within `Result-Boundary/` described before.

Finally, to get the barrier points, run the following command:
```shell
cd /home/java8-flakesync/scripts/
bash barrier_point_search.sh Results-Boundary/Boundary-com.alibaba.wasp.executor.TestExecutorService#testExecutorService-Result.csv
```
This command uses the results from the previous components and outputs the CSV file within `Results-Barrier/` described before.


## Running on Other Tests
The previous instructions are all for running FlakeSync on a single example test, `com.alibaba.wasp.executor.TestExecutorService#testExecutorService`. To run all other tests, you can use a different input CSV file containing lines that represent different tests. File `/home/java8-flakesync/scripts/data_list/all_input.csv` contains lines representing the tests for which FlakeSync could run successfully on. You can create a CSV file using any lines from this file to run FlakeSync on those tests. Running the end-to-end script on all tests from this file would take roughly 4-5 days.

You can find expected results for other tests under `/home/java8-flakesync/expected_results`.
