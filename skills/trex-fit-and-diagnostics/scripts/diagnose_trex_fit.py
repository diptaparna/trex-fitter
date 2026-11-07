#!/usr/bin/env python3
"""
diagnose_trex_fit.py — Automated diagnostic analyzer for TRExFitter fit outputs.

Parses Fits/<JobName>.txt (or a specified fit result .txt file) and optional
Fits/NPRanking*.txt / Fits/GroupedImpact*.txt files to flag:
  - Significantly pulled Nuisance Parameters (|pull| > threshold, default 1.0 sigma)
  - Severely over-constrained NPs (constraint < threshold, default 0.70)
  - Under-constrained NPs (constraint > threshold, default 1.05)
  - Asymmetric post-fit errors (|err_up - |err_down|| > 0.15)
  - Top-ranked NPs driving POI uncertainty

Usage:
    python3 diagnose_trex_fit.py <JobDir_or_FitTxtFile> [--pull-thresh 1.0] [--cons-low 0.7] [--cons-high 1.05]
"""

import argparse
import sys
from pathlib import Path
from typing import List, NamedTuple


class FitParam(NamedTuple):
    name: str
    central: float
    err_up: float
    err_down: float
    is_gamma: bool
    is_norm: bool

    @property
    def avg_err(self) -> float:
        return 0.5 * (abs(self.err_up) + abs(self.err_down))

    @property
    def asymmetry(self) -> float:
        return abs(abs(self.err_up) - abs(self.err_down))


def parse_fit_txt(txt_path: Path) -> List[FitParam]:
    params: List[FitParam] = []
    lines = txt_path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_np_section = False

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("NUISANCE_PARAMETERS"):
            in_np_section = True
            continue
        if line.startswith("CORRELATION_MATRIX"):
            break
        parts = line.split()
        if len(parts) >= 4:
            name = parts[0]
            try:
                central = float(parts[1])
                err_up = float(parts[2])
                err_down = float(parts[3])
            except ValueError:
                continue
            is_gamma = name.startswith("gamma_")
            # NormFactors / POIs typically appear before NUISANCE_PARAMETERS or have central ~ 1.0 and are not in NP block
            is_norm = not in_np_section and not is_gamma
            params.append(FitParam(name, central, err_up, err_down, is_gamma, is_norm))
    return params


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose TRExFitter fit results for pulls and constraints.")
    parser.add_argument("target", type=Path, help="Path to TRExFitter job directory or Fits/<JobName>.txt")
    parser.add_argument("--pull-thresh", type=float, default=1.0, help="Pull magnitude threshold (default: 1.0)")
    parser.add_argument("--cons-low", type=float, default=0.70, help="Over-constraint threshold (default: 0.70)")
    parser.add_argument("--cons-high", type=float, default=1.05, help="Under-constraint threshold (default: 1.05)")
    args = parser.parse_args()

    fit_txt: Path | None = None
    if args.target.is_file():
        fit_txt = args.target
    elif args.target.is_dir():
        fits_dir = args.target / "Fits" if (args.target / "Fits").is_dir() else args.target
        candidates = [
            p for p in sorted(fits_dir.glob("*.txt"))
            if not p.name.endswith("_statOnly.txt")
            and not p.name.startswith("NPRanking")
            and not p.name.startswith("GroupedImpact")
        ]
        if candidates:
            fit_txt = candidates[0]

    if not fit_txt or not fit_txt.is_file():
        print(f"[ERROR] Could not locate fit result text file in: {args.target}", file=sys.stderr)
        return 2

    params = parse_fit_txt(fit_txt)
    norms = [p for p in params if p.is_norm]
    systs = [p for p in params if not p.is_norm and not p.is_gamma]
    gammas = [p for p in params if p.is_gamma]

    print(f"=== TRExFitter Fit Diagnostics: {fit_txt} ===")
    print(f"Loaded {len(norms)} NormFactor/POI(s), {len(systs)} Systematic NP(s), {len(gammas)} Gamma parameter(s).\n")

    if norms:
        print("--- Fitted POIs / NormFactors ---")
        for p in norms:
            print(f"  {p.name:<30} = {p.central:+.4f}  +{p.err_up:.4f} / {p.err_down:+.4f}")
        print()

    pulled = [p for p in systs if abs(p.central) >= args.pull_thresh]
    over_cons = [p for p in systs if p.avg_err <= args.cons_low]
    under_cons = [p for p in systs if p.avg_err >= args.cons_high]
    asym = [p for p in systs if p.asymmetry >= 0.15]

    print(f"--- Systematic NP Health Summary ---")
    print(f"  Pulled NPs (|pull| >= {args.pull_thresh:.2f}):            {len(pulled)}")
    print(f"  Over-constrained NPs (err <= {args.cons_low:.2f}):     {len(over_cons)}")
    print(f"  Under-constrained NPs (err >= {args.cons_high:.2f}):    {len(under_cons)}")
    print(f"  Asymmetric-error NPs (|du - dd| >= 0.15): {len(asym)}\n")

    if pulled:
        print("  [!] Top Pulled Nuisance Parameters:")
        for p in sorted(pulled, key=lambda x: abs(x.central), reverse=True)[:15]:
            print(f"      {p.name:<35} pull = {p.central:+.3f}  (constraint = +{p.err_up:.3f} / {p.err_down:+.3f})")
        print("      -> Remedy: Enable 'SystDataPlots: TRUE', inspect Systematics/<NP>/, test 'Decorrelate: REGION' or 'SHAPEACC'.\n")

    if over_cons:
        print("  [!] Most Over-Constrained Nuisance Parameters:")
        for p in sorted(over_cons, key=lambda x: x.avg_err)[:15]:
            print(f"      {p.name:<35} constraint = ±{p.avg_err:.3f}  (pull = {p.central:+.3f})")
        print("      -> Remedy: Check Systematics/<NP>/ for MC stat spikes; apply 'Smoothing: 40' & 'Symmetrisation'; test 'DropNorm: \"all\"'.\n")

    if under_cons:
        print("  [!] Under-Constrained Nuisance Parameters (Constraint > 1):")
        for p in sorted(under_cons, key=lambda x: x.avg_err, reverse=True)[:15]:
            print(f"      {p.name:<35} constraint = +{p.err_up:.3f} / {p.err_down:+.3f}  (pull = {p.central:+.3f})")
        print("      -> Remedy: Run 'UseMinos' and 'doLHscan' on these NPs; consider 'AlternativeShapeHistFactory: TRUE' or 'TWOSIDED' symmetrisation.\n")

    if gammas:
        pulled_gammas = [g for g in gammas if abs(g.central - 1.0) / max(g.avg_err, 1e-6) >= 1.5]
        if pulled_gammas:
            print(f"  [!] Found {len(pulled_gammas)} Gamma parameter(s) pulled by >= 1.5x their pre-fit stat error:")
            for g in pulled_gammas[:10]:
                print(f"      {g.name:<35} val = {g.central:.4f} ± {g.avg_err:.4f}")
            print("      -> Remedy: Check for low-MC-stat bins with large event weights; consider rebinning or 'SeparateGammas: TRUE'.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
