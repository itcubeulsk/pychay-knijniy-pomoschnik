document.addEventListener('DOMContentLoaded', () => {
    const socket = io();

    const messagesDiv = document.getElementById('messages');
    const messageInput = document.getElementById('messageInput');
    const usernameInput = document.getElementById('usernameInput');
    const sendButton = document.getElementById('sendButton');

    function scrollToBottom() {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    function appendMessage(messageData) {
        const messageWrapper = document.createElement('div');
        const messageBubble = document.createElement('div');
        const userSpan = document.createElement('strong');
        const textSpan = document.createElement('span');

        userSpan.textContent = messageData.user + ':';
        textSpan.textContent = messageData.msg;

        messageBubble.appendChild(userSpan);
        messageBubble.appendChild(document.createTextNode(' '));
        messageBubble.appendChild(textSpan);

        messageWrapper.classList.add('message-wrapper');
        messageBubble.classList.add('message-bubble');

        if (messageData.type === 'user') {
            messageWrapper.classList.add('user-message-wrapper');
            messageBubble.classList.add('user-message-bubble');
        } else if (messageData.type === 'server') {
            messageWrapper.classList.add('server-message-wrapper');
            messageBubble.classList.add('server-message-bubble');
        }

        messageWrapper.appendChild(messageBubble);
        messagesDiv.appendChild(messageWrapper);
        scrollToBottom();
    }


    const typingIndicator = document.createElement('div');
    typingIndicator.classList.add('message-wrapper', 'server-message-wrapper');
    typingIndicator.innerHTML =
        '<div class="message-bubble server-message-bubble typing-bubble">' +
        '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>' +
        '</div>';

    function showTyping() {
        if (!typingIndicator.parentNode) {
            messagesDiv.appendChild(typingIndicator);
            scrollToBottom();
        }
    }

    function hideTyping() {
        if (typingIndicator.parentNode) {
            typingIndicator.remove();
        }
    }

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('message', (data) => {
        if (data.type === 'server') {
            hideTyping();
        }
        appendMessage(data);
    });

    function sendMessage() {
        const messageText = messageInput.value.trim();
        const username = usernameInput.value.trim();

        if (messageText && username) {
            socket.emit('message', { user: username, msg: messageText });
            messageInput.value = '';
            messageInput.focus();
            showTyping();
        }
    }

    sendButton.addEventListener('click', sendMessage);

    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    const initialMessagesHtml = document.querySelectorAll('#messages .message-wrapper');
    initialMessagesHtml.forEach(wrapperElement => {
        const isUserMessage = wrapperElement.classList.contains('user-message-wrapper');

        const bubbleElement = wrapperElement.querySelector('.message-bubble');
        let userText = 'Unknown';
        let messageText = '';

        if (bubbleElement) {
            const strongElement = bubbleElement.querySelector('strong');
            const textSpan = bubbleElement.querySelector('span');

            if (strongElement) {
                userText = strongElement.textContent.slice(0, -1);
            }
            if (textSpan) {
                messageText = textSpan.textContent;
            } else {
                messageText = bubbleElement.textContent.replace(`${userText}:`, '').trim();
            }
        }

        const messageData = {
            user: userText,
            msg: messageText,
            type: isUserMessage ? 'user' : 'server'
        };

        wrapperElement.remove();
        appendMessage(messageData);
    });

    scrollToBottom();
});