# TRExFitter

<p align="center">
  <img src="assets/TRExFitter_logo.png" alt="TRExFitter Logo" width="320"/>
</p>

Build, validate, run, and diagnose **HistFactory / xRooFit binned profile likelihood fits** in High Energy Physics (HEP) using [`TRExFitter`](https://gitlab.cern.ch/TRExStats/TRExFitter).

## Overview

`TRExFitter` (originally developed as `TtHFitter` in the ATLAS Collaboration) is the workhorse statistical inference framework used across ~45% of ATLAS analyses—spanning $t\bar{t}H$, four-top ($t\bar{t}t\bar{t}$), top-quark mass ($m_t$) and cross-section measurements, multiboson ($WW\gamma$, VBS) observations, Standard Model Effective Field Theory (SMEFT) interpretations, and exotic BSM searches (leptoquarks, heavy $W'/Z'$, vector-like quarks).

This plugin equips Antigravity agents with deep domain knowledge of HistFactory statistical models, `TRExFitter` configuration schemas (`jobSchema.config` and `multiFitSchema.config`), command-line workflows, and practical HEP fitting methodologies distilled from ATLAS publications and PhD theses.

## Installation

### From GitHub (Antigravity CLI)

```bash
agy plugin install https://github.com/diptaparna/trex-fitter
```

### From a Local Clone

```bash
git clone https://github.com/diptaparna/trex-fitter.git
agy plugin validate --strict ./trex-fitter
agy plugin install ./trex-fitter
```

## Included Skills & Slash Commands

| Skill / Slash Command | Directory | Focus Area |
| :--- | :--- | :--- |
| **`trex-fitter`** (`/trex-fitter`, alias **`/trf`**) | `skills/trex-fitter/` & `skills/trf/` | Master entry point: statistical model formulation ($\mathcal{L}(\mu, \boldsymbol{\theta}, \boldsymbol{\gamma})$), environment setup (`StatAnalysis`, Apptainer/Docker), CLI action steps (`u`/`n`/`h`/`b`/`w`/`f`/`d`/`p`/`r`/`i`/`l`/`s`/`m`/`x`/`a`), and workflow orchestration. |
| **`trex-config-and-inputs`** (`/trex-config-and-inputs`) | `skills/trex-config-and-inputs/` | Configuration file syntax, `Job`/`Region`/`Sample`/`NormFactor`/`ShapeFactor` blocks, `HIST` vs `NTUP` (and `FastFrames`) inputs, `AutoBin` (`TransfoD`, `TransfoF`, `TransfoJ`), blinding strategies, data-driven backgrounds (`GHOST`, `NormalizedByTheory: FALSE`), `Expression` re-parameterizations, and `hupdate.exe`. Includes `scripts/validate_trex_config.py`. |
| **`trex-systematics-and-gammas`** (`/trex-systematics-and-gammas`) | `skills/trex-systematics-and-gammas/` | Systematic uncertainties (`HISTO`, `OVERALL`, `SHAPE`), HistFactory modifiers (`OverallSys`, `HistoSys`, `ShapeSys`), interpolation codes (`IntCodeOverall`/`IntCodeShape`), symmetrisation (`ONESIDED`, `TWOSIDED`, `ABSMEAN`, `MAXIMUM`, `AlternativeShapeHistFactory`), smoothing algorithms (`MAXVARIATION`, `TTBARRESONANCE`, `COMMONTOOLSMOOTHMONOTONIC`, `COMMONTOOLSMOOTHPARABOLIC`, kernel methods), pruning (`SystPruningShape`, `SystPruningNorm`, `SystLarge`, `PruningType`), two-point generator systematics (`ReferenceSample`, `SubtractRefSampleVar`), envelopes (`CombineName`/`CombineType`), decorrelation (`Decorrelate`, `DropNorm`, `DropShapeIn`), and Barlow-Beeston MC stat `gamma` NPs (`SeparateGammas`, `CorrelateGammasWithSample`, negative bin handling, `Bootstrap`). |
| **`trex-fit-and-diagnostics`** (`/trex-fit-and-diagnostics`) | `skills/trex-fit-and-diagnostics/` | Profile likelihood minimization (`SPLUSB`, `BONLY`), Asimov & mixed data/Asimov fits, diagnosing HEP fit problems (Asimov unit-Hessian non-convergence, over-constraints $\Delta\hat{\theta} < 1$, under-constraints $>1$, spurious NP pulls, large correlations, non-smooth NLL scans), MINOS & 1D/2D likelihood scans, Saturated Model Goodness-of-Fit, NP ranking (`r` step), and Grouped Impact (`i` step). Includes `scripts/diagnose_trex_fit.py`. |
| **`trex-unfolding-and-morphing`** (`/trex-unfolding-and-morphing`) | `skills/trex-unfolding-and-morphing/` | Profile Likelihood Unfolding (`FitType: UNFOLDING`, `Unfolding`, `TruthSample`, `UnfoldingSample`, `UnfoldingSystematic`, response/migration matrices, normalized differential cross-sections, Tikhonov regularization `Tau`) and Template Morphing (`Morphing`, continuous POI interpolation `LINEAR`/`SMOOTHLINEAR`/`SQUAREROOT`, closure/linearity calibration). |
| **`trex-limits-significance-multifit`** (`/trex-limits-significance-multifit`) | `skills/trex-limits-significance-multifit/` | $\text{CL}_s$ exclusion limits (`l` step, `ASYMPTOTIC` & `TOYS`, signal injection, parameter scans), discovery significance (`s` step, $p_0$ and $Z$-score), `MultiFit` (`m` step) workspace combinations and cross-fit comparisons, and publication outputs (`HEPDataFormat`, `UheppFormat`, `CombinerFormat`, `UseATLASRounding`). |

## Bundled Helper Scripts

- `skills/trex-config-and-inputs/scripts/validate_trex_config.py`: Static validator for `TRExFitter` `.config` and `MultiFit` files (checks schema blocks, `ReferenceSample` `GHOST` references, `Morphing` nominal templates, `UNFOLDING` pruning settings, and Asimov Hessian pre-conditioning).
- `skills/trex-fit-and-diagnostics/scripts/diagnose_trex_fit.py`: Automated parser for `<JobName>/Fits/*.txt` that flags nuisance parameter pulls ($|\hat{\theta}| \ge \text{threshold}$), over-constraints ($\Delta\hat{\theta} < 0.70$), under-constraints ($\Delta\hat{\theta} > 1.05$), and abnormal `gamma` bin stat factors.
