(() => {
  const state = document.querySelector('#connection-state');
  const messages = document.querySelector('#messages');
  const form = document.querySelector('#composer');
  const input = document.querySelector('#message');
  const typing = document.querySelector('#typing');
  const username = new URLSearchParams(location.search).get('user') || 'Guest';
  document.querySelector('#user-label').textContent = username;
  const path = `${window.FLAXON_CHAT.websocketPath}?user=${encodeURIComponent(username)}`;
  let socket;
  let reconnectTimer;
  function render(event) {
    if (event.type === 'session.ready') { event.history.forEach(render); return; }
    if (event.type === 'typing') { typing.textContent = `${event.user} is typing...`; setTimeout(() => { typing.textContent = ''; }, 1200); return; }
    if (event.type.startsWith('presence.')) { document.querySelector('#room-status').textContent = event.type === 'presence.joined' ? `${event.user} joined` : 'Room online'; return; }
    if (event.type !== 'message.created') return;
    const node = document.createElement('article'); node.className = `message${event.user === username ? ' mine' : ''}`;
    const author = document.createElement('small'); author.textContent = event.user;
    const text = document.createElement('div'); text.textContent = event.text;
    node.append(author, text); messages.append(node); messages.scrollTop = messages.scrollHeight;
  }
  function connect() {
    socket = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}${path}`);
    socket.onopen = () => { state.textContent = 'Connected'; document.querySelector('#room-status').textContent = 'Online'; };
    socket.onmessage = event => render(JSON.parse(event.data));
    socket.onclose = () => { state.textContent = 'Reconnecting...'; clearTimeout(reconnectTimer); reconnectTimer = setTimeout(connect, 1500); };
  }
  form.addEventListener('submit', event => { event.preventDefault(); const text = input.value.trim(); if (text && socket.readyState === WebSocket.OPEN) { socket.send(JSON.stringify({type:'message.send', text})); input.value = ''; } });
  input.addEventListener('input', () => { if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({type:'typing'})); });
  connect();
})();
