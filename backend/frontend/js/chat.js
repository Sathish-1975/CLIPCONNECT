/**
 * ClipConnect - Real-Time Chat JavaScript
 */

document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    const currentUserStr = localStorage.getItem('user');
    
    if (!token || !currentUserStr) {
        window.location.href = 'login.html';
        return;
    }

    const currentUser = JSON.parse(currentUserStr);
    let socket = null;
    let activeContactId = null;
    let conversations = [];
    let typingTimeout = null;

    // DOM Elements
    const contactsListEl = document.getElementById('chat-contacts-list');
    const searchInputEl   = document.getElementById('chat-search');
    const messagesAreaEl = document.getElementById('chat-messages-area');
    const activeAvatarEl = document.getElementById('active-avatar');
    const activeNameEl   = document.getElementById('active-user-name');
    const activeStatusEl = document.getElementById('active-user-status');
    const typingIndicatorEl = document.getElementById('typing-indicator');
    const chatInputEl    = document.getElementById('chat-input');
    const sendBtnEl      = document.getElementById('chat-send-btn');
    const fileInputEl    = document.getElementById('chat-file-input');

    // Initialize SocketIO connection
    initSocket();
    await loadConversations();

    // Check query param for auto-opening chat (e.g. chat.html?user=5)
    const urlParams = new URLSearchParams(window.location.search);
    const targetUserId = urlParams.get('user');
    if (targetUserId) {
        selectContact(parseInt(targetUserId, 10));
    }

    function initSocket() {
        if (typeof io === 'undefined') return;

        socket = io({
            auth: { token: token },
            query: { token: token }
        });

        socket.on('connect', () => {
            console.log('⚡ Connected to Chat Socket Server');
        });

        socket.on('receive_chat_message', (msg) => {
            if (msg.sender_id === activeContactId || msg.receiver_id === activeContactId) {
                appendMessage(msg);
                scrollToBottom();
            }
            loadConversations();
        });

        socket.on('user_typing', (data) => {
            if (data.sender_id === activeContactId) {
                typingIndicatorEl.style.display = data.is_typing ? 'block' : 'none';
                if (data.is_typing) scrollToBottom();
            }
        });

        socket.on('user_online', (data) => {
            if (data.user_id === activeContactId) {
                activeStatusEl.textContent = 'Online';
                activeStatusEl.style.color = '#10b981';
            }
        });

        socket.on('user_offline', (data) => {
            if (data.user_id === activeContactId) {
                activeStatusEl.textContent = 'Offline';
                activeStatusEl.style.color = '#9ca3af';
            }
        });
    }

    async function loadConversations() {
        try {
            const res = await API.get('/chat/conversations');
            if (res && res.success) {
                conversations = res.data.conversations || [];
                renderContacts(conversations);
            }
        } catch (err) {
            console.error('Failed to load conversations:', err);
            contactsListEl.innerHTML = `<div style="padding:20px; color:#ef4444; text-align:center;">Failed to load contacts.</div>`;
        }
    }

    function renderContacts(contacts) {
        if (!contacts.length) {
            contactsListEl.innerHTML = `<div style="padding:20px; text-align:center; color:#9ca3af;">No conversations yet.</div>`;
            return;
        }

        contactsListEl.innerHTML = contacts.map(c => `
            <div class="contact-item ${c.contact_id === activeContactId ? 'active' : ''}" onclick="window.selectContact(${c.contact_id})">
                <div class="contact-avatar">
                    ${c.full_name.charAt(0).toUpperCase()}
                    <span class="status-dot ${c.is_online ? 'online' : 'offline'}"></span>
                </div>
                <div class="contact-info">
                    <div class="contact-name">
                        <span>${escapeHtml(c.full_name)}</span>
                        ${c.unread_count > 0 ? `<span class="unread-badge">${c.unread_count}</span>` : ''}
                    </div>
                    <div class="contact-last-msg">
                        ${c.last_message ? escapeHtml(c.last_message.content || 'Attachment') : 'Start talking...'}
                    </div>
                </div>
            </div>
        `).join('');
    }

    window.selectContact = async function(contactId) {
        activeContactId = contactId;
        renderContacts(conversations);

        chatInputEl.disabled = false;
        sendBtnEl.disabled = false;
        messagesAreaEl.innerHTML = '<div style="text-align:center; padding:20px; color:#9ca3af;">Loading history...</div>';

        try {
            const res = await API.get(`/chat/messages/${contactId}`);
            if (res && res.success) {
                const contact = res.data.contact;
                const msgs = res.data.messages;

                activeAvatarEl.textContent = contact.full_name.charAt(0).toUpperCase();
                activeNameEl.textContent = contact.full_name;
                activeStatusEl.textContent = 'Active';

                renderMessages(msgs);
                scrollToBottom();
            }
        } catch (err) {
            messagesAreaEl.innerHTML = '<div style="text-align:center; padding:20px; color:#ef4444;">Failed to load chat history.</div>';
        }
    };

    function renderMessages(messages) {
        if (!messages.length) {
            messagesAreaEl.innerHTML = `
                <div class="chat-empty-state">
                    <p>No messages yet. Send a message to start the conversation!</p>
                </div>
            `;
            return;
        }

        messagesAreaEl.innerHTML = messages.map(m => createMessageHtml(m)).join('');
    }

    function appendMessage(msg) {
        const emptyState = messagesAreaEl.querySelector('.chat-empty-state');
        if (emptyState) messagesAreaEl.innerHTML = '';

        messagesAreaEl.insertAdjacentHTML('beforeend', createMessageHtml(msg));
    }

    function createMessageHtml(msg) {
        const isSent = msg.sender_id === currentUser.id;
        const timeStr = new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        let attachmentsHtml = '';
        if (msg.attachments && msg.attachments.length) {
            attachmentsHtml = msg.attachments.map(att => `
                <div style="margin-top: 6px; font-size: 0.85rem; background: rgba(0,0,0,0.2); padding: 6px 10px; border-radius: 6px;">
                    📎 <a href="${att.file_url}" target="_blank" style="color: #6366f1; text-decoration: underline;">${escapeHtml(att.file_name)}</a>
                </div>
            `).join('');
        }

        return `
            <div class="message-bubble-wrapper ${isSent ? 'sent' : 'received'}">
                <div class="message-bubble">
                    ${escapeHtml(msg.content)}
                    ${attachmentsHtml}
                    <div class="message-meta">
                        <span>${timeStr}</span>
                        ${isSent ? (msg.is_read ? '✓✓' : '✓') : ''}
                    </div>
                </div>
            </div>
        `;
    }

    // Input handlers & Typing indicators
    chatInputEl.addEventListener('input', () => {
        if (!socket || !activeContactId) return;

        socket.emit('typing_start', { sender_id: currentUser.id, receiver_id: activeContactId });

        clearTimeout(typingTimeout);
        typingTimeout = setTimeout(() => {
            socket.emit('typing_stop', { sender_id: currentUser.id, receiver_id: activeContactId });
        }, 1500);
    });

    chatInputEl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    sendBtnEl.addEventListener('click', sendMessage);

    async function sendMessage() {
        const content = chatInputEl.value.trim();
        if (!content || !activeContactId) return;

        chatInputEl.value = '';

        try {
            const res = await API.post('/chat/messages', {
                receiver_id: activeContactId,
                content: content,
                message_type: 'text'
            });

            if (res && res.success) {
                const msg = res.data.message;
                appendMessage(msg);
                scrollToBottom();

                if (socket) {
                    socket.emit('send_chat_message', {
                        receiver_id: activeContactId,
                        message: msg
                    });
                }
                loadConversations();
            }
        } catch (err) {
            console.error('Failed to send message:', err);
            alert('Failed to send message.');
        }
    }

    function scrollToBottom() {
        messagesAreaEl.scrollTop = messagesAreaEl.scrollHeight;
    }

    function escapeHtml(text) {
        if (!text) return '';
        return text.replace(/[&<>"']/g, function(m) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
        });
    }

    // Search contact filter
    searchInputEl.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const filtered = conversations.filter(c => c.full_name.toLowerCase().includes(query));
        renderContacts(filtered);
    });
});
