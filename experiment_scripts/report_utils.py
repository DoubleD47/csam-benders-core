"""
Generate Markdown + PDF reports for single runs and factorial sweeps.

Reports are written to a reports/ subfolder inside the experiment or sweep directory.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent


def _reports_dir(base: Path) -> Path:
    d = base / "reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _fmt_list(items: list[Any] | None) -> str:
    if not items:
        return "none"
    return ", ".join(str(x) for x in items)


def _dataframe_to_markdown_table(df: pd.DataFrame, max_rows: int = 50) -> str:
    if df.empty:
        return "_No data._\n"
    view = df.head(max_rows)
    cols = list(view.columns)
    lines = [
        "| " + " | ".join(str(c) for c in cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for _, row in view.iterrows():
        cells = []
        for c in cols:
            val = row[c]
            if isinstance(val, float):
                cells.append(f"{val:.2f}")
            elif isinstance(val, list):
                cells.append(_fmt_list(val))
            else:
                cells.append(str(val))
        lines.append("| " + " | ".join(cells) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_Showing {max_rows} of {len(df)} rows._")
    return "\n".join(lines) + "\n"


def _write_pdf_from_markdown(md_path: Path, pdf_path: Path, image_paths: list[Path] | None = None) -> bool:
    """Render a simple PDF (text + optional images) using fpdf2."""
    try:
        from fpdf import FPDF
    except ImportError:
        return False

    text = md_path.read_text(encoding="utf-8")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)

    page_width = pdf.w - pdf.l_margin - pdf.r_margin

    def _safe_cell(content: str, h: float = 5) -> None:
        """Write wrapped text; truncate pathological single-token lines."""
        chunk = content if content else " "
        if len(chunk) > 500:
            chunk = chunk[:497] + "..."
        try:
            pdf.multi_cell(page_width, h, chunk)
        except Exception:
            for i in range(0, len(chunk), 90):
                pdf.multi_cell(page_width, h, chunk[i : i + 90])

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            pdf.set_font("Helvetica", "B", 14)
            _safe_cell(stripped[2:], h=8)
            pdf.set_font("Helvetica", size=10)
        elif stripped.startswith("## "):
            pdf.set_font("Helvetica", "B", 12)
            _safe_cell(stripped[3:], h=7)
            pdf.set_font("Helvetica", size=10)
        elif stripped.startswith("```"):
            continue
        elif stripped.startswith("!["):
            continue
        elif stripped.startswith("|"):
            pdf.set_font("Courier", size=7)
            # Split wide markdown tables into one cell per column
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            row = "  ".join(c[:20] for c in cells)
            _safe_cell(row, h=4)
            pdf.set_font("Helvetica", size=10)
        else:
            _safe_cell(line, h=5)

    if image_paths:
        for img in image_paths:
            if not img.exists():
                continue
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, img.name)
            pdf.ln(10)
            try:
                pdf.image(str(img), w=min(180, page_width))
            except Exception:
                _safe_cell(f"(Could not embed image: {img.name})")

    pdf.output(str(pdf_path))
    return True


def generate_run_report(
    experiment_dir: Path | str,
    summary: dict[str, Any],
    params: dict[str, Any] | None = None,
) -> dict[str, str]:
    """
    Write run_report.md and run_report.pdf for a single experiment folder.
    Called automatically at the end of solve_benders.
    """
    experiment_dir = Path(experiment_dir)
    if not experiment_dir.is_absolute():
        experiment_dir = REPO_ROOT / experiment_dir
    reports = _reports_dir(experiment_dir)

    run_id = summary.get("run_id", experiment_dir.name)
    deployed = summary.get("deployed_facilities", [])
    lines = [
        f"# CSAM Experiment Report: {run_id}",
        "",
        f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
        "## Configuration",
        "",
        f"- **Scenario:** {summary.get('scenario_name', 'N/A')}",
        f"- **MAX_CSAM_FACILITIES:** {summary.get('max_csam_facilities')}",
        f"- **Seed:** {summary.get('seed')}",
        f"- **Demand mean / variance:** {summary.get('demand_mean')} / {summary.get('demand_variance')}",
        f"- **CSAM opening cost (F):** {summary.get('F_cost')}",
        "",
        "## Results",
        "",
        f"- **Objective (total cost):** {summary.get('objective', 0):.2f}",
        f"- **Subproblem cost:** {summary.get('subproblem_cost', 0):.2f}",
        f"- **Deployment cost:** {summary.get('deployment_cost', 0):.2f}",
        f"- **CSAM deployed:** {_fmt_list(deployed)} ({summary.get('deployed_count', 0)} facilities)",
        f"- **Total demand:** {summary.get('total_demand', 0):.1f}",
        f"- **Unmet demand:** {summary.get('unmet_demand', 0):.1f} ({summary.get('unmet_demand_pct', 0):.1f}%)",
        f"- **Benders iterations:** {summary.get('iterations')}",
        f"- **Runtime (s):** {summary.get('runtime_seconds', 0):.1f}",
        "",
        "## Output Files",
        "",
    ]
    flow_files = summary.get("flow_files") or {}
    for key, path in flow_files.items():
        lines.append(f"- **{key} flows:** `{path}`")
    lines.append(f"- **Full log:** `{experiment_dir / 'summary.json'}`")
    lines.append("")

    # Omit full params dump from per-run PDF (can be very wide); available in configs for sweeps

    md_path = reports / "run_report.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    pdf_path = reports / "run_report.pdf"
    pdf_ok = _write_pdf_from_markdown(md_path, pdf_path)

    return {
        "markdown": str(md_path.relative_to(REPO_ROOT)),
        "pdf": str(pdf_path.relative_to(REPO_ROOT)) if pdf_ok else "",
    }


def generate_sweep_report(sweep_dir: Path | str) -> dict[str, str]:
    """
    Write sweep_report.md and sweep_report.pdf for a factorial sweep folder.
    Best run after analyze_sweep so visualizations exist.
    """
    sweep_dir = Path(sweep_dir)
    if not sweep_dir.is_absolute():
        sweep_dir = REPO_ROOT / sweep_dir
    reports = _reports_dir(sweep_dir)
    viz_dir = sweep_dir / "visualizations"

    manifest = {}
    manifest_path = sweep_dir / "sweep_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

    records = []
    results_dir = sweep_dir / "results"
    for path in sorted(results_dir.glob("*_summary.json")):
        with open(path, encoding="utf-8") as f:
            records.append(json.load(f))
    df = pd.DataFrame(records)

    lines = [
        f"# CSAM Factorial Sweep Report",
        "",
        f"_Sweep folder: `{sweep_dir.name}`_",
        f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
        "## Factor Grid",
        "",
    ]
    grid = manifest.get("factor_grid", {})
    for key, values in grid.items():
        lines.append(f"- **{key}:** {values}")
    lines.extend([
        "",
        f"- **Scenarios run:** {manifest.get('scenario_count', len(df))}",
        f"- **Full factorial size:** {manifest.get('full_factorial_size', 'N/A')}",
        f"- **Failed:** {len(manifest.get('failed', []))}",
        "",
        "## Summary Statistics",
        "",
    ])

    if not df.empty:
        for col in ("objective", "deployed_count", "unmet_demand_pct", "runtime_seconds"):
            if col in df.columns:
                lines.append(
                    f"- **{col}:** mean={df[col].mean():.2f}, "
                    f"min={df[col].min():.2f}, max={df[col].max():.2f}"
                )
        lines.extend(["", "## Deployment Frequency", ""])
        counts: dict[str, int] = {}
        for deployed in df.get("deployed_facilities", pd.Series(dtype=object)):
            if isinstance(deployed, list):
                for m in deployed:
                    counts[m] = counts.get(m, 0) + 1
        if counts:
            freq = pd.Series(counts).sort_values(ascending=False)
            for node, n in freq.items():
                pct = 100 * n / len(df)
                lines.append(f"- **{node}:** {n} scenarios ({pct:.0f}%)")
        else:
            lines.append("_No deployments recorded._")

        lines.extend(["", "## Scenario Results", ""])
        table_cols = [
            c for c in [
                "scenario", "MAX_CSAM_FACILITIES", "demand_mean", "demand_variance", "F_cost", "SEED",
                "objective", "deployed_count", "deployed_facilities", "unmet_demand_pct",
            ]
            if c in df.columns
        ]
        lines.append(_dataframe_to_markdown_table(df[table_cols]))

    lines.extend(["", "## Figures", ""])
    figure_names = sorted(p.name for p in viz_dir.glob("*.png")) if viz_dir.exists() else []
    if not figure_names:
        figure_names = [
            "deployment_frequency.png",
            "deployment_count_by_scenario.png",
            "unmet_demand_by_scenario.png",
        ]
    for name in figure_names:
        img = viz_dir / name
        if img.exists():
            rel = img.relative_to(sweep_dir)
            lines.append(f"![{name}]({rel.as_posix()})")
            lines.append("")

    md_path = reports / "sweep_report.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    image_paths = [viz_dir / n for n in figure_names if (viz_dir / n).exists()]
    pdf_path = reports / "sweep_report.pdf"
    pdf_ok = _write_pdf_from_markdown(md_path, pdf_path, image_paths=image_paths)

    return {
        "markdown": str(md_path.relative_to(REPO_ROOT)),
        "pdf": str(pdf_path.relative_to(REPO_ROOT)) if pdf_ok else "",
    }