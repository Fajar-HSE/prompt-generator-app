import os
import re

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

app = Flask(__name__)

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_URL = os.getenv("LLM_API_URL", "https://autoapp.biz.id/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

REQUIRED_FIELDS = {
    "programName": "Nama Program",
    "competency": "Topik / Kompetensi",
    "targetAudience": "Target Audience",
}

MAX_FIELD_LENGTH = 2000

SECTION_ORDER = ["IMAGE PROMPT", "NEGATIVE PROMPT", "FORMAT & RESOLUTION", "QUALITY SCORE"]

MATERIAL_BRIEFS = {
    "poster": {
        "brief": (
            "Poster: gabungan menarik perhatian dan mengajak bertindak. "
            "Headline kuat, satu pesan utama, visual mendominasi, CTA jelas. "
            "Boleh sedikit naratif tapi tetap fokus pada satu tujuan."
        ),
        "structure": "Hook -> Main Benefit -> Proof -> CTA",
        "goal": "Menarik & mengonversi",
        "hooks": (
            "Hook poster: tarik perhatian sekaligus sampaikan nilai utama. "
            "Gunakan headline singkat yang langsung ke manfaat atau offer, "
            "didukung kontras visual kuat. Bisa berupa pertanyaan provokatif "
            "('Masih bingung pilih pelatihan yang tepat?') atau statement offer "
            "('Sertifikasi Gratis Bulan Ini')."
        ),
    },
    "brosur": {
        "brief": (
            "Brosur - 'jelaskan dan yakinkan'. Audiens punya waktu untuk membaca, "
            "jadi bahasa boleh lebih lengkap dan persuasif: informatif, profesional, "
            "dan meyakinkan. Jelaskan fitur, manfaat, harga, dan detail. "
            "Gunakan struktur headline + subheadline + penjelasan. "
            "Prinsip: saya perlu menjelaskan produk ini supaya orang yakin."
        ),
        "structure": "Problem -> Solution -> Benefit -> Features -> Proof -> CTA",
        "goal": "Meyakinkan",
        "hooks": (
            "Hook brosur: membuat orang mau masuk ke informasi. Karena waktu baca "
            "lebih panjang, hook tidak harus 'teriak' — lebih elegan dan "
            "positioning-oriented. Pilihan: Problem ('Sulit menemukan rumah yang "
            "nyaman sekaligus dekat pusat kota?'), Promise ('Hunian Modern untuk "
            "Keluarga yang Menginginkan Lebih.'), atau Audience identification "
            "('Untuk Anda yang menginginkan rumah pertama tanpa mengorbankan "
            "kenyamanan.')."
        ),
    },
    "flyer": {
        "brief": (
            "Flyer - 'lihat, tertarik, bertindak'. Sangat singkat dan promosional. "
            "Headline besar, benefit langsung terlihat, CTA jelas. "
            "Prinsip: saya punya beberapa detik untuk membuat orang tertarik."
        ),
        "structure": "Hook -> Offer/Benefit -> Key info -> CTA",
        "goal": "Menarik & mengonversi",
        "hooks": (
            "Hook flyer: membuat orang berhenti dan melihat, lebih agresif. "
            "Tujuan sering conversion, jadi langsung tunjukkan offer: "
            "'PROMO SPESIAL - DISKON 50%', 'BELI 2 GRATIS 1', 'KHUSUS HARI INI!'. "
            "Flyer tidak harus menjelaskan problem; kalau promo sangat menarik, "
            "'DISKON 70%' sudah cukup menjadi hook."
        ),
    },
    "pamflet": {
        "brief": (
            "Pamflet - 'sampaikan pesan'. Untuk edukasi, kampanye, atau pengumuman; "
            "tidak selalu menjual. Bahasa jelas, sederhana, mudah dipahami, "
            "hindari jargon berlebih. Prinsip: saya ingin orang memahami dan mengingat pesan ini."
        ),
        "structure": "Context/Problem -> Information/Solution -> Explanation -> Action",
        "goal": "Mengedukasi",
        "hooks": (
            "Hook pamflet: membuat orang merasa 'informasi ini penting'. "
            "Gunakan: Question ('Tahukah Anda bahwa...?'), Warning ('Waspadai 5 "
            "Tanda...'), Fact ('1 dari 3 orang...'), atau Issue ('Sampah Plastik: "
            "Masalah yang Kita Ciptakan Setiap Hari'). Tujuannya membuat mereka "
            "merasa 'Saya perlu tahu tentang ini', bukan harus membeli."
        ),
    },
    "banner": {
        "brief": (
            "Banner - 'terbaca dalam sekejap'. Sangat sedikit kata, headline besar, "
            "kontras, satu pesan utama, CTA/identitas jelas, hindari paragraf. "
            "Prinsip: orang harus paham pesan bahkan sambil lewat."
        ),
        "structure": "Hook -> Main Benefit/Offer -> CTA",
        "goal": "Attention",
        "hooks": (
            "Hook banner: harus dipahami hampir seketika, 2-7 kata sangat kuat. "
            "Hindari kalimat panjang. Contoh: 'NAIKKAN PRODUKTIVITAS BISNIS', "
            "'PROMO 50%', 'GRATIS KONSULTASI'. Secara visual, hook bukan cuma teks: "
            "ukuran + posisi + kontras + whitespace juga merupakan bagian dari hook."
        ),
    },
    "social_media": {
        "brief": (
            "Social Media Post - 'stop the scroll'. Bahasa conversational, relatable, "
            "emotional, bisa pakai pertanyaan atau hook kuat. Visual dan teks saling "
            "melengkapi, sertakan CTA atau ajakan interaksi. "
            "Prinsip: saya harus membuat orang berhenti scrolling."
        ),
        "structure": "Hook -> Problem -> Insight/Solution -> Value -> CTA/Engagement",
        "goal": "Stop scroll & engagement",
        "hooks": (
            "Hook social media: paling psikologis, ciptakan alasan untuk berhenti "
            "scrolling. Tipe: Curiosity ('Ternyata alasan desainmu terlihat murah "
            "bukan karena warnanya.'), Problem ('Desainmu sudah rapi tapi tetap "
            "terasa membosankan?'), Contrarian ('Logo yang bagus tidak harus "
            "terlihat rumit.'), Mistake ('3 kesalahan yang bikin poster kamu "
            "terlihat amatir.'), atau Result ('Cara membuat poster lebih mudah "
            "dibaca dalam 5 detik.')."
        ),
    },
    "print": {
        "brief": (
            "Cetak A5 - paduan flyer dan brosur: singkat namun bisa menjelaskan. "
            "Headline jelas, benefit utama, detail seperlunya, CTA terlihat. "
            "Sesuaikan dengan ruang cetak A5."
        ),
        "structure": "Hook -> Offer/Benefit -> Features -> CTA",
        "goal": "Meyakinkan & mengonversi",
        "hooks": (
            "Hook print A5: paduan brosur & flyer. Bisa elegan seperti brosur "
            "(positioning/audience identification) atau langsung offer seperti "
            "flyer, tergantung tujuan (edukasi vs promo). Pastikan tetap terbaca "
            "nyaman di ukuran A5."
        ),
    },
}

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
GAYA BAHASA DESAIN: {material_brief}
STRUKTUR KONTEN: {material_structure}
TEKNIK HOOK: {material_hooks}
PLATFORM/FORMAT: {platform_format}
TANGGAL PELAKSANAAN: {date}
LOKASI TEMPAT: {location}
HARGA/BIAYA: {price}
BRAND/NAMA INSTITUSI: {brand}
CTA: {cta}
WARNA BRAND: {brand_colors}
UNIT KOMPETENSI: {unit_kompetensi}
KEUNGGULAN PROGRAM: {program_benefits}

OUTPUT FORMAT — HANYA BAGIAN INI, TANPA ANALISIS PANJANG, GUNAKAN HEADING MARKDOWN `##` DI SETIAP BAGIAN:

## IMAGE PROMPT
[Satu paragraf lengkap dalam bahasa Inggris untuk DALL-E / Midjourney / Stable Diffusion yang mencakup: subject, environment, action, composition, camera, lighting, visual style, color, typography area, professional quality, aspect ratio. WAJIB terapkan secara eksplisit dalam desain:
- HEADLINE / TEKS PEMBUKA HARUS berupa HOOK dari TEKNIK HOOK di atas sesuai jenis materi: poster = kuat & satu pesan, flyer = agresif & langsung offer, brosur = elegan & positioning, pamflet = urgent/important, banner = 2-7 kata kontras, social media = psikologis & stop-scroll, print A5 = paduan brosur/flyer.
- SUSUNAN COPY HARUS mengikuti STRUKTUR KONTEN di atas berurutan (mis. brosur: Problem -> Solution -> Benefit -> Features -> Proof -> CTA); tiap tahap tampil sebagai teks/copy berbeda di dalam layout.
- TONE, PANJANG COPY, HIRARKI, dan LAYOUT HARUS mengikuti GAYA BAHASA DESAIN di atas untuk jenis materi tersebut.
- Wajib cantumkan HARGA/BIAYA, TANGGAL, LOKASI, BRAND, dan CTA (jika bukan 'N/A'/kosong) sebagai elemen teks jelas, terbaca, di posisi strategis. Harga ditulis PERSIS sesuai input user (mis. 'Rp 2.500.000' atau 'Diskon 50%').]

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
- HARGA/BIAYA, TANGGAL, LOKASI, BRAND, dan CTA yang diisi user WAJIB muncul di dalam desain sebagai teks yang konsisten dan mudah dibaca (bukan sekadar disebut). Tuliskan harga persis seperti input (mis. 'Rp 2.500.000' / 'Diskon 50%'). Jika bernilai 'N/A' atau kosong, jangan tampilkan sama sekali.
- WAJIB: gaya bahasa, panjang copy, hierarki teks, dan tone mengikuti GAYA BAHASA DESAIN di atas. Tiap jenis materi (poster, brosur, flyer, pamflet, banner, social media, print) punya karakter berbeda — terapkan, jangan abaikan.
- WAJIB: urutan copy/teks pada desain mengikuti STRUKTUR KONTEN di atas (mis. brosur: Problem -> Solution -> Benefit -> Features -> Proof -> CTA). Setiap tahap harus tampil secara visual dan naratif sesuai tujuannya.
- WAJIB: headline/hook pembuka mengikuti TEKNIK HOOK di atas sesuai jenis materi (brosur elegan & positioning, flyer agresif & offer, pamflet soal urgency/important, banner 2-7 kata kontras, social media psikologis & stop-scroll, poster kuat & satu pesan). Hook bukan hanya teks — pertimbangkan ukuran, posisi, dan kontras visualnya.
"""


def _build_session():
    retries = Retry(
        total=LLM_MAX_RETRIES,
        backoff_factor=1.0,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST"],
        respect_retry_after_header=True,
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

    for field, value in data.items():
        if isinstance(value, str) and len(value) > MAX_FIELD_LENGTH:
            errors.append(
                f"Kolom '{field}' terlalu panjang (maksimal {MAX_FIELD_LENGTH} karakter)."
            )

    return errors


def parse_output(raw_output):
    """Parses markdown-style '## SECTION' output into a dict of sections."""
    sections = {}
    current = None
    buffer = []

    for line in raw_output.splitlines():
        match = re.match(r"^#{1,6}\s*(.+?)\s*$", line.strip())
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
        "platformFormat": "1080x1350px (4:5) — Instagram Feed",
        "date": "N/A",
        "location": "N/A",
        "price": "N/A",
        "brand": "",
        "cta": "",
        "brandColors": "",
        "unit_kompetensi": "",
        "programBenefits": "",
    }
    fields = {**defaults, **{k: (v or "") for k, v in data.items()}}
    brief = MATERIAL_BRIEFS.get(fields["materialType"], MATERIAL_BRIEFS["poster"])
    material_brief = brief["brief"]
    material_structure = f"{brief['structure']}  (Tujuan: {brief['goal']})"
    material_hooks = brief["hooks"]
    return PROMPT_GENERATOR_TEMPLATE.format(
        program_name=fields["programName"],
        competency=fields["competency"],
        program_type=fields["programType"],
        target_audience=fields["targetAudience"],
        material_type=fields["materialType"],
        material_brief=material_brief,
        material_structure=material_structure,
        material_hooks=material_hooks,
        platform_format=fields["platformFormat"],
        date=fields["date"],
        location=fields["location"],
        price=fields["price"],
        brand=fields["brand"],
        cta=fields["cta"],
        brand_colors=fields["brandColors"],
        unit_kompetensi=fields["unit_kompetensi"],
        program_benefits=fields["programBenefits"],
    )


def demo_resolution(material_type, platform_format):
    pf = (platform_format or "").strip()
    # If the platform choice already carries an explicit dimension AND is not the
    # generic default, honor it (the <select> options include concrete sizes).
    if pf and "1080x1350" not in pf and re.search(r"\d+x\d+", pf):
        return pf

    material_type = (material_type or "poster").lower()
    by_material = {
        "poster": "2480x3508px (A4) — poster cetak",
        "brosur": "1748x2480px (A5) — brosur cetak",
        "flyer": "1748x2480px (A5) — flyer cetak",
        "pamflet": "1080x1350px (4:5) — pamflet sosial media",
        "banner": "1200x627px (1.91:1) — web banner",
        "social_media": "1080x1080px (1:1) — social media post",
        "print": "1748x2480px (A5) — cetak A5",
    }
    return by_material.get(material_type, "1080x1350px (4:5) — Instagram Feed poster")


def generate_demo_output(data):
    platform_format = data.get("platformFormat") or ""
    material_type = data.get("materialType") or "poster"
    subject = data.get("targetAudience") or "young professional"
    competency = data.get("competency") or "data analytics"
    brand = data.get("brand") or ""
    unit_kompetensi = data.get("unit_kompetensi") or ""
    program_name = data.get("programName") or "Professional Training Program"
    price = data.get("price") or "N/A"
    date = data.get("date") or "N/A"
    location = data.get("location") or "N/A"
    cta = data.get("cta") or ""

    brief = MATERIAL_BRIEFS.get(material_type, MATERIAL_BRIEFS["poster"])
    structure = brief["structure"]
    goal = brief["goal"]

    hook_examples = {
        "poster": f"Headline hook: '{program_name} - Sertifikasi Diakui Industri'",
        "brosur": f"Headline hook: 'Untuk {subject} yang ingin karier lebih tinggi'",
        "flyer": f"Headline hook: 'PROMO - Diskon 50% {program_name}!'",
        "pamflet": f"Headline hook: 'Tahukah Anda? {competency} kini wajib di Industri 4.0'",
        "banner": f"Headline hook: 'NAIK KARIER LEWAT {competency.upper()}'",
        "social_media": f"Headline hook: '3 Alasan Desain Poster Kamu Terlihat Amatir'",
        "print": f"Headline hook: '{program_name} - Solusi Pelatihan Terbaik'",
    }
    hook = hook_examples.get(material_type, hook_examples["poster"])

    brand_part = f", branded with {brand}" if brand else ""

    image_prompt = (
        f"Professional {material_type} design for {program_name}, target {subject}, topic {competency}. "
        f"Material style (goal: {goal}): {brief['brief']} "
        f"Visual: modern corporate environment, natural lighting, premium color palette, "
        f"negative space for typography, sharp focus, high resolution, professional quality{brand_part}. "
        f"{hook}. "
        f"Copy structure to follow in layout: {structure}. "
        f"Visible text: program name '{program_name}'"
    )

    extras = []
    if price and price != "N/A":
        extras.append(f"price '{price}'")
    if date and date != "N/A":
        extras.append(f"date {date}")
    if location and location != "N/A":
        extras.append(f"location {location}")
    if cta:
        extras.append(f"CTA '{cta}'")
    if extras:
        image_prompt += "; " + ", ".join(extras) + "."
    image_prompt += f" Format: {demo_resolution(material_type, platform_format)}."

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
        "demo_mode": not bool(LLM_API_KEY),
        "model": LLM_MODEL,
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

    if not LLM_API_KEY:
        return jsonify({
            "success": True,
            "demo_mode": True,
            "model": LLM_MODEL,
            "sections": generate_demo_output(data),
        })

    prompt = build_prompt(data)

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": LLM_MODEL,
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
        "max_tokens": LLM_MAX_TOKENS,
        "top_p": 0.9,
    }

    try:
        session = _build_session()
        response = session.post(LLM_API_URL, headers=headers, json=payload, timeout=LLM_TIMEOUT)
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "error": "Waktu permintaan ke LLM API habis. Coba lagi, atau aktifkan demo mode.",
        }), 504
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "error": "Tidak dapat terhubung ke LLM API. Periksa koneksi internet Anda.",
        }), 502
    except requests.exceptions.RequestException as exc:
        return jsonify({
            "success": False,
            "error": f"Gagal menghubungi LLM API: {exc}",
        }), 502

    if response.status_code == 401:
        return jsonify({
            "success": False,
            "error": "API key tidak valid atau tidak ditemukan. Pastikan LLM_API_KEY sudah di-set di file .env.",
        }), 401
    if response.status_code == 429:
        return jsonify({
            "success": False,
            "error": "Rate limit API tercapai. Tunggu sebentar lalu coba lagi, atau aktifkan demo mode.",
        }), 429
    if response.status_code >= 400:
        try:
            detail = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            detail = response.text
        return jsonify({
            "success": False,
            "error": f"LLM API mengembalikan error {response.status_code}: {detail}",
        }), 502

    try:
        result = response.json()
        message = result.get("choices", [{}])[0].get("message", {})
        ai_output = message.get("content") or message.get("reasoning") or ""
    except (ValueError, IndexError, KeyError, TypeError):
        return jsonify({
            "success": False,
            "error": "Respons dari LLM API tidak dapat dipahami. Coba lagi, atau aktifkan demo mode.",
        }), 502

    if not ai_output or not ai_output.strip():
        return jsonify({
            "success": False,
            "error": "LLM API mengembalikan output kosong. Coba lagi.",
        }), 502

    return jsonify({
        "success": True,
        "demo_mode": False,
        "model": LLM_MODEL,
        "sections": parse_output(ai_output),
    })


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=debug, host="127.0.0.1", port=port, use_reloader=False)
