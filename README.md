# Bayesian classification of methane origin from bulk and clumped isotopes

Single Python script (`Bayes_methane_isotopologues.py`) that classifies the origin of methane from bulk (δ¹³C, δD) and clumped (Δ¹³CH₃D, Δ¹²CH₂D₂) isotope compositions with a Bayesian kernel-density (KDE) classifier. 


## Method in brief
1. **Bulk prior**: class-conditional KDEs in (δ¹³C, δD) space give a bulk prior, i.e. a softmax of the class log-densities on a grid.
2. **Projection**: the bulk prior is projected into clumped space (Δ¹³CH₃D, Δ¹²CH₂D₂) with a gate-weighted kernel estimator.
3. **Clumped likelihood**: class-conditional KDEs in clumped space, with cross-validated bandwidths and continuity regularisation (see the SI).
4. **Posterior**: clumped likelihood × projected bulk prior, shown as gated maps. Individual samples are evaluated at their exact coordinates (pointwise posterior).

## Two models, one script
Set `MODEL_MODE` in the first cell:

| `MODEL_MODE` | Classes |
|---|---|
| `'TMO'` | thermogenic, microbial, oxidation |
| `'BIO_ABI'` | biotic (the three classes above, merged), abiotic |

The mode switches the classes, the training sheets, the gate parameters and the extra outputs (Tyne et al. test for `TMO`, two-panel pointwise diagnostic for `BIO_ABI`). See Table S2 of the SI.

## Usage
1. Install: `pip install numpy scipy pandas matplotlib openpyxl scikit-learn`
2. In cell 00, set `DATABASE_FILE` to the Excel database and choose `MODEL_MODE`.
3. Run the script, or run it cell by cell in Spyder. Figures are saved to `OUTPUT_DIR` as `<MODEL_MODE>_<name>.pdf/png`.


## Outputs
Figure files are numbered `01`–`08` (KDE centres, bulk prior, projected prior, clumped log-likelihoods, gated and raw posterior panels, pointwise diagnostic). Table S3 of the SI maps each file to its SI figure.

