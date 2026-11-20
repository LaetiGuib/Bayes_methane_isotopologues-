#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bayesian classification of methane origin from bulk and clumped isotopes.

ONE script, TWO model schemes (switch in cell 00 with MODEL_MODE):

    MODEL_MODE = 'TMO'      3 classes  Thermogenic / Microbial / Oxidation
    MODEL_MODE = 'BIO_ABI'  2 classes  Biotic (T + M + O sheets merged) / Abiotic

HOW TO USE
    Run with F5 in Spyder (or run the '#%%' cells in order). Edit ONLY cell 00.
    Everything that differs between the 2-class and 3-class models (classes,
    Excel sheets, labels, colours, gate exponents, display thresholds) is
    collected in the SCHEMES dictionary of cell 00; the rest of the script is
    class-agnostic and loops over CLASSES.
    - TMO mode      : also runs the Tyne et al. (2021) external test (SI S11, Fig. S15).
    - BIO_ABI mode  : also draws the two-panel pointwise diagnostic of one
                      external sample (SI S9, Fig. S16).
    External samples (Excel/CSV or MANUAL_SAMPLES) are evaluated in both modes
    with the fitted KDEs and are NEVER added to the training data.

SI crosswalk
    S3 bandwidths | S4 continuity-weighted KDE + MST bridges | S5 competitive
    bulk priors | S6 gated projection of the bulk prior into clumped space |
    S7 clumped log-likelihoods | S8 posterior and visual support gate |
    S9 pointwise posterior with bulk log-likelihood tempering.

DATA SCOPE
    By default the bulk KDEs (and thus the bulk priors, S5) are fitted to the
    PAIRED bulk+clumped samples only, not to the 3,858-sample bulk-only
    compilation of SI S1 / Fig. 1. 

Model class probabilities are NOT physical fractions of methane endmembers.
"""
#%% 00 — EDIT HERE: MODEL MODE, INPUTS, GATES, EXPORTS
from pathlib import Path

# ---------------------------------------------------------------------------
# 0) MODEL SCHEME — the only switch needed to go from 3 classes to 2 classes
# ---------------------------------------------------------------------------
MODEL_MODE = 'BIO_ABI'      # 'TMO' (3 classes)  or  'BIO_ABI' (2 classes)

# ---------------------------------------------------------------------------
# 1) Files
# ---------------------------------------------------------------------------
DATABASE_FILE = Path(r"/Users//Documents/methane_isotope_database.xlsx")
OUTPUT_DIR = Path.home() / 'Downloads' / f'{MODEL_MODE}_publication_outputs'

# OPTIONAL — fit the BULK KDEs / bulk priors (S5) on the larger bulk-only
# compilation (e.g. the 3,858 natural samples of SI S1) instead of the paired
# samples. Keys of BULK_ONLY_SHEETS must be the classes of the chosen MODEL_MODE
# (T, M, O  or  BIO, ABI); each value is a list of sheet names holding the
# columns COL_BULK (delta13C_..., deltaD_...). The clumped KDEs (S7) and the
# projection (S6) always keep using the PAIRED samples.
BULK_ONLY_FILE = None      # e.g. Path('/path/to/bulk_only_compilation.xlsx')
BULK_ONLY_SHEETS = None    # e.g. {'T': ['Thermogenic'], 'M': ['Microbial'], 'O': ['Oxidation']}

# ---------------------------------------------------------------------------
# 2) Scheme definitions (THE ONLY PLACE WHERE THE 2- AND 3-CLASS MODELS DIFFER)
# ---------------------------------------------------------------------------
# SHEETS      : Excel sheets concatenated to form each class.
# *_GAMMA     : exponents of the pointwise bulk tempering (S9) and of the
#               clumped display gate (S8).
# MIN_SHOW    : lowest probability drawn in the clumped posterior maps.
# *_OVERLAY   : drawing order / transparency of the overlaid maps.
# BULK_PRIOR_*: colour scale of the projected-prior figure (S6).
# EQ_LABEL_OFFSETS: placement (points) of the temperature labels on the equilibrium curve.
SCHEMES = {
    'TMO': dict(
        CLASSES=['T', 'M', 'O'],
        SHEETS={'T': ['Thermo_clumped'], 'M': ['Microbial_clumped'], 'O': ['Oxidation']},
        NAMES={'T': 'Thermogenic', 'M': 'Microbial', 'O': 'Oxidation'},
        CMAPS={'T': 'Reds', 'M': 'Blues', 'O': 'Greens'},
        POINT_COLORS={'T': 'firebrick', 'M': 'navy', 'O': 'darkgreen'},
        POINTWISE_BULK_GAMMA=4.0,
        CLUMP_DISPLAY_GAMMA=0.4,
        MIN_SHOW={'T': 0.05, 'M': 0.05, 'O': 0.02},
        BULK_OVERLAY=dict(
            draw_order=['M', 'O', 'T'],
            alpha={'T': 0.70, 'M': 0.50, 'O': 0.50},
            zorder={'M': 10, 'O': 11, 'T': 12},
            contour_color={'T': 'firebrick', 'M': 'navy', 'O': 'darkgreen'}),
        POST_OVERLAY=dict(
            alpha={'T': 0.70, 'M': 0.75, 'O': 0.99},
            zorder={'T': 3, 'M': 2, 'O': 1},
            cmaps={'T': 'Oranges', 'M': 'Blues', 'O': 'Greens'}),
        BULK_PRIOR_RANGE=(0.15, 0.45),
        BULK_PRIOR_TICKS=[0.05, 0.10, 0.20, 0.30, 0.40, 0.50],
        EQ_LABEL_OFFSETS={0: (8, 2), 50: (8, 2), 200: (8, 2), 1500: (8, 2)},
    ),
    'BIO_ABI': dict(
        CLASSES=['BIO', 'ABI'],
        SHEETS={'BIO': ['Thermo_clumped', 'Microbial_clumped', 'Oxidation'],
                'ABI': ['Abiotic_clumped']},
        NAMES={'BIO': 'Biotic', 'ABI': 'Abiotic'},
        CMAPS={'BIO': 'Blues', 'ABI': 'Oranges'},
        POINT_COLORS={'BIO': 'navy', 'ABI': 'darkorange'},
        POINTWISE_BULK_GAMMA=0.4,
        CLUMP_DISPLAY_GAMMA=0.2,
        MIN_SHOW={'BIO': 0.02, 'ABI': 0.02},
        BULK_OVERLAY=dict(
            draw_order=['BIO', 'ABI'],
            alpha={'BIO': 0.98, 'ABI': 0.48},
            zorder={'BIO': 10, 'ABI': 11},
            contour_color={'BIO': 'navy', 'ABI': 'darkorange'}),
        POST_OVERLAY=dict(
            alpha={'BIO': 0.98, 'ABI': 0.48},
            zorder={'BIO': 2, 'ABI': 3},
            cmaps={'BIO': 'Blues', 'ABI': 'Oranges'}),
        BULK_PRIOR_RANGE=(0.0, 1.0),
        BULK_PRIOR_TICKS=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        EQ_LABEL_OFFSETS={0: (10, 7), 50: (10, -10), 200: (-38, -13), 1500: (-5, -17)},
    ),
}
if MODEL_MODE not in SCHEMES:
    raise ValueError(f"MODEL_MODE must be one of {list(SCHEMES)}; got {MODEL_MODE!r}")
SCHEME = SCHEMES[MODEL_MODE]
CLASSES = SCHEME['CLASSES']
SHEETS = SCHEME['SHEETS']
NAMES = SCHEME['NAMES']
CMAPS = SCHEME['CMAPS']
POINT_COLORS = SCHEME['POINT_COLORS']
MIN_SHOW = SCHEME['MIN_SHOW']

# ---------------------------------------------------------------------------
# 3) External samples (evaluated pointwise, never used for fitting)
# ---------------------------------------------------------------------------
# Excel/CSV with columns sample_id, d13C, dD, D13CH3D, D12CH2D2 (the four long
# column names of the database are also accepted); optional: site, study, doi,
# source, expected_set, notes. All four isotope values are required, in per mil.
EXTERNAL_SAMPLES_FILE = None  # Path.home()/'Downloads'/'external_samples.xlsx'
EXTERNAL_SHEET = 0
MANUAL_SAMPLES = [
    # Example used for SI Fig. S16 (BIO_ABI mode). Set to [] to disable.
    dict(sample_id='NSHQ04', d13C=4.177, dD=-227.396,
         D13CH3D=0.229, D12CH2D2=-24.50, source='Nothaft et al.'),
]
POINTWISE_FIG_SAMPLE_ID = 'NSHQ04'   # BIO_ABI two-panel diagnostic; None = first external sample

# ---------------------------------------------------------------------------
# 4) Numerical gates (thresholds T in [0,1), exponents gamma > 0)
# ---------------------------------------------------------------------------
# S6: support of the paired bulk observations used as projection weights.
PROJECTION_BULK_T = 0.001
PROJECTION_BULK_GAMMA = 0.4
USE_GATED_PROJECTION = True

# S9: pointwise tempering of the bulk log-densities (independent of the map gates).
POINTWISE_BULK_T = 0.001
POINTWISE_BULK_GAMMA = SCHEME['POINTWISE_BULK_GAMMA']   # TMO 4.0 | BIO_ABI 0.4

# S8: clumped support gate — MAP DISPLAY ONLY, not part of the probabilities.
CLUMP_DISPLAY_T = 0.001
CLUMP_DISPLAY_GAMMA = SCHEME['CLUMP_DISPLAY_GAMMA']     # TMO 0.4 | BIO_ABI 0.2
GATE_SUBSAMPLE = 4          # support computed on every 4th grid node, then interpolated
COMMON_SMOOTH_GATE = 4.0    # gaussian smoothing of the gate (grid pixels)

# S5: bulk display gate (quantile floor + power), maps only.
BULK_GATE_FLOOR_QUANTILE = 0.002
BULK_GATE_POWER = 0.70

# ---------------------------------------------------------------------------
# 5) Figures and exports
# ---------------------------------------------------------------------------
BULK_XLIM = (-110.0, 20.0)
BULK_YLIM = (-600.0, 300.0)
CLUMP_XLIM = (-20.0, 30.0)
CLUMP_YLIM = (-70.0, 120.0)
SHOW_BULK_DATA_POINTS = True
SHOW_CLUMPED_DATA_POINTS = False

TYNE_PIE_METHOD = 'Adjusted'  # TMO only: Bulk, Clumped, Original, Adjusted
TYNE_PIE_SIZE = 19
TYNE_SHOW_LABELS = True
RUN_POINTWISE_MC = False  # Optional Gaussian analytical-error Monte Carlo; expensive
POINTWISE_MC_N = 500
POINTWISE_MC_SEED = 42

EXPORT_PDF = True
EXPORT_PNG = True
EXPORT_DPI = 300
SHOW_FIGURES = True   # True: display each figure (Spyder: Preferences > IPython console >
                      # Graphics > Backend = 'Inline' for the Plots pane, or 'Qt' for windows)
EXPORT_EXCEL = True

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
if not DATABASE_FILE.is_file():
    raise FileNotFoundError(f'Update DATABASE_FILE in cell 00: {DATABASE_FILE}')
if (BULK_ONLY_FILE is None) != (BULK_ONLY_SHEETS is None):
    raise ValueError('Set BOTH BULK_ONLY_FILE and BULK_ONLY_SHEETS, or neither.')
if BULK_ONLY_SHEETS is not None and set(BULK_ONLY_SHEETS) != set(CLASSES):
    raise KeyError(f'BULK_ONLY_SHEETS keys must be {CLASSES} for MODEL_MODE={MODEL_MODE!r}.')

#%% 01 — IMPORTS / DATA SCHEMA
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1 import make_axes_locatable
from numpy.linalg import eigh
from scipy.ndimage import gaussian_filter, zoom
from scipy.spatial.distance import pdist, squareform
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.special import softmax
from sklearn.model_selection import KFold, LeaveOneOut
from sklearn.neighbors import KernelDensity

import matplotlib
print('Matplotlib backend:', matplotlib.get_backend(), '| output folder:', OUTPUT_DIR)

# Column names of the training database (same for every class sheet).
COL_BULK = {'d13C': 'delta13C_CH4_permil_VPDB', 'dD': 'deltaD_CH4_permil_VSMOW'}
COL_CLUMP = {'D13CH3D': 'Delta13CH3D_permil', 'D12CH2D2': 'Delta12CH2D2_permil'}


def save_fig(name, fig=None):
    """Export a figure as PDF/PNG (switches in cell 00), then show and close it."""
    fig = plt.gcf() if fig is None else fig
    stem = f'{MODEL_MODE}_{name}'
    if EXPORT_PDF:
        fig.savefig(OUTPUT_DIR / (stem + '.pdf'), bbox_inches='tight')
    if EXPORT_PNG:
        fig.savefig(OUTPUT_DIR / (stem + '.png'), dpi=EXPORT_DPI, bbox_inches='tight')
    print('Figure saved:', stem)
    if SHOW_FIGURES:
        # Do NOT close the figure here: with an interactive backend (Spyder Qt) show()
        # returns immediately and closing would make the window vanish at once.
        plt.show()
    else:
        plt.close(fig)


#%% 02 — KDE MODEL (SI S3–S8)
# %% LOAD PAIRED DATA

def extract_paired_data(df, col_bulk, col_clump):
    """
    Extract paired bulk and clumped-isotope coordinates.

    Array convention used throughout the script
    --------------------------------------------
    BULK[:, 0]  = δ13C-CH4
    BULK[:, 1]  = δD-CH4

    CLUMP[:, 0] = Δ13CH3D
    CLUMP[:, 1] = Δ12CH2D2
    """

    required_columns = [
        col_bulk["d13C"],          # column 0: δ13C
        col_bulk["dD"],            # column 1: δD
        col_clump["D13CH3D"],      # column 0: Δ13CH3D
        col_clump["D12CH2D2"],     # column 1: Δ12CH2D2
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise KeyError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    values = (
        df.loc[:, required_columns]
        .apply(pd.to_numeric, errors="coerce")
    )

    invalid_rows = values.isna().any(axis=1)

    if invalid_rows.any():
        bad_rows = df.index[invalid_rows].tolist()

        raise ValueError(
            "The paired bulk/clumped columns contain missing or "
            f"non-numeric values in {invalid_rows.sum()} row(s). "
            f"First affected rows: {bad_rows[:10]}"
        )

    values = values.to_numpy(dtype=float)

    bulk = values[:, :2]       # δ13C, δD
    clumped = values[:, 2:]    # Δ13CH3D, Δ12CH2D2

    return bulk, clumped


def read_class_sheets(path, sheets):
    """Concatenate one or several Excel sheets into one class table."""
    return pd.concat([pd.read_excel(path, sheet_name=s, header=0) for s in sheets],
                     ignore_index=True)


def extract_bulk_only(df, col_bulk, dataset_name):
    """Bulk-only samples (no clumped data needed); incomplete rows are dropped."""
    cols = [col_bulk['d13C'], col_bulk['dD']]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f'{dataset_name}: missing columns: {missing}')
    values = df.loc[:, cols].apply(pd.to_numeric, errors='coerce')
    ok = values.notna().all(axis=1)
    if (~ok).any():
        print(f'{dataset_name}: {int((~ok).sum())} incomplete bulk row(s) dropped')
    return values.loc[ok].to_numpy(dtype=float)


# PAIRED samples: BULK[k] and CLUMP[k] are the same rows (same samples).
# They feed the clumped KDEs (S7), the projection (S6) and the pointwise step (S9).
BULK = {}
CLUMP = {}
for k in CLASSES:
    BULK[k], CLUMP[k] = extract_paired_data(
        read_class_sheets(DATABASE_FILE, SHEETS[k]), COL_BULK, COL_CLUMP)
    print(f"{NAMES[k]}: {BULK[k].shape[0]} paired measurements")

# BULK_FIT[k]: samples used ONLY to fit the bulk KDEs and the bulk priors (S5).
# Default = the paired samples. With BULK_ONLY_FILE / BULK_ONLY_SHEETS (cell 00)
# the bulk side is fitted to the larger bulk-only compilation (e.g. 3,858 samples).
if BULK_ONLY_FILE is None:
    BULK_FIT = {k: BULK[k] for k in CLASSES}
else:
    BULK_FIT = {k: extract_bulk_only(read_class_sheets(BULK_ONLY_FILE, BULK_ONLY_SHEETS[k]),
                                     COL_BULK, f'bulk-only {k}')
                for k in CLASSES}
    print('\nBulk KDEs/priors fitted to the bulk-only compilation:',
          {k: len(BULK_FIT[k]) for k in CLASSES})

# Sanity check of coordinate order
print("\nCoordinate ranges:")
for k in CLASSES:
    print(f"{k} bulk (fit): d13C = [{BULK_FIT[k][:, 0].min():.1f}, {BULK_FIT[k][:, 0].max():.1f}] permil; "
          f"dD = [{BULK_FIT[k][:, 1].min():.1f}, {BULK_FIT[k][:, 1].max():.1f}] permil")
    print(f"{k} clumped: D13CH3D = [{CLUMP[k][:, 0].min():.1f}, {CLUMP[k][:, 0].max():.1f}] permil; "
          f"D12CH2D2 = [{CLUMP[k][:, 1].min():.1f}, {CLUMP[k][:, 1].max():.1f}] permil")

#%% BANDWIDTH SELECTION

def whitening_transform(X, eps=1e-8):
    X = np.asarray(X, float)
    mu = X.mean(axis=0)
    covariance = np.cov((X - mu).T, bias=False) + eps * np.eye(X.shape[1])
    eigenvalues, eigenvectors = eigh(covariance)
    transform = eigenvectors @ np.diag(1.0 / np.sqrt(np.maximum(eigenvalues, eps))) @ eigenvectors.T
    return mu, transform


def silverman_h0(Z):
    n, d = Z.shape
    if n < 2:
        return 0.5
    mad = np.median(np.abs(Z - np.median(Z, axis=0)), axis=0) + 1e-9
    sigma = float(np.sqrt(np.mean(mad**2)))
    return sigma * n ** (-1.0 / (d + 4.0))


def cv_best_bandwidth(Z, grid, cv_mode="auto", k_splits=5, seed=0):
    n = len(Z)
    if cv_mode == "auto":
        cv_mode = "loo" if n <= 150 else "kfold"

    if cv_mode == "loo":
        cv = LeaveOneOut()
    else:
        cv = KFold(
            n_splits=min(k_splits, max(2, n)),
            shuffle=True,
            random_state=seed,
        )

    scores = {}
    for h in grid:
        total = 0.0
        count = 0
        for train, test in cv.split(Z):
            kde = KernelDensity(kernel="gaussian", bandwidth=float(h)).fit(Z[train])
            total += float(kde.score(Z[test])) * len(test)
            count += len(test)
        scores[float(h)] = total / max(1, count)

    return max(scores, key=scores.get)


def bandwidth_config(n, n0=200):
    """Return the cross-validation grid without post-CV inflation."""
    if n < n0:
        return dict(grid_low=0.03, grid_high=1.5, grid_size=31, cv_mode="loo")
    return dict(grid_low=0.05, grid_high=2.0, grid_size=25, cv_mode="kfold")


def fit_whitened_kde(
    X,
    grid_low=0.05,
    grid_high=2.0,
    grid_size=25,
    cv_mode="auto",
    k_splits=5,
    seed=0,
):
    """Fit the initial KDE using the bandwidth selected directly by CV."""
    X = np.asarray(X, float)
    mu, transform = whitening_transform(X)
    Z = (X - mu) @ transform.T

    h0 = silverman_h0(Z)
    grid = np.geomspace(
        max(h0 * grid_low, 1e-3),
        max(h0 * grid_high, h0 * grid_low * 1.01),
        grid_size,
    )
    h = float(cv_best_bandwidth(Z, grid, cv_mode, k_splits, seed))

    kde = KernelDensity(kernel="gaussian", bandwidth=h).fit(Z)
    inverse = np.linalg.inv(transform)
    sigma_x = h**2 * (inverse.T @ inverse)
    return {"mu": mu, "A": transform, "h": h, "kde": kde, "Sigma_x": sigma_x}


def axis_bandwidths(sigma_x):
    return float(np.sqrt(sigma_x[0, 0])), float(np.sqrt(sigma_x[1, 1]))


def bilinear_interp(xv, yv, field, points):
    points = np.asarray(points, float)
    x = points[:, 0]
    y = points[:, 1]

    i = np.clip(np.searchsorted(xv, x) - 1, 0, len(xv) - 2)
    j = np.clip(np.searchsorted(yv, y) - 1, 0, len(yv) - 2)

    x0, x1 = xv[i], xv[i + 1]
    y0, y1 = yv[j], yv[j + 1]
    tx = np.where(x1 > x0, (x - x0) / (x1 - x0), 0.0)
    ty = np.where(y1 > y0, (y - y0) / (y1 - y0), 0.0)

    f00 = field[j, i]
    f10 = field[j, i + 1]
    f01 = field[j + 1, i]
    f11 = field[j + 1, i + 1]

    return (
        (1 - tx) * (1 - ty) * f00
        + tx * (1 - ty) * f10
        + (1 - tx) * ty * f01
        + tx * ty * f11
    )


# <<BULK-CLASSES>> bulk KDEs: one per bulk class (here bulk classes = CLASSES)
BASE_MODELS_BULK = {
    k: fit_whitened_kde(BULK_FIT[k], **bandwidth_config(len(BULK_FIT[k])), seed=0)
    for k in CLASSES
}
BASE_MODELS_CLUMP = {
    k: fit_whitened_kde(CLUMP[k], **bandwidth_config(len(CLUMP[k])), seed=0)
    for k in CLASSES
}

# =============================================================================
# CLASS-SPECIFIC BANDWIDTHS SELECTED BY CROSS-VALIDATION
# =============================================================================
#
# The isotropic bandwidth selected in whitened coordinates is transformed
# back into the original isotope coordinates. Only axis-specific safety
# limits are applied: there is no post-CV inflation and no interclass
# bandwidth shrinkage.
# =============================================================================

BULK_BW_MIN = (1e-3, 1e-3)
BULK_BW_MAX = (20.0, 100.0)

CLUMP_BW_MIN = (1e-3, 1e-3)
CLUMP_BW_MAX = (4.25, 4.25)


def clip_axis_bandwidths(
    bandwidths,
    lower_limits,
    upper_limits,
):
    """Apply independent safety limits to the two coordinate bandwidths."""
    return tuple(
        float(
            np.clip(
                bandwidths[axis],
                lower_limits[axis],
                upper_limits[axis],
            )
        )
        for axis in (0, 1)
    )


BW_BULK = {
    k: clip_axis_bandwidths(
        axis_bandwidths(BASE_MODELS_BULK[k]["Sigma_x"]),
        BULK_BW_MIN,
        BULK_BW_MAX,
    )
    for k in CLASSES
}

BW_CLUMP = {
    k: clip_axis_bandwidths(
        axis_bandwidths(BASE_MODELS_CLUMP[k]["Sigma_x"]),
        CLUMP_BW_MIN,
        CLUMP_BW_MAX,
    )
    for k in CLASSES
}

print("\nCross-validated class-specific bandwidths:")
for k in CLASSES:
    print(f"  {k} bulk={BW_BULK[k]} | clumped={BW_CLUMP[k]}")

print("\nBULK BANDWIDTH DIAGNOSTIC")

for k in CLASSES:

    raw_bw = axis_bandwidths(
        BASE_MODELS_BULK[k]["Sigma_x"]
    )

    range_d13C = np.ptp(BULK_FIT[k][:, 0])
    range_dD = np.ptp(BULK_FIT[k][:, 1])

    print(
        f"{k}: "
        f"raw bandwidth = ({raw_bw[0]:.2f}, {raw_bw[1]:.2f}) | "
        f"used bandwidth = ({BW_BULK[k][0]:.2f}, {BW_BULK[k][1]:.2f}) | "
        f"data range = ({range_d13C:.1f}, {range_dD:.1f})"
    )

#%% CONTINUITY-REGULARIZED KDE

def build_mst_bridge(Z, gap_factor=2.0, point_spacing=0.20):
    """Insert points along unusually long edges of the minimum spanning tree."""
    Z_unique = np.unique(np.asarray(Z, float), axis=0)
    if len(Z_unique) < 2:
        return np.empty((0, 2), float)

    distances = squareform(pdist(Z_unique, metric="euclidean"))
    mst = minimum_spanning_tree(distances).toarray()
    rows, cols = np.where(mst > 0.0)
    lengths = mst[rows, cols]
    if len(lengths) == 0:
        return np.empty((0, 2), float)

    threshold = float(gap_factor) * float(np.median(lengths))
    bridges = []
    for i, j, length in zip(rows, cols, lengths):
        if length <= threshold:
            continue
        n_segments = max(2, int(np.ceil(float(length) / float(point_spacing))))
        fractions = np.linspace(0.0, 1.0, n_segments + 1)[1:-1]
        bridges.append(Z_unique[i] + fractions[:, None] * (Z_unique[j] - Z_unique[i]))

    return np.vstack(bridges) if bridges else np.empty((0, 2), float)


def fit_continuity_kde(
    data,
    bw_x,
    bw_y,
    *,
    synthetic_weight_fraction=0.095,
    low_density_fraction_within_synthetic=0.01,
    synthetic_rank_center=0.50,
    synthetic_rank_width=0.30,
    low_density_percentile=10.0,
    iso_temp=1.0,
    n_samples=40_000,
    random_state=42,
    use_correlation=False,
    correlation_strength=0.50,
    correlation_clip=0.85,
    use_mst_bridge=False,
    mst_bridge_weight=0.05,
    mst_gap_factor=1.25,
    mst_point_spacing=0.15,
    return_sample=False,
):
    """
    Fit the final continuity-regularized KDE.

    The final KDE is fitted to four explicitly tracked components:

        1. original observations;
        2. intermediate-density points sampled from a pilot KDE;
        3. points sampled from the lowest-density percentile of that pilot KDE;
        4. deterministic MST bridge points.

    ``synthetic_weight_fraction`` is the collective weight of components 2 + 3.
    ``low_density_fraction_within_synthetic`` specifies the fraction of that
    synthetic weight assigned to component 3, not a fraction of the full KDE.

    With the default configuration and at least one MST bridge point, the
    collective weights are:

        original observations        = 85.500%
        intermediate pilot support   =  9.405%
        lowest-density pilot support =  0.095%
        MST bridge support           =  5.000%

    The two pilot-support groups therefore contribute 9.5% in total.
    The low-density component is sampled from the lowest 10% of pilot-KDE
    density ranks and receives 1% of the collective pilot-support weight.
    """
    data = np.asarray(data, float)

    if data.ndim != 2 or data.shape[1] != 2 or len(data) < 2:
        raise ValueError("data must contain at least two 2-D observations")

    synthetic_weight_fraction = float(synthetic_weight_fraction)
    low_density_fraction_within_synthetic = float(
        low_density_fraction_within_synthetic
    )
    mst_bridge_weight = float(mst_bridge_weight)

    if synthetic_weight_fraction < 0.0 or mst_bridge_weight < 0.0:
        raise ValueError("KDE component weights must be non-negative")

    if not 0.0 <= low_density_fraction_within_synthetic <= 1.0:
        raise ValueError(
            "low_density_fraction_within_synthetic must be between 0 and 1"
        )

    if synthetic_weight_fraction + mst_bridge_weight >= 1.0:
        raise ValueError(
            "synthetic and MST weights must sum to less than one"
        )

    if not 0.0 < float(low_density_percentile) < 100.0:
        raise ValueError("low_density_percentile must be between 0 and 100")

    # ------------------------------------------------------------------
    # Kernel geometry in the original isotope coordinates
    # ------------------------------------------------------------------
    if use_correlation:
        rho = float(np.corrcoef(data[:, 0], data[:, 1])[0, 1])

        if not np.isfinite(rho):
            rho = 0.0

        rho = float(
            np.clip(
                correlation_strength * rho,
                -correlation_clip,
                correlation_clip,
            )
        )

        covariance = np.array(
            [
                [bw_x**2, rho * bw_x * bw_y],
                [rho * bw_x * bw_y, bw_y**2],
            ],
            float,
        )

        scale = np.linalg.inv(
            np.linalg.cholesky(covariance)
        )

    else:
        scale = np.diag(
            [1.0 / bw_x, 1.0 / bw_y]
        )

    inverse_scale = np.linalg.inv(scale)
    scaled_data = data @ scale.T

    # ------------------------------------------------------------------
    # Pilot KDE and Monte Carlo support
    # ------------------------------------------------------------------
    pilot = KernelDensity(
        kernel="gaussian",
        bandwidth=iso_temp,
    ).fit(scaled_data)

    intermediate_support = np.empty((0, 2), float)
    low_density_support = np.empty((0, 2), float)

    if synthetic_weight_fraction > 0.0:
        candidate_scaled = pilot.sample(
            n_samples=n_samples,
            random_state=random_state,
        )

        candidate_original = (
            candidate_scaled @ inverse_scale.T
        )

        candidate_log_density = pilot.score_samples(
            candidate_scaled
        )

        order = np.argsort(
            candidate_log_density,
            kind="mergesort",
        )

        density_rank = np.empty(n_samples, float)
        density_rank[order] = (
            np.arange(n_samples, dtype=float) + 0.5
        ) / n_samples

        low_density_cutoff = (
            float(low_density_percentile) / 100.0
        )

        low_density_mask = density_rank <= low_density_cutoff

        # Gaussian preference for intermediate-density support. The lowest
        # density pool is excluded here because it is sampled separately below.
        intermediate_selection_weight = np.exp(
            -0.5
            * (
                (density_rank - float(synthetic_rank_center))
                / float(synthetic_rank_width)
            ) ** 2
        )
        intermediate_selection_weight[low_density_mask] = 0.0

        if (
            not np.isfinite(intermediate_selection_weight.sum())
            or intermediate_selection_weight.sum() <= 0.0
        ):
            raise RuntimeError(
                "No eligible intermediate-density pilot points remained."
            )

        low_density_indices = np.flatnonzero(low_density_mask)
        if len(low_density_indices) == 0:
            raise RuntimeError(
                "The lowest-density pilot pool is empty."
            )

        n_synthetic_total = int(
            round(n_samples * synthetic_weight_fraction)
        )

        n_low_density = int(
            round(
                n_synthetic_total
                * low_density_fraction_within_synthetic
            )
        )
        n_low_density = min(
            max(n_low_density, 0),
            n_synthetic_total,
        )
        n_intermediate = n_synthetic_total - n_low_density

        rng = np.random.default_rng(
            random_state + 1
        )

        if n_intermediate > 0:
            intermediate_probability = (
                intermediate_selection_weight
                / intermediate_selection_weight.sum()
            )

            intermediate_indices = rng.choice(
                n_samples,
                size=n_intermediate,
                replace=True,
                p=intermediate_probability,
            )

            intermediate_support = candidate_original[
                intermediate_indices
            ]

        if n_low_density > 0:
            selected_low_density_indices = rng.choice(
                low_density_indices,
                size=n_low_density,
                replace=True,
            )

            low_density_support = candidate_original[
                selected_low_density_indices
            ]

    # ------------------------------------------------------------------
    # Deterministic MST bridge support
    # ------------------------------------------------------------------
    mst_scaled = (
        build_mst_bridge(
            scaled_data,
            gap_factor=mst_gap_factor,
            point_spacing=mst_point_spacing,
        )
        if use_mst_bridge
        else np.empty((0, 2), float)
    )

    mst_original = (
        mst_scaled @ inverse_scale.T
        if len(mst_scaled)
        else np.empty((0, 2), float)
    )

    synthetic_points_exist = (
        len(intermediate_support) + len(low_density_support)
    ) > 0

    effective_synthetic_weight = (
        synthetic_weight_fraction
        if synthetic_points_exist
        else 0.0
    )

    effective_mst_weight = (
        mst_bridge_weight
        if len(mst_scaled)
        else 0.0
    )

    intermediate_total_weight = (
        effective_synthetic_weight
        * (1.0 - low_density_fraction_within_synthetic)
    )

    low_density_total_weight = (
        effective_synthetic_weight
        * low_density_fraction_within_synthetic
    )

    # If one synthetic subgroup has zero selected points, transfer its intended
    # weight to the other subgroup so that the total synthetic weight is retained.
    if len(intermediate_support) == 0:
        low_density_total_weight += intermediate_total_weight
        intermediate_total_weight = 0.0

    if len(low_density_support) == 0:
        intermediate_total_weight += low_density_total_weight
        low_density_total_weight = 0.0

    original_total_weight = (
        1.0
        - effective_synthetic_weight
        - effective_mst_weight
    )

    # ------------------------------------------------------------------
    # Exact centers and weights used to fit the final KDE
    # ------------------------------------------------------------------
    training_parts = [scaled_data]
    weight_parts = [
        np.full(
            len(scaled_data),
            original_total_weight / len(scaled_data),
            float,
        )
    ]

    if len(intermediate_support):
        intermediate_scaled = (
            intermediate_support @ scale.T
        )

        training_parts.append(intermediate_scaled)
        weight_parts.append(
            np.full(
                len(intermediate_scaled),
                intermediate_total_weight
                / len(intermediate_scaled),
                float,
            )
        )

    if len(low_density_support):
        low_density_scaled = (
            low_density_support @ scale.T
        )

        training_parts.append(low_density_scaled)
        weight_parts.append(
            np.full(
                len(low_density_scaled),
                low_density_total_weight
                / len(low_density_scaled),
                float,
            )
        )

    if len(mst_scaled):
        training_parts.append(mst_scaled)
        weight_parts.append(
            np.full(
                len(mst_scaled),
                effective_mst_weight / len(mst_scaled),
                float,
            )
        )

    training = np.vstack(training_parts)
    weights = np.concatenate(weight_parts)
    weights /= weights.sum()

    kde = KernelDensity(
        kernel="gaussian",
        bandwidth=iso_temp,
    ).fit(
        training,
        sample_weight=weights,
    )

    # Optional draw from the final KDE, used only for the numerical bulk-grid
    # bounds. It is not used to refit the KDE.
    sample = None

    if return_sample:
        sample = (
            kde.sample(
                n_samples=n_samples,
                random_state=random_state + 2,
            )
            @ inverse_scale.T
        )

    combined_synthetic_support = np.vstack(
        [
            array
            for array in (
                intermediate_support,
                low_density_support,
            )
            if len(array)
        ]
    ) if synthetic_points_exist else np.empty((0, 2), float)

    training_info = {
        "original": data.copy(),
        "synthetic_support": combined_synthetic_support.copy(),
        "intermediate_support": intermediate_support.copy(),
        "low_density_support": low_density_support.copy(),
        "mst_support": mst_original.copy(),
        "original_total_weight": float(original_total_weight),
        "synthetic_total_weight": float(effective_synthetic_weight),
        "intermediate_total_weight": float(intermediate_total_weight),
        "low_density_total_weight": float(low_density_total_weight),
        "mst_total_weight": float(effective_mst_weight),
        "weight_per_original": float(
            original_total_weight / len(data)
        ),
        "weight_per_intermediate": float(
            intermediate_total_weight / len(intermediate_support)
        ) if len(intermediate_support) else 0.0,
        "weight_per_low_density": float(
            low_density_total_weight / len(low_density_support)
        ) if len(low_density_support) else 0.0,
        "weight_per_mst": float(
            effective_mst_weight / len(mst_original)
        ) if len(mst_original) else 0.0,
        "n_pilot_candidates": int(n_samples),
        "n_original": int(len(data)),
        "n_synthetic": int(len(combined_synthetic_support)),
        "n_intermediate": int(len(intermediate_support)),
        "n_low_density": int(len(low_density_support)),
        "n_mst": int(len(mst_original)),
    }

    return scale, kde, sample, training_info


# -------------------------------------------------------------------------
# FINAL KDE WEIGHTS — EDIT THESE THREE VALUES
# -------------------------------------------------------------------------
# ``SYNTHETIC_TOTAL_WEIGHT`` is the total weight of intermediate + lowest-
# density Monte Carlo support. ``LOW_DENSITY_FRACTION_WITHIN_SYNTHETIC`` is
# the fraction of that synthetic total assigned to the lowest-density pool.
# The original-observation weight is calculated automatically as the residual.

SYNTHETIC_TOTAL_WEIGHT = 0.095  # Total intermediate + low-density pilot support
LOW_DENSITY_FRACTION_WITHIN_SYNTHETIC = 0.01  # 1% of pilot weight to lowest 10% density ranks
MST_TOTAL_WEIGHT = 0.05  # MST bridge support

ORIGINAL_TOTAL_WEIGHT = (
    1.0 - SYNTHETIC_TOTAL_WEIGHT - MST_TOTAL_WEIGHT
)
INTERMEDIATE_TOTAL_WEIGHT = (
    SYNTHETIC_TOTAL_WEIGHT
    * (1.0 - LOW_DENSITY_FRACTION_WITHIN_SYNTHETIC)
)
LOW_DENSITY_TOTAL_WEIGHT = (
    SYNTHETIC_TOTAL_WEIGHT
    * LOW_DENSITY_FRACTION_WITHIN_SYNTHETIC
)

BULK_CFG = dict(
    synthetic_weight_fraction=SYNTHETIC_TOTAL_WEIGHT,
    low_density_fraction_within_synthetic=(
        LOW_DENSITY_FRACTION_WITHIN_SYNTHETIC
    ),
    synthetic_rank_center=0.50,
    synthetic_rank_width=0.30,
    low_density_percentile=10.0,
    iso_temp=1.0,
    n_samples=40_000,
    random_state=42,
    use_correlation=True,
    correlation_strength=0.50,
    correlation_clip=0.85,
    use_mst_bridge=True,
    mst_bridge_weight=MST_TOTAL_WEIGHT,
    mst_gap_factor=1.25,
    mst_point_spacing=0.15,
)

CLUMP_CFG = BULK_CFG.copy()

S_BULK = {}
KDE_BULK = {}
BULK_SAMPLE = {}
KDE_TRAINING_BULK = {}

S_CLUMP = {}
KDE_CLUMP = {}
KDE_TRAINING_CLUMP = {}

for k in CLASSES:
    (
        S_BULK[k],
        KDE_BULK[k],
        BULK_SAMPLE[k],
        KDE_TRAINING_BULK[k],
    ) = fit_continuity_kde(
        BULK_FIT[k],
        *BW_BULK[k],
        **BULK_CFG,
        return_sample=True,
    )

    (
        S_CLUMP[k],
        KDE_CLUMP[k],
        _,
        KDE_TRAINING_CLUMP[k],
    ) = fit_continuity_kde(
        CLUMP[k],
        *BW_CLUMP[k],
        **CLUMP_CFG,
        return_sample=False,
    )

print("\nAll KDEs fitted successfully.")
print(
    "Target collective KDE weights: "
    f"original={ORIGINAL_TOTAL_WEIGHT:.5f}, "
    f"intermediate pilot={INTERMEDIATE_TOTAL_WEIGHT:.5f}, "
    f"lowest-density pilot={LOW_DENSITY_TOTAL_WEIGHT:.5f}, "
    f"MST={MST_TOTAL_WEIGHT:.5f}"
)

for k in CLASSES:
    for space_name, information in (
        ("bulk", KDE_TRAINING_BULK[k]),
        ("clumped", KDE_TRAINING_CLUMP[k]),
    ):
        print(
            f"  {k} {space_name} | "
            f"n_original={information['n_original']} | "
            f"n_intermediate={information['n_intermediate']} | "
            f"n_low_density={information['n_low_density']} | "
            f"n_MST={information['n_mst']} | "
            f"weights=("
            f"{information['original_total_weight']:.5f}, "
            f"{information['intermediate_total_weight']:.5f}, "
            f"{information['low_density_total_weight']:.5f}, "
            f"{information['mst_total_weight']:.5f})"
        )

#%% DIAGNOSTIC — ACTUAL CENTERS USED TO FIT FINAL KDES

# This figure displays the exact point sets passed to KernelDensity.fit:
#   circles       = original measurements;
#   small dots    = intermediate-density pilot-KDE support;
#   small triangles = support sampled from the lowest 10% of density ranks;
#   crosses       = MST bridge points.
#
# Marker count is not proportional to collective weight. Exact counts and
# weights are printed in KDE_TRAINING_SUMMARY.

training_summary_rows = []

for k in CLASSES:
    for space_name, information in (
        ("Bulk", KDE_TRAINING_BULK[k]),
        ("Clumped", KDE_TRAINING_CLUMP[k]),
    ):
        training_summary_rows.append(
            {
                "space": space_name,
                "class": k,
                "class_name": NAMES[k],
                "n_original": information["n_original"],
                "n_pilot_candidates": information[
                    "n_pilot_candidates"
                ],
                "n_intermediate_support": information[
                    "n_intermediate"
                ],
                "n_low_density_support": information[
                    "n_low_density"
                ],
                "n_all_pilot_support": information[
                    "n_synthetic"
                ],
                "n_mst": information["n_mst"],
                "original_total_weight": information[
                    "original_total_weight"
                ],
                "intermediate_total_weight": information[
                    "intermediate_total_weight"
                ],
                "low_density_total_weight": information[
                    "low_density_total_weight"
                ],
                "all_pilot_support_total_weight": information[
                    "synthetic_total_weight"
                ],
                "mst_total_weight": information[
                    "mst_total_weight"
                ],
                "weight_per_original": information[
                    "weight_per_original"
                ],
                "weight_per_intermediate": information[
                    "weight_per_intermediate"
                ],
                "weight_per_low_density": information[
                    "weight_per_low_density"
                ],
                "weight_per_mst": information[
                    "weight_per_mst"
                ],
            }
        )

KDE_TRAINING_SUMMARY = pd.DataFrame(
    training_summary_rows
)

print("\nACTUAL POINTS USED TO FIT THE FINAL KDES")
print(
    KDE_TRAINING_SUMMARY.to_string(
        index=False,
        float_format=lambda value: f"{value:.8g}",
    )
)

fig, axes = plt.subplots(
    1,
    2,
    figsize=(14, 6),
    constrained_layout=True,
)

ax_bulk, ax_clump = axes


def plot_actual_kde_centers(
    ax,
    training_dictionary,
):
    """Plot the exact original, pilot-support, and MST KDE centers."""

    for k in CLASSES:
        information = training_dictionary[k]

        # Intermediate-density Monte Carlo support used by KDE.fit.
        intermediate = information["intermediate_support"]
        if len(intermediate):
            ax.scatter(
                intermediate[:, 0],
                intermediate[:, 1],
                s=20,
                c=POINT_COLORS[k],
                marker=".",
                alpha=0.16,
                edgecolors="none",
                rasterized=True,
                zorder=1,
            )

        # Monte Carlo support drawn from the lowest 10% of pilot-density ranks.
        low_density = information["low_density_support"]
        if len(low_density):
            ax.scatter(
                low_density[:, 0],
                low_density[:, 1],
                s=10,
                c=POINT_COLORS[k],
                marker="v",
                alpha=0.45,
                edgecolors="none",
                rasterized=True,
                zorder=1.5,
            )

        # Deterministic MST bridge points used by KDE.fit.
        mst = information["mst_support"]
        if len(mst):
            ax.scatter(
                mst[:, 0],
                mst[:, 1],
                s=5,
                c=POINT_COLORS[k],
                marker="x",
                linewidths=0.65,
                alpha=0.75,
                rasterized=True,
                zorder=2,
            )

        # Original measurements.
        original = information["original"]
        ax.scatter(
            original[:, 0],
            original[:, 1],
            s=30,
            c=POINT_COLORS[k],
            edgecolors="black",
            linewidths=0.45,
            alpha=0.95,
            zorder=3,
        )


plot_actual_kde_centers(
    ax_bulk,
    KDE_TRAINING_BULK,
)

ax_bulk.set_xlim(*BULK_XLIM)
ax_bulk.set_ylim(*BULK_YLIM)
ax_bulk.set_xlabel("δ¹³C")
ax_bulk.set_ylabel("δD")
ax_bulk.set_title(
    "Bulk"
)

plot_actual_kde_centers(
    ax_clump,
    KDE_TRAINING_CLUMP,
)

ax_clump.set_xlim(*CLUMP_XLIM)
ax_clump.set_ylim(*CLUMP_YLIM)
ax_clump.set_xlabel(
    r"$\Delta^{13}$CH$_3$D (‰)"
)
ax_clump.set_ylabel(
    r"$\Delta^{12}$CH$_2$D$_2$ (‰)"
)
ax_clump.set_title(
    "Clumped"
)

class_handles = [
    Line2D(
        [0],
        [0],
        marker="o",
        linestyle="none",
        markerfacecolor=POINT_COLORS[k],
        markeredgecolor="black",
        markersize=7,
        label=NAMES[k],
    )
    for k in CLASSES
]

point_type_handles = [
    Line2D(
        [0],
        [0],
        marker="o",
        linestyle="none",
        markerfacecolor="white",
        markeredgecolor="black",
        markersize=7,
        label=f"Original observations — {100 * ORIGINAL_TOTAL_WEIGHT:.3g}%",
    ),
    Line2D(
        [0],
        [0],
        marker=".",
        linestyle="none",
        color="0.35",
        markersize=8,
        label=(
            "Intermediate pilot support — "
            f"{100 * INTERMEDIATE_TOTAL_WEIGHT:.4g}%"
        ),
    ),
    Line2D(
        [0],
        [0],
        marker="v",
        linestyle="none",
        color="0.35",
        markersize=5,
        label=(
            f"Lowest {BULK_CFG['low_density_percentile']:.3g}% "
            "pilot support — "
            f"{100 * LOW_DENSITY_TOTAL_WEIGHT:.4g}%"
        ),
    ),
    Line2D(
        [0],
        [0],
        marker="x",
        linestyle="none",
        color="0.15",
        markersize=7,
        label=f"MST bridge points — {100 * MST_TOTAL_WEIGHT:.3g}%",
    ),
]

legend_classes = ax_clump.legend(
    handles=class_handles,
    loc="upper left",
    title="Genetic class",
    fontsize=8,
)

ax_clump.add_artist(legend_classes)

ax_clump.legend(
    handles=point_type_handles,
    loc="lower right",
    title="Final KDE component",
    fontsize=8,
)

fig.suptitle(
    "Final KDE weights per class and isotope space: "
    f"{100 * ORIGINAL_TOTAL_WEIGHT:.3g}% original + "
    f"{100 * SYNTHETIC_TOTAL_WEIGHT:.3g}% pilot support + "
    f"{100 * MST_TOTAL_WEIGHT:.3g}% MST",
    fontsize=12,
)

save_fig('01_actual_KDE_centers')   # SI Fig. S4 (TMO) / S5 (BIO_ABI)

#%% BULK PRIORS (SI S5)
# ---------------------------------------------------------------------------
# DATA SCOPE — READ BEFORE CHANGING THE DATA
# The bulk KDEs, and therefore the bulk priors below, are fitted to BULK_FIT[k].
# By default BULK_FIT[k] = BULK[k] = the PAIRED samples (same rows as the
# clumped data). 
# ---------------------------------------------------------------------------

NGRID_BULK = 260
PAD_FRAC_BULK = 0.30
LEVELS_PRIOR = (0.005, 0.5, 0.999)


def loglike_on_grid(grid, scale, kde, shape=None):
    log_jacobian = np.log(np.abs(np.linalg.det(scale)) + 1e-300)
    values = kde.score_samples(grid @ scale.T) + log_jacobian
    return values.reshape(shape) if shape is not None else values


def normalize01(field):
    minimum = np.nanmin(field)
    maximum = np.nanmax(field)
    if not np.isfinite(minimum) or not np.isfinite(maximum) or maximum <= minimum:
        return np.zeros_like(field)
    return (field - minimum) / (maximum - minimum)


def softmax_fields(fields):
    stack = np.stack([np.asarray(fields[k], float) for k in CLASSES], axis=0)
    maximum = np.max(stack, axis=0, keepdims=True)
    exponential = np.exp(stack - maximum)
    normalized = exponential / (np.sum(exponential, axis=0, keepdims=True) + 1e-12)
    return {k: normalized[i] for i, k in enumerate(CLASSES)}


def normalize_class_fields(fields, fallback=None):
    stack = np.stack([np.asarray(fields[k], float) for k in CLASSES], axis=0)
    stack = np.clip(np.nan_to_num(stack, nan=0.0, posinf=0.0, neginf=0.0), 0.0, None)
    total = np.sum(stack, axis=0)
    unsupported = total <= 1e-12
    output = np.empty_like(stack)
    output[:, ~unsupported] = stack[:, ~unsupported] / total[None, ~unsupported]
    output[:, unsupported] = 1.0 / len(CLASSES) if fallback is None else fallback
    return {k: output[i] for i, k in enumerate(CLASSES)}


def bulk_priors_at_points(XX, YY, priors, points):
    xv = XX[0, :]
    yv = YY[:, 0]
    values = {
        k: np.clip(bilinear_interp(xv, yv, priors[k], points), 1e-12, 1.0)
        for k in CLASSES
    }
    matrix = np.vstack([values[k] for k in CLASSES]).T
    matrix /= matrix.sum(axis=1, keepdims=True) + 1e-12
    return {k: matrix[:, i] for i, k in enumerate(CLASSES)}


all_bulk_sample = np.vstack([BULK_SAMPLE[k] for k in CLASSES])
pad_x = PAD_FRAC_BULK * (np.ptp(all_bulk_sample[:, 0]) + 1e-9)
pad_y = PAD_FRAC_BULK * (np.ptp(all_bulk_sample[:, 1]) + 1e-9)

xv_b = np.linspace(all_bulk_sample[:, 0].min() - pad_x, all_bulk_sample[:, 0].max() + pad_x, NGRID_BULK)
yv_b = np.linspace(all_bulk_sample[:, 1].min() - pad_y, all_bulk_sample[:, 1].max() + pad_y, NGRID_BULK)
XXb, YYb = np.meshgrid(xv_b, yv_b)
GRIDb = np.c_[XXb.ravel(), YYb.ravel()]

# <<BULK-CLASSES>> bulk log-likelihood grid and competitive softmax (S5)
LL_BULK = {
    k: loglike_on_grid(GRIDb, S_BULK[k], KDE_BULK[k])
    for k in CLASSES
}
PRIORS_BULK = {
    k: field.reshape(XXb.shape)
    for k, field in softmax_fields(LL_BULK).items()
}

# <<BULK-CLASSES>> bulk display gate (union of class supports)
log_total = np.logaddexp.reduce(np.stack([LL_BULK[k] for k in CLASSES], axis=0), axis=0)
bulk_support = np.exp(log_total - np.max(log_total)).reshape(XXb.shape)
threshold = np.quantile(bulk_support, BULK_GATE_FLOOR_QUANTILE)
bulk_gate = np.clip((bulk_support - threshold) / (1.0 - threshold + 1e-12), 0.0, 1.0) ** BULK_GATE_POWER

PRIORS_BULK_PLOT = {
    k: normalize01(np.clip(PRIORS_BULK[k] * bulk_gate, 0.0, 1.0))
    for k in CLASSES
}




#%% FINAL BULK-PRIOR OVERLAY

def plot_bulk_prior_overlay():
    style = SCHEME['BULK_OVERLAY']
    alpha, draw_order = style['alpha'], style['draw_order']
    zorder, contour_color = style['zorder'], style['contour_color']
    minimum = float(LEVELS_PRIOR[0])
    levels = np.linspace(minimum, 1.0, 12)

    fig, ax = plt.subplots(figsize=(9.6, 8.2))
    fig.subplots_adjust(left=0.10, right=0.70, bottom=0.10, top=0.92)
    contour_sets = {}

    for k in draw_order:
        field = np.clip(PRIORS_BULK_PLOT[k], 0.0, 1.0)
        masked = np.ma.masked_less(field, minimum)
        contour_sets[k] = ax.contourf(
            XXb,
            YYb,
            masked,
            levels=levels,
            cmap=CMAPS[k],
            alpha=alpha[k],
            vmin=minimum,
            vmax=1.0,
            zorder=zorder[k],
            antialiased=True,
        )
        ax.contour(
            XXb,
            YYb,
            field,
            levels=np.asarray(LEVELS_PRIOR),
            colors=contour_color[k],
            linewidths=0.40,
            zorder=zorder[k] + 0.2,
        )
        ax.contour(
            XXb,
            YYb,
            field,
            levels=levels,
            colors="black",
            linewidths=0.18,
            zorder=zorder[k] + 0.3,
        )

        if SHOW_BULK_DATA_POINTS:
            ax.scatter(
                BULK[k][:, 0],
                BULK[k][:, 1],
                s=10,
                c=POINT_COLORS[k],
                edgecolor="none",
                alpha=0.7,
                zorder=zorder[k] + 1,
            )

    ax.set_xlabel("δ¹³C")
    ax.set_ylabel("δD")
    ax.set_title("Bulk priors: " + " / ".join(CLASSES))

    pos = ax.get_position()
    bar_width = 0.012
    gap = 0.010
    left = pos.x1 + 0.006
    bottom = pos.y0 + 0.02 * pos.height
    height = pos.height * 0.96

    for index, k in enumerate(CLASSES):
        cax = fig.add_axes([left + index * (bar_width + gap), bottom, bar_width, height])
        colorbar = fig.colorbar(contour_sets[k], cax=cax)
        cax.set_title(NAMES[k], fontsize=10, rotation=45, loc="left", pad=6)
        if k != CLASSES[-1]:
            colorbar.set_ticks([])

    save_fig('02_bulk_prior_overlay')   # SI Fig. S6 (TMO) / S7 (BIO_ABI)


plot_bulk_prior_overlay()


#%% CLUMPED LIKELIHOODS AND BULK-DERIVED PRIORS (SI S6, S7)

PAD_FRAC_CLUMP = 0.08
NGRID_CLUMP = 320


def padded_bounds(values, fraction):
    values = np.asarray(values, float)
    lower = values.min(axis=0)
    upper = values.max(axis=0)
    span = upper - lower
    return lower - fraction * span, upper + fraction * span


class_bounds = [padded_bounds(CLUMP[k], PAD_FRAC_CLUMP) for k in CLASSES]
lo = np.min(np.stack([bounds[0] for bounds in class_bounds], axis=0), axis=0)
hi = np.max(np.stack([bounds[1] for bounds in class_bounds], axis=0), axis=0)

xv_c = np.linspace(lo[0], hi[0], NGRID_CLUMP)
yv_c = np.linspace(lo[1], hi[1], NGRID_CLUMP)
XXc, YYc = np.meshgrid(xv_c, yv_c)
GRIDc = np.c_[XXc.ravel(), YYc.ravel()]

LL_CLUMP = {
    k: loglike_on_grid(GRIDc, S_CLUMP[k], KDE_CLUMP[k], XXc.shape)
    for k in CLASSES
}


def prior_in_clumped_from_bulk(Z_train, weights, sigma_x, bw_mult=1.0):
    """Kernel-average paired bulk compatibility over clumped-isotope space."""
    Z_train = np.asarray(Z_train, float)
    weights = np.asarray(weights, float)
    grid = np.c_[XXc.ravel(), YYc.ravel()]

    inverse_covariance = np.linalg.inv((bw_mult**2) * sigma_x)
    differences = grid[:, None, :] - Z_train[None, :, :]
    exponent = np.einsum("...i,ij,...j->...", differences, inverse_covariance, differences)
    kernels = np.exp(-0.5 * exponent)

    kernel_sum = np.sum(kernels, axis=1)
    weighted_sum = kernels @ weights
    supported = kernel_sum > 1e-10 * np.max(kernel_sum)

    values = np.full(len(grid), float(np.mean(weights)), float)
    values[supported] = weighted_sum[supported] / kernel_sum[supported]
    return np.clip(values, 0.0, 1.0).reshape(XXc.shape)


PRIOR_BW_MULT = {k: 1.0 for k in CLASSES}
PRIOR_CLUMP_RAW = {}

for k in CLASSES:
    class_weights = bulk_priors_at_points(XXb, YYb, PRIORS_BULK, BULK[k])[k]
    # S6: weight each paired training observation by its bulk KDE support.
    # The same support factor is NOT renormalized per observation: it reduces
    # its contribution to the local kernel average, without adding a uniform
    # component or altering the relative class-specific raw densities.
    if USE_GATED_PROJECTION:
        # <<BULK-CLASSES>> support of each paired bulk point = union over the bulk classes
        log_vals = np.column_stack([
            loglike_on_grid(BULK[k], S_BULK[j], KDE_BULK[j])
            for j in CLASSES
        ])
        maxima = np.array([np.max(LL_BULK[j]) for j in CLASSES])
        rel = np.exp(np.clip(log_vals - maxima, -745, 0))
        support_raw = 1.0 - np.prod(1.0-rel, axis=1)
        support = np.clip((support_raw-PROJECTION_BULK_T)/
                          (1-PROJECTION_BULK_T), 0., 1.) ** PROJECTION_BULK_GAMMA
        class_weights = class_weights * support
    PRIOR_CLUMP_RAW[k] = prior_in_clumped_from_bulk(
        CLUMP[k],
        class_weights,
        BASE_MODELS_CLUMP[k]["Sigma_x"],
        PRIOR_BW_MULT[k],
    )

PRIOR_CLUMP = normalize_class_fields(PRIOR_CLUMP_RAW)

#%% STRICT BAYESIAN POSTERIOR AND COMMON SUPPORT GATE (SI S8)

LOG_SCORE = {
    k: LL_CLUMP[k] + np.log(np.clip(PRIOR_CLUMP[k], 1e-12, 1.0))
    for k in CLASSES
}
P_POST = softmax_fields(LOG_SCORE)

# Display gate parameters (threshold, exponent, subsampling, smoothing) are set in cell 00.
COMMON_KDE_THRESH = CLUMP_DISPLAY_T
COMMON_GATE_POWER = CLUMP_DISPLAY_GAMMA

xv_coarse = xv_c[::GATE_SUBSAMPLE]
yv_coarse = yv_c[::GATE_SUBSAMPLE]
XX_coarse, YY_coarse = np.meshgrid(xv_coarse, yv_coarse)
GRID_coarse = np.c_[XX_coarse.ravel(), YY_coarse.ravel()]

relative_support = {}
for k in CLASSES:
    log_density = KDE_CLUMP[k].score_samples(GRID_coarse @ S_CLUMP[k].T)
    coarse = np.exp(log_density - np.max(log_density)).reshape(XX_coarse.shape)
    factors = (XXc.shape[0] / coarse.shape[0], XXc.shape[1] / coarse.shape[1])
    full = zoom(coarse, zoom=factors, order=1)[: XXc.shape[0], : XXc.shape[1]]
    relative_support[k] = full / (np.max(full) + 1e-12)

support_stack = np.stack([relative_support[k] for k in CLASSES], axis=0)
common_support_raw = 1.0 - np.prod(1.0 - support_stack, axis=0)
common_support_raw /= np.max(common_support_raw) + 1e-12

COMMON_GATE = np.clip(
    (common_support_raw - COMMON_KDE_THRESH) / (1.0 - COMMON_KDE_THRESH + 1e-12),
    0.0,
    1.0,
) ** COMMON_GATE_POWER
COMMON_GATE = gaussian_filter(COMMON_GATE, sigma=COMMON_SMOOTH_GATE)
COMMON_GATE /= np.max(COMMON_GATE) + 1e-12

P_POST_GATED = {k: P_POST[k] * COMMON_GATE for k in CLASSES}
DATA_POINTS = {k: CLUMP[k] for k in CLASSES}

#%% METHOD FIGURE — BULK PRIOR INSIDE EACH CLASS-SPECIFIC CLUMPED DOMAIN (SI S6)

# Class colours and colour scale come from the scheme chosen in cell 00.
BULK_PRIOR_CMAPS = CMAPS

# Common numerical scale for direct comparison
BULK_PRIOR_VMIN, BULK_PRIOR_VMAX = SCHEME['BULK_PRIOR_RANGE']

BULK_PRIOR_LEVELS = np.linspace(
    BULK_PRIOR_VMIN,
    BULK_PRIOR_VMAX,
    23,
)

BULK_PRIOR_CONTOUR_LEVELS = SCHEME['BULK_PRIOR_TICKS']

BULK_PRIOR_TICKS = SCHEME['BULK_PRIOR_TICKS']

# ------------------------------------------------------------------
# DISPLAY OPTIONS
# ------------------------------------------------------------------
SHOW_BACKGROUND = False          # fond coloré du prior
SHOW_PRIOR_CONTOURS = False      # lignes de contour du prior
SHOW_SUPPORT_CONTOUR = False     # contour noir du domaine de support
SHOW_CLASS_DATA_POINTS = True    # points des données
SHOW_COLORBAR = True             # une colorbar par panel

POINT_SIZE = 55
POINT_ALPHA = 1
POINT_EDGE = "none"

SHOW_PRIOR_CONTOUR_LABELS = False


def plot_bulk_prior_inside_class_domains():

    n_classes = len(CLASSES)

    prior_maps = {}
    for k in CLASSES:
        field = np.asarray(PRIOR_CLUMP[k], dtype=float)
        if field.shape != XXc.shape:
            field = field.reshape(XXc.shape)
        prior_maps[k] = field

    fig, axes = plt.subplots(
        1,
        n_classes,
        figsize=(5.7 * n_classes, 5.0),
        sharex=False,
        sharey=False,
        squeeze=False,
    )

    axes = axes.ravel()

    norm = Normalize(
        vmin=BULK_PRIOR_VMIN,
        vmax=BULK_PRIOR_VMAX,
    )

    print(
        "\n=== BULK PRIOR INSIDE CLASS-SPECIFIC CLUMPED DOMAINS ==="
    )

    for i, (ax, k) in enumerate(zip(axes, CLASSES)):

        field = prior_maps[k]

        # ----------------------------------------------------------
        # Class-specific clumped support
        # ----------------------------------------------------------
        class_support = np.asarray(
            relative_support[k],
            dtype=float,
        )

        if class_support.shape != XXc.shape:
            class_support = class_support.reshape(XXc.shape)

        class_display_domain = (
            class_support > COMMON_KDE_THRESH
        )

        # Mask only for display
        display_field = np.ma.masked_where(
            ~class_display_domain,
            field,
        )

        supported_values = field[class_display_domain]

        print(
            f"{k}: "
            f"min={np.nanmin(supported_values):.6f}, "
            f"median={np.nanmedian(supported_values):.6f}, "
            f"max={np.nanmax(supported_values):.6f}"
        )

        cf = None

        # ----------------------------------------------------------
        # Background field
        # ----------------------------------------------------------
        if SHOW_BACKGROUND:
            cf = ax.contourf(
                XXc,
                YYc,
                display_field,
                levels=BULK_PRIOR_LEVELS,
                cmap=BULK_PRIOR_CMAPS[k],
                norm=norm,
                extend="neither",
            )

        # ----------------------------------------------------------
        # Prior contours
        # ----------------------------------------------------------
        if SHOW_PRIOR_CONTOURS:
            field_min = np.nanmin(supported_values)
            field_max = np.nanmax(supported_values)

            available_levels = [
                level for level in BULK_PRIOR_CONTOUR_LEVELS
                if field_min < level < field_max
            ]

            if available_levels:
                cs = ax.contour(
                    XXc,
                    YYc,
                    display_field,
                    levels=available_levels,
                    colors="black",
                    linewidths=0.65,
                    alpha=0.75,
                    zorder=5,
                )

                if SHOW_PRIOR_CONTOUR_LABELS:
                    ax.clabel(
                        cs,
                        fmt=lambda value: f"{value:.2f}",
                        fontsize=7,
                        inline=True,
                        inline_spacing=3,
                    )

        # ----------------------------------------------------------
        # Support contour
        # ----------------------------------------------------------
        if SHOW_SUPPORT_CONTOUR:
            ax.contour(
                XXc,
                YYc,
                class_support,
                levels=[COMMON_KDE_THRESH],
                colors="black",
                linewidths=1.0,
                zorder=6,
            )

        # ----------------------------------------------------------
        # Data points colored by PRIOR_CLUMP[k]
        # ----------------------------------------------------------
        if SHOW_CLASS_DATA_POINTS:
            point_values = bilinear_interp(
                xv_c,
                yv_c,
                field,
                CLUMP[k],
            )

            point_values = np.clip(
                point_values,
                BULK_PRIOR_VMIN,
                BULK_PRIOR_VMAX,
            )

            ax.scatter(
                CLUMP[k][:, 0],
                CLUMP[k][:, 1],
                c=point_values,
                s=POINT_SIZE,
                cmap=BULK_PRIOR_CMAPS[k],
                norm=norm,
                edgecolors="black",
                linewidths=0.5,
                alpha=POINT_ALPHA,
                zorder=7,
            )

        # ----------------------------------------------------------
        # Formatting
        # ----------------------------------------------------------
        ax.set_xlim(xv_c[0], xv_c[-1])
        ax.set_ylim(yv_c[0], yv_c[-1])

        ax.set_xlabel(
            r"$\Delta^{13}\mathrm{CH_3D}$ (‰)"
        )

        ax.set_title(
            NAMES[k],
            fontsize=12,
        )

        if i > 0:
            ax.tick_params(
                axis="y",
                labelleft=False,
            )

        # ----------------------------------------------------------
        # Colorbar
        # ----------------------------------------------------------
        if SHOW_COLORBAR:
            divider = make_axes_locatable(ax)

            cax = divider.append_axes(
                "right",
                size="4.5%",
                pad=0.06,
            )

            # If no background exists, make a dummy mappable
            if cf is not None:
                mappable = cf
            else:
                mappable = ScalarMappable(norm=norm, cmap=BULK_PRIOR_CMAPS[k])
                mappable.set_array([])

            cb = fig.colorbar(
                mappable,
                cax=cax,
                ticks=BULK_PRIOR_TICKS,
            )

            cb.set_label(
                "Bulk-derived support\n" + r"$\pi_k(z)$",
                fontsize=9,
            )
            cb.ax.tick_params(labelsize=8)

    axes[0].set_ylabel(
        r"$\Delta^{12}\mathrm{CH_2D_2}$ (‰)"
    )

    fig.tight_layout()
    save_fig('03_projected_bulk_prior_by_class')   # SI Fig. S8 (TMO) / S9 (BIO_ABI)


plot_bulk_prior_inside_class_domains()

#%% METHOD FIGURE — CLUMPED LOG-LIKELIHOOD INSIDE EACH CLASS-SPECIFIC DOMAIN (SI S7)

# Class colours come from the scheme chosen in cell 00.
LIKELIHOOD_CMAPS = CMAPS


# ------------------------------------------------------------------
# DISPLAY SETTINGS
# ------------------------------------------------------------------

# Leave these as None to calculate one common scale automatically
# from all three class-specific supported domains.
LIKELIHOOD_VMIN = None
LIKELIHOOD_VMAX = None

# Automatic limits are rounded outward to this increment.
LIKELIHOOD_ROUND_STEP = 0.5

N_LIKELIHOOD_LEVELS = 25
N_LIKELIHOOD_TICKS = 7

SHOW_LIKELIHOOD_CONTOUR_LABELS = True
SHOW_CLASS_DATA_POINTS = True
SHOW_CLASS_SUPPORT_CONTOUR = True


def _round_limits_outward(vmin, vmax, step=0.5):
    """
    Round common display limits outward to readable values.
    """
    vmin_rounded = np.floor(vmin / step) * step
    vmax_rounded = np.ceil(vmax / step) * step

    if vmax_rounded <= vmin_rounded:
        vmax_rounded = vmin_rounded + step

    return vmin_rounded, vmax_rounded


def plot_clumped_log_likelihood_inside_class_domains():
    """
    Display the exact clumped-isotope log-likelihood term used in:

        LOG_SCORE_k(z)
        = LL_CLUMP_k(z) + log[PRIOR_CLUMP_k(z)]

    Each LL_CLUMP[k] map is shown only inside the clumped-support
    domain of the corresponding class.

    Important:
    - LL_CLUMP[k] is displayed directly.
    - relative_support[k] is used only as a class-specific display mask.
    """

    n_classes = len(CLASSES)

    likelihood_maps = {}
    class_support_maps = {}
    class_domains = {}
    supported_values_by_class = {}

    # ------------------------------------------------------------------
    # Prepare likelihood and support maps
    # ------------------------------------------------------------------
    for k in CLASSES:

        # Exact log-likelihood entering LOG_SCORE
        ll_field = np.asarray(
            LL_CLUMP[k],
            dtype=float,
        )

        if ll_field.shape != XXc.shape:
            ll_field = ll_field.reshape(XXc.shape)

        likelihood_maps[k] = ll_field

        # Class-specific relative clumped support used only for masking
        class_support = np.asarray(
            relative_support[k],
            dtype=float,
        )

        if class_support.shape != XXc.shape:
            class_support = class_support.reshape(
                XXc.shape
            )

        class_support_maps[k] = class_support

        class_domain = (
            (class_support > COMMON_KDE_THRESH)
            & np.isfinite(ll_field)
        )

        class_domains[k] = class_domain

        supported_values = ll_field[class_domain]

        if supported_values.size == 0:
            raise ValueError(
                f"No supported likelihood values found for class {k}. "
                "Check relative_support and COMMON_KDE_THRESH."
            )

        supported_values_by_class[k] = supported_values

    # ------------------------------------------------------------------
    # Determine one common numerical scale for all classes
    # ------------------------------------------------------------------
    all_supported_values = np.concatenate(
        [
            supported_values_by_class[k]
            for k in CLASSES
        ]
    )

    actual_global_min = np.nanmin(
        all_supported_values
    )

    actual_global_max = np.nanmax(
        all_supported_values
    )

    auto_vmin, auto_vmax = _round_limits_outward(
        actual_global_min,
        actual_global_max,
        step=LIKELIHOOD_ROUND_STEP,
    )

    plot_vmin = (
        auto_vmin
        if LIKELIHOOD_VMIN is None
        else LIKELIHOOD_VMIN
    )

    plot_vmax = (
        auto_vmax
        if LIKELIHOOD_VMAX is None
        else LIKELIHOOD_VMAX
    )

    likelihood_levels = np.linspace(
        plot_vmin,
        plot_vmax,
        N_LIKELIHOOD_LEVELS,
    )

    likelihood_ticks = np.linspace(
        plot_vmin,
        plot_vmax,
        N_LIKELIHOOD_TICKS,
    )

    # Interior tick values are also used as quantitative contours.
    likelihood_contour_levels = (
        likelihood_ticks[1:-1]
    )

    norm = Normalize(
        vmin=plot_vmin,
        vmax=plot_vmax,
    )

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    print(
        "\n=== CLUMPED LOG-LIKELIHOOD INSIDE "
        "CLASS-SPECIFIC DOMAINS ==="
    )

    for k in CLASSES:

        values = supported_values_by_class[k]

        print(
            f"{k}: "
            f"min={np.nanmin(values):.6f}, "
            f"median={np.nanmedian(values):.6f}, "
            f"max={np.nanmax(values):.6f}"
        )

    print(
        "Common displayed log-likelihood range: "
        f"{plot_vmin:.3f} to {plot_vmax:.3f}"
    )

    # ------------------------------------------------------------------
    # Figure
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(
        1,
        n_classes,
        figsize=(5.7 * n_classes, 5.0),
        sharex=True,
        sharey=True,
        squeeze=False,
    )

    axes = axes.ravel()

    for i, (ax, k) in enumerate(
        zip(axes, CLASSES)
    ):

        ll_field = likelihood_maps[k]
        class_support = class_support_maps[k]
        class_domain = class_domains[k]

        # Mask only outside the class-specific support domain.
        display_field = np.ma.masked_where(
            ~class_domain,
            ll_field,
        )

        # --------------------------------------------------------------
        # Exact clumped log-likelihood
        # --------------------------------------------------------------
        cf = ax.contourf(
            XXc,
            YYc,
            display_field,
            levels=likelihood_levels,
            cmap=LIKELIHOOD_CMAPS[k],
            norm=norm,
            extend="both",
        )

        # --------------------------------------------------------------
        # Boundary of the class-specific support domain
        # --------------------------------------------------------------
        if SHOW_CLASS_SUPPORT_CONTOUR:
            ax.contour(
                XXc,
                YYc,
                class_support,
                levels=[COMMON_KDE_THRESH],
                colors="black",
                linewidths=1.0,
                zorder=6,
            )

        # --------------------------------------------------------------
        # Quantitative log-likelihood contours
        # --------------------------------------------------------------
        class_min = np.nanmin(
            supported_values_by_class[k]
        )

        class_max = np.nanmax(
            supported_values_by_class[k]
        )

        available_levels = [
            level
            for level in likelihood_contour_levels
            if class_min < level < class_max
        ]

        if available_levels:

            cs = ax.contour(
                XXc,
                YYc,
                display_field,
                levels=available_levels,
                colors="black",
                linewidths=0.65,
                alpha=0.75,
                zorder=5,
            )

            if SHOW_LIKELIHOOD_CONTOUR_LABELS:
                ax.clabel(
                    cs,
                    fmt=lambda value: f"{value:.1f}",
                    fontsize=7,
                    inline=True,
                    inline_spacing=3,
                )

        # --------------------------------------------------------------
        # Optional training observations
        # --------------------------------------------------------------
        if SHOW_CLASS_DATA_POINTS:
            ax.scatter(
                CLUMP[k][:, 0],
                CLUMP[k][:, 1],
                s=13,
                facecolor="none",
                edgecolor="white",
                linewidth=0.45,
                alpha=0.75,
                zorder=7,
            )

        ax.set_xlim(
            xv_c[0],
            xv_c[-1],
        )

        ax.set_ylim(
            yv_c[0],
            yv_c[-1],
        )

        ax.set_xlabel(
            r"$\Delta^{13}\mathrm{CH_3D}$ (‰)"
        )

        ax.set_title(
            NAMES[k],
            fontsize=12,
        )

        if i > 0:
            ax.tick_params(
                axis="y",
                labelleft=False,
            )

        # --------------------------------------------------------------
        # One class-colored colorbar per panel
        # --------------------------------------------------------------
        divider = make_axes_locatable(ax)

        cax = divider.append_axes(
            "right",
            size="4.5%",
            pad=0.06,
        )

        cb = fig.colorbar(
            cf,
            cax=cax,
            ticks=likelihood_ticks,
        )

        cb.set_label(
            "Clumped-isotope log-likelihood\n"
            r"$LL_k(z)=\ln L_k(z)$",
            fontsize=9,
        )

        cb.ax.tick_params(
            labelsize=8
        )

    axes[0].set_ylabel(
        r"$\Delta^{12}\mathrm{CH_2D_2}$ (‰)"
    )

    fig.tight_layout()
    save_fig('04_clumped_loglikelihood_by_class')   # SI Fig. S10 (TMO) / S11 (BIO_ABI)


plot_clumped_log_likelihood_inside_class_domains()

#%% THERMODYNAMIC EQUILIBRIUM CURVE

T_K_EQ = np.arange(0, 1501, 50) + 273.15
G5 = 1.0 / T_K_EQ
T_C_EQ = T_K_EQ - 273.15

D13CH3D_EQ = 1000.0 * (
    0.03555020 * G5
    - 433.038 * G5**2
    + 1.27021e6 * G5**3
    - 5.94804e8 * G5**4
    + 1.19663e11 * G5**5
    - 9.0723e12 * G5**6
)
D12CH2D2_EQ = 1000.0 * (
    0.183798 * G5
    - 785.483 * G5**2
    + 1.056280e6 * G5**3
    + 9.37307e7 * G5**4
    - 8.91948e10 * G5**5
    + 9.90173e12 * G5**6
)


def add_equilibrium_curve(ax):
    
    ax.plot(D13CH3D_EQ, D12CH2D2_EQ, color="black", linewidth=1.2, linestyle="--", zorder=10)
    for temperature, offset in SCHEME['EQ_LABEL_OFFSETS'].items():
        index = int(np.argmin(np.abs(T_C_EQ - temperature)))
        ax.plot(D13CH3D_EQ[index], D12CH2D2_EQ[index], "ko", markersize=2.5, zorder=11)
        ax.annotate(
            f"{temperature}°C",
            xy=(D13CH3D_EQ[index], D12CH2D2_EQ[index]),
            xytext=offset,
            textcoords="offset points",
            fontsize=8,
            fontweight="bold",
            zorder=11,
        )



#%% FINAL SEPARATE GATED POSTERIOR MAPS (SI S8)
# Process labels written on the maps (TMO classes only; none for BIO_ABI).
ANNOTATIONS = {
    "T": [
        (9, 8, "Gas window formation\nhigh maturity"),
        (6, -10, "Low maturity"),
    ],
    "M": [
        (2, 35, "Energy-limited\nmethanogenesis"),
        (-3, -7, 'Kinetically driven\nHydrogenotrophic\n("endogenous")'),
        (7, -55, 'Kinetically driven\nmethylated compound\n("exogenous")'),
    ],
    "O": [
        (10, 105, "Kinetically driven - AOM"),
        (0, 75, "AeOM open-system /\nOH-Cl oxidation"),
        (15, 15, "Energy-limited AOM"),
        (0, -50, "AeOM close-system"),
    ],
}



def plot_gated_maps():
    n_classes = len(CLASSES)
    fig, axes = plt.subplots(1, n_classes, figsize=(16 * n_classes / 3, 4.8),
                             constrained_layout=True, squeeze=False)
    axes = axes.ravel()
    panel_labels = ["A", "B", "C", "D", "E", "F"]

    for i, (ax, k) in enumerate(zip(axes, CLASSES)):

        field = np.asarray(P_POST_GATED[k], float)
        minimum = MIN_SHOW[k]
        masked = np.ma.masked_where(field < minimum, field)
        levels = np.linspace(minimum, 1.0, 6)

        contour = ax.contourf(
            XXc,
            YYc,
            masked,
            levels=levels,
            cmap=CMAPS[k],
            vmin=0.0,
            vmax=1.0,
        )

        ax.contour(
            XXc, YYc, field,
            levels=[minimum],
            colors="black",
            linewidths=0.7
        )

        ax.contour(
            XXc, YYc, masked,
            levels=levels,
            colors="black",
            linewidths=0.2
        )

        add_equilibrium_curve(ax)

        if SHOW_CLUMPED_DATA_POINTS:
            ax.scatter(
                DATA_POINTS[k][:, 0],
                DATA_POINTS[k][:, 1],
                s=18,
                c=POINT_COLORS[k],
                edgecolors="black",
                linewidths=0.3,
                alpha=0.85,
                zorder=12,
            )

        # =====================================================
        # LABELS
        # =====================================================
        for x, y, label in ANNOTATIONS.get(k, []):
            ax.text(
                x,
                y,
                label,
                fontsize=9.5,
                fontname="Arial",
                fontweight="bold",
                ha="center",
                va="center",
                zorder=100,
                clip_on=False,
               
            )

        ax.text(
            0.02, 0.98,
            panel_labels[i],
            transform=ax.transAxes,
            fontsize=15,
            fontname="Arial",
            fontweight="bold",
            ha="left",
            va="top",
            zorder=200
        )
        ax.set_title(f"{NAMES[k]}")
        ax.set_xlabel(r"$\Delta^{13}$CH$_3$D (‰)")
        ax.set_ylabel(r"$\Delta^{12}$CH$_2$D$_2$ (‰)")

        cbar = fig.colorbar(contour, ax=ax)
        cbar.ax.yaxis.set_major_formatter(
            mticker.FormatStrFormatter("%.2g")
        )

    save_fig('05_gated_posterior_panels')


plot_gated_maps()

#%% NON-GATED POSTERIOR PROBABILITIES (SI S8)

def plot_raw_posterior_maps():

    n_classes = len(CLASSES)
    fig, axes = plt.subplots(
        1, n_classes,
        figsize=(16 * n_classes / 3, 4.8),
        constrained_layout=True,
        squeeze=False
    )
    axes = axes.ravel()

    # Same probability scale for all classes
    levels = np.linspace(0.0, 1.0, 10)

    for ax, k in zip(axes, CLASSES):

        # STRICT posterior probability — NO support gate
        field = np.asarray(P_POST[k], float)

        contour = ax.contourf(
            XXc,
            YYc,
            field,
            levels=levels,
            cmap=CMAPS[k],
            vmin=0.0,
            vmax=1.0,
            extend="neither",
        )

        # Probability isolines
        ax.contour(
            XXc,
            YYc,
            field,
            levels=levels[1:-1],
            colors="black",
            linewidths=0.25,
            alpha=0.6,
        )

        add_equilibrium_curve(ax)

        if SHOW_CLUMPED_DATA_POINTS:
            ax.scatter(
                DATA_POINTS[k][:, 0],
                DATA_POINTS[k][:, 1],
                s=18,
                c=POINT_COLORS[k],
                edgecolors="black",
                linewidths=0.3,
                alpha=0.85,
                zorder=12,
            )

        ax.set_title(NAMES[k])
        ax.set_xlabel(r"$\Delta^{13}$CH$_3$D (‰)")
        ax.set_ylabel(r"$\Delta^{12}$CH$_2$D$_2$ (‰)")

        cbar = fig.colorbar(
            contour,
            ax=ax,
            ticks=np.linspace(0, 1, 6)
        )
        cbar.set_label("Posterior probability")

    fig.suptitle(
        "Non-gated posterior probabilities",
        fontsize=13
    )

    save_fig('06_raw_posterior_panels')   # SI Fig. S12 (TMO)


plot_raw_posterior_maps()

#%% FINAL OVERLAID GATED POSTERIOR MAP

def plot_gated_overlay():
    style = SCHEME['POST_OVERLAY']
    zorder, alpha_fill = style['zorder'], style['alpha']
    alpha_edge = {k: 1.0 for k in CLASSES}
    alpha_inner = {k: 0.9 for k in CLASSES}
    overlay_cmaps = {k: plt.get_cmap(style['cmaps'][k]) for k in CLASSES}

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.subplots_adjust(right=0.72)
    contour_sets = {}

    for k in CLASSES:
        field = P_POST_GATED[k]
        minimum = MIN_SHOW[k]
        levels = np.linspace(minimum, 1.0, 8)
        z = zorder[k]

        contour_sets[k] = ax.contourf(
            XXc,
            YYc,
            field,
            levels=levels,
            cmap=overlay_cmaps[k],
            vmin=0.0,
            vmax=1.0,
            alpha=alpha_fill[k],
            zorder=z,
            antialiased=True,
        )
        ax.contour(
            XXc,
            YYc,
            field,
            levels=[minimum],
            colors="black",
            linewidths=0.5,
            alpha=alpha_edge[k],
            zorder=z + 0.3,
        )
        ax.contour(
            XXc,
            YYc,
            field,
            levels=levels,
            colors="black",
            linewidths=0.2,
            alpha=alpha_inner[k],
            zorder=z + 0.2,
        )

    add_equilibrium_curve(ax)

    if SHOW_CLUMPED_DATA_POINTS:
        for k in CLASSES:
            ax.scatter(
                DATA_POINTS[k][:, 0],
                DATA_POINTS[k][:, 1],
                s=22,
                c=POINT_COLORS[k],
                edgecolors="black",
                linewidths=0.4,
                alpha=0.9,
                zorder=12,
            )

    divider = make_axes_locatable(ax)
    for k in CLASSES:
        cax = divider.append_axes("right", size="5%", pad=0.08)
        colorbar = fig.colorbar(contour_sets[k], cax=cax)
    
        if k == CLASSES[-1]:  # numeric ticks only on the right-most colorbar
            ticks = np.linspace(MIN_SHOW[k], 1.0, 8)
            colorbar.set_ticks(ticks)
            colorbar.set_ticklabels([f"{t:.2f}" for t in ticks])
            colorbar.ax.tick_params(labelsize=8)
        else:
            colorbar.set_ticks([])
    
        cax.set_title(
            NAMES[k],
            fontsize=8,
            fontweight="bold",
            rotation=45,
            loc="left",
            pad=6,
        )

    if SHOW_CLUMPED_DATA_POINTS:
        handles = [
            Line2D(
                [0],
                [0],
                marker="o",
                color="white",
                markerfacecolor=POINT_COLORS[k],
                markeredgecolor="black",
                markersize=6,
                label=NAMES[k],
            )
            for k in CLASSES
        ]
        ax.legend(handles=handles, loc="lower right", fontsize=8, title="Data points", title_fontsize=8)

    ax.set_xlabel(r"$\Delta^{13}$CH$_3$D (‰)")
    ax.set_ylabel(r"$\Delta^{12}$CH$_2$D$_2$ (‰)")
    ax.set_aspect("auto")
    save_fig('07_gated_posterior_overlay')


plot_gated_overlay()




#%% 10 — EXTERNAL SAMPLES AND POINTWISE EVALUATION (SI S9; TMO mode: Tyne et al. 2021, SI S11)
# External samples are scored with the fitted KDEs; they are never added to the
# training arrays. Run after the KDE fitting (no refit here).
VAL_T = POINTWISE_BULK_T
VAL_GAMMA = POINTWISE_BULK_GAMMA
VAL_CLASSES = CLASSES
VAL_OUTPUT = OUTPUT_DIR / 'Tyne_validation'
TYNE_DOI = '10.1038/s41586-021-04153-3'
RUN_TYNE = (MODEL_MODE == 'TMO')   # the Tyne et al. test set is defined for the T/M/O scheme only
EXTERNAL_COLUMNS = ['sample_id', 'site', 'd13C', 'dD', 'D13CH3D', 'D12CH2D2']

if RUN_TYNE:
    # Tyne et al. (2021): bulk from Source Data Extended Data Fig. 3, clumped from
    # Extended Data Table 2 (O2 excluded: incomplete doubly clumped measurement).
    VAL_DATA = pd.DataFrame([
     ('O1','Olla',-47.6,-176.85,4.89,12.41),
     ('O3','Olla',-49.3,-176.67,5.62,9.13),
     ('O4','Olla',-48.2,-184.08,3.93,12.19),
     ('O5','Olla',-46.7,-176.91,5.66,12.46),
     ('O6','Olla',-44.8,-174.71,3.45,9.82),
     ('NHH1','Nebo-Hemphill',-46.0,-180.87,3.77,4.27),
     ('NHH2','Nebo-Hemphill',-49.8,-180.30,4.38,3.85),
     ('NHH3','Nebo-Hemphill',-61.0,-180.63,3.17,5.03),
     ('NHH4','Nebo-Hemphill',-54.5,-190.21,3.16,1.56),
     ('NHH5','Nebo-Hemphill',-57.0,-186.84,3.28,1.80),
     ('NHH6','Nebo-Hemphill',-57.5,-183.93,2.90,.01),
     ('NHH7','Nebo-Hemphill',-59.1,-184.81,3.33,2.02),
     ('NHH8','Nebo-Hemphill',-56.2,-182.16,3.64,5.14),
    ],columns=['sample_id','site','d13C','dD','D13CH3D','D12CH2D2'])
    VAL_DATA['study']='Tyne 2021'
    VAL_DATA['doi']='10.1038/s41586-021-04153-3'
    # Qualitative comparison targets, not true class labels or mixing fractions.
    VAL_DATA['expected_set']=np.where(VAL_DATA.site.eq('Olla'),'M|O','T')
    VAL_DATA['finding']=np.where(VAL_DATA.site.eq('Olla'),
     'Microbial-dominated methane; in situ methanogenesis and AOM',
     'Thermogenic-dominated with microbial contribution')
    VAL_DATA.loc[VAL_DATA.sample_id.isin(['O4','O6']),'finding']='Near internal equilibrium; temperatures below thermogenic generation; microbial contribution, dominance unresolved'
    VAL_DATA.loc[VAL_DATA.sample_id.isin(['O4','O6']),'expected_set']=''  # no unique dominant class claimed
    VAL_DATA['finding_scope']='group-level qualitative interpretation; not independent class ground truth'
    VAL_DATA['data_status']='Bulk verified against original Source Data Extended Data Fig. 3; clumped from Extended Data Table 2 transcription'
    # Published clumped uncertainties (Extended Data Table 2). Bulk analytical
    # sigmas are not supplied and are not assumed.
    TYNE_CLUMPED_SIGMAS = {
        'O1':(.36,1.29),'O3':(.31,1.60),'O4':(.52,1.39),
        'O5':(.39,1.07),'O6':(.26,1.53),
        'NHH1':(.37,1.29),'NHH2':(.28,1.81),'NHH3':(.35,1.24),
        'NHH4':(.54,1.67),'NHH5':(.40,1.13),'NHH6':(.42,1.63),
        'NHH7':(.57,1.38),'NHH8':(.35,1.10)
    }
    VAL_DATA['d13C_sigma']=0.0
    VAL_DATA['dD_sigma']=0.0
    VAL_DATA['D13CH3D_sigma']=VAL_DATA.sample_id.map(lambda x:TYNE_CLUMPED_SIGMAS[x][0])
    VAL_DATA['D12CH2D2_sigma']=VAL_DATA.sample_id.map(lambda x:TYNE_CLUMPED_SIGMAS[x][1])
else:
    VAL_DATA = pd.DataFrame(columns=EXTERNAL_COLUMNS + ['study', 'doi', 'expected_set', 'finding'])

# External pointwise observations are evaluated using the fitted KDEs but
# are never added to the training arrays.
def load_external_points():
    tables=[]
    if EXTERNAL_SAMPLES_FILE is not None:
        fp=Path(EXTERNAL_SAMPLES_FILE).expanduser()
        if not fp.is_file(): raise FileNotFoundError(f'External sample file not found: {fp}')
        data=pd.read_excel(fp,sheet_name=EXTERNAL_SHEET) if fp.suffix.lower() in ('.xlsx','.xls') else pd.read_csv(fp)
        rename={COL_BULK['d13C']:'d13C',COL_BULK['dD']:'dD',
                COL_CLUMP['D13CH3D']:'D13CH3D',COL_CLUMP['D12CH2D2']:'D12CH2D2'}
        tables.append(data.rename(columns=rename))
    if MANUAL_SAMPLES: tables.append(pd.DataFrame(MANUAL_SAMPLES))
    if not tables: return pd.DataFrame(columns=VAL_DATA.columns)
    data=pd.concat(tables,ignore_index=True)
    for col in EXTERNAL_COLUMNS:
        if col not in data.columns:
            if col=='sample_id': data[col]=[f'External_{i+1}' for i in range(len(data))]
            elif col=='site': data[col]='External'
            else: raise KeyError(f'External sample file missing {col}')
    if 'study' not in data.columns: data['study']='External'
    if 'doi' not in data.columns: data['doi']='external'
    if 'expected_set' not in data.columns: data['expected_set']=''
    if 'finding' not in data.columns: data['finding']='Not assigned'
    return data

EXTERNAL_INPUT=load_external_points()
if not EXTERNAL_INPUT.empty:
    VAL_DATA = pd.concat([VAL_DATA, EXTERNAL_INPUT],ignore_index=True,sort=False)

#%% EXTERNAL VALIDATION — CALCULATE FOUR MODELS (no KDE refit)
# Four pointwise models on the exact fitted KDEs:
#   Bulk = softmax(LL_bulk) | Clumped = softmax(LL_clumped) |
#   Original = softmax(LL_bulk + LL_clumped) |
#   Adjusted = softmax(G_bulk * (LL_bulk - max LL_bulk) + LL_clumped)   (S9)
def _target_mass(p, targets):
    """Probability mass on the qualitative target classes (NaN if no target given)."""
    out = []
    for i, t in enumerate(targets):
        idx = [j for j, k in enumerate(VAL_CLASSES) if k in t]
        out.append(float(p[i, idx].sum()) if idx else np.nan)
    return out


def val_log_density(points, scales, kdes):
    # <<BULK-CLASSES>> used for both bulk (S_BULK/KDE_BULK) and clumped KDEs
    return np.column_stack([loglike_on_grid(points,scales[k],kdes[k]) for k in VAL_CLASSES])

def val_gate(log_densities, grid_fields, t, gamma):
    if not 0 <= t < 1 or gamma <= 0:
        raise ValueError('Require 0 <= threshold < 1 and gamma > 0')
    maxima=np.array([np.nanmax(grid_fields[k]) for k in VAL_CLASSES])
    rel=np.exp(np.clip(log_densities-maxima,-745,0))
    raw=1-np.prod(1-rel,axis=1)
    return raw, np.clip((raw-t)/(1-t),0,1)**gamma

def val_evaluate(data,t=VAL_T,gamma=VAL_GAMMA):
    coords=['d13C','dD','D13CH3D','D12CH2D2']
    d=data.copy()
    d[coords]=d[coords].apply(pd.to_numeric,errors='coerce')
    missing=~np.isfinite(d[coords].to_numpy()).all(axis=1)
    if missing.any(): print('Skipped incomplete samples:',d.loc[missing,'sample_id'].tolist())
    d=d.loc[~missing].reset_index(drop=True)
    if d.empty: raise ValueError('No complete measured samples')
    if d.duplicated(['doi','sample_id']).any(): raise ValueError('Duplicate DOI/sample IDs')
    b=d[coords[:2]].to_numpy(); z=d[coords[2:]].to_numpy()
    lb=val_log_density(b,S_BULK,KDE_BULK); lc=val_log_density(z,S_CLUMP,KDE_CLUMP)
    raw,gb=val_gate(lb,LL_BULK,t,gamma)
    cb=lb-lb.max(axis=1,keepdims=True)
    models={'Bulk':softmax(lb,axis=1),'Clumped':softmax(lc,axis=1),
            'Original':softmax(lb+lc,axis=1),'Adjusted':softmax(gb[:,None]*cb+lc,axis=1)}
    eff=softmax(gb[:,None]*cb,axis=1)
    d['bulk_raw_support']=raw; d['bulk_gate']=gb
    d['clumped_raw_support'],_=val_gate(lc,LL_CLUMP,0,1)
    d['clumped_display_gate']=np.nan
    inside=(z[:,0]>=xv_c[0])&(z[:,0]<=xv_c[-1])&(z[:,1]>=yv_c[0])&(z[:,1]<=yv_c[-1])
    if inside.any(): d.loc[inside,'clumped_display_gate']=np.clip(bilinear_interp(xv_c,yv_c,COMMON_GATE,z[inside]),0,1)
    d['bulk_inside_grid']=(b[:,0]>=xv_b[0])&(b[:,0]<=xv_b[-1])&(b[:,1]>=yv_b[0])&(b[:,1]<=yv_b[-1])
    d['clumped_inside_grid']=inside
    for j,k in enumerate(VAL_CLASSES): d['Effective_'+k]=eff[:,j]
    for name,p in models.items():
        assert np.allclose(p.sum(axis=1),1)
        for j,k in enumerate(VAL_CLASSES): d[name+'_'+k]=p[:,j]
        d[name+'_winner']=np.asarray(VAL_CLASSES)[p.argmax(axis=1)]
        d[name+'_entropy']=-np.sum(p*np.log(np.maximum(p,1e-300)),axis=1)/np.log(len(VAL_CLASSES))
        # Agreement with an explicitly selected qualitative target only.
        targets=d['expected_set'].fillna('').astype(str).str.split('|')
        d[name+'_target_mass']=_target_mass(p,targets.tolist())
    d['delta_target_mass']=d.Adjusted_target_mass-d.Original_target_mass
    return d

VAL_METHODS=['Bulk','Clumped','Original','Adjusted']
if len(VAL_DATA):
    VAL_RESULTS=val_evaluate(VAL_DATA, VAL_T, VAL_GAMMA)
    VAL_SUMMARY=VAL_RESULTS.groupby(['study','site'])[[m+'_target_mass' for m in VAL_METHODS]+['bulk_gate']].mean()
    print(VAL_RESULTS[['study','sample_id','finding','bulk_gate']+[m+'_'+k for m in VAL_METHODS for k in VAL_CLASSES]+['delta_target_mass']].to_string(index=False,float_format=lambda x:f'{x:.3f}'))
    print('\nMean qualitative target mass (not accuracy):\n',VAL_SUMMARY.round(3))
else:
    VAL_RESULTS = None
    print('No external samples: pointwise evaluation skipped (figures are still produced).')


#%% OPTIONAL — ANALYTICAL UNCERTAINTY MONTE CARLO (NO INVENTED SIGMAS)
# Enable RUN_POINTWISE_MC in cell 00. Missing uncertainty columns are zero.
# Assumes independent Gaussian measurement uncertainties, when supplied.
MC_SIGMAS=['d13C_sigma','dD_sigma','D13CH3D_sigma','D12CH2D2_sigma']
def pointwise_mc(data, n=POINTWISE_MC_N, seed=POINTWISE_MC_SEED):
    rng=np.random.default_rng(seed)
    out=[]
    for row in data.to_dict('records'):
        mu=np.array([float(row[k]) for k in ('d13C','dD','D13CH3D','D12CH2D2')])
        sigma=np.array([float(row.get(k,0) or 0) if pd.notna(row.get(k,0)) else 0
                        for k in MC_SIGMAS])
        if (sigma<0).any(): raise ValueError(f'Negative sigma for {row["sample_id"]}')
        x=rng.normal(mu,sigma,(n,4))
        lb=val_log_density(x[:,:2],S_BULK,KDE_BULK)
        lc=val_log_density(x[:,2:],S_CLUMP,KDE_CLUMP)
        _, gate=val_gate(lb,LL_BULK,POINTWISE_BULK_T,POINTWISE_BULK_GAMMA)
        probs=softmax(gate[:,None]*(lb-lb.max(axis=1,keepdims=True))+lc,axis=1)
        win=np.argmax(probs,axis=1)
        result={'sample_id':row['sample_id'],'site':row.get('site',''),
                'n_draws':n,'assumed_independent_errors':True,
                'any_nonzero_sigma':bool((sigma>0).any())}
        for j,k in enumerate(VAL_CLASSES):
            result.update({f'{k}_mean':probs[:,j].mean(),
                f'{k}_median':np.median(probs[:,j]),
                f'{k}_q025':np.quantile(probs[:,j],.025),
                f'{k}_q975':np.quantile(probs[:,j],.975),
                f'{k}_winner_fraction':np.mean(win==j)})
        out.append(result)
    return pd.DataFrame(out)
if RUN_POINTWISE_MC and VAL_RESULTS is not None:
    Path(VAL_OUTPUT).mkdir(parents=True,exist_ok=True)
    VAL_MC=pointwise_mc(VAL_DATA)
    VAL_MC.to_csv(Path(VAL_OUTPUT)/'pointwise_uncertainty_MC.csv',index=False)
    print('Monte Carlo uncertainty:',len(VAL_MC),'samples')
else:
    VAL_MC=None

#%% TYNE — POINTWISE PIES ON THE EXISTING SPATIAL POSTERIOR (TMO mode only; SI Fig. S15)
if RUN_TYNE:
    from matplotlib.offsetbox import AnnotationBbox, DrawingArea
    from matplotlib.patches import Wedge, Circle, Patch

    # TYNE_PIE_METHOD, TYNE_PIE_SIZE and TYNE_SHOW_LABELS are set in cell 00.
    TYNE_XLIM = (-0.9, 10.2)
    TYNE_YLIM = (-27, 31)
    TYNE_ZOOM_XLIM = (2.3, 6.5)
    TYNE_ZOOM_YLIM = (-3, 16)
    TYNE_OUT = Path(VAL_OUTPUT)
    TYNE_OUT.mkdir(parents=True, exist_ok=True)
    TYNE_VAL = VAL_RESULTS.loc[VAL_RESULTS.doi.eq(TYNE_DOI)].copy()
    assert len(TYNE_VAL)==13, 'Expected 13 complete Tyne samples'
    TYNE_COLORS = dict(POINT_COLORS)  # original T/M/O pie colors
    TYNE_MAP_CMAPS = {'T':'Oranges', 'M':CMAPS['M'], 'O':CMAPS['O']}
    TYNE_ALPHA = {'T':.70,'M':.75,'O':.99}
    TYNE_NAMES = {'T':'Thermogenic','M':'Microbial','O':'Oxidation'}
    # Labels placed away from the crowded cluster, in isotope coordinates.
    TYNE_LABEL_FULL = {'O1':(4.5,17),'O3':(6.8,8),'O4':(2.6,15.5),'O5':(6.9,15.5),'O6':(1.6,9.2),
     'NHH1':(5.9,5.0),'NHH2':(6.0,.5),'NHH3':(.6,4.8),'NHH4':(.7,1.8),'NHH5':(4.5,-4.2),'NHH6':(1.8,-5.8),'NHH7':(2.5,-3.4),'NHH8':(1.2,7.2)}
    TYNE_LABEL_ZOOM = {'O1':(4.35,15),'O3':(6.15,7.2),'O4':(3.2,14.4),'O5':(6.1,14.7),'O6':(2.65,9.5),
     'NHH1':(4.7,6.7),'NHH2':(5.25,3.0),'NHH3':(2.65,6.7),'NHH4':(2.6,2.1),'NHH5':(3.9,-1.9),'NHH6':(2.65,-1.8),'NHH7':(4.05,.25),'NHH8':(3.6,7.8)}

    def tyne_background(ax, zoomed=False):
        # Unchanged existing spatial map, not a pointwise posterior surface.
        for k in ('O','M','T'):
            v=np.asarray(P_POST_GATED[k],float)
            levels=np.linspace(float(MIN_SHOW[k]),1.,8)
            ax.contourf(XXc,YYc,v,levels=levels,cmap=TYNE_MAP_CMAPS[k],vmin=0,vmax=1,
                        alpha=TYNE_ALPHA[k],zorder={'O':1,'M':2,'T':3}[k],antialiased=True)
            ax.contour(XXc,YYc,v,levels=levels,colors='black',linewidths=.22,alpha=.35,zorder=4)
        add_equilibrium_curve(ax)
        ax.set(xlim=TYNE_ZOOM_XLIM if zoomed else TYNE_XLIM,
               ylim=TYNE_ZOOM_YLIM if zoomed else TYNE_YLIM,
               xlabel=r'$\Delta^{13}$CH$_3$D (‰)',ylabel=r'$\Delta^{12}$CH$_2$D$_2$ (‰)')

    def tyne_pie(ax,row,method,labels):
        xy=(row.D13CH3D,row.D12CH2D2)
        vals=np.array([getattr(row,method+'_'+k) for k in VAL_CLASSES],float)
        assert np.isclose(vals.sum(),1)
        size=TYNE_PIE_SIZE; rad=size/2
        da=DrawingArea(size,size,0,0); angle=90.
        for k,p in zip(VAL_CLASSES,vals):
            if p>0:
                da.add_artist(Wedge((rad,rad),rad,angle-360*p,angle,
                             facecolor=TYNE_COLORS[k],edgecolor='black',linewidth=.45))
                angle-=360*p
        da.add_artist(Circle((rad,rad),rad,facecolor='none',edgecolor='black',linewidth=.7))
        ax.add_artist(AnnotationBbox(da,xy,frameon=False,pad=0,zorder=55))
        ax.scatter(*xy,marker='o' if row.site=='Olla' else '^',s=13,facecolor='white',edgecolor='black',linewidth=.55,zorder=56)
        if TYNE_SHOW_LABELS:
            ax.annotate(row.sample_id,xy=xy,xytext=labels[row.sample_id],fontsize=8,
                        ha='center',va='center',fontweight='semibold',zorder=60,
                        arrowprops=dict(arrowstyle='-',color='.25',lw=.55,shrinkA=2,shrinkB=TYNE_PIE_SIZE/2),
                        bbox=dict(facecolor='white',alpha=.76,pad=.6,edgecolor='none'))

    def tyne_finish(fig,caxes):
        for k,cax in zip(VAL_CLASSES,caxes):
            sm=ScalarMappable(norm=Normalize(0,1),cmap=TYNE_MAP_CMAPS[k]); sm.set_array([])
            cb=fig.colorbar(sm,cax=cax,ticks=[0,.2,.4,.6,.8,1])
            cax.set_title(TYNE_NAMES[k],fontsize=8,rotation=45,loc='left',pad=5)
            if k!='O': cb.set_ticks([])
            else: cb.set_label('Gated spatial posterior')
        handles=[Line2D([],[],marker=m,ls='',mfc='white',mec='black',label=s) for m,s in [('o','Olla'),('^','Nebo-Hemphill')]]
        handles += [Patch(facecolor=TYNE_COLORS[k],edgecolor='black',label=TYNE_NAMES[k]) for k in VAL_CLASSES]
        fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.015),ncol=5,frameon=False,fontsize=9)

    def tyne_save(fig,name):
        fig.savefig(TYNE_OUT/(name+'.pdf'),bbox_inches='tight')
        fig.savefig(TYNE_OUT/(name+'.png'),dpi=350,bbox_inches='tight')

    fig=plt.figure(figsize=(9.6,6.6))
    gs=fig.add_gridspec(1,4,width_ratios=[1,.034,.034,.034],left=.10,right=.89,bottom=.15,top=.87,wspace=.14)
    ax=fig.add_subplot(gs[0,0]); tyne_background(ax)
    for row in TYNE_VAL.itertuples(index=False): tyne_pie(ax,row,TYNE_PIE_METHOD,TYNE_LABEL_FULL)
    fig.suptitle('Tyne et al. (2021) — '+TYNE_PIE_METHOD+' pointwise posterior' if TYNE_PIE_METHOD in ('Adjusted','Original') else 'Tyne et al. (2021) — '+TYNE_PIE_METHOD+' class probabilities',fontweight='bold',y=.98)
    tyne_finish(fig,[fig.add_subplot(gs[0,j]) for j in (1,2,3)])
    tyne_save(fig,'Tyne_overview_'+TYNE_PIE_METHOD)
    if SHOW_FIGURES: plt.show()
    else: plt.close(fig)

    # Zoomed view split by field to reduce overlap without shifting sample locations.
    fig=plt.figure(figsize=(12,5.8))
    gs=fig.add_gridspec(1,5,width_ratios=[1,1,.035,.035,.035],left=.075,right=.9,bottom=.17,top=.84,wspace=.14)
    for j,site in enumerate(('Olla','Nebo-Hemphill')):
        ax=fig.add_subplot(gs[0,j]); tyne_background(ax,True)
        for row in TYNE_VAL.loc[TYNE_VAL.site.eq(site)].itertuples(index=False): tyne_pie(ax,row,TYNE_PIE_METHOD,TYNE_LABEL_ZOOM)
        ax.set_title(('A  ' if j==0 else 'B  ')+site,loc='left',fontweight='bold')
        if j: ax.set_ylabel('')
    fig.suptitle('Tyne et al. (2021) — '+TYNE_PIE_METHOD+' sample probabilities',fontweight='bold',y=.99)
    tyne_finish(fig,[fig.add_subplot(gs[0,j]) for j in (2,3,4)])
    tyne_save(fig,'Tyne_by_field_'+TYNE_PIE_METHOD)
    if SHOW_FIGURES: plt.show()
    else: plt.close(fig)


#%% TYNE — EXCEL COMPARISON WITH PUBLISHED INTERPRETATIONS (TMO mode only)
if RUN_TYNE:
    # No sample-specific mixing fractions are inferred from the model probabilities.
    # O4 and O6 have a microbial contribution, but no defensible unique target.
    TYNE_METHODS=['Bulk','Clumped','Original','Adjusted']
    TYNE_COMPARE=TYNE_VAL.copy()
    TYNE_COMPARE['author_group']=np.where(TYNE_COMPARE.site.eq('Nebo-Hemphill'),'Nebo-Hemphill: T-dominated',
        np.where(TYNE_COMPARE.sample_id.isin(['O4','O6']),'Olla O4/O6: microbial contribution','Olla O1/O3/O5: microbial cycling'))
    TYNE_COMPARE['reference']='https://doi.org/10.1038/s41586-021-04153-3'
    TYNE_COMPARE['comparison_target']=np.where(TYNE_COMPARE.site.eq('Nebo-Hemphill'),'T',
        np.where(TYNE_COMPARE.sample_id.isin(['O4','O6']),'No unique dominant class','M + O'))
    for method in TYNE_METHODS:
        TYNE_COMPARE[method+'_M_plus_O']=TYNE_COMPARE[method+'_M']+TYNE_COMPARE[method+'_O']
        TYNE_COMPARE[method+'_compatible_winner']=[('Not scored' if not s else ('Yes' if w in s.split('|') else 'No'))
              for s,w in zip(TYNE_COMPARE.expected_set,TYNE_COMPARE[method+'_winner'])]
    TYNE_COMPARE['adjusted_minus_clumped_target_mass']=TYNE_COMPARE.Adjusted_target_mass-TYNE_COMPARE.Clumped_target_mass
    TYNE_COMPARE['adjusted_minus_original_target_mass']=TYNE_COMPARE.Adjusted_target_mass-TYNE_COMPARE.Original_target_mass
    TYNE_COMPARE['interpretation_note']=np.where(TYNE_COMPARE.expected_set.eq(''),
        'Inspect M and O probabilities; no dominant-class score assigned.',
        'Target mass is qualitative agreement, not mixing fraction or accuracy.')
    TYNE_COMPARE['adjusted_report']=[f'T={t:.1%}; M={m:.1%}; O={o:.1%}' for t,m,o in TYNE_COMPARE[['Adjusted_T','Adjusted_M','Adjusted_O']].to_numpy()]
    report_cols=['sample_id','site','author_group','finding','comparison_target','adjusted_report','bulk_gate','clumped_display_gate']
    report_cols += [m+'_'+k for m in TYNE_METHODS for k in VAL_CLASSES]
    report_cols += [m+'_target_mass' for m in TYNE_METHODS]+['adjusted_minus_original_target_mass','adjusted_minus_clumped_target_mass','interpretation_note','reference']
    TYNE_REPORT=TYNE_COMPARE[report_cols]
    rows=[]
    for group,sub in TYNE_COMPARE.groupby('author_group',sort=False):
        for method in TYNE_METHODS:
            scores=sub[method+'_target_mass']; n=int(scores.notna().sum())
            rows.append({'Author group':group,'Model':method,'N':len(sub),'N scored':n,
                'Mean T':sub[method+'_T'].mean(),'Mean M':sub[method+'_M'].mean(),'Mean O':sub[method+'_O'].mean(),
                'Mean M+O':sub[method+'_M_plus_O'].mean(),'Mean target mass':scores.mean(),
                'Compatible winners':int(sub[method+'_compatible_winner'].eq('Yes').sum()) if n else np.nan,
                'Mean bulk gate':sub.bulk_gate.mean()})
    TYNE_GROUPS=pd.DataFrame(rows)
    TYNE_NOTES=pd.DataFrame([
     ('Reference','Tyne et al. (2021), Nature; https://doi.org/10.1038/s41586-021-04153-3'),
     ('Bulk data','Source Data Extended Data Fig. 3.'),
     ('Clumped data','Extended Data Table 2 (transcribed).'),
     ('O2','Excluded: incomplete doubly clumped measurement.'),
     ('O1/O3/O5','Microbial-dominated fluids undergoing methanogenesis and AOM; compare M+O.'),
     ('O4/O6','Near-equilibrium signatures below expected thermogenic generation temperature; microbial contribution, not a unique dominant class.'),
     ('Nebo-Hemphill','Thermogenic domination with microbial contribution; compare T.'),
     ('Target mass','Sum of probabilities for the selected author-compatible classes; no unique targets for O4/O6.'),
     ('Caution','Authors use clumped isotopes among other evidence. This is qualitative external consistency, not independently labeled ground truth.'),
     ('Caution','Class probabilities are not physical methane mixing fractions. No accuracy claim based on these mixed samples.'),
     ('Model','Adjusted = softmax(LL_clumped + G_bulk * centered LL_bulk).'),
     ('Spatial background','Existing P_POST_GATED; pie probabilities are normalized pointwise results, not gated spatial probabilities.'),
     ('Training independence','Check that Tyne measurements do not recur under a different DOI or reference before claiming strictly independent validation.'),
     ('Bulk threshold',VAL_T),('Bulk exponent',VAL_GAMMA),('Uncertainty','Central estimates only; no measurement uncertainty propagation in these comparisons.')
    ],columns=['Item','Description'])
    # Always export plain CSV for portability, plus formatted XLSX when available.
    sheets={'Comparison':TYNE_REPORT,'Field summary':TYNE_GROUPS,
            'Full results':TYNE_COMPARE,'Methods and sources':TYNE_NOTES}
    for name,table in sheets.items():
        table.to_csv(TYNE_OUT/('Tyne_'+name.lower().replace(' ','_')+'.csv'),index=False)
    output=TYNE_OUT/'Tyne_TMO_comparison.xlsx'
    if EXPORT_EXCEL:
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter
            from openpyxl.worksheet.table import Table, TableStyleInfo
            wb=Workbook();wb.remove(wb.active)
            for name,table in sheets.items():
                ws=wb.create_sheet(name);ws.append([str(x) for x in table.columns])
                for row in table.itertuples(index=False,name=None):
                    ws.append([None if pd.isna(x) else (x.item() if isinstance(x,np.generic) else x) for x in row])
                ws.freeze_panes='C2' if name!='Methods and sources' else 'B2'
                ws.auto_filter.ref=ws.dimensions
                ws.row_dimensions[1].height=34
                for cell in ws[1]:
                    cell.fill=PatternFill('solid',fgColor='203B54')
                    cell.font=Font(color='FFFFFF',bold=True)
                    cell.alignment=Alignment(wrap_text=True,vertical='center')
                for j,column in enumerate(table.columns,1):
                    label=str(column)
                    width=44 if label in ('finding','Description','interpretation_note','author_group') else 20
                    ws.column_dimensions[get_column_letter(j)].width=width
                    for i in range(2,len(table)+2):
                        cell=ws.cell(i,j)
                        if isinstance(cell.value,(int,float,np.integer,np.floating)):
                            cell.number_format='0.0000'
                        if width==44: cell.alignment=Alignment(wrap_text=True,vertical='top')
                ws.sheet_view.showGridLines=False
            wb.save(output)
            print('Excel workbook:',output)
        except ImportError:
            print('Excel optional: openpyxl missing; CSV files still exported. Install via macOS Terminal.')
    print('Saved figures and workbook:',TYNE_OUT)
    print(TYNE_REPORT[['sample_id','comparison_target','adjusted_report','adjusted_minus_original_target_mass','adjusted_minus_clumped_target_mass']].to_string(index=False))
    print(TYNE_GROUPS.to_string(index=False,float_format=lambda v:f'{v:.3f}'))


#%% EXTERNAL POINTWISE RESULTS — EXCEL / CSV, NO REFIT (SI S9)
# Pointwise results of the external samples (the Tyne et al. samples have their own outputs).
OTHER = (VAL_RESULTS.loc[~VAL_RESULTS.doi.eq(TYNE_DOI)].copy()
         if VAL_RESULTS is not None else pd.DataFrame())
if len(OTHER):
    show_cols = (['sample_id', 'bulk_raw_support', 'bulk_gate']
                 + ['Adjusted_' + k for k in CLASSES] + ['Adjusted_winner'])
    print('\nPOINTWISE POSTERIOR (normalized, NOT display-gated):')
    print(OTHER[show_cols].to_string(index=False, float_format=lambda v: f'{v:.4f}'))
    OTHER.to_csv(OUTPUT_DIR / 'external_pointwise_results.csv', index=False)
    if EXPORT_EXCEL:
        try:
            OTHER.to_excel(OUTPUT_DIR / 'external_pointwise_results.xlsx', index=False)
        except ImportError:
            print('Excel writer unavailable; CSV output is complete.')
    print('Exported', len(OTHER), 'external pointwise samples')


#%% 11 — BIO_ABI MODE: TWO-PANEL POINTWISE DIAGNOSTIC OF ONE EXTERNAL SAMPLE (SI S9, Fig. S16)
# Panel A: bulk prior map with the sample-specific raw and tempered bulk prior.
# Panel B: clumped posterior map with the clumped-only and combined posteriors.
# All numbers come from VAL_RESULTS (cell 10); nothing is refitted.

def _two_class_overlay(ax, X, Y, fields, space, min_show=0.02):
    """Overlay of the two class maps (opacity/order from SCHEME['POST_OVERLAY'])."""
    style = SCHEME['POST_OVERLAY']
    contour_sets = {}
    for k in CLASSES:
        values = np.asarray(fields[k], float)
        masked = np.ma.masked_less(values, min_show)
        levels = np.linspace(min_show, 1.0, 6)
        contour_sets[k] = ax.contourf(X, Y, masked, levels=levels, cmap=CMAPS[k], vmin=0, vmax=1,
                                      alpha=style['alpha'][k], zorder=style['zorder'][k])
        inner = levels[(levels > np.nanmin(values)) & (levels < np.nanmax(values))]
        if len(inner):
            ax.contour(X, Y, masked, levels=inner, colors='black', linewidths=.22, alpha=.7,
                       zorder=style['zorder'][k] + .2)
    if space == 'bulk':
        ax.set_xlabel(r'$\delta^{13}$C-CH$_4$ (‰)')
        ax.set_ylabel(r'$\delta$D-CH$_4$ (‰)')
        ax.set_xlim(*BULK_XLIM)
        ax.set_ylim(*BULK_YLIM)
    else:
        add_equilibrium_curve(ax)
        ax.set_xlabel(r'$\Delta^{13}$CH$_3$D (‰)')
        ax.set_ylabel(r'$\Delta^{12}$CH$_2$D$_2$ (‰)')
        ax.set_xlim(*CLUMP_XLIM)
        ax.set_ylim(*CLUMP_YLIM)
    return contour_sets


def _two_colorbars(fig, contours, lefts, bottom, height, bar_width):
    """Two discrete colour bars; numeric ticks only on the outer (last-class) bar."""
    for i, k in enumerate(CLASSES):
        cax = fig.add_axes([lefts[i], bottom, bar_width, height])
        cb = fig.colorbar(contours[k], cax=cax, spacing='uniform')
        cb.solids.set_edgecolor('face')
        if k != CLASSES[-1]:
            cb.set_ticks([])
            cb.ax.tick_params(which='both', length=0)
        else:
            cb.set_ticks(contours[k].levels)
            cb.ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f'))
            cb.ax.tick_params(labelsize=8, length=2, pad=2)
        fig.text(lefts[i] + bar_width * .3, bottom + height + .015, NAMES[k], rotation=50,
                 fontsize=8.5, fontweight='bold', ha='left', va='bottom')


def figure_pointwise_two_panel(row):
    """Two-panel diagnostic for one row of VAL_RESULTS (two-class model only)."""
    k1, k2 = CLASSES
    sid = str(row['sample_id'])
    label = row.get('source', None)
    label = label if isinstance(label, str) and label.strip() else sid
    bulk_pt = np.array([float(row['d13C']), float(row['dD'])])
    clump_pt = np.array([float(row['D13CH3D']), float(row['D12CH2D2'])])
    raw1, raw2 = float(row['Bulk_' + k1]), float(row['Bulk_' + k2])
    eff1, eff2 = float(row['Effective_' + k1]), float(row['Effective_' + k2])
    clu1, clu2 = float(row['Clumped_' + k1]), float(row['Clumped_' + k2])
    pos1, pos2 = float(row['Adjusted_' + k1]), float(row['Adjusted_' + k2])
    gb, raw_gb = float(row['bulk_gate']), float(row['bulk_raw_support'])

    def odds(p):
        q = max(1.0 - p, 1e-15)
        ratio = p / q if p > 0 else 0.0
        return f'{ratio:.2e}:1' if ratio >= 1000 else (f'{ratio:.0f}:1' if ratio >= 20 else f'{ratio:.2f}:1')

    fig = plt.figure(figsize=(7.0, 4.18))
    axes = [fig.add_axes([.095, .22, .285, .51]), fig.add_axes([.563, .22, .275, .51])]
    for ax in axes:
        ax.set_box_aspect(1)
        ax.tick_params(axis='both', labelsize=8, pad=2)
        ax.xaxis.label.set_size(9)
        ax.yaxis.label.set_size(9)

    # ---- Panel A: bulk prior
    ax = axes[0]
    cs_bulk = _two_class_overlay(ax, XXb, YYb, PRIORS_BULK_PLOT, 'bulk')
    ax.scatter(*bulk_pt, s=240, marker='*', c='#9ad9ea', edgecolors='black', linewidths=1.2, zorder=40)
    ax.text(.97, .95, label, transform=ax.transAxes, ha='right', va='top', fontsize=8.5, fontweight='bold',
            bbox=dict(facecolor='white', edgecolor='none', alpha=.85, pad=1.0), zorder=41)
    ax.text(0.03, 0.03,
            'Sample-specific bulk prior\n'
            f'Raw P({k1})     : {raw1:.4g}\n'
            f'Raw P({k2})     : {raw2:.4g}\n'
            f'Bulk odds {k1}/{k2}: {odds(raw1)}\n'
            f'Raw support    : {raw_gb:.4f}\n'
            f'Gate G(b)      : {gb:.4f}\n\n'
            f'Effective P({k1}): {eff1:.4f}\n'
            f'Effective P({k2}): {eff2:.4f}',
            transform=ax.transAxes, va='bottom', ha='left', fontsize=5.8, family='monospace',
            bbox=dict(boxstyle='square,pad=0.3', fc='white', ec='0.45', lw=0.8, alpha=0.96), zorder=50)
    ax.text(.00, 1.04, 'A', transform=ax.transAxes, fontsize=13, fontweight='bold', va='bottom', zorder=65)
    _two_colorbars(fig, cs_bulk, lefts=(.397, .434), bottom=.275, height=.40, bar_width=.016)

    # ---- Panel B: clumped posterior
    ax = axes[1]
    cs_clump = _two_class_overlay(ax, XXc, YYc, P_POST_GATED, 'clumped')
    ax.scatter(*clump_pt, s=240, marker='*', c='#5bc0de', edgecolors='black', linewidths=1.2, zorder=40)
    ax.text(.97, .04, label, transform=ax.transAxes, ha='right', va='bottom', fontsize=8.5, fontweight='bold',
            bbox=dict(facecolor='white', edgecolor='none', alpha=.85, pad=1.0), zorder=41)
    ax.text(0.02, 0.97,
            'Combined posterior  P(k|b*,z*)\n'
            f'{NAMES[k1]:<9s}: {pos1:.4f}\n'
            f'{NAMES[k2]:<9s}: {pos2:.4f}\n\n'
            'Clumped-only (equal prior)\n'
            f'{NAMES[k1]:<9s}: {clu1:.4f}\n'
            f'{NAMES[k2]:<9s}: {clu2:.4f}\n'
            f'LR {k1}/{k2}: {clu1 / max(clu2, 1e-15):.1f}:1',
            transform=ax.transAxes, va='top', ha='left', fontsize=6.1, family='monospace',
            bbox=dict(boxstyle='square,pad=0.3', fc='white', ec='0.45', lw=0.8, alpha=0.96), zorder=50)
    ax.text(.00, 1.04, 'B', transform=ax.transAxes, fontsize=13, fontweight='bold', va='bottom', zorder=65)
    _two_colorbars(fig, cs_clump, lefts=(.852, .889), bottom=.275, height=.40, bar_width=.016)

    save_fig('08_pointwise_diagnostic_' + sid.replace(' ', '_').replace('/', '_'), fig)


if MODEL_MODE == 'BIO_ABI' and len(OTHER):
    _pick = OTHER
    if POINTWISE_FIG_SAMPLE_ID is not None:
        _pick = OTHER.loc[OTHER['sample_id'].astype(str).eq(str(POINTWISE_FIG_SAMPLE_ID))]
        if _pick.empty:
            raise ValueError(f'POINTWISE_FIG_SAMPLE_ID {POINTWISE_FIG_SAMPLE_ID!r} not found in external samples')
    figure_pointwise_two_panel(_pick.iloc[0])

print('All outputs:', OUTPUT_DIR)
