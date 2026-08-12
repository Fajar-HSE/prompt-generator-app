(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        const form = document.getElementById('promptForm');
        const submitBtn = document.getElementById('submitBtn');
        const outputSection = document.getElementById('outputSection');
        const outputContainer = document.getElementById('outputContainer');
        const errorBanner = document.getElementById('errorBanner');
        const copyAllBtn = document.getElementById('copyAllBtn');
        const resetBtn = document.getElementById('resetBtn');
        const demoBanner = document.getElementById('demoBanner');
        const historySection = document.getElementById('historySection');
        const historyContainer = document.getElementById('historyContainer');
        const clearHistoryBtn = document.getElementById('clearHistoryBtn');

        const REQUIRED_FIELDS = ['programName', 'competency', 'targetAudience'];
        const STORAGE_KEY = 'promptGeneratorHistory';

        function setLoading(loading) {
            const btnText = submitBtn.querySelector('.btn-text');
            const btnLoading = submitBtn.querySelector('.btn-loading');
            btnText.style.display = loading ? 'none' : 'inline';
            btnLoading.style.display = loading ? 'inline' : 'none';
            submitBtn.disabled = loading;
        }

        function setError(message) {
            if (message) {
                errorBanner.textContent = message;
                errorBanner.style.display = 'block';
            } else {
                errorBanner.style.display = 'none';
                errorBanner.textContent = '';
            }
        }

        function clearFieldErrors() {
            REQUIRED_FIELDS.forEach(function (field) {
                const input = document.getElementById(field);
                const err = document.getElementById('error-' + field);
                if (input) input.classList.remove('input-error');
                if (err) err.textContent = '';
            });
        }

        function validate() {
            clearFieldErrors();
            let valid = true;
            REQUIRED_FIELDS.forEach(function (field) {
                const input = document.getElementById(field);
                const err = document.getElementById('error-' + field);
                if (input && !input.value.trim()) {
                    input.classList.add('input-error');
                    if (err) err.textContent = 'Kolom ini wajib diisi.';
                    valid = false;
                }
            });
            return valid;
        }

        function collectFormData() {
            const data = {};
            const formData = new FormData(form);
            formData.forEach(function (value, key) {
                data[key] = value;
            });
            return data;
        }

        function copyText(text, btn, successText) {
            if (!navigator.clipboard) {
                alert('Clipboard tidak didukung di browser ini. Salin manual.');
                return;
            }
            navigator.clipboard.writeText(text).then(function () {
                const original = btn.textContent;
                btn.textContent = successText || '✅ Tersalin!';
                setTimeout(function () { btn.textContent = original; }, 2000);
            }).catch(function (err) {
                alert('Gagal menyalin: ' + err.message);
            });
        }

        function createSectionCard(name, content) {
            const card = document.createElement('div');
            card.className = 'output-card';

            const header = document.createElement('div');
            header.className = 'output-card-header';

            const title = document.createElement('h3');
            title.textContent = name;

            const copyBtn = document.createElement('button');
            copyBtn.className = 'btn-copy';
            copyBtn.textContent = '📋 Salin';
            copyBtn.addEventListener('click', function () {
                copyText(content, copyBtn, '✅ Tersalin!');
            });

            header.appendChild(title);
            header.appendChild(copyBtn);
            card.appendChild(header);

            const pre = document.createElement('pre');
            pre.className = 'output-pre';
            pre.textContent = content;
            card.appendChild(pre);

            return card;
        }

        function renderSections(sections) {
            outputContainer.innerHTML = '';
            Object.keys(sections).forEach(function (name) {
                outputContainer.appendChild(createSectionCard(name, sections[name]));
            });
        }

        function saveToHistory(data, sections, demoMode, model) {
            let history = [];
            try {
                history = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
            } catch (e) {
                history = [];
            }
            const entry = {
                timestamp: new Date().toISOString(),
                programName: data.programName || '',
                demoMode: !!demoMode,
                model: model || '',
                sections: sections,
            };
            history.unshift(entry);
            if (history.length > 10) history = history.slice(0, 10);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
        }

        function loadHistory() {
            let history = [];
            try {
                history = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
            } catch (e) {
                history = [];
            }

            if (!history.length) {
                historySection.style.display = 'none';
                historyContainer.innerHTML = '';
                return;
            }

            historySection.style.display = 'block';
            historyContainer.innerHTML = '';

            history.forEach(function (entry, index) {
                const card = document.createElement('div');
                card.className = 'history-item';

                const title = document.createElement('div');
                title.className = 'history-item-header';

                const name = document.createElement('strong');
                name.textContent = entry.programName || 'Tanpa nama program';

                const meta = document.createElement('span');
                meta.className = 'history-meta';
                meta.textContent = entry.demoMode ? ' (demo)' : '';

                title.appendChild(name);
                title.appendChild(meta);
                card.appendChild(title);

                const actions = document.createElement('div');
                actions.className = 'history-actions';

                const viewBtn = document.createElement('button');
                viewBtn.className = 'btn-secondary btn-sm';
                viewBtn.textContent = '👁️ Lihat';
                viewBtn.addEventListener('click', function () {
                    renderSections(entry.sections);
                    setError(null);
                    outputSection.style.display = 'block';
                    outputSection.scrollIntoView({ behavior: 'smooth' });
                });

                const loadBtn = document.createElement('button');
                loadBtn.className = 'btn-secondary btn-sm';
                loadBtn.textContent = '↩️ Isi Ulang Form';
                loadBtn.addEventListener('click', function () {
                    form.reset();
                    Object.keys(entry.sections || {}).forEach(function () {});
                    outputSection.style.display = 'none';
                    setError(null);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                });

                const delBtn = document.createElement('button');
                delBtn.className = 'btn-secondary btn-sm btn-danger-text';
                delBtn.textContent = '🗑️ Hapus';
                delBtn.addEventListener('click', function () {
                    history.splice(index, 1);
                    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
                    loadHistory();
                });

                actions.appendChild(viewBtn);
                actions.appendChild(loadBtn);
                actions.appendChild(delBtn);
                card.appendChild(actions);

                historyContainer.appendChild(card);
            });
        }

        function checkStatus() {
            fetch('/api/status')
                .then(function (res) { return res.json(); })
                .then(function (data) {
                    if (data.demo_mode) {
                        demoBanner.style.display = 'block';
                    } else {
                        demoBanner.style.display = 'none';
                    }
                })
                .catch(function () {
                    demoBanner.style.display = 'none';
                });
        }

        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            setError(null);

            if (!validate()) {
                return;
            }

            const data = collectFormData();
            setLoading(true);

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                });

                const result = await response.json();

                if (!response.ok || !result.success) {
                    const message = result.fields
                        ? result.fields.join('\n')
                        : (result.error || 'Terjadi kesalahan tidak diketahui.');
                    setError('⚠️ ' + message);
                    outputSection.style.display = 'block';
                    outputContainer.innerHTML = '';
                    return;
                }

                renderSections(result.sections || {});
                saveToHistory(data, result.sections || {}, result.demo_mode, result.model);
                loadHistory();
                outputSection.style.display = 'block';
                outputSection.scrollIntoView({ behavior: 'smooth' });
            } catch (err) {
                setError('⚠️ ERROR KONEKSI: ' + err.message + '\nPastikan server sedang berjalan dan terhubung.');
                outputSection.style.display = 'block';
                outputContainer.innerHTML = '';
            } finally {
                setLoading(false);
            }
        });

        if (copyAllBtn) {
            copyAllBtn.addEventListener('click', function () {
                const text = Array.prototype.map.call(
                    outputContainer.querySelectorAll('.output-pre'),
                    function (pre) { return pre.textContent; }
                ).join('\n\n---\n\n');
                copyText(text, copyAllBtn, '✅ Semua tersalin!');
            });
        }

        if (resetBtn) {
            resetBtn.addEventListener('click', function () {
                form.reset();
                clearFieldErrors();
                outputSection.style.display = 'none';
                outputContainer.innerHTML = '';
                setError(null);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }

        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', function () {
                localStorage.removeItem(STORAGE_KEY);
                loadHistory();
            });
        }

        checkStatus();
        loadHistory();
    });
})();
