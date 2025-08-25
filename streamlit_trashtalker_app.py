import io, urllib.parse, requests
from PIL import Image, ImageOps, ImageDraw, ImageFont
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Roboflow Inference", layout="wide")
st.title("🔍 Roboflow Hosted API — Image Detector")

# ---------------- Sidebar config ----------------
st.sidebar.header("Settings")
PROJECT = st.sidebar.text_input("Project slug", value="trashtalkerobjectdetection-7pded")
VERSION = st.sidebar.number_input("Version", min_value=1, value=3, step=1)
API_URL = st.sidebar.selectbox("Endpoint", ["https://detect.roboflow.com", "https://infer.roboflow.com"])
API_KEY = st.sidebar.text_input("API key", value=st.secrets.get("ROBOFLOW_API_KEY", ""), type="password")
CONF = st.sidebar.slider("Confidence (percent)", 0, 100, 42)
OVERLAP = st.sidebar.slider("Overlap / NMS (%)", 0, 100, 50)
st.sidebar.markdown("---")
MAX_SIDE = st.sidebar.slider("Resize (max side px)", 512, 2048, 1024, step=64)
QUALITY = st.sidebar.slider("JPEG quality", 50, 95, 80)
st.sidebar.caption("Lower these if you still hit 413.")

# ---------------- Inputs ----------------
col_up, col_url = st.columns([1, 1])
with col_up:
    file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"])
with col_url:
    url_in = st.text_input("...or paste a PUBLIC image URL")

run = st.button("Run detection", type="primary")

# ---------------- Helpers ----------------
def compress_image(file_like, max_side=1024, quality=80):
    im = Image.open(file_like)
    im = ImageOps.exif_transpose(im)
    im.thumbnail((max_side, max_side))  # keep aspect ratio
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    buf.seek(0)
    return im, buf  # (PIL image shown to user, JPEG bytes sent to API)

def draw_preds(pil_img, preds):
    img = pil_img.copy()
    draw = ImageDraw.Draw(img)
    # You can load a TTF if you want consistent font sizing
    for p in preds:
        xc, yc = p["x"], p["y"]
        w, h = p["width"], p["height"]
        x1, y1 = xc - w / 2, yc - h / 2
        x2, y2 = xc + w / 2, yc + h / 2
        label = f'{p.get("class", "obj")} {p.get("confidence", 0):.2f}'
        draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0), width=3)
        tw, th = draw.textlength(label), 14
        draw.rectangle([x1, y1 - 18, x1 + tw + 6, y1], fill=(0, 255, 0))
        draw.text((x1 + 3, y1 - 16), label, fill=(0, 0, 0))
    return img

def preds_to_df(preds):
    if not preds:
        return pd.DataFrame(columns=["class", "confidence", "x", "y", "width", "height", "x1", "y1", "x2", "y2"])
    rows = []
    for p in preds:
        xc, yc, w, h = p["x"], p["y"], p["width"], p["height"]
        rows.append({
            "class": p.get("class"), "confidence": round(float(p.get("confidence", 0.0)), 4),
            "x": xc, "y": yc, "width": w, "height": h,
            "x1": xc - w/2, "y1": yc - h/2, "x2": xc + w/2, "y2": yc + h/2
        })
    return pd.DataFrame(rows)

# ---------------- Run ----------------
if run:
    if not API_KEY:
        st.error("Add your API key in the sidebar (or .streamlit/secrets.toml).")
    elif not (file or url_in):
        st.warning("Upload an image or paste a public image URL.")
    else:
        endpoint = f"{API_URL.rstrip('/')}/{PROJECT}/{int(VERSION)}"
        params = {"api_key": API_KEY, "confidence": int(CONF), "overlap": int(OVERLAP), "format": "json"}

        try:
            if file:
                pil_in, jpeg_buf = compress_image(file, max_side=MAX_SIDE, quality=QUALITY)
                st.info(f"Sending ~{len(jpeg_buf.getbuffer())//1024} KB after compression ({pil_in.size[0]}x{pil_in.size[1]}).")
                resp = requests.post(endpoint, params=params, files={"file": ("image.jpg", jpeg_buf, "image/jpeg")}, timeout=60)
            else:
                # URL ingestion (no upload size issue)
                qs = {"api_key": API_KEY, "image": url_in, "confidence": int(CONF), "overlap": int(OVERLAP), "format": "json"}
                # NOTE: For safety, we still show a preview image if URL is valid
                try:
                    pil_in = Image.open(requests.get(url_in, stream=True, timeout=20).raw)
                except Exception:
                    pil_in = None
                resp = requests.get(endpoint, params=qs, timeout=60)

            st.write(f"Status: {resp.status_code}")
            if resp.status_code == 413:
                st.error("413 Request Entity Too Large — reduce image size/quality or use a public URL.")
            resp.raise_for_status()

            data = resp.json()
            preds = data.get("predictions", [])
            df = preds_to_df(preds)

            col1, col2 = st.columns([1.2, 1])
            with col1:
                if pil_in is None and file:
                    pil_in, _ = compress_image(file, max_side=MAX_SIDE, quality=QUALITY)
                if pil_in is not None:
                    st.subheader("Detections")
                    st.image(draw_preds(pil_in, preds), caption="Overlay", use_column_width=True)
            with col2:
                st.subheader("Raw predictions")
                st.dataframe(df, use_container_width=True)
                st.download_button(
                    "Download JSON", data=io.BytesIO(resp.content).getvalue(),
                    file_name="predictions.json", mime="application/json"
                )

        except requests.HTTPError as e:
            st.error(f"HTTP error: {e}\nBody: {getattr(e.response, 'text', '')[:300]}")
        except Exception as e:
            st.exception(e)

