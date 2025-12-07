const API_URL = "http://127.0.0.1:8008/chat";

const chatBox = document.getElementById("chat-box");
const userField = document.getElementById("user-id");
const messageField = document.getElementById("message");
const sendBtn = document.getElementById("send");
const resetBtn = document.getElementById("reset-btn");

// user color assignment
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

// unique user per browser session
let SESSION_USER_ID = localStorage.getItem("tastebuddy_user");
if (!SESSION_USER_ID) {
  SESSION_USER_ID = crypto.randomUUID();
  localStorage.setItem("tastebuddy_user", SESSION_USER_ID);
}

// send real join event to backend
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

// trigger join when name is entered
userField.addEventListener("change", () => {
  const name = userField.value.trim();
  if (name) {
    sendJoinEvent(name);
  }
});

// events
sendBtn.addEventListener("click", sendMessage);
messageField.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    sendMessage();
  }
});

// reset button
resetBtn.addEventListener("click", async () => {
  if (!confirm("are you sure you want to clear all user memory?")) return;

  try {
    const res = await fetch("http://127.0.0.1:8000/reset_memory", {
      method: "POST",
    });

    if (!res.ok) {
      alert("server error while resetting memory.");
      return;
    }

    chatBox.innerHTML = "";
    lastRenderedIndex = 0;
    appendMessage("bot", "🧹 memory has been reset!");

  } catch (err) {
    alert("network error: " + err.message);
  }
});

// add a message to the chat area
function appendMessage(senderClass, html) {
  const div = document.createElement("div");

  if (senderClass === "user") {
    const nameMatch = html.match(/<b>(.*?):<\/b>/);
    if (nameMatch) {
      const name = nameMatch[1];
      div.style.background = getUserColor(name);
      div.style.color = "white";
    }
  }

  div.className = senderClass;
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

    if (!res.ok) {
      let detail = res.statusText;
      try {
        const err = await res.json();
        if (err.detail) detail = err.detail;
      } catch (_) {}

      appendMessage("bot", `⚠️ server error: ${detail}`);
      return;
    }

    const data = await res.json();

    if (!data.reply) return;

    appendMessage("bot", "");
    updateLastBotMessage(data);

  } catch (err) {
    appendMessage("bot", "⚠️ network error: " + err.message);
  }
}

// update bot ui
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

    let mood = "😊";
    if (harmony < 0.33) mood = "😬";
    else if (harmony < 0.66) mood = "🤔";

    harmonyBadge = `
      <div style="background:${color}; color:white; padding:4px 10px;
        width:max-content; border-radius:8px; font-weight:bold;">
        harmony: ${harmony.toFixed(2)} ${mood}
      </div>
    `;
  }

  let html = harmonyBadge + `
    <p style="white-space: pre-line;">${data.reply}</p>
  `;

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

// pdf export
document.getElementById("pdf-btn")?.addEventListener("click", async () => {
  if (!window.lastRestaurants || window.lastRestaurants.length === 0) {
    alert("ask tastebuddy for recommendations first!");
    return;
  }

  const res = await fetch("http://127.0.0.1:8000/export_pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(window.lastRestaurants),
  });

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "TasteBuddy_Recommendations.pdf";
  a.click();
});

// shared group chat polling
let lastRenderedIndex = 0;

async function fetchGroupHistory() {
  try {
    const res = await fetch("http://127.0.0.1:8000/history");
    const data = await res.json();

    const newMessages = data.slice(lastRenderedIndex);

    newMessages.forEach(msg => {
      if (msg.sender === "TasteBuddy") {
        appendMessage("bot", "");
        updateLastBotMessage({
          reply: msg.text,
          harmony_score: msg.harmony ?? null,
          restaurants: msg.restaurants ?? []
        });
      } else {
        const cls = msg.sender === "system" ? "bot" : "user";
        appendMessage(cls, `<b>${msg.sender}:</b> ${msg.text}`);
      }
    });

    lastRenderedIndex = data.length;

  } catch (err) {
    console.error("history fetch error:", err);
  }
}

// poll every 2 seconds
setInterval(fetchGroupHistory, 2000);
