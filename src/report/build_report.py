"""
Build HTML Validation Report
"""
import sys
import json
import datetime
import platform
from pathlib import Path
from jinja2 import Template
import markdown

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Epistemic
from merge import concordance

def load_json(path):
    """Load JSON file"""
    with open(path) as f:
        return json.load(f)

def build_report(output_html, generate_pdf=False):
    """
    Build validation report

    Parameters
    ----------
    output_html : str
        Output HTML file path
    generate_pdf : bool
        If True, also generate PDF (requires pandoc)
    """
    results_dir = Path("outputs/results")

    print("="*70)
    print("BUILDING VALIDATION REPORT")
    print("="*70)
    print()

    # Load validation results
    print("Loading validation results...")
    try:
        loao = load_json(results_dir / "loao.json")
        grid = load_json(results_dir / "grids.json")
        boot = load_json(results_dir / "bootstrap.json")
        inject = load_json(results_dir / "inject.json")
    except FileNotFoundError as e:
        print(f"ERROR: Missing validation result: {e}")
        print("Run validations first: make validate")
        return False

    # Compute baseline concordance
    print("Computing baseline concordance...")
    h0 = concordance(Epistemic.delta_T, Epistemic.f_systematic)

    # Normalize LOAO structure to match template expectations
    # LOAO uses different gate structure than other validations
    if "gate_a_engineering" in loao and "gate" not in loao:
        loao["gate"] = loao["gate_a_engineering"]["threshold"]
        loao["passed"] = loao.get("overall_passed", False)

    # Check overall pass status
    all_passed = (
        loao.get("passed", False) and
        grid.get("passed", False) and
        boot.get("passed", False) and
        inject.get("passed", False)
    )

    # Load template
    template_path = Path(__file__).parent / "templates/report.tpl.md"
    print(f"Loading template: {template_path}")
    with open(template_path) as f:
        template_text = f.read()

    template = Template(template_text)

    # Render markdown
    print("Rendering report...")
    md_content = template.render(
        date=datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        env=f"{platform.system()} {platform.release()} / Python {platform.python_version()}",
        h0=h0,
        loao=loao,
        grid=grid,
        boot=boot,
        inject=inject,
        all_passed=all_passed,
        runtime=None  # TODO: track runtime
    )

    # Convert to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code']
    )

    # Add CSS styling
    html_styled = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>H₀ Concordance Validation Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #2c3e50;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 8px;
            margin-top: 40px;
        }}
        h3 {{
            color: #555;
        }}
        code {{
            background: #ecf0f1;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        pre code {{
            background: none;
            padding: 0;
        }}
        .pass {{
            color: #27ae60;
            font-weight: bold;
        }}
        .fail {{
            color: #e74c3c;
            font-weight: bold;
        }}
        hr {{
            border: none;
            border-top: 1px solid #bdc3c7;
            margin: 30px 0;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

    # Write HTML
    outpath = Path(output_html)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with open(outpath, 'w') as f:
        f.write(html_styled)

    print(f"✓ HTML report written to: {outpath}")

    # Generate PDF if requested
    if generate_pdf:
        try:
            import subprocess
            pdf_path = outpath.with_suffix('.pdf')
            subprocess.run([
                'pandoc',
                str(outpath),
                '-o', str(pdf_path),
                '--pdf-engine=pdflatex'
            ], check=True)
            print(f"✓ PDF report written to: {pdf_path}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠ PDF generation failed (pandoc/pdflatex not installed)")

    # Print summary
    print()
    print("="*70)
    print("REPORT SUMMARY")
    print("="*70)
    print(f"\nConcordance H₀: {h0['mu_star']:.2f} ± {h0['sigma_star']:.2f} km/s/Mpc")
    print(f"Tension to Planck: {h0['z_planck']:.2f}σ")
    print(f"\nValidation gates: {'✅ ALL PASSED' if all_passed else '⚠️ ONE OR MORE FAILED'}")
    print(f"  LOAO: {'✅' if loao.get('passed') else '❌'}")
    print(f"  Grid-scan: {'✅' if grid.get('passed') else '❌'}")
    print(f"  Bootstrap: {'✅' if boot.get('passed') else '❌'}")
    print(f"  Injection: {'✅' if inject.get('passed') else '❌'}")
    print("="*70)

    return True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build validation report")
    parser.add_argument("--out", type=str, required=True, help="Output HTML file")
    parser.add_argument("--pdf", action="store_true", help="Also generate PDF")
    args = parser.parse_args()

    success = build_report(args.out, args.pdf)
    sys.exit(0 if success else 1)
