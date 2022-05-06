#! /usr/bin/env python3

import re
from argparse import ArgumentParser
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from typing import DefaultDict, List, Optional

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from get_result_dir import get_dir

ROOT = Path(__file__).parent


class Counter:
    cntr: DefaultDict[str, List[int]]

    def __init__(self):
        self.cntr = defaultdict(list)

    def add(self, repo: str, time: int):
        self.cntr[repo].append(time)

    def total(self, repo: str = None) -> int:
        res = 0
        for k, v in self.cntr.items():
            if repo is None or repo == k:
                res += sum(v)
        return res

    def __len__(self) -> int:
        return sum(map(len, self.cntr.values()))

    def __iter__(self):
        for l in self.cntr.values():
            yield from l


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument(
        "dir",
        help="Result folder to check average time for (opts for latest when absent).",
        nargs="?",
    )
    args = parser.parse_args()

    def get_ts(line: str) -> Optional[timedelta]:
        if match := re.match(r"^(\d\d:\d\d:\d\d) \w+\.go:\d+:", line):
            hr, mn, ss = map(int, match.group(1).split(":"))
            return timedelta(hours=hr, minutes=mn, seconds=ss)
        return None

    def tdiff(a: timedelta, b: timedelta) -> int:
        diff = b.total_seconds() - a.total_seconds()
        if diff < 0:
            # If one run can take more than 24 hours this does not work any more
            diff += timedelta(days=1).total_seconds()
        return int(diff)

    # Latest result folder
    result_dir = ROOT / get_dir(args.dir)
    pointer_times, analysis_times, slack_times = (Counter() for _ in range(3))
    skips = 0
    for file in result_dir.rglob("*.txt"):
        repo = file.relative_to(result_dir).parts[0]
        pre_start: Optional[timedelta] = None
        last_ts = pre_end = anal_start = pre_start
        for line in file.read_text().splitlines():
            if (ts := get_ts(line)) is not None:
                last_ts = ts

            if "Performing points-to analysis..." in line:
                pre_start = get_ts(line)
            elif "CFG construction done" in line or "CFG extensions done" in line:
                assert pre_start is not None and ts is not None, file
                pointer_times.add(repo, tdiff(pre_start, ts))
                pre_start = None
                pre_end = ts
            elif ": Skipped" in line:
                skips += 1
            elif ": Found PSet" in line:
                anal_start = get_ts(line)
            elif ": Superlocation graph size" in line:
                assert anal_start is not None and ts is not None
                analysis_times.add(repo, tdiff(anal_start, ts))
                anal_start = None

        if pre_end is not None:
            assert last_ts is not None
            slack_times.add(repo, tdiff(pre_end, last_ts))

    pre_tot = pointer_times.total() + slack_times.total() - analysis_times.total()
    pre_time = timedelta(seconds=pre_tot)
    print(f"Number of pre-analyses: {len(pointer_times)}, total time: {pre_time}")
    analysis_time = timedelta(seconds=analysis_times.total())
    print(f"Number of runs: {len(analysis_times)}, total time: {analysis_time}")

    second = timedelta(seconds=1)
    desired_order = """
grpc}
etcd}
go-ethereum}
tidb}
prometheus}
kubernetes}
""".replace(
        "}", ""
    ).split()
    rows = []
    for repo in desired_order:
        if prt := pointer_times.cntr[repo]:
            analysis_h = timedelta(seconds=analysis_times.total(repo)) / second
            analysis_cnt = len(analysis_times.cntr[repo])
            pre_t = pointer_times.total(repo) + slack_times.total(repo)
            pre_h = timedelta(seconds=pre_t) / second - analysis_h
            reponame = f"\\textsl{{{repo}}}".ljust(20)
            rows.append(
                f" {reponame} & \\num{{{len(prt)}}} & \\SI{{{pre_h / len(prt):.0f}}}{{\\second}}"
                + f" & \\num{{{analysis_cnt}}} & \\SI{{{analysis_h / analysis_cnt:.2f}}}{{\\second}} \\\\\n"
            )

    print(
        rf"""
\begin{{tabular}}{{lrrrr}}
  \toprule
             & \multicolumn{{2}}{{c}}{{Pre-analysis}} & \multicolumn{{2}}{{c}}{{Main analysis}} \\
  Benchmark  & Runs  & Avg.~Time                     & Runs  & Avg.~Time \\
  \midrule
{"".join(rows)}  \midrule
    Total      & \num{{{len(pointer_times)}}} & \SI{{{pre_time / second / len(pointer_times):.0f}}}{{\second}} & \num{{{len(analysis_times)}}} & \SI{{{analysis_time / second / len(analysis_times):.2f}}}{{\second}} \\
  \bottomrule
\end{{tabular}}
"""
    )

    matplotlib.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42})

    bar_width = 0.8
    opacity = 0.8

    fig, ax = plt.subplots(figsize=(8, 5), num="Analysis times")
    # fig.canvas.set_window_title("Analysis times")

    bucket_size = 5
    timeout_time = 60
    assert timeout_time % bucket_size == 0
    num_buckets = timeout_time // bucket_size + 1
    counts = [0] * num_buckets
    for time in analysis_times:
        counts[min(num_buckets - 1, time // bucket_size)] += 1

    print(f"Timeouts: {counts[-1]} implicit, {skips} explicit")

    index = np.arange(num_buckets)
    plt.yscale("log")
    plt.grid(True, axis="y")
    plt.bar(index, counts, bar_width, alpha=opacity, edgecolor="black")

    plt.xlabel("Analysis time (s)")
    plt.ylabel("Count")
    plt.xticks(
        index - 0.5,
        [f"{i * bucket_size}" for i in range(num_buckets - 1)] + [f"≥ {timeout_time}"],
    )
    plt.tight_layout()

    if args.pdf:
        dir = ROOT / "pdfs"
        dir.mkdir(exist_ok=True)
        pdf_path = dir / result_dir.with_suffix(".pdf").name
        fig.savefig(pdf_path, bbox_inches="tight")
        print(f"Saved pdf to {pdf_path}")
    else:
        plt.show()
