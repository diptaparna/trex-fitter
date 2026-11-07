---
name: trex-unfolding-and-morphing
description: Configure Profile Likelihood Unfolding (PLU) for differential cross-section measurements and Continuous Template Morphing for precision parameter extraction (such as top-quark mass or EFT couplings) in TRExFitter. Use when setting up Unfolding, TruthSample, UnfoldingSample, UnfoldingSystematic, or Morphing blocks, configuring response/migration matrices, Tikhonov regularization, or diagnosing morphing linearity and closure tests.
---

# TRExFitter Profile Likelihood Unfolding & Template Morphing

This skill covers two advanced statistical inference techniques implemented in `TRExFitter` and widely used in ATLAS precision Standard Model and top-quark measurements:
1. **Profile Likelihood Unfolding (`FitType: UNFOLDING`)** for differential cross-section measurements ($\mathrm{d}\sigma/\mathrm{d}X$).
2. **Continuous Template Morphing (`Morphing`)** for extracting continuous physics parameters (e.g., top-quark mass $m_t$, $W$-boson mass $m_W$, or non-linear EFT couplings) that alter histogram shapes non-linearly.

For complete configuration option tables and copy-ready `.config` templates, read `references/unfolding_and_morphing_reference.md`.

---

## 1. Profile Likelihood Unfolding (PLU)

Unlike iterative Bayesian (D'Agostini) or matrix-inversion unfolding which subtract background before unfolding and propagate systematic uncertainties by repeating the unfolding for each shift, **Profile Likelihood Unfolding** embeds the response matrix directly into the `HistFactory` likelihood. Background normalization/shape constraints from Control Regions and systematic nuisance parameters $\bm{\theta}$ are profiled simultaneously with the truth-level signal strengths $\bm{\mu} = (\mu_1, \dots, \mu_{N_{\text{truth}}})$.

### 1.1 Mathematical Formulation of Folding in `TRExFitter`

Each truth bin $j \in \{1, \dots, N_{\text{truth}}\}$ is treated as an independent `HistFactory` signal sample scaled by its own free `NormFactor` $\mu_j$. The predicted reconstructed yield in detector bin $i \in \{1, \dots, N_{\text{reco}}\}$ is folded from the truth yield $T_j$ via the response matrix $R_{ij}$:

$$\nu_i^{\text{sig}}(\bm{\mu}, \bm{\theta}) = \sum_{j=1}^{N_{\text{truth}}} \mu_j \, R_{ij}(\bm{\theta}) \, T_j^{\text{nom}} + B_i^{\text{fake}}(\bm{\theta})$$

where the folding element $R_{ij}$ is decomposed by `TRExFitter`'s `UnfoldingCode` submodule into:
- **Migration matrix** $M_{ij} = P(\text{reco bin } i \mid \text{truth bin } j \land \text{selected both truth \& reco})$, normalized such that $\sum_{i=1}^{N_{\text{reco}}} M_{ij} = 1$ for every truth bin $j$.
- **Selection efficiency** $\epsilon_j = N_{\text{truth } j \land \text{reco}} / N_{\text{truth } j}$ (probability that an event in truth bin $j$ passes detector reconstruction and selection).
- **Acceptance / fiducial efficiency** $A_i = N_{\text{truth} \land \text{reco } i} / N_{\text{reco } i}$ (fraction of reconstructed signal events in bin $i$ that originate inside the fiducial phase space; events failing truth selection enter $1 - A_i$ as non-fiducial / fake signal).

Combined, the folded expectation in reco bin $i$ from truth bin $j$ is:

$$R_{ij} \, T_j = \frac{\epsilon_j \, M_{ij}}{A_i} \, T_j$$

### 1.2 Execution Sequence (`u n w f p r`)

Profile Likelihood Unfolding introduces the **`u` step** (`PrepareUnfolding`), which MUST run **before** `n`/`h`/`b` and `w`:
```bash
# 1. Fold response matrices & truth spectra into per-truth-bin histograms (u)
# 2. Read/prepare inputs (n or h)
# 3. Build workspace (w), fit (f), plot post-fit & unfolded spectrum (p), rankings (r)
trex-fitter uhtwfpr my_unfolding.config
```

### 1.3 Essential Configuration Blocks for Unfolding

1. **`Job` block**:
   - Set `PruningType: COMBINEDSIGNAL`! Because `u` splits the signal into $N_{\text{truth}}$ small sub-samples (one per truth bin), default per-sample pruning (`SEPARATESAMPLE`) can prune systematic variations in off-diagonal migration bins inconsistently across truth bins. `COMBINEDSIGNAL` evaluates pruning against the total summed signal across all truth bins.
2. **`Fit` block**:
   - Set `FitType: UNFOLDING`.
3. **`Unfolding` block**:
   - `MatrixOrientation: TRUTHONHORIZONTAL` (default: X-axis = truth, Y-axis = reco) or `TRUTHONVERTICAL` (X-axis = reco, Y-axis = truth). Verify your 2D `TH2` axes carefully—swapping this inverts the migration matrix!
   - `TruthDistributionPath`, `TruthDistributionFile`, `TruthDistributionName`: Path to the 1D truth histogram $T_j^{\text{nom}}$ used to derive unfolded cross-sections $\hat{\sigma}_j = \hat{\mu}_j \, T_j^{\text{nom}}$.
   - `NumberOfTruthBins`: Number of bins in the truth distribution.
   - `UnfoldingDivideByBinWidth: TRUE`: Divides the final unfolded distribution by the bin width $\Delta X_j$ to produce differential cross-sections $\mathrm{d}\sigma/\mathrm{d}X$.
   - `UnfoldingResultMin` / `UnfoldingResultMax`, `UnfoldingTitleX`, `UnfoldingTitleY`, `UnfoldingScaleRangeY`, `UnfoldingLogY`: Controls the unfolded result plot (`UnfoldedData.pdf`).
   - `NominalTruthSample`: Name of the `TruthSample` used as the baseline reference.
   - `AlternativeAsimovTruthSample`: Sets an alternative `TruthSample` to generate a non-nominal Asimov dataset for **stress-testing unfolding bias / closure** (e.g., reweighting truth $p_T$ by a linear slope and checking if the unfolded Asimov recovers the injected truth within uncertainties).
   - `UndivideStep: TRUE`: If your input histograms were already divided by bin width, undivides them before building the Poisson workspace.
   - `NormalizeUnfolded: TRUE` (or `NormalizedCrossSection`): Extracts normalized differential cross-sections $(1/\sigma_{\text{fid}})\,\mathrm{d}\sigma/\mathrm{d}X$ by constraining the sum of truth yields or profiling total fiducial cross-section, cancelling luminosity and overall normalization uncertainties.
4. **`TruthSample` block**:
   - Defines truth-level theory predictions overlaid on the final unfolded plot (e.g., `Powheg+Pythia8`, `Powheg+Herwig7`, `Sherpa`).
   - Use `LineStyle`, `LineColor`, `Title`, `TruthDistributionFile`, `TruthDistributionName`.
5. **`UnfoldingSample` block**:
   - Replaces standard `SIGNAL` `Sample` blocks. Defines how the 2D migration matrix (`MigrationFile`, `MigrationName`), 1D selection efficiency (`SelectionEffFile`, `SelectionEffName`), and 1D acceptance (`AcceptanceFile`, `AcceptanceName`) are loaded, or how they are built from ntuples (`ResponseMatrixFile`, `ResponseMatrixName`, `ResponseMatrixPaths`, `AcceptanceMcPaths`, `SelectionEffMcPaths`, `SubStep: MIGRATION | ACCEPTANCE | SELECTIONEFF`).
   - `Type: STANDARD` (default) or `GHOST` (used as a reference for two-point unfolding systematics).
6. **`UnfoldingSystematic` block**:
   - Propagates systematic uncertainties onto the response matrix $R_{ij}(\bm{\theta})$ (varying migration, efficiency, and acceptance simultaneously for each truth bin $j$).
   - Supports `Symmetrisation: ONESIDED | TWOSIDED | ABSMEAN | MAXIMUM`, `SampleUp`, `SampleDown`, `ReferenceSample` (pointing to a `GHOST` `UnfoldingSample`), `Smoothing`, `Category`, `SubCategory`, `Decorrelate`, `DropShapeIn`, `DropNorm`.

### 1.4 Diagnosis of Bin-to-Bin Anti-Correlations & Tikhonov Regularization

When $N_{\text{reco}}$ bins have significant off-diagonal migrations ($M_{ij}$ non-diagonal, e.g., purity or stability $< 50\%$), maximum likelihood unfolding exhibits strong negative correlations ($\rho(\mu_j, \mu_{j+1}) \ll -0.5$) and amplified statistical variances in adjacent truth bins.

- **First line of defense (Unregularized Binning Optimization)**:
  - Merge truth and reco bins until diagonal migration elements (purity and stability) exceed **50–60%** in every bin. Unregularized PLU is preferred in ATLAS whenever bin purity/stability is sufficient because it has zero regularization bias.
- **Tikhonov Regularization in `TRExFitter`** (when fine truth binning is required):
  - Adds a penalty term $\tau^2 \, \| L (\bm{\mu} - \bm{\mu}_0) \|^2$ to $-2\ln\Lambda$, where $L$ is a discrete derivative operator (`RegularizationType` in `Unfolding` block):
    - `RegularizationType: 0`: Zeroth-order ($L = I$, penalizes $|\mu_j - 1|^2$).
    - `RegularizationType: 1`: First-order derivative (penalizes $(\mu_{j+1} - \mu_j)^2$).
    - `RegularizationType: 2`: Second-order derivative / curvature (penalizes $(\mu_{j+1} - 2\mu_j + \mu_{j-1})^2$, standard Tikhonov curvature penalty).
    - `RegularizationType: 3` or `4`: Strength-weighted curvature penalties accounting for bin widths / truth slope.
  - Set the regularization strength via `Tau: <val>` (or scan multiple values using `Tau: 0.1, 0.2, 0.5`).
  - **Crucial Pitfall with Regularized Uncertainties**: Standard `HESSE`/`MINOS` uncertainties on regularized POIs include the artificial constraint from the penalty term, underestimating the true frequentist variance! When using `Tau > 0`, enable toy-based statistical error propagation (`ToysStatOutput: TRUE` / `UnfoldingToys`) and inspect bias via `AlternativeAsimovTruthSample` stress tests.

---

## 2. Continuous Template Morphing (`Morphing`)

When extracting a continuous physics parameter $\alpha$ (e.g., top-quark mass $m_t \in [170, 175]\text{ GeV}$, or an EFT Wilson coefficient $c_W$) where Monte Carlo samples are generated at discrete parameter values $\alpha_1 < \alpha_2 < \dots < \alpha_M$, `TRExFitter` interpolates both bin yields and shapes continuously as a function of a free POI `NormFactor`.

### 2.1 How Template Morphing Works in `TRExFitter`

1. Define a free `NormFactor` representing the continuous parameter (e.g., `NormFactor: "TopMass"` with `Nominal: 172.5`, `Min: 170.0`, `Max: 175.0`).
2. Provide one `Sample` block (or `GHOST` templates merged into the morphing sample) for each generated discrete template, tagging each template with `Morphing: "<NormFactorName>", <ParamValue>`:
   ```text
   Sample: "ttbar_mt1715"
     Morphing: "TopMass", 171.5
     ...
   Sample: "ttbar_mt1725"
     Morphing: "TopMass", 172.5
     ...
   Sample: "ttbar_mt1735"
     Morphing: "TopMass", 173.5
     ...
   ```
3. Configure the `Morphing` block:
   - `TemplateInterpolationOption`:
     - `LINEAR` (default): Piece-wise linear bin-by-bin interpolation between adjacent templates $\alpha_k$ and $\alpha_{k+1}$.
     - `SMOOTHLINEAR`: Smooth piece-wise linear interpolation with continuous first derivatives at the anchor points $\alpha_k$ (prevents kinks in $-2\ln\Lambda(\alpha)$ when $\hat{\alpha}$ crosses a discrete template point!).
     - `SQUAREROOT`: Square-root interpolation, useful for quadratic cross-section dependence (e.g., SM + interference + BSM $|\mathcal{M}_{\text{SM}} + c\,\mathcal{M}_{\text{BSM}}|^2$).
   - `SmoothMorphingTemplates: TRUE`: Applies bin-by-bin parabolic/polynomial smoothing across the discrete parameter points $\alpha_1, \dots, \alpha_M$ in each histogram bin $i$ to damp MC statistical fluctuations between independent template samples.

### 2.2 Critical Intricacies & Best Practices from ATLAS Precision Mass Fits

Drawing from recent ATLAS template morphing fits (such as the Run 2 boosted top-quark mass measurement $m_t = 172.95 \pm 0.53\text{ GeV}$):

1. **Nominal Template Rule with `PropagateSystsForMorphing: TRUE`**:
   - Evaluating full detector and modelling systematics at every discrete mass point $\alpha_k$ is computationally prohibitive. Instead, systematics are evaluated on the nominal sample ($\alpha_0 = 172.5\text{ GeV}$) and propagated across the morphed templates using `PropagateSystsForMorphing: TRUE`.
   - **Rule**: When `PropagateSystsForMorphing: TRUE` is enabled, **one of the input templates MUST sit at the exact `Nominal` value of the `NormFactor`** (e.g., `172.5`), and all `Systematic` blocks are attached to that nominal sample.
2. **Simultaneous Auxiliary Observables for In-Situ Nuisance Parameter Constraints**:
   - If the primary morphing observable (e.g., boosted jet invariant mass $m_J$) is strongly degenerate with a nuisance parameter (such as Jet Energy Scale `JES`, $b$-jet energy scale `bJES`, or Final State Radiation `FSR` $\alpha_s^{\text{FSR}}$), the profile likelihood will exhibit a wide ellipse in $(m_t, \theta_{\text{JES}})$.
   - Add auxiliary Regions or 2D unrolled distributions sensitive to those NPs but insensitive to the POI (or combine multiple Regions in `TRExFitter`) so the fit constrains $\theta_{\text{JES}}$ and $\theta_{\text{FSR}}$ *in situ*, reducing the total uncertainty on the morphed POI.
3. **Linearity and Closure Testing (`ExcludeFromMorphing`)**:
   - Before unblinding, you must verify that the piece-wise morphing parameterization has negligible interpolation bias across the entire parameter range.
   - Generate pseudo-data (or Asimov data) from an existing discrete MC template $\alpha_{\text{test}}$ (e.g., $172.0\text{ GeV}$ or $173.0\text{ GeV}$) while **excluding that template from the morphing model** using `ExcludeFromMorphing: "ttbar_mt1720"` (or fitting pseudo-data built from the excluded sample).
   - Plot the residual $(\hat{\alpha} - \alpha_{\text{injected}})$ vs. $\alpha_{\text{injected}}$ across all mass points to confirm linearity and verify that pull widths match 1.0.
4. **Saturated Model Goodness-of-Fit (`GetGoodnessOfFit: TRUE`)**:
   - When using multi-observable morphing or 2D unrolled histograms, always check the **Saturated Model GoF** $p$-value (`GetGoodnessOfFit: TRUE` in `Fit`) on real data to ensure the morphed template + background model accurately describes the joint bin correlations across observables.
5. **1D and 2D Parameter Scans (`doLHscan`)**:
   - Because template morphing introduces non-linear shape dependencies on the POI, parabolic `HESSE` errors are insufficient. Always run `doLHscan: "<NormFactorName>"` (and `do2DLHscan` between the morphed POI and its top-ranked nuisance parameters) to inspect the exact $-2\Delta\ln L(\alpha)$ curve for local minima or kinks at template boundaries.
