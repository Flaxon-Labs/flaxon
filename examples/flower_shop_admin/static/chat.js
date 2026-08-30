(() => {
  const room = "shop-floor";
  const user = new URLSearchParams(location.search).get("user") || "guest";
  const list = document.querySelector("#messages");
  const status = document.querySelector("#status");
  const input = document.querySelector("#message");
  const add = (message) => {
    const row = document.createElement("div"); row.className = "message";
    const name = document.createElement("b"); name.textContent = `${message.user}: `;
    row.append(name, document.createTextNode(message.text)); list.append(row); list.scrollTop = list.scrollHeight;
  };
  const socket = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/chat/${room}?user=${encodeURIComponent(user)}`);
  socket.onopen = () => { status.textContent = `Connected as ${user}`; };
  socket.onclose = () => { status.textContent = "Disconnected"; };
  socket.onmessage = (event) => { const data = JSON.parse(event.data); if (data.messages) data.messages.forEach(add); if (data.message) add(data.message); };
  document.querySelector("#chat-form").addEventListener("submit", (event) => { event.preventDefault(); const text = input.value.trim(); if (text && socket.readyState === WebSocket.OPEN) { socket.send(JSON.stringify({type: "message.send", text})); input.value = ""; } });
})();
