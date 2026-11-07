---
name: trex-config-and-inputs
description: Author, structure, and validate TRExFitter configuration files (.config), input pipelines (ReadFrom HIST or NTUP, FastFrames integration, hupdate.exe), Region definitions, automatic binning algorithms (AutoBin TransfoD, TransfoF, TransfoJ), blinding strategies, Sample blocks (SIGNAL, BACKGROUND, DATA, GHOST, data-driven templates), NormFactor (including Expression re-parameterizations), and ShapeFactor blocks. Use when creating or modifying a TRExFitter config or setting up input histograms/ntuples.
---

# TRExFitter Configuration Architecture & Input Pipelines

Every single-fit `TRExFitter` job is driven by a plain-text `.config` file validated at startup against `jobSchema.config` (or `multiFitSchema.config` for `m` jobs).

For exhaustive block-by-block settings, consult [`references/config_blocks_reference.md`](references/config_blocks_reference.md).
To lint and validate any `.config` file before running `trex-fitter`, run:
```bash
python3 scripts/validate_trex_config.py path/to/myFit.config
```

---

## 1. Syntax Rules & Mandatory Block Structure

A `TRExFitter` `.config` file consists of blocks separated by **at least one blank line**:
```yaml
<ObjectType>: "<ObjectName>"
  <Property1>: <Value1>
  <Property2>: <Value2>

<ObjectType>: "<AnotherObjectName>"
  <Property1>: <Value1>
```

### Critical Syntax Invariants
1. **Blank lines between blocks are mandatory.** Omitting a blank line between two blocks merges the second block's settings into the first block or triggers a schema error.
2. **Unique `<ObjectName>` per block type.** Every `Region`, `Sample`, `NormFactor`, `ShapeFactor`, and `Systematic` must have a unique identifier (avoid spaces in `<ObjectName>`; use `Title` or `Label` for human-readable strings).
3. **Comments** start with `%` or `#` (in `.config` files, `%` is the traditional comment character; `%%%` is commonly used for section headers).
4. **Required blocks for a standard fit:**
   - Exactly 1 `Job` block
   - Exactly 1 `Fit` block
   - At least 1 `Region` block
   - At least 1 `Sample` block
   - Optional: `Limit`, `Significance`, `Options`, `Morphing`, `Unfolding`, and any number of `NormFactor`, `ShapeFactor`, `Systematic`, `TruthSample`, `UnfoldingSample`, `UnfoldingSystematic` blocks.

---

## 2. Input Pipelines: `ReadFrom: HIST` vs. `ReadFrom: NTUP`

### A. Histogram Inputs (`ReadFrom: HIST` — Recommended for Large Analyses / `FastFrames`)
In modern ATLAS Run 2 & Run 3 analyses, event loop processing from columnar ntuples (`RDataFrame` via [`FastFrames`](https://gitlab.cern.ch/atlas-amglab/fastframes)) is decoupled from the statistical fit. `FastFrames` produces histogram ROOT files that `TRExFitter` ingests via the `h` step.

How `TRExFitter` resolves a histogram path:
- **File path**: `<HistoPath>/<HistoPathSuff>/<HistoFile><HistoFileSuff>.root`
- **Histogram name inside ROOT file**: `<HistoName><HistoNameSuff>` (or `<HistoNameNominal>` for nominal when systematics replace the nominal suffix).
- Hierarchy of overrides: `Job` -> `Region` -> `Sample` -> `Systematic`.

```yaml
Job: "ttH_Multilepton"
  ReadFrom: HIST
  HistoPath: "/eos/atlas/user/a/analyst/histograms"
  UseFolderStructure: TRUE
  SplitHistoFiles: TRUE
  MergeUnderOverFlow: FALSE % Default is FALSE for HIST, TRUE for NTUP! Set TRUE if overflow events should enter the last bin.
  CorrectNormForNegativeIntegral: FALSE
  GuessMCStatEmptyBins: TRUE
```

### B. Ntuple Inputs (`ReadFrom: NTUP`)
`TRExFitter` reads `TTree` branches directly during the `n` step using `TTree::Draw` / `RDataFrame`-style expressions:
- **Tree path**: `<NtuplePath>/<NtuplePathSuff>/<NtupleFile><NtupleFileSuff>.root` -> tree `<NtupleName><NtupleNameSuff>`
- **Selection**: Logical `&&` of `Job->Selection`, `Region->Selection`, and `Sample->Selection` (unless `Sample->IgnoreSelection: TRUE`).
- **Event weight (`MCweight`)**: Product `(` `Job->MCweight` `) * (` `Region->MCweight` `) * (` `Sample->MCweight` `)` multiplied by `Lumi * LumiScale` (for samples with `NormalizedByTheory: TRUE`, the default).
- **Custom C++ functions & aliases**:
  - `AddAliases: "ht_ratio:HT_all/1e3;m_ll:invMass(lep_pt,lep_eta)"` prevents `TTreeFormula` buffer overflows on long expressions.
  - `CustomFunctions: "util/myReweight.C"` loads custom ROOT macros before `n` runs.
  - `UseFriend: TRUE` and `FriendPath: "/path/to/friends"` attaches friend trees (e.g., GNN/BDT scores evaluated in a separate step).

### C. Parallel Input Processing & `hupdate.exe`
When `n` or `h` is slow across hundreds of systematics and regions:
1. Set `SplitHistoFiles: TRUE` in `Job`.
2. Run batch jobs filtering by `Regions=...` and `Systematics=...` with `SaveSuffix=_batch1`.
3. Merge partial histogram ROOT files into `<JobName>_<Region>_histos.root` using `hupdate.exe` (or `Update=TRUE` on sequential runs), then run `trex-fitter bwf <config>`.

---

## 3. Designing `Region` Blocks & Automatic Binning (`AutoBin`)

### Region Types (`Type`)
- `SIGNAL`: Enters the fit when `FitRegion: CRSR` (default); excluded when `FitRegion: CRONLY`.
- `CONTROL`: Enters the fit under both `CRSR` and `CRONLY`. Designed to be signal-depleted and enriched in a specific background to constrain its normalization (`NormFactor`) and nuisance parameters in situ.
- `VALIDATION`: **Never** enters the likelihood fit. Used strictly to verify that post-fit normalizations and NP pulls extrapolated from CRs properly describe data in an intermediate phase space.

### Automatic Binning Transformations (`TransfoD`, `TransfoF`, `TransfoJ`)
In HEP searches and measurements fitting a multivariate classifier (BDT, DNN, Transformer, GNN) output score $x \in [0, 1]$, uniform binning causes empty high-score bins (breaking asymptotic assumptions and creating large MC statistical fluctuations) and overly coarse bins at low scores. `TRExFitter` provides `AutoBin` transformations (widely used in ATLAS $t\bar{t}H$, $4t$, FCNC, and leptoquark analyses):

```yaml
Region: "SR_2lSS"
  Type: SIGNAL
  Variable: "gnn_score"
  Binning: "AutoBin","TransfoD",10.,10.
```

- **`TransfoD` (with parameters $z_b, z_s$)**:
  Starts from a finely binned histogram (e.g., 1000 bins during `n` or fine input `HIST`) and iteratively merges adjacent fine bins starting from the background-rich (low-score) end until the cumulative metric
  $$Z = z_b \frac{n_b}{N_b} + z_s \frac{n_s}{N_s} \ge 1$$
  where $n_b, n_s$ are the background and signal yields in the current merged bin, and $N_b, N_s$ are the total background and signal yields in the region.
  - Total number of resulting bins is $N_{\text{bins}} = z_b + z_s$.
  - Setting $z_b = 0$ produces flat signal bins; setting $z_s = 0$ produces flat background bins.
  - Setting $z_b = z_s$ (e.g., `5.,5.` for 10 bins or `10.,10.` for 20 bins) balances background statistical precision at low score with fine signal resolution in the high-score tail.
  - **Intricacy in Control Regions**: If `TransfoD` is used in a `CONTROL` region where signal is negligible and $z_s \neq 0$, append the name(s) of the target background sample(s) to act as the "signal" proxy: `Binning: "AutoBin","TransfoD",5.,5.,"ttbar_bb"`.
- **`TransfoF` and `TransfoJ`**: Alternative transformations controlling maximum relative MC statistical uncertainty per bin (`TransfoErr`, default `0.1`).
- **`Rebinning` vs. `Binning`**:
  - `Binning` defines the bin edges created during `n`/`h`. Changing `Binning` requires re-running `n` or `h`.
  - `Rebinning: 0,50,100,200,500` merges existing bins during the `b` step (`TH1::Rebin`), allowing fast binning optimization (`trex-fitter bwf`) without re-running `n`/`h`.

---

## 4. Blinding Strategies in HEP Analyses

ATLAS analyses enforce strict blinding protocols until background modeling and fit stability are signed off on Asimov and CR-only fits. `TRExFitter` offers four distinct blinding mechanisms—**know which ones affect the likelihood vs. plots only**:

| Setting | Block | Affects Fit Likelihood? | Behavior & Use Case |
| :--- | :--- | :---: | :--- |
| **`BlindingThreshold: 0.05`** + **`BlindingType: SOVERB`** | `Job` / `Region` | **NO** (Plots only!) | Masks data points in pre-fit/post-fit plots for bins where $S/B$ (or `SOVERSPLUSB`, `SOVERSQRTB`, `SOVERSQRTSPLUSB`) exceeds threshold. **Warning**: Data in those bins are STILL used in the fit unless combined with `AutomaticDropBins: TRUE` or `BlindSRs: TRUE`! |
| **`AutomaticDropBins: TRUE`** or **`DropBins: 8,9,10`** | `Region` | **YES** | Sets both data and prediction yields to `0` in bins above `BlindingThreshold` (or in listed 1-indexed bins). Used to perform a "partial unblinding" or background-only fit in low-$S/B$ bins of an SR. |
| **`FitBlind: TRUE`** | `Fit` | **YES** | Forces the fit across **all** regions to use an Asimov dataset built from pre-fit nominal MC (or shifted by `POIAsimov` / `NPValues`). |
| **`DataType: ASIMOV`** (or **`BlindSRs: TRUE`**) | `Region` (`Job`) | **YES** (Hybrid / Mixed Fit) | When CRs have `DataType: DATA` and SRs have `DataType: ASIMOV`, `TRExFitter` performs a **Mixed Fit**: it fits real data in the CRs first, projects the post-fit nuisance parameters and background normalizations into the SRs to construct a **post-CR conditioned Asimov dataset** in the SRs, and then evaluates expected limits/significances/uncertainties. (Requires `NPValues` NOT to be set). |
| **`BlindedParameters: "mu_sig"`** | `Fit` | **NO** (Console/Text Obfuscation) | Writes the fitted value of the specified POI/NPs as a hexadecimal string and suppresses Minuit console output so analysts can fit real data to inspect NP pulls, constraints, and post-fit background shapes without seeing the extracted POI value (standard in precision measurements like top-quark mass $m_t$). |
| **`RandomNFscale: "mu_topWidth:0.8:1.2"`** | `Region` | **NO** (Pre-fit plots) | Multiplies the POI by a hidden random scale factor on pre-fit plots. |

---

## 5. `Sample`, `NormFactor`, and `ShapeFactor` Patterns

### A. Data-Driven Backgrounds & `GHOST` Samples
- **Data-driven templates** (e.g., multijet / fake leptons via Matrix Method or ABCD):
  Always set `NormalizedByTheory: FALSE` so `TRExFitter` does **not** multiply the sample by `Lumi`, `LumiScale`, or `Job->MCweight`.
- **Template arithmetic with `GHOST` samples**:
  A `Sample` with `Type: GHOST` is never drawn on plots, has no systematics by default (unless `UseSystematics: TRUE`), and is not added to the `RooWorkspace`. It serves as an auxiliary building block for:
  1. **ABCD / Transfer-Factor Data-Driven Estimates**: Create `GHOST` samples for data and MC prompt backgrounds in a loose/anti-ID region, use `SubtractSample` to get `Data - MC_prompt`, and `MultiplyBy` / `DivideBy` to apply a transfer factor bin-by-bin.
  2. **Two-point generator systematics (`ReferenceSample`)**: E.g., comparing `AFII` (FastSim)Herwig7 to `AFII` Powheg+Pythia8 while applying the relative difference to a `FullSim` nominal sample.
  3. **Custom Asimov Datasets (`AsimovReplacementFor`)**: Define an alternative hypothesis (e.g., BSM EFT point or alternative $t\bar{t}+\text{HF}$ generator) as a `GHOST` sample with `AsimovReplacementFor: "customAsimovName","nominalSampleName"` and set `CustomAsimov: "customAsimovName"` in `Job`.

### B. `NormFactor` & Non-Linear `Expression` Parameterizations
A `NormFactor` multiplies specified samples/regions by an unconstrained parameter:
```yaml
NormFactor: "mu_XS_ttH"
  Title: "#mu(t#bar{t}H)"
  Nominal: 1.0
  Min: -5.0
  Max: 10.0
  Samples: "ttH"
```
- **Correlating or re-parameterizing `NormFactor`s via `Expression`**:
  Used for SMEFT quadratic Wilson coefficient parameterizations ($\mu(\mathbf{c}) = 1 + \sum_i A_i c_i + \sum_{i \le j} B_{ij} c_i c_j$), polarization fractions, or total-cross-section vs. branching-ratio fits:
  ```yaml
  NormFactor: "nf_eft_bin1"
    Samples: "ttZ_bin1"
    Expression: "(1.0 + 0.14*ctZ + 0.08*ctZ*ctZ):ctZ[0.0,-5.0,5.0]"
  ```
  Here `ctZ` becomes the free parameter in the `RooWorkspace` (`AddPreprocessFunction`), and `ScaleHistosForPruning: TRUE` in `Job` ensures pruning uses the evaluated expression scale.

### C. `ShapeFactor`
Creates an unconstrained free normalization parameter **in every individual bin** of the specified `Regions` and `Samples`. Used for fully data-driven bin-by-bin background extraction across sidebands/control regions shareable with a signal region.

---

## 6. Validating Configurations with `validate_trex_config.py`

Always run the bundled validator script after drafting or editing a `.config` file:
```bash
python3 scripts/validate_trex_config.py path/to/config.config
```
It checks block separation, required blocks (`Job`, `Fit`, `Region`, `Sample`), POI-to-`NormFactor` linkage, `ReferenceSample` / `AsimovReplacementFor` existence, `MergeUnderOverFlow` consistency with `ReadFrom`, and blinding configuration safety.
