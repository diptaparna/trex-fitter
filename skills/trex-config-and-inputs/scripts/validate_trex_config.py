#!/usr/bin/env python3
"""
validate_trex_config.py — Static validator and HEP best-practice linter for TRExFitter .config files.

Usage:
    python3 validate_trex_config.py <path/to/file.config> [--multi]
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


VALID_SINGLE_BLOCKS = {
    "Job", "Fit", "Limit", "Significance", "Options",
    "Region", "Sample", "NormFactor", "ShapeFactor",
    "Systematic", "Morphing", "Unfolding", "TruthSample",
    "UnfoldingSample", "UnfoldingSystematic",
}

VALID_MULTI_BLOCKS = {
    "MultiFit", "Fit", "Limit", "Significance", "Options",
}


class Block:
    def __init__(self, block_type: str, name: str, line_no: int):
        self.block_type = block_type
        self.name = name.strip().strip('"').strip("'")
        self.line_no = line_no
        self.props: List[Tuple[str, str, int]] = []

    def get(self, key: str, default: str = "") -> str:
        for k, v, _ in self.props:
            if k.lower() == key.lower():
                return v.strip().strip('"').strip("'")
        return default

    def has(self, key: str) -> bool:
        return any(k.lower() == key.lower() for k, _, _ in self.props)


def strip_comment(line: str) -> str:
    """Remove unquoted % or # comments (preserving # inside quotes like #mu or #bar{t})."""
    in_quote = False
    quote_char = ""
    for i, ch in enumerate(line):
        if ch in ('"', "'"):
            if not in_quote:
                in_quote = True
                quote_char = ch
            elif quote_char == ch:
                in_quote = False
        elif not in_quote and ch == "%":
            return line[:i]
    return line


def parse_config(path: Path) -> Tuple[List[Block], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    blocks: List[Block] = []

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    current_block: Block | None = None
    saw_blank_since_last_prop = True

    block_header_re = re.compile(r"^\s*([A-Za-z]+)\s*:\s*(.+?)\s*$")
    prop_re = re.compile(r"^\s*([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$")

    for idx, raw_line in enumerate(lines, start=1):
        stripped_raw = raw_line.strip()
        if not stripped_raw or stripped_raw.startswith("%") or stripped_raw.startswith("#"):
            if not stripped_raw:
                saw_blank_since_last_prop = True
            continue

        line = strip_comment(raw_line).rstrip()
        if not line.strip():
            continue

        m_header = block_header_re.match(line)
        is_known_block = m_header and m_header.group(1) in (VALID_SINGLE_BLOCKS | VALID_MULTI_BLOCKS)

        if is_known_block and (current_block is None or saw_blank_since_last_prop or not line.startswith((" ", "\t"))):
            if current_block is not None and not saw_blank_since_last_prop:
                errors.append(
                    f"Line {idx}: Missing mandatory blank line before block '{m_header.group(1)}: {m_header.group(2)}'. "
                    "TRExFitter requires a blank line between every block!"
                )
            current_block = Block(m_header.group(1), m_header.group(2), idx)
            blocks.append(current_block)
            saw_blank_since_last_prop = False
            continue

        if current_block is None:
            errors.append(f"Line {idx}: Property or unknown block header outside any block: '{line.strip()}'")
            continue

        m_prop = prop_re.match(line)
        if not m_prop:
            errors.append(f"Line {idx}: Malformed key:value syntax in {current_block.block_type} '{current_block.name}': '{line.strip()}'")
            continue

        key, val = m_prop.group(1), m_prop.group(2)
        current_block.props.append((key, val, idx))
        saw_blank_since_last_prop = False

    return blocks, errors, warnings


def validate_single_fit(blocks: List[Block], errors: List[str], warnings: List[str]) -> None:
    by_type: Dict[str, List[Block]] = {}
    for b in blocks:
        by_type.setdefault(b.block_type, []).append(b)
        if b.block_type not in VALID_SINGLE_BLOCKS:
            errors.append(f"Line {b.line_no}: Unknown block type '{b.block_type}' for single-fit config.")

    # Check required singleton/plural blocks
    if len(by_type.get("Job", [])) != 1:
        errors.append(f"Expected exactly 1 'Job' block, found {len(by_type.get('Job', []))}.")
    if len(by_type.get("Fit", [])) != 1:
        errors.append(f"Expected exactly 1 'Fit' block, found {len(by_type.get('Fit', []))}.")
    if len(by_type.get("Region", [])) < 1:
        errors.append("Expected at least 1 'Region' block, found 0.")
    if len(by_type.get("Sample", [])) < 1 and len(by_type.get("UnfoldingSample", [])) < 1:
        errors.append("Expected at least 1 'Sample' (or 'UnfoldingSample') block, found 0.")

    # Check duplicate names per block type
    for btype, blist in by_type.items():
        seen = {}
        for b in blist:
            if b.name in seen:
                errors.append(
                    f"Line {b.line_no}: Duplicate {btype} name '{b.name}' (first defined at line {seen[b.name]})."
                )
            seen[b.name] = b.line_no

    job = by_type.get("Job", [None])[0]
    fit = by_type.get("Fit", [None])[0]
    regions = {b.name: b for b in by_type.get("Region", [])}
    samples = {b.name: b for b in by_type.get("Sample", [])}
    norm_factors = {b.name: b for b in by_type.get("NormFactor", [])}

    # Collect inline NormFactors & Morphing params from Sample blocks
    inline_nfs = set()
    morph_params = set()
    for s in samples.values():
        for k, v, _ in s.props:
            if k.lower() == "normfactor":
                nf_name = v.split(",")[0].strip().strip('"').strip("'")
                inline_nfs.add(nf_name)
            elif k.lower() == "morphing":
                mp_name = v.split(",")[0].strip().strip('"').strip("'")
                morph_params.add(mp_name)

    if job:
        read_from = job.get("ReadFrom", "HIST").upper()
        if read_from not in ("HIST", "NTUP"):
            errors.append(f"Line {job.line_no}: Job->ReadFrom must be HIST or NTUP, got '{read_from}'.")
        if read_from == "HIST" and not job.has("MergeUnderOverFlow"):
            warnings.append(
                f"Line {job.line_no}: ReadFrom is HIST and 'MergeUnderOverFlow' is not explicitly set "
                "(defaults to FALSE for HIST vs TRUE for NTUP). Consider setting MergeUnderOverFlow: TRUE if overflow bins contain signal/background."
            )
        if job.has("BlindingThreshold") and not job.has("BlindSRs"):
            if fit and fit.get("FitBlind", "FALSE").upper() != "TRUE":
                sr_not_asimov = [
                    r.name for r in regions.values()
                    if r.get("Type", "SIGNAL").upper() == "SIGNAL"
                    and r.get("DataType", "DATA").upper() != "ASIMOV"
                    and r.get("AutomaticDropBins", "FALSE").upper() != "TRUE"
                ]
                if sr_not_asimov:
                    warnings.append(
                        f"Line {job.line_no}: 'BlindingThreshold' only blinds plots, NOT the likelihood fit! "
                        f"Signal regions {sr_not_asimov} have DataType=DATA and FitBlind!=TRUE."
                    )

        # Check POI existence
        pois = [p.strip().strip('"').strip("'") for p in job.get("POI", "").split(",") if p.strip()]
        is_unfolding = fit and fit.get("FitType", "").upper() == "UNFOLDING"
        if not pois and not is_unfolding:
            warnings.append(f"Line {job.line_no}: No 'POI' defined in Job block.")
        for poi in pois:
            if poi not in norm_factors and poi not in inline_nfs and poi not in morph_params and not is_unfolding:
                errors.append(
                    f"Line {job.line_no}: POI '{poi}' in Job block does not match any NormFactor or Morphing parameter."
                )

    # Validate Sample settings
    has_data = any(s.get("Type", "BACKGROUND").upper() == "DATA" for s in samples.values())
    if not has_data and fit and fit.get("FitBlind", "FALSE").upper() != "TRUE":
        warnings.append("No Sample with 'Type: DATA' defined, and Fit->FitBlind is not TRUE.")

    for s in samples.values():
        stype = s.get("Type", "BACKGROUND").upper()
        if stype not in ("SIGNAL", "BACKGROUND", "DATA", "GHOST"):
            errors.append(f"Line {s.line_no}: Sample '{s.name}' has invalid Type '{stype}'.")
        if s.get("SeparateGammas", "FALSE").upper() == "TRUE":
            if job and job.get("MCstatThreshold", "").upper() == "NONE":
                warnings.append(
                    f"Line {s.line_no}: Sample '{s.name}' sets SeparateGammas: TRUE, but Job->MCstatThreshold: NONE disables it."
                )
        for ref_key in ("MultiplyBy", "DivideBy", "AddSample", "AddSamples", "SubtractSample", "SubtractSamples"):
            if s.has(ref_key):
                for ref_s in s.get(ref_key).split(","):
                    ref_s = ref_s.strip().strip('"').strip("'")
                    if ref_s and ref_s not in samples:
                        errors.append(f"Line {s.line_no}: Sample '{s.name}' {ref_key} references unknown Sample '{ref_s}'.")

    # Validate Systematics
    for syst in by_type.get("Systematic", []):
        sym = syst.get("Symmetrisation", "").upper()
        if sym and sym not in ("ONESIDED", "TWOSIDED", "ABSMEAN", "MAXIMUM"):
            errors.append(
                f"Line {syst.line_no}: Systematic '{syst.name}' has invalid Symmetrisation '{sym}' "
                "(allowed: ONESIDED, TWOSIDED, ABSMEAN, MAXIMUM)."
            )
        ref_sample = syst.get("ReferenceSample", "")
        if ref_sample and ref_sample not in samples:
            errors.append(
                f"Line {syst.line_no}: Systematic '{syst.name}' ReferenceSample '{ref_sample}' is not defined as a Sample (or GHOST Sample)."
            )
        subcat = syst.get("SubCategory", "")
        if subcat in ("Gammas", "FullSyst", "combine"):
            errors.append(
                f"Line {syst.line_no}: Systematic '{syst.name}' uses reserved SubCategory name '{subcat}'."
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a TRExFitter .config file.")
    parser.add_argument("config", type=Path, help="Path to the .config file")
    parser.add_argument("--multi", action="store_true", help="Validate as a MultiFit config")
    args = parser.parse_args()

    if not args.config.is_file():
        print(f"[ERROR] File not found: {args.config}", file=sys.stderr)
        return 2

    blocks, errors, warnings = parse_config(args.config)
    if not args.multi and not any(b.block_type == "MultiFit" for b in blocks):
        validate_single_fit(blocks, errors, warnings)

    print(f"=== TRExFitter Config Validation: {args.config} ===")
    print(f"Parsed {len(blocks)} blocks.")
    for w in warnings:
        print(f"  [WARN]  {w}")
    for e in errors:
        print(f"  [ERROR] {e}")

    if not errors and not warnings:
        print("  [OK] Configuration passed all schema and HEP best-practice checks.")
    elif not errors:
        print(f"  [OK] Configuration is valid with {len(warnings)} warning(s).")
    else:
        print(f"  [FAIL] Found {len(errors)} error(s) and {len(warnings)} warning(s).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
