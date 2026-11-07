# Reference: Diagnosing and Resolving HEP Fit Pathologies in TRExFitter

## 1. Quick Triage Matrix for Fit Problems

| Observed Symptom | Primary Suspects | Diagnostic Action in `TRExFitter` | Recommended Fix |
| :--- | :--- | :--- | :--- |
| **Asimov fit fails to converge** (`HESSE` invalid, `EDM` failed at 0 iterations) | Minuit starts at the exact Asimov minimum ($\theta_k = 0$), takes 0 steps, and leaves the initial unit Hessian un-updated despite NP correlations. | Check log: did `MIGRAD` perform almost 0 function calls before failing `HESSE`? | Set `SetRandomInitialNPval: 0.1` (and optionally `UseHesseBeforeMigrad: TRUE`) in `Fit`. |
| **Data fit fails with `NaN` in likelihood** | A systematic variation or negative MC weight drives expected bin yield $\nu_{ci}(\boldsymbol{\theta}) \le 0$. | Run `trex-fitter f <config>` with `DebugLevel: 3` in `Job`; inspect which region/bin prints `NaN` or negative PDF. | Ensure `CorrectNormForNegativeIntegral` / positive floor is active; smooth/prune pathological `SystLarge` variations; merge tiny negative-weight samples. |
| **Strong Over-Constraint ($\Delta\hat{\theta}_k < 0.5$)** | 1. MC stat fluctuations in two-point variation (`Py8 vs H7`, `aMC@NLO`, `JER`).<br>2. Over-correlated acceptance + shape across multiple phase-space regions. | 1. Inspect `Systematics/<NP>/` plots (`SystControlPlots: TRUE`).<br>2. Test `DropNorm: "all"`, `Decorrelate: SHAPEACC`, and `Decorrelate: REGION`. | 1. Add `Smoothing: 40` and `Symmetrisation: ONESIDED`/`TWOSIDED`.<br>2. Decorrelate acceptance vs. shape (`Decorrelate: SHAPEACC`) or across jet/b-tag regions if physics dictates. |
| **Under-Constraint ($\Delta\hat{\theta}_k > 1.05$)** | 1. Asymmetric/one-sided `Up`/`Down` templates causing a kink or wider curvature at $\hat{\theta}_k$.<br>2. Poor `HESSE` second-derivative estimate. | Add `UseMinos: "<NP>"` and `doLHscan: "<NP>"` in `Fit`; inspect `LHoodPlots/NLLscan_<NP>.pdf` and `Systematics/<NP>/`. | Symmetrise (`Symmetrisation: TWOSIDED` or `AlternativeShapeHistFactory: TRUE`), smooth templates, or report MINOS errors. |
| **Large Unexpected Pull ($|\hat{\theta}_k| > 1.0$)** | 1. Real data-MC mismodelling in a sensitive region.<br>2. Large systematic compensating for a random stat fluctuation in 1–2 bins. | Set `SystDataPlots: TRUE` in `Job` and run `d`; inspect `Systematics/<NP>/*_data.*`. Test `Decorrelate: REGION` or `Type: SHAPE`. | Rebin sparse tails, add a dedicated CR or normalization parameter if mismodelling is physical, or decorrelate across distinct kinematic regimes. |
| **Strong Anti-Correlation ($|\rho_{ij}| > 0.80$) between two NPs or POIs** | Degenerate shape/normalization effects between two parameters (e.g., Luminosity vs. inclusive cross-section, or two similar JES/b-tag/theory NPs). | Compare `Systematics/<NP1>/` and `Systematics/<NP2>/` shape ratios. | If both NPs act identically on the same single bin/region, include a CR or finer binning that separates their shapes, or re-parameterize via `Expression`. |
| **Jagged / Non-Smooth Likelihood Scan (`NLLscan_*.pdf`)** | Local minima from many tiny unpruned NPs or MC stat $\gamma$ parameters jumping at scan steps. | Run `doLHscan` with `UseNLLwithoutOffsetInLHscan: TRUE` and `FitStrategy: 2`. | Tighten `SystPruningShape` / `SystPruningNorm` (with `PruningType: BACKGROUNDREFERENCE`) and `MCstatThreshold: 0.01`. |

---

## 2. Detailed `Fit` Block Reference

| Setting | Values / Default | Description |
| :--- | :--- | :--- |
| `FitType` | `SPLUSB` (default), `BONLY`, `UNFOLDING` | Signal+background fit, background-only fit ($\mu=0$ fixed), or Profile Likelihood Unfolding. |
| `FitRegion` | `CRSR` (default), `CRONLY`, or region list | Regions included in the likelihood minimization. |
| `FitBlind` | `FALSE` (default) / `TRUE` | Force pure Asimov dataset across all fitted regions. |
| `POIAsimov` | `POI1@1.0,POI2@0.0` | Injected POI values when building the Asimov dataset. |
| `NPValues` | `alpha_NP1:1.0,alpha_NP2:-0.5` | Injected NP values for custom Asimov creation (disables Mixed Fit projection if set). |
| `NPValuesFromFitResults` | Path to `Fits/<Job>.txt` | Reads best-fit NPs from a previous fit (e.g. CR-only fit) to build a conditioned Asimov dataset. |
| `InjectGlobalObservables` | `FALSE` (default) / `TRUE` | Shifts global observables $a_k$ consistently with `NPValues` / `NPValuesFromFitResults` during injection tests. |
| `FixNPs` | `NP1:0.0,NP2:1.0` | Fixes specified NPs/NormFactors during the `f` step. |
| `SetRandomInitialNPval` | Float (e.g. `0.1`) | Randomizes initial NP values before `MIGRAD` (essential for Asimov convergence). |
| `UseHesseBeforeMigrad` | `FALSE` (default) / `TRUE` | Runs `HESSE` pre-conditioning before `MIGRAD`. |
| `FitStrategy` | `1` (default), `0`, `2` | `Minuit2` strategy (`0` = fast, `1` = standard, `2` = full Hessian at every step for difficult fits). |
| `BinnedLikelihoodOptimization` | `FALSE` (default) / `TRUE` | Enables `RooFit` `BinnedLikelihood` optimization (faster evaluation, slightly less stable covariance). |
| `MultiStageFit`, `NPCutOff` | `FALSE`/`TRUE`, Float (e.g. `0.3`) | Fits dominant NPs first (dropping $\gamma$s and bottom `NPCutOff` fraction of NPs from `NPorder.txt`), then runs full fit starting from stage-1 minimum. |
| `UseMinos` | `"all"` or comma-separated POI/NPs | Computes asymmetric profile-likelihood intervals via `MINOS`. |
| `doLHscan`, `LHscanMin`, `LHscanMax`, `LHscanSteps` | `"all"` or param list, Floats, Int (`30`) | 1D profile likelihood scan settings. |
| `do2DLHscan`, `Parallel2Dscan`, `Parallel2DscanStep` | `"pX1,pY1:pX2,pY2"`, `TRUE`/`FALSE`, Int | 2D profile likelihood contour scan and slice parallelization. |
| `doImpactscan` | `"NP1,POI1:NP2,POI2"` | Scans the conditional impact of an NP on a POI across the scan range. |
| `StatOnlyFit` | `FALSE` (default) / `TRUE` | Fixes all NPs and $\gamma$s to best-fit values and saves `Fits/<Job>_statOnly.txt`. |
| `GetGoodnessOfFit`, `SaturatedModel` | `TRUE` / `FALSE` | Computes GoF probability using the Baker-Cousins Saturated Model. |
| `FitToys`, `ToysSeed`, `ToysPseudodataNP`, `ToysPseudodataNPShift`, `ToysStatOutput` | Int, Int (`1234`), String, Float (`1.0`), `TRUE`/`FALSE` | Generates and fits $N$ toy pseudo-experiments for pull/bias/linearity validation or regularized unfolding stat errors. |
| `BlindedParameters` | Comma-separated POI/NPs | Obfuscates parameter values in hexadecimal in fit outputs and hides Minuit console logs. |
| `DataWeighted` | `FALSE` (default) / `TRUE` | Scales data and MC bin-wise by $N_{\text{data}} / \sigma_{\text{data}}^2$ when fitting weighted data or pseudodata. |
