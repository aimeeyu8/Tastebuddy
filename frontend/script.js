const API_URL = "http://127.0.0.1:8000/chat";

const chatBox = document.getElementById("chat-box");
const userField = document.getElementById("user-id");
const messageField = document.getElementById("message");
const sendBtn = document.getElementById("send");

sendBtn.addEventListener("click", sendMessage);
messageField.addEventListener("keypress", e => {
  if (e.key === "Enter") sendMessage();
});

function appendMessage(sender, text) {
  const div = document.createElement("div");
  div.className = sender;
  div.innerHTML = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const user = userField.value.trim() || "guest";
  const message = messageField.value.trim();
  if (!message) return;

  appendMessage("user", `<b>${user}:</b> ${message}`);
  messageField.value = "";
  appendMessage("bot", "Thinking...");

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: user, message }),
    });
    const data = await res.json();

    const prefs = JSON.stringify(data.preferences);
    const harmony = data.harmony_score;
    const recs = data.recommendations;

    let reply = `<b>Preferences:</b> ${prefs}<br>`;
    reply += `<b>Harmony score:</b> ${harmony}<br><b>Top picks:</b><br>`;

    recs.forEach((r, i) => {
      reply += `${i + 1}. <b>${r.name}</b> (${r.rating}★, ${r.price || "?"}) - ${r.location?.city || ""}<br>`;
    });

    updateLastBotMessage(reply);
  } catch (err) {
    updateLastBotMessage("⚠️ Server error.");
  }
}

function updateLastBotMessage(text) {
  const bots = document.getElementsByClassName("bot");
  const last = bots[bots.length - 1];
  last.innerHTML = text;
}
