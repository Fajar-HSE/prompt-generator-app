document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('promptForm');
    const submitBtn = document.getElementById('submitBtn');
    const outputSection = document.getElementById('outputSection');
    const outputContent = document.getElementById('outputContent');
    const copyBtn = document.getElementById('copyBtn');
    const resetBtn = document.getElementById('resetBtn');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoading = submitBtn.querySelector('.btn-loading');
        const formData = new FormData(form);

        const data = {
            programName: formData.get('programName'),
            competency: formData.get('competency'),
            programType: formData.get('programType'),
            targetAudience: formData.get('targetAudience'),
            materialType: formData.get('materialType'),
            platformFormat: formData.get('platformFormat'),
            date: formData.get('date'),
            location: formData.get('location'),
            price: formData.get('price'),
            brand: formData.get('brand'),
            cta: formData.get('cta'),
            brandColors: formData.get('brandColors'),
            logo: formData.get('logo'),
            programBenefits: formData.get('programBenefits')
        };

        btnText.style.display = 'none';
        btnLoading.style.display = 'inline';
        submitBtn.disabled = true;

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.error) {
                outputContent.textContent = `⚠️ ERROR:\n\n${result.error}\n\n💡 Solusi:\nPastikan file .env sudah berisi GROQ_API_KEY yang valid.\n\nJika belum ada API key, silakan:\n1. Daftar gratis di https://console.groq.com\n2. Buat file .env\ndengan:\n   GROQ_API_KEY=sk-api-key-anda\n3. Restart server.\n\nSambil menunggu, kami tunjukkan contoh output demo:`;
                outputSection.style.display = 'block';
                btnText.style.display = 'inline';
                btnLoading.style.display = 'none';
                submitBtn.disabled = false;
                return;
            }

            if (result.demo_mode) {
                outputContent.innerHTML = result.output + '\n\n---\n⚠️ ANDA SEDANG MELIHAT OUTPUT DEMO.\nBuat file .env dengan GROQ_API_KEY untuk hasil akurat.';
            } else {
                outputContent.textContent = result.output;
            }

            outputSection.style.display = 'block';
            outputSection.scrollIntoView({ behavior: 'smooth' });

        } catch (err) {
            outputContent.textContent = `⚠️ ERROR KONEKSI:\n\n${err.message}\n\nPastikan server sedang berjalan dan terhubung.`;
            outputSection.style.display = 'block';
        } finally {
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
            submitBtn.disabled = false;
        }
    });

    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            const textToCopy = outputContent.textContent || outputContent.innerText;
            navigator.clipboard.writeText(textToCopy).then(function() {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = '✅ Tersalin!';
                setTimeout(function() {
                    copyBtn.textContent = originalText;
                }, 2000);
            }).catch(function(err) {
                alert('Gagal menyalin: ' + err.message);
            });
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            form.reset();
            outputSection.style.display = 'none';
            outputContent.textContent = '';
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
});
