const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

function addMessage(text, cls) {
  const el = document.createElement("div");
  el.className = `msg ${cls}`;
  el.textContent = text;
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return el;
}

addMessage(
  "Hi! Ask me anything about the database, e.g. \"Which genre has the longest tracks on average?\"",
  "bot"
);

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = inputEl.value.trim();
  if (!question) return;

  addMessage(question, "user");
  inputEl.value = "";
  sendBtn.disabled = true;
  const pending = addMessage("Thinking...", "bot pending");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: question }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Something went wrong.");
    }

    pending.textContent = data.reply;
    pending.classList.remove("pending");
  } catch (err) {
    pending.textContent = `Error: ${err.message}`;
    pending.classList.remove("pending");
    pending.classList.add("error");
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
});
