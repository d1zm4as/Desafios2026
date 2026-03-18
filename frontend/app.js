const qs = (id) => document.getElementById(id);

const dom = {
  baseUrl: qs('baseUrl'),
  jwtToken: qs('jwtToken'),
  tokenHint: qs('tokenHint'),
  statusBar: qs('statusBar'),
  statusText: qs('statusText'),
  apiLog: qs('apiLog'),
  posterTitle: qs('posterTitle'),
  sessionHint: qs('sessionHint'),
  selectedSession: qs('selectedSession'),
  selectedSeat: qs('selectedSeat'),
  movies: qs('movies'),
  sessions: qs('sessions'),
  seats: qs('seats'),
  tickets: qs('tickets'),
  ticketFilter: qs('ticketFilter'),
};

const state = {
  baseUrl: localStorage.getItem('baseUrl') || window.location.origin,
  token: localStorage.getItem('jwtToken') || '',
  selectedMovie: null,
  selectedSession: null,
  selectedSeat: null,
  seats: [],
};

const normalizeBaseUrl = (value) => value.replace(/\/+$/, '');

const setStatus = (message, type = 'info') => {
  dom.statusText.textContent = message;
  dom.statusBar.classList.toggle('error', type === 'error');
};

const logApi = (payload) => {
  dom.apiLog.textContent = JSON.stringify(payload, null, 2);
};

const updateTokenHint = () => {
  if (state.token) {
    dom.tokenHint.textContent = `Autenticado (token ${state.token.slice(0, 8)}...)`;
  } else {
    dom.tokenHint.textContent = 'Nao autenticado';
  }
};

const saveConfig = () => {
  state.baseUrl = normalizeBaseUrl(dom.baseUrl.value.trim() || window.location.origin);
  state.token = dom.jwtToken.value.trim();
  localStorage.setItem('baseUrl', state.baseUrl);
  localStorage.setItem('jwtToken', state.token);
  updateTokenHint();
};

const clearConfig = () => {
  localStorage.removeItem('baseUrl');
  localStorage.removeItem('jwtToken');
  state.baseUrl = window.location.origin;
  state.token = '';
  dom.baseUrl.value = '';
  dom.jwtToken.value = '';
  updateTokenHint();
};

const api = async (path, options = {}) => {
  const headers = { ...(options.headers || {}) };
  const useAuth = options.auth !== false;
  if (useAuth && state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  try {
    const response = await fetch(`${state.baseUrl}${path}`, {
      ...options,
      headers,
    });
    const data = await response.json().catch(() => ({}));
    return { ok: response.ok, status: response.status, data };
  } catch (error) {
    return { ok: false, status: 0, data: { error: error.message || 'Erro de rede' } };
  }
};

const formatDate = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString('pt-BR');
};

const resetUi = () => {
  state.selectedMovie = null;
  state.selectedSession = null;
  state.selectedSeat = null;
  state.seats = [];
  dom.movies.innerHTML = '';
  dom.sessions.innerHTML = '';
  dom.seats.innerHTML = '';
  dom.tickets.innerHTML = '';
  dom.posterTitle.textContent = 'Selecione um filme';
  dom.sessionHint.textContent = 'Nenhum filme selecionado.';
  dom.selectedSession.textContent = '-';
  dom.selectedSeat.textContent = '-';
  dom.apiLog.textContent = 'Nenhuma chamada realizada.';
  setStatus('Estado limpo');
};

const renderMovies = (movies) => {
  dom.movies.innerHTML = '';
  if (!movies || movies.length === 0) {
    dom.movies.innerHTML = '<p class="hint">Nenhum filme encontrado.</p>';
    return;
  }
  movies.forEach((movie) => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <strong>${movie.title}</strong>
      <p>${movie.description || 'Sem descricao.'}</p>
      <p>Duraçao: ${movie.duration_minutes} min</p>
      <div class="card-actions">
        <button class="btn" data-movie-id="${movie.id}">Ver sessoes</button>
      </div>
    `;
    card.querySelector('button').addEventListener('click', () => {
      state.selectedMovie = movie;
      dom.posterTitle.textContent = movie.title;
      dom.sessionHint.textContent = `Filme selecionado: ${movie.title}`;
      loadSessions();
    });
    dom.movies.appendChild(card);
  });
};

const renderSessions = (sessions) => {
  dom.sessions.innerHTML = '';
  if (!sessions || sessions.length === 0) {
    dom.sessions.innerHTML = '<p class="hint">Nenhuma sessao encontrada.</p>';
    return;
  }
  sessions.forEach((session) => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <strong>Sessao ${session.id}</strong>
      <p>${formatDate(session.starts_at)}</p>
      <p>Sala: ${session.auditorium}</p>
      <div class="card-actions">
        <button class="btn" data-session-id="${session.id}">Abrir assentos</button>
      </div>
    `;
    card.querySelector('button').addEventListener('click', () => {
      state.selectedSession = session;
      dom.selectedSession.textContent = `#${session.id} - ${formatDate(session.starts_at)}`;
      state.selectedSeat = null;
      dom.selectedSeat.textContent = '-';
      loadSeats();
    });
    dom.sessions.appendChild(card);
  });
};

const renderSeats = (seats) => {
  dom.seats.innerHTML = '';
  if (!seats || seats.length === 0) {
    dom.seats.innerHTML = '<p class="hint">Sem assentos disponiveis.</p>';
    return;
  }

  const rows = {};
  seats.forEach((seat) => {
    if (!rows[seat.row]) rows[seat.row] = [];
    rows[seat.row].push(seat);
  });

  Object.keys(rows)
    .map((row) => Number(row))
    .sort((a, b) => a - b)
    .forEach((row) => {
      const rowWrap = document.createElement('div');
      rowWrap.className = 'seat-row';
      const label = document.createElement('span');
      label.className = 'row-label';
      label.textContent = `Fila ${row}`;
      rowWrap.appendChild(label);
      rows[row]
        .sort((a, b) => a.number - b.number)
        .forEach((seat) => {
          const btn = document.createElement('button');
          const isSelected = state.selectedSeat && state.selectedSeat.id === seat.id;
          btn.className = `seat ${seat.status}${isSelected ? ' selected' : ''}`;
          btn.textContent = `N${seat.number}`;
          btn.disabled = seat.status !== 'available';
          btn.addEventListener('click', () => {
            state.selectedSeat = seat;
            dom.selectedSeat.textContent = `R${seat.row} N${seat.number} (#${seat.id})`;
            renderSeats(state.seats);
          });
          rowWrap.appendChild(btn);
        });
      dom.seats.appendChild(rowWrap);
    });
};

const renderTickets = (tickets) => {
  dom.tickets.innerHTML = '';
  if (!tickets || tickets.length === 0) {
    dom.tickets.innerHTML = '<p class="hint">Nenhum ingresso encontrado.</p>';
    return;
  }
  tickets.forEach((ticket) => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <strong>${ticket.session.movie_title}</strong>
      <p>Ingresso: ${ticket.code}</p>
      <p>${formatDate(ticket.session.starts_at)}</p>
      <p>Sala ${ticket.session.auditorium} - R${ticket.seat.row} N${ticket.seat.number}</p>
    `;
    dom.tickets.appendChild(card);
  });
};

const loadMovies = async () => {
  saveConfig();
  setStatus('Carregando filmes...');
  const result = await api('/api/movies/', { auth: false });
  logApi(result);
  if (!result.ok) {
    setStatus('Falha ao carregar filmes', 'error');
    return;
  }
  setStatus('Filmes carregados');
  renderMovies(result.data.results || []);
};

const loadSessions = async () => {
  saveConfig();
  if (!state.selectedMovie) {
    setStatus('Selecione um filme primeiro', 'error');
    return;
  }
  setStatus('Carregando sessoes...');
  const result = await api(`/api/movies/${state.selectedMovie.id}/sessions/`, { auth: false });
  logApi(result);
  if (!result.ok) {
    setStatus('Falha ao carregar sessoes', 'error');
    return;
  }
  setStatus('Sessoes carregadas');
  renderSessions(result.data.results || []);
};

const loadSeats = async () => {
  saveConfig();
  if (!state.selectedSession) {
    setStatus('Selecione uma sessao primeiro', 'error');
    return;
  }
  setStatus('Carregando assentos...');
  const result = await api(`/api/sessions/${state.selectedSession.id}/seats/`, { auth: false });
  logApi(result);
  if (!result.ok) {
    setStatus('Falha ao carregar assentos', 'error');
    return;
  }
  setStatus('Assentos carregados');
  state.seats = result.data || [];
  renderSeats(state.seats);
};

const reserveSeat = async () => {
  saveConfig();
  if (!state.selectedSession || !state.selectedSeat) {
    setStatus('Selecione uma sessao e um assento', 'error');
    return;
  }
  if (!state.token) {
    setStatus('Faca login para reservar', 'error');
    return;
  }
  setStatus('Reservando assento...');
  const result = await api(`/api/sessions/${state.selectedSession.id}/reserve/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ seat_id: Number(state.selectedSeat.id) }),
  });
  logApi(result);
  if (!result.ok) {
    setStatus('Nao foi possivel reservar', 'error');
    return;
  }
  setStatus('Assento reservado');
  await loadSeats();
};

const checkoutSeat = async () => {
  saveConfig();
  if (!state.selectedSession || !state.selectedSeat) {
    setStatus('Selecione uma sessao e um assento', 'error');
    return;
  }
  if (!state.token) {
    setStatus('Faca login para finalizar', 'error');
    return;
  }
  setStatus('Finalizando checkout...');
  const result = await api(`/api/sessions/${state.selectedSession.id}/checkout/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ seat_id: Number(state.selectedSeat.id) }),
  });
  logApi(result);
  if (!result.ok) {
    setStatus('Checkout falhou', 'error');
    return;
  }
  setStatus('Checkout concluido');
  await loadSeats();
  await loadTickets();
};

const loadTickets = async () => {
  saveConfig();
  if (!state.token) {
    setStatus('Faca login para ver ingressos', 'error');
    return;
  }
  const status = dom.ticketFilter.value;
  const suffix = status && status !== 'all' ? `?status=${status}` : '';
  setStatus('Carregando ingressos...');
  const result = await api(`/api/me/tickets/${suffix}`);
  logApi(result);
  if (!result.ok) {
    setStatus('Falha ao carregar ingressos', 'error');
    return;
  }
  setStatus('Ingressos carregados');
  renderTickets(result.data.results || []);
};

const testApi = async () => {
  saveConfig();
  setStatus('Testando conexao...');
  const result = await api('/api/movies/', { auth: false });
  logApi(result);
  if (!result.ok) {
    const detail = result.data?.detail || result.data?.error || result.data?.message;
    setStatus(`API indisponivel (${result.status})${detail ? `: ${detail}` : ''}`, 'error');
    return;
  }
  setStatus('API ok');
};

const register = async () => {
  saveConfig();
  const payload = {
    email: qs('regEmail').value,
    username: qs('regUsername').value,
    password: qs('regPassword').value,
  };
  setStatus('Criando usuario...');
  const result = await api('/api/auth/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  logApi(result);
  if (!result.ok) {
    setStatus('Falha no cadastro', 'error');
    return;
  }
  setStatus('Usuario criado');
};

const login = async () => {
  saveConfig();
  const payload = {
    username: qs('loginUsername').value,
    password: qs('loginPassword').value,
  };
  setStatus('Autenticando...');
  const result = await api('/api/auth/token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  logApi(result);
  if (result.ok && result.data.access) {
    state.token = result.data.access;
    dom.jwtToken.value = state.token;
    localStorage.setItem('jwtToken', state.token);
    updateTokenHint();
    setStatus('Login realizado');
    return;
  }
  setStatus('Login falhou', 'error');
};

const init = () => {
  dom.baseUrl.value = state.baseUrl;
  dom.jwtToken.value = state.token;
  updateTokenHint();

  qs('saveConfig').addEventListener('click', saveConfig);
  qs('clearConfig').addEventListener('click', clearConfig);
  qs('loadMovies').addEventListener('click', loadMovies);
  qs('loadSessions').addEventListener('click', loadSessions);
  qs('refreshSeats').addEventListener('click', loadSeats);
  qs('reserveBtn').addEventListener('click', reserveSeat);
  qs('checkoutBtn').addEventListener('click', checkoutSeat);
  qs('loadTickets').addEventListener('click', loadTickets);
  qs('testApi').addEventListener('click', testApi);
  qs('resetUi').addEventListener('click', resetUi);
  qs('registerBtn').addEventListener('click', register);
  qs('loginBtn').addEventListener('click', login);
};

init();
