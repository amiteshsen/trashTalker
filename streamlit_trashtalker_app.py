import io, re, requests
from PIL import Image, ImageOps, ImageDraw
import pandas as pd
import streamlit as st

# ---------- PAGE ----------
st.set_page_config(page_title="TrashTalker", layout="wide", initial_sidebar_state="collapsed")
# hide sidebar entirely
## Run Detection style ##
st.markdown("""
<style>
/* Only style the Run Detection button wrapped in .run-btn */
.run-btn .stButton > button {
  background: linear-gradient(90deg, #10b981, #06b6d4) !important; /* teal → cyan */
  color: #ffffff !important;
  border: none !important;
  border-radius: 999px !important;     /* pill */
  padding: 10px 24px !important;
  font-weight: 700 !important;
  box-shadow: 0 8px 20px rgba(6,182,212,0.25);
}
.run-btn .stButton > button:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(6,182,212,0.32);
}
.run-btn .stButton > button:active {
  transform: translateY(0);
}
.run-btn .stButton > button:focus-visible{
  outline: 3px solid #99f6e4 !important;  /* accessible focus ring */
  outline-offset: 2px;
}
</style>
""", unsafe_allow_html=True)



st.markdown("""
<style>
/* Big, Google-y, ALL CAPS hero */
.hero-wrap { text-align:center; margin: 8px auto 12px; }
.hero-title{
  font-family:'Roboto', -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  text-transform:uppercase;
  font-weight:900;
  letter-spacing:.14em;
  line-height:1;
  /* responsive size: scales from phones to desktops */
  font-size: clamp(40px, 9vw, 96px);
  /* gradient ink + soft glow */
  background: linear-gradient(90deg,#2563eb,#22c55e);
  -webkit-background-clip:text; background-clip:text; color:transparent;
  filter: drop-shadow(0 6px 20px rgba(0,0,0,.10));
  margin: 4px 0 8px;
}
.hero-accent{
  height:6px; width: clamp(140px, 22vw, 260px);
  margin: 6px auto 0;
  background: linear-gradient(90deg,#22c55e,#38bdf8);
  border-radius: 999px;
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
/* Center the tab row */
div[role="tablist"] { justify-content: center; gap: 12px; margin: 10px 0 6px; }

/* Base tab chip style */
div[role="tablist"] button[role="tab"]{
  border: 1.5px solid #e5e7eb;           /* gray-200 */
  background: #fff;
  color: #374151;                         /* gray-700 */
  padding: 8px 16px;
  border-radius: 999px;                   /* pill */
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0,0,0,.06);
}
div[role="tablist"] button[role="tab"]:hover{
  border-color: #cbd5e1;                  /* gray-300 */
  background: #f8fafc;                    /* gray-50 */
}

/* Active state (white text, shadow) */
div[role="tablist"] button[role="tab"][aria-selected="true"]{
  color: #fff;
  border-color: transparent;
  box-shadow: 0 6px 18px rgba(0,0,0,.08);
}

/* Give each tab its own color when active */
div[role="tablist"] button[role="tab"][aria-selected="true"]:nth-child(1){
  background: linear-gradient(90deg, #16a34a, #22c55e);   /* Upload: green */
}
div[role="tablist"] button[role="tab"][aria-selected="true"]:nth-child(2){
  background: linear-gradient(90deg, #2563eb, #38bdf8);   /* URL: blue */
}
div[role="tablist"] button[role="tab"][aria-selected="true"]:nth-child(3){
  background: linear-gradient(90deg, #7c3aed, #a78bfa);   /* Camera: purple */
}

/* Optional: subtle colored outline for inactive tabs */
div[role="tablist"] button[role="tab"]:nth-child(1)[aria-selected="false"] { border-color: #86efac; }
div[role="tablist"] button[role="tab"]:nth-child(2)[aria-selected="false"] { border-color: #93c5fd; }
div[role="tablist"] button[role="tab"]:nth-child(3)[aria-selected="false"] { border-color: #c4b5fd; }

/* Accessible focus ring */
div[role="tablist"] button[role="tab"]:focus-visible{
  outline: 3px solid #60a5fa !important; outline-offset: 2px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Wrapper to keep the uploader compact and centered */
.uploader-center { max-width: 380px; margin: 0 auto; }

/* Make the dropzone layout vertical, text under the button, and center everything */
.uploader-center [data-testid="stFileUploaderDropzone"] { padding: 14px; }
.uploader-center [data-testid="stFileUploaderDropzone"] > div {
  display: flex !important;
  flex-direction: column-reverse !important;  /* put hint text below the button */
  align-items: center !important;
  gap: 8px;
  text-align: center;
}

/* Force the Browse control itself to center (covers label/button/role variations across versions) */
.uploader-center [data-testid="stFileUploaderDropzone"] label,
.uploader-center [data-testid="stFileUploaderDropzone"] button,
.uploader-center [data-testid="stFileUploaderDropzone"] [role="button"] {
  margin: 0 auto !important;
  align-self: center !important;
  display: inline-flex !important;
  justify-content: center;
}

/* Center the native hint line */
.uploader-center [data-testid="stFileUploaderDropzone"] small {
  display: block;
  text-align: center !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Center the tabs row */
div[role="tablist"] { justify-content: center; gap: 24px; }

/* Center + shrink the uploader area */
.uploader-center { max-width: 380px; margin: 0 auto; }

/* Put the dropzone text UNDER the Browse button and center everything */
.uploader-center [data-testid="stFileUploaderDropzone"] { padding: 14px; }
.uploader-center [data-testid="stFileUploaderDropzone"] > div {
  display: flex; flex-direction: column-reverse; align-items: center; gap: 8px;
}

/* Make sure the Browse files control is centered */
.uploader-center [data-testid="stFileUploaderDropzone"] label { margin: 0 auto; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Center all headings */
h1, h2, h3, h4, h5, h6 { text-align:center; }

/* Center the tabs row (Upload / URL / Camera) */
div[role="tablist"] { justify-content: center; gap: 24px; }

/* Center + shrink the uploader area */
.uploader-center { max-width: 420px; margin: 0 auto; }
.uploader-center [data-testid="stFileUploaderDropzone"] { padding: 14px; }
.uploader-center [data-testid="stFileUploaderDropzone"] > div {
  display: flex; flex-direction: column-reverse; align-items: center; gap: 8px; /* puts text under the button */
}
.uploader-hint { text-align:center; font-size: 0.9rem; color: #6b7280; margin-top: 6px; }

/* Colorful bold tagline */
.tagline strong {
  font-weight: 900; font-size: 1.1rem;
  background: linear-gradient(90deg,#16a34a,#2563eb);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}

/* Make prediction image smaller and centered */
.detect-img { display:block; margin: 0 auto; max-width: 420px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] { display:none !important; }
h1, h2, h3, h4, h5, h6 { text-align:center; }
.centered { text-align:center; }
.main-narrow { max-width: 800px; margin: 0 auto; }
</style>
""", unsafe_allow_html=True)

# Google-like font + minimal theming
st.markdown("""
<style>
/* Load Roboto like google.com (falls back to system sans if blocked) */
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&display=swap');

:root { --tt-text:#202124; --tt-green:#065f46; --tt-green-bg:#d1fae5;
        --tt-amber:#7c2d12; --tt-amber-bg:#ffedd5; }

html, body, [data-testid="stAppViewContainer"], .stApp {
  font-family: 'Roboto', -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  color: var(--tt-text);
}

/* Centered, Google-clean headings */
h1 { text-align:center; font-weight:500; letter-spacing:.2px; margin: 8px 0 2px; }
.centered { text-align:center; }

/* Big, high-contrast result banner */
.result-banner {
  margin: 8px 0 18px;
  padding: 16px 18px;
  border-radius: 14px;
  font-weight: 700;
  font-size: 26px;
  display:flex; align-items:center; gap:12px;
  box-shadow: 0 6px 24px rgba(0,0,0,.07);
}
.result-banner .emoji { font-size: 28px; line-height: 1; }

.result-yes { background: var(--tt-green-bg); color: var(--tt-green); border: 2px solid #34d399; }
.result-no  { background: var(--tt-amber-bg); color: var(--tt-amber); border: 2px solid #fdba74; }

/* Keep layout narrow like google.com hero */
.main-narrow { max-width: 800px; margin: 0 auto; }
</style>
""", unsafe_allow_html=True)

# ---------- DEFAULTS (overridden by bottom Settings via session_state) ----------
DEFAULTS = dict(
    PROJECT="trashtalkerobjectdetection-7pded",
    VERSION=3,
    API_URL="https://detect.roboflow.com",
    CONF=42,
    OVERLAP=50,
    MAX_SIDE=1024,
    QUALITY=80,
)
PROJECT  = st.session_state.get("PROJECT",  DEFAULTS["PROJECT"])
VERSION  = st.session_state.get("VERSION",  DEFAULTS["VERSION"])
API_URL  = st.session_state.get("API_URL",  DEFAULTS["API_URL"])
CONF     = st.session_state.get("CONF",     DEFAULTS["CONF"])
OVERLAP  = st.session_state.get("OVERLAP",  DEFAULTS["OVERLAP"])
MAX_SIDE = st.session_state.get("MAX_SIDE", DEFAULTS["MAX_SIDE"])
QUALITY  = st.session_state.get("QUALITY",  DEFAULTS["QUALITY"])
API_KEY  = st.secrets.get("ROBOFLOW_API_KEY") or st.session_state.get("API_KEY", "")

# ---------- TITLE + SUBTEXT (centered, Google-simple) ----------
st.markdown("""
<div class="hero-wrap">
  <div class="hero-title">TrashTalker</div>
  <div class="hero-accent"></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='tagline centered'><strong>Upload or take a picture to predict</strong></div>", unsafe_allow_html=True)

st.markdown("<div class='main-narrow'>", unsafe_allow_html=True)

# ---------- HELPERS ----------
def compress_image(file_like, max_side=1024, quality=80):
    im = Image.open(file_like)
    im = ImageOps.exif_transpose(im)
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    buf.seek(0)
    return im, buf

def draw_preds(pil_img, preds):
    img = pil_img.copy()
    draw = ImageDraw.Draw(img)
    for p in preds:
        xc, yc, w, h = p["x"], p["y"], p["width"], p["height"]
        x1, y1, x2, y2 = xc - w/2, yc - h/2, xc + w/2, yc + h/2
        label = f'{p.get("class","obj")} {p.get("confidence",0):.2f}'
        draw.rectangle([x1, y1, x2, y2], outline=(0, 160, 80), width=3)
        tw = draw.textlength(label)
        draw.rectangle([x1, y1-18, x1+tw+6, y1], fill=(0,160,80))
        draw.text((x1+3, y1-16), label, fill=(0,0,0))
    return img

def preds_to_df(preds):
    if not preds:
        return pd.DataFrame(columns=["class","confidence","x","y","width","height","x1","y1","x2","y2"])
    rows = []
    for p in preds:
        xc, yc, w, h = p["x"], p["y"], p["width"], p["height"]
        rows.append({
            "class": p.get("class"),
            "confidence": round(float(p.get("confidence", 0.0)), 4),
            "x": xc, "y": yc, "width": w, "height": h,
            "x1": xc - w/2, "y1": yc - h/2, "x2": xc + w/2, "y2": yc + h/2
        })
    return pd.DataFrame(rows)

def normalize_label(raw: str) -> str:
    base = re.split(r"[-|]", str(raw))[0]
    base = base.strip().lower().replace("_", " ").replace("  ", " ")
    aliases = {
        "plasticfilms": "plastic film",
        "plasticfilm":  "plastic film",
        "plastic films":"plastic film",
        "plastic bag":  "plastic film",
    }
    return aliases.get(base, base)

def is_plastic_film(preds) -> bool:
    return any(normalize_label(p.get("class","")) == "plastic film" for p in preds)

def render_result_banner(is_plastic: bool):
    if is_plastic:
        st.markdown(
            "<div class='result-banner result-yes'><span class='emoji'>♻️</span>"
            "<span>It’s a plastic film</span></div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div class='result-banner result-no'><span class='emoji'>🚫</span>"
            "<span>Not a plastic film</span></div>",
            unsafe_allow_html=True
        )

# ---------- INPUT AREA (centered) ----------
tab_up, tab_url, tab_cam = st.tabs(["Upload", "URL", "Camera"])

with tab_up:
    st.markdown("<div class='uploader-center'>", unsafe_allow_html=True)
    file = st.file_uploader(
        label="", type=["jpg","jpeg","png","webp","bmp","tiff"],
        label_visibility="collapsed", key="uploader_main"
    )
    st.markdown("</div>", unsafe_allow_html=True)

with tab_url:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        url_in = st.text_input("", placeholder="Paste a PUBLIC image URL", label_visibility="collapsed")

with tab_cam:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        cam_file = st.camera_input("", label_visibility="collapsed")  # centered webcam widget


left, mid, right = st.columns([1, 1, 1])
with mid:
    st.markdown("<div class='run-btn'>", unsafe_allow_html=True)
    run = st.button("Run Detection", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ---------- INFERENCE ----------
if run:
    if not API_KEY:
        st.error("Add your Roboflow API key in Settings (bottom) or Streamlit Secrets.")
    else:
        endpoint = f"{API_URL.rstrip('/')}/{PROJECT}/{int(VERSION)}"
        params   = {"api_key": API_KEY, "confidence": int(CONF), "overlap": int(OVERLAP), "format": "json"}

        source_mode, pil_in, jpeg_buf, resp = None, None, None, None
        try:
            if cam_file is not None:
                source_mode = "camera"
                pil_in, jpeg_buf = compress_image(cam_file, max_side=MAX_SIDE, quality=QUALITY)
                resp = requests.post(endpoint, params=params, files={"file": ("cam.jpg", jpeg_buf, "image/jpeg")}, timeout=60)
            elif file is not None:
                source_mode = "upload"
                pil_in, jpeg_buf = compress_image(file, max_side=MAX_SIDE, quality=QUALITY)
                resp = requests.post(endpoint, params=params, files={"file": ("image.jpg", jpeg_buf, "image/jpeg")}, timeout=60)
            elif url_in:
                source_mode = "url"
                try:
                    pil_in = Image.open(requests.get(url_in, stream=True, timeout=20).raw)
                except Exception:
                    pil_in = None
                resp = requests.get(endpoint, params={**params, "image": url_in}, timeout=60)
            else:
                st.warning("Please provide an image via Upload, URL, or Camera.")

            if resp is not None:
                if resp.status_code == 413:
                    st.error("Image too large for endpoint. Lower Resize/Quality in Settings or use a URL.")
                resp.raise_for_status()

                data  = resp.json()
                preds = data.get("predictions", [])
                df    = preds_to_df(preds)

                # ---- OUTPUT LAYOUT: left=image, right=result+table ----
                col_left, col_right = st.columns(2, gap="large")

                with col_left:
                    if pil_in is None and (file or cam_file):
                        pil_in, _ = compress_image(file or cam_file, max_side=MAX_SIDE, quality=QUALITY)
                    if pil_in is not None and preds:
                        st.image(draw_preds(pil_in, preds), use_column_width=False, width=420)  # ~420px wide
                    elif pil_in is not None:
                        st.image(pil_in, use_column_width=True)

                with col_right:
                    st.markdown("### Result")
                    if preds:
                        render_result_banner(is_plastic_film(preds))
                    else:
                        # If truly nothing detected, show a subtle note (keeps the page tidy)
                        st.markdown(
                            "<div class='result-banner result-no'><span class='emoji'>⚠️</span>"
                            "<span>No detection</span></div>", unsafe_allow_html=True
                        )

                    st.markdown("### Raw prediction")
                    st.dataframe(df, use_container_width=True)


        except requests.HTTPError as e:
            st.error(f"HTTP error: {e}\n{getattr(e.response,'text','')[:300]}")
        except Exception as e:
            st.exception(e)

# ---------- BOTTOM SECTION: Settings & Quiz ----------
st.markdown("---")

with st.expander("⚙️ Settings", expanded=False):
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        st.session_state["PROJECT"] = st.text_input("Project slug", value=PROJECT, key="PROJECT_in")
        st.session_state["VERSION"] = st.number_input("Version", min_value=1, value=int(VERSION), step=1, key="VERSION_in")
        st.session_state["API_URL"] = st.selectbox("Endpoint", ["https://detect.roboflow.com","https://infer.roboflow.com"], index=0 if API_URL.endswith("detect.roboflow.com") else 1, key="API_URL_in")
    with c2:
        st.session_state["CONF"]    = st.slider("Confidence (percent)", 0, 100, int(CONF), key="CONF_in")
        st.session_state["OVERLAP"] = st.slider("Overlap / NMS (%)", 0, 100, int(OVERLAP), key="OVERLAP_in")
    with c3:
        st.session_state["MAX_SIDE"] = st.slider("Resize (max side px)", 512, 2048, int(MAX_SIDE), step=64, key="MAX_SIDE_in")
        st.session_state["QUALITY"]  = st.slider("JPEG quality", 50, 95, int(QUALITY), key="QUALITY_in")

    st.session_state["API_KEY"] = st.text_input(
        "Roboflow API key",
        value=API_KEY,
        type="password",
        help="On Streamlit Cloud, set in Manage app → Settings → Secrets. Locally, use .streamlit/secrets.toml",
        key="API_KEY_in"
    )

with st.expander("🧠 Quick Quiz: What goes where?", expanded=False):
    q = [
        ("Plastic grocery bags?", ["Curbside bin", "Store drop-off / special", "Landfill"], "Store drop-off / special",
         "Most curbside programs reject film; many stores collect bags/wrap."),
        ("Paper coffee cups?", ["Curbside bin", "Compost", "Landfill / check local"], "Landfill / check local",
         "Most are plastic-lined; a few cities can handle them—always check local rules."),
        ("Cardboard boxes?", ["Curbside bin", "Landfill"], "Curbside bin",
         "Flatten first to improve sorting."),
    ]
    with st.form("quiz"):
        answers = []
        for i, (prompt, opts, correct, _) in enumerate(q):
            answers.append(st.radio(prompt, opts, index=0, key=f"q{i}"))
        submitted = st.form_submit_button("Check answers")
        if submitted:
            score = sum(a == q[i][2] for i, a in enumerate(answers))
            if score == len(q):
                st.success(f"Perfect! {score}/{len(q)} ✅")
            else:
                st.warning(f"You got {score}/{len(q)}. See tips below:")
                for i, a in enumerate(answers):
                    if a != q[i][2]:
                        st.write(f"• **{q[i][0]}** — {q[i][3]}")
