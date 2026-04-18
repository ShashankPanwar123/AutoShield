# ================================================================
# AutoShield — Streamlit Frontend  v2.0
# Calls the FastAPI backend; no direct model loading here.
# ================================================================

import streamlit as st
import requests
import os
from pathlib import Path

# ----------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="AutoShield — AI Insurance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================================================================
# CUSTOM CSS — refined dark theme
# ================================================================
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #0a0c10;
    color: #e8eaf0;
  }

  /* Hide default Streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 2rem 3rem 3rem; max-width: 1200px; }

  /* ---- Hero ---- */
  .hero-wrap {
    background: linear-gradient(135deg, #0f1117 0%, #141824 60%, #0f1117 100%);
    border: 1px solid #1e2535;
    border-radius: 20px;
    padding: 2.8rem 3rem;
    margin-bottom: 2.4rem;
    position: relative;
    overflow: hidden;
  }
  .hero-wrap::before {
    content: "";
    position: absolute;
    top: -60px; right: -60px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(99,179,237,0.12) 0%, transparent 70%);
    border-radius: 50%;
  }
  .hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(90deg, #63b3ed, #a78bfa, #f687b3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.4rem;
  }
  .hero-sub {
    color: #8892a4;
    font-size: 1rem;
    font-weight: 300;
  }
  .badge {
    display: inline-block;
    background: rgba(99,179,237,0.12);
    color: #63b3ed;
    border: 1px solid rgba(99,179,237,0.3);
    border-radius: 999px;
    padding: 3px 14px;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 1rem;
  }

  /* ---- Cards ---- */
  .card {
    background: #111520;
    border: 1px solid #1e2535;
    border-radius: 16px;
    padding: 1.8rem;
    height: 100%;
  }
  .card-title {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #c5cfe0;
    letter-spacing: 0.5px;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  /* ---- Result cards ---- */
  .result-block {
    background: #0d1018;
    border: 1px solid #1e2535;
    border-radius: 14px;
    padding: 1.6rem;
    margin-bottom: 1rem;
  }
  .result-label {
    font-size: 0.72rem;
    font-weight: 500;
    color: #5a6478;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
  }
  .result-value {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #e8eaf0;
  }
  .result-value.green { color: #68d391; }
  .result-value.amber { color: #f6ad55; }
  .result-value.red   { color: #fc8181; }

  /* ---- Decision banner ---- */
  .decision-approve {
    background: linear-gradient(135deg, rgba(72,187,120,0.12), rgba(72,187,120,0.04));
    border: 1px solid rgba(72,187,120,0.35);
    border-radius: 14px;
    padding: 1.4rem 1.8rem;
    margin-top: 1rem;
  }
  .decision-review {
    background: linear-gradient(135deg, rgba(246,173,85,0.12), rgba(246,173,85,0.04));
    border: 1px solid rgba(246,173,85,0.35);
    border-radius: 14px;
    padding: 1.4rem 1.8rem;
    margin-top: 1rem;
  }
  .decision-flag {
    background: linear-gradient(135deg, rgba(252,129,129,0.12), rgba(252,129,129,0.04));
    border: 1px solid rgba(252,129,129,0.35);
    border-radius: 14px;
    padding: 1.4rem 1.8rem;
    margin-top: 1rem;
  }
  .decision-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
  }
  .decision-title.green { color: #68d391; }
  .decision-title.amber { color: #f6ad55; }
  .decision-title.red   { color: #fc8181; }
  .decision-text { color: #8892a4; font-size: 0.88rem; }

  /* ---- Progress bar override ---- */
  .stProgress > div > div { background: #1e2535; border-radius: 999px; }
  .stProgress > div > div > div { border-radius: 999px; }

  /* ---- Inputs ---- */
  .stSlider > div > div { color: #8892a4 !important; }
  .stSelectbox > div > div { background: #111520; border-color: #1e2535; }
  div[data-baseweb="select"] { background: #111520; }

  /* ---- Status pill ---- */
  .status-online {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(72,187,120,0.1);
    border: 1px solid rgba(72,187,120,0.3);
    color: #68d391;
    font-size: 0.72rem;
    font-weight: 500;
    padding: 4px 12px;
    border-radius: 999px;
    letter-spacing: 1px;
    text-transform: uppercase;
  }
  .status-offline {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(252,129,129,0.1);
    border: 1px solid rgba(252,129,129,0.3);
    color: #fc8181;
    font-size: 0.72rem;
    font-weight: 500;
    padding: 4px 12px;
    border-radius: 999px;
    letter-spacing: 1px;
    text-transform: uppercase;
  }
  .dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
  .dot-green { background: #68d391; }
  .dot-red   { background: #fc8181; }

  /* ---- Divider ---- */
  .hline { border-top: 1px solid #1e2535; margin: 1.2rem 0; }

  /* ---- Error box ---- */
  .err-box {
    background: rgba(252,129,129,0.06);
    border: 1px solid rgba(252,129,129,0.25);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    color: #fc8181;
    font-size: 0.88rem;
  }
</style>
""", unsafe_allow_html=True)


# ================================================================
# HELPERS
# ================================================================

def check_backend() -> tuple[bool, dict]:
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=4)
        if r.status_code == 200:
            return True, r.json()
        return False, {}
    except Exception:
        return False, {}


def call_predict_numeric(age, car_age, fuel, airbags, tenure, ncap) -> dict | None:
    payload = {
        "age_of_policyholder": age,
        "age_of_car": car_age,
        "fuel_type": fuel,
        "airbags": airbags,
        "policy_tenure": tenure,
        "ncap_rating": ncap,
    }
    try:
        r = requests.post(f"{BACKEND_URL}/predict/numeric", json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot reach the backend. Is the FastAPI server running?"}
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e))
        return {"error": f"Backend returned error: {detail}"}
    except Exception as e:
        return {"error": str(e)}


def call_predict_combined(age, car_age, fuel, airbags, tenure, ncap, image_file=None) -> dict | None:
    data = {
        "age_of_policyholder": str(age),
        "age_of_car": str(car_age),
        "fuel_type": fuel,
        "airbags": str(airbags),
        "policy_tenure": str(tenure),
        "ncap_rating": str(ncap),
    }
    files = {}
    if image_file is not None:
        files = {"file": (image_file.name, image_file.getvalue(), image_file.type)}
    try:
        r = requests.post(
            f"{BACKEND_URL}/predict/combined",
            data=data,
            files=files if files else None,
            timeout=15,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot reach the backend. Is the FastAPI server running?"}
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e))
        return {"error": f"Backend returned error: {detail}"}
    except Exception as e:
        return {"error": str(e)}


def color_for_risk(risk: str) -> str:
    return {"Low Risk": "green", "Medium Risk": "amber", "High Risk": "red"}.get(risk, "green")


def render_decision_banner(decision: str, explanation: str):
    if decision == "Auto Approve":
        css_class, color = "decision-approve", "green"
        icon = "✅"
    elif decision == "Manual Review":
        css_class, color = "decision-review", "amber"
        icon = "⚠️"
    else:
        css_class, color = "decision-flag", "red"
        icon = "🚩"

    st.markdown(f"""
    <div class="{css_class}">
      <div class="decision-title {color}">{icon} {decision}</div>
      <div class="decision-text">{explanation}</div>
    </div>
    """, unsafe_allow_html=True)


# ================================================================
# HEADER
# ================================================================
backend_ok, health_data = check_backend()
status_pill = (
    '<span class="status-online"><span class="dot dot-green"></span>API Online</span>'
    if backend_ok else
    '<span class="status-offline"><span class="dot dot-red"></span>API Offline</span>'
)

st.markdown(f"""
<div class="hero-wrap">
  <div class="badge">AI-Powered</div><br>
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;">
    <div>
      <div class="hero-title">AutoShield</div>
      <div class="hero-sub">Intelligent car insurance claim analysis — powered by XGBoost & deep learning</div>
    </div>
    <div>{status_pill}</div>
  </div>
</div>
""", unsafe_allow_html=True)

if not backend_ok:
    st.markdown("""
    <div class="err-box">
      <strong>Backend not reachable.</strong> Start the FastAPI server first:<br>
      <code>uvicorn backend.main:app --reload --port 8000</code>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ================================================================
# TWO-COLUMN LAYOUT
# ================================================================
left, right = st.columns([1, 1.1], gap="large")

# ----------------------------------------------------------------
# LEFT — Input Form
# ----------------------------------------------------------------
with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">👤 Policyholder Details</div>', unsafe_allow_html=True)

    age = st.slider("Age of Policyholder", 18, 80, 35,
                    help="Current age of the policyholder")
    car_age = st.slider("Age of Car (years)", 0, 20, 3,
                        help="How old is the vehicle?")

    col_a, col_b = st.columns(2)
    with col_a:
        fuel = st.selectbox("Fuel Type", ["Petrol", "Diesel", "CNG"])
    with col_b:
        airbags = st.slider("Airbags", 0, 10, 4)

    col_c, col_d = st.columns(2)
    with col_c:
        tenure = st.slider("Policy Tenure", 0.0, 1.0, 0.55, 0.05,
                           help="Normalized policy tenure (0 = new, 1 = max)")
    with col_d:
        ncap = st.slider("NCAP Rating", 0, 5, 3,
                         help="Safety rating (0 = unrated, 5 = best)")

    st.markdown('<div class="hline"></div>', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🖼️ Damage Image (optional)</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload car image for fraud check",
                                type=["jpg", "jpeg", "png"],
                                label_visibility="collapsed")
    if uploaded:
        st.image(uploaded, use_container_width=True, caption="Uploaded image")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    analyse_btn = st.button("🚀  Analyse Claim", use_container_width=True, type="primary")

# ----------------------------------------------------------------
# RIGHT — Results
# ----------------------------------------------------------------
with right:
    if not analyse_btn:
        st.markdown("""
        <div style="height:100%;display:flex;flex-direction:column;justify-content:center;
                    align-items:center;text-align:center;padding:3rem 2rem;
                    background:#111520;border:1px solid #1e2535;border-radius:16px;">
          <div style="font-size:3rem;margin-bottom:1rem;">🛡️</div>
          <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:700;color:#c5cfe0;">
            Ready to Analyse
          </div>
          <div style="color:#5a6478;font-size:0.88rem;margin-top:0.5rem;max-width:280px;">
            Fill in the policyholder details on the left and click <em>Analyse Claim</em> to get an AI-powered risk assessment.
          </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        with st.spinner("Running AI models…"):
            if uploaded:
                result = call_predict_combined(age, car_age, fuel, airbags, tenure, ncap, uploaded)
            else:
                raw = call_predict_numeric(age, car_age, fuel, airbags, tenure, ncap)
                result = {"numeric": raw, "image": None,
                          "final_approval_score": 1 - raw.get("claim_probability", 0.5),
                          "final_decision": raw.get("decision", "—")} if "error" not in raw else raw

        # Error handling
        if "error" in result:
            st.markdown(f'<div class="err-box">⚠️ {result["error"]}</div>', unsafe_allow_html=True)
        else:
            num  = result.get("numeric", {})
            img  = result.get("image")
            appr = result.get("final_approval_score", 0)
            dec  = result.get("final_decision", "—")

            claim_pct    = num.get("claim_probability", 0) * 100
            approval_pct = num.get("approval_probability", 0) * 100
            risk         = num.get("risk_level", "—")
            expl         = num.get("explanation", "")
            color        = color_for_risk(risk)

            # ---- Metric row ----
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="result-block">
                  <div class="result-label">Claim Risk</div>
                  <div class="result-value {color}">{claim_pct:.1f}%</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="result-block">
                  <div class="result-label">Approval Chance</div>
                  <div class="result-value {'green' if approval_pct > 60 else 'amber' if approval_pct > 40 else 'red'}">{approval_pct:.1f}%</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="result-block">
                  <div class="result-label">Risk Level</div>
                  <div class="result-value {color}" style="font-size:1.1rem;padding-top:0.4rem">{risk}</div>
                </div>""", unsafe_allow_html=True)

            # ---- Progress bar ----
            st.markdown(f'<div style="font-size:0.72rem;color:#5a6478;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;">Claim risk score</div>', unsafe_allow_html=True)
            st.progress(int(claim_pct))

            # ---- Image result ----
            if img:
                img_label = img.get("label", "—")
                img_conf  = img.get("confidence", 0) * 100
                img_color = "green" if img_label == "Normal" else "amber" if img_label == "Uncertain" else "red"
                st.markdown(f"""
                <div class="result-block" style="margin-top:1rem;">
                  <div class="result-label">🧠 Fraud Detection (Image)</div>
                  <div class="result-value {img_color}" style="font-size:1.4rem">{img_label}</div>
                  <div style="color:#5a6478;font-size:0.82rem;margin-top:4px;">Confidence: {img_conf:.1f}%</div>
                  {f'<div style="color:#5a6478;font-size:0.78rem;margin-top:4px;">ℹ️ {img.get("note","")}</div>' if img.get("note") else ""}
                </div>""", unsafe_allow_html=True)

            # ---- Final score ----
            st.markdown(f"""
            <div class="result-block" style="margin-top:0.5rem;">
              <div class="result-label">Final Approval Score</div>
              <div class="result-value {'green' if appr>0.7 else 'amber' if appr>0.4 else 'red'}">{appr*100:.1f}%</div>
            </div>""", unsafe_allow_html=True)

            render_decision_banner(dec, expl)

            st.markdown("""
            <div style="color:#3a4255;font-size:0.75rem;margin-top:1rem;text-align:right;">
              Powered by AutoShield AI v2.0 — results are indicative only
            </div>""", unsafe_allow_html=True)
