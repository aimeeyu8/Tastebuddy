// ⚠️ For local testing ONLY. Do NOT commit real keys.
const chatWindow = document.getElementById("chat-window");
const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const userIdInput = document.getElementById("user-id");

// ✅ Each browser gets a permanent unique user_id
let SESSION_USER_ID = localStorage.getItem("tastebuddy_user");
if (!SESSION_USER_ID) {
  SESSION_USER_ID = crypto.randomUUID();
  localStorage.setItem("tastebuddy_user", SESSION_USER_ID);
}

function addMessage(text, who = "agent") {
  const div = document.createElement("div");
  div.className = `message ${who}`;
  div.textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage(text, userName) {
  const res = await fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: SESSION_USER_ID,
      user_name: userName || "Anonymous",
      message: text
    })
  });

  const data = await res.json();

  // MUCA can stay silent
  if (data.reply) {
    addMessage("TasteBuddy: " + data.reply, "agent");
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  const userName = userIdInput.value.trim() || "Anonymous";

  addMessage(userName + ": " + text, "user");
  input.value = "";

  await sendMessage(text, userName);
});

