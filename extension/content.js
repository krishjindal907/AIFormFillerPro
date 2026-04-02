(async function() {
    console.log("NeoVault AI Form Filler: Content script injected.");

    // ── Helper: React/SPA-safe value setter ──────────────────────────────────
    function setNativeValue(el, value) {
        // Plain HTML inputs
        el.value = value;

        // React synthetic event hack (nativeInputValueSetter)
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        );
        const nativeTextareaSetter = Object.getOwnPropertyDescriptor(
            window.HTMLTextAreaElement.prototype, 'value'
        );

        if (el.tagName === 'TEXTAREA' && nativeTextareaSetter) {
            nativeTextareaSetter.set.call(el, value);
        } else if (nativeInputValueSetter) {
            nativeInputValueSetter.set.call(el, value);
        }

        // Fire all events React/Vue/Angular listen to
        ['input', 'change', 'blur', 'keyup'].forEach(eventName => {
            el.dispatchEvent(new Event(eventName, { bubbles: true }));
        });
    }

    // ── Helper: Select dropdown option ───────────────────────────────────────
    function setSelectValue(el, value) {
        const lower = value.toLowerCase();
        for (let opt of el.options) {
            if (
                opt.value.toLowerCase() === lower ||
                opt.text.toLowerCase().includes(lower) ||
                lower.includes(opt.text.toLowerCase())
            ) {
                el.value = opt.value;
                el.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }
        }
        return false;
    }

    // ── Helper: Get label text for an element ─────────────────────────────────
    function getLabelText(el) {
        // Method 1: <label for="id">
        if (el.id) {
            const label = document.querySelector(`label[for="${el.id}"]`);
            if (label) return label.innerText.trim();
        }
        // Method 2: Parent <label>
        const parentLabel = el.closest('label');
        if (parentLabel) {
            return parentLabel.innerText.replace(el.value || '', '').trim();
        }
        // Method 3: Previous sibling / heading (Google Forms, custom SPAs)
        let prev = el.previousElementSibling;
        while (prev) {
            const tag = prev.tagName;
            if (['LABEL', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'P', 'SPAN', 'DIV'].includes(tag)) {
                const txt = prev.innerText.trim();
                if (txt && txt.length < 200) return txt;
            }
            prev = prev.previousElementSibling;
        }
        // Method 4: aria-label / aria-labelledby
        if (el.getAttribute('aria-label')) return el.getAttribute('aria-label');
        if (el.getAttribute('aria-labelledby')) {
            const ref = document.getElementById(el.getAttribute('aria-labelledby'));
            if (ref) return ref.innerText.trim();
        }
        // Method 5: Parent container text (for Material UI, Ant Design etc.)
        const container = el.closest('[class*="field"], [class*="form-group"], [class*="input-wrapper"], [class*="MuiFormControl"]');
        if (container) {
            const labelEl = container.querySelector('label, [class*="label"], [class*="Label"]');
            if (labelEl) return labelEl.innerText.trim();
        }
        return '';
    }

    // ── Step 1: Scrape all fillable fields ───────────────────────────────────
    const inputs = Array.from(document.querySelectorAll(
        'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"]):not([type="file"]):not([type="image"]), select, textarea'
    )).filter(el => {
        // Invisible elements skip karo
        const style = window.getComputedStyle(el);
        return style.display !== 'none' && style.visibility !== 'hidden' && el.offsetParent !== null;
    });

    if (inputs.length === 0) {
        alert("NeoVault: No fillable fields found on this page.");
        return;
    }

    const fields = inputs.map(el => ({
        tag: el.tagName.toLowerCase(),
        type: el.type || el.tagName.toLowerCase(),
        name: el.name || '',
        id: el.id || '',
        label: getLabelText(el),
        placeholder: el.placeholder || '',
        options: el.tagName === 'SELECT'
            ? Array.from(el.options).map(o => o.text.trim())
            : []
    }));

    // ── Step 2: Loading overlay ───────────────────────────────────────────────
    const loading = document.createElement('div');
    loading.id = '__neovault_loader__';
    loading.innerHTML = `
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:18px;height:18px;border:3px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:__nv_spin__ 0.8s linear infinite;"></div>
            <span>NeoVault AI is analyzing this form...</span>
        </div>
    `;
    loading.style.cssText = `
        position: fixed; top: 20px; right: 20px;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white; padding: 14px 20px; border-radius: 12px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 14px; font-weight: 600; z-index: 2147483647;
        box-shadow: 0 8px 32px rgba(99,102,241,0.4);
        border: 1px solid rgba(255,255,255,0.2);
    `;
    // Spinner animation inject
    const styleTag = document.createElement('style');
    styleTag.textContent = `@keyframes __nv_spin__ { to { transform: rotate(360deg); } }`;
    document.head.appendChild(styleTag);
    document.body.appendChild(loading);

    // ── Step 3: API call to Flask backend ─────────────────────────────────────
    try {
        const res = await fetch("http://127.0.0.1:5000/api/extension/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ url: window.location.href, fields })
        });

        let data;
        try {
            data = await res.json();
        } catch (e) {
            const raw = await res.text();
            throw new Error(`Server returned non-JSON. Make sure you are logged into http://127.0.0.1:5000 first.\n\nRaw response: ${raw.slice(0, 150)}`);
        }

        loading.remove();

        if (data.status === "error") {
            alert("NeoVault Backend Error:\n" + (data.error || JSON.stringify(data)));
            return;
        }

        // ── Step 4: Apply AI mapping to fields ───────────────────────────────
        const ai_mapping = data.ai_mapping || {};
        let filledCount = 0;
        let delay = 0;

        inputs.forEach(el => {
            // Key: name > id > placeholder match karo
            const mappedVal =
                ai_mapping[el.name] ||
                ai_mapping[el.id] ||
                null;

            if (!mappedVal) return;

            setTimeout(() => {
                try {
                    if (el.tagName === 'SELECT') {
                        setSelectValue(el, String(mappedVal));
                    } else if (el.type === 'checkbox') {
                        const val = String(mappedVal).toLowerCase();
                        el.checked = ['true', 'yes', '1', 'on'].includes(val);
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    } else if (el.type === 'radio') {
                        if (el.value.toLowerCase() === String(mappedVal).toLowerCase()) {
                            el.checked = true;
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    } else {
                        setNativeValue(el, String(mappedVal));
                    }

                    // Visual highlight
                    el.style.transition = 'all 0.4s ease';
                    el.style.backgroundColor = 'rgba(16, 185, 129, 0.12)';
                    el.style.border = '2px solid #10b981';
                    el.style.borderRadius = '4px';
                } catch (err) {
                    console.warn('NeoVault: Could not fill field', el, err);
                }
            }, delay);

            delay += 120;
            filledCount++;
        });

        // ── Step 5: Success / failure toast ──────────────────────────────────
        setTimeout(() => {
            const toast = document.createElement('div');
            if (filledCount > 0) {
                toast.innerHTML = `✅ NeoVault filled <strong>${filledCount}</strong> field${filledCount > 1 ? 's' : ''} successfully!`;
                toast.style.cssText = `
                    position:fixed;top:20px;right:20px;
                    background:linear-gradient(135deg,#10b981,#059669);
                    color:#fff;padding:14px 20px;border-radius:12px;
                    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                    font-size:14px;font-weight:600;z-index:2147483647;
                    box-shadow:0 8px 32px rgba(16,185,129,0.35);
                `;
            } else {
                toast.innerHTML = `⚠️ NeoVault: No fields matched your Knowledge Vault.<br><small>Please update your Profile to improve autofill accuracy.</small>`;
                toast.style.cssText = `
                    position:fixed;top:20px;right:20px;
                    background:linear-gradient(135deg,#f59e0b,#d97706);
                    color:#fff;padding:14px 20px;border-radius:12px;
                    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                    font-size:13px;font-weight:600;z-index:2147483647;
                    box-shadow:0 8px 32px rgba(245,158,11,0.35);max-width:300px;
                `;
            }
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 4000);
        }, delay + 200);

    } catch (err) {
        loading.remove();
        alert(
            "❌ NeoVault: Failed to connect to AI Backend.\n\n" +
            "Steps to fix:\n" +
            "1. Open http://127.0.0.1:5000 in a new tab\n" +
            "2. Log in to your NeoVault account\n" +
            "3. Come back and click Autofill again\n\n" +
            "Error: " + err.message
        );
    }
})();
