---
name: trex-fit-and-diagnostics
description: Configure, execute, and diagnose profile likelihood fits in TRExFitter. Covers Fit block settings (SPLUSB, BONLY, CRSR, CRONLY, Asimov and mixed fits), diagnosing and resolving HEP fit pathologies (Asimov non-convergence from unit Hessian, over-constraints < 1, under-constraints > 1, unexpected NP pulls, large correlations, non-smooth likelihood scans), MINOS and 1D/2D likelihood scans, Saturated Model Goodness-of-Fit, NP Ranking (r step), and Grouped Impact breakdown (i step).
---

# Profile Likelihood Fitting & Diagnostics in TRExFitter

In ATLAS analyses and HEP PhD theses, a profile likelihood fit is never treated as a black box. Before unblinding signal regions, analysts systematically validate the fit model through a sequence of diagnostic tests:
1. **Pre-fit & Asimov Fit (`FitBlind: TRUE`)**: Verify closure ($\hat{\mu} = \mu_{\text{inj}}$, $\hat{\theta}_k = 0$), inspect expected NP constraints ($\Delta\hat{\theta}_k$), correlations, and ranking.
2. **Background-Only / CR-Only Fit (`FitType: BONLY`, `FitRegion: CRONLY`)**: Fit real data in control regions only to validate background normalizations, NP pulls, and post-fit extrapolation into validation regions (`p` step).
3. **Mixed / Hybrid Fit (`DataType: DATA` in CRs, `DataType: ASIMOV` in SRs)**: Propagate data-driven CR pulls and constraints into SRs without looking at SR data.
4. **Full Unblinded Fit (`FitType: SPLUSB`, `FitRegion: CRSR`, `FitBlind: FALSE`)**: Extract final POIs, pulls, ranking (`r`), grouped impact (`i`), and Goodness-of-Fit.

For an in-depth guide to diagnosing and fixing every common HEP fit pathology, consult [`references/hep_fit_pathologies_and_remedies.md`](references/hep_fit_pathologies_and_remedies.md).
To automatically inspect a `TRExFitter` fit result (`Fits/<JobName>.txt` and `Fits/NPRanking*.txt`) for pulls, constraints, and pathologies, run:
```bash
python3 scripts/diagnose_trex_fit.py path/to/JobDir
```

---

## 1. Essential `Fit` Block Configuration

```yaml
Fit: "myFit"
  FitType: SPLUSB                  % SPLUSB (default), BONLY, or UNFOLDING
  FitRegion: CRSR                  % CRSR (default), CRONLY, or comma-separated region list
  FitBlind: FALSE                  % TRUE = pure Asimov fit across all regions; FALSE = use Region->DataType
  POIAsimov: "mu_XS_ttH"@1.0       % Injected POI value(s) in Asimov dataset (supports comma-separated POI1@1.0,POI2@1.0)
  SetRandomInitialNPval: 0.1       % Crucial for Asimov fit convergence! Perturbs starting NPs away from minimum
  SetRandomInitialNPvalSeed: 12345
  NumCPU: 4                        % Parallel likelihood evaluation in RooFit / xRooFit
  GetGoodnessOfFit: TRUE           % Evaluate GoF p-value
  SaturatedModel: TRUE             % Use Baker-Cousins Saturated Model for GoF (must be set during 'w' and 'f')
  UseMinos: "mu_XS_ttH"            % Compute exact profile likelihood asymmetric errors for POI(s) and key NPs
  doLHscan: "mu_XS_ttH"            % Produce 1D -2 Delta ln L scan in LHoodPlots/
```

---

## 2. The 6 Classic HEP Fit Pathologies & How to Solve Them in TRExFitter

### Pathology 1: Fit Fails to Converge on Asimov Data!
- **Symptom**: `Minuit2` / `MIGRAD` reports failed covariance matrix (`HESSE` not positive-definite or `EDM > 0.001`) on an Asimov dataset (`FitBlind: TRUE`), even though the model is smooth.
- **Physics / Numerical Cause**: By construction, an Asimov dataset is generated at $\theta_k = 0$, which is also the exact initial starting point of `Minuit2`. Because the fit starts *at* the exact minimum, `MIGRAD` takes 0 steps and never updates its initial internal approximation of the Hessian matrix (which starts as the identity matrix $\mathbf{I}$, assuming zero correlation between parameters). When NPs are correlated, the true Hessian is non-diagonal, causing the convergence check to fail!
- **TRExFitter Solution**:
  ```yaml
  SetRandomInitialNPval: 0.1
  UseHesseBeforeMigrad: TRUE
  ```
  Perturbing the initial NP values by $\sim 0.1\sigma$ forces `MIGRAD` to iterate back to $\theta_k = 0$ and build an accurate Hessian matrix along the trajectory.

### Pathology 2: Fit Fails to Converge on Real Data (or Toys)
- **Symptom**: `MIGRAD` fails after 3 automatic retry attempts (with increased precision), or prints `NaN` warnings.
- **Diagnostic & Remedy Checklist**:
  1. Set `DebugLevel: 3` in `Job` and search the log for `NaN` or negative PDF evaluations—this points to a specific region/bin where a systematic variation drives the total predicted yield $\nu_{ci}(\boldsymbol{\theta}) \le 0$.
  2. Test `MCstatThreshold: NONE` temporarily (for debugging only, never for publication!) to check if a tiny background sample with huge negative/positive MC weights is destabilizing a bin's $\gamma_{ci}$ parameter. If so, merge minor backgrounds or use `SeparateGammas: TRUE`.
  3. Increase pruning thresholds (`SystPruningShape: 0.01`, `SystPruningNorm: 0.005`, `PruningType: BACKGROUNDREFERENCE`)—hundreds of near-zero NPs create flat directions in the likelihood.
  4. For very complex workspaces ($>500$ NPs), enable `MultiStageFit: TRUE` and `NPCutOff: 0.3` in `Fit` to fit dominant parameters first before releasing small NPs and $\gamma$s.

### Pathology 3: Severe Over-Constraint ($\Delta\hat{\theta}_k \ll 1.0$, e.g. $< 0.5$)
- **Symptom**: In `NuisPar.pdf` or `Fits/<JobName>.txt`, a theoretical or instrumental NP has post-fit error bars much smaller than $\pm 1\sigma$.
- **Why It Happens & How to Diagnose**:
  - **Fake constraint (Bad)**: A two-point systematic (`Pythia8 vs Herwig7`, `Powheg vs aMC@NLO`, `JER`) has unsmoothed MC statistical fluctuations in a few bins, giving the fit artificial discriminating power against that NP.
    - *Fix*: Inspect `<JobName>/Systematics/<NP>/` plots. Enable `Smoothing: 40` (`TTBARRESONANCE` or `COMMONTOOLSMOOTHMONOTONIC`), `Symmetrisation: ONESIDED`/`TWOSIDED`, or rebin sparse tails.
  - **Over-aggressive correlation assumptions (Physics Modeling Issue)**: A single NP correlates overall normalization across multiple jet/b-tag regions AND bin-by-bin shape (`Type: HISTO`). High statistics in a control region (e.g., $\ge 4\text{j}, 2\text{b}$) constrains the overall acceptance difference between two generators and forces that tight constraint onto the signal region ($\ge 6\text{j}, \ge 4\text{b}$) where the theoretical uncertainty should not be reduced!
    - *Diagnostic in TRExFitter*:
      1. Add `DropNorm: "all"` (or `Decorrelate: SHAPEACC`) on the systematic to test whether the constraint comes from normalization (`OverallSys`) or shape (`HistoSys`).
      2. Add `Decorrelate: REGION` (or `Decorrelate: SAMPLE`) to identify which region or sample drives the constraint.
      3. Check if a missing nuisance parameter (e.g., heavy-flavour fraction normalization or luminosity) is forcing a single NP to absorb all degrees of freedom; adding physically motivated NPs/NormFactors introduces correlations that relax artificial constraints.

### Pathology 4: Under-Constraint ($\Delta\hat{\theta}_k > 1.0$, e.g. $1.15$)
- **Symptom**: Post-fit uncertainty on a Gaussian-constrained NP exceeds its pre-fit $\pm 1.0$ prior width!
- **Why It Happens**:
  1. **Asymmetric / Non-Parabolic Likelihood**: When the `Up` and `Down` variations of a systematic have different magnitudes (or same-sign shifts in some bins), the profile likelihood $-2\Delta\ln\mathcal{L}(\theta_k)$ is kinked or wider than a parabola near $\hat{\theta}_k$, so the local 2nd-derivative (`HESSE`) error exceeds $1.0$.
  2. **Imprecise Hessian Matrix**: Numerical inaccuracy in finite-difference second derivatives.
- **TRExFitter Solution**:
  - Run `doLHscan: "<NP_name>"` and `UseMinos: "<NP_name>"` in `Fit`.
  - Inspect `LHoodPlots/NLLscan_<NP_name>.pdf`. If the curve has a kink at $\theta = 0$, check `Systematics/<NP_name>/` for one-sided/asymmetric templates and enable `Symmetrisation: TWOSIDED` (or `AlternativeShapeHistFactory: TRUE`).

### Pathology 5: Unexpected / Large NP Pulls ($|\hat{\theta}_k| > 1.0$)
- **Symptom**: An NP is pulled significantly away from $0$ in a data fit (or even when data and pre-fit MC appear consistent in most bins).
- **Why It Happens & How to Diagnose**:
  1. **Enable `SystDataPlots: TRUE` in `Job`**: This overlays the pre-fit $\pm 1\sigma$ systematic shape directly against the `Data / Nominal MC` ratio in every region! You can immediately see which bins of data are pulling the NP.
  2. **Large-uncertainty leverage**: If a systematic has a huge pre-fit variation (e.g. $40\%$) in a low-purity bin, a tiny $0.2\sigma$ penalty in the Gaussian constraint $-2\ln f(\theta_k) = \theta_k^2 = 0.04$ allows the fit to change the bin yield by $8\%$ to perfectly match a random statistical fluctuation in data.
  3. **Correlated Shape Pull across Regions (`Type: HISTO` vs `Type: SHAPE`)**: As shown in the `TRExFitter` model studies (`docs/model_studies/decorrelation.md`), if a single `HISTO` NP is pulled to fix a mismodelling slope across 10 bins, switching it temporarily to `Type: SHAPE` (or `Decorrelate: REGION`) tests whether the pull is a coherent regional mismodelling vs. an isolated bin outlier.

### Pathology 6: Non-Smooth / Double-Minimum Profile Likelihood Scans
- **Symptom**: `LHoodPlots/NLLscan_<param>.pdf` shows jagged steps, local minima, or discontinuities.
- **Remedies**:
  - Ensure `UseNLLwithoutOffsetInLHscan: TRUE` (or test `FALSE` if numerical precision loss occurs in very large simultaneous fits).
  - Increase `FitStrategy: 2` in `Fit` for higher-precision `HESSE` evaluations during the scan.
  - Increase `SystPruningShape` / `SystPruningNorm` to eliminate tiny flat-direction systematics that jump between local minima at each scan step.

---

## 3. Goodness-of-Fit: Saturated Model vs. $\chi^2$

- **`SaturatedModel: TRUE` + `GetGoodnessOfFit: TRUE` (Recommended in HEP)**:
  Constructs the Baker-Cousins **Saturated Model** (equivalent to adding one free normalization parameter per bin so $\nu_{ci}^{\text{sat}} = n_{ci}$) during `w`, and evaluates the likelihood ratio test statistic:
  $$q_{\text{GoF}} = -2\ln\frac{\mathcal{L}(\hat{\boldsymbol{\mu}}, \hat{\boldsymbol{\theta}}, \hat{\boldsymbol{\gamma}})}{\mathcal{L}_{\text{saturated}}}$$
  with $\text{ndf} = N_{\text{bins}}^{\text{fitted}} - N_{\text{free params}}$ (where $N_{\text{free params}}$ counts unconstrained `NormFactor`s and `ShapeFactor`s). Unlike naive Pearson $\chi^2$, the Saturated Model exactly respects Poisson statistics in low-count bins and accounts for all profiled nuisance parameters.
- **Plot-level $\chi^2$ (`GetChi2: TRUE` and `PlotOptions: "CHI2"`)**:
  Computes an extended $\chi^2$ using the full post-fit covariance matrix on each individual region's plot during `d` and `p`.

---

## 4. Ranking (`r`) and Grouped Impact (`i`) Workflows

### A. Nuisance Parameter Ranking (`r` step)
Produces the standard ATLAS NP ranking plot showing pre-fit/post-fit pulls (points/error bars, bottom axis) and pre-fit/post-fit impact $\Delta\hat{\mu}$ on the POI (hatched/solid bars, top axis):
```bash
# Sequential (for small workspaces)
trex-fitter r myFit.config

# Parallelized across batch jobs (recommended for production fits)
trex-fitter r myFit.config "Ranking=0"
trex-fitter r myFit.config "Ranking=1"
# ... (or by NP name: Ranking=JES_Flavor_Comp)
# Finally merge and plot:
trex-fitter r myFit.config "Ranking=plot"
```
- Note: Recent `TRExFitter` / `xRooFit` versions also print a **fast covariance-based ranking** directly during the `f` step using the Hessian correlation matrix ($\Delta\hat{\mu}_k \approx \rho_{\mu, \theta_k} \sigma_\mu$), which is instantaneous and provides an immediate check against the exact refit ranking (`r` step).

### B. Grouped Impact Breakdown (`i` step — Uncertainty Table in ATLAS Papers)
Every ATLAS measurement paper includes a table breaking down $\sigma(\mu)$ into categories (`Data Stat`, `Full Syst`, `MC Stat (Gammas)`, `Jet/MET`, `b-tagging`, `t\bar{t} Modelling`, `Luminosity`, etc.).
1. Assign every `Systematic` and `NormFactor` a `SubCategory: "<GroupName>"` (never use the reserved strings `Gammas`, `FullSyst`, or `combine`).
2. Run the nominal fit `f`, then run `i`:
   ```bash
   # Run all SubCategory groups sequentially:
   trex-fitter i myFit.config

   # Or parallelize per group on a batch cluster:
   trex-fitter i myFit.config "GroupedImpact=Gammas"
   trex-fitter i myFit.config "GroupedImpact=FullSyst"
   trex-fitter i myFit.config "GroupedImpact=ttbar_Modelling"
   trex-fitter i myFit.config "GroupedImpact=JES"
   # Combine into Fits/GroupedImpact*.txt and tables:
   trex-fitter i myFit.config "GroupedImpact=combine"
   ```
- Note: Because NPs across categories are correlated in the profile likelihood fit, the sum in quadrature of individual `SubCategory` impacts $\sum_G (\Delta\mu_G)^2$ **does not equal** $\sigma_{\text{syst}}^2$ (`FullSyst`), which should always be noted in publication tables!
- **Extended Covariance Matrices (`DoExtendedCovariances: TRUE` in `Job`)**:
  For multi-POI or differential/unfolding measurements, running `f`, then `f "StatOnlyFit=TRUE"`, then `r` with `DoExtendedCovariances: TRUE` produces per-systematic covariance matrices in `Covariances/` (and HEPData format if `HEPDataFormat: TRUE`).
