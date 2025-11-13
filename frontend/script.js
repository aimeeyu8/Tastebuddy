const API_URL = "http://127.0.0.1:8000/chat";

const chatBox = document.getElementById("chat-box");
const userField = document.getElementById("user-id");
const messageField = document.getElementById("message");
const sendBtn = document.getElementById("send");

sendBtn.addEventListener("click", sendMessage);
messageField.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    e.preventDefault(); // so it doesn't submit a form/reload
    sendMessage();
  }
});

function appendMessage(senderClass, html) {
  const div = document.createElement("div");
  div.className = senderClass;
  div.innerHTML = html;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const user = userField.value.trim() || "guest";
  const message = messageField.value.trim();
  if (!message) return;

  // show user message
  appendMessage("user", `<b>${user}:</b> ${message}`);
  messageField.value = "";

  // placeholder bot message
  appendMessage("bot", "Thinking...");

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: user, message }),
    });

    if (!res.ok) {
      // try to pull error detail from backend
      let detail = res.statusText;
      try {
        const err = await res.json();
        if (err.detail) detail = err.detail;
      } catch (_) {}
      updateLastBotMessage(`⚠️ Server error: ${detail}`);
      return;
    }

    const data = await res.json();
    // backend returns: { reply: "..." }
    updateLastBotMessage(data.reply || "⚠️ No reply from server.");
  } catch (err) {
    updateLastBotMessage("⚠️ Network error: " + err.message);
  }
}

function updateLastBotMessage(text) {
  const bots = document.getElementsByClassName("bot");
  const last = bots[bots.length - 1];
  if (last) {
    last.innerHTML = text;
  }
}
