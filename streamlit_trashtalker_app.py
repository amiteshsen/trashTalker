import os, io, re, base64, requests, time
import pandas as pd
from PIL import Image, ImageOps, ImageDraw, ImageFilter
import streamlit as st
import streamlit.components.v1 as components

# ---------------- CONFIG ----------------
BASE_DIR = os.path.dirname(__file__)
st.set_page_config(page_title="TrashTalker ♻️", layout="wide", initial_sidebar_state="collapsed")

# ---------------- THEME STYLES ----------------
st.markdown("""
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] { display: none !important; }
body, div, button, input { font-family: 'Roboto', sans-serif !important; }

.hero-wrap { text-align: center; margin-top: -25px; }
.hero-title {
  font-weight: 900; font-size: clamp(34px, 5vw, 54px);
  background: linear-gradient(90deg, #2563eb, #22c55e);
  -webkit-background-clip: text; color: transparent;
}
.hero-tagline { color: #4b5563; font-weight: 500; margin-bottom: 12px; }

.run-btn { display:flex; justify-content:center; margin:32px 0 24px; }
.run-btn .stButton>button {
  background: linear-gradient(90deg,#2563eb,#22c55e)!important; color:white!important;
  border:none!important; border-radius:999px!important; padding:12px 36px!important;
  font-weight:800!important; letter-spacing:.02em!important; box-shadow:0 6px 18px rgba(37,99,235,.25);
  transition: all .25s ease-in-out!important;
}
.run-btn .stButton>button:hover { filter:brightness(1.08); transform:translateY(-2px); }
.run-btn .stButton>button:active { transform:scale(.97); filter:brightness(.9); }

.result-banner {
  margin:12px 0 18px; padding:16px; border-radius:12px; font-weight:700; font-size:22px;
  display:flex; align-items:center; gap:12px; box-shadow:0 6px 18px rgba(0,0,0,.07);
}
.result-yes { background:#d1fae5; color:#065f46; border:2px solid #34d399; }
.result-no { background:#ffedd5; color:#7c2d12; border:2px solid #fdba74; }
.emoji { font-size:26px; }

.gallery-item { min-height:420px; text-align:center; }
.subheading {
  font-weight:800; background:linear-gradient(90deg,#2563eb,#22c55e);
  -webkit-background-clip:text; color:transparent; margin-bottom:6px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DEFAULTS ----------------
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

# ---------------- HEADER ----------------
st.markdown("""
<div class="hero-wrap">
  <div class="hero-title">TrashTalker</div>
  <div class="hero-tagline">AI-powered material detection and sorting for a cleaner planet</div>
</div>
""", unsafe_allow_html=True)

# ---------------- IMAGE GALLERY ----------------
def load_fit_dark(path, box_size=(400,300)):
    img = Image.open(path).convert("RGB")
    img = ImageOps.exif_transpose(img)
    img.thumbnail(box_size, Image.Resampling.LANCZOS)
    bg = Image.new("RGB", box_size, (14,17,23))
    x = (box_size[0]-img.width)//2; y = (box_size[1]-img.height)//2
    bg.paste(img, (x,y))
    return bg

def render_gallery(title, images, idx_key):
    if idx_key not in st.session_state: st.session_state[idx_key]=0
    img = load_fit_dark(images[st.session_state[idx_key]])
    buf=io.BytesIO(); img.save(buf,format="JPEG"); encoded=base64.b64encode(buf.getvalue()).decode()
    st.markdown(f"<div class='gallery-item'><div class='subheading'>{title}</div>"
                f"<img src='data:image/jpeg;base64,{encoded}' width='400' style='border-radius:12px;'/>"
                f"<p style='color:#6b7280;'>Image {st.session_state[idx_key]+1} of {len(images)}</p></div>",
                unsafe_allow_html=True)
    cols=st.columns([1,1,1])
    with cols[0]:
        if st.button("←", key=f"{idx_key}_left"): st.session_state[idx_key]=(st.session_state[idx_key]-1)%len(images)
    with cols[2]:
        if st.button("→", key=f"{idx_key}_right"): st.session_state[idx_key]=(st.session_state[idx_key]+1)%len(images)

trash_imgs=[os.path.join(BASE_DIR,"assets",f"smartbin{i}.jpg") for i in range(1,7)]
nextrex_imgs=[os.path.join(BASE_DIR,"assets",f"nextrex{i}.jpg") for i in range(1,4)]
col1,col2=st.columns(2)
with col1: render_gallery("TrashTalker Smart Bin Prototype", trash_imgs, "trash_idx")
with col2: render_gallery("NexTrex Sustainability Initiative", nextrex_imgs, "nextrex_idx")

# ---------------- HELPERS ----------------
def compress_image(file_like, max_side=1024, quality=80):
    im=Image.open(file_like); im=ImageOps.exif_transpose(im); im.thumbnail((max_side,max_side))
    buf=io.BytesIO(); im.convert("RGB").save(buf,"JPEG",quality=quality,optimize=True,progressive=True); buf.seek(0)
    return im,buf

def draw_preds(pil_img,preds):
    img=pil_img.copy(); draw=ImageDraw.Draw(img)
    for p in preds:
        xc,yc,w,h=p["x"],p["y"],p["width"],p["height"]
        x1,y1,x2,y2=xc-w/2,yc-h/2,xc+w/2,yc+h/2
        label=f'{p.get("class","obj")} {p.get("confidence",0):.2f}'
        draw.rectangle([x1,y1,x2,y2],outline=(0,160,80),width=3)
        tw=draw.textlength(label)
        draw.rectangle([x1,y1-18,x1+tw+6,y1],fill=(0,160,80))
        draw.text((x1+3,y1-16),label,fill=(0,0,0))
    return img

def preds_to_df(preds):
    if not preds: return pd.DataFrame(columns=["class","confidence","x","y","width","height"])
    return pd.DataFrame([{**p,
        "x1":p["x"]-p["width"]/2,"y1":p["y"]-p["height"]/2,
        "x2":p["x"]+p["width"]/2,"y2":p["y"]+p["height"]/2
    } for p in preds])

def normalize_label(raw:str)->str:
    base=re.split(r"[-|]",str(raw))[0].strip().lower().replace("_"," ")
    return {"plasticfilms":"plastic film","plasticfilm":"plastic film",
            "plastic films":"plastic film","plastic bag":"plastic film"}.get(base,base)

def is_plastic_film(preds): return any(normalize_label(p.get("class",""))=="plastic film" for p in preds)

def render_result_banner(is_plastic):
    if is_plastic:
        st.markdown("<div class='result-banner result-yes'><span class='emoji'>♻️</span>It's a plastic film</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='result-banner result-no'><span class='emoji'>🚫</span>Not a plastic film</div>", unsafe_allow_html=True)

# ---------------- INPUT AREA ----------------
tab_up,tab_url,tab_cam=st.tabs(["Upload","URL","Camera"])

with tab_up:
    file=st.file_uploader("Upload",type=["jpg","jpeg","png"],label_visibility="collapsed")
with tab_url:
    c1,c2,c3=st.columns([1,2,1])
    with c2: url_in=st.text_input("URL",placeholder="Paste image URL",label_visibility="collapsed")
with tab_cam:
    c1,c2,c3=st.columns([1,2,1])
    with c2: cam_file=st.camera_input("Camera",label_visibility="collapsed")

# ---------------- WORKING RUN DETECTION BUTTON ----------------
st.markdown("<div class='run-btn'>", unsafe_allow_html=True)
run_clicked = st.button("Run Detection", type="primary")
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- INFERENCE ----------------
if run_clicked:
    if not API_KEY:
        st.error("Missing Roboflow API key in Settings or secrets.")
        st.stop()

    endpoint=f"{API_URL.rstrip('/')}/{PROJECT}/{int(VERSION)}"
    params={"api_key":API_KEY,"confidence":int(CONF),"overlap":int(OVERLAP),"format":"json"}

    pil_in,jpeg_buf,resp=None,None,None
    try:
        if cam_file:
            pil_in,jpeg_buf=compress_image(cam_file,MAX_SIDE,QUALITY)
            resp=requests.post(endpoint,params=params,files={"file":("cam.jpg",jpeg_buf,"image/jpeg")},timeout=60)
        elif file:
            pil_in,jpeg_buf=compress_image(file,MAX_SIDE,QUALITY)
            resp=requests.post(endpoint,params=params,files={"file":("image.jpg",jpeg_buf,"image/jpeg")},timeout=60)
        elif url_in:
            pil_in=Image.open(requests.get(url_in,stream=True,timeout=20).raw)
            resp=requests.get(endpoint,params={**params,"image":url_in},timeout=60)
        else:
            st.warning("Please provide an image first.")
            st.stop()

        resp.raise_for_status()
        data=resp.json(); preds=data.get("predictions",[])
        df=preds_to_df(preds)

        colL,colR=st.columns(2)
        with colL:
            if pil_in is not None:
                st.image(draw_preds(pil_in,preds) if preds else pil_in, width=420)
        with colR:
            st.markdown("### Result")
            render_result_banner(is_plastic_film(preds))
            st.markdown("### Raw predictions")
            st.dataframe(df,use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")

# ---------------- SETTINGS ----------------
st.markdown("---")
with st.expander("⚙️ Settings"):
    c1,c2,c3=st.columns(3)
    with c1:
        st.session_state["PROJECT"]=st.text_input("Project",PROJECT)
        st.session_state["VERSION"] = st.number_input("Version", min_value=1, max_value=50, value=int(VERSION), step=1)
        st.session_state["API_URL"]=st.selectbox("Endpoint",["https://detect.roboflow.com","https://infer.roboflow.com"])
    with c2:
        st.session_state["CONF"]=st.slider("Confidence (%)",0,100,int(CONF))
        st.session_state["OVERLAP"]=st.slider("Overlap (%)",0,100,int(OVERLAP))
    with c3:
        st.session_state["MAX_SIDE"]=st.slider("Resize px",512,2048,int(MAX_SIDE),step=64)
        st.session_state["QUALITY"]=st.slider("JPEG quality",50,95,int(QUALITY))
    st.session_state["API_KEY"]=st.text_input("Roboflow API key",API_KEY,type="password")

# ---------------- QUIZ ----------------
with st.expander("🧠 Quick Quiz: What Goes Where?"):
    q = [
        ("Plastic grocery bags?", ["Curbside", "Store drop-off", "Landfill"], "Store drop-off"),
        ("Paper coffee cups?", ["Curbside", "Compost", "Landfill"], "Landfill"),
        ("Cardboard boxes?", ["Curbside", "Landfill"], "Curbside")
    ]
    with st.form("quiz"):
        answers = [st.radio(prompt, opts, index=0, key=f"q{i}") for i, (prompt, opts, _) in enumerate(q)]
        if st.form_submit_button("Check"):
            score=sum(a==q[i][2] for i,a in enumerate(answers))
            if score==len(q): st.success("Perfect! ✅")
            else: st.warning(f"{score}/{len(q)} correct — check local recycling rules.")
