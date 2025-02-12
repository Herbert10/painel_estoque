document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const questionInput = document.getElementById('question-input');
    const sendBtn = document.getElementById('send-btn');
    const predefinedBtns = document.querySelectorAll('.predefined-btn');
    const clientIdInput = document.getElementById('client-id-input');

    function addMessageToChat(message, isUser) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', isUser ? 'user-message' : 'bot-message');
        messageElement.textContent = message;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function sendQuestion(question) {
        addMessageToChat(question, true);
        questionInput.value = '';

        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question }),
            });

            const data = await response.json();
            addMessageToChat(data.response, false);
        } catch (error) {
            addMessageToChat('Erro ao processar a pergunta.', false);
        }
    }

    sendBtn.addEventListener('click', () => {
        const question = questionInput.value.trim();
        if (question) {
            sendQuestion(question);
        }
    });

    questionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const question = questionInput.value.trim();
            if (question) {
                sendQuestion(question);
            }
        }
    });

    predefinedBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const clientId = clientIdInput.value.trim();
            if (!clientId) {
                alert("Por favor, insira o ID do cliente.");
                return;
            }

            const baseQuestion = btn.getAttribute('data-question');
            const fullQuestion = `${baseQuestion}${clientId}`;
            sendQuestion(fullQuestion);
        });
    });
});