---
name: trf
description: Shorthand alias (/trf) for the trex-fitter skill. Master workflow and architecture guide for TRExFitter, the HistFactory and xRooFit based binned profile likelihood fitting framework used in ATLAS and HEP. Use when the user invokes /trf or asks to set up a TRExFitter environment, plan an end-to-end HEP statistical analysis workflow, execute trex-fitter CLI actions (n, h, b, w, f, d, p, r, i, l, s, m, x, a), or route to specialized TRExFitter skills.
---

# TRExFitter Master Workflow & Architecture (`/trf` Alias for `/trex-fitter`)

> **Note**: This skill (`trf`) is the shorthand `/trf` alias for [`trex-fitter`](../trex-fitter/SKILL.md).

`TRExFitter` (**T**op **R**elated **Ex**perimental **Fitter**) is the primary binned profile likelihood fitting, unfolding, template morphing, and hypothesis-testing framework used across the ATLAS Collaboration and the High Energy Physics (HEP) community. Built on top of ROOT's `HistFactory`, `RooFit`, `RooStats`, and **`xRooFit`**, it constructs a simultaneous statistical model across Signal Regions (SRs), Control Regions (CRs), and Validation Regions (VRs) from plain-text `.config` files.

---

## 1. Skill Routing Table

When working on a `TRExFitter` task, load the specialized skill matching your current phase using `lookup_skill`:

| Task / Phase | Target Skill | Key Topics Covered |
| :--- | :--- | :--- |
| **Authoring `.config` files, Inputs (`HIST`/`NTUP`), Regions, `AutoBin`, Blinding, Samples, `NormFactor`/`ShapeFactor`** | `trex-config-and-inputs` | `Job`, `Region`, `Sample`, `GHOST` samples, `AutoBin` (`TransfoD`, `TransfoF`, `TransfoJ`), blinding (`BlindingThreshold`, `BlindSRs`, `DataType: ASIMOV`), `NormFactor` (`Expression`), `ShapeFactor`, `FastFrames` integration, `hupdate.exe`, config validation script. |
| **Systematics (`HISTO`/`OVERALL`/`SHAPE`), Smoothing, Symmetrisation, Pruning, Generator 2-Point Uncertainties, Gammas** | `trex-systematics-and-gammas` | `ONESIDED`/`TWOSIDED`/`ABSMEAN`/`MAXIMUM`, `AlternativeShapeHistFactory`, smoothing (`MAXVARIATION`, `TTBARRESONANCE`, `COMMONTOOLSMOOTHMONOTONIC`, `COMMONTOOLSMOOTHPARABOLIC`), `ReferenceSample`, `CombineName: ENVELOPE\|STDDEV\|HESSIAN`, `Decorrelate`, `DropNorm`/`DropShapeIn`, `SeparateGammas`, negative bin cleaning. |
| **Running Fits (`SPLUSB`/`BONLY`/`CRSR`/`CRONLY`), Diagnosing Pulls, Over/Under-Constraints, Asimov Convergence, Rankings & Impacts** | `trex-fit-and-diagnostics` | Fixing Asimov unit-Hessian non-convergence (`SetRandomInitialNPval`, `UseHesseBeforeMigrad`), diagnosing constraints $< 1$ or $> 1$, spurious pulls, large correlations, `UseMinos`, `doLHscan`/`do2DLHscan`, `GetGoodnessOfFit` (`SaturatedModel`), `r` (NP ranking) and `i` (grouped impact), automated fit diagnostic script. |
| **Profile Likelihood Unfolding (`UNFOLDING`) & Continuous Template Morphing (`Morphing`)** | `trex-unfolding-and-morphing` | `Unfolding`, `TruthSample`, `UnfoldingSample`, `UnfoldingSystematic`, migration/efficiency/acceptance folding, Tikhonov regularization (`RegularizationType`, `Tau`), `Morphing` (`LINEAR`, `SMOOTHLINEAR`, `SQUAREROOT`), `PropagateSystsForMorphing`, closure/linearity tests. |
| **Exclusion Limits ($\text{CL}_s$), Discovery Significance ($p_0$), `MultiFit` Combinations & HEPData/uhepp Exports** | `trex-limits-significance-multifit` | `Limit` (`ASYMPTOTIC` vs `TOYS`, `SignalInjection`), `Significance`, `MultiFit` (`Combine: TRUE`, `CompareLimits`, `ComparePOI`, `ComparePulls`, channel decorrelation), `HEPDataFormat`, `UheppFormat`, `UseATLASRounding`. |

For the exact mathematical formulation of the binned `HistFactory` likelihood $L(\bm{\mu}, \bm{\theta}, \bm{\gamma})$ and interpolation codes (`InterpCode` 0–4) implemented by `TRExFitter`, read `references/histfactory_statistical_model.md`.

---

## 2. Environment Setup & Installation

### 2.1 CVMFS (`StatAnalysis` Release — Recommended on lxplus / ATLAS clusters)
`TRExFitter` relies on the ATLAS `StatAnalysis` LCG release (which bundles ROOT, `RooFit`, and `xRooFit`):
```bash
setupATLAS
asetup StatAnalysis,0.8.0
source build/setup.sh
```
When cloning from GitLab (`https://gitlab.cern.ch/TRExStats/TRExFitter.git`), **always** initialize submodules (`xroofit`, `SystematicSmoothingTool`, `UnfoldingCode`, `Blinder`, `yaml-cpp`):
```bash
git clone --recursive https://gitlab.cern.ch/TRExStats/TRExFitter.git
cd TRExFitter
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### 2.2 Containerized Execution (Apptainer / Singularity / Docker)
When running outside CERN `lxplus` or without CVMFS:
- Official container images are published to the CERN GitLab registry: `gitlab-registry.cern.ch/trexstats/trexfitter:latest`.
- With Apptainer/Singularity:
  ```bash
  apptainer exec docker://gitlab-registry.cern.ch/trexstats/trexfitter:latest trex-fitter <actions> <config_file>
  ```

---

## 3. Command-Line Execution & Action Steps (`trex-fitter`)

The CLI syntax is:
```bash
trex-fitter <action_letters> <config_file> ["<option1>=<val1>:<option2>=<val2>"]
```
Action letters can be chained in a single invocation (e.g., `trex-fitter hwfpr my_fit.config`).

### Complete Action Step Reference

| Action Letter | Step Name | Inputs Required | Outputs Produced (`<JobName>/`) | When to Run |
| :---: | :--- | :--- | :--- | :--- |
| **`u`** | **Prepare Unfolding** | Response/migration matrices & truth distributions | Folded per-truth-bin histograms in `Unfolding/` | **Before** `n`/`h`/`b` when `FitType: UNFOLDING`. |
| **`n`** | **Read Ntuples (`NTUP`)** | ROOT `TTree` ntuples (`NtuplePaths`) | Intermediate histogram files (`Histograms/<JobName>_*histos.root`) | When `ReadFrom: NTUP` (applying cuts, weights, formulas). |
| **`h`** | **Read Histograms (`HIST`)** | Pre-produced ROOT histograms (e.g., from `FastFrames`) | `<JobName>/Histograms/*_histos.root` | When `ReadFrom: HIST` (significantly faster than `n`). |
| **`b`** | **Binning & Systematics Processing** | Raw histograms from `n` or `h` (`*_histos.root`) | Rebinned, smoothed, symmetrised, pruned histograms + `Systematics/` red/blue control plots | **Mandatory** whenever binning (`Rebin`/`AutoBin`), smoothing, symmetrisation, or pruning changes; or when running directly from pre-made `Histograms/` without re-running `n`/`h`. |
| **`w`** | **Workspace Creation** | Processed histograms (`b` step, or automatically triggers `b` after `n`/`h`) | `RooFit` / `xRooFit` workspaces (`RooStats/<JobName>_combined_*.root`) & pre-fit yield tables | Before fitting (`f`), limits (`l`), significance (`s`), or likelihood scans (`x`). |
| **`f`** | **Profile Likelihood Fit** | Workspace (`RooStats/`) | Fit results (`Fits/<JobName>.txt`, `.root`), NP pull plots (`NuisPar.pdf`), correlation matrix (`CorrMatrix.pdf`) | To extract best-fit POIs $\hat{\mu}$, NP pulls $(\hat{\theta}-\theta_0)/\Delta\theta_0$, constraints, and covariance matrices. |
| **`d`** | **Draw Pre-Fit Plots** | Processed histograms (`Histograms/`) | Pre-fit Data/MC stack plots (`Plots/*_prefit.pdf`), `Tables/*_prefit.tex` | To verify pre-fit modelling, blinding masks, and yield tables. |
| **`p`** | **Draw Post-Fit Plots** | Workspace (`RooStats/`) + Fit results (`Fits/`) | Post-fit Data/MC stack plots (`Plots/*_postfit.pdf`), `Tables/*_postfit.tex`, `Summary.pdf`, unfolded plots | After `f` to inspect post-fit agreement and constrained uncertainty bands. |
| **`r`** | **Nuisance Parameter Ranking** | Workspace (`RooStats/`) + Fit results (`Fits/`) | Pre-fit & post-fit impact plots (`Ranking_*.pdf`, `Ranking_*.yaml`) | To compute $\Delta\hat{\mu}$ impact of each NP (supports parallel execution via `Ranking=<NP_name_or_index>`). |
| **`i`** | **Grouped Impact Breakdown** | Workspace (`RooStats/`) + Fit results (`Fits/`) | Grouped systematic covariance breakdown (`Fits/GroupedImpact*.txt`, `.tex`) | To decompose $\sigma_{\mu}^2$ by `Category` / `SubCategory` (fixing groups of NPs at $\hat{\theta}$ and subtracting in quadrature). |
| **`l`** | **Exclusion Limits** | Workspace (`RooStats/`) | 95% $\text{CL}_s$ upper limits (`Limits/Asymptotics/*.root`, Brazil-band plots) | For BSM searches or upper limit setting (`ASYMPTOTIC` or `TOYS`). |
| **`s`** | **Discovery Significance** | Workspace (`RooStats/`) | $p_0$-value and $Z$-score (`Significance/`) | To quantify excess over the background-only ($\mu=0$) hypothesis. |
| **`m`** | **Multi-Fit** | Multiple individual `.config` files & their workspaces/fit outputs | Combined workspaces, joint fits, POI/pull/limit comparison plots | When running a `MultiFit` config (`trex-fitter mwf multi.config` or `trex-fitter mp multi.config`). |
| **`x`** | **Likelihood Scan** | Workspace (`RooStats/`) | 1D/2D $-2\Delta\ln L$ curves (`LHoodPlots/`) | Standalone likelihood scan execution without re-running full `f`. |
| **`a`** | **Alternative / Toys** | Workspace (`RooStats/`) | Pseudo-experiment toy distributions (`Toys/`) | Running standalone toy studies and frequentist coverage checks. |

### Command-Line Overrides
Pass colon-separated `Key=Value` overrides as the third argument to avoid duplicating `.config` files during batch submissions or diagnostic checks:
- `Regions=CR_ttbar,SR_boosted`: Restrict regions included in the run.
- `Samples=ttbar,Wjets`: Restrict samples processed in `n`/`h`.
- `Systematics=JES_Flavor_Comp`: Process only specific systematics.
- `Exclude=JER_*`: Exclude matching items (wildcards supported).
- `Ranking=1` (or `Ranking=ATLAS_JES_PU_Rho`): Run the ranking fit for a single NP (1-indexed) on a batch worker node, then run `Ranking=plot` once all jobs finish to assemble the Brazil-style ranking plot.
- `GroupedImpact="CategoryName"` (then `GroupedImpact="combine"`): Parallelize grouped impact jobs across categories.
- `FitBlind=TRUE` or `FitBlind=FALSE`: Toggle Asimov vs. real data fitting on the fly.
- `Suffix=_decorr_test`: Append a custom suffix to output plots/tables/fit files so diagnostic tests do not overwrite baseline results.

---

## 4. Standard Staged Analysis Workflow in HEP

Never jump straight to an unblinded Signal + Control Region fit (`FitRegion: CRSR`, `FitBlind: FALSE`). Follow the strict 5-stage validation protocol used in ATLAS analyses:

1. **Stage 1 — Pre-Fit & Systematic Input Validation (`h`/`n` $\to$ `b` $\to$ `d`)**:
   - Inspect pre-fit yield tables (`Tables/`) and plots (`Plots/`).
   - Inspect `Systematics/<SystName>/*.pdf` (red/blue up/down variations vs. nominal, both raw dashed and smoothed solid lines) and `Pruning.pdf` before building the workspace.
   - Check that no bin has zero or negative total background prediction and that MC statistical uncertainty (`gamma`) per bin is $\lesssim 10\text{--}15\%$.
2. **Stage 2 — Pure Asimov Fit (`w` $\to$ `f` $\to$ `r` with `FitBlind: TRUE`)**:
   - Fit the Asimov dataset where by construction all NP pulls must be $0.00 \pm 0.001$ and the POI matches the injected Asimov value (`POIAsimov: 1.0`).
   - Enable `SetRandomInitialNPval: 0.1` and `UseHesseBeforeMigrad: TRUE` so `Minuit2` steps away from the initial point and computes the true Hessian covariance matrix.
   - Inspect **pre-fit vs. post-fit NP constraints** ($\Delta\hat{\theta}/\Delta\theta_0$). Any NP constrained to $\ll 0.5\text{--}0.7$ in an Asimov fit indicates an overly aggressive variation (often an unsmoothed two-point generator systematic or an artificial shape variation across unphysical bin edges).
3. **Stage 3 — Unblinded Control Region-Only Fit (`FitRegion: CRONLY`, `FitBlind: FALSE`, `FitType: BONLY`)**:
   - Fit real data in Control Regions only (`CRONLY`), keeping SRs completely excluded from the likelihood.
   - Propagate the CR-only post-fit parameters to Validation Regions (`VR`s) and blinded SRs (`p` step) to verify background normalization and shape extrapolation.
   - Run the Saturated Model Goodness-of-Fit (`GetGoodnessOfFit: TRUE`) in CRs and VRs.
4. **Stage 4 — Hybrid / Conditioned ("Mixed") Fit (`FitRegion: CRSR`, `BlindSRs: TRUE` or `DataType: ASIMOV` in SRs, `DataType: DATA` in CRs)**:
   - Fits real data in CRs while using a CR-conditioned Asimov dataset in SRs (`TRExFitter` automatically performs a two-step fit: first fitting CR data to find $\hat{\hat{\bm{\theta}}}_{\text{CR}}$, then generating the SR Asimov dataset at those post-fit background NP values).
   - Run full NP rankings (`r`) and grouped impacts (`i`) on this mixed dataset for pre-unblinding approval.
5. **Stage 5 — Unblinding (`FitRegion: CRSR`, `FitBlind: FALSE`)**:
   - Unblind SRs, run `f`, `p`, `r`, `i`, `l`/`s`, and compare post-fit pulls and constraints against the Stage 4 Mixed Fit using `MultiFit` (`ComparePulls: TRUE`).
