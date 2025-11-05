import io, re, requests
from PIL import Image, ImageOps, ImageDraw, ImageFilter
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import threading
import time
import base64, io
import os
BASE_DIR = os.path.dirname(__file__)

# ---------- PAGE ----------
st.set_page_config(
    page_title="AI-Powered Recyclable Material Detector",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---- Force theme primary color to blue-green ----
st.markdown("""
<style>
:root {
    --primary-color: #2563eb;       /* Deep blue */
    --secondary-color: #22c55e;     /* Bright green */
    --text-color: #ffffff;
}

/* Override Streamlit's button primary color */
button[kind="primary"], button[data-testid="baseButton-primary"] {
    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color)) !important;
    color: var(--text-color) !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 10px 26px !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em;
    box-shadow: 0 6px 16px rgba(37,99,235,.25), 0 4px 12px rgba(34,197,94,.25);
    transition: all 0.25s ease-in-out;
}

/* Hover + active */
button[kind="primary"]:hover {
    filter: brightness(1.08);
    transform: translateY(-1px);
}
button[kind="primary"]:active {
    transform: scale(0.97);
    filter: brightness(0.9);
}
</style>
""", unsafe_allow_html=True)


# 1) Strong, early CSS injection (works even if normal markdown is finicky)
CSS = r"""
/* ===== sanity check: turn h1 text blue briefly ===== */
h1 { color: #2563eb !important; }

/* ----- Center the tab row ("Upload","URL","Camera") and color active ----- */
div[role="tablist"] { justify-content: center; gap: 12px; margin: 10px 0 6px; }
div[role="tablist"] button[role="tab"]{
  border: 1.5px solid #e5e7eb; background: #fff; color:#374151; padding:8px 16px;
  border-radius:999px; font-weight:600; box-shadow:0 1px 3px rgba(0,0,0,.06);
}
div[role="tablist"] button[role="tab"]:hover{ border-color:#cbd5e1; background:#f8fafc; }
div[role="tablist"] button[role="tab"][aria-selected="true"]{
  color:#fff; border-color:transparent; box-shadow:0 6px 18px rgba(0,0,0,.08);
  background: linear-gradient(90deg,#2563eb,#22c55e);
}

/* ----- Compact centered uploader; "Browse files" centered; hint below ----- */
.uploader-center { max-width: 380px; margin: 0 auto; }
.uploader-center [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] { padding:14px; background:#f3f4f6; border:1px solid #e5e7eb; border-radius:12px; }
.uploader-center [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] > div{
  display:flex !important; flex-direction:column-reverse !important; align-items:center !important; gap:8px; text-align:center;
}
/* center the Browse control regardless of markup differences */
.uploader-center [data-testid="stFileUploaderDropzone"] label,
.uploader-center [data-testid="stFileUploaderDropzone"] button,
.uploader-center [data-testid="stFileUploaderDropzone"] [role="button"]{
  margin:0 auto !important; align-self:center !important; display:inline-flex !important; justify-content:center;
  background:#e5e7eb !important; color:#2563eb !important; border:1px solid #d1d5db !important; border-radius:999px !important;
  padding:8px 16px !important; font-weight:700 !important;
}
.uploader-center [data-testid="stFileUploaderDropzone"] [role="button"]:hover{ background:#d1d5db !important; }

/* ----- Gray expander headers + TrashTalker text color (Settings, Quick Quiz) ----- */
.gray-expander [data-testid="stExpander"] > details > summary{
  background:#f3f4f6; border:1px solid #e5e7eb; border-radius:10px; padding:10px 12px; color:#2563eb !important; font-weight:700;
}

/* ----- Center & theme the Run Detection button (works primary/secondary) ----- */
.run-btn [data-testid="baseButton-primary"],
.run-btn .stButton > button[kind="primary"],
.run-btn [data-testid="baseButton-secondary"],
.run-btn .stButton > button[kind="secondary"],
.run-btn .stButton > button:not([kind]) {
  background: linear-gradient(90deg, #2563eb, #22c55e) !important;
  color:#fff !important; border:none !important; border-radius:999px !important; padding:10px 24px !important;
  font-weight:800 !important; letter-spacing:.02em; box-shadow:0 10px 24px rgba(37,99,235,.25);
}
.run-btn .stButton > button:hover{ filter:brightness(1.05); transform:translateY(-1px); box-shadow:0 12px 28px rgba(34,197,94,.30); }

/* ----- Smaller detection image ----- */
.detect-img { display:block; margin:0 auto; max-width:420px; }
"""

# inject into the main document head reliably
components.html(f"<style>{CSS}</style>", height=0, scrolling=False)

## Buttons background ###
st.markdown("""
<style>
/* --- Centered, compact uploader wrapper --- */
.uploader-center { max-width: 380px; margin: 0 auto; }

/* Put the hint text UNDER the Browse button and center everything */
.uploader-center [data-testid="stFileUploaderDropzone"] { padding: 14px; }
.uploader-center [data-testid="stFileUploaderDropzone"] > div {
  display: flex !important;
  flex-direction: column-reverse !important;  /* hint below the button */
  align-items: center !important;
  gap: 8px; text-align: center;
}

/* Gray background for the whole dropzone */
.uploader-center [data-testid="stFileUploaderDropzone"] {
  background: #f3f4f6;                 /* gray-100 */
  border: 1px solid #e5e7eb;           /* gray-200 */
  border-radius: 12px;
}

/* Force the Browse button to be centered + gray */
.uploader-center [data-testid="stFileUploaderDropzone"] label,
.uploader-center [data-testid="stFileUploaderDropzone"] button,
.uploader-center [data-testid="stFileUploaderDropzone"] [role="button"]{
  margin: 0 auto !important;
  align-self: center !important;
  display: inline-flex !important;
  justify-content: center;
  background: #e5e7eb !important;      /* gray-200 button */
  color: #111827 !important;            /* gray-900 text */
  border: 1px solid #d1d5db !important; /* gray-300 */
  border-radius: 999px !important;      /* pill */
  padding: 8px 16px !important;
  font-weight: 600 !important;
}
.uploader-center [data-testid="stFileUploaderDropzone"] [role="button"]:hover{
  background:#d1d5db !important;        /* gray-300 hover */
}

/* === Unified expander styling matching the uploader box === */
.gray-expander [data-testid="stExpander"] > details {
  background: #f8fafc !important;           /* slightly darker gray-blue than page bg */
  border: 1.5px solid #e5e7eb !important;
  border-radius: 14px !important;
  margin-top: 16px !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  overflow: hidden;
}

/* Expander header — bold, blue-green accent */
.gray-expander [data-testid="stExpander"] > details > summary {
  background: linear-gradient(90deg, rgba(37,99,235,0.08), rgba(34,197,94,0.08)) !important;
  color: #2563eb !important;                /* same blue as tagline */
  font-weight: 700 !important;
  padding: 14px 16px !important;
  font-size: 1rem !important;
  border-bottom: 1px solid #e5e7eb !important;
  text-align: left !important;
  cursor: pointer;
  transition: all 0.25s ease-in-out;
}

/* Hover effect — more vibrant gradient */
.gray-expander [data-testid="stExpander"] > details > summary:hover {
  background: linear-gradient(90deg, rgba(37,99,235,0.15), rgba(34,197,94,0.15)) !important;
}

/* Expanded content area */
.gray-expander [data-testid="stExpander"] > details[open] {
  background: #f9fafb !important;
  border-radius: 14px !important;
  padding-bottom: 14px !important;
}

/* Inner content spacing */
.gray-expander [data-testid="stExpander"] div[data-testid="stExpanderContent"] {
  padding: 12px 16px 0 16px !important;
}

/* Smooth open animation */
.gray-expander details[open] summary ~ * {
  animation: fadeIn 0.25s ease-in;
}
@keyframes fadeIn {
  from {opacity: 0; transform: translateY(-4px);}
  to {opacity: 1; transform: translateY(0);}
}

/* === Remove top padding added by Streamlit === */
section.main > div:first-child {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}
.block-container {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}

/* === Force hero header to start fully visible === */
.hero-wrap {
    margin-top: 0 !important;
    padding-top: 20px !important;  /* gentle buffer to prevent clipping */
    margin-bottom: 16px !important;
    line-height: 1.2;
}

/* === Optional: hide Streamlit header space (if logged in) === */
[data-testid="stHeader"] {
    display: none;
}

/* === Unified Blue-Green Gradient Theme === */
.subheading {
  text-align: center;
  font-family: 'Roboto', -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  font-weight: 800;
  font-size: clamp(18px, 2vw, 26px);
  margin-top: 12px;
  margin-bottom: 14px;
  background: linear-gradient(90deg, #2563eb 0%, #22c55e 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.08));
  letter-spacing: 0.03em;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* ==== FORCE consistent look for Settings + Quick Quiz expanders ==== */

/* 1️⃣ Outer expander box */
[data-testid="stExpander"] {
  background: #f3f4f6 !important;            /* visible gray tone */
  border: 1.5px solid #e5e7eb !important;    /* gray-200 */
  border-radius: 14px !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  margin-top: 18px !important;
  overflow: hidden;
}

/* 2️⃣ Expander header */
[data-testid="stExpander"] > details > summary {
  background: linear-gradient(90deg, rgba(37,99,235,0.10), rgba(34,197,94,0.10)) !important;
  color: #2563eb !important;                 /* theme blue */
  font-weight: 700 !important;
  font-size: 1rem !important;
  border-bottom: 1px solid #e5e7eb !important;
  padding: 14px 18px !important;
  cursor: pointer;
  transition: background 0.25s ease-in-out;
  list-style: none;
}

/* 3️⃣ Hover gradient */
[data-testid="stExpander"] > details > summary:hover {
  background: linear-gradient(90deg, rgba(37,99,235,0.20), rgba(34,197,94,0.20)) !important;
}

/* 4️⃣ Expanded content area */
[data-testid="stExpander"] > details[open] {
  background: #f9fafb !important;            /* slightly lighter */
  border-radius: 0 0 14px 14px !important;
  padding-bottom: 12px !important;
}

/* 5️⃣ Inner content padding */
[data-testid="stExpanderContent"] {
  padding: 12px 18px !important;
  background: #f9fafb !important;
}

/* 6️⃣ Smooth open animation */
[data-testid="stExpander"] details[open] summary ~ * {
  animation: fadeIn 0.25s ease-in;
}
@keyframes fadeIn {
  from {opacity: 0; transform: translateY(-4px);}
  to {opacity: 1; transform: translateY(0);}
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Reduce the empty space above the header */
.hero-wrap {
  text-align: center;
  margin-top: -30px;        /* pulls it up slightly */
  margin-bottom: 16px;
  line-height: 1.25;
  padding-top: 0;
}

/* Remove default Streamlit top padding */
[data-testid="stAppViewContainer"] > .main {
  padding-top: 1rem !important;   /* default is ~6rem; this brings it up */
}
.hero-title {
  font-family: 'Roboto', -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  text-transform: uppercase;
  font-weight: 800;
  letter-spacing: .08em;
  font-size: clamp(34px, 5vw, 54px);
  background: linear-gradient(90deg, #2563eb, #22c55e);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, .08));
  margin-bottom: 6px;
}

.hero-tagline {
  font-family: 'Roboto', -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  font-size: clamp(16px, 2vw, 22px);
  font-weight: 500;
  color: #4b5563;
  letter-spacing: .01em;
  margin-top: 0;
}

/* NEW subtitle styling */
.hero-subtitle {
  font-family: 'Roboto', -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  font-weight: 600;
  font-size: clamp(18px, 2.5vw, 26px);  /* slightly larger */
  letter-spacing: .03em;
  background: linear-gradient(90deg, #22c55e, #38bdf8); /* matches site theme */
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 2px 8px rgba(0,0,0,.08));
  margin-top: 0;
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

/* Completely remove default top padding/margin from Streamlit containers */
section.main > div:first-child {
  padding-top: 0rem !important;
  margin-top: 0rem !important;
}

/* Override internal padding inside block container */
.block-container {
  padding-top: 0rem !important;
  margin-top: 0rem !important;
}

/* Optional: pull hero up slightly if still too low */
.hero-wrap {
  margin-top: -40px !important;   /* Adjust: -20 to -60 */
  margin-bottom: 16px !important;
  line-height: 1.2;
}

/* --- Final top-spacing fix for Streamlit --- */

/* Kill padding/margin in every top-level container */
section.main, .block-container, .block-container > div, [data-testid="stVerticalBlock"] {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* Specifically target the first visible block to remove top padding */
section.main > div:first-child,
.block-container > div:first-child,
[data-testid="stVerticalBlock"] > div:first-child {
    margin-top: -40px !important;  /* pull up hero tighter to top */
}

/* Keep your hero spacing consistent */
.hero-wrap {
    margin-top: -40px !important;
    margin-bottom: 12px !important;
    line-height: 1.2;
}

img {
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.25);
}

/* ==== Arrow Buttons Styled to Match Hero Tagline ==== */
.carousel-arrow {
  background: linear-gradient(90deg, #22c55e, #38bdf8); /* same gradient as hero-tagline */
  color: white;
  border: none;
  border-radius: 999px;
  width: 46px;
  height: 46px;
  font-size: 22px;
  font-weight: bold;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(34, 197, 94, 0.2), 0 4px 16px rgba(56, 189, 248, 0.2);
  transition: all 0.25s ease-in-out;
}

/* Hover & active state */
.carousel-arrow:hover {
  filter: brightness(1.1);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(56, 189, 248, 0.3);
}
.carousel-arrow:active {
  transform: scale(0.95);
}

/* Center arrows beside the image */
.carousel-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
}

/* === Themed Circular Arrow Buttons === */
.arrow-btn > button {
  background: linear-gradient(90deg, #2563eb, #22c55e) !important; /* TrashTalker theme */
  color: #ffffff !important;              /* arrow color */
  border: none !important;
  border-radius: 50% !important;          /* perfect circle */
  width: 48px !important;
  height: 48px !important;
  font-size: 22px !important;
  font-weight: 700 !important;
  cursor: pointer !important;
  transition: all 0.25s ease-in-out;
  box-shadow: 0 4px 14px rgba(37,99,235,0.25), 0 4px 14px rgba(34,197,94,0.25);
  display: flex !important;
  align-items: center;
  justify-content: center;
}

/* Hover: subtle glow + lift */
.arrow-btn > button:hover {
  filter: brightness(1.1);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(37,99,235,0.35), 0 6px 20px rgba(34,197,94,0.35);
}

/* Click: tiny shrink */
.arrow-btn > button:active {
  transform: scale(0.93);
  filter: brightness(0.9);
}

/* Center container so arrows don't misalign */
.arrow-btn {
  display: flex;
  justify-content: center;
  align-items: center;
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Target ONLY the Run Detection button — by position and text */
div[data-testid="stVerticalBlock"] button[kind="primary"],
div[data-testid="stVerticalBlock"] button:has(span:contains("Run Detection")) {
    background: linear-gradient(90deg, #2563eb, #22c55e) !important;
    color: white !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 10px 28px !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
    letter-spacing: .02em !important;
    box-shadow: 0 6px 18px rgba(37,99,235,.25), 0 4px 14px rgba(34,197,94,.25) !important;
    transition: all 0.25s ease-in-out !important;
}

/* Hover and active effects */
div[data-testid="stVerticalBlock"] button[kind="primary"]:hover {
    filter: brightness(1.08);
    transform: translateY(-2px);
}
div[data-testid="stVerticalBlock"] button[kind="primary"]:active {
    transform: scale(0.97);
    filter: brightness(0.9);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* === Match Settings & Quick Quiz with Drag-and-Drop container === */
.gray-expander [data-testid="stExpander"] > details {
  background: #f3f4f6 !important;            /* same as uploader bg (#f3f4f6) */
  border: 1px solid #e5e7eb !important;      /* light gray border */
  border-radius: 12px !important;
  padding: 0 !important;
  margin-top: 12px !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);    /* soft depth */
}

/* Expander header styling (matches uploader text color & shape) */
.gray-expander [data-testid="stExpander"] > details > summary {
  background: #f3f4f6 !important;
  color: #2563eb !important;                /* blue theme color */
  font-weight: 700 !important;
  padding: 12px 14px !important;
  border-radius: 12px !important;
  border: 1px solid #e5e7eb !important;
  text-align: left !important;
  list-style: none !important;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

/* Hover effect for consistency */
.gray-expander [data-testid="stExpander"] > details > summary:hover {
  background: #e5e7eb !important;           /* gray-200 hover like uploader */
  border-color: #d1d5db !important;
}

/* Content area matches uploader container background */
.gray-expander [data-testid="stExpander"] > details[open] {
  background: #f3f4f6 !important;
  border-radius: 12px !important;
  padding-bottom: 12px !important;
}

/* Smooth expand animation */
.gray-expander details[open] summary ~ * {
  animation: fadeIn 0.25s ease-in;
}
@keyframes fadeIn {
  from {opacity: 0; transform: translateY(-4px);}
  to {opacity: 1; transform: translateY(0);}
}
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

# ---------- HEADER SECTION ----------
st.markdown("""
<div class="hero-wrap" style="margin-top:-10px;">
  <div class="hero-title"> TrashTalker </div>
  <div class="hero-accent">
  <div class="hero-tagline">
  AI-driven material detection and sorting for a cleaner planet
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------- IMAGE SLIDER SECTION ----------

col_left, col_right = st.columns(2, gap="large")

BASE_DIR = os.path.dirname(__file__)

# Image paths
trash_images = [
    os.path.join(BASE_DIR, "assets", "smartbin1.jpg"),
    os.path.join(BASE_DIR, "assets", "smartbin2.jpg"),
    os.path.join(BASE_DIR, "assets", "smartbin3.jpg"),
    os.path.join(BASE_DIR, "assets", "smartbin4.jpg"),
    os.path.join(BASE_DIR, "assets", "smartbin5.jpg"),
    os.path.join(BASE_DIR, "assets", "smartbin6.jpg"),

]
nextrex_images = [
    os.path.join(BASE_DIR, "assets", "nextrex1.jpg"),
    os.path.join(BASE_DIR, "assets", "nextrex2.jpg"),
    os.path.join(BASE_DIR, "assets", "nextrex3.jpg"),
]

# Initialize indices once
if "trash_idx" not in st.session_state:
    st.session_state.trash_idx = 0
if "nextrex_idx" not in st.session_state:
    st.session_state.nextrex_idx = 0

# ✅ Initialize arrow click state flags
for key in ["trash_idx_prev", "trash_idx_next", "nextrex_idx_prev", "nextrex_idx_next"]:
    if key not in st.session_state:
        st.session_state[key] = False

# Helper function to load images safely
def load_uniform(path, box_size=(400, 300), fill=(245, 245, 245)):
    """Load image with correct EXIF orientation and pad to fixed size."""
    img = Image.open(path).convert("RGB")
    # ✅ Correct orientation from camera EXIF (prevents sideways rotation)
    img = ImageOps.exif_transpose(img)
    # Resize while preserving aspect ratio
    img.thumbnail(box_size, Image.Resampling.LANCZOS)
    # Center the image inside a padded background to keep dimensions consistent
    bg = Image.new("RGB", box_size, fill)
    x = (box_size[0] - img.width) // 2
    y = (box_size[1] - img.height) // 2
    bg.paste(img, (x, y))
    return bg

def load_filled(path, box_size=(400, 300)):
    """
    Open image, correct EXIF orientation, and fill the box by center-cropping.
    Produces clean, edge-to-edge images without gray padding.
    """
    img = Image.open(path).convert("RGB")
    img = ImageOps.exif_transpose(img)  # fix sideways rotation
    # --- Fill the box instead of padding it ---
    img = ImageOps.fit(img, box_size, Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    return img

def load_fit_dark(path, box_size=(400, 300), bg_color=(14, 17, 23)):
    """
    Open image, fix orientation, and fit it into a Streamlit-dark background box.
    Keeps full image visible and avoids patchwork. (#374151 ≈ rgb(55,65,81))
    """
    img = Image.open(path).convert("RGB")
    img = ImageOps.exif_transpose(img)

    # Resize to fit completely (no cropping)
    img.thumbnail(box_size, Image.Resampling.LANCZOS)

    # Create background matching Streamlit dark theme
    bg = Image.new("RGB", box_size, bg_color)

    # Center the image
    x = (box_size[0] - img.width) // 2
    y = (box_size[1] - img.height) // 2
    bg.paste(img, (x, y))

    # Slight softening blend for uniform tone
    blended = Image.blend(bg, bg.filter(ImageFilter.GaussianBlur(4)), alpha=0.02)
    blended.paste(img, (x, y))

    return blended
import streamlit.components.v1 as components

# ---------- CONFIG ----------
CONTAINER_HEIGHT = 400  # keep both columns equal height
BUTTON_STYLE = """
background: linear-gradient(90deg,#2563eb,#22c55e);
color: white;
border: none;
border-radius: 50%;
width: 46px;
height: 46px;
font-size: 22px;
font-weight: 700;
cursor: pointer;
box-shadow: 0 4px 14px rgba(37,99,235,0.25),
             0 4px 14px rgba(34,197,94,0.25);
transition: all 0.25s ease-in-out;
"""

# ---------- HELPERS ----------
def render_arrow_buttons(idx_key):
    """Render themed circular arrow buttons; return -1, 0, or +1."""
    c1, _, c3 = st.columns([1, 6, 1])
    delta = 0

    st.markdown("""
    <style>
    .stButton > button {
        background: linear-gradient(90deg, #2563eb, #22c55e) !important;
        color: white !important;
        border: none !important;
        border-radius: 50% !important;
        width: 46px !important;
        height: 46px !important;
        font-size: 22px !important;
        font-weight: 700 !important;
        cursor: pointer !important;
        box-shadow: 0 4px 14px rgba(37,99,235,0.25),
                     0 4px 14px rgba(34,197,94,0.25);
        transition: all 0.25s ease-in-out;
    }
    .stButton > button:hover {
        filter: brightness(1.1);
        transform: translateY(-2px);
    }
    .stButton > button:active {
        transform: scale(0.95);
        filter: brightness(0.9);
    }
    </style>
    """, unsafe_allow_html=True)

    with c1:
        if st.button("←", key=f"{idx_key}_left"):
            delta = -1
    with c3:
        if st.button("→", key=f"{idx_key}_right"):
            delta = +1

    return delta

# ---------- TWO COLUMN LAYOUT ----------
col_left, col_right = st.columns(2, gap="large")

# Inject targeted CSS to eliminate Streamlit vertical gaps
st.markdown("""
<style>
/* Tighten spacing between subheading and image */
.block-container [data-testid="column"] > div {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
.block-container [data-testid="stVerticalBlock"] {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
div[data-testid="stImage"] {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
.subheading {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- TWO COLUMN LAYOUT ----------
col_left, col_right = st.columns(2, gap="large")
import base64, io

# Two columns with equal width
col_left, col_right = st.columns(2, gap="large")

for col, title, images, idx_key in [
    (col_left, "TrashTalker Smart Bin Prototype", trash_images, "trash_idx"),
    (col_right, "NexTrex Sustainability Initiative", nextrex_images, "nextrex_idx"),
]:
    with col:
        # --- Load + normalize image size ---
        img = load_fit_dark(images[st.session_state[idx_key]], box_size=(400, 300))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        encoded_img = base64.b64encode(buf.getvalue()).decode()

        # --- Unified block with fixed height ---
        st.markdown(f"""
        <div class="gallery-item" style="
            display:flex; 
            flex-direction:column; 
            align-items:center; 
            justify-content:center; 
            height:420px; 
            text-align:center; 
            margin:0; 
            padding:0;">
            <div class="subheading" style="margin:0; padding-bottom:6px;">{title}</div>
            <img src="data:image/jpeg;base64,{encoded_img}"
                 style="height:300px; width:auto; border-radius:12px; object-fit:contain; display:block;"/>
            <p style='text-align:center;color:#6b7280;margin:6px 0 0;'>Image {st.session_state[idx_key]+1} of {len(images)}</p>
        </div>
        """, unsafe_allow_html=True)

        # --- Arrows below image ---
        with st.container():
            st.markdown("<div style='text-align:center; margin-top:4px;'>", unsafe_allow_html=True)
            delta = render_arrow_buttons(idx_key)
            st.markdown("</div>", unsafe_allow_html=True)

            if delta != 0:
                st.session_state[idx_key] = (st.session_state[idx_key] + delta) % len(images)

# Add CSS to ensure alignment between both columns
st.markdown("""
<style>
/* Force equal column height and vertical alignment */
[data-testid="column"] {
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
}

/* Make both image sections same height */
.gallery-item {
    min-height: 420px;
}

/* Center arrows consistently */
.gallery-item + div {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: -4px;
}
</style>
""", unsafe_allow_html=True)


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
st.markdown("""
<style>
/* === FORCE Streamlit red Run Detection button === */

/* Target the specific button text “Run Detection” to isolate it */
div.stButton > button:has(span:contains("Run Detection")),
div[class*="run-btn"] > button,
div[class*="run-btn"] .stButton > button {
    background: #F63366 !important;          /* Streamlit default red */
    color: white !important;
    border: none !important;
    border-radius: 0.5rem !important;
    padding: 0.65rem 1.5rem !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    width: auto !important;
    height: auto !important;
    box-shadow: none !important;
    transform: none !important;
}

/* Hover + active restore defaults */
div.stButton > button:has(span:contains("Run Detection")):hover,
div[class*="run-btn"] .stButton > button:hover {
    background: #ff4b6e !important;          /* lighter hover */
    transform: none !important;
    filter: none !important;
}
div.stButton > button:has(span:contains("Run Detection")):active,
div[class*="run-btn"] .stButton > button:active {
    background: #e0315b !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] {
    background-color: #FFFFFF !important;
  }
</style>
""", unsafe_allow_html=True)

tab_up, tab_url, tab_cam = st.tabs(["Upload", "URL", "Camera"])

with tab_up:
    st.markdown("<div class='uploader-center'>", unsafe_allow_html=True)
    file = st.file_uploader(
        "Upload image",                          # real label (kept accessible)
        type=["jpg","jpeg","png","webp","bmp","tiff"],
        label_visibility="collapsed",
        key="uploader_main"
    )
    st.markdown("</div>", unsafe_allow_html=True)

with tab_url:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        url_in = st.text_input(
            "Image URL",
            placeholder="Paste a PUBLIC image URL",
            label_visibility="collapsed"
        )

with tab_cam:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        cam_file = st.camera_input(
            "Camera",
            label_visibility="collapsed"
        )

left, mid, right = st.columns([1, 1, 1])
with mid:
    # Use HTML for complete control
    st.markdown("""
    <div style='text-align:center;'>
        <button id='run-detect-btn'
                style="
                    background-color:#F63366;
                    color:white;
                    border:none;
                    border-radius:8px;
                    padding:12px 24px;
                    font-weight:700;
                    font-size:16px;
                    cursor:pointer;
                    box-shadow:0 2px 6px rgba(0,0,0,0.15);
                "
                onclick="window.runDetection=true">
            Run Detection
        </button>
    </div>
    """, unsafe_allow_html=True)

# This button won't directly trigger Streamlit's rerun, so add:
if "runDetection" not in st.session_state:
    st.session_state.runDetection = False

# Detect click manually via query param trigger
if st.query_params.get("runDetection"):
    run = True
else:
    run = False


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
                        st.image(draw_preds(pil_in, preds), use_container_width=False, width=420)  # ~420px wide
                    elif pil_in is not None:
                        st.image(pil_in, use_container_width=True)

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

st.markdown("<div class='gray-expander'>", unsafe_allow_html=True)
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
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='gray-expander'>", unsafe_allow_html=True)
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
st.markdown("</div>", unsafe_allow_html=True)
