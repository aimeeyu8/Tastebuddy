const API_URL = "http://127.0.0.1:8000/chat";

const chatBox = document.getElementById("chat-box");
const userField = document.getElementById("user-id");
const messageField = document.getElementById("message");
const sendBtn = document.getElementById("send");
const resetBtn = document.getElementById("reset-btn");

// Events
sendBtn.addEventListener("click", sendMessage);
messageField.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    sendMessage();
  }
});

// reset btn
resetBtn.addEventListener("click", async () => {
  if (!confirm("Are you sure you want to clear all user memory?")) return;

  try {
    const res = await fetch("http://127.0.0.1:8000/reset_memory", {
      method: "POST",
    });

    if (!res.ok) {
      alert("Server error while resetting memory.");
      return;
    }

    chatBox.innerHTML = ""; // Clear frontend chat window
    appendMessage("bot", "🧹 Memory has been reset!");

  } catch (err) {
    alert("Network error: " + err.message);
  }
});

// Add a message to the chat area
function appendMessage(senderClass, html) {
  const div = document.createElement("div");
  div.className = senderClass;
  div.innerHTML = html;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Handle sending message to backend
async function sendMessage() {
  const user = userField.value.trim() || "guest";
  const message = messageField.value.trim();

  if (!message) return;

  // show the user's message
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
      let detail = res.statusText;
      try {
        const err = await res.json();
        if (err.detail) detail = err.detail;
      } catch (_) {}

      updateLastBotMessage({
        reply: `⚠️ Server error: ${detail}`,
        restaurants: []
      });
      return;
    }

    const data = await res.json();

    // Pass full backend response to UI updater
    updateLastBotMessage(data);

  } catch (err) {
    updateLastBotMessage({
      reply: "⚠️ Network error: " + err.message,
      restaurants: []
    });
  }
}

// Update the *last* bot bubble
function updateLastBotMessage(data) {
  const bots = document.getElementsByClassName("bot");
  const last = bots[bots.length - 1];
  if (!last) return;

  let harmony = data.harmony_score ?? null;
  let harmonyBadge = "";

  if (harmony !== null) {
    let color = "#4caf50"; // green
    if (harmony < 0.66) color = "#ff9800"; // orange
    if (harmony < 0.33) color = "#f44336"; // red

    harmonyBadge = `
      <div style="
        background:${color};
        color:white;
        padding:4px 10px;
        width:max-content;
        border-radius:8px;
        font-weight:bold;
        margin-bottom:8px;
      ">
        Harmony Score: ${harmony}
      </div>
    `;
  }

  // base reply text
  let html = harmonyBadge + `<p style="white-space: pre-line;">${data.reply}</p>`;

  // if restaurants exist, show them nicely
  if (data.restaurants && data.restaurants.length > 0) {
    html += `<br><b>Top Recommendations:</b><br>`;
    data.restaurants.forEach((r) => {
      html += `
        <div style="margin-left:12px; margin-bottom:10px;">
          • <b>${r.title}</b><br>
          Rating: ${r.rating ?? "?"} ★<br>
          Price: ${r.price ?? "?"}<br>
          Type: ${r.type ?? ""}<br>
          Address: ${r.address ?? ""}<br>
        </div>
      `;
    });
  }

  last.innerHTML = html;
}
