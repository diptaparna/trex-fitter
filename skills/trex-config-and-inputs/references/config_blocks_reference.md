# TRExFitter Configuration Blocks Quick Reference

## 1. `Job` Block Settings

| Category | Setting | Values / Default | Notes |
| :--- | :--- | :--- | :--- |
| **Core** | `Label` | String or `NONE` | Label displayed on plots. |
| | `POI` | Comma-separated strings | Name(s) of the Parameter(s) of Interest (must match `NormFactor` or `Morphing` parameter names). |
| | `ReadFrom` | `HIST` (default) or `NTUP` | Input mode (`h` step vs `n` step). |
| | `Lumi` | Float | Integrated luminosity scaling applied to all `NormalizedByTheory: TRUE` samples. |
| | `LumiScale` | Float | Additional post-creation scale factor. |
| | `DebugLevel` | `0`, `1`, `2`, `>2` | `<2` suppresses verbose `RooFit`/`RooStats` messages; `>=2` enables detailed debug logs. |
| **Paths** | `HistoPath(s)`, `HistoFile(s)`, `HistoName(s)`, `HistoNameNominal` | Strings | Base paths/names for `ReadFrom: HIST`. |
| | `NtuplePath(s)`, `NtupleFile(s)`, `NtupleName(s)`, `MCweight`, `Selection` | Strings | Base paths/trees/weights/cuts for `ReadFrom: NTUP`. |
| | `UseFriend`, `FriendPath(s)` | `TRUE`/`FALSE`, Strings | Attach ROOT friend trees during `n`. |
| | `OutputDir`, `InputFolder`, `InputName`, `Suffix`, `SaveSuffix` | Strings | Customize input/output directory and file suffixes. |
| | `SplitHistoFiles` | `TRUE` / `FALSE` | Store one histogram file per `Region` (`<Job>_<Region>_histos.root`). Essential for parallel `n`/`h`/`b`. |
| | `UseFolderStructure` | `TRUE` (default) / `FALSE` | Organize histograms inside `.root` files as `<Region>/<Sample>/<Systematic>`. |
| **Histograms & Stat** | `MergeUnderOverFlow` | `TRUE` / `FALSE` | Default is `FALSE` for `HIST` and `TRUE` for `NTUP`. |
| | `CorrectNormForNegativeIntegral` | `FALSE` (default) / `TRUE` | Negative bins are floored to `1e-6` and positive bins rescaled to preserve integral. |
| | `GuessMCStatEmptyBins` | `TRUE` (default) / `FALSE` | Assigns smallest non-zero stat error in histogram to empty/floored bins (or 100% of `1e-6` if `FALSE`). |
| | `MCstatThreshold` | Float or `NONE` | Relative bin MC stat threshold above which a Barlow-Beeston $\gamma$ NP is created (default: all bins). |
| | `MCstatConstraint` | `POISSON` (default) / `GAUSSIAN` | Constraint term for $\gamma$ NPs. |
| | `HistoChecks` | `NOCRASH` | Downgrades missing input histogram crashes to warnings. |
| **Pruning & Smoothing** | `SmoothingOption` | `MAXVARIATION` (default), `TTBARRESONANCE`, `COMMONTOOLSMOOTHMONOTONIC`, `COMMONTOOLSMOOTHPARABOLIC`, `TCHANNEL`, `KERNELRATIOUNIFORM`, `KERNELDELTAGAUSS`, `KERNELRATIOGAUSS` | Global default smoothing algorithm for systematics with `Smoothing` enabled. |
| | `PruningType` | `SEPARATESAMPLE` (default), `BACKGROUNDREFERENCE`, `COMBINEDREFERENCE`, `COMBINEDSIGNAL` | Reference yield denominator used for `SystPruningShape` and `SystPruningNorm`. |
| | `SystPruningShape` | Float (e.g. `0.01`) | Prune shape component if variation is below threshold (e.g. 1%). |
| | `SystPruningNorm` | Float (e.g. `0.005`) | Prune normalization component if yield variation is below threshold (e.g. 0.5%). |
| | `SystLarge` | Float (e.g. `0.40`) | Threshold to flag or remove (if `RemoveLargeSyst: TRUE`) pathologically large variations. |
| | `PruningShapeOption` | `MAXBIN` (default) / `KSTEST` | Criterion for shape pruning. |
| | `KeepPruning` | `TRUE` / `FALSE` | Save and reuse `Pruning.root`. |
| **Blinding** | `BlindingThreshold`, `BlindingType` | Float, `SOVERB` / `SOVERSPLUSB` / `SOVERSQRTB` / `SOVERSQRTSPLUSB` | Blind data points in plots above threshold (does NOT blind the fit!). |
| | `BlindSRs` | `TRUE` / `FALSE` | Force `DataType: ASIMOV` on all `SIGNAL` regions (impacts fit!). |
| **Plotting & Formats** | `PlotOptions` | `YIELDS`, `NORMSIG`, `NOSIG`, `SKIPSIG`, `OVERSIG`, `CHI2`, `PREFITONPOSTFIT`, `NOXERR`, `POISSONIZE`, `NORATIO` | Comma-separated plotting flags. |
| | `GetChi2` | `TRUE` (`STAT+SYST`) / `STAT` | Compute extended $\chi^2/\text{ndf}$ and probability on `d` and `p` plots. |
| | `SystControlPlots`, `SystDataPlots` | `TRUE` / `FALSE` | Generate shape/ratio plots in `Systematics/` before/after smoothing & symmetrisation. |
| | `CorrelationThreshold` | Float (e.g. `0.20`) | Only include NPs with $|\rho_{ij}| \ge \text{threshold}$ in `CorrMatrix.pdf`. |
| | `HEPDataFormat`, `UheppFormat`, `CombinerFormat` | `TRUE` / `FALSE` | Export HEPData YAML, `uhepp` JSON/YAML plots, or ATLAS Combiner inputs. |
| | `UseATLASRounding` | `TRUE` / `FALSE` | Apply PDG/ATLAS rounding rules to `.txt` and `.tex` yield tables. |

---

## 2. `Region` Block Settings

| Setting | Values / Default | Notes |
| :--- | :--- | :--- |
| `Type` | `SIGNAL` (default), `CONTROL`, `VALIDATION` | Role of region in likelihood fit. |
| `DataType` | `DATA` (default), `ASIMOV` | Setting `ASIMOV` on SRs and `DATA` on CRs triggers a conditioned **Mixed Fit**. |
| `Variable`, `Selection`, `MCweight`, `NtupleName(s)`, `NtupleFile(s)`, `NtuplePathSuff(s)` | Strings | `NTUP`-specific variable expression, cut string, weight, and tree location. |
| `VariableForSample` | `sample1:var1,sample2:var2` | Override `Variable` for specific samples (e.g. TRF b-tagging or data-driven variables). |
| `HistoFile(s)`, `HistoName(s)`, `HistoPathSuff(s)` | Strings | `HIST`-specific histogram path/name overrides. |
| `Binning` | Comma-separated floats or `"AutoBin","TransfoD",zB,zS` | Applied during `n`/`h` histogram creation. |
| `Rebin` / `Rebinning` | Int / Comma-separated floats | Applied during `b` step (`TH1::Rebin`) without re-reading inputs. |
| `DropBins` / `AutomaticDropBins` | `1,2,...` / `TRUE`/`FALSE` | Zero out specified 1-indexed bins (or bins above `BlindingThreshold`) in both data and MC. |
| `IsBinOfRegion` | `"ValRegionName":binIndex` | 2D fit smoothing propagation from a `VALIDATION` region bin. |
| `NumberOfRecoBins` | Int | Mandatory in `UNFOLDING` fits for detector-level regions. |

---

## 3. `Sample` Block Settings

| Setting | Values / Default | Notes |
| :--- | :--- | :--- |
| `Type` | `BACKGROUND` (default), `SIGNAL`, `DATA`, `GHOST` | Sample role. `GHOST` is not drawn or added to workspace. |
| `Title`, `TexTitle`, `Group` | Strings | Legend and table labels; `Group` merges multiple `Sample` blocks into one visual legend entry. |
| `FillColor`, `LineColor`, `FillColorRGB`, `LineColorRGB` | ROOT color int or `R,G,B` | Visual styling. |
| `NormalizedByTheory` | `TRUE` (default) / `FALSE` | Set `FALSE` for data-driven backgrounds to ignore `Lumi`, `LumiScale`, and `Job->MCweight`. |
| `Regions`, `Exclude` | Comma-separated region names | Restrict where this sample is active. |
| `LumiScale(s)` | Float(s) | Constant scale factor (e.g. $k$-factor or branching ratio) applied to the sample. |
| `NormFactor` | `"name",nom,min,max` | Inline shortcut to attach a `NormFactor` to this sample. |
| `UseMCstat` | `TRUE` (default) / `FALSE` | Set `FALSE` to disable MC statistical uncertainties on this sample (e.g. analytic/data-driven template). |
| `SeparateGammas` | `FALSE` (default) / `TRUE` | Give this sample its own bin-by-bin `ShapeSys` MC stat NPs instead of merging into shared bin $\gamma$. Requires running `b` step! |
| `CorrelateGammasInRegions`, `CorrelateGammasWithSample` | Strings | Used with `SeparateGammas: TRUE` to correlate MC stat NPs across regions or reweighted samples. |
| `MultiplyBy`, `DivideBy`, `AddSample(s)`, `SubtractSample(s)` | Sample name(s) | Bin-by-bin histogram algebra (often referencing `GHOST` samples). |
| `AsimovReplacementFor` | `"datasetName","targetSample"` | On a `GHOST` sample: replaces `targetSample` when `CustomAsimov: "datasetName"` is set in `Job`. |
| `Morphing` | `"paramName",value` | Declares this sample as a discrete template at `value` for continuous parameter `paramName`. |
| `SystFromSample` | `TRUE` / `FALSE` | Inherit systematic relative variations from another sample. |
| `BuildPullTable` | `TRUE`, `NORM-ONLY`, `NORM+SHAPE` | Produce post-fit acceptance impact table for this sample. |
