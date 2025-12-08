const API_URL = "http://127.0.0.1:8000/chat";

const chatBox = document.getElementById("chat-box");
const userField = document.getElementById("user-id");
const messageField = document.getElementById("message");
const sendBtn = document.getElementById("send");
const resetBtn = document.getElementById("reset-btn");

// color assignments for users
function getUserColor(name) {
  let key = `color_${name}`;
  let stored = localStorage.getItem(key);
  if (stored) return stored;

  const colors = [
    "#1e90ff", "#ff6b6b", "#6f42c1", "#20c997",
    "#fd7e14", "#0dcaf0", "#198754"
  ];
  const color = colors[Math.floor(Math.random() * colors.length)];
  localStorage.setItem(key, color);
  return color;
}

// user id based session id
let SESSION_USER_ID = localStorage.getItem("tastebuddy_user");
if (!SESSION_USER_ID) {
  SESSION_USER_ID = crypto.randomUUID();
  localStorage.setItem("tastebuddy_user", SESSION_USER_ID);
}

// send join event
async function sendJoinEvent(name) {
  try {
    await fetch("http://127.0.0.1:8000/join", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name })
    });
  } catch (err) {
    console.error("join event failed:", err);
  }
}

userField.addEventListener("change", () => {
  const name = userField.value.trim();
  if (name) sendJoinEvent(name);
});

// buttons
sendBtn.addEventListener("click", sendMessage);

messageField.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    sendMessage();
  }
});

resetBtn.addEventListener("click", async () => {
  if (!confirm("Are you sure you want to clear all memory?")) return;

  try {
    const res = await fetch("http://127.0.0.1:8000/reset_memory", {
      method: "POST",
    });

    if (!res.ok) {
      alert("Server error while resetting memory.");
      return;
    }

    chatBox.innerHTML = "";
    lastRenderedIndex = 0;
    appendMessage("bot", "🧹 Memory has been reset!");

  } catch (err) {
    alert("Network error: " + err.message);
  }
});

//message append
function appendMessage(senderClass, html, msgId = null) {
  // skip if already rendered
  if (msgId && document.querySelector(`[data-msgid="${msgId}"]`)) {
    return;
  }

  const div = document.createElement("div");
  div.className = senderClass;

  if (msgId !== null) div.dataset.msgid = msgId;

  // diff color for diff user messages
  if (senderClass === "user") {
    const nameMatch = html.match(/<b>(.*?):<\/b>/);
    if (nameMatch) {
      const name = nameMatch[1];
      div.style.background = getUserColor(name);
      div.style.color = "white";
    }
  }

  div.innerHTML = html;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}
// main send function
async function sendMessage() {
  const userName = userField.value.trim() || "Guest";
  const message = messageField.value.trim();
  if (!message) return;

  messageField.value = "";

  // Do not append the user's message locally here — the server pushes
  // the user message into the shared history and `fetchGroupHistory`
  // will render it. This avoids showing the same message twice.

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: SESSION_USER_ID,
        user_name: userName,
        message: message,
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      appendMessage("bot", `⚠️ Server error: ${data.detail}`);
      return;
    }

    // Immediately fetch history to render the user's message and bot reply
    // without waiting for the next polling interval.
    fetchGroupHistory();

  } catch (err) {
    appendMessage("bot", "⚠️ Network error: " + err.message);
  }
}
// update bot messaage content
function updateLastBotMessage(data) {
  const bots = document.getElementsByClassName("bot");
  const last = bots[bots.length - 1];
  if (!last) return;

  let harmony = data.harmony_score ?? null;
  let harmonyBadge = "";

  if (harmony !== null) {
    let color = "#4caf50";
    if (harmony < 0.66) color = "#ff9800";
    if (harmony < 0.33) color = "#f44336";

    let mood = harmony < 0.33 ? "😬"
              : harmony < 0.66 ? "🤔"
              : "😊";

    harmonyBadge = `
      <div style="background:${color}; color:white; padding:4px 10px;
        width:max-content; border-radius:8px; font-weight:bold;">
        harmony: ${harmony.toFixed(2)} ${mood}
      </div>
    `;
  }

  let html = harmonyBadge +
    `<p style="white-space: pre-line;">${data.reply}</p>`;

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
        </div>`;
    });

    window.lastRestaurants = data.restaurants;
  }

  last.innerHTML = html;
}

// group history polling
let lastRenderedIndex = 0;

async function fetchGroupHistory() {
  try {
    const res = await fetch("http://127.0.0.1:8000/history");
    const data = await res.json();

    const newMessages = data.slice(lastRenderedIndex);

    newMessages.forEach(msg => {
      if (msg.id && document.querySelector(`[data-msgid="${msg.id}"]`)) {
        return; // skip duplicates
      }

      if (msg.sender === "TasteBuddy") {
        appendMessage("bot", "", msg.id);
        updateLastBotMessage({
          reply: msg.text,
          harmony_score: msg.harmony ?? null,
          restaurants: msg.restaurants ?? []
        });
      } else if (msg.sender === "system") {
        appendMessage("system", `<i>${msg.text}</i>`, msg.id);
      } else {
        appendMessage("user", `<b>${msg.sender}:</b> ${msg.text}`, msg.id);
      }
    });

    lastRenderedIndex = data.length;

  } catch (err) {
    console.error("history fetch error:", err);
  }
}

setInterval(fetchGroupHistory, 2000);
