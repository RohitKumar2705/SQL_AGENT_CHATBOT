const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

function addMessage(text, cls) {
  const el = document.createElement("div");
  el.className = `msg ${cls}`;
  if (cls.includes("bot")) {
    el.innerHTML = renderMarkdown(text);
  } else {
    el.textContent = text;
  }
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return el;
}

function escapeHtml(text) {
  return text.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[character]);
}

function renderMarkdown(markdown) {
  let html = escapeHtml(String(markdown)).replace(/\r\n/g, "\n");
  html = html.replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>");
  html = html.replace(/^### (.+)$/gm, "<h4>$1</h4>");
  html = html.replace(/^## (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^# (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^[-*] (.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  return html.split("\n\n").map((paragraph) => (
    paragraph.startsWith("<h") || paragraph.startsWith("<ul>") || paragraph.startsWith("<pre>")
      ? paragraph
      : `<p>${paragraph.replace(/\n/g, "<br>")}</p>`
  )).join("");
}

addMessage(
  "Ask me about the company task database, for example:\n\n- Show all pending checklist tasks\n- Which employee has the most delegated tasks?\n- List overdue delegations\n- Show checklist completion by department",
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

    const responseText = await response.text();
    let data;
    try {
      data = JSON.parse(responseText);
    } catch {
      throw new Error(
        response.ok
          ? "The server returned an invalid response. Please redeploy the latest version."
          : `Server returned HTTP ${response.status}. Please check the Render logs.`
      );
    }

    if (!response.ok) {
      throw new Error(data.detail || "Something went wrong.");
    }

    pending.innerHTML = renderMarkdown(data.reply);
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
