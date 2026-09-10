import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def create_document():
    doc = Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Styles
    primary_color = RGBColor(220, 38, 38)    # #DC2626 (Red for Security)
    dark_heading = RGBColor(15, 23, 42)
    sub_heading = RGBColor(51, 65, 85)
    body_color = RGBColor(30, 41, 59)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("INTELLITRACK — CYBERSECURITY & ENTERPRISE RISK ARCHITECTURE")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = primary_color

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("Defending Critical Infrastructure (Oil & Gas) Data from Internal & External Threats")
    run_sub.font.name = "Arial"
    run_sub.font.size = Pt(11)
    run_sub.font.italic = True
    run_sub.font.color.rgb = sub_heading

    def add_section_header(title):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
        r = h.add_run(title)
        r.font.name = "Arial"
        r.font.size = Pt(14)
        r.font.bold = True
        r.font.color.rgb = primary_color

    def add_body(text, bold_prefix=""):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.font.name = "Calibri"
            rb.font.size = Pt(10.5)
            rb.font.bold = True
            rb.font.color.rgb = dark_heading
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(10.5)
        r.font.color.rgb = body_color

    def add_bullet(bold_part, text_part):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        rb = p.add_run(bold_part)
        rb.font.name = "Calibri"
        rb.font.size = Pt(10.5)
        rb.font.bold = True
        rb.font.color.rgb = dark_heading
        rt = p.add_run(text_part)
        rt.font.name = "Calibri"
        rt.font.size = Pt(10.5)
        rt.font.color.rgb = body_color

    add_section_header("1. Preventing Impersonation & Internal Scams")
    add_body("In critical sectors, internal fraud (e.g., a supervisor logging fake progress to trigger contractor billing) is a massive risk. We prevent this via:")
    add_bullet("Strict Role-Based Access Control (RBAC): ", "A Civil Supervisor can only log Civil activities. The system automatically rejects progress logged outside their authorized discipline.")
    add_bullet("Immutable Audit Trails: ", "As implemented in 'audit_service.py', every single extraction and update is logged with a timestamp, user ID, and action type. These logs cannot be deleted, ensuring absolute non-repudiation.")
    add_bullet("Human-in-the-Loop (HitL) Validation: ", "The AI never automatically overrides the master Primavera schedule. The 'ActivitiesPage' dashboard requires a senior Planner to manually 'Confirm' or 'Reject' the AI's fuzzy matches, preventing rogue AI updates or malicious data poisoning.")
    add_bullet("Future Scope - Voice Biometrics: ", "Because we ingest voice notes, future production systems can verify the speaker's actual voiceprint, making impersonation nearly impossible.")

    add_section_header("2. Protecting Against External Hackers & System Crashes")
    add_body("Public-facing APIs and databases are frequent targets for DDoS attacks and injection. IntelliTrack defends against this via:")
    add_bullet("API Gateways & Rate Limiting: ", "FastAPI routes are protected by rate limiters (e.g., max 10 requests/minute per supervisor) to prevent automated bots from crashing the LLM ingestion service.")
    add_bullet("Strict Payload Validation: ", "Uploaded PDFs and Excel files are scanned for malicious macros, and file sizes are strictly capped (e.g., 10MB limit in 'ai_ingestion.py') to prevent memory overflow crashes.")
    add_bullet("Data Encryption: ", "All data is encrypted in transit via TLS 1.3 and at rest using AES-256 encryption in Firestore and Databricks.")

    add_section_header("3. LLM Data Privacy for Critical Infrastructure")
    add_body("Oil India cannot send sensitive pipeline coordinates and contractor budgets to public AI APIs like ChatGPT.")
    add_bullet("On-Premise LLM Hosting: ", "Because we use LLaMA-3 (which is open-source), in a production enterprise environment, the model will be hosted entirely on Oil India's internal Virtual Private Cloud (VPC) or bare-metal servers. No sensitive project data will ever leave the corporate firewall.")
    add_bullet("Prompt Injection Defense: ", "The AI 'Time Agent' is strictly constrained by its system prompt to ONLY output JSON activity logs. It is sandboxed from executing backend code, preventing hackers from using conversational prompts to delete database tables (SQL/NoSQL injection).")

    add_section_header("4. Summary for the Judges")
    add_body("If a judge asks about security, emphasize three points:")
    add_bullet("1. Zero Trust: ", "We assume both external users and internal supervisors might be malicious. Access is siloed by discipline.")
    add_bullet("2. Human-in-the-Loop: ", "The AI suggests; the human Planner decides. The AI cannot maliciously crash the master schedule.")
    add_bullet("3. Data Sovereignty: ", "The architecture is designed for on-premise, open-source LLM deployment, keeping Oil India's data 100% private.")

    output_path = r"d:\DATABRICKS\IntelliTrack_Security_Architecture.docx"
    doc.save(output_path)
    print(f"SUCCESS: Document saved to {output_path}")

if __name__ == "__main__":
    create_document()
