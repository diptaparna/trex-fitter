# Limits, Significance, and MultiFit Configuration Reference

This reference provides complete option tables and copy-ready `.config` templates for the `Limit`, `Significance`, and `MultiFit` blocks in `TRExFitter`.

---

## 1. `Limit` Block Options (`l` Step)

| Setting | Type / Values | Description |
| :--- | :--- | :--- |
| `Limit: "<name>"` | Block header | Defines the exclusion limit configuration. |
| `LimitType` | `ASYMPTOTIC` \| `TOYS` | Method used to evaluate 95% $\text{CL}_s$ upper limits. Default: `ASYMPTOTIC`. |
| `LimitBlind` | `TRUE` \| `FALSE` | If `TRUE`, masks the observed data limit and only computes expected limits on Asimov data. |
| `POIAsimov` | `<float>` | Value of the POI $\mu$ used to generate the Asimov dataset for the expected limit (default `0`). |
| `SignalInjection` | `TRUE` \| `FALSE` | Performs a signal injection test by evaluating the expected upper limit on an S+B Asimov dataset. |
| `SignalInjectionValue` | `<float>` | Injected signal strength $\mu_{\text{inj}}$ when `SignalInjection: TRUE`. |
| `ConfidenceLevel` | `<float>` | Confidence level for the upper limit (default `0.95` for 95% $\text{CL}_s$). |
| `SplusBToys` | `<int>` | Number of signal+background toys per scan step when `LimitType: TOYS` (e.g., `1000`). |
| `BonlyToys` | `<int>` | Number of background-only toys per scan step when `LimitType: TOYS` (e.g., `1000`). |
| `ScanSteps` | `<int>` | Number of $\mu$ grid points scanned in `[ScanMin, ScanMax]` for toy limits (e.g., `20`). |
| `ScanMin` / `ScanMax` | `<float>` | Minimum and maximum POI values for the $\text{CL}_s(\mu)$ scan. |
| `FitStrategy` | `0` \| `1` \| `2` | `Minuit2` strategy during limit fits. |
| `ParamName` | `<string>` | Name of the model parameter (e.g., `"m_Zprime"`) for 1D mass-scan limit plots in `MultiFit`. |
| `ParamValue` | `<float>` | Numerical value of the parameter for this config point (e.g., `1000`). |
| `OutputPrefixName` | `<string>` | Custom prefix for output limit files in `<JobName>/Limits/`. |

---

## 2. `Significance` Block Options (`s` Step)

| Setting | Type / Values | Description |
| :--- | :--- | :--- |
| `Significance: "<name>"` | Block header | Defines the discovery significance ($p_0$) configuration. |
| `SignificanceType` | `ASYMPTOTIC` \| `TOYS` | Method used to compute $p_0$ and $Z$-score. Default: `ASYMPTOTIC`. |
| `SignificanceBlind` | `TRUE` \| `FALSE` | If `TRUE`, masks observed significance and reports expected significance on the Asimov dataset. |
| `POIAsimov` | `<float>` | Signal strength $\mu$ used to generate the S+B Asimov dataset for expected significance (default `1.0`). |
| `BonlyToys` | `<int>` | Number of background-only toys thrown when `SignificanceType: TOYS`. |
| `IncludeStatOnly` | `TRUE` \| `FALSE` | Also evaluates significance with all nuisance parameters fixed (stat-only). |
| `LogX` | `TRUE` \| `FALSE` | Uses logarithmic X-axis in significance scan plots. |

---

## 3. `MultiFit` Block Options (`m` Step, `multiFitSchema.config`)

A `MultiFit` configuration file starts with a `MultiFit: "<name>"` block followed by two or more `ConfigFile: "<id>"` blocks (and optional `Fit` / `Limit` / `Significance` override blocks).

### 3.1 `MultiFit` Header Block Options

| Setting | Type / Values | Description |
| :--- | :--- | :--- |
| `MultiFit: "<name>"` | Block header | Output directory name and identifier for the multi-fit job. |
| `Label` / `CmeLabel` / `LumiLabel` | `<string>` | Experiment label, $\sqrt{s}$, and integrated luminosity displayed on combined plots. |
| `Combine` | `TRUE` \| `FALSE` | If `TRUE`, merges the individual workspaces into a joint likelihood workspace (`mw`) for simultaneous fitting (`mf`), limits (`ml`), significance (`ms`), or ranking (`mr`). |
| `Compare` | `TRUE` \| `FALSE` | Enables comparison plots across the listed `ConfigFile` jobs. |
| `ComparePOI` | `TRUE` \| `FALSE` | Generates a forest plot comparing best-fit POI values ($\hat{\mu} \pm \Delta\mu_{\text{stat}} \pm \Delta\mu_{\text{syst}}$) across channels. |
| `ComparePulls` | `TRUE` \| `FALSE` | Generates side-by-side NP pull and constraint comparison plots across configs (`Pulls/`). |
| `CompareLimits` | `TRUE` \| `FALSE` | Compares upper limits across channels or builds a 1D Brazil-band limit curve vs. `ParamValue`. |
| `CompareUnfolded` | `TRUE` \| `FALSE` | Overlays unfolded distributions from multiple unfolding configs. |
| `POIName` | `<string>` (or list) | Name(s) of the POI(s) to extract and compare (`"mu_signal"`). |
| `POITitle` | `<string>` | X-axis label on the POI comparison plot (e.g., `"#mu_{t#bar{t}H}"`). |
| `POIRange` | `<min>, <max>` | X-axis range on the POI comparison plot (e.g., `-0.5, 2.5`). |
| `POIPrecision` | `<int>` | Number of decimal places shown on the POI comparison plot. |
| `DataName` | `<string>` | Name of the dataset in the individual workspaces (`"obsData"` or `"asimovData"`). |
| `FitType` | `SPLUSB` \| `BONLY` \| `UNFOLDING` | Fit type for the combined fit. |
| `IncludeSysts` | `TRUE` \| `FALSE` | Include systematic uncertainties in the combined fit. |
| `PlotCombCorrMatrix` | `TRUE` \| `FALSE` | Plots the combined nuisance parameter correlation matrix. |
| `CorrelationThreshold` | `<float>` | Minimum correlation $|\rho_{jk}|$ to include an NP in the combined correlation matrix. |
| `UseHesseBeforeMigrad` | `TRUE` \| `FALSE` | Pre-conditions the combined fit step matrix using `HESSE` before `MIGRAD`. |
| `SetRandomInitialNPval` | `<float>` | Randomizes initial NP values in the combined fit to prevent Asimov unit-Hessian failure. |
| `HEPDataFormat` | `TRUE` \| `FALSE` | Exports combined/compared results in HEPData YAML format. |

### 3.2 `ConfigFile` Block Options (Inside a `MultiFit` File)

| Setting | Type / Values | Description |
| :--- | :--- | :--- |
| `ConfigFile: "<id>"` | Block header | Unique identifier for one sub-configuration included in `MultiFit`. |
| `Name` | `<path/to/job.config>` | Path to the individual `TRExFitter` `.config` file. |
| `Label` | `<string>` | Display name for this channel/configuration in comparison plots (e.g., `"1-Lepton Channel"`). |
| `Color` / `Style` | `<int>` | Marker/line color and style for this config in `ComparePulls` and `ComparePOI`. |
| `DecorrSysts` | `<syst1>, <syst2>` | Comma-separated list of systematics (supports wildcards) to decorrelate for this channel during `Combine: TRUE`. |
| `DecorrSuff` | `<string>` | Suffix appended to the decorrelated NP names (e.g., `"_1L"`). |

---

## 4. Complete `MultiFit` Combination & Comparison `.config` Example

```text
MultiFit: "ttH_Combination_Run2"
  Label: "t#bar{t}H Combination"
  CmeLabel: "13 TeV"
  LumiLabel: "140 fb^{-1}"
  Combine: TRUE
  Compare: TRUE
  ComparePOI: TRUE
  ComparePulls: TRUE
  CompareLimits: TRUE
  PlotCombCorrMatrix: TRUE
  CorrelationThreshold: 0.20
  POIName: "mu_ttH"
  POITitle: "#mu_{t#bar{t}H}"
  POIRange: -0.5, 3.0
  POIPrecision: 2
  DataName: "obsData"
  FitType: SPLUSB
  SetRandomInitialNPval: 0.1
  UseHesseBeforeMigrad: TRUE
  HEPDataFormat: TRUE

ConfigFile: "Channel_1L"
  Name: "configs/ttH_1L.config"
  Label: "Single Lepton"
  Color: 2
  DecorrSysts: "ttbar_norm"
  DecorrSuff: "_1L"

ConfigFile: "Channel_2L"
  Name: "configs/ttH_2L.config"
  Label: "Dilepton"
  Color: 4
  DecorrSysts: "ttbar_norm"
  DecorrSuff: "_2L"

ConfigFile: "Channel_Multilepton"
  Name: "configs/ttH_ML.config"
  Label: "Multilepton"
  Color: 8
```
