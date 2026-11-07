---
name: trex-systematics-and-gammas
description: Configure and troubleshoot systematic uncertainties and Monte Carlo statistical uncertainties (gammas) in TRExFitter. Covers HISTO, OVERALL, and SHAPE systematics, symmetrisation (ONESIDED, TWOSIDED, ABSMEAN, MAXIMUM, AlternativeShapeHistFactory), smoothing algorithms (MAXVARIATION, TTBARRESONANCE, COMMONTOOLSMOOTHMONOTONIC, COMMONTOOLSMOOTHPARABOLIC, kernel methods), pruning (SystPruningShape, SystPruningNorm, SystLarge, PruningType), two-point theoretical/generator uncertainties (ReferenceSample, SubtractRefSampleVar), scale/PDF envelopes (CombineName, CombineType), decorrelation (Decorrelate, DropNorm, DropShapeIn), and Barlow-Beeston gammas (SeparateGammas, CorrelateGammasWithSample, negative yields, Bootstrap).
---

# Systematic Uncertainties & MC Statistical Gammas in TRExFitter

In collider physics analyses (such as ATLAS $t\bar{t}H$, $t\bar{t}+\text{HF}$, $4t$, top mass, and diboson/triboson measurements), hundreds of experimental and theoretical systematic uncertainties enter the binned profile likelihood. Improper treatment of statistical fluctuations in systematic templates is the **#1 cause of spurious nuisance parameter (NP) constraints, erratic pulls, and fit non-convergence**.

For detailed mathematical definitions of all smoothing, symmetrisation, and pruning algorithms, consult [`references/smoothing_symmetrisation_pruning.md`](references/smoothing_symmetrisation_pruning.md).

---

## 1. Types of `Systematic` Blocks & HistFactory Modifiers

Each `Systematic` block specifies `Type`:
- **`Type: OVERALL`**: Pure normalization uncertainty across all bins of a region/sample (`OverallSys` in `HistFactory`). Configured via `OverallUp: 0.05` and `OverallDown: -0.05` (for $\pm 5\%$).
- **`Type: HISTO`** (Default): Both overall normalization (`OverallSys`) and bin-by-bin shape migration (`HistoSys` in `HistFactory`), controlled by a **single correlated Gaussian NP** $\theta_k$ (`alpha_<Name>`).
  - To keep **only the shape component** and drop the normalization effect in all or specific regions/samples: use `DropNorm: "all"` (or `DropNorm: "CR_ttbar"`).
  - To keep **only the normalization component** and drop the shape effect: use `DropShapeIn: "all"` (or `DropShapeIn: "SR1"`).
- **`Type: SHAPE`**: Creates an **independent, uncorrelated bin-by-bin parameter** in every bin (`ShapeSys` in `HistFactory`, constrained by Poisson/Gaussian terms).
  - **HEP Use Case**: Used when a systematic represents uncorrelated bin-by-bin uncertainties (or when testing whether a `HISTO` systematic's pull is driven by coherent shape across bins vs. single-bin fluctuations).

---

## 2. Two-Point Theoretical / Generator Systematics (`ReferenceSample`)

In ATLAS analyses, parton shower / hadronisation uncertainties (e.g., `Powheg+Pythia8` vs. `Powheg+Herwig7`) or matrix-element generator uncertainties (e.g., `Powheg+Pythia8` vs. `MadGraph5_aMC@NLO+Pythia8` or `Sherpa`) are evaluated by comparing two independent Monte Carlo samples.

### Intricacy 1: FastSim (`AFII`/`Atlfast3`) vs. `FullSim` Nominal
Often the nominal sample is simulated with Geant4 (`FullSim`), whereas the alternative generator sample is only available in Fast Simulation (`AFII` / `Atlfast3`). Comparing `AFII Herwig7` directly to `FullSim Pythia8` would conflate detector simulation differences with parton shower physics!
- **Solution (`ReferenceSample`)**:
  1. Define a `GHOST` sample for the nominal generator in FastSim (`ttbar_Py8_AFII`).
  2. In the `Systematic` block acting on the `FullSim` nominal sample (`ttbar`), set `ReferenceSample: "ttbar_Py8_AFII"`.
  3. `TRExFitter` computes the relative bin-by-bin ratio (or difference if `SubtractRefSampleVar: TRUE`) between the alternative sample and `ReferenceSample`, and multiplies that relative variation onto the `FullSim` nominal template:
     $$\nu_{i}^{\text{syst}} = \nu_{i}^{\text{nom, FullSim}} \times \frac{\nu_{i}^{\text{alt, AFII}}}{\nu_{i}^{\text{ref, AFII}}}$$

```yaml
Sample: "ttbar_Py8_AFII"
  Type: GHOST
  HistoFile: "ttbar_PhPy8_AFII"

Systematic: "ttbar_PS_Model"
  Title: "t#bar{t} Parton Shower (Py8 vs H7)"
  Type: HISTO
  Samples: "ttbar"
  ReferenceSample: "ttbar_Py8_AFII"
  HistoFileUp: "ttbar_PhH7_AFII"
  Symmetrisation: ONESIDED
  Smoothing: 40
  Category: "Theory"
  SubCategory: "ttbar_PS"
```

### Intricacy 2: Statistical Fluctuations in Independent MC Variations
Because two-point generator variations (`Herwig7`, `aMC@NLO`, `hdamp`, `top mass` variations) use statistically independent MC events rather than internal event weights, their bin-by-bin difference $\nu_i^{\text{alt}} - \nu_i^{\text{nom}}$ carries the quadrature sum of both samples' MC statistical errors.
- If left unsmoothed in a multi-bin distribution, a $2\sigma$ statistical spike in a single high-statistics background bin acts as a fake "lever arm" that **artificially over-constrains** ($\Delta\hat{\theta} \ll 1$) and **pulls** the generator NP in the fit!
- **Mandatory Remedies in TRExFitter**:
  1. Always apply `Symmetrisation: ONESIDED` for single-template two-point comparisons.
  2. Always enable `Smoothing` (e.g., `Smoothing: 40` with an appropriate `SmoothingOption` in `Job`, or `COMMONTOOLSMOOTHMONOTONIC` / `TTBARRESONANCE`) or use `Bootstrap` to verify whether constraints are physical or driven by MC stat noise.
  3. Always inspect `<JobName>/Systematics/<SystName>/` plots (`SystControlPlots: TRUE`), which show the dashed raw variation alongside the solid smoothed/symmetrised template and its statistical error bars (`SystErrorBars: TRUE`).

---

## 3. Symmetrisation Schemes (`Symmetrisation`)

| Option | Input Variations | Formula for $\Delta_i^{\text{up}}$ and $\Delta_i^{\text{down}}$ | When to Use in HEP |
| :--- | :--- | :--- | :--- |
| **`ONESIDED`** | Only `Up` (or only `Down`) provided | $\Delta_i^{\text{up}} = \nu_i^{\text{up}} - \nu_i^0$, $\Delta_i^{\text{down}} = -\Delta_i^{\text{up}}$ | Two-point generator comparisons (PS, ME, `hdamp`), JER single-sided smearing, or single-template theory uncertainties. |
| **`TWOSIDED`** | Both `Up` and `Down` provided | $\Delta_i^{\text{up}} = \frac{\nu_i^{\text{up}} - \nu_i^{\text{down}}}{2} = -\Delta_i^{\text{down}}$ | Standard for up/down variations (e.g., JES/JER components, ISR/FSR, colour reconnection) that suffer from MC stat noise or same-sign ("one-sided") bin fluctuations where both `Up` and `Down` shift in the same direction relative to nominal. |
| **`ABSMEAN`** | Both `Up` and `Down` provided | $\Delta_i^{\text{up}} = +\frac{|\nu_i^{\text{up}} - \nu_i^0| + |\nu_i^{\text{down}} - \nu_i^0|}{2} = -\Delta_i^{\text{down}}$ | When both `Up` and `Down` shift in the **same direction** in a bin and you want the average magnitude rather than cancellation ($\nu^{\text{up}} - \nu^{\text{down}} \approx 0$). **Note**: Loses sign correlation across bins unless used carefully! |
| **`MAXIMUM`** | Both `Up` and `Down` provided | $|\Delta_i| = \max(|\nu_i^{\text{up}} - \nu_i^0|, |\nu_i^{\text{down}} - \nu_i^0|)$ (preserving sign of larger shift) | Conservative envelope-style symmetrisation when one variation is much larger than the other. |

### `AlternativeShapeHistFactory: TRUE` (Normalization Order Intricacy)
By default (`AlternativeShapeHistFactory: FALSE`), for a `ONESIDED` systematic, `TRExFitter` first symmetrises the unnormalized template ($\nu_i^{\text{down}} = 2\nu_i^0 - \nu_i^{\text{up}}$) and *then* normalizes both `Up` and `Down` templates to the nominal integral $I^0$ for `HistoSys`. If the overall normalization shift $\epsilon = (I^{\text{up}} - I^0)/I^0$ is large (e.g., $>15\%$), the resulting normalized `HistoSys` shape templates are **asymmetric**:
$$\frac{\hat{\nu}_i^{\text{up}}}{\nu_i^0} - 1 \neq -\left(\frac{\hat{\nu}_i^{\text{down}}}{\nu_i^0} - 1\right)$$
Setting **`AlternativeShapeHistFactory: TRUE`** in `Job` reverses the order: `TRExFitter` first normalizes $\nu_i^{\text{up}}$ to the nominal integral $I^0$, and *then* symmetrises the pure shape template (while the overall normalization shift is still captured in `OverallSys`). This guarantees strictly symmetric `HistoSys` shapes and prevents artificial second-derivative kinks in $-\ln\mathcal{L}$ at $\theta = 0$.

---

## 4. Smoothing Algorithms (`SmoothingOption` & `Smoothing`)

To activate smoothing on a systematic, set `Smoothing: 40` (or `TRUE`) in the `Systematic` block and choose `SmoothingOption` in `Job` (or per-systematic `SmoothingOption`):
- **`MAXVARIATION`** (Default): Merges adjacent bins where statistical uncertainty exceeds variations, limiting the number of local extrema (`TH1::Smooth` after adaptive rebinning).
- **`TTBARRESONANCE`**: Adaptive bin merging until statistical error is small compared to systematic variation, widely used for two-point MC generator comparisons.
- **`COMMONTOOLSMOOTHMONOTONIC`** / **`COMMONTOOLSMOOTHPARABOLIC`**: From the ATLAS `SystematicSmoothingTool` submodule; enforces monotonic (0 extrema) or parabolic ($\le 1$ extremum) shape variations—ideal for kinematic distributions ($p_T$, $m_{jj}$, $H_T$) where physical scale/shower variations are smooth.
- **`KERNELRATIOUNIFORM`**, **`KERNELDELTAGAUSS`**, **`KERNELRATIOGAUSS`**: Kernel density smoothing on ratios or differences.

> **Important**: Smoothing is executed during `n`, `h`, or `b`. If you change `Smoothing` or `Symmetrisation`, you only need to re-run `trex-fitter bwf <config>` (no need to re-run `n` or `h`).

---

## 5. Scale / PDF Envelopes (`CombineName` & `CombineType`)

To build a 7-point QCD renormalization/factorization scale $(\mu_R, \mu_F)$ envelope or a PDF standard-deviation band directly inside `TRExFitter` during the `b` step:
1. Define a separate `Systematic` block for each scale/PDF variation.
2. Give all components the **exact same** `CombineName: "ttbar_Scale_Envelope"` and set `CombineType: ENVELOPE` (or `STANDARDDEVIATION` for Hessian/replica PDF sets).
3. During the `b` step, `TRExFitter` evaluates the bin-by-bin envelope (or quadrature/standard-deviation sum), stores the combined variation in the first systematic, and zeroes out the remaining components.

---

## 6. Pruning (`SystPruningShape`, `SystPruningNorm`, `SystLarge`)

Pruning occurs during the `w` step (`Pruning.pdf` and `Pruning.root`) to strip negligible or pathological variations before building the `RooWorkspace`, vastly improving `Minuit2` speed and stability:
- `SystPruningNorm: 0.005` (drops `OverallSys` if $|\Delta I / I| < 0.5\%$).
- `SystPruningShape: 0.01` (drops `HistoSys` if $\max_i |\hat{\nu}_i^{\pm} - \nu_i^0| / \nu_i^0 < 1\%$ under `PruningShapeOption: MAXBIN`, or if the KS-test probability $> 1 - \text{threshold}$ under `PruningShapeOption: KSTEST`).
- **`PruningType` choice**:
  - `SEPARATESAMPLE` (default): Evaluates relative variation with respect to that individual sample's yield $\nu_{csi}^0$.
  - `BACKGROUNDREFERENCE` or `COMBINEDREFERENCE`: Evaluates the variation of sample $s$ divided by the **total background** (or **total signal + background**) yield in that bin/region! This is a major improvement in HEP fits with tiny minor backgrounds (e.g., $tWZ$ representing $0.5\%$ of total yield having a $20\%$ theory uncertainty that is only $0.1\%$ of total yield and would otherwise bloat the workspace).
  - `COMBINEDSIGNAL`: Evaluates variation relative to total signal yield—**mandatory for `UNFOLDING` fits** where individual truth bins appear as separate signal samples in reco regions.
- `SystLarge: 0.40` + `RemoveLargeSyst: FALSE` (or `TRUE`): Flags (or prunes) variations exceeding $40\%$ in `Pruning.pdf` so broken histograms are caught immediately.

---

## 7. Decorrelating Systematics (`Decorrelate`, `DecorrSysts`, `StoredName`)

When a nuisance parameter is strongly pulled or over-constrained, you must test whether the pull/constraint originates from a specific region, sample, or its shape vs. normalization component (see `docs/model_studies/decorrelation.md`):
- **Automatic `Decorrelate` keyword inside a `Systematic` block**:
  - `Decorrelate: REGION` — Splits the NP into independent NPs per `Region`.
  - `Decorrelate: SAMPLE` — Splits the NP into independent NPs per `Sample`.
  - `Decorrelate: SHAPEACC` — Splits `Type: HISTO` into two independent NPs: one controlling only the shape (`HistoSys`) and one controlling only the regional acceptance/normalization (`OverallSys`).
- **Manual Decorrelation without Re-running `n`/`h` (`StoredName` + `NuisanceParameter`)**:
  To correlate two differently named `Systematic` blocks in the fit, set `NuisanceParameter: "Common_NP_Name"` on both. Conversely, to split a systematic across two regions without re-creating histograms in `Histograms/`, clone the `Systematic` block with a new name, restrict `Regions`, and set `StoredName: "OriginalSystName"` so `w` reads the existing histogram from `Histograms/`.

---

## 8. Monte Carlo Statistical Uncertainties (`Gammas`) & Negative Yields

1. **Standard Barlow-Beeston Lite (`gamma_stat_<Region>_bin_<i>`)**:
   By default, one Poisson-constrained $\gamma_{ci}$ NP per bin scales the sum of all MC samples in that bin (`MCstatThreshold: 0.01` only adds $\gamma_{ci}$ if relative MC stat error $> 1\%$).
2. **Sample-Specific Gammas (`SeparateGammas: TRUE`)**:
   When a specific background has large MC weights or when its normalization is free-floating (`NormFactor`), lumping its statistical uncertainty into the shared bin $\gamma_{ci}$ can bias the fit. Setting `SeparateGammas: TRUE` on that `Sample` creates dedicated bin-by-bin `ShapeSys` NPs (`re-run the b step!`).
   - Use `CorrelateGammasInRegions: "SR1:CR1"` or `CorrelateGammasWithSample: "otherSample"` when two samples/regions share the same underlying MC events (e.g., reweighted templates), with `ApplyGammaCorrection: TRUE` to prevent double counting.
3. **Negative Event Weights & Empty Bins**:
   NLO generators (`Sherpa`, `MadGraph5_aMC@NLO`) can produce bins with negative net yield $\nu_{csi}^0 \le 0$, which would make the Poisson likelihood $\text{Pois}(n \mid \nu)$ undefined ($\text{NaN}$ in `Minuit2`):
   - `TRExFitter` automatically floors negative/zero bin contents to $10^{-6}$ and rescales positive bins to preserve the total integral of that sample in the region (unless the total integral itself is negative, controlled by `CorrectNormForNegativeIntegral`).
   - `GuessMCStatEmptyBins: TRUE` (default) assigns the smallest non-zero statistical error from other bins of that histogram to any empty ($0$-error) bin.
4. **Bootstrap Method (`Bootstrap`)**:
   For `ReadFrom: NTUP`, `Bootstrap: "BootstrapDefault(eventNumber+mcChannelNumber+BootstrapIdx)"` generates Poisson-weighted pseudo-experiments (`BootstrapIdx=0,1,2,...`) preserving exact statistical correlations between nominal and systematic variations (`BootstrapSyst`, `BootstrapSample`).
