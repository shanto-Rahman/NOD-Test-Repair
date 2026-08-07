"""
Download the csv with updated data from google sheet: https://docs.google.com/spreadsheets/d/18p8Vj1RnN7U-V4sK0tmcj4ul3Fiqu8LqKF0gG1Ruzl8/edit?gid=1846536626#gid=1846536626
Save the csv under the name "master.csv" in the same directory as this script.
Run this script to generate the ablation plot (ablation_plot.png) in the same directory.
Visualize K and L ablation success rates and time taken (master.csv).

"""

import pandas as pd
import matplotlib.pyplot as plt

COLOR_K = "#2a78d6"   # dataviz palette slot 1 (blue)
COLOR_L = "#eb6834"   # dataviz palette slot 2 (orange)
COLOR_BASELINE = "#eda100"  # gold, marks the k=10,l=10 chosen point

df = pd.read_csv("master.csv", skiprows=1, header=0)
df = df[df["#ID"].notna()]  # drop blank/summary rows

# if TDRepro was not run, do not consider the result. Which means remove the rows where column "Reproduced: TDRepro" is not either "0" or "1", remove it.
df = df[df["Reproduced: TDRepro"].isin(["0", "1"])]


def rate(col):
    return pd.to_numeric(df[col], errors="coerce").mean()


def avg_time(col):
    return pd.to_numeric(df[col], errors="coerce").mean()


# def pareto_frontier(points):
#     """Points not dominated by another point with lower time AND higher success."""
#     frontier = []
#     for t, s in points:
#         if not any(t2 <= t and s2 >= s and (t2, s2) != (t, s) for t2, s2 in points):
#             frontier.append((t, s))
#     return sorted(frontier)


x = [3, 5, 10, 15, 20]

k_success = [rate("Completed Shanto's Part: Ablation Top-K-Methods: When K=3, TDRepro Result"),
             rate("Ablation Top-K-Methods: When K=5, TDRepro Result (Reproduced)"),
             rate("Reproduced: TDRepro"),
             rate("(I should try running all tests here) Ablation Top-K-Methods: When K=15, TDRepro Result"),
             rate("(I should try running all tests here) Ablation Top-K-Methods: When K=20, TDRepro Result")]

k_time = [avg_time("Time Ablation Top-K-Methods: When K=3"),
          avg_time("Time Ablation Top-K-Methods: When K=5"),
          avg_time("Time: TDRepro"),
          avg_time("Time Ablation Top-K-Methods: When K=15"),
          avg_time("Time Ablation Top-K-Methods: When K=20")]

l_success = [rate("Ablation Top-L suggestions by GPT: When L=3, TDRepro Result"),
             rate("Ablation Top-L suggestions by GPT: When L=5, TDRepro Result (Reproduced)"),
             rate("Reproduced: TDRepro"),
             rate("Ablation Top-L suggestions by GPT: When L=15, TDRepro Result"),
             rate("Ablation Top-L suggestions by GPT: When L=20, TDRepro Result")]

l_time = [avg_time("Time Ablation Top-L suggestions by GPT: When L=3"),
          avg_time("Time Ablation Top-L suggestions by GPT: When L=5"),
          avg_time("Time: TDRepro"),
          avg_time("Time Ablation Top-L suggestions by GPT: When L=15"),
          avg_time("Time Ablation Top-L suggestions by GPT: When L=20")]

fig, ax3 = plt.subplots(1, 1, figsize=(6, 5))

# # Panel 1: success rate vs. ablation value
# ax1.plot(x, k_success, marker="o", color=COLOR_K, label="K ablation")
# ax1.plot(x, l_success, marker="s", color=COLOR_L, label="L ablation")
# ax1.set_xlabel("Ablation value")
# ax1.set_ylabel("Success rate")
# ax1.set_title("Success rate vs. ablation value")
# ax1.set_xticks(x)
# ax1.legend()

# # Panel 2: time vs. ablation value
# ax2.plot(x, k_time, marker="o", color=COLOR_K, label="K ablation")
# ax2.plot(x, l_time, marker="s", color=COLOR_L, label="L ablation")
# ax2.set_xlabel("Ablation value")
# ax2.set_ylabel("Avg. time (s)")
# ax2.set_title("Time taken vs. ablation value")
# ax2.set_xticks(x)
# ax2.legend()

# Efficiency frontier (time vs. success rate)
k_points = list(zip(k_time, k_success))
l_points = list(zip(l_time, l_success))

for pts, color, marker, label in [(k_points, COLOR_K, "o", "K ablation"),
                                   (l_points, COLOR_L, "s", "L ablation")]:
    ax3.scatter(*zip(*pts), color=color, marker=marker, s=70, label=label, zorder=3)
    for (t, s), v in zip(pts, x):
        ax3.annotate(str(v), (t, s), textcoords="offset points", xytext=(6, 4), fontsize=8, color=color)
    # frontier = pareto_frontier(pts)
    # ft, fs = zip(*frontier)
    # ax3.plot(ft, fs, color=color, linestyle="--", linewidth=1, alpha=0.6, zorder=2)

baseline_time, baseline_success = avg_time("Time: TDRepro"), rate("Reproduced: TDRepro")
ax3.scatter([baseline_time], [baseline_success], color=COLOR_BASELINE, marker="*", s=300,
            edgecolor="black", linewidth=0.8, zorder=4, label="Chosen: k=10, l=10")

ax3.set_xlabel("Avg. time (s)")
ax3.set_ylabel("Success rate")
ax3.set_title("Ablation: success rate vs. time for K and L values")
ax3.legend()

fig.tight_layout()
fig.savefig("ablation_plot.png", dpi=150)
print("Saved ablation_plot.png")
