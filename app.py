import streamlit as st
import tempfile
import os
from rag_engine import build_qa_chain, analyze_resume, improve_resume, extract_keywords, build_heatmap

st.set_page_config(
    page_title="SeaWee — Resume Analyzer",
    page_icon="⛵",
    layout="centered"
)

BOAT_SVG = """<svg viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:{size}px;height:{size}px;display:inline-block">
  <circle cx="30" cy="30" r="28" fill="#0d2144"/>
  <path d="M10 40 Q30 26 50 40" fill="#1a3a6e" stroke="#378ADD" stroke-width="1.2"/>
  <path d="M30 8 L30 37" stroke="#B5D4F4" stroke-width="2" stroke-linecap="round"/>
  <path d="M30 8 L50 32 L30 36 Z" fill="#378ADD"/>
  <path d="M8 44 Q20 38 30 41 Q40 44 52 44" stroke="#378ADD" stroke-width="1.2" fill="none" stroke-linecap="round"/>
  <path d="M6 49 Q18 44 29 47 Q40 50 54 48" stroke="#185FA5" stroke-width="0.8" fill="none" stroke-linecap="round"/>
</svg>"""

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body { 
  font-family: 'Inter', sans-serif !important; 
}

* {
  box-sizing: border-box;
}

.stApp { background-color: #141920 !important; }
.stApp > div { background-color: #141920 !important; }
[data-testid="stAppViewContainer"] { background-color: #141920 !important; }
[data-testid="stAppViewBlockContainer"] { background-color: #141920 !important; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem !important; max-width: 860px; }

/* ── Navbar ── */
.sw-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 20px 0 20px;
    border-bottom: 1px solid #1e2733;
    margin-bottom: 0;
    background: #141920;
}
.sw-nav-logo { display: flex; align-items: center; gap: 10px; }
.sw-nav-brand { font-size: 20px; font-weight: 800; color: #f1f5f9; letter-spacing: -0.6px; }
.sw-nav-brand span { color: #378ADD; font-weight: 300; }
.sw-nav-links { display: flex; gap: 6px; }
.sw-nav-pill {
    font-size: 11px; font-weight: 600;
    background: #1c2530; border: 1px solid #2a3647;
    color: #94a3b8; padding: 4px 12px;
    border-radius: 999px; letter-spacing: 0.02em;
}

/* ── Hero ── */
.sw-hero {
    text-align: center;
    padding: 64px 20px 48px;
}
.sw-hero-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #1c2530; border: 1px solid #2a3647;
    border-radius: 999px; padding: 6px 16px;
    font-size: 12px; font-weight: 600; color: #94a3b8;
    margin-bottom: 28px; letter-spacing: 0.03em;
}
.sw-hero-badge-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #378ADD; display: inline-block;
}
.sw-hero-title {
    font-size: 58px; font-weight: 900;
    color: #f1f5f9; letter-spacing: -3px;
    line-height: 1.05; margin-bottom: 20px;
}
.sw-hero-title span { color: #378ADD; font-weight: 300; }
.sw-hero-sub {
    font-size: 16px; color: #94a3b8;
    line-height: 1.7; max-width: 520px;
    margin: 0 auto 8px; font-weight: 400;
}
.sw-hero-tagline {
    font-size: 13px; color: #378ADD;
    font-style: italic; margin-top: 4px;
    font-weight: 500;
}

/* ── Module badges ── */
.sw-modules {
    display: flex; justify-content: center;
    gap: 8px; flex-wrap: wrap;
    margin: 24px 0 48px;
}
.sw-mod-badge {
    display: flex; align-items: center; gap: 6px;
    background: #1c2530; border: 1px solid #2a3647;
    border-radius: 999px; padding: 6px 14px;
    font-size: 12px; font-weight: 600; color: #cbd5e1;
}
.sw-mod-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }

/* ── Upload zone ── */
.sw-upload-zone {
    background: #1c2530;
    border: 2px dashed #2a3647;
    border-radius: 20px;
    padding: 48px 32px;
    text-align: center;
    margin-bottom: 12px;
    transition: border-color 0.2s;
    cursor: pointer;
}
.sw-upload-zone:hover { border-color: #378ADD; }
.sw-upload-icon {
    width: 52px; height: 52px;
    background: #232f3e; border-radius: 50%;
    display: flex; align-items: center;
    justify-content: center; margin: 0 auto 14px;
}
.sw-upload-title { font-size: 15px; font-weight: 600; color: #e2e8f0; margin-bottom: 4px; }
.sw-upload-sub { font-size: 13px; color: #9ca3af; }
.sw-upload-hint { font-size: 12px; color: #9ca3af; margin-top: 6px; display: flex; align-items: center; justify-content: center; gap: 4px; }

/* ── Section label ── */
.sw-section {
    font-size: 11px; font-weight: 700;
    color: #475569; text-transform: uppercase;
    letter-spacing: 0.1em; margin: 20px 0 8px;
}

/* ── Score card ── */
.sw-score-card {
    background: #1c2530; border: 1px solid #2a3647;
    border-radius: 20px; padding: 32px 24px;
    text-align: center; margin: 16px 0;
}
.sw-score-num {
    font-size: 72px; font-weight: 900;
    letter-spacing: -4px; line-height: 1;
}
.sw-score-denom { font-size: 28px; font-weight: 300; color: #2a3647; }
.sw-score-label {
    font-size: 12px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em;
    margin-top: 10px;
}

/* ── Result card ── */
.sw-card {
    background: #1c2530; border: 1px solid #2a3647;
    border-radius: 16px; padding: 16px 20px;
    margin-bottom: 10px;
}
.sw-card p { font-size: 14px; color: #94a3b8; line-height: 1.8; margin: 0; }
.sw-skill {
    display: inline-block; background: #1a2a4a;
    border: 1px solid #2a4a7a; color: #60a5fa;
    font-size: 12px; font-weight: 500;
    padding: 4px 12px; border-radius: 999px; margin: 3px;
}

/* ── Agent log ── */
.sw-agent {
    background: #0f1f0f; border: 1px solid #1a3a1a;
    border-radius: 16px; padding: 16px 20px; margin-top: 12px;
}
.sw-agent-row {
    display: flex; align-items: center; gap: 10px;
    padding: 6px 0; border-bottom: 1px solid #1a3a1a;
    font-size: 13px; color: #4ade80; font-weight: 500;
}
.sw-agent-row:last-child { border-bottom: none; }
.sw-agent-dot { width: 6px; height: 6px; border-radius: 50%; background: #22c55e; flex-shrink: 0; }

/* ── Tips ── */
.sw-tips { background: #1c2530; border: 1px solid #2a3647; border-radius: 16px; padding: 18px 20px; margin-top: 12px; }
.sw-tips h4 { font-size: 10px; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.1em; margin: 0 0 12px; }
.sw-tip { color: #94a3b8; font-size: 14px; padding: 7px 0; border-bottom: 1px solid #1e2733; display: flex; align-items: center; gap: 10px; }
.sw-tip:last-child { border-bottom: none; }
.sw-tip-dot { width: 5px; height: 5px; background: #378ADD; border-radius: 50%; flex-shrink: 0; }

/* ── Streamlit overrides ── */
[data-testid="stFileUploaderDropzone"] {
    background: #1c2530 !important;
    border: 2px dashed #2a3647 !important;
    border-radius: 20px !important;
    padding: 48px 20px !important;
    text-align: center !important;
}
[data-testid="stFileUploaderDropzone"] button { display: none !important; }
[data-testid="stFileUploaderDropzone"] span { display: none !important; }
[data-testid="stFileUploaderDropzone"] small { color: #9ca3af !important; font-size: 12px !important; }
[data-testid="stFileUploaderDropzone"] p { color: #6b7280 !important; font-size: 14px !important; }
[data-testid="stFileUploaderDropzone"]::before {
    content: "Drop your PDF resume here";
    display: block; font-size: 15px;
    font-weight: 600; color: #e2e8f0;
    font-family: Inter, sans-serif; margin-bottom: 4px;
}
[data-testid="stFileUploaderDropzone"]::after {
    content: "or click to browse • PDF only";
    display: block; font-size: 13px;
    color: #64748b; font-family: Inter, sans-serif;
}

.stTextArea textarea {
    background: #1c2530 !important;
    border: 1px solid #2a3647 !important;
    color: #cbd5e1 !important;
    border-radius: 14px !important;
    font-size: 14px !important;
    padding: 14px !important;
}
.stTextArea textarea:focus { border-color: #378ADD !important; box-shadow: 0 0 0 3px #378ADD22 !important; }
.stTextArea textarea::placeholder { color: #9ca3af !important; }

.stButton > button {
    background: #378ADD !important;
    color: white !important; border: none !important;
    border-radius: 14px !important;
    font-weight: 700 !important; font-size: 15px !important;
    padding: 0.8rem 1.5rem !important;
    width: 100% !important; letter-spacing: -0.2px !important;
    transition: background 0.15s !important;
    box-shadow: 0 4px 14px #378ADD44 !important;
}
.stButton > button:hover { background: #2b6cb0 !important; box-shadow: 0 6px 20px #378ADD55 !important; }
.stButton > button:active { transform: scale(0.98) !important; }

.stChatMessage {
    background: #1c2530 !important;
    border-radius: 14px !important;
    border: 1px solid #2a3647 !important;
    margin-bottom: 8px !important;
}
[data-testid="stChatMessageAvatarUser"] { background: #378ADD !important; }
[data-testid="stChatMessageAvatarAssistant"] { background: #1D9E75 !important; }
[data-testid="stChatMessageAvatarUser"] *,
[data-testid="stChatMessageAvatarAssistant"] * { color: white !important; font-size: 11px !important; }
[data-testid="stChatInput"] {
    background: #1c2530 !important;
    border: 1px solid #2a3647 !important;
    border-radius: 14px !important;
    box-shadow: none !important;
    outline: none !important;
}
[data-testid="stChatInput"]:focus,
[data-testid="stChatInput"]:focus-within,
[data-testid="stChatInput"]:active {
    border: 1px solid #378ADD !important;
    box-shadow: 0 0 0 2px #378ADD22 !important;
    outline: none !important;
}
[data-testid="stChatInput"] textarea {
    background: #1c2530 !important;
    color: #cbd5e1 !important;
}
[data-testid="stChatInput"] textarea:focus {
    box-shadow: none !important;
    outline: none !important;
    border: none !important;
}
/* Reset everything first */
[data-testid="stChatInput"] {
    background: #1c2530 !important;
    border: 1px solid #2a3647 !important;
    border-radius: 14px !important;
    box-shadow: none !important;
    outline: none !important;
}

/* Remove ALL internal outlines */
[data-testid="stChatInput"] *,
[data-testid="stChatInput"] textarea {
    outline: none !important;
    box-shadow: none !important;
    border: none !important;
}

/* Clean single focus style */
[data-testid="stChatInput"]:focus-within {
    border: 1px solid #378ADD !important;
    box-shadow: 0 0 0 2px #378ADD33 !important;
}

/* Textarea styling */
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #cbd5e1 !important;
}

div[data-testid="stTabs"] button {
    color: #64748b !important;
    font-weight: 500 !important; font-size: 14px !important;
    background: transparent !important; border: none !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #f1f5f9 !important; font-weight: 700 !important;
}
div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background: #378ADD !important; height: 2px !important;
}
div[data-testid="stTabs"] [data-baseweb="tab-border"] { background: #1e2733 !important; }

.stSuccess { background: #0f1f0f !important; border: 1px solid #1a3a1a !important; border-radius: 12px !important; color: #4ade80 !important; }
.stWarning { background: #1f1a0a !important; border: 1px solid #3a2f0a !important; border-radius: 12px !important; color: #fbbf24 !important; }
.stSpinner > div { border-top-color: #378ADD !important; }

#MainMenu, footer, .stDeployButton, header { visibility: hidden; }
</style>
<script>
function fixChatBorder() {
    document.querySelectorAll("[data-testid=stChatInput]").forEach(el => {
        el.style.border = "1px solid #2a3647";
        el.style.boxShadow = "none";
        el.style.outline = "none";
    });
    document.querySelectorAll("[data-baseweb=textarea]").forEach(el => {
        el.style.borderColor = "#378ADD";
        el.style.boxShadow = "none";
    });
}
setInterval(fixChatBorder, 300);
</script>
<style>
</style>
""", unsafe_allow_html=True)

# ── Navbar ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="sw-nav">
  <div class="sw-nav-logo">
    {BOAT_SVG.format(size=34)}
    <div class="sw-nav-brand">Sea<span>Wee</span></div>
  </div>
  <div class="sw-nav-links">
    <span class="sw-nav-pill">GenAI</span>
    <span class="sw-nav-pill">RAG</span>
    <span class="sw-nav-pill">Agentic</span>
    <span class="sw-nav-pill">DevOps</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Hero ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="sw-hero">
  <div class="sw-hero-badge">
    <span class="sw-hero-badge-dot"></span>
    AI-Powered Resume Analysis
  </div>
  <div class="sw-hero-title">
    Navigate the<br><span>Job Market</span>
  </div>
  <div class="sw-hero-sub">
    Upload your resume, paste a job description, and get instant AI-powered
    feedback — match score, missing skills, and an auto-improved resume.
  </div>
  <div class="sw-hero-tagline">The sea of competition just got smaller</div>
</div>
""", unsafe_allow_html=True)

# ── Module badges ────────────────────────────────────────────────────────
st.markdown("""
<div class="sw-modules">
  <div class="sw-mod-badge"><div class="sw-mod-dot" style="background:#378ADD"></div>GenAI · Groq</div>
  <div class="sw-mod-badge"><div class="sw-mod-dot" style="background:#1D9E75"></div>RAG · LangChain</div>
  <div class="sw-mod-badge"><div class="sw-mod-dot" style="background:#D85A30"></div>Agentic AI</div>
  <div class="sw-mod-badge"><div class="sw-mod-dot" style="background:#7F77DD"></div>DevOps · Docker</div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────
# ── Single Resume Upload (shared across both tabs) ──────────────────────
uploaded = st.file_uploader(
    "Resume PDF", type="pdf", label_visibility="hidden")

if uploaded:
    if st.session_state.get("uploaded_name") != uploaded.name:
        pdf_bytes = uploaded.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(pdf_bytes)
            st.session_state.resume_path = f.name
            st.session_state.resume_bytes = pdf_bytes
            st.session_state.uploaded_name = uploaded.name
            st.session_state.chain = None
            if "analysis" in st.session_state:
                del st.session_state["analysis"]
            st.session_state.messages = []

# Recreate temp file if it was cleaned up by OS
if st.session_state.get("resume_bytes") and st.session_state.get("resume_path"):
    if not os.path.exists(st.session_state.resume_path):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(st.session_state.resume_bytes)
            st.session_state.resume_path = f.name

tab1, tab2 = st.tabs(["  Analyze & Improve  ", "  Chat with Resume  "])

# ══════════════════════════════════════════════════
# TAB 1 — ANALYZE & IMPROVE
# ══════════════════════════════════════════════════
with tab1:
    if uploaded:
        tmp_path = st.session_state.get("resume_path", "")

        st.markdown('<div class="sw-section">Job Description</div>',
                    unsafe_allow_html=True)
        jd = st.text_area(
            "Job Description",
            placeholder='Paste the job description here — e.g. "We are looking for a Python developer with 2+ years experience in Django, REST APIs, and SQL..."',
            height=140,
            label_visibility="collapsed"
        )

        if st.button("Analyze Resume"):
            if not jd.strip():
                st.warning("Please paste a job description first.")
            elif not tmp_path or not os.path.exists(tmp_path):
                st.warning("Resume file not found. Please re-upload your PDF.")
            else:
                with st.spinner("Analyzing your resume against the job description..."):
                    result = analyze_resume(tmp_path, jd)
                    if result:
                        st.session_state.analysis = result
                        st.session_state.jd = jd
                    else:
                        st.error("Analysis failed. Please try again.")

        if st.session_state.get("analysis") is not None:
            st.markdown("""<div id='results-anchor'></div>
            <script>
            setTimeout(function(){
                var el = document.getElementById('results-anchor');
                if(el){ el.scrollIntoView({behavior:'smooth', block:'start'}); }
            }, 100);
            </script>""", unsafe_allow_html=True)
            result = st.session_state.analysis
            score = result.get("score", 0)

            if score >= 70:
                color = "#16a34a"
                label = "Strong Match"
            elif score >= 50:
                color = "#d97706"
                label = "Moderate Match"
            else:
                color = "#dc2626"
                label = "Needs Improvement"

            st.markdown(f"""
            <div class="sw-score-card">
              <div class="sw-score-num" style="color:{color}">
                {score}<span class="sw-score-denom">/100</span>
              </div>
              <div class="sw-score-label" style="color:{color}">{label}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="sw-section">Missing Skills</div>',
                        unsafe_allow_html=True)
            missing = result.get("missing_skills", "")
            skills_html = "".join(
                f'<span class="sw-skill">{s.strip()}</span>'
                for s in missing.split(",") if s.strip()
            )
            st.markdown(
                f'<div class="sw-card">{skills_html if skills_html else "<p>No major gaps found.</p>"}</div>', unsafe_allow_html=True)

            st.markdown('<div class="sw-section">Feedback</div>',
                        unsafe_allow_html=True)
            st.markdown(f"""
            <div class="sw-card">
              <p>{result.get("feedback", "").replace(chr(10), "<br>")}</p>
            </div>
            """, unsafe_allow_html=True)

            # ── ATS Keyword Heatmap ──────────────────────────
            st.markdown(
                '<div class="sw-section">ATS Keyword Heatmap</div>', unsafe_allow_html=True)

            if st.button("Generate Keyword Heatmap"):
                with st.spinner("Extracting keywords and building heatmap..."):
                    keywords = extract_keywords(st.session_state.jd)
                    resume_text = result.get("resume_text", "")
                    heatmap_result = build_heatmap(resume_text, keywords)
                    if isinstance(heatmap_result, tuple):
                        highlighted_html, matched, missing_kw = heatmap_result
                    else:
                        highlighted_html = heatmap_result
                        matched, missing_kw = [], []
                    st.session_state.heatmap_html = highlighted_html
                    st.session_state.heatmap_matched = matched
                    st.session_state.heatmap_missing = missing_kw

            if st.session_state.get("heatmap_html"):
                matched = st.session_state.get("heatmap_matched", [])
                missing_kw = st.session_state.get("heatmap_missing", [])

                # Build pills separately as plain strings
                matched_pills = ""
                for k in matched:
                    matched_pills += '<span style="display:inline-block;background:#14532d;color:#4ade80;border-radius:999px;padding:3px 12px;font-size:12px;font-weight:600;margin:3px">&#10003; ' + k + '</span>'

                missing_pills = ""
                for k in missing_kw:
                    missing_pills += '<span style="display:inline-block;background:#450a0a;color:#f87171;border-radius:999px;padding:3px 12px;font-size:12px;font-weight:600;margin:3px">&#10007; ' + k + '</span>'

                if not matched_pills:
                    matched_pills = '<span style="color:#475569;font-size:12px">None found</span>'
                if not missing_pills:
                    missing_pills = '<span style="color:#475569;font-size:12px">No gaps found</span>'

                n_matched = len(matched)
                n_missing = len(missing_kw)
                heatmap_html = st.session_state.heatmap_html

                summary_html = (
                    '<div style="display:flex;gap:16px;align-items:center;margin-bottom:12px;flex-wrap:wrap">'
                    '<span style="color:#4ade80;font-weight:700;font-size:13px">' +
                    str(n_matched) + ' matched</span>'
                    '<span style="color:#f87171;font-weight:700;font-size:13px">' +
                    str(n_missing) + ' missing</span>'
                    '<span style="color:#475569;font-size:11px">from job description keywords</span>'
                    '</div>'
                )

                found_html = (
                    '<div style="margin-bottom:10px">'
                    '<div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px">Found in your resume</div>'
                    '<div>' + matched_pills + '</div>'
                    '</div>'
                )

                missing_html = (
                    '<div style="margin-bottom:14px">'
                    '<div style="font-size:10px;font-weight:700;color:#f87171;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px">Missing — add these to your resume!</div>'
                    '<div>' + missing_pills + '</div>'
                    '</div>'
                )

                resume_label = '<div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px">Resume with matched keywords highlighted</div>'

                st.markdown(summary_html + found_html + missing_html + resume_label +
                            '<div class="sw-heatmap">' + heatmap_html + '</div>', unsafe_allow_html=True)

            st.markdown(
                '<div class="sw-section">Agentic AI — Auto Improvement</div>', unsafe_allow_html=True)

            if st.button("Auto-Improve My Resume"):
                current_score = score
                improved_text = result.get("resume_text", "")
                log_lines = []
                progress = st.progress(0, text="Agent starting...")

                for round_num in range(1, 4):
                    if current_score >= 75:
                        break
                    progress.progress(
                        round_num * 30, text=f"Agent round {round_num} — rewriting resume...")
                    improved = improve_resume(
                        improved_text, st.session_state.jd, current_score)
                    improved_text = improved.get(
                        "improved_text", improved_text)
                    new_score = improved.get("new_score", current_score)
                    log_lines.append(
                        f"Round {round_num}: Score {current_score} → {new_score}")
                    current_score = new_score

                progress.progress(100, text="Done!")

                rows_html = "".join(
                    f'<div class="sw-agent-row"><div class="sw-agent-dot"></div>{line}</div>'
                    for line in log_lines
                )
                rows_html += f'<div class="sw-agent-row" style="font-weight:700"><div class="sw-agent-dot"></div>Final score: {current_score}/100 — agent complete</div>'
                st.markdown(
                    f'<div class="sw-agent">{rows_html}</div>', unsafe_allow_html=True)

                st.markdown(
                    '<div class="sw-section">Improved Resume</div>', unsafe_allow_html=True)
                st.text_area("Improved resume", value=improved_text,
                             height=300, label_visibility="collapsed")

        # temp file kept alive for chat tab — cleaned up when new file uploaded

# ══════════════════════════════════════════════════
# TAB 2 — CHAT
# ══════════════════════════════════════════════════
with tab2:
    if not uploaded:
        st.markdown("""
        <div class="sw-tips">
          <h4>Upload your resume above, then try asking</h4>
          <div class="sw-tip"><div class="sw-tip-dot"></div>What skills does this person have?</div>
          <div class="sw-tip"><div class="sw-tip-dot"></div>Where did they last work?</div>
          <div class="sw-tip"><div class="sw-tip-dot"></div>What is their educational background?</div>
          <div class="sw-tip"><div class="sw-tip-dot"></div>How many years of experience do they have?</div>
          <div class="sw-tip"><div class="sw-tip-dot"></div>Are they a good fit for a Python developer role?</div>
          <div class="sw-tip"><div class="sw-tip-dot"></div>What can they improve on their resume?</div>
        </div>
        """, unsafe_allow_html=True)

    if uploaded:
        tmp_path2 = st.session_state.get("resume_path", "")

        # Rebuild chain if missing or file recreated
        if not st.session_state.get("chain"):
            if tmp_path2 and os.path.exists(tmp_path2):
                with st.spinner("Loading resume for chat..."):
                    try:
                        st.session_state.chain = build_qa_chain(tmp_path2)
                        if "messages" not in st.session_state:
                            st.session_state.messages = []
                        st.success("Resume ready! Ask me anything below.")
                    except Exception as e:
                        st.error(f"Failed to load resume: {str(e)}")
            else:
                st.warning("Resume file missing. Please re-upload your PDF.")

        # Show chat history
        if st.session_state.get("messages"):
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Chat input
        if st.session_state.get("chain"):
            question = st.chat_input("Ask anything about this resume...")
            if question:
                st.session_state.messages.append(
                    {"role": "user", "content": question})
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            answer = st.session_state.chain.invoke(question)
                            st.markdown(answer)
                            st.session_state.messages.append(
                                {"role": "assistant", "content": answer})
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
