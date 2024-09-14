import seutil as su
from jsonargparse import CLI
from datasets import load_dataset
from tqdm import tqdm
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import *
import re


from bench.macros import Macros
from bench.data_analyze import load_swe_bench_lite, extract_changed_files_from_patch
from bench.result_analyze import get_change_range_from_patch

sub_agents = ["file_localizer", "region_localizer", "bug_fixer"]

class ReflectionAnalyzer:
    
    def eval_self_reflection_acc(self, traj_dir: Union[List, str]):
        # first load preds and dataset
        model_preds = su.io.load(Path(traj_dir) / "all_preds.jsonl")
        swe_bench_test = load_swe_bench_lite()["test"]
        reflection_results = {}
        resolve_in_single_run_cnt = 0
        reflection_success_cnt, reflection_fail_cnt = 0, 0
        for pred in tqdm(model_preds, total=len(model_preds)):
            self_reflection_traj = None
            resolve_in_single_run, reflection_success = False, False
            ground_truth_reflection = []
            reflection_loop = 0
            instance_id = pred["instance_id"]
            gold_instance = [ins for ins in swe_bench_test if ins["instance_id"] == instance_id][0]
            gold_patch = gold_instance["patch"]

            if pred["model_patch"] is None:
                reflection_fail_cnt += 1
                try:
                    self_reflection_traj = su.io.load(Path(traj_dir)/f"{instance_id}-trial-1"/f"{instance_id}-critic.traj", fmt=su.io.Fmt.json)
                except FileNotFoundError as e:
                    print(str(e))
                    continue
            else:
                if not ((Path(traj_dir)/instance_id/f"{instance_id}-critic.traj").exists()):
                    resolve_in_single_run_cnt += 1
                else:
                    reflection_success_cnt += 1
                    reflection_success = True
                    self_reflection_traj = su.io.load(Path(traj_dir)/instance_id/f"{instance_id}-critic.traj", fmt=su.io.Fmt.json)
            if self_reflection_traj:
                pred_actions, gt_actions, reflection_rounds = analyze_self_reflection_loops(self_reflection_traj, instance_id, gold_patch)
            # analyze across all reflection rounds
            instance_result = {
                "reflection_loops": len(reflection_rounds),
                "reflection_final_success": reflection_success,
                "predicted_actions": pred_actions,
                "ground_truth_actions": gt_actions,
            }
            reflection_results[instance_id] = instance_result
        
        su.io.dump(Macros.results_dir / "swe-bench-lite" / "reflection_results.json", reflection_results, su.io.Fmt.jsonPretty)
        compute_reflection_metrics(reflection_results)
        print(f"Reflection pass: {reflection_success_cnt}, Reflection fail: {reflection_fail_cnt}, resolved without reflection: {resolve_in_single_run_cnt}")
        # reflection_pass, reflection_fail = 0, 0
        # fail_reflection_acc, fail_file_loc_acc, fail_reg_loc_acc, fail_bug_fix_acc = [], [], [], []
        # total_refection, file_loc_action, reg_loc_action, bug_fix_action = 0, 0, 0, 0
        # for ins, result in reflection_results.items():
        #     if result["reflection_final_success"]:
        #         reflection_pass += 1
        #     else:
        #         reflection_fail += 1
        #         fail_reflection_acc += result["reflection_success"]
        #         fail_file_loc_acc += result["file_loc_success"]
        #         fail_reg_loc_acc += result["region_loc_success"]
        #         fail_bug_fix_acc += result["bug_fix_success"]
        #     total_refection += len(result["pred_action"])
        #     file_loc_action += result["pred_action"].count("file_localizer")
        #     reg_loc_action += result["pred_action"].count("region_localizer")
        #     bug_fix_action += result["pred_action"].count("bug_fixer")
        #
        # fail_reflection_acc = mean(fail_reflection_acc)
        # fail_file_loc_acc = mean(fail_file_loc_acc)
        # fail_reg_loc_acc = mean(fail_reg_loc_acc)
        # fail_bug_fix_acc = mean(fail_bug_fix_acc)
        # print(f"Fail reflection acc: {fail_reflection_acc}")
        # print(f"Fail file loc acc: {fail_file_loc_acc}")
        # print(f"Fail region loc acc: {fail_reg_loc_acc}")
        # print(f"Fail bug fix acc: {fail_bug_fix_acc}")
        # print(f"Total reflection: {total_refection}")
        # print(f"File loc action freq: {file_loc_action/total_refection}")
        # print(f"Region loc action freq: {reg_loc_action/total_refection}")
        # print(f"Bug fix action freq: {bug_fix_action/total_refection}")

def compute_reflection_metrics(results: dict):
    """
    Compute the metrics:
    acc, precision for each action, recall for each action, freq of each action
    """
    acc_list = []
    fl_prec, fl_recall = [], []
    rl_prec, rl_recall = [], []
    bf_prec, bf_recall = [], []
    bf_cnt, fl_cnt, rl_cnt = 0, 0, 0
    gt_bf_cnt, gt_fl_cnt, gt_rl_cnt = 0, 0, 0
    total_reflection_rounds = 0
    resolved_after_reflection = 0
    for instance_id, result_dict in results.items():
        pred_actions, gt_actions = result_dict["predicted_actions"], result_dict["ground_truth_actions"]
        total_reflection_rounds += result_dict["reflection_loops"]
        if result_dict["reflection_final_success"]:
            resolved_after_reflection += 1
        for p_action, g_action in zip(pred_actions, gt_actions):
            if p_action != "finish":
                acc_list.append(int(p_action == g_action))
                if p_action == "file_localizer":
                    fl_prec.append(int(p_action == g_action))
                    fl_cnt += 1
                if g_action == "file_localizer":
                    fl_recall.append(int(p_action == g_action))
                    gt_fl_cnt += 1
                if p_action == "region_localizer":
                    rl_prec.append(int(p_action == g_action))
                    rl_cnt += 1
                if g_action == "region_localizer":
                    rl_recall.append(int(p_action == g_action))
                    gt_rl_cnt += 1
                if p_action == "bug_fixer":
                    bf_prec.append(int(p_action == g_action))
                    bf_cnt += 1
                if g_action == "bug_fixer":
                    bf_recall.append(int(p_action == g_action))
                    gt_bf_cnt += 1
    #
    print(f"Total reflection rounds: {total_reflection_rounds}\n"
          f"Resolved after reflection: {resolved_after_reflection}\n"
        f"Reflection accuracy: {mean(acc_list)}\n"
          f"File localizer precision: {mean(fl_prec)}, recall: {mean(fl_recall)}, pred freq: {fl_cnt}, gt freq: {gt_fl_cnt}\n"
          f"Region localizer precision: {mean(rl_prec)}, recall: {mean(rl_recall)}, pred freq: {rl_cnt}, gt freq: {gt_rl_cnt}\n"
          f"Bug fixer precision: {mean(bf_prec)}, recall: {mean(bf_recall)}, pred freq: {bf_cnt}, gt freq: {gt_bf_cnt}\n")

                
def analyze_self_reflection_loops(self_reflection_traj: dict, instance_id: str, gold_patch: str):
    reflection_history = self_reflection_traj["history"]
    # first. split reflection into rounds
    reflection_rounds = []
    current_reflection_round = []
    if len(reflection_history) == 1:
        print(f"Only one step for {instance_id} in reflection loop, needs checking")
        raise RuntimeError
    for _, his in enumerate(reflection_history):
        if his["content"].startswith("SETTING"):
            continue
        if his["content"].startswith("Task: Evaluate the file localization"):
            if current_reflection_round:
                reflection_rounds.append(current_reflection_round)
                current_reflection_round = []
        current_reflection_round.append(his)
        #
    if current_reflection_round:
        reflection_rounds.append(current_reflection_round)
    #
    # second. analyze the accuracy of reflection
    pred_actions, gt_actions = [], []
    for j, reflection_round in enumerate(reflection_rounds):
        reflection_correct = True
        for i, his in enumerate(reflection_round):
            if his["role"] == "user":
                # start single step reflection
                action = reflection_round[i+1]["action"]
                if action == "finish" and "bug fixing step" in his["content"]:
                    action = "bug_fixer"
                # if reflection fails in previous steps, we should keep the gt action as before
                if not reflection_correct:
                    assert gt_action != "finish"
                    pred_actions.append(action)
                    gt_actions.append(gt_action)
                else:
                    gt_action, reflection_correct = eval_self_reflection(his["content"], action, gold_patch)
                    pred_actions.append(action)
                    if action == "region_localizer" and gt_action == "finish":
                        gt_action = "bug_fixer"
                        gt_actions.append(gt_action)
                    else:
                        gt_actions.append(gt_action)
    return pred_actions, gt_actions, reflection_rounds

def eval_self_reflection(prompt: str, action: str, gold_patch: str):
    """
    Return ground truth action. TODO: test this function
    """
    if prompt.startswith("Task: Evaluate the file localization step"):
        pred_file_names = extract_file_from_reflection_prompt(prompt)
        gold_patch_files = extract_changed_files_from_patch(gold_patch)
        file_loc_correct = set(gold_patch_files) <= set(pred_file_names)
        if file_loc_correct:
            reflection_correct = action == "finish"
            gt_action = "finish"
        else:
            reflection_correct = action == "file_localizer"
            gt_action = "file_localizer"
    elif prompt.startswith("Task: Evaluate the region localization step"):
        region_loc_correct = region_localization_success(prompt, gold_patch)
        if region_loc_correct:
            reflection_correct = action == "finish"
            gt_action = "finish"
        else:
            reflection_correct = action == "region_localizer"
            gt_action = "region_localizer"
    else:
        # reflect on bug fix step
        gt_action = "bug_fixer"
        reflection_correct = True
    return gt_action, reflection_correct

                
def parse_generated_patch(content: str):
    location_pattern = re.compile("<patch>(.*?)</patch>", re.DOTALL)
    patches = location_pattern.findall(content)
    if len(patches) == 0:
        return None
        raise RuntimeError("No buggy location found in the region summary.")
    pred_patch = patches[0]
    return pred_patch

def file_localization_success(pred_patch: str, gold_patch: str):
    """
    Compute the file localization accuracy of the agent.

    return bool: if the file localization is successful.
    """
    FILE_LOCALIZE_SUCCESS = False
    gold_patch_files = extract_changed_files_from_patch(gold_patch)
    pred_patch_files = extract_changed_files_from_patch(pred_patch)
    if set(gold_patch_files) <= set(pred_patch_files):
        # model predicted buggy files cover the ground-truth buggy files
        FILE_LOCALIZE_SUCCESS = True
    return FILE_LOCALIZE_SUCCESS

def extract_file_from_reflection_prompt(prompt: str):
    """
    Compute if the file is successfully localized by the agent

    return bool: if the file localizatino is successful.
    """
    # first parse content between <buggy_file>
    location_pattern = re.compile("<buggy_file>(.*?)</buggy_file>", re.DOTALL)
    locations = location_pattern.findall(prompt)
    if len(locations) == 0:
        return []
    else:
        prompt = locations[0]
    pattern = r"<file name='([^']+)'>"
    # Find all matches
    file_names = re.findall(pattern, prompt)
    # Print the list of file names
    return file_names
    

def region_localization_success(prompt: str, gold_patch: dict):
    """
    Compute if the region is successfully localized by the agent

    return bool: if the region localization is successful.
    """
    # extract ground truth code
    gold_change_lines = []
    for gl in gold_patch.splitlines():
        if gl.startswith("+") or gl.startswith("-"):
            gold_change_lines.append(gl[1:])
        else:
            gold_change_lines.append(gl)
    gold_change_lines = set(gold_change_lines)

    # extract localized code
    localized_lines = set()
    location_pattern = re.compile("<python>(.*?)</python>", re.DOTALL)
    locations = location_pattern.findall(prompt)
    if len(locations) == 0:
        return []
    else:
        for code_snippet in locations:
            localized_lines.update(set(code_snippet.splitlines()))

    # check if the localized lines range have any overlap
    return not gold_change_lines.isdisjoint(localized_lines)

if __name__ == "__main__":
    CLI(ReflectionAnalyzer, as_positional=False)