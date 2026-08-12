import os
import re

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "2000"))
GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "60"))
GROQ_MAX_RETRIES = int(os.getenv("GROQ_MAX_RETRIES", "3"))

REQUIRED_FIELDS = {
    "programName": "Nama Program",
    "competency": "Topik / Kompetensi",
    "targetAudience": "Target Audience",
}

SECTION_ORDER = ["IMAGE PROMPT", "NEGATIVE PROMPT", "FORMAT & RESOLUTION", "QUALITY SCORE"]

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

OUTPUT FORMAT — HANYA BAGIAN INI, TANPA ANALISIS PANJANG, GUNAKAN HEADING MARKDOWN `##` DI SETIAP BAGIAN:

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


def _build_session():
    retries = Retry(
        total=GROQ_MAX_RETRIES,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
        raise_on_status=False,
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def validate_input(data):
    if not isinstance(data, dict):
        return ["Body request harus berupa JSON object."]
    errors = []
    for field, label in REQUIRED_FIELDS.items():
        value = data.get(field)
        if value is None or not str(value).strip():
            errors.append(f"{label} wajib diisi.")
    return errors


def parse_output(raw_output):
    """Parses markdown-style '## SECTION' output into a dict of sections."""
    sections = {}
    current = None
    buffer = []

    for line in raw_output.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line.strip())
        if match:
            if current:
                sections[current] = "\n".join(buffer).strip()
            current = match.group(1).strip()
            buffer = []
        else:
            buffer.append(line)

    if current:
        sections[current] = "\n".join(buffer).strip()

    ordered = {}
    for name in SECTION_ORDER:
        for key in sections:
            if key.upper() == name:
                ordered[name] = sections[key]
                break

    for key, value in sections.items():
        if key not in ordered:
            ordered[key] = value

    return ordered


def build_prompt(data):
    defaults = {
        "programName": "",
        "competency": "",
        "programType": "",
        "targetAudience": "",
        "materialType": "poster",
        "platformFormat": "Instagram feed 1080x1350",
        "date": "N/A",
        "location": "N/A",
        "price": "N/A",
        "brand": "",
        "cta": "",
        "brandColors": "",
        "logo": "",
        "programBenefits": "",
    }
    fields = {**defaults, **{k: (v or "") for k, v in data.items()}}
    return PROMPT_GENERATOR_TEMPLATE.format(
        program_name=fields["programName"],
        competency=fields["competency"],
        program_type=fields["programType"],
        target_audience=fields["targetAudience"],
        material_type=fields["materialType"],
        platform_format=fields["platformFormat"],
        date=fields["date"],
        location=fields["location"],
        price=fields["price"],
        brand=fields["brand"],
        cta=fields["cta"],
        brand_colors=fields["brandColors"],
        logo=fields["logo"],
        program_benefits=fields["programBenefits"],
    )


def demo_resolution(material_type, platform_format):
    haystack = f"{platform_format or ''} {material_type or ''}".lower()
    mapping = [
        (("story", "reel"), "1080x1920px (9:16) — Instagram Story / Reel"),
        (("linkedin", "1200x627", "banner"), "1200x627px (1.91:1) — LinkedIn / web banner"),
        (("a4",), "2480x3508px (A4) — poster cetak"),
        (("a5", "print", "flyer"), "1748x2480px (A5) — flyer cetak"),
        (("social_media", "social"), "1080x1080px (1:1) — social media post"),
        (("1080x1350", "instagram", "feed", "poster", "pamflet"), "1080x1350px (4:5) — Instagram Feed poster"),
    ]
    for keywords, label in mapping:
        if any(kw in haystack for kw in keywords):
            return label
    return "1080x1350px (4:5) — Instagram Feed poster"


def generate_demo_output(data):
    platform_format = data.get("platformFormat") or ""
    material_type = data.get("materialType") or "poster"
    subject = data.get("targetAudience") or "young professional"
    competency = data.get("competency") or "data analytics"
    brand = data.get("brand") or ""
    brand_part = f", branded with {brand}" if brand else ""

    image_prompt = (
        f"Professional realistic {subject} in a modern corporate environment, engaged with {competency} tasks, "
        "clean contemporary office or training room, natural window lighting, shallow depth of field, "
        "corporate editorial photography style, premium color palette, ample negative space for typography "
        f"overlay, sharp focus, high resolution, professional quality{brand_part}, {platform_format}"
    ).strip(", ")

    return {
        "IMAGE PROMPT": image_prompt,
        "NEGATIVE PROMPT": (
            "generic stock photo, cheap Canva aesthetic, cluttered composition, excessive text, tiny typography, "
            "unreadable text, random letters, cartoon, low quality, unrealistic anatomy, distorted hands, "
            "duplicate people, poor lighting, low contrast, weak hierarchy, watermark, signature"
        ),
        "FORMAT & RESOLUTION": demo_resolution(material_type, platform_format),
        "QUALITY SCORE": (
            "Visual Impact: 8/10 | Audience Fit: 8/10 | Marketing: 8/10 | Hierarchy: 8/10 | "
            "Readability: 8/10 | Professionalism: 8/10 | Differentiation: 7/10 | CTA: 8/10 | OVERALL: 7.7/10"
        ),
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    return jsonify({
        "demo_mode": not bool(GROQ_API_KEY),
        "model": GROQ_MODEL,
    })


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True)
    errors = validate_input(data)
    if errors:
        return jsonify({
            "success": False,
            "error": "Validasi gagal. Periksa kembali kolom yang wajib diisi.",
            "fields": errors,
        }), 400

    if not GROQ_API_KEY:
        return jsonify({
            "success": True,
            "demo_mode": True,
            "model": GROQ_MODEL,
            "sections": generate_demo_output(data),
        })

    prompt = build_prompt(data)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Kamu adalah AI Creative Director profesional yang menghasilkan image generation prompt "
                           "berdasarkan input program pelatihan. Ikuti format output yang diminta, gunakan heading "
                           "markdown '## ' untuk setiap bagian.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": GROQ_MAX_TOKENS,
        "top_p": 0.9,
    }

    try:
        session = _build_session()
        response = session.post(GROQ_API_URL, headers=headers, json=payload, timeout=GROQ_TIMEOUT)
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "error": "Waktu permintaan ke Groq API habis. Coba lagi, atau aktifkan demo mode.",
        }), 504
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "error": "Tidak dapat terhubung ke Groq API. Periksa koneksi internet Anda.",
        }), 502
    except requests.exceptions.RequestException as exc:
        return jsonify({
            "success": False,
            "error": f"Gagal menghubungi Groq API: {exc}",
        }), 502

    if response.status_code == 401:
        return jsonify({
            "success": False,
            "error": "API key Groq tidak valid atau tidak ditemukan. Pastikan GROQ_API_KEY sudah di-set di file .env.",
        }), 401
    if response.status_code == 429:
        return jsonify({
            "success": False,
            "error": "Rate limit Groq API tercapai. Tunggu sebentar lalu coba lagi, atau aktifkan demo mode.",
        }), 429
    if response.status_code >= 400:
        try:
            detail = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            detail = response.text
        return jsonify({
            "success": False,
            "error": f"Groq API mengembalikan error {response.status_code}: {detail}",
        }), 502

    try:
        result = response.json()
        ai_output = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    except (ValueError, IndexError, KeyError, TypeError):
        return jsonify({
            "success": False,
            "error": "Respons dari Groq API tidak dapat dipahami. Coba lagi, atau aktifkan demo mode.",
        }), 502

    if not ai_output.strip():
        return jsonify({
            "success": False,
            "error": "Groq API mengembalikan output kosong. Coba lagi.",
        }), 502

    return jsonify({
        "success": True,
        "demo_mode": False,
        "model": GROQ_MODEL,
        "sections": parse_output(ai_output),
    })


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=debug, host="0.0.0.0", port=port)
