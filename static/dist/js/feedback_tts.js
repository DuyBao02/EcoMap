document.addEventListener("DOMContentLoaded", function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    function appendMessage(sender, message, locations = []) {
        const messageElement = document.createElement('div');
        messageElement.className = sender === 'You' ? 'text-right' : 'text-left';
        messageElement.innerHTML = `
            <div class="${sender === 'You' ? 'bg-blue-500 text-white' : 'bg-gray-300'} inline-block rounded-lg px-3 py-2 m-1">
                ${message}
                ${sender === 'Chatbot' ? '<button class="text-to-speech-button ml-2"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="size-5"><path d="M10.5 3.75a.75.75 0 0 0-1.264-.546L5.203 7H2.667a.75.75 0 0 0-.7.48A6.985 6.985 0 0 0 1.5 10c0 .887.165 1.737.468 2.52.111.29.39.48.7.48h2.535l4.033 3.796a.75.75 0 0 0 1.264-.546V3.75ZM16.45 5.05a.75.75 0 0 0-1.06 1.061 5.5 5.5 0 0 1 0 7.778.75.75 0 0 0 1.06 1.06 7 7 0 0 0 0-9.899Z" /><path d="M14.329 7.172a.75.75 0 0 0-1.061 1.06 2.5 2.5 0 0 1 0 3.536.75.75 0 0 0 1.06 1.06 4 4 0 0 0 0-5.656Z" /></svg></button>' : ''}
            </div>
        `;
        if (locations.length > 0) {
            locations.forEach(location => {
                location.dia_diem.forEach((place, index) => {
                    const placeElement = document.createElement('div');
                    placeElement.className = 'mt-2 text-white dark:text-black';
                    placeElement.innerHTML = `<strong>${place}</strong>`;
                    const imgElement = document.createElement('img');
                    imgElement.src = `${location.hinh_anh[index]}`;
                    imgElement.alt = place;
                    imgElement.className = 'max-w-full h-auto rounded-lg mt-2';  // CSS để chỉnh hình ảnh
                    placeElement.appendChild(imgElement);
                    messageElement.appendChild(placeElement);
                });
            });
        }
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll to the bottom

        const ttsButtons = messageElement.getElementsByClassName('text-to-speech-button');
        if (ttsButtons.length > 0) {
            ttsButtons[0].addEventListener('click', function() {
                fetch('/text-to-speech', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: message }),
                })
                .then(response => response.blob())
                .then(blob => {
                    const url = URL.createObjectURL(blob);
                    const audio = new Audio(url);
                    audio.play();
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            });
        }
    }

    function sendMessage(message) {
        fetch('/webhook', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        })
        .then(response => response.json())
        .then(data => {
            const botResponse = data.response;
            const locations = data.locations || [];
            appendMessage('Chatbot', botResponse, locations);
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    function handleSendMessage() {
        const userMessage = userInput.value.trim();
        if (userMessage !== '') {
            appendMessage('You', userMessage);
            sendMessage(userMessage);
            userInput.value = '';
        }
    }

    sendButton.addEventListener('click', handleSendMessage);

    userInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            handleSendMessage();
        }
    });

    appendMessage('Chatbot', 'Xin chào, tôi có thể giúp gì cho bạn?');
});