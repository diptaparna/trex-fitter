# Unfolding and Morphing Configuration Reference

This reference provides complete option tables and production-grade `.config` examples for **Profile Likelihood Unfolding (`FitType: UNFOLDING`)** and **Continuous Template Morphing (`Morphing`)** in `TRExFitter`.

---

## 1. Profile Likelihood Unfolding Block Reference

### 1.1 `Unfolding` Block Options

| Setting | Type / Values | Description |
| :--- | :--- | :--- |
| `MatrixOrientation` | `TRUTHONHORIZONTAL` \| `TRUTHONVERTICAL` | Orientation of 2D migration histograms (`TH2`). Default: `TRUTHONHORIZONTAL` (X = truth bin $j$, Y = reco bin $i$). |
| `TruthDistributionPath` | `<path>` | Base directory for truth distribution files. |
| `TruthDistributionFile` | `<filename>` | ROOT file containing the 1D truth histogram $T_j^{\text{nom}}$ (without `.root`). |
| `TruthDistributionName` | `<histname>` | Name of the 1D truth histogram in `TruthDistributionFile`. |
| `NumberOfTruthBins` | `<int>` | Number of truth bins $N_{\text{truth}}$. `TRExFitter` automatically creates POIs `NormFactor` `Unfolding_Bin_001_mu` ... `Unfolding_Bin_N_mu`. |
| `UnfoldingDivideByBinWidth` | `TRUE` \| `FALSE` | Divides the unfolded yields by the bin width $\Delta X_j$ to produce $\mathrm{d}\sigma/\mathrm{d}X$. |
| `UndivideStep` | `TRUE` \| `FALSE` | If input histograms were already divided by bin width, multiplies by bin width before building the Poisson likelihood. |
| `NominalTruthSample` | `<TruthSampleName>` | Reference `TruthSample` used to convert unfolded signal strengths $\hat{\mu}_j$ into unfolded yields/cross-sections. |
| `AlternativeAsimovTruthSample` | `<TruthSampleName>` | Uses an alternative `TruthSample` to weight the Asimov dataset for unfolding closure/bias stress tests. |
| `UnfoldingResultMin` / `UnfoldingResultMax` | `<float>` | Default range `[Min, Max]` for the generated truth-bin POI `NormFactor`s. |
| `UnfoldingTitleX` / `UnfoldingTitleY` | `<string>` | Axis labels for the final unfolded plot (`UnfoldedData.pdf`). |
| `UnfoldingScaleRangeY` | `<float>` | Y-axis scaling factor for the unfolded distribution plot. |
| `UnfoldingLogY` | `TRUE` \| `FALSE` | Plot unfolded distribution with logarithmic Y-axis. |
| `UnfoldingShowStatOnlyError` | `TRUE` \| `FALSE` | Overlays the statistical-only uncertainty band inside the total uncertainty band on the unfolded plot. |
| `UnfoldingShowUncertaintyBreakdown` | `TRUE` \| `FALSE` | Produces a fractional uncertainty breakdown plot across truth bins by `SubCategory`. |
| `RegularizationType` | `0` \| `1` \| `2` \| `3` \| `4` | Tikhonov regularization penalty operator ($0$: unit, $1$: 1st derivative, $2$: 2nd derivative curvature, $3/4$: strength-weighted curvature). |
| `Tau` | `<float>` (or comma-separated list) | Tikhonov regularization strength parameter $\tau$. |
| `ToysStatOutput` | `TRUE` \| `FALSE` | Computes statistical uncertainties on unfolded bins via pseudo-experiments (essential when `Tau > 0`). |

### 1.2 `TruthSample` Block Options

| Setting | Type / Values | Description |
| :--- | :--- | :--- |
| `TruthSample: "<name>"` | Block header | Unique identifier for a truth-level prediction curve. |
| `Title` | `<string>` | Legend label on the unfolded plot (e.g., `"Powheg+Pythia8"`). |
| `TruthDistributionPath` / `File` / `Name` | `<string>` | Location of the 1D truth histogram for this generator prediction. |
| `LineStyle` / `LineColor` / `LineWidth` | `<int>` | ROOT line styling for the prediction overlay on `UnfoldedData.pdf`. |
| `UseForPlotting` | `TRUE` \| `FALSE` | Whether to draw this `TruthSample` on the final unfolded plot. |

### 1.3 `UnfoldingSample` Block Options

| Setting | Type / Values | Description |
| :--- | :--- | :--- |
| `UnfoldingSample: "<name>"` | Block header | Defines the signal sample to be folded via the response matrix. |
| `Type` | `STANDARD` \| `GHOST` | Set to `GHOST` for alternative generator samples used only in `UnfoldingSystematic` `ReferenceSample` / `SampleUp`. |
| `Title` / `FillColor` / `LineColor` | `<string>` / `<int>` | Legend title and colors for the folded signal in pre/post-fit detector plots. |
| `Regions` | `<reg1>, <reg2>` | Reconstructed Signal Regions where this response matrix applies. |
| `MigrationFile` / `MigrationName` | `<string>` | File and 2D histogram (`TH2`) name for the migration matrix $M_{ij}$. |
| `SelectionEffFile` / `SelectionEffName` | `<string>` | File and 1D truth-binned histogram (`TH1`) for the selection efficiency $\epsilon_j$. |
| `AcceptanceFile` / `AcceptanceName` | `<string>` | File and 1D reco-binned histogram (`TH1`) for the fiducial acceptance $A_i$. |
| `ResponseMatrixFile` / `ResponseMatrixName` | `<string>` | Alternative: directly provide the combined response matrix $R_{ij}$ as a 2D `TH2`. |

### 1.4 `UnfoldingSystematic` Block Options

| Setting | Type / Values | Description |
| :--- | :--- | :--- |
| `UnfoldingSystematic: "<name>"` | Block header | Defines a systematic uncertainty acting on the response matrix $R_{ij}(\theta)$. |
| `Title` / `Category` / `SubCategory` | `<string>` | Display title and grouping for tables/uncertainty breakdowns. |
| `UnfoldingSamples` | `<name>` | Target `UnfoldingSample`(s) affected by this systematic. |
| `Symmetrisation` | `ONESIDED` \| `TWOSIDED` \| `ABSMEAN` \| `MAXIMUM` | Symmetrisation prescription applied to the folded template variations in each truth bin. |
| `Smoothing` | `<int>` (e.g. `40`) | Smoothing applied to folded reco templates per truth bin. |
| `MigrationFileUp` / `Down`, `MigrationNameUp` / `Down` | `<string>` | Up/Down varied 2D migration matrices. |
| `SelectionEffFileUp` / `Down`, `SelectionEffNameUp` / `Down` | `<string>` | Up/Down varied 1D selection efficiencies. |
| `AcceptanceFileUp` / `Down`, `AcceptanceNameUp` / `Down` | `<string>` | Up/Down varied 1D fiducial acceptances. |
| `SampleUp` / `SampleDown` | `<GhostUnfoldingSample>` | Build the response variation from a `GHOST` `UnfoldingSample`. |
| `ReferenceSample` | `<GhostUnfoldingSample>` | Reference `GHOST` `UnfoldingSample` for relative two-point generator variations (e.g., `AFII` vs `AFII`). |
| `HasAcceptance` | `TRUE` \| `FALSE` | Whether the systematic includes acceptance variations $A_i$. |

---

## 2. Complete Profile Likelihood Unfolding `.config` Example

```text
Job: "ttbar_diff_pt_unfolding"
  Label: "t#bar{t} d#sigma/dp_{T}^{t}"
  CmeLabel: "13 TeV"
  LumiLabel: "140 fb^{-1}"
  ReadFrom: HIST
  HistoPath: "inputs/unfolding"
  POI: "Unfolding_Bin_001_mu","Unfolding_Bin_002_mu","Unfolding_Bin_003_mu","Unfolding_Bin_004_mu"
  DebugLevel: 1
  SystControlPlots: TRUE
  UseGammaPulls: TRUE
  PruningType: COMBINEDSIGNAL
  SystPruningShape: 0.005
  SystPruningNorm: 0.005
  KeepPruning: TRUE

Fit: "fit"
  FitType: UNFOLDING
  FitRegion: CRSR
  FitBlind: FALSE
  UseMinos: "all"
  SetRandomInitialNPval: 0.1
  UseHesseBeforeMigrad: TRUE
  DoNonProfileFit: TRUE

Unfolding: "unfolding"
  MatrixOrientation: TRUTHONHORIZONTAL
  TruthDistributionPath: "inputs/unfolding"
  TruthDistributionFile: "ttbar_PP8_nominal"
  TruthDistributionName: "h_truth_top_pt"
  NumberOfTruthBins: 4
  UnfoldingResultMin: 0.0
  UnfoldingResultMax: 3.0
  UnfoldingTitleX: "Truth p_{T}^{t} [GeV]"
  UnfoldingTitleY: "d#sigma / dp_{T}^{t} [pb / GeV]"
  UnfoldingDivideByBinWidth: TRUE
  NominalTruthSample: "PP8"
  UnfoldingShowStatOnlyError: TRUE
  UnfoldingShowUncertaintyBreakdown: TRUE

TruthSample: "PP8"
  Title: "Powheg + Pythia8"
  LineColor: 2
  LineStyle: 1
  TruthDistributionFile: "ttbar_PP8_nominal"
  TruthDistributionName: "h_truth_top_pt"
  UseForPlotting: TRUE

TruthSample: "PH7"
  Title: "Powheg + Herwig7"
  LineColor: 4
  LineStyle: 2
  TruthDistributionFile: "ttbar_PH7_alt"
  TruthDistributionName: "h_truth_top_pt"
  UseForPlotting: TRUE

Region: "SR_ljets"
  Type: SIGNAL
  HistoFile: "reco_histograms"
  HistoName: "h_reco_top_pt"
  VariableTitle: "Reconstructed p_{T}^{t} [GeV]"

Sample: "Data"
  Type: DATA
  Title: "Data"

UnfoldingSample: "ttbar_signal"
  Title: "t#bar{t} Fiducial Signal"
  FillColor: 0
  LineColor: 1
  Regions: "SR_ljets"
  MigrationFile: "ttbar_PP8_nominal"
  MigrationName: "h2_migration_top_pt"
  SelectionEffFile: "ttbar_PP8_nominal"
  SelectionEffName: "h_eff_top_pt"
  AcceptanceFile: "ttbar_PP8_nominal"
  AcceptanceName: "h_acc_top_pt"

UnfoldingSample: "ttbar_PH7_ghost"
  Type: GHOST
  Regions: "SR_ljets"
  MigrationFile: "ttbar_PH7_alt"
  MigrationName: "h2_migration_top_pt"
  SelectionEffFile: "ttbar_PH7_alt"
  SelectionEffName: "h_eff_top_pt"
  AcceptanceFile: "ttbar_PH7_alt"
  AcceptanceName: "h_acc_top_pt"

Sample: "Wjets"
  Type: BACKGROUND
  Title: "W + jets"
  FillColor: 92
  LineColor: 1
  HistoFile: "reco_histograms"

UnfoldingSystematic: "ttbar_PS_Hadronisation"
  Title: "t#bar{t} Parton Shower (PH7 vs PP8)"
  Category: "Modelling"
  SubCategory: "ttbar PS"
  UnfoldingSamples: "ttbar_signal"
  SampleUp: "ttbar_PH7_ghost"
  Symmetrisation: ONESIDED
  Smoothing: 40
```

---

## 3. Continuous Template Morphing Reference & Example

### 3.1 `Morphing` Block & `Sample` Options

| Setting | Block | Values | Description |
| :--- | :--- | :--- | :--- |
| `Morphing: "<POI>", <value>` | `Sample` | `<string>, <float>` | Associates a sample template with parameter value `<value>` of `NormFactor` `<POI>`. |
| `TemplateInterpolationOption` | `Morphing` | `LINEAR` \| `SMOOTHLINEAR` \| `SQUAREROOT` | Interpolation functional form between discrete templates (`SMOOTHLINEAR` recommended for smooth derivatives). |
| `SmoothMorphingTemplates` | `Morphing` | `TRUE` \| `FALSE` | Applies polynomial smoothing across discrete template points per bin to reduce MC statistical jitter. |
| `PropagateSystsForMorphing` | `Job` / `Morphing` | `TRUE` \| `FALSE` | Evaluates `Systematic` blocks on the nominal template (matching `NormFactor` `Nominal`) and propagates relative shifts to all morphed templates. |
| `ExcludeFromMorphing` | `Morphing` | `<SampleName>` | Drops a specific discrete template from the morphing setup (used for linearity/closure tests at that parameter point). |
| `MorphingFunctionParam` | `Morphing` | `<int>, <string>, <float>` | Tunes polynomial order or smoothing parameters when `SmoothMorphingTemplates: TRUE`. |

### 3.2 Complete Template Morphing `.config` Example (Top-Quark Mass Extraction)

```text
Job: "TopMass_Boosted_Morphing"
  Label: "Boosted m_{t} Extraction"
  CmeLabel: "13 TeV"
  LumiLabel: "140 fb^{-1}"
  ReadFrom: HIST
  HistoPath: "inputs/topmass"
  POI: "TopMass"
  PropagateSystsForMorphing: TRUE
  SystControlPlots: TRUE
  GetChi2: TRUE

Fit: "fit"
  FitType: SPLUSB
  FitRegion: CRSR
  FitBlind: FALSE
  UseMinos: "TopMass"
  GetGoodnessOfFit: TRUE
  SaturatedModel: TRUE
  doLHscan: "TopMass"
  SetRandomInitialNPval: 0.1
  UseHesseBeforeMigrad: TRUE

Morphing: "morphing"
  TemplateInterpolationOption: SMOOTHLINEAR
  SmoothMorphingTemplates: FALSE

NormFactor: "TopMass"
  Title: "m_{t} [GeV]"
  Nominal: 172.5
  Min: 170.0
  Max: 175.0
  Samples: "ttbar"

Region: "SR_BoostedTop_mJ"
  Type: SIGNAL
  HistoFile: "boosted_histos"
  HistoName: "h_mJ"
  VariableTitle: "Large-R Jet Mass m_{J} [GeV]"

Region: "CR_InSitu_JSF"
  Type: CONTROL
  HistoFile: "boosted_histos"
  HistoName: "h_mW_had"
  VariableTitle: "Reconstructed Hadronic W Mass [GeV]"

Sample: "Data"
  Type: DATA
  Title: "Data"

# Nominal template at exact Nominal value of TopMass (172.5 GeV)
Sample: "ttbar"
  Type: SIGNAL
  Title: "t#bar{t} (m_{t} morphed)"
  FillColor: 0
  LineColor: 2
  HistoFile: "ttbar_mt1725"
  Morphing: "TopMass", 172.5

Sample: "ttbar_mt1700"
  Type: SIGNAL
  HistoFile: "ttbar_mt1700"
  Morphing: "TopMass", 170.0

Sample: "ttbar_mt1715"
  Type: SIGNAL
  HistoFile: "ttbar_mt1715"
  Morphing: "TopMass", 171.5

Sample: "ttbar_mt1735"
  Type: SIGNAL
  HistoFile: "ttbar_mt1735"
  Morphing: "TopMass", 173.5

Sample: "ttbar_mt1750"
  Type: SIGNAL
  HistoFile: "ttbar_mt1750"
  Morphing: "TopMass", 175.0

# Systematics are defined on the nominal "ttbar" sample and automatically
# propagated across all morphed templates via PropagateSystsForMorphing: TRUE
Systematic: "JET_LargeR_MassScale"
  Title: "Large-R Jet Mass Scale"
  Type: HISTO
  Samples: "ttbar"
  HistoFileUp: "ttbar_mt1725_JMS_Up"
  HistoFileDown: "ttbar_mt1725_JMS_Down"
  Symmetrisation: TWOSIDED
  Smoothing: 40
  Category: "Instrumental"
```
