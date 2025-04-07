// frontend/static/js/chat.js
class ChatBot {
    constructor() {
        this.messageContainer = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.apiUrl = 'http://localhost:8000/api';
        this.messageCounter = 0; // Unique ID counter to avoid overlaps
        this.userId = `user-${Math.random().toString(36).slice(-5)}`; // Unique user ID for each session
        console.log("User ID: " + this.userId); // Log the user ID for debugging
        this.init();
    }

    init() {
        this.addMessage("Welcome! What specific cultural elements in Stardew Valley Mods are you interested in exploring from people's perspectives?\nYou can enter a group term (e.g., LGBT, Asian), country-prefixed broad categories (e.g., Japanese cuisine, French architecture), or a country name to generate specific cultural elements as well.", 'bot');
    }

    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message) return;

        this.addMessage(message, 'user');
        this.userInput.value = '';
        this.userInput.disabled = true; // Disable input while processing
  
        const loadingId = this.addMessage('Analyzing...', 'bot'); 
        try { 
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({message: message, user_id: this.userId}), // Send the user ID with the message
            });

            if (!response.ok) throw new Error('Network response was not ok');

        const data = await response.json();  // Parse the JSON response
            console.log(data);
            this.addMessage(data.response, 'bot'); // Add the backend response
            this.removeMessage(loadingId); // Remove "Analyzing..." using the ID

        } catch (error) {
            console.error('Error:', error);
            this.removeMessage(loadingId); // Remove "Analyzing..." even on error
            this.addMessage('Sorry, there was an error processing your request.', 'bot');
        } finally {
            this.userInput.disabled = false; // Re-enable input
            this.userInput.focus();
        }
    }

    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        
        // Convert newlines to <br> tags
        messageDiv.innerHTML = text.replace(/\n/g, '<br>');

        // Use a unique ID with timestamp and counter
        const id = `msg-${Date.now()}-${this.messageCounter++}`;
        messageDiv.setAttribute('id', id);
        
        this.messageContainer.appendChild(messageDiv);
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
        
        return id; // Return the ID string
    }

    removeMessage(id) {
        const message = document.getElementById(id);
        if (message) {
            console.log("Deleted message with ID: " + id);
            message.remove();
        } else {
            console.warn("No message found with ID: " + id);
        }
    }
}

const chatbot = new ChatBot();

window.sendMessage = () => chatbot.sendMessage(); 

document.getElementById('user-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        chatbot.sendMessage();
    }
});