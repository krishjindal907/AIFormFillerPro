document.addEventListener('DOMContentLoaded', () => {

    /* --- THEME TOGGLE --- */
    const themeToggles = document.querySelectorAll('#theme-toggle, #mobile-theme-toggle');
    const storedTheme = localStorage.getItem('theme') || 'light';
    if(storedTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        themeToggles.forEach(t => {
            const i = t.querySelector('i');
            if(i) i.className = 'fa-solid fa-sun';
        });
    }
    
    themeToggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            let currentTheme = document.documentElement.getAttribute('data-theme');
            let newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            themeToggles.forEach(t => {
                const icon = t.querySelector('i');
                if(icon) {
                    icon.className = newTheme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
                }
            });
        });
    });

    /* --- FLASH MESSAGES --- */
    const flashes = document.querySelectorAll('.flash');
    if (flashes.length > 0) {
        setTimeout(() => {
            flashes.forEach(flash => {
                flash.style.opacity = '0';
                flash.style.transform = 'translateY(-10px)';
                flash.style.transition = 'all 0.5s ease';
                setTimeout(() => flash.remove(), 500);
            });
        }, 5000);
    }

    /* --- V4 FORM ANALYZER LOGIC - LIVE IFRAME --- */
    const analyzeForm = document.getElementById('analyze-form');
    const tabUrl = document.getElementById('tab-url');
    const tabHtml = document.getElementById('tab-html');
    const urlGroup = document.getElementById('url-group');
    const htmlGroup = document.getElementById('html-group');
    
    if(tabUrl && tabHtml) {
        tabUrl.addEventListener('click', (e) => {
            e.preventDefault();
            tabUrl.style.borderBottomColor = 'var(--primary)';
            tabHtml.style.borderBottomColor = 'transparent';
            urlGroup.style.display = 'block';
            htmlGroup.style.display = 'none';
        });
        tabHtml.addEventListener('click', (e) => {
            e.preventDefault();
            tabHtml.style.borderBottomColor = 'var(--primary)';
            tabUrl.style.borderBottomColor = 'transparent';
            htmlGroup.style.display = 'block';
            urlGroup.style.display = 'none';
        });
    }
    
    let currentAnalysisId = null;

    if(analyzeForm) {
        analyzeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = analyzeForm.querySelector('button');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';
            btn.disabled = true;
            
            const formData = new FormData();
            const isUrl = urlGroup.style.display !== 'none';
            if(isUrl) {
                formData.append('url', document.getElementById('form_url').value);
            } else {
                formData.append('html_content', document.getElementById('form_html').value);
            }
            
            try {
                const res = await fetch('/api/fetch_form', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                
                if(data.status === 'success') {
                    document.getElementById('form-input-section').style.display = 'none';
                    document.getElementById('form-render-section').style.display = 'block';
                    
                    document.getElementById('stat-detected').innerText = data.metrics.total;
                    document.getElementById('stat-matched').innerText = data.metrics.matched;
                    currentAnalysisId = data.analysis_id;
                    
                    window.currentFormFields = data.fields;
                    
                    const iframe = document.getElementById('target-iframe');
                    const loader = document.getElementById('iframe-loader');
                    
                    loader.style.display = 'block';
                    iframe.style.display = 'none';
                    document.getElementById('submit-wrapper').style.display = 'none';
                    
                    if(isUrl) {
                        const targetUrl = document.getElementById('form_url').value;
                        if (targetUrl.includes('docs.google.com/forms')) {
                            // Direct load + Instant Auto-Fill prepopulation for Google Forms
                            let baseUrl = targetUrl.split('?')[0];
                            let queryParams = ['usp=pp_url'];
                            data.fields.forEach(f => {
                                if(f.match_key && f.prefill_value && f.name.startsWith('entry.')) {
                                    queryParams.push(`${f.name}=${encodeURIComponent(f.prefill_value)}`);
                                }
                            });
                            iframe.src = baseUrl + '?' + queryParams.join('&');
                            
                            // Mark button as done visually since we pre-filled instantly
                            const autoBtn = document.getElementById('master-autofill-btn');
                            if (autoBtn) {
                                autoBtn.innerHTML = '<i class="fa-solid fa-check"></i> Applied Magic';
                                autoBtn.style.background = 'var(--success)';
                                autoBtn.disabled = true;
                            }
                        } else {
                            iframe.src = '/proxy?url=' + encodeURIComponent(targetUrl);
                        }
                    } else {
                        iframe.srcdoc = document.getElementById('form_html').value;
                    }
                    
                    iframe.onload = () => {
                        loader.style.display = 'none';
                        iframe.style.display = 'block';
                        document.getElementById('submit-wrapper').style.display = 'block';
                        
                        // Automatically trigger autofill for generic/proxy HTML forms
                        const autoBtn = document.getElementById('master-autofill-btn');
                        if (autoBtn && !autoBtn.disabled) {
                            setTimeout(() => { autoBtn.click(); }, 300);
                        }
                    };

                } else {
                    alert(data.error || "Failed to analyze form.");
                }
            } catch(err) {
                console.error(err);
                alert("An error occurred during analysis.");
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    const masterAutofillBtn = document.getElementById('master-autofill-btn');

    if(masterAutofillBtn) {
        masterAutofillBtn.addEventListener('click', () => {
            const fields = window.currentFormFields || [];
            const iframe = document.getElementById('target-iframe');
            
            const isUrl = urlGroup.style.display !== 'none';
            const targetUrl = isUrl ? document.getElementById('form_url').value : '';
            const isGoogleForm = targetUrl.includes('docs.google.com/forms');
            
            if(isGoogleForm) {
                // Google Forms URL Pre-population
                let baseUrl = targetUrl.split('?')[0];
                let queryParams = ['usp=pp_url'];
                
                fields.forEach(f => {
                    if(f.match_key && f.prefill_value && f.name.startsWith('entry.')) {
                        queryParams.push(`${f.name}=${encodeURIComponent(f.prefill_value)}`);
                    }
                });
                
                iframe.src = baseUrl + '?' + queryParams.join('&');
                
                masterAutofillBtn.innerHTML = '<i class="fa-solid fa-check"></i> Applied Magic';
                masterAutofillBtn.style.background = 'var(--success)';
                masterAutofillBtn.disabled = true;
                return;
            }
            
            if(!iframe || !iframe.contentDocument) return;
            const iframeDoc = iframe.contentDocument;
            
            let delay = 0;
            fields.forEach(f => {
                if(f.match_key && f.prefill_value) {
                    setTimeout(() => {
                        let el = null;
                        if(f.id) {
                            el = iframeDoc.getElementById(f.id);
                        } else if(f.name) {
                            el = iframeDoc.querySelector(`[name="${f.name}"]`);
                        }
                        
                        if(el) {
                            el.value = f.prefill_value;
                            el.dispatchEvent(new Event('input', {bubbles: true}));
                            el.dispatchEvent(new Event('change', {bubbles: true}));
                            el.style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
                            el.style.border = '2px solid #10b981';
                        }
                    }, delay);
                    delay += 150;
                }
            });
            
            setTimeout(() => {
                masterAutofillBtn.innerHTML = '<i class="fa-solid fa-check"></i> Applied Magic';
                masterAutofillBtn.style.background = 'var(--success)';
                masterAutofillBtn.disabled = true;
            }, delay + 200);
        });
    }

    const resetBtn = document.getElementById('reset-analyzer');
    if(resetBtn) {
        resetBtn.addEventListener('click', () => {
            document.getElementById('form-render-section').style.display = 'none';
            document.getElementById('form-input-section').style.display = 'block';
            document.getElementById('feedback-panel').style.display = 'none';
            document.getElementById('submit-wrapper').style.display = 'none';
            
            const iframe = document.getElementById('target-iframe');
            if(iframe) {
                iframe.src = 'about:blank';
                iframe.srcdoc = '';
            }
            
            if(masterAutofillBtn) {
                masterAutofillBtn.disabled = false;
                masterAutofillBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Auto Fill Form';
                masterAutofillBtn.style.background = 'linear-gradient(45deg, var(--primary), #818cf8)';
            }
        });
    }

    const fakeSubmitBtn = document.getElementById('fake-submit-btn');
    const reviewModal = document.getElementById('review-modal');
    const reviewTableBody = document.getElementById('review-table-body');
    const reviewEditBtn = document.getElementById('review-edit-btn');
    const reviewConfirmBtn = document.getElementById('review-confirm-btn');

    if(fakeSubmitBtn) {
        fakeSubmitBtn.addEventListener('click', () => {
            if(!reviewTableBody) return;
            reviewTableBody.innerHTML = '';
            
            const fields = window.currentFormFields || [];
            const iframe = document.getElementById('target-iframe');
            
            const isUrl = urlGroup.style.display !== 'none';
            const targetUrl = isUrl ? document.getElementById('form_url').value : '';
            const isGoogleForm = targetUrl.includes('docs.google.com/forms');
            
            let iframeDoc = null;
            if(!isGoogleForm && iframe && iframe.contentDocument) {
                iframeDoc = iframe.contentDocument;
            }
            
            fields.forEach(f => {
                let currentVal = f.prefill_value || '';
                
                if(iframeDoc) {
                    let el = null;
                    if(f.id) {
                        el = iframeDoc.getElementById(f.id);
                    } else if(f.name) {
                        el = iframeDoc.querySelector(`[name="${f.name}"]`);
                    }
                    if(el) currentVal = el.value;
                }
                
                const tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid var(--border-color)';
                
                const tdLabel = document.createElement('td');
                tdLabel.style.padding = '0.75rem 0.5rem';
                tdLabel.style.fontWeight = '500';
                tdLabel.innerText = f.label || f.name || 'Field';
                
                const tdValue = document.createElement('td');
                tdValue.style.padding = '0.75rem 0.5rem';
                if (!currentVal || currentVal.trim() === '') {
                    tdValue.innerHTML = '<span style="color: var(--danger); font-size: 0.85rem;"><i class="fa-solid fa-circle-exclamation"></i> Empty</span>';
                } else {
                    tdValue.innerText = currentVal;
                    tdValue.style.color = 'var(--primary)';
                    tdValue.style.fontWeight = '600';
                }
                
                tr.appendChild(tdLabel);
                tr.appendChild(tdValue);
                reviewTableBody.appendChild(tr);
            });
            
            reviewModal.style.display = 'flex';
        });
    }

    if(reviewEditBtn) {
        reviewEditBtn.addEventListener('click', () => {
            reviewModal.style.display = 'none';
        });
    }

    if(reviewConfirmBtn) {
        reviewConfirmBtn.addEventListener('click', () => {
            reviewModal.style.display = 'none';
            const iframe = document.getElementById('target-iframe');
            if(iframe) {
                iframe.style.opacity = '0.5';
                iframe.style.pointerEvents = 'none';
                
                const iframeDoc = iframe.contentDocument;
                if(iframeDoc) {
                    const formEl = iframeDoc.querySelector('form');
                    if(formEl) {
                        try {
                            formEl.submit();
                        } catch(e) {
                            console.warn("Could not programmatically submit iframe form:", e);
                        }
                    }
                }
            }
            document.getElementById('feedback-panel').style.display = 'block';
            if(fakeSubmitBtn) fakeSubmitBtn.disabled = true;
        });
    }

    const feedbackBtns = document.querySelectorAll('.feedback-btn');
    feedbackBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            if (!currentAnalysisId) return;
            const isAccurate = btn.getAttribute('data-val') === 'true';
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
            
            try {
                await fetch('/api/feedback', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        analysis_id: currentAnalysisId,
                        is_accurate: isAccurate
                    })
                });
                document.getElementById('feedback-panel').innerHTML = '<h3 style="color: var(--success);"><i class="fa-solid fa-heart"></i> Thank You!</h3><p>Your feedback helps improve our engine.</p>';
            } catch(e) {
                console.error(e);
            }
        });
    });

});
