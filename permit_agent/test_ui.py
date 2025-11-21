#!/usr/bin/env python3

import asyncio
import json
from flask import Flask, render_template_string, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Permit Agent Test UI</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; margin-bottom: 30px; }
        .chat-container { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 15px; margin-bottom: 20px; background-color: #fafafa; border-radius: 5px; }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
        .user-message { background-color: #007bff; color: white; text-align: right; }
        .agent-message { background-color: #e9ecef; color: #333; }
        .system-message { background-color: #28a745; color: white; font-style: italic; }
        .error-message { background-color: #dc3545; color: white; }
        .input-container { display: flex; gap: 10px; }
        .query-input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
        .send-btn { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .send-btn:hover { background-color: #0056b3; }
        .send-btn:disabled { background-color: #6c757d; cursor: not-allowed; }
        .classification { margin: 10px 0; padding: 8px; border-radius: 5px; font-weight: bold; }
        .time-calc { background-color: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .content-search { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .loading { text-align: center; color: #666; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Permit Agent Test UI</h1>
            <p>Test the improved retrieval flow with query classification</p>
        </div>
        
        <div id="chat-container" class="chat-container">
            <div class="message system-message">
                <strong>System:</strong> Permit Agent initialized. Ready to test query classification and retrieval flow!
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="query-input" class="query-input" placeholder="Enter your query (e.g., 'Dokumen apa yang sudah expired?' or 'Berapa panjang pipeline di IT Semarang?')" onkeypress="handleKeyPress(event)">
            <button id="send-btn" class="send-btn" onclick="sendQuery()">Send</button>
        </div>
        
        <div style="margin-top: 15px; font-size: 14px; color: #666;">
            <strong>Test Examples:</strong><br>
            • Time Calculation: "Dokumen apa yang sudah expired?"<br>
            • Content Search: "Berapa panjang pipeline di IT Semarang?"<br>
            • Mixed Query: "Berapa lama lagi masa berlaku PLO untuk IT Jakarta?"
        </div>
    </div>

    <script>
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendQuery();
            }
        }

        async function sendQuery() {
            const input = document.getElementById('query-input');
            const sendBtn = document.getElementById('send-btn');
            const chatContainer = document.getElementById('chat-container');
            
            const query = input.value.trim();
            if (!query) return;
            
            // Add user message
            addMessage('user', query);
            
            // Clear input and disable button
            input.value = '';
            sendBtn.disabled = true;
            sendBtn.textContent = 'Processing...';
            
            // Add loading message
            const loadingDiv = addMessage('system', 'Processing query...', 'loading');
            
            try {
                const response = await fetch('/test_query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: query })
                });
                
                const result = await response.json();
                
                // Remove loading message
                chatContainer.removeChild(loadingDiv);
                
                if (result.error) {
                    addMessage('error', `Error: ${result.error}`);
                } else {
                    // Add classification
                    const classType = result.classification === 'time_calculation' ? 'time-calc' : 'content-search';
                    const classText = result.classification === 'time_calculation' ? 
                        '🕒 Time Calculation → Cosmos DB' : 
                        '📄 Content Search → AI Search (Filtered)';
                    
                    addMessage('system', `Classification: ${classText}`, classType);
                    
                    // Add agent response
                    addMessage('agent', result.response || 'No response received');
                }
                
            } catch (error) {
                // Remove loading message
                chatContainer.removeChild(loadingDiv);
                addMessage('error', `Network Error: ${error.message}`);
            }
            
            // Re-enable button
            sendBtn.disabled = false;
            sendBtn.textContent = 'Send';
            
            // Focus input
            input.focus();
        }
        
        function addMessage(type, content, extraClass = '') {
            const chatContainer = document.getElementById('chat-container');
            const messageDiv = document.createElement('div');
            
            let className = 'message ';
            let prefix = '';
            
            switch(type) {
                case 'user':
                    className += 'user-message';
                    prefix = 'You: ';
                    break;
                case 'agent':
                    className += 'agent-message';
                    prefix = 'Agent: ';
                    break;
                case 'system':
                    className += 'system-message';
                    prefix = 'System: ';
                    break;
                case 'error':
                    className += 'error-message';
                    prefix = 'Error: ';
                    break;
            }
            
            if (extraClass) {
                className += ' ' + extraClass;
            }
            
            messageDiv.className = className;
            messageDiv.innerHTML = `<strong>${prefix}</strong>${content}`;
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            return messageDiv;
        }
        
        // Focus input on load
        document.getElementById('query-input').focus();
    </script>
</body>
</html>
"""

def classify_query_intent(user_query: str) -> str:
    """Classify if query needs time calculation or content search"""
    time_keywords = ["expired", "kedaluwarsa", "berapa lama", "sudah berapa", "waktu", "tanggal", "masa berlaku", "habis"]
    if any(keyword in user_query.lower() for keyword in time_keywords):
        return "time_calculation"
    return "content_search"

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/test_query', methods=['POST'])
def test_query():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'No query provided'})
        
        # Classify query
        classification = classify_query_intent(query)
        
        # Simulate agent response based on classification
        if classification == "time_calculation":
            response = f"🕒 Time calculation query detected. This would route to Cosmos DB tools:\n\n"
            response += "• get_current_date()\n"
            response += "• get_time_difference()\n"
            response += "• get_list_documents_already_expired()\n\n"
            response += f"Query: '{query}' would be processed using metadata from Cosmos DB for accurate date calculations."
        else:
            response = f"📄 Content search query detected. This would use improved retrieval flow:\n\n"
            response += "Step 1: Search title_index for distinct documents\n"
            response += "Step 2: Filter content search in index_typea_cz_5000_co_500_prod_2\n"
            response += "Step 3: Return filtered results with citations\n\n"
            response += f"Query: '{query}' would be processed using the enhanced document filtering approach."
        
        return jsonify({
            'classification': classification,
            'response': response,
            'query': query
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("🚀 Starting Permit Agent Test UI...")
    print("📍 Access at: http://localhost:5001")
    print("🔍 Test query classification and routing logic")
    print("\nPress Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
