#! /usr/bin/env python3

import sys

assert sys.version_info >= (3, 7), "Python %s is too old" % sys.version

import concurrent.futures
import random
import re
import subprocess
from argparse import REMAINDER, ArgumentParser
from datetime import datetime
from pathlib import Path
from threading import Lock

from tqdm import tqdm

ROOT = Path(__file__).parent.parent

parser = ArgumentParser()
parser.add_argument(
    "--parallel", "-p", type=int, default=4, help="Degree of parallelization."
)
parser.add_argument(
    "--repo",
    help="Analyze only benchmarks in this repository.",
)
parser.add_argument("--entry_point", help="Analyze only this particular entry point.")
parser.add_argument(
    "--dir",
    help="Name of the folder to store the results in (is results_[time] if absent).",
)
parser.add_argument(
    "--order",
    choices=["default", "shuffled", "by-time"],
    default="default",
    help="Choose an order to run the benchmarks in",
)
parser.add_argument("--flags", help="Flags to pass on to Goat.", nargs=REMAINDER)
args = parser.parse_args()

flags = "" if args.flags is None else " ".join(args.flags)

entry_progress_re = re.compile(r"Entry (\d+) of (\d+)")
num_primitives_re = re.compile(r"(\d+) primitives outside GOROOT")
entry_done_re = re.compile(r"Superlocation graph size: (\d+)")


def get_benchmark_filename(module_path: str, package: str) -> str:
    module_name = module_path.split("/", maxsplit=2)[-1]
    return f"{module_name}_{package}".replace("/", "#")


if __name__ == "__main__":
    start_time = datetime.now()
    result_dir = "results_" + start_time.strftime("%Y-%m-%d#%H:%M")
    if args.dir is not None:
        result_dir = args.dir
    results_root_directory = ROOT / f"benchmarks/{result_dir}"

    subprocess.run(
        "go build Goat".split(),
        text=True,
        check=True,
        cwd=ROOT,
    )

    print("Built Goat binary")

    p = subprocess.run(
        [str(ROOT / "benchmarks/list_packages.sh")],
        text=True,
        check=True,
        capture_output=True,
    )

    rawbenchmarks = [l.split(",") for l in p.stdout.splitlines()]
    if args.entry_point != None:
        benchmarks = []
        for b in rawbenchmarks:
            if args.entry_point == b[1]:
                benchmarks.append(b)
                break
    elif args.repo != None:
        benchmarks = []
        for b in rawbenchmarks:
            if args.repo in b[0]:
                benchmarks.append(b)
    else:
        benchmarks = rawbenchmarks

    if args.order == "shuffled":
        random.shuffle(benchmarks)
    elif args.order == "by-time":
        bench_to_index = {
            benchmark: i
            for i, benchmark in enumerate(
                (ROOT / "benchmarks/bench_order.txt").read_text().splitlines()
            )
        }

        benchmarks.sort(
            key=lambda b: bench_to_index.get(
                get_benchmark_filename(*b), len(benchmarks)
            )
        )

    PARALLEL = args.parallel
    lock = Lock()  # protects slots
    pbar_slots = [False] * PARALLEL

    inner_pbar_format = (
        "{desc}: {percentage:3.0f}%|{bar}| "
        "{n:.1f}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
    )

    def analyze_benchmark(outer_pbar, module_path: str, package: str):
        with lock:
            for pbar_slot, taken in enumerate(pbar_slots):
                if not taken:
                    pbar_slots[pbar_slot] = True
                    break
            else:
                assert False

        try:
            benchmark_name = module_path.split("/")[2]

            results_directory = results_root_directory / benchmark_name
            results_directory.mkdir(parents=True, exist_ok=True)

            results_filename = get_benchmark_filename(module_path, package) + ".txt"

            with (results_directory / results_filename).open(
                "w", buffering=1
            ) as outfile, tqdm(
                unit="entry",
                desc=package,
                position=pbar_slot,
                total=1,
                leave=False,
                miniters=0.01,
                bar_format=inner_pbar_format,
                dynamic_ncols=True,
            ) as pbar:

                command = f"""./Goat -gopath {ROOT / 'external/gfuzz'} -modulepath {module_path}
                            -include-tests -metrics {flags} -task collect-primitives {package}""".split()

                # Put the command to run the analysis at the top of the log
                print(*command, file=outfile, flush=True)

                with subprocess.Popen(
                    command,
                    cwd=ROOT,
                    text=True,
                    stderr=subprocess.STDOUT,
                    stdout=subprocess.PIPE,
                ) as p:
                    num_primitives = 0
                    assert p.stdout is not None  # satisfy MyPy
                    for line in p.stdout:
                        print(line, end="", file=outfile)

                        match = entry_progress_re.search(line)
                        if match:
                            _, total = map(int, match.groups())
                            pbar.total = total
                            # Maybe refresh outer_pbar
                            outer_pbar.update(0)

                        match = num_primitives_re.search(line)
                        if match:
                            num_primitives = int(match.groups()[0])
                            if num_primitives == 0:
                                pbar.update(1)

                        match = entry_done_re.search(line)
                        if match:
                            pbar.update(1 / num_primitives)

                tqdm.write(
                    f'{module_path} {package} {"succeded!" if p.returncode == 0 else "failed!"}'
                )
        finally:
            with lock:
                pbar_slots[pbar_slot] = False

    with tqdm(
        unit="benchmark",
        position=len(pbar_slots),
        total=len(benchmarks),
        miniters=0,
        dynamic_ncols=True,
    ) as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL) as executor:
            futures = [
                executor.submit(analyze_benchmark, pbar, *bench) for bench in benchmarks
            ]

            for future in concurrent.futures.as_completed(futures):
                pbar.update(1)
                future.result()  # Possibly unwraps exception
