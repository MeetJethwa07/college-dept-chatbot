const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");

function addMessage(text, sender = "bot") {
    const msg = document.createElement("div");
    msg.classList.add("message", sender);

    const avatar = document.createElement("div");
    avatar.classList.add("avatar");
    avatar.textContent = sender === "user" ? "🧑" : "🤖";

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");
    bubble.innerHTML = text.replace(/\n/g, "<br>");


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

chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    // show user message
    addMessage(text, "user");
    userInput.value = "";

    // temporary typing message
    const typingId = "typing-" + Date.now();
    const typingMsg = document.createElement("div");
    typingMsg.classList.add("message", "bot");
    typingMsg.id = typingId;

    const avatar = document.createElement("div");
    avatar.classList.add("avatar");
    avatar.textContent = "🤖";

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");
    bubble.textContent = "Thinking...";

    typingMsg.appendChild(avatar);
    typingMsg.appendChild(bubble);
    chatWindow.appendChild(typingMsg);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ message: text }),
        });

        const data = await response.json();

        // remove typing message
        typingMsg.remove();

        addMessage(data.reply || "No reply from server.", "bot");
    } catch (err) {
        typingMsg.remove();
        addMessage("Error: could not reach the server.", "bot");
        console.error(err);
    }
});
