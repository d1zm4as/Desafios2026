const qs = (id) => document.getElementById(id);

const state = {
  baseUrl: localStorage.getItem('baseUrl') || window.location.origin,
  token: localStorage.getItem('jwtToken') || '',
};

const saveConfig = () => {
  state.baseUrl = qs('baseUrl').value.trim();
  state.token = qs('jwtToken').value.trim();
  localStorage.setItem('baseUrl', state.baseUrl);
  localStorage.setItem('jwtToken', state.token);
};

const clearConfig = () => {
  localStorage.removeItem('baseUrl');
  localStorage.removeItem('jwtToken');
  qs('baseUrl').value = '';
  qs('jwtToken').value = '';
};

const api = async (path, options = {}) => {
  const headers = options.headers || {};
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  const response = await fetch(`${state.baseUrl}${path}`, {
    ...options,
    headers,
  });
  const data = await response.json().catch(() => ({}));
  return { ok: response.ok, status: response.status, data };
};

const renderList = (target, items, formatter) => {
  const root = qs(target);
  root.innerHTML = '';
  if (!items || items.length === 0) {
    root.innerHTML = '<div class="item">Sem dados.</div>';
    return;
  }
  items.forEach((item) => {
    const div = document.createElement('div');
    div.className = 'item';
    div.innerHTML = formatter(item);
    root.appendChild(div);
  });
};

qs('baseUrl').value = state.baseUrl;
qs('jwtToken').value = state.token;

qs('saveConfig').addEventListener('click', saveConfig);
qs('clearConfig').addEventListener('click', clearConfig);

qs('registerBtn').addEventListener('click', async () => {
  saveConfig();
  const payload = {
    email: qs('regEmail').value,
    username: qs('regUsername').value,
    password: qs('regPassword').value,
  };
  const result = await api('/api/auth/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  qs('registerOut').textContent = JSON.stringify(result, null, 2);
});

qs('loginBtn').addEventListener('click', async () => {
  saveConfig();
  const payload = {
    username: qs('loginUsername').value,
    password: qs('loginPassword').value,
  };
  const result = await api('/api/auth/token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (result.ok && result.data.access) {
    state.token = result.data.access;
    qs('jwtToken').value = state.token;
    localStorage.setItem('jwtToken', state.token);
  }
  qs('loginOut').textContent = JSON.stringify(result, null, 2);
});

qs('loadMovies').addEventListener('click', async () => {
  saveConfig();
  const result = await api('/api/movies/');
  renderList('movies', result.data.results || [], (movie) => {
    return `<strong>${movie.title}</strong><div>${movie.description || ''}</div><div>Duração: ${movie.duration_minutes} min</div>`;
  });
});

qs('loadSessions').addEventListener('click', async () => {
  saveConfig();
  const movieId = qs('movieId').value;
  if (!movieId) return;
  const result = await api(`/api/movies/${movieId}/sessions/`);
  renderList('sessions', result.data.results || [], (session) => {
    return `<strong>Sessão ${session.id}</strong><div>${session.starts_at}</div><div>Sala: ${session.auditorium}</div>`;
  });
});

qs('loadSeats').addEventListener('click', async () => {
  saveConfig();
  const sessionId = qs('sessionId').value;
  if (!sessionId) return;
  const result = await api(`/api/sessions/${sessionId}/seats/`);
  const root = qs('seats');
  root.innerHTML = '';
  (result.data || []).forEach((seat) => {
    const div = document.createElement('div');
    div.className = `seat ${seat.status}`;
    div.textContent = `#${seat.id} R${seat.row} N${seat.number} ${seat.status}`;
    root.appendChild(div);
  });
});

qs('reserveBtn').addEventListener('click', async () => {
  saveConfig();
  const sessionId = qs('actionSessionId').value;
  const seatId = qs('actionSeatId').value;
  if (!sessionId || !seatId) return;
  const result = await api(`/api/sessions/${sessionId}/reserve/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ seat_id: Number(seatId) }),
  });
  qs('actionOut').textContent = JSON.stringify(result, null, 2);
});

qs('checkoutBtn').addEventListener('click', async () => {
  saveConfig();
  const sessionId = qs('actionSessionId').value;
  const seatId = qs('actionSeatId').value;
  if (!sessionId || !seatId) return;
  const result = await api(`/api/sessions/${sessionId}/checkout/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ seat_id: Number(seatId) }),
  });
  qs('actionOut').textContent = JSON.stringify(result, null, 2);
});

qs('loadTickets').addEventListener('click', async () => {
  saveConfig();
  const result = await api('/api/me/tickets/');
  renderList('tickets', result.data.results || [], (ticket) => {
    return `<strong>${ticket.code}</strong><div>${ticket.session.movie_title}</div><div>${ticket.session.starts_at}</div><div>Assento: R${ticket.seat.row} N${ticket.seat.number}</div>`;
  });
});
