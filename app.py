import os
from flask import Flask, request, jsonify, render_template
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

PROMPT_GENERATOR_TEMPLATE = """
Kamu adalah AI Creative Director ahli yang sedang menghasilkan image generation prompt untuk poster/flyer/pamflet pelatihan dan sertifikasi. Ikuti workflow ini secara cepat:

1. ANALYSIS CEPAT: Analisis target audience, pain point, aspirational identity, dan marketing angle terbaik.
2. VISUAL CONCEPT: Tentukan hero subject, environment, mood, lighting, photography style, dan data/technical elements relevan dengan kompetensi.
3. ART DIRECTION: Composition, camera angle, subject placement, lighting.
4. DESIGN SYSTEM: Color palette (60/30/10), typography (modern sans-serif), layout sesuai jenis materi.
5. QUALITY CONTROL: Pastikan skor minimum 8/10.

INPUT:
NAMA PROGRAM: {program_name}
TOPIK/KOMPETENSI: {competency}
JENIS PROGRAM: {program_type}
TARGET AUDIENCE: {target_audience}
JENIS MATERI: {material_type}
PLATFORM/FORMAT: {platform_format}
TANGGAL PELAKSANAAN: {date}
LOKASI TEMPAT: {location}
HARGA/BIAYA: {price}
BRAND/NAMA INSTITUSI: {brand}
CTA: {cta}
WARNA BRAND: {brand_colors}
LOGO: {logo}
KEUNGGULAN PROGRAM: {program_benefits}

OUTPUT FORMAT — HANYA BAGIAN INI, TANPA ANALISIS PANJANG:

## IMAGE PROMPT
[Satu paragraf lengkap dalam bahasa Inggris untuk DALL-E / Midjourney / Stable Diffusion yang mencakup: subject, environment, action, composition, camera, lighting, visual style, color, typography area, professional quality, aspect ratio]

## NEGATIVE PROMPT
[Satu baris negative prompt — selalu sebutkan: generic stock photo, cheap Canva aesthetic, cluttered composition, excessive text, low quality, unrealistic anatomy, distorted hands, cartoon, watermark, plus negative spesifik topik]

## FORMAT & RESOLUTION
[Disediakan dimensi sesuai jenis materi dan platform — contoh: 1080x1350px for Instagram poster, 1748x2480px for A5 print]

## QUALITY SCORE
Visual Impact: X/10 | Audience Fit: X/10 | Marketing: X/10 | Hierarchy: X/10 | Readability: X/10 | Professionalism: X/10 | Differentiation: X/10 | CTA: X/10 | OVERALL: X/10

ATURAN:
- Prompt dalam bahasa Inggris.
- JANGAN keluarkan analisis panjang — langsung ke format output.
- Visual harus professional, premium, bukan khas Canva generic.
- Negativ prompt harus spesifik dengan topik.
- Jika ada harga, tanggal, atau CTA, sebutkan relevansinya di prompt.
"""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    program_name = data.get("programName", "")
    competency = data.get("competency", "")
    program_type = data.get("programType", "")
    target_audience = data.get("targetAudience", "")
    material_type = data.get("materialType", "poster")
    platform_format = data.get("platformFormat", "Instagram feed 1080x1350")
    date = data.get("date", "N/A")
    location = data.get("location", "N/A")
    price = data.get("price", "N/A")
    brand = data.get("brand", "")
    cta = data.get("cta", "")
    brand_colors = data.get("brandColors", "")
    logo = data.get("logo", "")
    program_benefits = data.get("programBenefits", "")

    prompt = PROMPT_GENERATOR_TEMPLATE.format(
        program_name=program_name,
        competency=competency,
        program_type=program_type,
        target_audience=target_audience,
        material_type=material_type,
        platform_format=platform_format,
        date=date,
        location=location,
        price=price,
        brand=brand,
        cta=cta,
        brand_colors=brand_colors,
        logo=logo,
        program_benefits=program_benefits,
    )

    if not GROQ_API_KEY:
        demo_output = generate_demo_output(
            program_name, competency, target_audience, material_type, platform_format, brand
        )
        return jsonify({
            "success": True,
            "output": demo_output,
            "demo_mode": True
        })

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": "Kamu adalah AI Creative Director profesional yang menghasilkan image generation prompt berdasarkan input program pelatihan. Ikuti format output yang diminta."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 0.9,
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        ai_output = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return jsonify({
            "success": True,
            "output": ai_output,
            "demo_mode": False
        })
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            return jsonify({
                "error": "API key Groq tidak valid atau tidak ditemukan. Pastikan GROQ_API_KEY sudah di-set di file .env"
            }), 401
        return jsonify({
            "error": f"Gagal menghubungi Groq API: {error_msg}. Coba lagi atau gunakan demo mode."
        }), 500


def generate_demo_output(program_name, competency, target_audience, material_type, platform_format, brand):
    return f"""## IMAGE PROMPT
Professional realistic {target_audience or "young professional"} in modern corporate environment, engaged with {competency} tasks, clean contemporary office or training room, natural window lighting, shallow depth of field, corporate editorial photography style, premium color palette, ample negative space for typography overlay, sharp focus, high resolution, professional quality, {platform_format}

## NEGATIVE PROMPT
generic stock photo, cheap Canva aesthetic, cluttered composition, excessive text, tiny typography, unreadable text, random letters, cartoon, low quality, unrealistic anatomy, distorted hands, duplicate people, poor lighting, low contrast, weak hierarchy, watermark, signature

## FORMAT & RESOLUTION
1080x1350px (4:5 portrait) — Instagram Feed poster

## QUALITY SCORE
Visual Impact: 8/10 | Audience Fit: 8/10 | Marketing: 8/10 | Hierarchy: 8/10 | Readability: 8/10 | Professionalism: 8/10 | Differentiation: 7/10 | CTA: 8/10 | OVERALL: 7.7/10

> **Note:** Ini adalah output demo. Buat file `.env` dengan `GROQ_API_KEY` Anda untuk hasil yang lebih akurat.
"""


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
