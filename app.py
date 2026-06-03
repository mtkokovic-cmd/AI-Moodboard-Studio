import os
import re
import base64
import tempfile
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from fpdf import FPDF

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="AI Moodboard Studio", page_icon="✨", layout="wide")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f0f0f, #1a1518);
    color: #f5f0e8;
}
h1, h2, h3 {
    color: #f4d7a1;
}
.hero {
    text-align: center;
    padding: 40px 20px;
    border-radius: 25px;
    background: linear-gradient(135deg, #21191d, #111111);
    border: 1px solid #b8925a;
    margin-bottom: 30px;
}
.hero h1 {
    font-size: 52px;
    margin-bottom: 10px;
}
.hero p {
    font-size: 18px;
    color: #d8c7b0;
}
.card {
    background: rgba(255,255,255,0.06);
    padding: 22px;
    border-radius: 18px;
    border: 1px solid rgba(244,215,161,0.25);
    margin-bottom: 18px;
}
.stButton button {
    background: linear-gradient(90deg, #b8925a, #f4d7a1);
    color: #111;
    border-radius: 12px;
    border: none;
    font-weight: bold;
    padding: 10px 22px;
}
.stTextArea textarea {
    background-color: #181818;
    color: #f5f0e8;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

if not OPENAI_API_KEY:
    st.error("OpenAI API ključ nije pronađen. Proveri .env fajl.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

st.markdown("""
<div class="hero">
    <h1>AI Moodboard Studio</h1>
    <p>Create premium brand concepts, color palettes, visual directions, AI moodboards and logos.</p>
</div>
""", unsafe_allow_html=True)


def safe_text(text):
    return text.encode("latin-1", "replace").decode("latin-1")


def prikazi_boje(text):
    hex_boje = re.findall(r"#(?:[0-9a-fA-F]{6})", text)

    if hex_boje:
        st.subheader("🎨 Color Palette")
        cols = st.columns(min(len(hex_boje), 5))

        for i, boja in enumerate(hex_boje[:5]):
            cols[i].markdown(
                f"""
                <div style="
                    background-color:{boja};
                    height:120px;
                    border-radius:18px;
                    border:1px solid #d6b06d;
                    box-shadow: 0 0 18px rgba(0,0,0,0.35);
                "></div>
                <p style="text-align:center; font-weight:bold; color:#f4d7a1;">{boja}</p>
                """,
                unsafe_allow_html=True
            )


def generisi_sliku(prompt):
    image_response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024"
    )
    image_base64 = image_response.data[0].b64_json
    return base64.b64decode(image_base64)


def generisi_logo_koncept(opis):
    prompt = f"""
You are a senior brand designer.

Create a detailed logo and brand identity concept for:
{opis}

Do NOT generate an actual image. Only describe how the logo could look.

Return:
1. Brand Name Ideas
2. Main Logo Concept
3. Logo Symbol/Icon Idea
4. Font Recommendation
5. Slogan Ideas
6. Packaging Direction
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )
    return response.output_text


def napravi_pdf(opis, moodboard, logo_koncept, image_bytes, logo_bytes):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "AI Moodboard Studio Report", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Brand Description:", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 7, safe_text(opis))

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Moodboard:", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 6, safe_text(moodboard))

    if logo_koncept:
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Logo / Brand Concept:", ln=True)
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(0, 6, safe_text(logo_koncept))

    if image_bytes:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(image_bytes)
            image_path = tmp.name

        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Generated Visual Moodboard", ln=True)
        pdf.image(image_path, x=25, y=30, w=160)

    if logo_bytes:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(logo_bytes)
            logo_path = tmp.name

        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Generated Logo", ln=True)
        pdf.image(logo_path, x=40, y=35, w=130)

    pdf_output = pdf.output(dest="S")

    if isinstance(pdf_output, str):
        return pdf_output.encode("latin-1")

    return bytes(pdf_output)


if "rezultat" not in st.session_state:
    st.session_state.rezultat = ""

if "image_prompt" not in st.session_state:
    st.session_state.image_prompt = ""

if "logo_prompt" not in st.session_state:
    st.session_state.logo_prompt = ""

if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None

if "logo_bytes" not in st.session_state:
    st.session_state.logo_bytes = None

if "logo_koncept" not in st.session_state:
    st.session_state.logo_koncept = ""


left, right = st.columns([1.2, 0.8])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Describe your brand")
    opis = st.text_area(
        "Brand description",
        placeholder="Luxury skincare brand for Gen Z women. Soft pink and ivory color palette, premium glass packaging...",
        height=180
    )
    generate = st.button("✨ Generate Moodboard")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Project Features")
    st.write("• Brand strategy")
    st.write("• Target audience")
    st.write("• Color palette")
    st.write("• Visual moodboard")
    st.write("• Logo concept")
    st.write("• AI-generated logo")
    st.write("• PDF export")
    st.markdown('</div>', unsafe_allow_html=True)


if generate:
    if not opis.strip():
        st.warning("Unesi opis brenda.")
    else:
        with st.spinner("Generating premium moodboard..."):
            prompt = f"""
You are a professional creative director.

Create a premium moodboard for this brand:
{opis}

Return:
1. Brand Personality
2. Target Audience
3. Color Palette with HEX codes
4. Visual Style
5. Typography Style
6. Keywords
7. Instagram Content Ideas
8. AI Image Generation Prompts
"""

            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt
            )

            st.session_state.rezultat = response.output_text

            st.session_state.image_prompt = (
                "Create a luxury visual moodboard collage based on this brand concept: "
                + opis
                + ". Premium editorial layout, high-end branding, elegant composition, no text."
            )

            st.session_state.logo_prompt = (
                "Create a clean premium logo design for this brand: "
                + opis
                + ". Minimal luxury logo, elegant symbol, premium branding, centered composition, simple background, no mockup."
            )

            st.session_state.image_bytes = None
            st.session_state.logo_bytes = None
            st.session_state.logo_koncept = ""


if st.session_state.rezultat:
    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📌 Generated Brand Strategy")
        st.markdown(st.session_state.rezultat)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🖼 Visual Moodboard")

        if st.button("Generate AI Image"):
            with st.spinner("Generating image..."):
                st.session_state.image_bytes = generisi_sliku(
                    st.session_state.image_prompt
                )

        if st.session_state.image_bytes:
            st.image(
                st.session_state.image_bytes,
                caption="Generated Visual Moodboard"
            )

            st.download_button(
                label="Download Moodboard Image",
                data=st.session_state.image_bytes,
                file_name="visual_moodboard.png",
                mime="image/png"
            )

        st.markdown('</div>', unsafe_allow_html=True)

    prikazi_boje(st.session_state.rezultat)

    logo_col1, logo_col2 = st.columns([1, 1])

    with logo_col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("✨ Logo / Brand Concept")

        if st.button("Generate Logo Concept"):
            with st.spinner("Generating logo concept..."):
                st.session_state.logo_koncept = generisi_logo_koncept(opis)

        if st.session_state.logo_koncept:
            st.markdown(st.session_state.logo_koncept)

        st.markdown('</div>', unsafe_allow_html=True)

    with logo_col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🎨 Generate Logo")

        if st.button("Generate Logo"):
            with st.spinner("Generating logo..."):
                st.session_state.logo_bytes = generisi_sliku(
                    st.session_state.logo_prompt
                )

        if st.session_state.logo_bytes:
            st.image(
                st.session_state.logo_bytes,
                caption="Generated Logo"
            )

            st.download_button(
                label="Download Logo",
                data=st.session_state.logo_bytes,
                file_name="generated_logo.png",
                mime="image/png"
            )

        st.markdown('</div>', unsafe_allow_html=True)

    pdf_bytes = napravi_pdf(
        opis,
        st.session_state.rezultat,
        st.session_state.logo_koncept,
        st.session_state.image_bytes,
        st.session_state.logo_bytes
    )

    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_bytes,
        file_name="ai_moodboard_report.pdf",
        mime="application/pdf"
    )