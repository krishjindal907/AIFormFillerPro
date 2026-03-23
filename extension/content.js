(async function() {
    console.log("AI Form Filler: Content script injected.");
    
    // 1. Scrape all relevant input fields
    const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), select, textarea'));
    
    if (inputs.length === 0) {
        alert("AI Form Filler: No fillable fields found on this page.");
        return;
    }

    let fields = [];
    inputs.forEach(el => {
        let labelText = "";
        if (el.id) {
            let label = document.querySelector(`label[for="${el.id}"]`);
            if (label) labelText = label.innerText.trim();
        }
        if (!labelText && el.closest('label')) {
            labelText = el.closest('label').innerText.trim();
        }
        if (!labelText && el.previousElementSibling) {
            let heading = el.previousElementSibling;
            if (['H1','H2','H3','H4','H5','H6','DIV','P','SPAN'].includes(heading.tagName) && heading.innerText.length < 150) {
                labelText = heading.innerText.trim();
            }
        }
        fields.push({
            tag: el.tagName.toLowerCase(),
            type: el.type,
            name: el.name || '',
            id: el.id || '',
            label: labelText,
            placeholder: el.placeholder || ''
        });
    });

    // 2. Show loading overlay
    let loading = document.createElement("div");
    loading.innerHTML = "✨ AI is analyzing this form...";
    loading.style.cssText = "position: fixed; top: 20px; right: 20px; background: linear-gradient(45deg, #6366f1, #8b5cf6); color: white; padding: 12px 24px; border-radius: 8px; font-family: sans-serif; font-weight: 600; z-index: 2147483647; box-shadow: 0 4px 15px rgba(0,0,0,0.2);";
    document.body.appendChild(loading);

    // 3. Request API mapping
    try {
        const res = await fetch("http://127.0.0.1:5000/api/extension/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include", // Pulls authentication from the local session!
            body: JSON.stringify({ url: window.location.href, fields: fields })
        });
        
        let data;
        try {
            data = await res.json();
        } catch(e) {
            const raw = await res.text();
            throw new Error(`Server returned non-JSON. Make sure you are logged in to the local app. Raw: ${raw.slice(0,100)}`);
        }
        
        loading.remove();
        
        if (data.status === "error") {
            alert("AI Form Filler Backend Error:\n" + data.error);
            return;
        }

        // 4. Apply mapping cleanly
        let delay = 0;
        let ai_mapping = data.ai_mapping || {};
        let filledCount = 0;
        
        inputs.forEach(el => {
            const mappedVal = ai_mapping[el.name] || ai_mapping[el.id];
            if (mappedVal) {
                setTimeout(() => {
                    el.value = mappedVal;
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                    el.style.backgroundColor = 'rgba(16, 185, 129, 0.15)';
                    el.style.border = '2px solid #10b981';
                    el.style.transition = 'all 0.3s';
                }, delay);
                delay += 100;
                filledCount++;
            }
        });
        
        if(filledCount === 0) {
            alert("AI Form Filler: Form analyzed, but no fields could be confidently matched using your Knowledge Vault.");
        }

    } catch(err) {
        loading.remove();
        alert("Failed to connect to the AI Backend.\nMake sure the Flask server is running at 127.0.0.1:5000 and that you have logged into it at least once to establish a session cookie.\n\nDetails: " + err.message);
    }
})();
