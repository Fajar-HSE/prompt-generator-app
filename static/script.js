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
        const settingsModal = document.getElementById('settingsModal');
        const settingsBtn = document.getElementById('settingsBtn');
        const settingsForm = document.getElementById('settingsForm');
        const showSettingsFooter = document.getElementById('showSettingsFooter');

        const REQUIRED_FIELDS = ['programName', 'competency', 'targetAudience'];
        const STORAGE_KEY = 'promptGeneratorHistory';
        const SETTINGS_KEY = 'llmSettings';
        const PROVIDER_URLS = {
            'openai': 'https://api.openai.com/v1/chat/completions',
            'anthropic': 'https://api.anthropic.com/v1/messages',
            'google': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
            'openrouter': 'https://openrouter.ai/api/v1/chat/completions',
            'together': 'https://api.together.xyz/v1',
            'groq': 'https://api.groq.com/openai/v1',
            'mistral': 'https://api.mistral.ai/v1',
            'deepseek': 'https://api.deepseek.com/v1',
            'perplexity': 'https://api.perplexity.ai',
            'custom': ''
        };

        const OPENAI_COMPATIBLE_SUFFIXES = [
            '/chat/completions',
            '/completions',
            '/v1/chat/completions',
            '/v1/completions'
        ];

        const VALID_PATHS = [
            '/v1/chat/completions',
            '/v1/completions',
            '/chat/completions',
            '/completions',
            '/v1/messages',
            '/v1/responses',
            '/v1/models',
            '/v1/images/',
            'generateContent'
        ];

        let savedSinceEdit = true;

        function getSettingsFromServer() {
            return fetch('/api/settings')
                .then(res => res.json())
                .catch(() => ({}));
        }

        function updateProviderUrl() {
            const provider = document.getElementById('providerSelect').value;
            const baseUrlInput = document.getElementById('baseUrl');
            const modelInput = document.getElementById('llmModel');

            if (provider !== 'custom' && PROVIDER_URLS[provider]) {
                baseUrlInput.value = PROVIDER_URLS[provider];
                baseUrlInput.readOnly = true;
            } else {
                baseUrlInput.value = '';
                baseUrlInput.readOnly = false;
            }

            // Set default model berdasarkan provider
            const defaultModels = {
                'openai': 'gpt-4o',
                'anthropic': 'claude-3-haiku-20240307',
                'google': 'gemini-pro',
                'openrouter': 'openai/gpt-4o',
                'together': 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo',
                'groq': 'llama-3.1-8b-instant',
                'mistral': 'mistral-large-latest',
                'deepseek': 'deepseek-chat',
                'perplexity': 'sonar',
                'custom': ''
            };
            if (!modelInput.value || modelInput.value === 'gpt-4o') {
                modelInput.value = defaultModels[provider] || '';
            }
        }

        function saveSettingsToServer(settings) {
            return fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            })
                .then(res => res.json())
                .catch(() => ({ success: false }));
        }

        function isValidApiUrl(url) {
            if (!url || url.length < 10) return false;
            try {
                const parsed = new URL(url);
                if (parsed.protocol !== 'https:') return false;
                const pathname = parsed.pathname.toLowerCase();
                
                // Check for complete valid paths
                const hasValidPath = VALID_PATHS.some(path => pathname.endsWith(path));
                if (hasValidPath) return true;
                
                // Check for OpenAI-compatible base URLs (e.g., https://api.b.ai/v1)
                const isOpenAICompatible = OPENAI_COMPATIBLE_SUFFIXES.some(suffix => 
                    pathname === suffix || pathname === suffix.replace('/v1', '')
                );
                if (isOpenAICompatible) return true;
                
                // Accept custom URLs ending with /v1 (common for OpenAI-compatible providers)
                if (pathname.endsWith('/v1') || pathname.endsWith('/v1/')) return true;
                
                return false;
            } catch {
                return false;
            }
        }

        function testConnection() {
            const provider = document.getElementById('providerSelect').value;
            const baseUrl = document.getElementById('baseUrl').value.trim();
            const apiKey = document.getElementById('apiKey').value.trim();
            const model = document.getElementById('llmModel').value.trim();

            if (!baseUrl || !apiKey || !model) {
                showToast('Mohon lengkapi semua field sebelum test koneksi');
                return;
            }

            if (!isValidApiUrl(baseUrl)) {
                const resultEl = document.getElementById('testResult');
                resultEl.textContent = '❌ URL tidak valid. Harap gunakan format lengkap:';
                resultEl.style.color = '#ef4444';
                showToast('URL Base tidak valid!');
                return;
            }

            const resultEl = document.getElementById('testResult');
            resultEl.textContent = '⏳ Testing koneksi...';
            resultEl.style.color = '#666';

            fetch('/api/test-connection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ baseUrl, apiKey, model, provider })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        resultEl.textContent = '✅ Koneksi berhasil!';
                        resultEl.style.color = '#10b981';
                        showToast('Koneksi berhasil!');
                    } else {
                        let msg = data.message || 'Koneksi gagal';
                        // Format error message untuk 403/invalid path
                        if (msg.includes('HTTP node only allows') || msg.includes('allowed paths')) {
                            msg = '❌ URL Base salah. Harap gunakan format lengkap:\n- https://openrouter.ai/api/v1/chat/completions\n- https://api.openai.com/v1/chat/completions';
                        }
                        resultEl.textContent = msg;
                        resultEl.style.color = '#ef4444';
                        showToast('Koneksi gagal');
                    }
                })
                .catch(err => {
                    resultEl.textContent = `❌ Error: ${err.message || 'Unknown error'}`;
                    resultEl.style.color = '#ef4444';
                    showToast('Koneksi gagal: ' + (err.message || 'Unknown error'));
                });
        }
        if (form) {
            form.addEventListener('input', function () { savedSinceEdit = false; });
            form.addEventListener('change', function () { savedSinceEdit = false; });
        }

        const brandColorsInput = document.getElementById('brandColors');
        const brandColorCustom = document.getElementById('brandColorCustom');
        const brandColorSwatches = document.getElementById('brandColorSwatches');
        const clearBrandColorsBtn = document.getElementById('clearBrandColors');

        const BRAND_COLORS = [
            '#1a73e8', '#0a66c2', '#1877f2', '#e1306c',
            '#25d366', '#34a853', '#fbbc04', '#ea4335',
            '#ff6d00', '#6f42c1', '#00897b', '#d4af37',
            '#111111', '#ffffff', '#f1f3f4', '#c0392b'
        ];

        function getSelectedColors() {
            return (brandColorsInput.value || '')
                .split(',')
                .map(function (c) { return c.trim().toLowerCase(); })
                .filter(function (c) { return c.length > 0; });
        }

        function setSelectedColors(colors) {
            const unique = [];
            colors.forEach(function (c) {
                c = c.trim().toLowerCase();
                if (c && unique.indexOf(c) === -1) unique.push(c);
            });
            brandColorsInput.value = unique.join(', ');
            syncSwatches();
        }

        function toggleColor(hex) {
            const current = getSelectedColors();
            const idx = current.indexOf(hex.toLowerCase());
            if (idx === -1) {
                current.push(hex.toLowerCase());
            } else {
                current.splice(idx, 1);
            }
            setSelectedColors(current);
        }

        function syncSwatches() {
            const selected = getSelectedColors();
            const swatches = brandColorSwatches.querySelectorAll('.color-swatch');
            swatches.forEach(function (sw) {
                if (selected.indexOf(sw.dataset.color.toLowerCase()) !== -1) {
                    sw.classList.add('active');
                } else {
                    sw.classList.remove('active');
                }
            });
            if (selected.length) {
                brandColorCustom.value = selected[selected.length - 1];
            }
        }

        function renderSwatches() {
            BRAND_COLORS.forEach(function (hex) {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'color-swatch';
                btn.style.background = hex;
                btn.dataset.color = hex;
                btn.title = hex;
                btn.setAttribute('aria-label', 'Warna ' + hex);
                btn.addEventListener('click', function () { toggleColor(hex); });
                brandColorSwatches.appendChild(btn);
            });
        }

        if (brandColorCustom) {
            brandColorCustom.addEventListener('input', function () {
                const hex = brandColorCustom.value;
                const current = getSelectedColors();
                if (current.indexOf(hex.toLowerCase()) === -1) {
                    current.push(hex.toLowerCase());
                    setSelectedColors(current);
                }
            });
        }

        if (clearBrandColorsBtn) {
            clearBrandColorsBtn.addEventListener('click', function () {
                brandColorsInput.value = '';
                syncSwatches();
            });
        }

        if (brandColorsInput) {
            brandColorsInput.addEventListener('input', syncSwatches);
        }

        renderSwatches();
        syncSwatches();

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

        function showToast(message) {
            let toast = document.getElementById('appToast');
            if (!toast) {
                toast = document.createElement('div');
                toast.id = 'appToast';
                toast.className = 'toast';
                toast.setAttribute('role', 'status');
                toast.setAttribute('aria-live', 'polite');
                document.body.appendChild(toast);
            }
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(function () { toast.classList.remove('show'); }, 2500);
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
                showToast('Clipboard tidak didukung di browser ini. Salin manual.');
                return;
            }
            navigator.clipboard.writeText(text).then(function () {
                const original = btn.textContent;
                btn.textContent = successText || '✅ Tersalin!';
                setTimeout(function () { btn.textContent = original; }, 2000);
            }).catch(function (err) {
                showToast('Gagal menyalin: ' + err.message);
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

        function populateForm(data) {
            form.reset();
            Object.keys(data || {}).forEach(function (key) {
                const input = document.getElementById(key);
                if (input) {
                    input.value = data[key];
                }
            });
            if (brandColorsInput) {
                syncSwatches();
            }
            savedSinceEdit = true;
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
                data: data,
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
                    populateForm(entry.data || {});
                    outputSection.style.display = 'none';
                    setError(null);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                });

                const delBtn = document.createElement('button');
                delBtn.className = 'btn-secondary btn-sm btn-danger-text';
                delBtn.textContent = '🗑️ Hapus';
                delBtn.addEventListener('click', function () {
                    if (!window.confirm('Hapus riwayat ini? Tindakan tidak dapat dibatalkan.')) {
                        return;
                    }
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

            const settings = getSettings();
            if (!settings.apiKey) {
                openSettings();
                return;
            }

            const data = collectFormData();
            setLoading(true);

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': settings.apiKey,
                        'X-API-URL': settings.baseUrl,
                        'X-Model': settings.model,
                    },
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
                savedSinceEdit = true;
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
                if (brandColorsInput) syncSwatches();
                outputSection.style.display = 'none';
                outputContainer.innerHTML = '';
                setError(null);
                savedSinceEdit = true;
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }

        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', function () {
                if (!window.confirm('Hapus semua riwayat generate? Tindakan tidak dapat dibatalkan.')) {
                    return;
                }
                localStorage.removeItem(STORAGE_KEY);
                loadHistory();
            });
        }

        window.addEventListener('beforeunload', function (e) {
            if (!savedSinceEdit) {
                e.preventDefault();
                e.returnValue = '';
                return '';
            }
        });

        function getSettings() {
            try {
                return JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}');
            } catch (e) {
                return {};
            }
        }

        function saveSettings(settings) {
            localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
        }

        function checkSettings() {
            const settings = getSettings();
            if (!settings.apiKey) {
                openSettings();
            }
        }

        function openSettings() {
            const settings = getSettings();
            if (settings.baseUrl) {
                document.getElementById('baseUrl').value = settings.baseUrl;
                // Try to detect provider from URL
                const url = settings.baseUrl.toLowerCase();
                if (url.includes('openai.com')) {
                    document.getElementById('providerSelect').value = 'openai';
                } else if (url.includes('anthropic.com')) {
                    document.getElementById('providerSelect').value = 'anthropic';
                } else if (url.includes('googleapis.com')) {
                    document.getElementById('providerSelect').value = 'google';
                } else if (url.includes('openrouter.ai')) {
                    document.getElementById('providerSelect').value = 'openrouter';
                } else if (url.includes('together.xyz')) {
                    document.getElementById('providerSelect').value = 'together';
                } else if (url.includes('groq.com')) {
                    document.getElementById('providerSelect').value = 'groq';
                } else if (url.includes('mistral.ai')) {
                    document.getElementById('providerSelect').value = 'mistral';
                } else if (url.includes('deepseek.com')) {
                    document.getElementById('providerSelect').value = 'deepseek';
                } else if (url.includes('perplexity.ai')) {
                    document.getElementById('providerSelect').value = 'perplexity';
                } else {
                    document.getElementById('providerSelect').value = 'custom';
                }
            }
            if (settings.model) document.getElementById('llmModel').value = settings.model;
            if (settings.apiKey) document.getElementById('apiKey').value = settings.apiKey;
            settingsModal.style.display = 'flex';
            updateProviderUrl();
        }

        function closeSettings() {
            settingsModal.style.display = 'none';
        }

        if (settingsBtn) {
            settingsBtn.addEventListener('click', openSettings);
        }

        if (showSettingsFooter) {
            showSettingsFooter.addEventListener('click', function(e) {
                e.preventDefault();
                openSettings();
            });
        }

        if (settingsForm) {
            settingsForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const baseUrl = document.getElementById('baseUrl').value.trim();
                const model = document.getElementById('llmModel').value.trim();
                const apiKey = document.getElementById('apiKey').value.trim();
                const provider = document.getElementById('providerSelect').value;

                if (!baseUrl || !model || !apiKey) {
                    alert('Semua field wajib diisi!');
                    return;
                }

                if (!isValidApiUrl(baseUrl)) {
                    alert('URL Base tidak valid! Harap gunakan URL lengkap dengan path seperti:\n- https://api.openai.com/v1/chat/completions\n- https://openrouter.ai/api/v1/chat/completions');
                    return;
                }

                saveSettings({ baseUrl, model, apiKey, provider });
                closeSettings();
                showToast('Pengaturan berhasil disimpan!');
            });
        }

        if (settingsModal) {
            settingsModal.addEventListener('click', function(e) {
                if (e.target === settingsModal) {
                    closeSettings();
                }
            });
        }

        const providerSelect = document.getElementById('providerSelect');
        // Update provider select options with OpenAI-compatible providers
        if (providerSelect) {
            providerSelect.addEventListener('change', updateProviderUrl);
        }

        // Add OpenAI-compatible options to custom provider
        const customOption = document.querySelector('#providerSelect option[value="custom"]');
        if (customOption) {
            customOption.textContent = 'Penyedia kustom (OpenAI-compatible)';
        }

        const testConnectionBtn = document.getElementById('testConnectionBtn');
        if (testConnectionBtn) {
            testConnectionBtn.addEventListener('click', testConnection);
        }

        checkSettings();
        checkStatus();
        loadHistory();
    });
})();
