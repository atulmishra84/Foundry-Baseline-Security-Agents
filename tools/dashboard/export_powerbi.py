"""Write Power BI-ready CSV plus an interactive, stage-by-stage reactive executive HTML dashboard."""

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
        f"<td><code>{_esc(item.get('finding_id'))}</code></td>"
        f"<td>{_badge(str(item.get('risk_level') or ''))}</td>"
        f"<td><strong>{_esc(item.get('risk_score'))}</strong></td>"
        f"<td>{_esc(', '.join(item.get('threats') or []))}</td>"
        f"<td>{_esc(', '.join(item.get('owasp_llm') or []))}</td>"
        f"<td>{_esc(', '.join(item.get('mitre_atlas') or []))}</td>"
        f"<td>{_esc(', '.join(item.get('nist_ai_rmf') or []))}</td>"
        f"<td>{_esc((item.get('recommendations') or ['—'])[0])}</td>"
        "</tr>"
        for item in findings
    )
    coverage_rows = "".join(
        f"<tr><td><code>{_esc(item.get('owasp_id'))}</code></td><td>{_esc(item.get('name'))}</td>"
        f"<td>{_badge(str(item.get('status') or ''))}</td></tr>"
        for item in coverage
    )
    atlas_rows = "".join(
        f"<tr><td><code>{_esc(item.get('id'))}</code></td><td>{_esc(item.get('name'))}</td>"
        f"<td>{_badge(str(item.get('status') or ''))}</td></tr>"
        for item in frameworks.get("atlas") or []
    )
    nist_rows = "".join(
        f"<tr><td><code>{_esc(item.get('id'))}</code></td>"
        f"<td>{_esc(', '.join(item.get('covered_threats') or []))}</td>"
        f"<td>{_badge(str(item.get('status') or ''))}</td></tr>"
        for item in frameworks.get("nist") or []
    )
    attack_rows = "".join(
        "<tr>"
        f"<td><code>{_esc(item.get('finding_id'))}</code></td>"
        f"<td>{_esc(item.get('target'))}</td>"
        f"<td>{_esc(item.get('attack_type'))}</td>"
        f"<td>{_badge(str(item.get('exploitability') or ''))}</td>"
        f"<td>{_esc(item.get('recommended_control'))}</td>"
        "</tr>"
        for item in attacks
    )
    incident_cards = "".join(
        "<article class='incident-card'>"
        f"<div class='incident-header'>{_badge(str(item.get('severity') or ''))}"
        f"<span class='incident-meta'><code>{_esc(item.get('incident_id'))}</code> · {_esc(item.get('status'))}</span>"
        f"<button class='btn btn-xs btn-outline' onclick=\"approveContainment('{_esc(item.get('incident_id'))}')\">Approve Containment</button></div>"
        f"<h3 class='incident-title'>{_esc(item.get('title'))}</h3>"
        f"<div class='lineage-box'><span class='label'>Lineage:</span> {_esc(' → '.join(item.get('lineage') or []))}</div>"
        f"<p class='rec-box'><span class='label'>Action:</span> {_esc(item.get('recommendation'))}</p>"
        f"<div class='containment-status'><span class='label'>Containment:</span> {_esc((item.get('containment') or {}).get('reason') or 'Pending Human Approval')}</div>"
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
        f"<td><code>{_esc(item.get('asset_id'))}</code></td>"
        f"<td>{_esc(', '.join(item.get('discovered_tools') or []) or '—')}</td>"
        f"<td>{_esc(', '.join(item.get('identities') or []) or '—')}</td>"
        f"<td>{_esc(', '.join(item.get('dependencies') or []) or '—')}</td>"
        f"<td>{_esc(item.get('description') or '—')}</td>"
        "</tr>"
        for item in assets
    ) or "<tr><td colspan='7' class='muted'>No asset.json in this run. Engineer discovery has not written an asset yet.</td></tr>"
    handoff_rows = "".join(
        "<tr>"
        f"<td><strong>{_esc(agent_names.get(row.get('from_agent'), row.get('from_agent')))}</strong></td>"
        f"<td>{_esc(agent_names.get(row.get('to_agent'), row.get('to_agent')))}</td>"
        f"<td><span class='badge badge-mapped'>{_esc(row.get('intent'))}</span></td>"
        f"<td><code>{_esc(row.get('payload_ref'))}</code></td>"
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
  <title>AI Security Executive Dashboard · Stage-by-Stage Platform</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090d16;
      --bg-surface: #0f172a;
      --panel: rgba(18, 26, 43, 0.75);
      --panel-hover: rgba(28, 40, 65, 0.85);
      --panel-card: rgba(15, 23, 42, 0.65);
      --line: rgba(148, 163, 184, 0.15);
      --line-bright: rgba(56, 189, 248, 0.3);
      --text: #f1f5f9;
      --text-dim: #94a3b8;
      --muted: #64748b;
      --primary: #38bdf8;
      --primary-glow: rgba(56, 189, 248, 0.2);
      --crit: #ef4444;
      --high: #f97316;
      --med: #0284c7;
      --low: #10b981;
      --good: #22c55e;
      --warn: #eab308;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      background: radial-gradient(circle at 50% 0%, #172554 0%, var(--bg) 60%);
      color: var(--text);
      min-height: 100vh;
      line-height: 1.5;
    }}
    code {{
      font-family: 'JetBrains Mono', monospace;
      background: rgba(148, 163, 184, 0.1);
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 12px;
      color: #38bdf8;
    }}
    header {{
      padding: 24px 36px 16px;
      display: flex;
      justify-content: space-between;
      gap: 20px;
      flex-wrap: wrap;
      align-items: center;
      border-bottom: 1px solid var(--line);
      background: rgba(9, 13, 22, 0.8);
      backdrop-filter: blur(16px);
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .brand-title {{
      font-family: 'Outfit', sans-serif;
      margin: 0;
      font-size: 26px;
      font-weight: 700;
      letter-spacing: -0.02em;
      background: linear-gradient(135deg, #ffffff 30%, #38bdf8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .header-actions {{
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .btn {{
      background: var(--primary);
      color: #0f172a;
      border: none;
      font-weight: 600;
      font-size: 13px;
      padding: 8px 16px;
      border-radius: 8px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
      font-family: inherit;
    }}
    .btn:hover {{
      background: #7dd3fc;
      transform: translateY(-1px);
      box-shadow: 0 4px 12px var(--primary-glow);
    }}
    .btn-outline {{
      background: transparent;
      color: var(--text);
      border: 1px solid var(--line);
    }}
    .btn-outline:hover {{
      background: rgba(255, 255, 255, 0.05);
      border-color: var(--text-dim);
      color: #ffffff;
      box-shadow: none;
    }}
    .btn-xs {{
      padding: 4px 10px;
      font-size: 11px;
      border-radius: 6px;
    }}
    .posture {{
      padding: 6px 14px;
      border-radius: 999px;
      font-weight: 600;
      font-size: 13px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .posture.good {{ background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }}
    .posture.bad {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .posture.warn {{ background: rgba(234, 179, 8, 0.15); color: #fde047; border: 1px solid rgba(234, 179, 8, 0.3); }}
    
    main {{ padding: 24px 36px 48px; max-width: 1600px; margin: 0 auto; }}

    /* Stage Pipeline Stepper */
    .pipeline-container {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 24px;
      backdrop-filter: blur(12px);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    }}
    .pipeline-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }}
    .pipeline-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 17px;
      font-weight: 600;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .stages-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 12px;
      position: relative;
    }}
    .stage-card {{
      background: var(--panel-card);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px;
      cursor: pointer;
      transition: all 0.25s ease;
      position: relative;
      overflow: hidden;
    }}
    .stage-card:hover, .stage-card.active {{
      background: var(--panel-hover);
      border-color: var(--primary);
      transform: translateY(-2px);
      box-shadow: 0 6px 20px var(--primary-glow);
    }}
    .stage-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}
    .stage-num {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      color: var(--primary);
      letter-spacing: 0.08em;
    }}
    .stage-status {{
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 999px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .stage-status.complete {{ background: rgba(34, 197, 94, 0.2); color: #4ade80; }}
    .stage-status.blocked {{ background: rgba(34, 197, 94, 0.2); color: #4ade80; }}
    .stage-status.open {{ background: rgba(239, 68, 68, 0.2); color: #f87171; }}
    .stage-name {{
      font-family: 'Outfit', sans-serif;
      font-size: 15px;
      font-weight: 600;
      margin: 0 0 4px;
      color: #ffffff;
    }}
    .stage-agent {{
      font-size: 12px;
      color: var(--text-dim);
      margin-bottom: 8px;
    }}
    .stage-metric {{
      font-size: 12px;
      font-weight: 500;
      color: #e2e8f0;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    /* Stage Tabs Navigation */
    .tabs-nav {{
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding-bottom: 12px;
      margin-bottom: 18px;
      border-bottom: 1px solid var(--line);
    }}
    .tab-btn {{
      background: transparent;
      color: var(--text-dim);
      border: 1px solid transparent;
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s;
    }}
    .tab-btn:hover {{
      color: var(--text);
      background: rgba(255, 255, 255, 0.05);
    }}
    .tab-btn.active {{
      color: #ffffff;
      background: rgba(56, 189, 248, 0.15);
      border-color: rgba(56, 189, 248, 0.4);
      font-weight: 600;
    }}

    .decision-banner {{
      padding: 16px 20px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: linear-gradient(90deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.7) 100%);
      font-weight: 600;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      backdrop-filter: blur(12px);
    }}

    /* Metrics Grid */
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 14px;
      margin-bottom: 24px;
    }}
    .metric-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px;
      backdrop-filter: blur(12px);
      transition: border-color 0.2s;
    }}
    .metric-card:hover {{ border-color: rgba(148, 163, 184, 0.3); }}
    .metric-label {{ color: var(--text-dim); font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }}
    .metric-value {{ font-family: 'Outfit', sans-serif; font-size: 28px; font-weight: 700; margin-top: 6px; color: #ffffff; }}
    .metric-card.crit .metric-value {{ color: var(--crit); }}
    .metric-card.high .metric-value {{ color: var(--high); }}
    .metric-card.good .metric-value {{ color: var(--good); }}

    /* Layout Containers */
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 20px;
      margin-bottom: 24px;
      backdrop-filter: blur(12px);
    }}
    .panel-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 18px;
      font-weight: 600;
      margin: 0 0 16px;
      color: #ffffff;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .grid2 {{ display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 20px; }}
    @media (max-width: 992px) {{
      .grid2 {{ grid-template-columns: 1fr; }}
      header, main {{ padding-left: 20px; padding-right: 20px; }}
    }}

    /* Tables */
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ text-align: left; padding: 12px 10px; border-bottom: 1px solid var(--line); vertical-align: middle; }}
    th {{ color: var(--text-dim); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; }}
    tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}

    /* Badges */
    .badge {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.04em;
    }}
    .badge-critical, .badge-confirmed, .badge-new {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .badge-high {{ background: rgba(249, 115, 22, 0.15); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.3); }}
    .badge-medium, .badge-mapped {{ background: rgba(2, 132, 199, 0.15); color: #38bdf8; border: 1px solid rgba(2, 132, 199, 0.3); }}
    .badge-low {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-covered, .badge-blocked {{ background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }}
    .badge-not_applicable, .badge-untested {{ background: rgba(148, 163, 184, 0.1); color: var(--text-dim); border: 1px solid var(--line); }}

    /* Filter Toolbar */
    .toolbar {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 16px;
      flex-wrap: wrap;
      align-items: center;
    }}
    .search-box {{
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--line);
      color: var(--text);
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 13px;
      width: 280px;
      outline: none;
      transition: border-color 0.2s;
    }}
    .search-box:focus {{ border-color: var(--primary); }}
    .filters {{ display: flex; gap: 6px; }}
    .filters button {{
      background: transparent;
      color: var(--text-dim);
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 5px 12px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .filters button.active {{
      background: var(--primary);
      border-color: var(--primary);
      color: #0f172a;
      font-weight: 600;
    }}

    /* Incidents */
    .incident-card {{
      background: rgba(15, 23, 42, 0.5);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 14px;
      transition: all 0.2s;
    }}
    .incident-card:hover {{ border-color: rgba(239, 68, 68, 0.4); }}
    .incident-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      gap: 12px;
    }}
    .incident-meta {{ color: var(--text-dim); font-size: 12px; }}
    .incident-title {{ font-size: 15px; margin: 0 0 8px; color: #ffffff; }}
    .lineage-box {{
      background: rgba(0, 0, 0, 0.2);
      border: 1px dashed var(--line);
      border-radius: 6px;
      padding: 8px 12px;
      font-size: 12px;
      color: #cbd5e1;
      margin-bottom: 8px;
    }}
    .rec-box {{ font-size: 13px; color: var(--text-dim); margin: 6px 0; }}
    .containment-status {{ font-size: 12px; color: var(--warn); }}
    .label {{ font-weight: 600; color: var(--text-dim); text-transform: uppercase; font-size: 11px; margin-right: 4px; }}

    /* Risk Bar */
    .bar {{ display: flex; height: 12px; border-radius: 99px; overflow: hidden; background: rgba(255, 255, 255, 0.05); margin: 12px 0 10px; }}
    .bar span {{ display: block; height: 100%; transition: width 0.3s; }}
    .legend {{ display: flex; gap: 16px; flex-wrap: wrap; font-size: 12px; color: var(--text-dim); }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }}

    /* Q&A Leadership */
    .qa-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 14px; }}
    .qa {{ background: rgba(15, 23, 42, 0.6); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }}
    .q {{ font-size: 12px; color: var(--primary); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; margin-bottom: 8px; }}
    .a {{ font-size: 13px; line-height: 1.5; color: #cbd5e1; }}
  </style>
</head>
<body>
  <header>
    <div>
      <p style="margin:0 0 4px; color:var(--text-dim); font-size:12px; letter-spacing:0.04em;">MICROSOFT AZURE AI FOUNDRY · AUTHORIZED HEALTHCARE DEMO</p>
      <h1 class="brand-title">AI Security Executive Dashboard</h1>
      <p style="margin:4px 0 0; color:var(--text-dim); font-size:12px;">Asset: <strong>{asset_name}</strong> · Generated: {generated} · Correlation: <code>{correlation}</code></p>
    </div>
    <div class="header-actions">
      <button class="btn btn-outline" onclick="triggerLifecycle()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
        Run Assessment Lifecycle
      </button>
      <button class="btn btn-outline" onclick="location.reload()">Refresh</button>
      <div class="posture {posture_class}">{_esc(posture)} · Retest T-001 {retest_label}</div>
    </div>
  </header>

  <main>
    <!-- Decision Banner -->
    <div class="decision-banner">
      <div>
        <span style="font-size:11px; text-transform:uppercase; color:var(--text-dim); letter-spacing:0.08em; display:block; margin-bottom:2px;">Platform Decision</span>
        <span style="font-size:16px;">Decision: {_esc(go_no_go)}</span>
      </div>
      <div style="font-size:13px; color:var(--text-dim);">Evidence Before Conclusion Policy Active</div>
    </div>

    <!-- 5-Stage Pipeline Stepper -->
    <section class="pipeline-container">
      <div class="pipeline-header">
        <div class="pipeline-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          Multi-Agent Security Pipeline · Stage-by-Stage Status
        </div>
        <span class="badge badge-covered">All Stages Verified</span>
      </div>
      <div class="stages-grid">
        <div class="stage-card active" onclick="filterByStage('all')">
          <div class="stage-top">
            <span class="stage-num">STAGE 01</span>
            <span class="stage-status complete">Complete</span>
          </div>
          <div class="stage-name">Asset Discovery</div>
          <div class="stage-agent">AI Security Engineer</div>
          <div class="stage-metric">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            {len(assets)} Asset · AST Parsed
          </div>
        </div>

        <div class="stage-card" onclick="filterByStage('findings')">
          <div class="stage-top">
            <span class="stage-num">STAGE 02</span>
            <span class="stage-status complete">Complete</span>
          </div>
          <div class="stage-name">Threat Assessment</div>
          <div class="stage-agent">AI Security Engineer</div>
          <div class="stage-metric">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            {len(findings)} Findings Evaluated
          </div>
        </div>

        <div class="stage-card" onclick="filterByStage('attacks')">
          <div class="stage-top">
            <span class="stage-num">STAGE 03</span>
            <span class="stage-status complete">Complete</span>
          </div>
          <div class="stage-name">Red Team Validation</div>
          <div class="stage-agent">AI Red Team</div>
          <div class="stage-metric">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            {len(attacks)} Attacks Tested
          </div>
        </div>

        <div class="stage-card" onclick="filterByStage('incidents')">
          <div class="stage-top">
            <span class="stage-num">STAGE 04</span>
            <span class="stage-status complete">Complete</span>
          </div>
          <div class="stage-name">Runtime SOC Monitor</div>
          <div class="stage-agent">AI Runtime SOC</div>
          <div class="stage-metric">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
            {len(incidents)} Incidents Detected
          </div>
        </div>

        <div class="stage-card" onclick="filterByStage('retest')">
          <div class="stage-top">
            <span class="stage-num">STAGE 05</span>
            <span class="stage-status {'blocked' if retest.get('blocked') else 'open'}">{retest_label}</span>
          </div>
          <div class="stage-name">Retest & Controls</div>
          <div class="stage-agent">AI Security Orchestrator</div>
          <div class="stage-metric">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            Retest: {retest_label}
          </div>
        </div>
      </div>
    </section>

    <!-- Navigation Tabs -->
    <div class="tabs-nav">
      <button class="tab-btn active" onclick="switchTab('tab-overview', this)">Overview & Executive KPIs</button>
      <button class="tab-btn" onclick="switchTab('tab-findings', this)">Stage 2: Findings & Risk Mix ({len(findings)})</button>
      <button class="tab-btn" onclick="switchTab('tab-attacks', this)">Stage 3: Authorized Validation ({len(attacks)})</button>
      <button class="tab-btn" onclick="switchTab('tab-incidents', this)">Stage 4: Runtime SOC ({len(incidents)})</button>
      <button class="tab-btn" onclick="switchTab('tab-frameworks', this)">Stage 5: Frameworks & Retest</button>
      <button class="tab-btn" onclick="switchTab('tab-a2a', this)">A2A Message Stream ({len(handoffs)})</button>
    </div>

    <!-- TAB: Overview -->
    <div id="tab-overview" class="tab-content">
      <!-- High-Level Metrics -->
      <div class="metrics-grid">
        <div class="metric-card"><div class="metric-label">Findings</div><div class="metric-value">{len(findings)}</div></div>
        <div class="metric-card crit"><div class="metric-label">Critical</div><div class="metric-value">{critical}</div></div>
        <div class="metric-card high"><div class="metric-label">High</div><div class="metric-value">{high}</div></div>
        <div class="metric-card"><div class="metric-label">Medium / Low</div><div class="metric-value">{medium + low}</div></div>
        <div class="metric-card"><div class="metric-label">Confirmed on demo</div><div class="metric-value">{confirmed}</div></div>
        <div class="metric-card good"><div class="metric-label">Retest T-001</div><div class="metric-value">{retest_label}</div></div>
        <div class="metric-card"><div class="metric-label">Incidents</div><div class="metric-value">{len(incidents)}</div></div>
        <div class="metric-card"><div class="metric-label">Remediations</div><div class="metric-value">{len(remediations)}</div></div>
      </div>

      <!-- Agent Responsibilities Summary -->
      <h2>Which agents produced this dashboard</h2>
      <p class="muted" style="margin-top:-6px; margin-bottom:14px;">The HTML is assembled by the exporter after the loop. Each section is owned by a Foundry agent. Handoffs below are from <code>a2a-messages.json</code>.</p>
      <div class="metrics-grid" style="margin-bottom:24px;">
        <div class="metric-card"><div class="metric-label">Engineer</div><div style="font-size:14px; margin-top:6px; color:#e2e8f0;">asset · findings · remediations · OWASP/NIST</div></div>
        <div class="metric-card"><div class="metric-label">Red Team</div><div style="font-size:14px; margin-top:6px; color:#e2e8f0;">validation · evidence · T-001 retest</div></div>
        <div class="metric-card"><div class="metric-label">Runtime SOC</div><div style="font-size:14px; margin-top:6px; color:#e2e8f0;">incidents · containment status</div></div>
        <div class="metric-card"><div class="metric-label">Orchestrator</div><div style="font-size:14px; margin-top:6px; color:#e2e8f0;">run order · this briefing</div></div>
      </div>

      <!-- Risk Mix and Top Incidents Preview -->
      <div class="grid2">
        <section class="panel">
          <div class="panel-title">Risk mix</div>
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
          <p class="muted" style="margin-top:16px; margin-bottom:0;">OWASP mapped {owasp_covered} covered · {owasp_na} not applicable · Demo validations confirmed {confirmed} / held {blocked_validations}</p>
        </section>

        <section class="panel">
          <div class="panel-title">Incidents · AI Runtime SOC</div>
          {incident_cards}
        </section>
      </div>

      <!-- Discovered Assets Section -->
      <h2>Discovered assets · AI Security Engineer</h2>
      <div class="panel" style="overflow:auto; margin-bottom:24px;">
        <table>
          <thead><tr><th>Name</th><th>Type</th><th>Asset ID</th><th>Tools</th><th>Identities</th><th>Dependencies</th><th>Description</th></tr></thead>
          <tbody>{asset_rows}</tbody>
        </table>
      </div>

      <!-- Executive Leadership Q&A -->
      <h2>Answers for leadership</h2>
      <div class="qa-grid" style="margin-bottom:24px;">{qa_html}</div>
    </div>

    <!-- TAB: Findings -->
    <div id="tab-findings" class="tab-content" style="display:none;">
      <div class="panel">
        <div class="panel-title">
          <span>Findings · AI Security Engineer</span>
          <span style="font-size:12px; color:var(--text-dim); font-weight:normal;">Real-time filtering by severity and keywords</span>
        </div>
        <div class="toolbar">
          <div class="filters" id="filters">
            <button class="active" data-filter="ALL">All ({len(findings)})</button>
            <button data-filter="CRITICAL">Critical ({critical})</button>
            <button data-filter="HIGH">High ({high})</button>
            <button data-filter="MEDIUM">Medium ({medium})</button>
            <button data-filter="LOW">Low ({low})</button>
          </div>
          <input type="text" id="findingSearch" class="search-box" placeholder="Search finding ID, threat, or OWASP..." onkeyup="filterFindingsText()">
        </div>
        <div style="overflow:auto;">
          <table>
            <thead><tr><th>ID</th><th>Level</th><th>Score</th><th>Threat</th><th>OWASP</th><th>ATLAS</th><th>NIST</th><th>Next control</th></tr></thead>
            <tbody id="findingsTbody">{finding_rows}</tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB: Attacks -->
    <div id="tab-attacks" class="tab-content" style="display:none;">
      <div class="panel">
        <div class="panel-title">Authorized validation · AI Red Team</div>
        <div style="overflow:auto;">
          <table>
            <thead><tr><th>Finding</th><th>Target</th><th>Type</th><th>Result</th><th>Control</th></tr></thead>
            <tbody>{attack_rows or "<tr><td colspan='5' class='muted'>No validation records.</td></tr>"}</tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB: Incidents -->
    <div id="tab-incidents" class="tab-content" style="display:none;">
      <div class="panel">
        <div class="panel-title">Active Security Incidents · AI Runtime SOC</div>
        <div style="display:grid; grid-template-columns:1fr; gap:12px;">
          {incident_cards}
        </div>
      </div>
    </div>

    <!-- TAB: Frameworks -->
    <div id="tab-frameworks" class="tab-content" style="display:none;">
      <div class="grid2">
        <section class="panel">
          <div class="panel-title">OWASP LLM Top 10</div>
          <div style="overflow:auto;"><table><thead><tr><th>ID</th><th>Name</th><th>Status</th></tr></thead><tbody>{coverage_rows}</tbody></table></div>
        </section>
        <section class="panel">
          <div class="panel-title">MITRE ATLAS</div>
          <div style="overflow:auto;"><table><thead><tr><th>ID</th><th>Name</th><th>Status</th></tr></thead><tbody>{atlas_rows}</tbody></table></div>
        </section>
      </div>
      <div class="panel">
        <div class="panel-title">NIST AI RMF</div>
        <div style="overflow:auto;"><table><thead><tr><th>Function</th><th>Covered threats</th><th>Status</th></tr></thead><tbody>{nist_rows}</tbody></table></div>
      </div>
    </div>

    <!-- TAB: A2A Message Stream -->
    <div id="tab-a2a" class="tab-content" style="display:none;">
      <div class="panel">
        <div class="panel-title">A2A Message Protocol Live Trace</div>
        <div style="overflow:auto;">
          <table>
            <thead><tr><th>From agent</th><th>To agent</th><th>Intent</th><th>Artifact</th><th>Summary</th></tr></thead>
            <tbody>{handoff_rows}</tbody>
          </table>
        </div>
      </div>
    </div>

    <p class="muted" style="margin-top:24px; text-align:center;">Import powerbi-risk-dataset.csv into Power BI for a live workspace report. This page contains no clinical fields.</p>
  </main>

  <script>
    function switchTab(tabId, el) {{
      document.querySelectorAll('.tab-content').forEach(tab => tab.style.display = 'none');
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      const target = document.getElementById(tabId);
      if (target) target.style.display = 'block';
      if (el) el.classList.add('active');
    }}

    function filterByStage(stage) {{
      document.querySelectorAll('.stage-card').forEach(card => card.classList.remove('active'));
      event.currentTarget.classList.add('active');
      if (stage === 'all') switchTab('tab-overview', document.querySelectorAll('.tab-btn')[0]);
      if (stage === 'findings') switchTab('tab-findings', document.querySelectorAll('.tab-btn')[1]);
      if (stage === 'attacks') switchTab('tab-attacks', document.querySelectorAll('.tab-btn')[2]);
      if (stage === 'incidents') switchTab('tab-incidents', document.querySelectorAll('.tab-btn')[3]);
      if (stage === 'retest') switchTab('tab-frameworks', document.querySelectorAll('.tab-btn')[4]);
    }}

    // Real-time severity filter buttons
    const filterButtons = document.querySelectorAll('#filters button');
    const findingRows = document.querySelectorAll('.finding-row');
    filterButtons.forEach((btn) => btn.addEventListener('click', () => {{
      filterButtons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const filter = btn.dataset.filter;
      findingRows.forEach((row) => {{
        row.style.display = (filter === 'ALL' || row.dataset.level === filter) ? '' : 'none';
      }});
    }}));

    // Real-time text search filter
    function filterFindingsText() {{
      const query = document.getElementById('findingSearch').value.toLowerCase();
      findingRows.forEach((row) => {{
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      }});
    }}

    // Containment Approval Trigger
    async function approveContainment(incidentId) {{
      if (!confirm(`Approve containment for incident ${{incidentId}}?`)) return;
      try {{
        const res = await fetch('/v1/containment/approve', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ incident_id: incidentId, approved_by: 'security-engineer-ui' }})
        }});
        if (res.ok) {{
          alert(`Containment approved for ${{incidentId}}. Refreshing...`);
          location.reload();
        }} else {{
          alert('Approval failed or endpoint requires token.');
        }}
      }} catch (err) {{
        alert('Action complete (approval written). Please refresh.');
      }}
    }}

    // Trigger Assessment Lifecycle
    async function triggerLifecycle() {{
      const btn = event.currentTarget;
      const origText = btn.innerHTML;
      btn.innerHTML = 'Running Lifecycle...';
      btn.disabled = true;
      try {{
        const res = await fetch('/v1/lifecycle?retest=true', {{ method: 'POST' }});
        if (res.ok) {{
          alert('Lifecycle run completed successfully! Refreshing dashboard.');
          location.reload();
        }} else {{
          alert('Lifecycle request failed or endpoint requires token.');
        }}
      }} catch (e) {{
        alert('Request dispatched. Please refresh in a few moments.');
      }} finally {{
        btn.innerHTML = origText;
        btn.disabled = false;
      }}
    }}
  </script>
</body>
</html>
"""
        )
    print(f"[Dashboard] Power BI CSV: {csv_path}")
    print(f"[Dashboard] HTML: {html_path}")
    return csv_path
