# Executive dashboard and Power BI

## Local dashboard

After `python3 tests/mvp_lifecycle.py`, open:

`output/executive-dashboard.html`

## Power BI

1. Get data → Text/CSV → `output/powerbi-risk-dataset.csv`
2. Suggested visuals:
   - Card: count of findings
   - Stacked bar: `risk_level`
   - Table: `finding_id`, `threats`, `owasp_llm`, `risk_score`
3. Refresh the CSV after each lifecycle run (or point Power BI at a synced folder / storage account `source-of-truth` container later).

Do not import `output/azure_deployment_output.json` or `.env` into Power BI.

## Publish a workspace (API)

```bash
python3 tools/dashboard/publish_powerbi.py
```

Creates workspace `Foundary AI Security` and push dataset `FoundaryRiskFindings` from `output/powerbi-risk-dataset.csv`. Requires a Power BI / Fabric license. See `docs/ENTERPRISE.md`.
