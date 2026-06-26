# ARWSDProject — streetscape visual-complexity metrics

Computes perception-based **visual-complexity** metrics on street/scene images, plus a
CARLA simulator camera capture used to gather frames. The metrics reimplement:

> Ma, Guo, Lu, He & Wang (2023). *Developing an urban streetscape indexing based on
> visual complexity and self-organizing map.* **Building and Environment** 242:110549.
> https://doi.org/10.1016/j.buildenv.2023.110549

## The three metrics

| Metric | Meaning | Method (paper §) | Function |
|--------|---------|------------------|----------|
| **VCoT** | texture | box-counting fractal dimension of Canny edges (§3.2.1) | `metrics.vcot` |
| **VCoS** | shape | Potts segmentation → grayscale → 2-D entropy (§3.2.2) | `metrics.vcos` |
| **VCoC** | color | Potts segmentation → CIELab → mean CCM of 4 quarter-masks (§3.2.3) | `metrics.vcoc` |

`metrics.edge_density` is an extra Canny edge-pixel ratio (handy, but **not** one of the
paper's three metrics).

## Setup

Tested on **Python 3.13** (`pottslab` ships a Rust-core wheel for cp313, so no slow
pure-Python fallback):

```bash
python -m venv .venv
# Windows:           .venv\Scripts\activate
# Linux/macOS:       source .venv/bin/activate
pip install -r requirements.txt
```

`carla` is **not** in `requirements.txt` (it is tied to a specific simulator build); install
it separately only to run `CarlaControl/`.

## Run

```bash
python run_all.py        # computes all metrics for every pic/*.png -> metrics_results.csv
```

Or from your own code:

```python
import metrics
img = metrics.load_image("pic/1.png")     # read (BGR) + resize to 512x512
print(metrics.all_metrics(img))
```

## Important implementation notes

- **All inputs are resized to 512×512** (`metrics.IMAGE_SIZE`), matching the paper's uniform
  street-view images. This is required for comparability: **VCoC is an un-normalised pixel
  sum** and the **box-counting fractal dimension depends on image size**, so metrics computed
  on images of *different* native sizes are not comparable. (The sample `pic/` images are
  720×1280 and 941×1672 — different sizes — which is exactly why resizing matters.) Resizing a
  non-square image stretches it; this reproduces the paper's pipeline.
- **Channel order is BGR everywhere** (OpenCV's native order). All metric functions take a BGR
  image. The old notebooks disagreed (one segmented RGB then applied BGR grayscale weights);
  `metrics.py` is the single consistent source of truth.
- **VCoC / CCM semantics.** `calculate_ccm` is a faithful transcription of the paper's
  equation `CCM = Σ Gₐ(D(c, c̄))`. The Gaussian bandwidth α is `std(D)` (the paper's prose
  says "variance", but a Gaussian weighting `exp(-d²/2α²)` requires α in the same units as `d`,
  i.e. the standard deviation). Note that as defined this measure responds to color
  *homogeneity / dominant-color concentration* rather than to intuitive color *diversity*; that
  is a property of the published metric, kept as-is for faithful reproduction.
- **Parameters** live as named constants at the top of `metrics.py`
  (`POTTS_GAMMA=0.8`, `CCM_GAMMA=14`, `CANNY_LOW/HIGH=100/200`, `IMAGE_SIZE=512`).

## Files

| Path | Purpose |
|------|---------|
| `metrics.py` | **canonical implementation** of all metrics |
| `run_all.py` | batch driver → `metrics_results.csv` |
| `requirements.txt` | pinned dependencies (Python 3.11) |
| `pic/` | sample images (`1–3` are 720×1280, `4` is 941×1672); `pic/1.xml` is an ICY ROI export |
| `CarlaControl/RGBCamera.ipynb` | CARLA RGB-camera capture |
| `release_smoke_test.ipynb` | checks the `pottslab` Rust core is installed |

### Superseded scratch scripts

These predate `metrics.py` and duplicate it (the `.py`/`.ipynb` pairs had drifted apart). Kept
for reference; safe to delete once `metrics.py` is adopted:
`test.py` (VCoS), `test2.py` (VCoC), `calculate.py` (edge density), `VCoTTest.py` (VCoT),
`FDTest.py` (fractal-dimension sanity check), `PottsSegmentationTest.py` (Potts demo),
`VCoCTest.ipynb`, `VCoSTest.ipynb`, `VCoS.ipynb`, and `FDForPic.txt` (now regenerated as
`metrics_results.csv`).
