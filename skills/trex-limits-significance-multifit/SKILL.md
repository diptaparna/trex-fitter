---
name: trex-limits-significance-multifit
description: Compute 95% CLs exclusion upper limits, discovery significance (p0 and Z-score), and MultiFit statistical combinations or comparisons in TRExFitter, and export HEPData, uhepp, and publication-ready LaTeX tables. Use when configuring Limit, Significance, or MultiFit blocks, running asymptotic vs toy-based hypothesis tests (l, s, m steps), injecting signal, or combining orthogonal analysis channels.
---

# TRExFitter Exclusion Limits, Discovery Significance & MultiFit Combinations

This skill covers hypothesis testing (`l` and `s` steps), multi-channel combinations and comparisons (`m` step via `MultiFit`), and publication/preservation exports (`HEPDataFormat`, `UheppFormat`, `UseATLASRounding`) in `TRExFitter`.

For complete block option tables and copy-ready `Limit`, `Significance`, and `MultiFit` configurations, read `references/multifit_limits_significance_reference.md`.

---

## 1. Exclusion Upper Limits (`l` Step, `Limit` Block)

In BSM searches and rare-process analyses, `TRExFitter` computes 95% Confidence Level ($\text{CL}_s$) upper limits on the signal strength $\mu$ using the one-sided profile likelihood test statistic $\tilde{q}_\mu$ (Cowan, Cranmer, Gross, Vitells, [arXiv:1007.1727](https://arxiv.org/abs/1007.1727)):

$$\tilde{q}_\mu = \begin{cases} -2\ln\frac{L(\mu, \hat{\hat{\bm{\theta}}}(\mu))}{L(0, \hat{\hat{\bm{\theta}}}(0))} & \text{if } \hat{\mu} < 0, \\[6pt] -2\ln\frac{L(\mu, \hat{\hat{\bm{\theta}}}(\mu))}{L(\hat{\mu}, \hat{\bm{\theta}})} & \text{if } 0 \le \hat{\mu} \le \mu, \\[6pt] 0 & \text{if } \hat{\mu} > \mu, \end{cases} \qquad \text{CL}_s(\mu) = \frac{p_{\mu}}{1 - p_b} \le 1 - \text{CL}$$

### 1.1 Key `Limit` Block Configurations

- **`LimitType: ASYMPTOTIC | TOYS`**:
  - `ASYMPTOTIC` (default): Uses the Wald / Asimov approximation via `xRooFit` to compute observed $\mu_{\text{obs}}^{95\%}$, median expected $\mu_{\text{exp}}^{95\%}$ under $\mu=0$, and the $\pm 1\sigma$ (green) and $\pm 2\sigma$ (yellow) Brazil-band quantiles instantly.
  - `TOYS`: Generates full frequentist/hybrid pseudo-experiments (`SplusBToys: <int>`, `BonlyToys: <int>`, scanned across `ScanSteps: <int>` points in `[ScanMin, ScanMax]`).
  - **When `TOYS` is mandatory in ATLAS**: Whenever the high-sensitivity Signal Region bins have very low expected counts ($N_{\text{bkg}} \lesssim 2\text{--}5$ events) where the asymptotic $\chi^2$ approximation breaks down and asymptotic limits are typically 10–30% too aggressive (optimistic).
- **Blinding & Background Conditioning (`LimitBlind` & `POIAsimov`)**:
  - `LimitBlind: TRUE`: Masks the observed limit and computes the expected limit from an Asimov dataset.
  - If Control Regions are unblinded (`DataType: DATA`) while Signal Regions are blinded (`DataType: ASIMOV` or `BlindSRs: TRUE`), `TRExFitter` first fits the CR data under $\mu=0$ to extract data-constrained background nuisance parameters $\hat{\hat{\bm{\theta}}}_{\text{CR}}(0)$ and builds the SR Asimov dataset at those post-fit NP values (pre-unblinding **Mixed Expected Limit**).
  - `POIAsimov: <float>`: Sets the signal strength used when generating the Asimov dataset for the expected limit (default `0` for background-only expected limits).
- **Signal Injection Tests (`SignalInjection`)**:
  - `SignalInjection: TRUE` and `SignalInjectionValue: <float>` (e.g., `1.0`): Generates an S+B Asimov dataset with injected signal $\mu_{\text{inj}}$ and computes the expected upper limit if a signal of strength $\mu_{\text{inj}}$ were present in data.
- **2D Mass / Coupling Limit Contours**:
  - Use `ParamName: "<param>"` and `ParamValue: <float>` inside each single-point `.config`'s `Limit` block, then combine all mass points via `MultiFit` with `CompareLimits: TRUE` to produce 1D Brazil-band limit plots as a function of mass or coupling.

---

## 2. Discovery Significance (`s` Step, `Significance` Block)

Tests the compatibility of the observed data with the background-only hypothesis ($\mu = 0$) against the positive-signal alternative ($\mu > 0$) using the uncapped test statistic $q_0$:

$$q_0 = \begin{cases} -2\ln\frac{L(0, \hat{\hat{\bm{\theta}}}(0))}{L(\hat{\mu}, \hat{\bm{\theta}})} & \text{if } \hat{\mu} \ge 0, \\[6pt] 0 & \text{if } \hat{\mu} < 0, \end{cases} \qquad Z = \Phi^{-1}(1 - p_0) \approx \sqrt{q_0}$$

### 2.1 Key `Significance` Block Configurations

- **`SignificanceType: ASYMPTOTIC | TOYS`**:
  - `ASYMPTOTIC` (default): Evaluates observed and expected $p_0$ and significance $Z = \sqrt{q_0}$ using the Asimov dataset generated at `POIAsimov` (default `1.0`).
  - `TOYS`: Throws `BonlyToys` background-only toys to sample the tail of $f(q_0 \mid 0)$ directly.
- **`SignificanceBlind: TRUE | FALSE`**:
  - When `TRUE`, only the expected significance on the S+B Asimov dataset (`POIAsimov: 1.0`) is reported.
- **`IncludeStatOnly: TRUE`**:
  - Computes both the full-systematics significance and the stat-only significance (with all nuisance parameters fixed to their conditional MLEs).

---

## 3. Multi-Channel Combinations & Comparisons (`m` Step, `MultiFit`)

When an analysis comprises multiple orthogonal channels (e.g., `1-lepton`, `2-lepton`, `hadronic`, or multiple years/datasets) or when comparing several fit configurations (e.g., Asimov vs. Data, Run 2 vs. Run 3, or a grid of BSM mass points), create a **multi-fit configuration file** (validated against `multiFitSchema.config`) and execute the **`m` step**:

```bash
# Run MultiFit combination/comparison across individual Job configs
trex-fitter mwf my_multifit.config      # Combine workspaces (w) and run combined fit (f)
trex-fitter ml  my_multifit.config      # Compare or combine limits across configs
trex-fitter mp  my_multifit.config      # Produce summary comparison plots (POI, pulls, rankings)
```

### 3.1 Two Modes of `MultiFit` Operation

1. **Comparison Mode (`Combine: FALSE`, default)**:
   - Reads the already-executed output directories of multiple individual `Job` `.config` files and overlays their results onto unified summary plots without running a joint fit:
     - `ComparePOI: TRUE`: Produces a summary forest plot comparing best-fit $\hat{\mu} \pm \Delta\mu_{\text{tot}} (\pm \Delta\mu_{\text{stat}} \pm \Delta\mu_{\text{syst}})$ across channels and against the combined result.
     - `ComparePulls: TRUE`: Overlays nuisance parameter pulls $\hat{\theta}_k \pm \Delta\hat{\theta}_k$ from multiple fits (e.g., CR-only fit vs. CR+SR fit, or Channel A vs. Channel B vs. Combined) grouped by `Category` (`SysCategory`).
     - `CompareLimits: TRUE`: Builds the 1D Brazil-band upper limit curve across mass/parameter points (`ParamValue` in each sub-config) or compares per-channel limits in a bar chart.
     - `CompareUnfolded: TRUE`: Compares unfolded differential cross-sections from different setups.
2. **Simultaneous Combination Mode (`Combine: TRUE`)**:
   - Merges the RooFit / `xRooFit` workspaces (`ws`) of all listed `ConfigFile` jobs into a single joint workspace (`trex-fitter mw`) and performs a simultaneous profile likelihood fit (`trex-fitter mf`), limit (`ml`), significance (`ms`), or ranking (`mr`).
   - **Correlation Rule in Combinations**:
     - Any nuisance parameter (`Systematic`, `NormFactor`, or shared `SeparateGammas` group) with the **exact same NP name** in two `ConfigFile` workspaces is treated as **100% correlated** in the combined likelihood!
     - Any NP with a distinct name is treated as **uncorrelated**.
     - To control correlations across channels without editing every sub-config, use:
       - `NuisanceParameter: "<shared_NP_name>"` inside individual `Systematic` blocks to correlate differently named systematics across channels.
       - `DecorrSysts: "<syst1>", "<syst2>"` and `DecorrSuff: "_chanA"` inside a `ConfigFile` entry in the `MultiFit` config to decorrelate specific systematics for that channel during workspace combination.

---

## 4. Publication Exports & Data Preservation (`HEPData`, `uhepp`, LaTeX)

ATLAS publications require standardized rounding, systematic breakdown tables, and machine-readable preservation archives:

- **`UseATLASRounding: TRUE`** (`Job` block):
  - Formats all LaTeX yield tables (`Tables/`), pull tables, and POI outputs following official ATLAS Particle Data Group (PDG) significant-digit rounding rules.
- **`CleanTables: TRUE` & `SystCategoryTables: TRUE`** (`Job` block):
  - Generates clean publication-ready LaTeX tables and grouped systematic impact tables (`GroupedImpact.tex`) breaking down $\Delta\mu/\mu$ by `Category` and `SubCategory`.
- **`HEPDataFormat: TRUE`** (`Job` / `MultiFit` block):
  - Exports pre-fit and post-fit region histograms, covariance/correlation matrices, unfolded spectra, and limit curves in YAML format inside `<JobName>/HEPData/`, ready for direct upload to `hepdata.net`.
- **`UheppFormat: TRUE`** (`Job` block):
  - Exports self-contained JSON histograms in the Universal HEP Plot (`uhepp`) format inside `<JobName>/uhepp/`.
- **`CombinerFormat: TRUE`** (`Job` block):
  - Exports metadata cards for downstream ATLAS Higgs/Top workspace combination tools.
