#!/usr/bin/env python3

import asyncio
import json
import sys
import os
from flask import Flask, render_template_string, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# HTML Template (same as test_ui.py but with real agent integration)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Permit Agent Test UI - Advanced</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; margin-bottom: 30px; }
        .status { padding: 10px; margin-bottom: 20px; border-radius: 5px; font-weight: bold; }
        .status.ready { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .chat-container { border: 1px solid #ddd; height: 450px; overflow-y: auto; padding: 15px; margin-bottom: 20px; background-color: #fafafa; border-radius: 5px; }
        .message { margin-bottom: 15px; padding: 12px; border-radius: 8px; }
        .user-message { background-color: #007bff; color: white; text-align: right; }
        .agent-message { background-color: #e9ecef; color: #333; white-space: pre-wrap; }
        .system-message { background-color: #28a745; color: white; font-style: italic; }
        .error-message { background-color: #dc3545; color: white; }
        .input-container { display: flex; gap: 10px; }
        .query-input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
        .send-btn { padding: 12px 24px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .send-btn:hover { background-color: #0056b3; }
        .send-btn:disabled { background-color: #6c757d; cursor: not-allowed; }
        .classification { margin: 10px 0; padding: 10px; border-radius: 5px; font-weight: bold; }
        .time-calc { background-color: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .content-search { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .loading { text-align: center; color: #666; font-style: italic; }
        .examples { margin-top: 15px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }
        .examples h4 { margin-top: 0; color: #495057; }
        .example-btn { margin: 5px; padding: 8px 12px; background-color: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .example-btn:hover { background-color: #5a6268; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Permit Agent Test UI - Advanced</h1>
            <p>Real integration with agent_langchain.py and backend.py</p>
        </div>
        
        <div id="status" class="status ready">
            <strong>Status:</strong> <span id="status-text">Initializing agent...</span>
        </div>
        
        <div id="chat-container" class="chat-container">
            <div class="message system-message">
                <strong>System:</strong> Advanced Permit Agent Test UI loaded. Checking agent status...
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="query-input" class="query-input" placeholder="Enter your query..." onkeypress="handleKeyPress(event)">
            <button id="send-btn" class="send-btn" onclick="sendQuery()">Send</button>
        </div>
        
        <div class="examples">
            <h4>🧪 Test Examples:</h4>
            <button class="example-btn" onclick="setQuery('Dokumen apa saja yang sudah expired?')">Time Calculation</button>
            <button class="example-btn" onclick="setQuery('Berapa panjang submarine pipeline yang ada di IT Semarang?')">Content Search</button>
            <button class="example-btn" onclick="setQuery('Berapa lama lagi masa berlaku PLO untuk IT Jakarta?')">Mixed Query</button>
            <button class="example-btn" onclick="setQuery('List dokumen PLO yang akan expired tahun ini')">Cosmos DB Query</button>
        </div>
    </div>

    <script>
        // Check agent status on load
        window.onload = function() {
            checkAgentStatus();
        };
        
        async function checkAgentStatus() {
            try {
                const response = await fetch('/status');
                const result = await response.json();
                
                const statusDiv = document.getElementById('status');
                const statusText = document.getElementById('status-text');
                
                if (result.ready) {
                    statusDiv.className = 'status ready';
                    statusText.textContent = 'Agent ready! All components initialized.';
                    addMessage('system', 'Agent successfully initialized and ready for testing!');
                } else {
                    statusDiv.className = 'status error';
                    statusText.textContent = `Agent initialization failed: ${result.error}`;
                    addMessage('error', `Agent Status: ${result.error}`);
                }
            } catch (error) {
                const statusDiv = document.getElementById('status');
                const statusText = document.getElementById('status-text');
                statusDiv.className = 'status error';
                statusText.textContent = 'Failed to check agent status';
                addMessage('error', `Status Check Failed: ${error.message}`);
            }
        }
        
        function setQuery(query) {
            document.getElementById('query-input').value = query;
            document.getElementById('query-input').focus();
        }
        
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
            const loadingDiv = addMessage('system', 'Agent is processing your query...', 'loading');
            
            try {
                const response = await fetch('/query', {
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
                        '🕒 Time Calculation → Cosmos DB Tools' : 
                        '📄 Content Search → AI Search (Title → Content Filtering)';
                    
                    addMessage('system', `Classification: ${classText}`, classType);
                    
                    // Add agent response
                    addMessage('agent', result.response || 'No response received');
                    
                    // Add execution info if available
                    if (result.execution_info) {
                        addMessage('system', `Execution: ${result.execution_info}`);
                    }
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
    </script>
</body>
</html>
"""

# Global variables for agent
agent = None
agent_ready = False
agent_error = None

def initialize_agent():
    """Initialize the agent"""
    global agent, agent_ready, agent_error
    
    try:
        # Try to import and initialize agent
        from agent_langchain import agent as imported_agent, classify_query_intent
        agent = imported_agent
        agent_ready = True
        print("✅ Agent initialized successfully")
        return True
    except Exception as e:
        agent_error = str(e)
        agent_ready = False
        print(f"❌ Agent initialization failed: {e}")
        return False

def classify_query_intent(user_query: str) -> str:
    """Classify if query needs time calculation or content search"""
    time_keywords = ["expired", "kedaluwarsa", "berapa lama", "sudah berapa", "waktu", "tanggal", "masa berlaku", "habis"]
    if any(keyword in user_query.lower() for keyword in time_keywords):
        return "time_calculation"
    return "content_search"

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    """Check agent status"""
    return jsonify({
        'ready': agent_ready,
        'error': agent_error
    })

@app.route('/query', methods=['POST'])
def query():
    """Process query with real agent"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'No query provided'})
        
        # Classify query
        classification = classify_query_intent(query)
        
        if agent_ready and agent:
            # Use real agent
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                response = loop.run_until_complete(
                    agent.ainvoke({
                        "messages": [{"role": "user", "content": query}]
                    })
                )
                
                agent_response = response['messages'][-1]['content'] if response.get('messages') else "No response"
                execution_info = f"Real agent executed with {len(response.get('messages', []))} message exchanges"
                
            except Exception as e:
                agent_response = f"Agent execution failed: {str(e)}"
                execution_info = "Agent execution error"
        else:
            # Fallback simulation
            if classification == "time_calculation":
                agent_response = f"🕒 [SIMULATED] Time calculation query processed.\n\nThis would execute:\n• get_current_date()\n• get_time_difference()\n• get_list_documents_already_expired()\n\nQuery: '{query}' classified for Cosmos DB processing."
            else:
                agent_response = f"📄 [SIMULATED] Content search query processed.\n\nFlow executed:\n1. Search title_index for distinct documents\n2. Filter content in index_typea_cz_5000_co_500_prod_2\n3. Return filtered results\n\nQuery: '{query}' processed with enhanced filtering."
            
            execution_info = "Simulated response (agent not available)"
        
        return jsonify({
            'classification': classification,
            'response': agent_response,
            'execution_info': execution_info,
            'query': query
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("🚀 Starting Advanced Permit Agent Test UI...")
    print("🔧 Initializing agent...")
    
    # Initialize agent
    initialize_agent()
    
    print("📍 Access at: http://localhost:5002")
    print("🤖 Real agent integration with fallback simulation")
    print("\nPress Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
