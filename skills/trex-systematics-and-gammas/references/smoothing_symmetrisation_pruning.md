# Reference: Systematic Block Options, Smoothing, Symmetrisation & Pruning

## 1. Complete `Systematic` Block Settings

| Setting | Values / Default | Description |
| :--- | :--- | :--- |
| `Type` | `HISTO` (default), `OVERALL`, `SHAPE` | `HISTO` = `OverallSys` + `HistoSys`; `OVERALL` = normalization only; `SHAPE` = uncorrelated bin-by-bin `ShapeSys`. |
| `Title` | String | Displayed name on pull, ranking, and systematic control plots. |
| `Category` | String (e.g. `"Instrumental"`, `"Theory"`, `"ttbar"`) | Splits pull plots (`NuisPar_<Category>.pdf`) and systematic tables (`SystCategoryTables: TRUE`). |
| `SubCategory` | String (e.g. `"JES"`, `"bTag"`, `"ttbar_PS"`) | Groups NPs for Grouped Impact (`i` step). **Never** use reserved names `Gammas`, `FullSyst`, or `combine`. |
| `Samples`, `Regions`, `Exclude`, `ExcludeRegionSample` | Comma-separated strings (`region:sample` for `ExcludeRegionSample`) | Target samples and regions where the systematic is applied. |
| `NuisanceParameter` | String | Overrides the internal `RooStats` NP name (`alpha_<NuisanceParameter>`). Use identical `NuisanceParameter` across two `Systematic` blocks to correlate them 100%. |
| `StoredName` | String | Histogram base name read from/written to `Histograms/` ROOT files. Allows decorrelating or splitting a systematic in `w` without re-running `n`/`h`. |
| `IsFreeParameter` | `FALSE` (default) / `TRUE` | Uses a flat (unconstrained) prior instead of a unit Gaussian prior. |
| `OverallUp`, `OverallDown` | Float (e.g. `0.05`, `-0.05`) | Relative normalization shifts for `Type: OVERALL` (or overriding the norm part of `HISTO`). |
| `ScaleUp`, `ScaleDown` | Float (or `region:float`) | Multiplies the systematic shift by a constant factor (e.g. `0.5` to halve a two-point variation). |
| `HistoPathUp`/`Down`, `HistoFileUp`/`Down`, `HistoNameUp`/`Down`, `*SufUp`/`Down` | Strings | Path/file/name specifications for `ReadFrom: HIST`. |
| `NtuplePath(s)Up`/`Down`, `NtupleFile(s)Up`/`Down`, `NtupleName(s)Up`/`Down`, `WeightUp`/`Down`, `WeightSufUp`/`Down` | Strings | Tree/file/weight specifications for `ReadFrom: NTUP`. |
| `ReferenceSample` | Sample name (often `Type: GHOST`) | Derives relative variation w.r.t. `ReferenceSample` and applies it to `Samples`. |
| `SubtractRefSampleVar` | `FALSE` (default) / `TRUE` | Uses additive difference $(\nu_{\text{alt}} - \nu_{\text{ref}})$ instead of multiplicative ratio $(\nu_{\text{alt}} / \nu_{\text{ref}})$ when `ReferenceSample` is set. |
| `ReferencePruning` | Sample name | Forces pruning decision for this systematic to follow `ReferencePruning` sample. |
| `Symmetrisation` | `ONESIDED`, `TWOSIDED`, `ABSMEAN`, `MAXIMUM` | Symmetrisation mode applied during `n`/`h`/`b`. Omit for no symmetrisation. |
| `Smoothing` | Int (`40` standard) or `TRUE` | Enables smoothing for this systematic. |
| `SmoothingOption` | Algorithm name | Overrides `Job->SmoothingOption` for this specific systematic. |
| `DropNorm` | `"all"` or comma-separated regions/samples | Drops the normalization (`OverallSys`) component in specified regions/samples (pure shape). |
| `DropShapeIn` | `"all"` or comma-separated regions/samples | Drops the shape (`HistoSys`) component in specified regions/samples (pure normalization). |
| `KeepNormForSamples` | Comma-separated sample names | Retains the overall normalization effect on the sum of listed samples while dropping relative inter-sample migration. |
| `DummyForSamples` | Comma-separated sample names | Prevents shape or norm from acting on specific samples in a multi-sample group. |
| `Decorrelate` | `REGION`, `SAMPLE`, `SHAPEACC` | Automatically splits the NP across regions, samples, or shape vs. acceptance. |
| `CombineName` | String | Identifier used to combine multiple `Systematic` blocks during the `b` step. |
| `CombineType` | `ENVELOPE` or `STANDARDDEVIATION` | Combination rule for `CombineName` blocks (`ENVELOPE` takes max bin-by-bin excursion; `STANDARDDEVIATION` takes RMS and applies `ONESIDED`). |
| `PreSmoothing` | `TRUE` / `FALSE` | Smooths nominal and varied histograms before computing their ratio. |

---

## 2. Choosing the Right Smoothing & Symmetrisation Combination in HEP

1. **Instrumental Scale/Resolution Uncertainties (Two-sided by construction: JES, Muon scale, b-tagging eigenvectors)**:
   - Usually smooth when evaluated via internal event weights (`WeightSufUp`/`Down`) or calibrated four-momentum shifts on large MC samples.
   - If four-momentum shifts cause bin migrations with MC stat noise (e.g., JER or MET soft-term in low-stat tails), apply `Symmetrisation: TWOSIDED` and `Smoothing: 40` (`MAXVARIATION` or `COMMONTOOLSMOOTHMONOTONIC`).
2. **Two-Point Generator Comparisons (Parton Shower `Py8 vs H7`, Matrix Element `Powheg vs aMC@NLO`, `hdamp`)**:
   - Only one alternative sample exists -> **must** use `Symmetrisation: ONESIDED`.
   - Because the two samples are statistically independent, raw bin-by-bin ratios fluctuate wildly. Always enable `Smoothing: 40` (typically with `TTBARRESONANCE`, `COMMONTOOLSMOOTHMONOTONIC`, or `COMMONTOOLSMOOTHPARABOLIC`) and inspect `Systematics/<Name>/*.pdf`.
   - If the alternative sample is `AFII` while nominal is `FullSim`, **always** use `ReferenceSample: "<Nominal_AFII_GhostSample>"`.
   - In some ATLAS analyses (e.g., $t\bar{t}H$ and $t\bar{t}b\bar{b}$), two-point generator variations are additionally decorrelated between shape and normalization (`Decorrelate: SHAPEACC`) or across jet/b-tag multiplicity regions (`Decorrelate: REGION`) so that a normalization difference in a high-stat CR cannot over-constrain the kinematic shape in the SR via a single shared NP.
3. **QCD Scale ($\mu_R, \mu_F$) Variations and PDF Uncertainties**:
   - Evaluated via internal generator event weights on the *same* MC events, so bin-by-bin statistical fluctuations cancel to first order.
   - Combine the 6 off-diagonal $(\mu_R, \mu_F) \in \{(2,1), (0.5,1), (1,2), (1,0.5), (2,2), (0.5,0.5)\}$ variations using `CombineName: "Scale_Env"` + `CombineType: ENVELOPE` + `Symmetrisation: TWOSIDED`.
   - Combine PDF variations using `CombineName: "PDF_RMS"` + `CombineType: STANDARDDEVIATION`.
