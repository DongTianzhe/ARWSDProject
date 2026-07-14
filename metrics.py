"""
metrics.py - Visual-complexity metrics for the ARWSD project (single source of truth).

Reimplements the three visual-complexity measures from:
  Ma, Guo, Lu, He & Wang (2023), "Developing an urban streetscape indexing based on
  visual complexity and self-organizing map", Building and Environment 242:110549.
  https://doi.org/10.1016/j.buildenv.2023.110549

  VCoT (texture) - box-counting fractal dimension of Canny edges        (sec. 3.2.1)
  VCoS (shape)   - Potts segmentation -> grayscale -> 2-D entropy        (sec. 3.2.2)
  VCoC (color)   - Potts segmentation -> CIELab -> mean CCM of 4 masks   (sec. 3.2.3)

Every input is first resized to IMAGE_SIZE x IMAGE_SIZE, matching the paper's uniform
512x512 street-view images. This matters: VCoC is an un-normalised pixel sum and the
box-counting fractal dimension depends on the range of box sizes, so both are only
comparable across images of the *same* size.

All public functions take a BGR uint8 image (OpenCV's native order) so the channel
convention is consistent everywhere (the old notebooks disagreed on BGR vs RGB).
"""
from __future__ import annotations

import os

import cv2 as cv
import numpy as np

# --- parameters (all values from the paper) ---
IMAGE_SIZE = 512          # paper uses uniform 512x512 SVIs (sec. 3.1)
POTTS_GAMMA = 0.8         # Potts partition strength; larger = coarser (sec. 3.2.2/3.2.3)
CCM_GAMMA = 14            # CCM normalisation factor (sec. 3.2.3, from Yoon & Kweon 2001)
CANNY_LOW, CANNY_HIGH = 100, 200
MEAN_KERNEL = 3           # neighbourhood size for the 2-D-entropy local mean


# --------------------------------------------------------------------------- #
# I/O and shared pre-processing
# --------------------------------------------------------------------------- #
def load_image(path: str, size: int | None = IMAGE_SIZE) -> np.ndarray:
    """Read a BGR image, failing loudly if it is missing, then resize to size x size."""
    img = cv.imread(path)
    if img is None:
        raise FileNotFoundError(
            f"could not read image {path!r} (cwd={os.getcwd()!r}); "
            f"check the path and the working directory"
        )
    return resize(img, size)


def resize(img: np.ndarray, size: int | None = IMAGE_SIZE) -> np.ndarray:
    """Resize to a fixed square to match the paper's 512x512 inputs.

    NOTE: a non-square image is stretched to square. This reproduces the paper's
    pipeline and, more importantly, makes VCoC and VCoT comparable across images of
    different native size. Pass size=None to skip resizing.
    """
    if size is None:
        return img
    return cv.resize(img, (size, size), interpolation=cv.INTER_AREA)


def potts_segment(img_bgr: np.ndarray, gamma: float = POTTS_GAMMA) -> np.ndarray:
    """Potts-segment a BGR uint8 image; returns a uint8 BGR piecewise-constant image."""
    import pottslab as pl  # heavy optional dep; imported lazily

    imgf64 = img_bgr.astype(np.float64) / 255.0          # pottslab needs float64 in [0, 1]
    seg = pl.min_l2_potts_2d(imgf64, gamma=gamma)
    return np.clip(seg * 255, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- #
# VCoT - texture (sec. 3.2.1)
# --------------------------------------------------------------------------- #
def canny_edges(img_bgr: np.ndarray) -> np.ndarray:
    """One-pixel Canny edge map (the paper applies Canny directly, with no blur)."""
    gray = cv.cvtColor(img_bgr, cv.COLOR_BGR2GRAY)
    return cv.Canny(gray, CANNY_LOW, CANNY_HIGH)


def vcot(img_bgr: np.ndarray) -> tuple[float, float]:
    """Visual complexity of texture: box-counting fractal dimension of Canny edges.

    Returns (fractal_dimension, r_squared).
    """
    from fracDimPy import box_counting  # heavy optional dep; imported lazily

    edges = canny_edges(img_bgr)
    dim, result = box_counting(edges, data_type="image")
    return float(dim), float(result["R2"])


def edge_density(img_bgr: np.ndarray) -> float:
    """Auxiliary measure (NOT one of the paper's three metrics): edge-pixel fraction."""
    edges = canny_edges(img_bgr)
    return float(np.count_nonzero(edges) / edges.size)


# --------------------------------------------------------------------------- #
# VCoS - shape (sec. 3.2.2)
# --------------------------------------------------------------------------- #
def two_d_entropy(gray: np.ndarray) -> float:
    """Abutaleb 2-D entropy: entropy of the joint histogram of (gray, local-mean gray).

    The local mean is a MEAN_KERNEL x MEAN_KERNEL box filter. Returned in nats; the
    paper does not specify a log base and it only rescales the value monotonically.
    """
    kernel = np.ones((MEAN_KERNEL, MEAN_KERNEL), np.float32) / (MEAN_KERNEL ** 2)
    mean = np.round(cv.filter2D(gray.astype(np.float32), -1, kernel)).astype(np.uint8)

    hist = np.zeros((256, 256), np.float64)
    np.add.at(hist, (gray.ravel(), mean.ravel()), 1)     # vectorised joint histogram
    p = hist / hist.sum()
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)))


def vcos(img_bgr: np.ndarray, gamma: float = POTTS_GAMMA) -> float:
    """Visual complexity of shape: 2-D entropy of the Potts-segmented grayscale image."""
    seg = potts_segment(img_bgr, gamma)
    gray = cv.cvtColor(seg, cv.COLOR_BGR2GRAY)
    return two_d_entropy(gray)


# --------------------------------------------------------------------------- #
# VCoC - color (sec. 3.2.3)
# --------------------------------------------------------------------------- #
def _to_lab(seg_bgr: np.ndarray) -> np.ndarray:
    """Convert a BGR uint8 image to CIELab with standard ranges (L in [0,100], a/b ~ +-128)."""
    lab = cv.cvtColor(seg_bgr, cv.COLOR_BGR2Lab)
    L, a, b = cv.split(lab)
    return cv.merge([
        L.astype(np.float32) * 100.0 / 255.0,
        a.astype(np.float32) - 128.0,
        b.astype(np.float32) - 128.0,
    ])


def calculate_ccm(block_lab: np.ndarray, gamma: float = CCM_GAMMA) -> float:
    """Color Complexity Measure of one CIELab mask.

    Paper eq.:  CCM = sum_{x,y in mask} G_alpha( D(c(x,y), mean_color) )
    with  D = 1 - exp(-E / gamma),  E = Euclidean CIELab distance to the mask mean,
    and  G_alpha(D) = exp(-D^2 / (2 * alpha^2)).

    alpha is std(D), NOT the variance: in a Gaussian weighting exp(-d^2/2alpha^2) the
    bandwidth must share units with d (= D), so it is the standard deviation. The
    paper's prose ("variance") is loose wording for the spread of D.
    """
    if block_lab.size == 0:
        return 0.0
    mean_color = block_lab.reshape(-1, 3).mean(axis=0)
    diff = block_lab - mean_color
    E = np.sqrt((diff ** 2).sum(axis=2))                 # Euclidean Lab distance to the mean
    D = 1 - np.exp(-E / gamma)
    alpha = np.std(D)
    if alpha < 1e-8:                                      # degenerate mask (all D equal)
        return 0.0
    G = np.exp(-(D ** 2) / (2 * alpha ** 2))
    return float(np.sum(G))


def vcoc(img_bgr: np.ndarray, gamma: float = POTTS_GAMMA) -> float:
    """Visual complexity of color: mean CCM over the four 1/4-image masks."""
    seg = potts_segment(img_bgr, gamma)
    lab = _to_lab(seg)
    h, w = lab.shape[:2]
    masks = [
        lab[:h // 2, :w // 2], lab[:h // 2, w // 2:],
        lab[h // 2:, :w // 2], lab[h // 2:, w // 2:],
    ]
    return float(np.mean([calculate_ccm(m) for m in masks]))


# --------------------------------------------------------------------------- #
def all_metrics(img_bgr: np.ndarray) -> dict:
    """Compute every metric for one BGR image (already resized by load_image)."""
    dim, r2 = vcot(img_bgr)
    return {
        "vcot_fractal_dim": dim,
        "vcot_r2": r2,
        "edge_density": edge_density(img_bgr),
        "vcos_entropy": vcos(img_bgr),
        "vcoc": vcoc(img_bgr),
    }
