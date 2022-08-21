from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent


def get_dir(result_arg: str) -> str:
    if not result_arg:
        results_list = [p.name for p in ROOT.iterdir() if p.name.startswith("results_")]

        dates = []
        # Get latest result folder
        for r in results_list:
            datestr = r.split("_")[1].replace("#", " ")[2:] + ":00"
            dates.append(datetime.strptime(datestr, "%y-%m-%d %H:%M:%S"))

        biggest = -1
        for i in range(len(dates)):
            if biggest == -1:
                biggest = i
            elif dates[i] > dates[biggest]:
                biggest = i
        return "results_" + dates[biggest].strftime("%Y-%m-%d#%H:%M")
    else:
        return result_arg
