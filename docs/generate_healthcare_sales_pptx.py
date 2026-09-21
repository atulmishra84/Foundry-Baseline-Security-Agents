"""
Healthcare sales / investment briefing.
Senior-consultant tone. Facts match the shipped Foundary platform.
Run: python3 docs/generate_healthcare_sales_pptx.py
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

NAVY = RGBColor(0x0B, 0x1F, 0x3A)
INK = RGBColor(0x1B, 0x24, 0x33)
MUTED = RGBColor(0x5B, 0x67, 0x7A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PALE = RGBColor(0xF4, 0xF6, 0xFA)
LINE = RGBColor(0xD8, 0xDE, 0xE8)
BLUE = RGBColor(0x1D, 0x4E, 0xD8)
TEAL = RGBColor(0x0F, 0x76, 0x6E)
RED = RGBColor(0xB9, 0x1C, 0x1C)
GOLD = RGBColor(0xB4, 0x53, 0x09)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Foundary-Healthcare-AI-Security-Brief.pptx"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def slide():
    return prs.slides.add_slide(BLANK)


def rect(s, x, y, w, h, color):
    shp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    return shp


def text(s, content, x, y, w, h, size=16, bold=False, color=INK, align=PP_ALIGN.LEFT):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = content
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = "Calibri"
    return box


def bullets(s, items, x, y, w, h, size=15):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = "•  " + item
        run.font.size = Pt(size)
        run.font.color.rgb = INK
        run.font.name = "Calibri"
        p.space_after = Pt(8)
    return box


def footer(s, page, total=16):
    text(s, "Foundary  |  Confidential  |  Healthcare AI Security briefing", 0.5, 7.15, 9, 0.25, 10, False, MUTED)
    text(s, f"{page}  /  {total}", 11.6, 7.15, 1.3, 0.25, 10, False, MUTED, PP_ALIGN.RIGHT)


def header_bar(s, kicker, title):
    rect(s, 0, 0, 13.333, 7.5, PALE)
    rect(s, 0, 0, 0.12, 7.5, BLUE)
    text(s, kicker.upper(), 0.5, 0.22, 12, 0.28, 11, True, BLUE)
    text(s, title, 0.5, 0.48, 12.3, 0.55, 26, True, NAVY)


# 1 Title
s = slide()
rect(s, 0, 0, 13.333, 7.5, NAVY)
rect(s, 0, 0, 0.14, 7.5, GOLD)
text(s, "CONFIDENTIAL  ·  HEALTHCARE BUYER BRIEFING", 0.6, 0.45, 12, 0.3, 12, True, GOLD)
text(s, "Secure the AI that\ntouches the patient record", 0.6, 1.3, 12, 2.0, 40, True, WHITE)
text(
    s,
    "Foundary on Microsoft Azure AI Foundry — a closed-loop AI security system for agentic\n"
    "clinical and operational assistants. Discover. Evidence. Validate. Retest. Brief the board.",
    0.6,
    3.6,
    11.5,
    1.2,
    18,
    False,
    RGBColor(0xC5, 0xD0, 0xDE),
)
text(s, "Prepared as a product + strategy recommendation  ·  September 2026", 0.6, 6.5, 10, 0.3, 13, False, RGBColor(0x9A, 0xA8, 0xB8))
text(s, "1  /  16", 11.6, 7.15, 1.3, 0.25, 10, False, RGBColor(0x9A, 0xA8, 0xB8), PP_ALIGN.RIGHT)

# 2 The ask
header_bar(s := slide(), "The decision", "What we are asking a healthcare buyer to decide")
bullets(
    s,
    [
        "Buy a purpose-built control plane for AI agents that can search patients, book visits, or summarize charts — not another generic SOC seat.",
        "Place it next to where those agents are already built: Azure AI Foundry (your tenant, your model, your evidence).",
        "Accept a controlled first scope: authorized systems only, human approval before containment, no “spray and pray” red team against the EHR.",
        "Do not substitute this with “we already own Security Copilot / Defender / a WAF.” Those tools do not close the AI-agent loop.",
    ],
    0.5,
    1.3,
    12.2,
    4.8,
    18,
)
footer(s, 2)

# 3 Why now
header_bar(s := slide(), "Industry context", "Why this is a 2026 healthcare problem, not a lab toy")
items = [
    ("Agents are in the workflow", "Patient search, intake, prior-auth drafts, and nursing copilots invoke tools. A prompt is now an access path."),
    ("HIPAA still applies", "If the model can dump a store, that is an ePHI event — even when the “UI” looked like a chatbot."),
    ("Boards will ask", "“Show me evidence the copilot cannot be instructed to ignore policy.” Annual pentest PDFs will not suffice."),
    ("Azure is already chosen", "Most IDNs building agents are on OpenAI in Azure. Security that does not live on Foundry becomes shadow IT."),
]
for i, (h, b) in enumerate(items):
    x = 0.5 + (i % 2) * 6.4
    y = 1.25 + (i // 2) * 2.6
    rect(s, x, y, 6.15, 2.4, WHITE)
    text(s, h, x + 0.25, y + 0.2, 5.7, 0.45, 18, True, NAVY)
    text(s, b, x + 0.25, y + 0.75, 5.7, 1.4, 14, False, MUTED)
footer(s, 3)

# 4 Problem
header_bar(s := slide(), "The gap", "What known tools actually see vs what the agent does")
text(s, "Known stack", 0.5, 1.2, 6, 0.35, 16, True, RED)
bullets(
    s,
    [
        "Defender / CSPM: VMs, identities, public blobs — not prompt injection.",
        "WAF / API gateway: HTTP schema, not instruction override.",
        "SAST/SCA: libraries, not tool dumps when patient_id is null.",
        "Security Copilot: excellent SOC copilot; it does not own your AI SoT or retest.",
        "Annual red team: one week, one report, no closed-loop control proof.",
    ],
    0.5,
    1.6,
    6.0,
    4.8,
    14,
)
text(s, "What failed in our authorized healthcare demo", 6.9, 1.2, 6, 0.35, 16, True, TEAL)
bullets(
    s,
    [
        "T-001: instruction-override returned bulk mock records.",
        "T-002 / T-006: patient_search + system-admin identity.",
        "SOC raised a CRITICAL incident — containment stayed human-gated.",
        "Retest on the hardened copy: T-001 BLOCKED.",
        "That is the story a CISO can take to compliance: fail, fix, prove.",
    ],
    6.9,
    1.6,
    5.9,
    4.8,
    14,
)
footer(s, 4)

# 5 What it is
header_bar(s := slide(), "The product", "Foundary: three specialists, one Source of Truth, one loop")
cards = [
    ("AI Security Engineer", "Discovers the agent, scores T-001–T-010, maps OWASP / ATLAS / NIST, drafts remediations."),
    ("AI Red Team", "Validates only allowlisted targets. Records CONFIRMED / BLOCKED. No freelance exploits."),
    ("AI Runtime SOC", "Turns evidence into incidents and lineage. Containment requires written approval."),
    ("Orchestrator + runtime", "Foundry agents call the Container App. JSON to blob. Executive dashboard for the board."),
]
for i, (h, b) in enumerate(cards):
    y = 1.2 + i * 1.35
    rect(s, 0.5, y, 12.3, 1.25, WHITE)
    text(s, h, 0.75, y + 0.15, 11.8, 0.35, 18, True, NAVY)
    text(s, b, 0.75, y + 0.55, 11.8, 0.55, 15, False, MUTED)
footer(s, 5)

# 6 How a health system uses it
header_bar(s := slide(), "Usage", "How a health system would run this in week one")
steps = [
    "1. Inventory the AI assistants that can touch scheduling, HIM, or clinical search. Put only authorized systems on the allowlist.",
    "2. Operator (Entra) opens Foundry project → Orchestrator Playground → “Call runLifecycle with retest true.” Or POST /v1/lifecycle.",
    "3. Engineer writes asset / finding / remediation JSON. Red Team confirms T-001 on the authorized build only.",
    "4. SOC opens an incident. Nobody disables an identity until Security + Compliance sign the approval file.",
    "5. Retest the hardened control. Dashboard states GO / NO-GO. Export CSV to Power BI if the CISO wants a workspace.",
    "6. Repeat when the agent, tools, or model deployment changes — not once a year.",
]
bullets(s, steps, 0.5, 1.25, 12.3, 5.6, 16)
footer(s, 6)

# 7 Technical architecture
header_bar(s := slide(), "Technical fact base", "What is actually running (no vapor)")
bullets(
    s,
    [
        "Azure: Hub + project on AI Foundry, Azure OpenAI gpt-4o, Key Vault, Storage, Log Analytics, Container Apps runtime.",
        "Loop: discover → assess → remediate → authorized validate → detect → retest T-001 on hardened copy.",
        "SoT: threats T-001–T-010, controls CTRL-001–007, OWASP LLM Top 10 2025, MITRE ATLAS, NIST AI RMF.",
        "Artifacts: asset, finding, remediation, attack, evidence (PHI redacted), incident, framework coverage, dashboard HTML.",
        "Safety: production.json allowlist; Red Team cannot aim at an EHR URL; SOC Graph disable is one demo SP only.",
        "Network: hybrid private endpoints on storage / KV / OpenAI; public access still on until VPN/Bastion cutover.",
        "Auth today: humans Entra; some agent connections still API key / Bearer — call that out as the Entra-only backlog.",
    ],
    0.5,
    1.2,
    12.3,
    5.7,
    15,
)
footer(s, 7)

# 8 Demo proof
header_bar(s := slide(), "Proof, not a slideware screenshot", "Authorized healthcare assistant — last closed loop")
metrics = [
    ("8", "Findings"),
    ("2", "Critical"),
    ("3", "High"),
    ("1", "Confirmed T-001"),
    ("1", "Incident"),
    ("BLOCKED", "Retest"),
]
for i, (n, l) in enumerate(metrics):
    x = 0.5 + i * 2.1
    rect(s, x, 1.3, 1.95, 1.7, WHITE)
    text(s, n, x, 1.45, 1.95, 0.7, 22, True, NAVY, PP_ALIGN.CENTER)
    text(s, l, x, 2.25, 1.95, 0.5, 12, False, MUTED, PP_ALIGN.CENTER)
text(
    s,
    "Decision the dashboard already prints: NO-GO for the unprotected demo. GO to keep the hardened control set.\n"
    "That is the buying motion: we do not ask you to trust a model. We ask you to trust a repeatable fail / fix / prove cycle.",
    0.5,
    3.3,
    12.3,
    1.4,
    16,
    False,
    INK,
)
bullets(
    s,
    [
        "Evidence never stores clinical fields — record ids + [REDACTED] only.",
        "Same loop is callable from Foundry (OpenAPI + connection) or the Container App.",
    ],
    0.5,
    4.8,
    12.3,
    1.6,
    15,
)
footer(s, 8)

# 9 Why buy
header_bar(s := slide(), "Why buy Foundary", "The healthcare-specific reasons this is worth a budget line")
bullets(
    s,
    [
        "It speaks the threat language regulators will borrow: OWASP LLM, ATLAS, NIST AI RMF — mapped to one SoT.",
        "It is built for agents with tools (patient_search), not for a static website.",
        "It refuses to become your next rogue pentest against Epic/Cerner. Allowlist is a product feature, not a footnote.",
        "It produces artifacts Legal and Privacy can file: findings, remediations, incidents, retest BLOCKED.",
        "It sits on Microsoft’s path you already staff: Foundry, Entra, Azure RBAC, (later) Security Copilot YAML upload.",
        "Time-to-answer for “did the copilot leak?” drops from a consulting sprint to one lifecycle run.",
    ],
    0.5,
    1.25,
    12.3,
    5.6,
    16,
)
footer(s, 9)

# 10 Why not buy known
header_bar(s := slide(), "Competitive honesty", "Why “we already bought X” is not an answer")
rows = [
    ("Microsoft Security Copilot", "Best SOC analyst copilot in the Microsoft estate.", "Does not discover your agent’s tools, confirm T-001 on an allowlist, or retest a hardened build."),
    ("Defender / Purview / DLP", "Necessary for tenant, data, and endpoint.", "Blind to instruction-override → tool dump. Complementary, not a substitute."),
    ("Lakera / Prompt Security / HiddenLayer", "Strong prompt-layer or model-security points.", "Point control. You still lack SoT, remediations, SOC incident, exec GO/NO-GO."),
    ("Traditional AppSec + pentest", "Needed for the rest of the estate.", "Wrong unit of work: they test code paths, not agent reasoning + tools."),
    ("Build it on Copilot Studio only", "Fast UX for clinicians.", "No closed-loop AI security system of record."),
]
text(s, "Alternative", 0.5, 1.15, 3.2, 0.3, 12, True, MUTED)
text(s, "Keep it for", 3.8, 1.15, 3.8, 0.3, 12, True, MUTED)
text(s, "It does not replace Foundary because", 7.7, 1.15, 5.1, 0.3, 12, True, MUTED)
for i, (a, b, c) in enumerate(rows):
    y = 1.5 + i * 1.0
    rect(s, 0.5, y, 12.3, 0.92, WHITE)
    text(s, a, 0.65, y + 0.15, 3.0, 0.65, 13, True, NAVY)
    text(s, b, 3.8, y + 0.15, 3.7, 0.65, 12, False, MUTED)
    text(s, c, 7.7, y + 0.15, 4.9, 0.65, 12, False, INK)
footer(s, 10)

# 11 Buy vs not
header_bar(s := slide(), "Recommendation", "Buy this if / do not buy this if")
rect(s, 0.5, 1.25, 6.05, 5.3, WHITE)
text(s, "Buy Foundary when", 0.75, 1.4, 5.6, 0.4, 18, True, TEAL)
bullets(
    s,
    [
        "You are deploying Azure-hosted clinical or RCM agents in the next 12 months.",
        "Compliance has asked for AI-specific evidence, not a SOC alert screenshot.",
        "You want fail / fix / prove on an authorized system before production.",
        "You will staff a human approver — we will not auto-disable care systems.",
    ],
    0.7,
    1.95,
    5.6,
    4.3,
    14,
)
rect(s, 6.75, 1.25, 6.05, 5.3, WHITE)
text(s, "Do not buy (yet) if", 7.0, 1.4, 5.6, 0.4, 18, True, RED)
bullets(
    s,
    [
        "You need a multi-tenant SaaS tomorrow with a price list and 21-hospital rollout.",
        "You expect Entra-only everywhere on day one — keys still exist on two paths.",
        "You want us to red-team Epic production. We will refuse. That is the product.",
        "You only needed a WAF rule and a training slide.",
    ],
    6.95,
    1.95,
    5.6,
    4.3,
    14,
)
footer(s, 11)

# 12 Commercial packaging
header_bar(s := slide(), "How to sell it", "Packaging a health-system commercial motion")
bullets(
    s,
    [
        "Offer 1 — Foundry Security Loop (this platform): agents, SoT, runtime, dashboard, allowlisted validation.",
        "Offer 2 — Healthcare scenario pack: patient-search / scheduling agent patterns, PHI redaction, approval language.",
        "Offer 3 — Operating model: who approves containment, who owns remediations, how often the loop runs.",
        "Price against: one delayed go-live + one reportable incident investigation. Not against a $20/user SOC add-on.",
        "Land: one service line (e.g., digital front door). Expand: every Foundry agent that gains a tool.",
        "Microsoft attach: Azure consumption + Foundry; optional Security Copilot YAML for the SOC they already bought.",
    ],
    0.5,
    1.25,
    12.3,
    5.6,
    16,
)
footer(s, 12)

# 13 Risks
header_bar(s := slide(), "Diligence", "What a good CISO will push back on — answer now")
bullets(
    s,
    [
        "“Is this production SaaS?”  Controlled platform + proven loop. Not 50-tenant healthcare SaaS. Sell a joint productionization plan.",
        "“Will you attack our EHR?”  No. Allowlist only. If they want production, they put a replica on the list and sign a rules of engagement.",
        "“Entra-only policy?”  Portal is Entra. Next increment: AAD for OpenAI connection + JWT on the runtime. Put it in the SOW.",
        "“Model hallucination?”  Deterministic tools write JSON; the LLM only annotates. Exec numbers come from tools, not prose.",
        "“PHI in logs?”  Redaction is on. Still review LAW / App Insights retention with Privacy.",
        "“Quota / Playground?”  Use the existing gpt-4o deployment; do not create a second one. Runtime API is the system of record.",
    ],
    0.5,
    1.2,
    12.3,
    5.7,
    15,
)
footer(s, 13)

# 14 Roadmap
header_bar(s := slide(), "Next 90 days", "If they say yes Tuesday")
cols = [
    ("Days 1–30", "Pilot SOW. Allowlist one non-prod assistant. Entra RBAC. Run lifecycle weekly. Dashboard in CISO review."),
    ("Days 31–60", "Entra-only outbound. Private-link cutover plan. Power BI workspace if licensed. Approval playbook with Compliance."),
    ("Days 61–90", "Second agent (scheduling or HIM). Security Copilot YAML in their tenant. Decision to productize vs keep as platform service."),
]
for i, (h, b) in enumerate(cols):
    x = 0.5 + i * 4.2
    rect(s, x, 1.3, 4.0, 5.1, WHITE)
    text(s, h, x + 0.25, 1.5, 3.5, 0.5, 20, True, BLUE)
    text(s, b, x + 0.25, 2.2, 3.5, 3.8, 15, False, INK)
footer(s, 14)

# 15 The line
header_bar(s := slide(), "The sentence to leave in the room", "If they remember one thing")
text(
    s,
    "You already bought Microsoft to build the clinical copilot.\n"
    "Foundary is how you prove that copilot cannot be talked into\n"
    "handing over the chart — and how you prove the fix held.",
    0.5,
    2.0,
    12.3,
    3.0,
    26,
    True,
    NAVY,
)
footer(s, 15)

# 16 Close
s = slide()
rect(s, 0, 0, 13.333, 7.5, NAVY)
rect(s, 0, 0, 0.14, 7.5, GOLD)
text(s, "NEXT CONVERSATION", 0.6, 1.3, 12, 0.35, 12, True, GOLD)
text(s, "Pick one authorized assistant.\nRun the loop. Read the GO / NO-GO.\nThen decide whether to buy the category\nor keep renting point tools.", 0.6, 1.9, 12, 3.2, 28, True, WHITE)
text(
    s,
    "Foundary  ·  Azure AI Foundry  ·  project-security-agents  ·  executive-dashboard.html",
    0.6,
    6.3,
    12,
    0.35,
    14,
    False,
    RGBColor(0x9A, 0xA8, 0xB8),
)
text(s, "16  /  16", 11.6, 7.15, 1.3, 0.25, 10, False, RGBColor(0x9A, 0xA8, 0xB8), PP_ALIGN.RIGHT)

prs.save(OUT)
print(OUT)
