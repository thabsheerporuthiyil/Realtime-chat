/**
 * Real-Time Chat API — WebSocket Test Client
 *
 * Handles authentication (register/login), user listing,
 * WebSocket connection management, and real-time messaging.
 *
 * Modules:
 *   - Config: API/WS base URLs
 *   - Auth: register(), login(), updateAuthStatus()
 *   - Users: fetchUsers()
 *   - WebSocket: connectToUser(), sendMessage(), loadHistory()
 *   - UI: appendMessage(), log()
 */

// =========================================================================
// Config
// =========================================================================
const API_BASE = window.location.origin;
const WS_BASE = `ws://${window.location.host}`;

// =========================================================================
// State
// =========================================================================
let accessToken = null;
let currentUser = null;
let socket = null;
let targetUserId = null;

// =========================================================================
// Debug Logging
// =========================================================================

/**
 * Append a timestamped entry to the debug log panel.
 * @param {string} msg - The message to log.
 */
function log(msg) {
    const el = document.getElementById('log');
    const time = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.textContent = `[${time}] ${msg}`;
    el.appendChild(entry);
    el.scrollTop = el.scrollHeight;
}

// =========================================================================
// Authentication
// =========================================================================

/**
 * Register a new user via the REST API.
 * On success, stores the JWT token and fetches the user list.
 */
async function register() {
    const data = {
        username: document.getElementById('reg-username').value,
        email: document.getElementById('reg-email').value,
        password: document.getElementById('reg-password').value,
        password_confirm: document.getElementById('reg-password-confirm').value,
    };

    try {
        const res = await fetch(`${API_BASE}/api/auth/register/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const json = await res.json();

        if (res.ok) {
            accessToken = json.tokens.access;
            currentUser = json.user;
            updateAuthStatus(true);
            log(`✅ Registered as "${currentUser.username}"`);
            fetchUsers();
        } else {
            log(`❌ Register error: ${JSON.stringify(json)}`);
        }
    } catch (e) {
        log(`❌ Network error: ${e.message}`);
    }
}

/**
 * Login an existing user via the REST API.
 * On success, stores the JWT token and fetches the user list.
 */
async function login() {
    const data = {
        username: document.getElementById('login-username').value,
        password: document.getElementById('login-password').value,
    };

    try {
        const res = await fetch(`${API_BASE}/api/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const json = await res.json();

        if (res.ok) {
            accessToken = json.access;
            currentUser = { username: data.username };
            updateAuthStatus(true);
            log(`✅ Logged in as "${data.username}"`);
            fetchUsers();
        } else {
            log(`❌ Login error: ${JSON.stringify(json)}`);
        }
    } catch (e) {
        log(`❌ Network error: ${e.message}`);
    }
}

/**
 * Update the auth status badge in the UI.
 * @param {boolean} loggedIn - Whether the user is logged in.
 */
function updateAuthStatus(loggedIn) {
    const el = document.getElementById('auth-status');
    if (loggedIn) {
        el.innerHTML = `
            <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
            ${currentUser.username}
        `;
        el.className = 'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-green-500/20 text-green-400 border border-green-500/30';
    } else {
        el.innerHTML = `
            <span class="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>
            Not logged in
        `;
        el.className = 'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-red-500/20 text-red-400 border border-red-500/30';
    }
}

// =========================================================================
// User List
// =========================================================================

/**
 * Fetch the list of registered users from the REST API.
 * Populates the user list sidebar.
 */
async function fetchUsers() {
    if (!accessToken) {
        log('⚠️  Login first to fetch users');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/auth/users/`, {
            headers: { 'Authorization': `Bearer ${accessToken}` },
        });
        const json = await res.json();

        if (res.ok) {
            const list = document.getElementById('user-list');
            const users = json.results || json;
            list.innerHTML = '';

            if (users.length === 0) {
                list.innerHTML = `
                    <li class="px-3 py-2 text-xs text-slate-500 italic">
                        No other users found
                    </li>
                `;
                return;
            }

            users.forEach(user => {
                const li = document.createElement('li');
                li.className = `px-3 py-2 rounded-lg cursor-pointer text-sm text-slate-300
                                hover:bg-surface-tertiary transition-colors duration-150
                                flex items-center justify-between group`;
                li.innerHTML = `
                    <span>${user.username}</span>
                    <span class="text-[10px] text-slate-500 group-hover:text-accent font-mono">
                        #${user.id}
                    </span>
                `;
                li.onclick = (e) => connectToUser(user.id, user.username, e);
                list.appendChild(li);
            });

            log(`👥 Found ${users.length} user(s)`);
        } else {
            log(`❌ Users error: ${JSON.stringify(json)}`);
        }
    } catch (e) {
        log(`❌ Network error: ${e.message}`);
    }
}

// =========================================================================
// WebSocket Connection
// =========================================================================

/**
 * Open a WebSocket connection to chat with a specific user.
 * Loads message history first, then connects.
 *
 * @param {number} userId - The target user's ID.
 * @param {string} username - The target user's username.
 * @param {Event} clickEvent - The click event from the user list.
 */
async function connectToUser(userId, username, clickEvent) {
    if (!accessToken) {
        log('⚠️  Login first');
        return;
    }

    // Close existing connection
    if (socket) {
        socket.close();
    }

    targetUserId = userId;
    document.getElementById('chat-target').textContent = `— ${username}`;

    // Load message history first
    await loadHistory(userId);

    // Open WebSocket connection
    const wsUrl = `${WS_BASE}/ws/chat/${userId}/?token=${accessToken}`;
    log(`🔌 Connecting to ws://…/ws/chat/${userId}/`);

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        updateWsStatus(true);
        log('🟢 WebSocket connected');
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'chat_message') {
            appendMessage(data.message);
        } else if (data.type === 'error') {
            log(`⚠️  Server error: ${data.detail}`);
        }
    };

    socket.onclose = (event) => {
        updateWsStatus(false);
        log(`🔴 WebSocket closed (code: ${event.code})`);
    };

    socket.onerror = () => {
        log('❌ WebSocket error');
    };

    // Highlight active user in list
    document.querySelectorAll('#user-list li').forEach(li => {
        li.classList.remove('bg-accent/20', 'text-accent-hover', 'border-l-2', 'border-accent');
    });
    if (clickEvent && clickEvent.currentTarget) {
        clickEvent.currentTarget.classList.add('bg-accent/20', 'text-accent-hover');
    }
}

/**
 * Update the WebSocket connection status badge.
 * @param {boolean} connected - Whether the WS is connected.
 */
function updateWsStatus(connected) {
    const el = document.getElementById('ws-status');
    if (connected) {
        el.innerHTML = `
            <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
            Connected
        `;
        el.className = 'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-green-500/20 text-green-400 border border-green-500/30';
    } else {
        el.innerHTML = `
            <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
            Disconnected
        `;
        el.className = 'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-red-500/20 text-red-400 border border-red-500/30';
    }
}

// =========================================================================
// Messaging
// =========================================================================

/**
 * Load message history with a specific user from the REST API.
 * @param {number} userId - The target user's ID.
 */
async function loadHistory(userId) {
    try {
        const res = await fetch(`${API_BASE}/api/chat/messages/${userId}/`, {
            headers: { 'Authorization': `Bearer ${accessToken}` },
        });
        const json = await res.json();

        if (res.ok) {
            const chatLog = document.getElementById('chat-log');
            chatLog.innerHTML = '';

            const messages = json.results || json;
            if (messages.length === 0) {
                chatLog.innerHTML = `
                    <div class="text-center text-slate-500 italic text-xs py-8">
                        No messages yet. Say hello! 👋
                    </div>
                `;
            } else {
                messages.forEach(msg => appendMessage(msg));
            }
            log(`📜 Loaded ${messages.length} message(s) from history`);
        }
    } catch (e) {
        log(`❌ History error: ${e.message}`);
    }
}

/**
 * Send a message through the active WebSocket connection.
 */
function sendMessage() {
    const input = document.getElementById('message-input');
    const text = input.value.trim();

    if (!socket || socket.readyState !== WebSocket.OPEN) {
        log('⚠️  Not connected to a chat');
        return;
    }

    if (!text) return;

    socket.send(JSON.stringify({ message: text }));
    input.value = '';
    input.focus();
}

/**
 * Append a message bubble to the chat log.
 * @param {Object} msg - Message object with sender, content, timestamp.
 */
function appendMessage(msg) {
    const chatLog = document.getElementById('chat-log');

    // Remove placeholder text if present
    const placeholder = chatLog.querySelector('.text-center.italic');
    if (placeholder) placeholder.remove();

    const isSent = currentUser &&
        (msg.sender === currentUser.username || msg.sender_id === currentUser.id);

    const wrapper = document.createElement('div');
    wrapper.className = `flex ${isSent ? 'justify-end' : 'justify-start'}`;

    const bubble = document.createElement('div');
    bubble.className = isSent
        ? 'max-w-[75%] px-3.5 py-2 rounded-2xl rounded-br-md bg-accent text-white text-sm'
        : 'max-w-[75%] px-3.5 py-2 rounded-2xl rounded-bl-md bg-surface-tertiary text-slate-200 text-sm';

    const time = new Date(msg.timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
    });

    bubble.innerHTML = `
        <div>${msg.content}</div>
        <div class="text-[10px] mt-1 ${isSent ? 'text-white/50' : 'text-slate-500'}">
            ${msg.sender} · ${time}
        </div>
    `;

    wrapper.appendChild(bubble);
    chatLog.appendChild(wrapper);
    chatLog.scrollTop = chatLog.scrollHeight;
}
