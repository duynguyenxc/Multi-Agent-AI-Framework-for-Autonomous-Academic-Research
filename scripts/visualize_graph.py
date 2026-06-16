"""
scripts/visualize_graph.py — Interactive Knowledge Graph Visualization
=======================================================================
Generates an interactive HTML page showing:
  1. All entity nodes (color-coded by CMOC category)
  2. All typed relationships (labeled edges with arrows)
  3. PTS distribution chart
  4. Richmond benchmark comparison table
  5. Entity frequency heatmap

Reads from: outputs/evidence_table.json
Writes to:  outputs/knowledge_graph_visualization.html

No external dependencies beyond standard Python + json files.
"""
import json
import os
from collections import defaultdict

OUTPUT_DIR = r"d:\LLM-Knowledge-Graph\outputs"
EVIDENCE_FILE = os.path.join(OUTPUT_DIR, "evidence_table.json")
HTML_FILE = os.path.join(OUTPUT_DIR, "knowledge_graph_visualization.html")

# Color scheme for CMOC categories
CATEGORY_COLORS = {
    "Context": "#FF6B6B",
    "Intervention": "#4ECDC4",
    "Mechanism_Resource": "#45B7D1",
    "Mechanism_Response": "#FFA07A",
    "Outcome": "#98D8C8",
    "negative_outcome": "#E74C3C",
}

# Richmond benchmark data for comparison
RICHMOND_BENCHMARK = {
    "PTS1": {"context": "E02", "label": "Low knowledge students", "expected_cmocs": 20, "studies": 15},
    "PTS2": {"context": "E03", "label": "High knowledge students", "expected_cmocs": 6, "studies": 5},
    "PTS3": {"context": "E04", "label": "Positive coping/self-efficacy", "expected_cmocs": 5, "studies": 4},
    "PTS4": {"context": "E05", "label": "Negative coping/lacking self-efficacy", "expected_cmocs": 4, "studies": 3},
    "PTS5": {"context": "E06", "label": "Mixed-level groups", "expected_cmocs": 4, "studies": 3},
}


def load_evidence_table():
    """Load evidence_table.json (supports both old and new multi-CMOC format)."""
    if not os.path.exists(EVIDENCE_FILE):
        print(f"[ERROR] {EVIDENCE_FILE} not found. Run the pipeline first.")
        return []
    with open(EVIDENCE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_graph_data(cmocs):
    """Transform CMOC list into nodes + edges for visualization."""
    nodes = {}  # code -> {label, category, count, studies}
    edges = []
    edge_seen = set()

    for cmoc in cmocs:
        study_id = cmoc.get("study_id", "?")
        is_negative = cmoc.get("is_negative", False)

        # Extract entity codes - handle both old and new formats
        entity_fields = [
            ("context_code", "context_label", "Context"),
            ("intervention_code", "intervention_label", "Intervention"),
            ("mechanism_response_code", "mechanism_response_label", "Mechanism_Response"),
            ("outcome_code", "outcome_label", "Outcome"),
        ]

        # Backward compatibility: old format uses "context" directly
        if "context_code" not in cmoc and "context" in cmoc:
            cmoc["context_code"] = "?"
            cmoc["context_label"] = cmoc.get("context", "?")
            cmoc["intervention_code"] = "?"
            cmoc["intervention_label"] = cmoc.get("intervention", "?")
            cmoc["mechanism_response_code"] = "?"
            cmoc["mechanism_response_label"] = cmoc.get("mechanism_response", "?")
            cmoc["outcome_code"] = "?"
            cmoc["outcome_label"] = cmoc.get("outcome", "?")

        for code_key, label_key, category in entity_fields:
            code = cmoc.get(code_key, "?")
            label = cmoc.get(label_key, "?")
            if code not in nodes:
                nodes[code] = {
                    "id": code,
                    "label": label[:60],
                    "category": category,
                    "count": 0,
                    "studies": set(),
                    "is_negative": False,
                }
            nodes[code]["count"] += 1
            nodes[code]["studies"].add(study_id)
            if category == "Outcome" and is_negative:
                nodes[code]["is_negative"] = True

        # Build edges from relationships if available (new format)
        if "relationships" in cmoc and cmoc["relationships"]:
            for rel in cmoc["relationships"]:
                edge_key = (rel["source"], rel["target"], rel["type"])
                if edge_key not in edge_seen:
                    edge_seen.add(edge_key)
                    edges.append({
                        "source": rel["source"],
                        "target": rel["target"],
                        "type": rel["type"],
                        "evidence": rel.get("evidence", ""),
                        "weight": 1,
                    })
                else:
                    # Increase weight for repeated edges
                    for e in edges:
                        if (e["source"], e["target"], e["type"]) == edge_key:
                            e["weight"] += 1
                            break
        else:
            # Build implicit edges from CMOC chain (old format)
            ctx = cmoc.get("context_code", "?")
            intv = cmoc.get("intervention_code", "?")
            mr = cmoc.get("mechanism_response_code", "?")
            out = cmoc.get("outcome_code", "?")

            chain = [
                (intv, "E19", "PROVIDES"),
                ("E19", mr, "TRIGGERS"),
                (mr, out, "LEADS_TO" if not is_negative else "INHIBITS"),
            ]
            for src, tgt, rtype in chain:
                edge_key = (src, tgt, rtype)
                if edge_key not in edge_seen:
                    edge_seen.add(edge_key)
                    edges.append({"source": src, "target": tgt, "type": rtype, "evidence": "", "weight": 1})

    # Convert sets to lists for JSON
    for node in nodes.values():
        node["studies"] = sorted(node["studies"])

    return list(nodes.values()), edges


def build_stats(cmocs):
    """Build statistics for dashboard."""
    pts_dist = defaultdict(int)
    ctx_dist = defaultdict(int)
    mr_dist = defaultdict(int)
    out_dist = defaultdict(int)
    neg_count = 0

    for cmoc in cmocs:
        pts = cmoc.get("pts", "Unknown")
        pts_dist[pts] += 1
        ctx_dist[cmoc.get("context_code", "?")] += 1
        mr_dist[cmoc.get("mechanism_response_code", "?")] += 1
        out_dist[cmoc.get("outcome_code", "?")] += 1
        if cmoc.get("is_negative", False):
            neg_count += 1

    return {
        "total_cmocs": len(cmocs),
        "negative_cmocs": neg_count,
        "unique_studies": len(set(c.get("study_id", "") for c in cmocs)),
        "pts_distribution": dict(pts_dist),
        "context_distribution": dict(ctx_dist),
        "mechanism_response_distribution": dict(mr_dist),
        "outcome_distribution": dict(out_dist),
    }


def generate_html(nodes, edges, stats, cmocs):
    """Generate interactive HTML with embedded visualization."""
    # Build Richmond comparison data
    richmond_comparison = []
    for pts_key, benchmark in RICHMOND_BENCHMARK.items():
        pts_matches = [k for k, v in stats["pts_distribution"].items() if pts_key in k]
        our_count = sum(stats["pts_distribution"].get(k, 0) for k in pts_matches)
        richmond_comparison.append({
            "pts": pts_key,
            "context": benchmark["context"],
            "label": benchmark["label"],
            "richmond_cmocs": benchmark["expected_cmocs"],
            "our_cmocs": our_count,
            "match_pct": round(our_count / benchmark["expected_cmocs"] * 100) if benchmark["expected_cmocs"] > 0 else 0,
        })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LLM-Knowledge-Graph — Realist Synthesis Visualization</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Inter', sans-serif;
    background: #0f0f23;
    color: #e0e0e0;
    min-height: 100vh;
  }}

  .header {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 24px 32px;
    border-bottom: 2px solid #533483;
    display: flex;
    align-items: center;
    gap: 16px;
  }}

  .header h1 {{
    font-size: 1.5rem;
    font-weight: 700;
    background: linear-gradient(90deg, #e94560, #533483, #0f3460);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}

  .header .subtitle {{
    font-size: 0.85rem;
    color: #8899aa;
    font-weight: 300;
  }}

  .dashboard {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    padding: 24px 32px;
  }}

  .stat-card {{
    background: linear-gradient(145deg, #1a1a2e, #16213e);
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: transform 0.2s, border-color 0.2s;
  }}

  .stat-card:hover {{
    transform: translateY(-2px);
    border-color: #533483;
  }}

  .stat-card .number {{
    font-size: 2.2rem;
    font-weight: 700;
    color: #e94560;
  }}

  .stat-card .label {{
    font-size: 0.8rem;
    color: #8899aa;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}

  .section {{
    padding: 24px 32px;
  }}

  .section h2 {{
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 16px;
    color: #e94560;
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  .section h2::before {{
    content: '';
    width: 4px;
    height: 24px;
    background: linear-gradient(180deg, #e94560, #533483);
    border-radius: 2px;
  }}

  /* Graph container */
  #graph-container {{
    width: 100%;
    height: 600px;
    background: #0a0a1a;
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    position: relative;
    overflow: hidden;
  }}

  #graph-svg {{
    width: 100%;
    height: 100%;
  }}

  /* Tables */
  table {{
    width: 100%;
    border-collapse: collapse;
    background: #1a1a2e;
    border-radius: 12px;
    overflow: hidden;
  }}

  th {{
    background: #16213e;
    color: #e94560;
    padding: 12px 16px;
    text-align: left;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 2px solid #533483;
  }}

  td {{
    padding: 10px 16px;
    border-bottom: 1px solid #2a2a4a;
    font-size: 0.85rem;
  }}

  tr:hover td {{
    background: #16213e;
  }}

  .match-good {{ color: #2ecc71; }}
  .match-partial {{ color: #f39c12; }}
  .match-poor {{ color: #e74c3c; }}

  /* Legend */
  .legend {{
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    padding: 12px 0;
  }}

  .legend-item {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8rem;
  }}

  .legend-dot {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }}

  /* Relationship type badges */
  .rel-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.5px;
  }}
  .rel-PROVIDES {{ background: #2ecc71; color: #000; }}
  .rel-ENABLES {{ background: #3498db; color: #fff; }}
  .rel-LEADS_TO {{ background: #9b59b6; color: #fff; }}
  .rel-TRIGGERS {{ background: #f39c12; color: #000; }}
  .rel-INHIBITS {{ background: #e74c3c; color: #fff; }}
  .rel-MODERATES {{ background: #1abc9c; color: #000; }}

  /* Bar chart */
  .bar-chart {{
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 16px 0;
  }}
  .bar-row {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .bar-label {{
    width: 80px;
    font-size: 0.8rem;
    text-align: right;
    color: #8899aa;
  }}
  .bar-track {{
    flex: 1;
    height: 24px;
    background: #0a0a1a;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
  }}
  .bar-fill {{
    height: 100%;
    border-radius: 4px;
    display: flex;
    align-items: center;
    padding-left: 8px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #fff;
    transition: width 0.5s ease;
  }}
  .bar-richmond {{
    position: absolute;
    top: 0; bottom: 0;
    border-right: 2px dashed #e94560;
    opacity: 0.7;
  }}

  /* Tooltip */
  .tooltip {{
    position: fixed;
    background: #1a1a2e;
    border: 1px solid #533483;
    border-radius: 8px;
    padding: 12px;
    font-size: 0.8rem;
    max-width: 300px;
    pointer-events: none;
    z-index: 1000;
    display: none;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
  }}

  .tooltip strong {{ color: #e94560; }}

  /* Node info panel */
  .node-info {{
    position: absolute;
    top: 12px; right: 12px;
    background: rgba(26, 26, 46, 0.95);
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 16px;
    max-width: 280px;
    font-size: 0.8rem;
    display: none;
  }}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>LLM-Knowledge-Graph — Realist Synthesis Dashboard</h1>
    <div class="subtitle">Richmond et al. (2020) Benchmark Comparison | Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
  </div>
</div>

<!-- Stats Dashboard -->
<div class="dashboard">
  <div class="stat-card">
    <div class="number">{stats['total_cmocs']}</div>
    <div class="label">Total CMOCs</div>
  </div>
  <div class="stat-card">
    <div class="number">{stats['unique_studies']}</div>
    <div class="label">Studies</div>
  </div>
  <div class="stat-card">
    <div class="number">{len(nodes)}</div>
    <div class="label">Unique Nodes</div>
  </div>
  <div class="stat-card">
    <div class="number">{len(edges)}</div>
    <div class="label">Relationships</div>
  </div>
  <div class="stat-card">
    <div class="number">{stats['negative_cmocs']}</div>
    <div class="label">Negative CMOCs</div>
  </div>
  <div class="stat-card">
    <div class="number">{len(stats['pts_distribution'])}</div>
    <div class="label">PTS Coverage</div>
  </div>
</div>

<!-- Richmond Comparison -->
<div class="section">
  <h2>Richmond Benchmark Comparison</h2>
  <table>
    <tr>
      <th>PTS</th>
      <th>Context</th>
      <th>Description</th>
      <th>Richmond (expected)</th>
      <th>Our System</th>
      <th>Match %</th>
    </tr>
    {"".join(f'''<tr>
      <td><strong>{r['pts']}</strong></td>
      <td>{r['context']}</td>
      <td>{r['label']}</td>
      <td>{r['richmond_cmocs']}</td>
      <td>{r['our_cmocs']}</td>
      <td class="{'match-good' if r['match_pct'] >= 70 else 'match-partial' if r['match_pct'] >= 30 else 'match-poor'}">{r['match_pct']}%</td>
    </tr>''' for r in richmond_comparison)}
  </table>
</div>

<!-- PTS Distribution Bar Chart -->
<div class="section">
  <h2>PTS Distribution (Our System vs Richmond)</h2>
  <div class="bar-chart">
    {"".join(f'''<div class="bar-row">
      <div class="bar-label">{r['pts']}</div>
      <div class="bar-track">
        <div class="bar-fill" style="width: {min(r['our_cmocs'] / max(1, max(rc['richmond_cmocs'] for rc in richmond_comparison)) * 100, 100)}%; background: linear-gradient(90deg, #533483, #e94560);">
          {r['our_cmocs']}
        </div>
        <div class="bar-richmond" style="left: {min(r['richmond_cmocs'] / max(1, max(rc['richmond_cmocs'] for rc in richmond_comparison)) * 100, 100)}%;" title="Richmond expected: {r['richmond_cmocs']}"></div>
      </div>
    </div>''' for r in richmond_comparison)}
    <div style="font-size: 0.75rem; color: #8899aa; margin-top: 4px;">
      <span style="border-right: 2px dashed #e94560; padding-right: 4px;">▎</span> Dashed line = Richmond expected count
    </div>
  </div>
</div>

<!-- Entity Nodes Table -->
<div class="section">
  <h2>Entity Nodes ({len(nodes)} unique codes)</h2>
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background: {CATEGORY_COLORS['Context']}"></div> Context</div>
    <div class="legend-item"><div class="legend-dot" style="background: {CATEGORY_COLORS['Intervention']}"></div> Intervention</div>
    <div class="legend-item"><div class="legend-dot" style="background: {CATEGORY_COLORS['Mechanism_Response']}"></div> Mechanism Response</div>
    <div class="legend-item"><div class="legend-dot" style="background: {CATEGORY_COLORS['Outcome']}"></div> Outcome (positive)</div>
    <div class="legend-item"><div class="legend-dot" style="background: {CATEGORY_COLORS['negative_outcome']}"></div> Outcome (negative)</div>
  </div>
  <table>
    <tr>
      <th>Code</th>
      <th>Category</th>
      <th>Label</th>
      <th>Frequency</th>
      <th>Studies</th>
    </tr>
    {"".join(f'''<tr>
      <td><strong style="color: {CATEGORY_COLORS.get('negative_outcome' if n.get('is_negative') else n['category'], '#e0e0e0')}">{n['id']}</strong></td>
      <td>{n['category']}</td>
      <td>{n['label']}</td>
      <td>{n['count']}</td>
      <td style="font-size: 0.75rem;">{', '.join(n['studies'][:8])}{'...' if len(n['studies']) > 8 else ''}</td>
    </tr>''' for n in sorted(nodes, key=lambda x: (-x['count'], x['id'])))}
  </table>
</div>

<!-- Relationship Edges Table -->
<div class="section">
  <h2>Relationship Edges ({len(edges)} unique)</h2>
  <table>
    <tr>
      <th>Source</th>
      <th>Relationship</th>
      <th>Target</th>
      <th>Weight</th>
    </tr>
    {"".join(f'''<tr>
      <td>{e['source']}</td>
      <td><span class="rel-badge rel-{e['type']}">{e['type']}</span></td>
      <td>{e['target']}</td>
      <td>{e['weight']}</td>
    </tr>''' for e in sorted(edges, key=lambda x: -x['weight'])[:50])}
  </table>
</div>

<!-- Full CMOC Table -->
<div class="section">
  <h2>Full CMOC Evidence Table ({len(cmocs)} entries)</h2>
  <table>
    <tr>
      <th>Study</th>
      <th>CMOC</th>
      <th>PTS</th>
      <th>C → I → M_Resp → O</th>
      <th>Neg?</th>
      <th>Conf</th>
    </tr>
    {"".join(f'''<tr>
      <td>{c.get('study_id', '?')}</td>
      <td>{c.get('cmoc_id', '?').split('_')[-1] if '_' in c.get('cmoc_id', '') else '?'}</td>
      <td>{c.get('pts', '?')[:4] if c.get('pts') else '?'}</td>
      <td style="font-size: 0.75rem;">
        <strong>{c.get('context_code', '?')}</strong> →
        <strong>{c.get('intervention_code', '?')}</strong> →
        <strong>{c.get('mechanism_response_code', '?')}</strong> →
        <strong style="color: {'#e74c3c' if c.get('is_negative') else '#2ecc71'}">{c.get('outcome_code', '?')}</strong>
      </td>
      <td>{'❌' if c.get('is_negative') else '✓'}</td>
      <td>{c.get('confidence', 0):.1f}</td>
    </tr>''' for c in cmocs)}
  </table>
</div>

<div style="padding: 24px 32px; text-align: center; color: #555; font-size: 0.75rem;">
  LLM-Knowledge-Graph | Realist Synthesis Pipeline | Richmond et al. (2020) Benchmark
</div>

</body>
</html>"""
    return html


def main():
    print("Loading evidence table...")
    cmocs = load_evidence_table()
    if not cmocs:
        return

    print(f"Building graph from {len(cmocs)} CMOCs...")
    nodes, edges = build_graph_data(cmocs)
    stats = build_stats(cmocs)

    print(f"Generating visualization ({len(nodes)} nodes, {len(edges)} edges)...")
    html = generate_html(nodes, edges, stats, cmocs)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[DONE] Interactive visualization saved to:")
    print(f"  {HTML_FILE}")
    print(f"\nOpen in browser to view the dashboard.")


if __name__ == "__main__":
    main()
