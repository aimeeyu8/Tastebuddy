// ⚠️ For local testing ONLY. Do NOT commit a real key to GitHub.
const OPENAI_API_KEY = "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";

const chatWindow = document.getElementById("chat-window");
const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const userIdInput = document.getElementById("user-id");

// We'll store the conversation so TasteBuddy has memory
let messages = [
  {
    role: "system",
    content: `
You are TasteBuddy, a friendly restaurant assistant for group chats in New York City.

- You read users' messages and infer cuisines, budget, allergies, and preferences.
- You suggest 3–5 restaurant ideas in NYC tailored to the group.
- If multiple people talk, refer to them by their names ("Kelly", "Cassidy", etc.) if mentioned.
- Be concise and clear. Use bullet points when listing restaurants.
- If the user has allergies, avoid those foods and mention that you're keeping them safe.
`,
  },
];

function addMessage(text, who = "agent") {
  const div = document.createElement("div");
  div.className = `message ${who}`;
  div.textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function callOpenAI(userMessage, userName) {
  // push user message into conversation history
  const namePrefix = userName ? `${userName}: ` : "";
  messages.push({
    role: "user",
    content: namePrefix + userMessage,
  });

  try {
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: messages,
        temperature: 0.5,
      }),
    });

    if (!response.ok) {
        const text = await response.text();
        console.error("OpenAI raw error response:", text);
      
        let errorMessage = response.statusText || "Unknown error";
        try {
          const parsed = JSON.parse(text);
          if (parsed.error && parsed.error.message) {
            errorMessage = parsed.error.message;
          } else {
            errorMessage = text;
          }
        } catch (e) {
          // not JSON, just use raw text
          errorMessage = text;
        }
      
        addMessage("TasteBuddy error: " + errorMessage, "agent");
        return;
      }      

    const data = await response.json();
    const reply = data.choices[0].message.content;

    // Add assistant reply to history
    messages.push({
      role: "assistant",
      content: reply,
    });

    addMessage(reply, "agent");
  } catch (e) {
    console.error(e);
    addMessage("Network error: " + e.message, "agent");
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  const userName = userIdInput.value.trim();

  // Show user's message on screen
  addMessage((userName || "You") + ": " + text, "user");
  input.value = "";

  // Call OpenAI
  await callOpenAI(text, userName);
});
