document.getElementById('mic-button').addEventListener('click', function() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'vi-VN';
    recognition.onresult = function(event) {
        const text = event.results[0][0].transcript;
        document.getElementById('user-input').value = text;
    };
    recognition.start();
});