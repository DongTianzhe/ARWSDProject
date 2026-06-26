"""Batch-compute every visual-complexity metric over pic/*.png and write a CSV.

Replaces the hand-pasted FDForPic.txt with a regenerable, structured result table.
Run from anywhere:  python run_all.py
"""
import csv
import glob
import os

import metrics

HERE = os.path.dirname(os.path.abspath(__file__))
PIC_DIR = os.path.join(HERE, "pic")
OUT_CSV = os.path.join(HERE, "metrics_results.csv")


def main() -> None:
    paths = sorted(glob.glob(os.path.join(PIC_DIR, "*.png")))
    if not paths:
        raise FileNotFoundError(f"no .png images found in {PIC_DIR!r}")

    rows = []
    for path in paths:
        img = metrics.load_image(path)               # resized to 512x512 inside
        row = {"image": os.path.basename(path)}
        row.update({k: round(v, 4) for k, v in metrics.all_metrics(img).items()})
        rows.append(row)
        print(row)

    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nwrote {OUT_CSV}")


if __name__ == "__main__":
    main()
