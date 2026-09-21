"""Write Power BI-ready CSV plus a static executive HTML dashboard."""

from __future__ import annotations

import csv
import html
import json
import os
from datetime import datetime, timezone


def _load(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _esc(value) -> str:
    return html.escape("" if value is None else str(value))


def _badge(level: str) -> str:
    token = (level or "UNKNOWN").upper()
    return f'<span class="badge badge-{_esc(token.lower())}">{_esc(token)}</span>'


def export_dataset(output_dir: str = "output", meta: dict | None = None) -> str:
    os.makedirs(output_dir, exist_ok=True)
    findings = _load(os.path.join(output_dir, "finding.json"), [])
    incidents = _load(os.path.join(output_dir, "incident.json"), [])
    attacks = _load(os.path.join(output_dir, "attack.json"), [])
    remediations = _load(os.path.join(output_dir, "remediation.json"), [])
    coverage = _load(os.path.join(output_dir, "owasp-coverage.json"), [])
    frameworks = _load(os.path.join(output_dir, "framework-coverage.json"), {})
    retest = _load(os.path.join(output_dir, "retest.json"), {})
    raw_assets = _load(os.path.join(output_dir, "asset.json"), {})
    assets = raw_assets if isinstance(raw_assets, list) else ([raw_assets] if raw_assets else [])
    asset = assets[0] if assets else {}
    a2a = _load(os.path.join(output_dir, "a2a-messages.json"), [])
    meta = meta or {}

    csv_path = os.path.join(output_dir, "powerbi-risk-dataset.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "finding_id",
                "asset",
                "risk_score",
                "risk_level",
                "threats",
                "owasp_llm",
                "mitre_atlas",
                "nist_ai_rmf",
            ],
        )
        writer.writeheader()
        for finding in findings:
            writer.writerow(
                {
                    "finding_id": finding.get("finding_id"),
                    "asset": finding.get("asset"),
                    "risk_score": finding.get("risk_score"),
                    "risk_level": finding.get("risk_level"),
                    "threats": ";".join(finding.get("threats") or []),
                    "owasp_llm": ";".join(finding.get("owasp_llm") or []),
                    "mitre_atlas": ";".join(finding.get("mitre_atlas") or []),
                    "nist_ai_rmf": ";".join(finding.get("nist_ai_rmf") or []),
                }
            )

    html_path = os.path.join(output_dir, "executive-dashboard.html")
    critical = sum(1 for item in findings if item.get("risk_level") == "CRITICAL")
    high = sum(1 for item in findings if item.get("risk_level") == "HIGH")
    medium = sum(1 for item in findings if item.get("risk_level") == "MEDIUM")
    low = sum(1 for item in findings if item.get("risk_level") == "LOW")
    confirmed = sum(1 for item in attacks if item.get("exploitability") == "CONFIRMED")
    blocked_validations = sum(1 for item in attacks if item.get("exploitability") == "BLOCKED")
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    correlation = _esc(str(meta.get("correlation_id") or "local"))
    asset_name = _esc(asset.get("name") or "HealthcareAIAssistant")
    if retest.get("blocked") is True:
        retest_label = "BLOCKED"
        posture = "Controls held on retest"
        posture_class = "good"
    elif retest.get("exploitability") or confirmed:
        retest_label = "OPEN"
        posture = "Authorized demo still exploitable"
        posture_class = "bad"
    else:
        retest_label = "—"
        posture = "Awaiting validation"
        posture_class = "warn"

    total = max(len(findings), 1)
    def _pct(n: int) -> int:
        return round(100 * n / total)

    finding_rows = "".join(
        "<tr class='finding-row' data-level='"
        f"{_esc(item.get('risk_level'))}'>"
        f"<td>{_esc(item.get('finding_id'))}</td>"
        f"<td>{_badge(str(item.get('risk_level') or ''))}</td>"
        f"<td>{_esc(item.get('risk_score'))}</td>"
        f"<td>{_esc(', '.join(item.get('threats') or []))}</td>"
        f"<td>{_esc(', '.join(item.get('owasp_llm') or []))}</td>"
        f"<td>{_esc(', '.join(item.get('mitre_atlas') or []))}</td>"
        f"<td>{_esc(', '.join(item.get('nist_ai_rmf') or []))}</td>"
        f"<td>{_esc((item.get('recommendations') or ['—'])[0])}</td>"
        "</tr>"
        for item in findings
    )
    coverage_rows = "".join(
        f"<tr><td>{_esc(item.get('owasp_id'))}</td><td>{_esc(item.get('name'))}</td>"
        f"<td>{_badge(str(item.get('status') or ''))}</td></tr>"
        for item in coverage
    )
    atlas_rows = "".join(
        f"<tr><td>{_esc(item.get('id'))}</td><td>{_esc(item.get('name'))}</td>"
        f"<td>{_badge(str(item.get('status') or ''))}</td></tr>"
        for item in frameworks.get("atlas") or []
    )
    nist_rows = "".join(
        f"<tr><td>{_esc(item.get('id'))}</td>"
        f"<td>{_esc(', '.join(item.get('covered_threats') or []))}</td>"
        f"<td>{_badge(str(item.get('status') or ''))}</td></tr>"
        for item in frameworks.get("nist") or []
    )
    attack_rows = "".join(
        "<tr>"
        f"<td>{_esc(item.get('finding_id'))}</td>"
        f"<td>{_esc(item.get('target'))}</td>"
        f"<td>{_esc(item.get('attack_type'))}</td>"
        f"<td>{_badge(str(item.get('exploitability') or ''))}</td>"
        f"<td>{_esc(item.get('recommended_control'))}</td>"
        "</tr>"
        for item in attacks
    )
    incident_cards = "".join(
        "<article class='incident'>"
        f"<div class='incident-top'>{_badge(str(item.get('severity') or ''))}"
        f"<span class='muted'>{_esc(item.get('incident_id'))} · {_esc(item.get('status'))}</span></div>"
        f"<h3>{_esc(item.get('title'))}</h3>"
        f"<p class='muted'>Lineage: {_esc(' → '.join(item.get('lineage') or []))}</p>"
        f"<p>{_esc(item.get('recommendation'))}</p>"
        f"<p class='muted'>Containment: {_esc((item.get('containment') or {}).get('reason') or 'Not requested')}</p>"
        "</article>"
        for item in incidents
    ) or "<p class='muted'>No incidents in this run.</p>"

    owasp_covered = sum(1 for item in coverage if item.get("status") == "COVERED")
    owasp_na = sum(1 for item in coverage if item.get("status") == "NOT_APPLICABLE")
    owasp_mapped_only = [item.get("owasp_id") for item in coverage if item.get("status") == "MAPPED"]
    crit_findings = [item for item in findings if item.get("risk_level") == "CRITICAL"]
    top_actions = []
    for item in findings:
        if item.get("risk_level") in {"CRITICAL", "HIGH"}:
            rec = (item.get("recommendations") or ["Review finding"])[0]
            top_actions.append(f"{item.get('finding_id')}: {rec}")
    top_actions = top_actions[:4]
    containment_done = any((item.get("containment") or {}).get("executed") for item in incidents)
    untested_threats = sorted(
        {
            tid
            for item in findings
            for tid in (item.get("threats") or [])
            if tid != "T-001"
        }
    )

    if retest.get("blocked") is True and confirmed:
        safe_now = (
            "No. The original demo still failed the authorized T-001 check (CONFIRMED). "
            "The hardened copy passed retest (BLOCKED). Do not promote the original demo. "
            "Promote only the hardened control path."
        )
        board_line = (
            f"Authorized demo: T-001 confirmed on the unprotected build; "
            f"same check blocked after controls. {critical} critical / {high} high findings remain on the unprotected build."
        )
        go_no_go = "NO-GO for unprotected demo · GO to keep the hardened control set"
    elif retest.get("blocked") is True:
        safe_now = "Retest of T-001 held. Other findings were assessed, not all were re-validated."
        board_line = "T-001 control held on retest. Residual findings still need owners."
        go_no_go = "CONDITIONAL GO — retest held; close remaining HIGH/CRITICAL owners"
    elif confirmed:
        safe_now = "No. Authorized validation confirmed T-001 on the demo. Treat as an open critical until retest is BLOCKED."
        board_line = "Open critical: authorized demo failed T-001. Human approval required before any containment."
        go_no_go = "NO-GO until T-001 retest is BLOCKED"
    else:
        safe_now = "Not enough validation yet. Run the lifecycle with retest."
        board_line = "Assessment incomplete — no confirmed validation result."
        go_no_go = "HOLD"

    qa = [
        ("Is this a customer or production incident?",
         "No. Scope is only the authorized in-repo HealthcareAIAssistant mock. No tenant or live EHR was targeted."),
        ("Was real patient / PHI leaked?",
         "No. Evidence stores redacted record ids only. Clinical fields are not written to this dashboard."),
        ("Are we safe right now?",
         safe_now),
        ("What actually failed?",
         f"{confirmed} authorized validation(s) CONFIRMED on the unprotected demo; "
         f"{blocked_validations} BLOCKED on that pass. Retest T-001 is {retest_label}."),
        ("What is the one-line board message?",
         board_line),
        ("Ship / no-ship decision?",
         go_no_go),
        ("What must we do this week?",
         " · ".join(top_actions) if top_actions else "No HIGH/CRITICAL recommendations in this run."),
        ("Did SOC shut anything down?",
         "Yes — containment executed." if containment_done else
         "No. Containment stays off until a human writes an approval file and FOUNDRY_SOC_EXECUTE=true. "
         "That only disables the allowlisted demo service principal, never a customer identity."),
        ("Who owns the next action?",
         "Security Engineer: apply remaining HIGH/CRITICAL remediations. "
         "SOC: keep the incident NEW until approval. "
         "Leadership: do not approve production use of the unprotected demo."),
        ("Are we aligned to OWASP / NIST?",
         f"OWASP: {owasp_covered} covered, {owasp_na} not applicable"
         + (f", still only mapped (not evidenced): {', '.join(owasp_mapped_only)}." if owasp_mapped_only else ".")
         + " NIST functions that have at least one mapped finding are marked COVERED in the table below."),
        ("What did we not retest?",
         ("T-001 is the only authorized validation. Not retested: " + ", ".join(untested_threats) + ".")
         if untested_threats else "Only T-001 is in the red-team allowlist; no other threats were due for retest."),
        ("Does this meet Entra-only company policy?",
         "Not yet for all paths. Humans already use Entra for the portal. "
         "Agent-to-model and agent-to-runtime still can use API keys / a static Bearer token. "
         "That is a policy gap, not a finding in the demo app."),
        ("Could this have been a customer system?",
         "The platform refuses any target not in config/production.json. This run stayed on the allowlisted demo."),
    ]
    qa_html = "".join(
        f"<div class='qa'><div class='q'>{_esc(question)}</div><div class='a'>{_esc(answer)}</div></div>"
        for question, answer in qa
    )

    agent_names = {
        "security-engineer": "AI Security Engineer",
        "red-team": "AI Red Team",
        "runtime-soc": "AI Runtime SOC",
        "orchestrator": "AI Security Orchestrator",
    }
    corr_filter = str(meta.get("correlation_id") or "")
    handoffs = [row for row in a2a if corr_filter and row.get("correlation_id") == corr_filter]
    if not handoffs and a2a:
        last_corr = a2a[-1].get("correlation_id")
        handoffs = [row for row in a2a if row.get("correlation_id") == last_corr]
    asset_rows = "".join(
        "<tr>"
        f"<td><strong>{_esc(item.get('name') or 'Unknown')}</strong></td>"
        f"<td>{_esc(item.get('asset_type'))}</td>"
        f"<td>{_esc(item.get('asset_id'))}</td>"
        f"<td>{_esc(', '.join(item.get('discovered_tools') or []) or '—')}</td>"
        f"<td>{_esc(', '.join(item.get('identities') or []) or '—')}</td>"
        f"<td>{_esc(', '.join(item.get('dependencies') or []) or '—')}</td>"
        f"<td>{_esc(item.get('description') or '—')}</td>"
        "</tr>"
        for item in assets
    ) or "<tr><td colspan='7' class='muted'>No asset.json in this run. Engineer discovery has not written an asset yet.</td></tr>"
    handoff_rows = "".join(
        "<tr>"
        f"<td>{_esc(agent_names.get(row.get('from_agent'), row.get('from_agent')))}</td>"
        f"<td>{_esc(agent_names.get(row.get('to_agent'), row.get('to_agent')))}</td>"
        f"<td>{_esc(row.get('intent'))}</td>"
        f"<td>{_esc(row.get('payload_ref'))}</td>"
        f"<td>{_esc(row.get('summary'))}</td>"
        "</tr>"
        for row in handoffs
    ) or "<tr><td colspan='5' class='muted'>No A2A handoffs in this folder. Run the lifecycle to stamp agent provenance.</td></tr>"

    with open(html_path, "w", encoding="utf-8") as handle:
        handle.write(
            f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI Security Executive Dashboard</title>
  <style>
    :root {{
      --bg: #f4f6fa; --panel: #ffffff; --line: #d8dee8; --text: #1b2433; --muted: #5b677a;
      --crit: #c81e3a; --high: #b45309; --med: #0369a1; --low: #047857; --good: #15803d;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: "Segoe UI", system-ui, sans-serif; background: linear-gradient(180deg, #eef3fb 0%, var(--bg) 28%); color: var(--text); }}
    header {{ padding: 28px 32px 12px; display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; align-items: flex-end; }}
    h1 {{ margin: 0; font-size: 26px; letter-spacing: -0.02em; }}
    h2 {{ margin: 28px 0 12px; font-size: 16px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); }}
    h3 {{ margin: 8px 0; font-size: 16px; }}
    .muted {{ color: var(--muted); font-size: 13px; }}
    main {{ padding: 0 32px 48px; }}
    .posture {{ padding: 8px 12px; border-radius: 999px; font-weight: 600; font-size: 13px; }}
    .posture.good {{ background: #dcfce7; color: #166534; }}
    .posture.bad {{ background: #fee2e2; color: #991b1b; }}
    .posture.warn {{ background: #fef3c7; color: #92400e; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }}
    .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; }}
    .label {{ color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; }}
    .value {{ font-size: 28px; margin-top: 8px; font-weight: 650; }}
    .card.crit .value {{ color: var(--crit); }}
    .card.high .value {{ color: var(--high); }}
    .card.good .value {{ color: var(--good); }}
    .grid2 {{ display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 16px; }}
    @media (max-width: 900px) {{ .grid2 {{ grid-template-columns: 1fr; }} header, main {{ padding-left: 16px; padding-right: 16px; }} }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ text-align: left; padding: 9px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 700; }}
    .badge-critical, .badge-confirmed {{ background: #fee2e2; color: #991b1b; }}
    .badge-high {{ background: #ffedd5; color: #9a3412; }}
    .badge-medium, .badge-mapped {{ background: #e0f2fe; color: #075985; }}
    .badge-low {{ background: #d1fae5; color: #065f46; }}
    .badge-covered, .badge-blocked {{ background: #dcfce7; color: #166534; }}
    .badge-not_applicable, .badge-untested {{ background: #e5e7eb; color: #374151; }}
    .badge-new {{ background: #fee2e2; color: #991b1b; }}
    .bar {{ display: flex; height: 14px; border-radius: 99px; overflow: hidden; background: #e5eaf2; margin: 10px 0 6px; }}
    .bar span {{ display: block; height: 100%; }}
    .filters {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0 12px; }}
    .filters button {{ background: transparent; color: var(--text); border: 1px solid var(--line); border-radius: 999px; padding: 6px 10px; cursor: pointer; }}
    .filters button.active {{ background: #1d4ed8; border-color: #1d4ed8; color: #fff; }}
    .incident {{ border: 1px solid var(--line); border-radius: 10px; padding: 12px; margin-bottom: 10px; }}
    .incident-top {{ display: flex; gap: 10px; align-items: center; }}
    .legend {{ display: flex; gap: 12px; flex-wrap: wrap; font-size: 12px; color: var(--muted); }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 4px; }}
    .decision {{ margin: 0 32px 16px; padding: 14px 16px; border-radius: 12px; border: 1px solid var(--line); background: var(--panel); font-weight: 650; }}
    .qa-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    @media (max-width: 900px) {{ .qa-grid {{ grid-template-columns: 1fr; }} .decision {{ margin-left: 16px; margin-right: 16px; }} }}
    .qa {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }}
    .q {{ font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px; }}
    .a {{ font-size: 14px; line-height: 1.45; }}
  </style>
</head>
<body>
  <header>
    <div>
      <p class="muted">Foundary · Authorized healthcare demo only</p>
      <h1>AI Security Executive Dashboard</h1>
      <p class="muted">Asset {asset_name} · Generated {generated} · Correlation {correlation}</p>
    </div>
    <div class="posture {posture_class}">{_esc(posture)} · Retest T-001 {retest_label}</div>
  </header>
  <div class="decision">Decision: {_esc(go_no_go)}</div>
  <main>
    <h2>Which agents produced this dashboard</h2>
    <p class="muted">The HTML is assembled by the exporter after the loop. Each section is owned by a Foundry agent. Handoffs below are from <code>a2a-messages.json</code>.</p>
    <div class="cards" style="margin-bottom:12px">
      <div class="card"><div class="label">Engineer</div><div class="value" style="font-size:16px">asset · findings · remediations · OWASP/NIST</div></div>
      <div class="card"><div class="label">Red Team</div><div class="value" style="font-size:16px">validation · evidence · T-001 retest</div></div>
      <div class="card"><div class="label">Runtime SOC</div><div class="value" style="font-size:16px">incidents · containment status</div></div>
      <div class="card"><div class="label">Orchestrator</div><div class="value" style="font-size:16px">run order · this briefing</div></div>
    </div>
    <div class="panel" style="overflow:auto;margin-bottom:18px">
      <table>
        <thead><tr><th>From agent</th><th>To agent</th><th>Intent</th><th>Artifact</th><th>Summary</th></tr></thead>
        <tbody>{handoff_rows}</tbody>
      </table>
    </div>
    <h2>Discovered assets · AI Security Engineer</h2>
    <div class="panel" style="overflow:auto;margin-bottom:18px">
      <table>
        <thead><tr><th>Name</th><th>Type</th><th>Asset ID</th><th>Tools</th><th>Identities</th><th>Dependencies</th><th>Description</th></tr></thead>
        <tbody>{asset_rows}</tbody>
      </table>
    </div>
    <h2>Answers for leadership</h2>
    <div class="qa-grid">{qa_html}</div>
    <div class="cards" style="margin-top:18px">
      <div class="card"><div class="label">Findings</div><div class="value">{len(findings)}</div></div>
      <div class="card crit"><div class="label">Critical</div><div class="value">{critical}</div></div>
      <div class="card high"><div class="label">High</div><div class="value">{high}</div></div>
      <div class="card"><div class="label">Medium / Low</div><div class="value">{medium + low}</div></div>
      <div class="card"><div class="label">Confirmed on demo</div><div class="value">{confirmed}</div></div>
      <div class="card good"><div class="label">Retest T-001</div><div class="value">{retest_label}</div></div>
      <div class="card"><div class="label">Incidents</div><div class="value">{len(incidents)}</div></div>
      <div class="card"><div class="label">Remediations</div><div class="value">{len(remediations)}</div></div>
    </div>

    <div class="grid2" style="margin-top:18px">
      <section class="panel">
        <h2>Risk mix</h2>
        <div class="bar">
          <span style="width:{_pct(critical)}%;background:var(--crit)"></span>
          <span style="width:{_pct(high)}%;background:var(--high)"></span>
          <span style="width:{_pct(medium)}%;background:var(--med)"></span>
          <span style="width:{_pct(low)}%;background:var(--low)"></span>
        </div>
        <div class="legend">
          <span><i class="dot" style="background:var(--crit)"></i>Critical {critical}</span>
          <span><i class="dot" style="background:var(--high)"></i>High {high}</span>
          <span><i class="dot" style="background:var(--med)"></i>Medium {medium}</span>
          <span><i class="dot" style="background:var(--low)"></i>Low {low}</span>
        </div>
        <p class="muted" style="margin-top:14px">OWASP mapped {owasp_covered} covered · {owasp_na} not applicable · Demo validations confirmed {confirmed} / held {blocked_validations}</p>
      </section>
      <section class="panel">
        <h2>Incidents · AI Runtime SOC</h2>
        {incident_cards}
      </section>
    </div>

    <h2>Findings · AI Security Engineer</h2>
    <div class="filters" id="filters">
      <button class="active" data-filter="ALL">All</button>
      <button data-filter="CRITICAL">Critical</button>
      <button data-filter="HIGH">High</button>
      <button data-filter="MEDIUM">Medium</button>
    </div>
    <div class="panel" style="overflow:auto">
      <table>
        <thead><tr><th>ID</th><th>Level</th><th>Score</th><th>Threat</th><th>OWASP</th><th>ATLAS</th><th>NIST</th><th>Next control</th></tr></thead>
        <tbody>{finding_rows}</tbody>
      </table>
    </div>

    <h2>Authorized validation · AI Red Team</h2>
    <div class="panel" style="overflow:auto">
      <table>
        <thead><tr><th>Finding</th><th>Target</th><th>Type</th><th>Result</th><th>Control</th></tr></thead>
        <tbody>{attack_rows or "<tr><td colspan='5' class='muted'>No validation records.</td></tr>"}</tbody>
      </table>
    </div>

    <div class="grid2">
      <section>
        <h2>OWASP LLM Top 10</h2>
        <div class="panel" style="overflow:auto"><table><thead><tr><th>ID</th><th>Name</th><th>Status</th></tr></thead><tbody>{coverage_rows}</tbody></table></div>
      </section>
      <section>
        <h2>MITRE ATLAS</h2>
        <div class="panel" style="overflow:auto"><table><thead><tr><th>ID</th><th>Name</th><th>Status</th></tr></thead><tbody>{atlas_rows}</tbody></table></div>
      </section>
    </div>
    <h2>NIST AI RMF</h2>
    <div class="panel" style="overflow:auto"><table><thead><tr><th>Function</th><th>Covered threats</th><th>Status</th></tr></thead><tbody>{nist_rows}</tbody></table></div>
    <p class="muted">Import powerbi-risk-dataset.csv into Power BI for a live workspace report. This page contains no clinical fields.</p>
  </main>
  <script>
    const buttons = document.querySelectorAll('#filters button');
    const rows = document.querySelectorAll('.finding-row');
    buttons.forEach((btn) => btn.addEventListener('click', () => {{
      buttons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const filter = btn.dataset.filter;
      rows.forEach((row) => {{
        row.style.display = (filter === 'ALL' || row.dataset.level === filter) ? '' : 'none';
      }});
    }}));
  </script>
</body>
</html>
"""
        )
    print(f"[Dashboard] Power BI CSV: {csv_path}")
    print(f"[Dashboard] HTML: {html_path}")
    return csv_path
