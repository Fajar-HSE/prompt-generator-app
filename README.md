# AI Creative Director — Prompt Generator App

Web app sederhana untuk generate **image generation prompts siap pakai** berdasarkan skill AI Creative Director, menggunakan Groq API (free tier).

## Fitur

- Form input lengkap sesuai template skill dengan validasi di sisi client & server
- Generate prompt untuk DALL-E / Midjourney / Stable Diffusion
- Output terstruktur: **IMAGE PROMPT**, **NEGATIVE PROMPT**, **FORMAT & RESOLUTION**, **QUALITY SCORE** — masing-masing punya tombol salin terpisah, plus tombol **Salin Semua**
- Banner **demo mode** otomatis ketika API key belum diset
- Riwayat generate tersimpan di browser (localStorage, maks 10 entri)
- Responsive design — pakai di desktop atau mobile
- Error handling lengkap: validasi input, rate limit, timeout, retry otomatis
- Model LLM dapat dikonfigurasi via env (`GROQ_MODEL`)

## Persiapan

### 1. Install Dependencies

Disarankan memakai virtual environment:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate  # macOS / Linux

pip install -r requirements.txt
```

### 2. Dapatkan API Key Groq

- Daftar gratis di https://console.groq.com
- Free tier cukup untuk penggunaan pribadi
- Salin API key Anda

### 3. Buat File `.env`

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Lalu isi API key:

```env
GROQ_API_KEY=sk-you-api-key-here
```

### 4. Jalankan App

```bash
python app.py
```

Buka di browser: http://localhost:5000

Tanpa API key app tetap berjalan dalam **demo mode** (output statis, tanpa panggilan LLM).

## Cara Pakai

1. Isi formulir dengan detail program pelatihan Anda
2. Klik **"Generate Prompt"**
3. Salin **IMAGE PROMPT** ke DALL-E / Midjourney / Stable Diffusion
4. Salin **NEGATIVE PROMPT** ke negative prompt field generator gambar
5. Gunakan **FORMAT & RESOLUTION** untuk setting dimensi canvas
6. Pantau **QUALITY SCORE** — regenerate jika ada skor di bawah 8/10

## Konfigurasi Env

| Variabel | Default | Keterangan |
|---|---|---|
| `GROQ_API_KEY` | `""` | API key Groq. Kosong = demo mode. |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Model chat completion Groq. |
| `GROQ_MAX_TOKENS` | `2000` | Batas token output. |
| `GROQ_TIMEOUT` | `60` | Timeout request (detik). |
| `GROQ_MAX_RETRIES` | `3` | Retry otomatis saat rate limit/5xx. |
| `PORT` | `5000` | Port server. |
| `FLASK_DEBUG` | `false` | Aktifkan debug mode (`true`). |

## Menjalankan Test

```bash
pytest -v
```

## Deployment

### Docker

```bash
docker build -t prompt-generator-app .
docker run -p 5000:5000 --env-file .env prompt-generator-app
```

### Heroku / Render / Railway

- Set `GROQ_API_KEY` sebagai environment variable di platform (jangan taruh di file).
- `Procfile` dan `runtime.txt` sudah disediakan untuk Heroku/Render.
- Render: buat **Web Service**, set build command `pip install -r requirements.txt` dan start command `gunicorn -b 0.0.0.0:$PORT -w 2 --timeout 90 app:app`.

### Vercel

Project ini menggunakan framework **Vercel Services**. Pastikan di Vercel Dashboard → Project Settings → Framework Preset bernilai **Services**, dan `vercel.json` memuat blok `services` (sudah disediakan) yang menunjuk ke `app:app` dengan `framework: flask` dan durasi maksimal 60 detik. Lalu set `GROQ_API_KEY` di Environment Variables project Vercel.

```bash
vercel env add GROQ_API_KEY
vercel deploy
```

## API

### `GET /api/status`

Mengembalikan status demo mode & model:

```json
{ "demo_mode": true, "model": "llama-3.3-70b-versatile" }
```

### `POST /api/generate`

Body JSON sama dengan field form. Field wajib: `programName`, `competency`, `targetAudience`.

Respons sukses:

```json
{
  "success": true,
  "demo_mode": false,
  "model": "llama-3.3-70b-versatile",
  "sections": {
    "IMAGE PROMPT": "...",
    "NEGATIVE PROMPT": "...",
    "FORMAT & RESOLUTION": "...",
    "QUALITY SCORE": "..."
  }
}
```

## Topik yang Didukung

Data Analyst, GIS, K3, HVAC, Environmental, LCA, Instructor, Finance, IT Service, Quality Control, dan topik training/sertifikasi lainnya secara otomatis.

## Keamanan

- `GROQ_API_KEY` hanya dipakai di sisi server; tidak pernah dikirim ke browser.
- Pastikan `.env` tidak pernah masuk ke git (sudah ada di `.gitignore`).
- Di production, selalu set key via environment variable platform, bukan `.env`.
