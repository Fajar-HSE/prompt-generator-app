# AI Creative Director — Prompt Generator App

Web app sederhana untuk generate **image generation prompts siap pakai** berdasarkan skill AI Creative Director, menggunakan Groq API (free tier).

## Fitur

- Form input lengkap sesuai template skill
- Generate prompt untuk DALL-E / Midjourney / Stable Diffusion
- Output: IMAGE PROMPT + NEGATIVE PROMPT + FORMAT + QUALITY SCORE
- Responsive design — pakai di desktop atau mobile
- Bisa pakai API key sendiri atau demo key

## Persiapan

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Dapatkan API Key Groq

- Daftar gratis di https://console.groq.com
- Free tier: 6000 tokens/menit, 30 RPM — cukup untuk penggunaan pribadi
- Salin API key Anda

### 3. Buat File `.env`

Buat file `.env` di folder aplikasi:

```env
GROQ_API_KEY=sk-you-api-key-here
```

### 4. Jalankan App

```bash
python app.py
```

Buka di browser: http://localhost:5000

## Cara Pakai

1. Isi formulir dengan detail program pelatihan Anda
2. Klik **"Generate Prompt"**
3. Salin **IMAGE PROMPT** ke DALL-E / Midjourney / Stable Diffusion
4. Salin **NEGATIVE PROMPT** ke negative prompt field generator gambar

## Topik yang Didukung

Data Analyst, GIS, K3, HVAC, Environmental, LCA, Instructor, Finance, IT Service, Quality Control, dan topik training/sertifikasi lainnya secara otomatis.

## Catatan

- Jika belum punya API key, app tetap berjalan — gunakan **demo mode** untuk melihat contoh output
- Demo mode menggunakan prompt template statis, bukan LLM API call
