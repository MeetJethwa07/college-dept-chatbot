const chatWindow = document.getElementById("chat-window");
const chatForm   = document.getElementById("chat-form");
const userInput  = document.getElementById("user-input");

// ── Markdown parser ──────────────────────────────────────────────────────────
function parseMarkdown(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g,     '<em>$1</em>')
        .replace(/^- (.+)/gm,      '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/gs,'<ul>$1</ul>')
        .replace(/\n/g,            '<br>');
}

// ── Add message bubble ───────────────────────────────────────────────────────
function addMessage(text, sender = "bot") {
    const msg    = document.createElement("div");
    msg.classList.add("message", sender);

    const avatar = document.createElement("div");
    avatar.classList.add("avatar");
    avatar.textContent = sender === "user" ? "🧑" : "🤖";

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");
    bubble.innerHTML = sender === "bot" ? parseMarkdown(text) : text;

    if (sender === "user") {
        msg.appendChild(bubble);
        msg.appendChild(avatar);
    } else {
        msg.appendChild(avatar);
        msg.appendChild(bubble);
    }

    chatWindow.appendChild(msg);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ── Source links pill (clickable toggle) ────────────────────────────────────
function buildSourcesUI(sources) {
    if (!sources || sources.length === 0) return null;

    // Wrapper
    const wrapper = document.createElement("div");
    wrapper.classList.add("sources-wrapper");

    // Pill button
    const pill = document.createElement("button");
    pill.classList.add("sources-pill");
    pill.innerHTML = `🔗 <span>${sources.length} Source${sources.length > 1 ? "s" : ""}</span>`;

    // Dropdown panel
    const panel = document.createElement("div");
    panel.classList.add("sources-panel");
    panel.style.display = "none";

    sources.forEach((url, i) => {
        const slug  = url.replace(/\/$/, "").split("/").pop();
        const label = slug
            ? slug.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase())
            : `Source ${i + 1}`;

        const link = document.createElement("a");
        link.href        = url;
        link.target      = "_blank";
        link.rel         = "noopener noreferrer";
        link.textContent = `↗ ${label}`;
        link.classList.add("source-link-item");

        panel.appendChild(link);
    });

    // Toggle on click
    pill.addEventListener("click", () => {
        const isOpen = panel.style.display === "block";
        panel.style.display = isOpen ? "none" : "block";
        pill.classList.toggle("active", !isOpen);
    });

    wrapper.appendChild(pill);
    wrapper.appendChild(panel);
    return wrapper;
}

// ── Submit handler ───────────────────────────────────────────────────────────
chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    addMessage(text, "user");
    userInput.value = "";

    // Typing indicator
    const typingEl = document.createElement("div");
    typingEl.classList.add("message", "bot");

    const tAvatar = document.createElement("div");
    tAvatar.classList.add("avatar");
    tAvatar.textContent = "🤖";

    const tBubble = document.createElement("div");
    tBubble.classList.add("bubble", "typing");
    tBubble.innerHTML = '<span></span><span></span><span></span>';

    typingEl.appendChild(tAvatar);
    typingEl.appendChild(tBubble);
    chatWindow.appendChild(typingEl);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const response = await fetch("/chat", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ message: text }),
        });

        const data = await response.json();
        typingEl.remove();

        // Separate reply text from source HTML (sent by backend)
        // We now handle sources purely in JS — strip any old source HTML
        let replyText = (data.reply || "No reply from server.")
            .replace(/<div class="sources-box">[\s\S]*?<\/div>/g, "")
            .trim();

        // Build bot message
        const msg    = document.createElement("div");
        msg.classList.add("message", "bot");

        const avatar = document.createElement("div");
        avatar.classList.add("avatar");
        avatar.textContent = "🤖";

        const bubble = document.createElement("div");
        bubble.classList.add("bubble");
        bubble.innerHTML = parseMarkdown(replyText);

        msg.appendChild(avatar);
        msg.appendChild(bubble);

        // Attach sources pill if sources came back
        if (data.sources && data.sources.length > 0) {
            const sourcesUI = buildSourcesUI(data.sources);
            if (sourcesUI) bubble.appendChild(sourcesUI);
        }

        chatWindow.appendChild(msg);
        chatWindow.scrollTop = chatWindow.scrollHeight;

    } catch (err) {
        typingEl.remove();
        addMessage("⚠️ Error: could not reach the server.", "bot");
        console.error(err);
    }
});