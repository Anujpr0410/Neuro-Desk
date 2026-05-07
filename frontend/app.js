/**
 * NeuroDesk Frontend - Main Application
 * Handles chat, streaming, and UI interactions
 */

// Global State
const state = {
    config: {},
    preInstructions: {},
    currentPlatform: 'All',
    timer: { seconds: 0, interval: null },
    currentTab: 'mab',
    websocket: null,
    currentSessionId: null,
    messageHistory: {
        mab: [],
        sab1: [],
        sab2: [],
        sab3: []
    }
};

// DOM Elements
const dom = {
    themeToggle: document.getElementById('theme-toggle'),
    themeIcon: document.getElementById('theme-icon'),
    pageTitle: document.getElementById('page-title'),
    platformDisplay: document.getElementById('platform-display'),
    platformButtons: document.querySelectorAll('.platform-btn'),
    activityTimer: document.getElementById('activity-timer'),
    activityMessages: document.getElementById('activity-messages'),
    modal: {
        addTool: document.getElementById('add-tool-modal'),
        output: document.getElementById('output-modal')
    },
    inputArea: {
        mab: document.getElementById('mab-input'),
        sab1: document.getElementById('sab1-input'),
        sab2: document.getElementById('sab2-input'),
        sab3: document.getElementById('sab3-input')
    },
    chatMessages: {
        mab: document.getElementById('mab-chat-messages'),
        sab1: document.getElementById('sab1-chat-messages'),
        sab2: document.getElementById('sab2-chat-messages'),
        sab3: document.getElementById('sab3-chat-messages')
    },
    sendButtons: {
        mab: document.getElementById('mab-send'),
        sab1: document.getElementById('sab1-send'),
        sab2: document.getElementById('sab2-send'),
        sab3: document.getElementById('sab3-send')
    },
    settings: {
        providerSelects: document.querySelectorAll('.provider-select'),
        apiKeyInputs: document.querySelectorAll('.api-key-input'),
        modelInputs: document.querySelectorAll('.model-input'),
        preInstructionTextareas: document.querySelectorAll('.pre-instruction-textarea'),
        saveButtons: document.querySelectorAll('.save-btn')
    },
    history: {
        list: document.getElementById('history-list'),
        newBtn: document.getElementById('new-session-btn')
    }
};

// Agent Colors for Messages
const AGENT_COLORS = {
    mab: '#4f98a3',
    sab1: '#5b8dee',
    sab2: '#9b72cf',
    sab3: '#f0a050'
};

const AGENT_EMOJIS = {
    mab: '🧠',
    sab1: '🔍',
    sab2: '📊',
    sab3: '✍️'
};

const AGENT_NAMES = {
    mab: 'MAB',
    sab1: 'SAB1',
    sab2: 'SAB2',
    sab3: 'SAB3'
};

// Initialize Application
function init() {
    loadConfiguration();
    setupEventListeners();
    startTimer();
    connectWebSocket();
    setupSettings();
    initSession();
}

// Load Configuration
function loadConfiguration() {
    fetch('/config')
        .then(r => r.json())
        .then(config => {
            state.config = config;
            updateAgentInfo();
        })
        .catch(() => {
            // Use defaults if API not available
            state.config = {
                MAB: { provider: 'Ollama', api_key: '', model: 'llama3:8b' },
                SAB1: { provider: 'Ollama', api_key: '', model: 'llama3:8b' },
                SAB2: { provider: 'Ollama', api_key: '', model: 'llama3:8b' },
                SAB3: { provider: 'Ollama', api_key: '', model: 'llama3:8b' }
            };
            updateAgentInfo();
        });

    fetch('/pre-instructions')
        .then(r => r.json())
        .then(instructions => {
            state.preInstructions = instructions;
        })
        .catch(() => {
            state.preInstructions = {};
        });
}

// Update Agent Info Display
function updateAgentInfo() {
    document.getElementById('sab1-provider').textContent = state.config.SAB1?.provider || 'Ollama';
    document.getElementById('sab1-model').textContent = state.config.SAB1?.model || 'llama3:8b';

    document.getElementById('sab2-provider').textContent = state.config.SAB2?.provider || 'Ollama';
    document.getElementById('sab2-model').textContent = state.config.SAB2?.model || 'llama3:8b';

    document.getElementById('sab3-provider').textContent = state.config.SAB3?.provider || 'Ollama';
    document.getElementById('sab3-model').textContent = state.config.SAB3?.model || 'llama3:8b';
}

// Setup Event Listeners
function setupEventListeners() {
    // Theme toggle
    dom.themeToggle.addEventListener('click', toggleTheme);

    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const tab = item.dataset.tab;
            switchTab(tab);
        });
    });

    // Platform selector
    dom.platformButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            dom.platformButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentPlatform = btn.dataset.platform;
            dom.platformDisplay.textContent = state.currentPlatform;
        });
    });

    // Message inputs
    ['mab', 'sab1', 'sab2', 'sab3'].forEach(agent => {
        const input = document.getElementById(`${agent}-input`);
        const sendBtn = document.getElementById(`${agent}-send`);

        const handleSend = () => {
            const text = input.value.trim();
            if (text) {
                addMessageToChat(agent, 'user', text);
                sendChatMessage(agent, text);
                input.value = '';
            }
        };

        sendBtn.addEventListener('click', handleSend);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        });
    });

    // Run Campaign button
    const runCampaignBtn = document.getElementById('run-campaign-btn');
    if (runCampaignBtn) {
        runCampaignBtn.addEventListener('click', () => {
            const input = document.getElementById('mab-input');
            const text = input.value.trim() || 'Please run the full marketing campaign.';
            addMessageToChat('mab', 'user', text);
            sendCampaignGoal(text);
            input.value = '';
        });
    }

    // Modal controls
    document.getElementById('add-tool-btn').addEventListener('click', () => {
        dom.modal.addTool.style.display = 'flex';
    });

    document.getElementById('add-tool-close').addEventListener('click', () => {
        dom.modal.addTool.style.display = 'none';
    });

    document.getElementById('add-tool-cancel').addEventListener('click', () => {
        dom.modal.addTool.style.display = 'none';
    });

    document.getElementById('add-tool-submit').addEventListener('click', addTool);
    document.getElementById('output-close').addEventListener('click', () => {
        dom.modal.output.style.display = 'none';
    });

    // Output actions
    document.getElementById('copy-output').addEventListener('click', copyOutput);
    document.getElementById('download-md').addEventListener('click', downloadMarkdown);
    document.getElementById('download-txt').addEventListener('click', downloadText);

    // Tool registry actions
    document.getElementById('tool-registry-body').addEventListener('click', (e) => {
        if (e.target.dataset.tool) {
            handleToolAction(e.target.dataset.tool, e.target.dataset.action);
        }
    });

    // Click outside modals to close
    document.addEventListener('click', (e) => {
        if (e.target === dom.modal.addTool) {
            dom.modal.addTool.style.display = 'none';
        }
        if (e.target === dom.modal.output) {
            dom.modal.output.style.display = 'none';
        }
    });
}

// Setup Settings Form
function setupSettings() {
    // Pre-populate settings from config
    const populateAgentSettings = (agentKey, index) => {
        if (state.config[agentKey]) {
            dom.settings.providerSelects[index].value = state.config[agentKey].provider || 'Ollama';
            dom.settings.apiKeyInputs[index].value = state.config[agentKey].api_key || '';
            
            // Set model value (it might be a select or input, but setting .value works for both)
            const modelInput = document.querySelector(`.model-input[data-agent="${agentKey}"]`);
            if (modelInput) modelInput.value = state.config[agentKey].model || 'llama3:8b';
            
            // Trigger change event to show/hide API key input based on provider if we had that logic
        }
    };

    populateAgentSettings('MAB', 0);
    populateAgentSettings('SAB1', 1);
    populateAgentSettings('SAB2', 2);
    populateAgentSettings('SAB3', 3);

    // Load pre-instructions into textareas
    if (state.preInstructions.MAB) {
        dom.settings.preInstructionTextareas[0].value = state.preInstructions.MAB;
    }
    if (state.preInstructions.SAB1) {
        dom.settings.preInstructionTextareas[1].value = state.preInstructions.SAB1;
    }
    if (state.preInstructions.SAB2) {
        dom.settings.preInstructionTextareas[2].value = state.preInstructions.SAB2;
    }
    if (state.preInstructions.SAB3) {
        dom.settings.preInstructionTextareas[3].value = state.preInstructions.SAB3;
    }

    // Save button handlers
    dom.settings.saveButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            saveAgentConfig(btn.dataset.agent);
        });
    });

    // Fetch models handlers
    document.querySelectorAll('.fetch-models-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const agent = e.target.dataset.agent;
            fetchModels(agent);
        });
    });
}

// Switch Tab
function switchTab(tab) {
    // Remove active class from all tabs
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });

    // Add active class to selected tab
    document.getElementById(`${tab}-tab`).classList.add('active');
    document.querySelector(`.nav-item[data-tab="${tab}"]`).classList.add('active');

    // Update page title
    const titles = {
        mab: 'Campaign Mode',
        sab1: 'Research Chat - SAB1',
        sab2: 'Strategy Chat - SAB2',
        sab3: 'Content Chat - SAB3',
        settings: 'Settings',
        history: 'Session History'
    };
    dom.pageTitle.textContent = titles[tab] || 'NeuroDesk';

    state.currentTab = tab;
}

// Toggle Theme
function toggleTheme() {
    const body = document.body;
    if (body.classList.contains('light-mode')) {
        body.classList.remove('light-mode');
        dom.themeIcon.textContent = '🌙';
        localStorage.setItem('theme', 'dark');
    } else {
        body.classList.add('light-mode');
        dom.themeIcon.textContent = '☀️';
        localStorage.setItem('theme', 'light');
    }
}

// Start Timer
function startTimer() {
    state.timer.seconds = 0;
    state.timer.interval = setInterval(() => {
        state.timer.seconds++;
        updateTimerDisplay();
    }, 1000);
}

function updateTimerDisplay() {
    const hours = Math.floor(state.timer.seconds / 3600);
    const minutes = Math.floor((state.timer.seconds % 3600) / 60);
    const seconds = state.timer.seconds % 60;

    dom.activityTimer.textContent = `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
}

function pad(num) {
    return num.toString().padStart(2, '0');
}

// Add Message to Chat
function addMessageToChat(agent, sender, message) {
    const messagesDiv = dom.chatMessages[agent];
    const emoji = AGENT_EMOJIS[agent];
    const color = AGENT_COLORS[agent];
    const name = AGENT_NAMES[agent];

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${sender === 'user' ? 'user' : 'agent'} ${agent}`;

    let avatarHtml = '';
    if (sender === 'user') {
        avatarHtml = `<div class="chat-avatar">👤</div>`;
    } else {
        avatarHtml = `<div class="chat-avatar">${emoji}</div>`;
    }

    // Render markdown for agent/user messages
    let renderedContent = message;
    try {
        if (typeof marked !== 'undefined') {
            // Support both old and new marked versions
            renderedContent = (typeof marked.parse === 'function') ? marked.parse(message) : marked(message);
        } else {
            renderedContent = escapeHtml(message);
        }
    } catch (e) {
        console.error('Markdown rendering error:', e);
        renderedContent = escapeHtml(message);
    }

    messageElement.innerHTML = `
        ${avatarHtml}
        <div class="chat-content">
            <div class="message-text">${renderedContent}</div>
            <div class="chat-meta">
                <span class="agent-badge">${name}</span>
                <span class="timestamp">${timestamp}</span>
            </div>
        </div>
    `;

    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Add Activity Message
function addActivityMessage(agent, message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const messageElement = document.createElement('div');
    messageElement.className = `activity-message ${agent} ${type}`;

    let messageHtml = '';
    if (agent === 'mab') {
        messageHtml = `<div class="timestamp">${timestamp}</div><div class="message">🧠 MAB: ${escapeHtml(message)}</div>`;
    } else {
        messageHtml = `<div class="timestamp">${timestamp}</div><div class="message">${AGENT_EMOJIS[agent]} ${AGENT_NAMES[agent]}: ${escapeHtml(message)}</div>`;
    }

    messageElement.innerHTML = messageHtml;
    dom.activityMessages.appendChild(messageElement);
    dom.activityMessages.scrollTop = dom.activityMessages.scrollHeight;
}

// Send Campaign Goal
async function sendCampaignGoal(goal) {
    try {
        const response = await fetch('/campaign/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                goal: goal,
                platform: state.currentPlatform
            })
        });

        const data = await response.json();

        if (data.success) {
            const finalOutput = data.result.final_output || data.result;
            showOutput(finalOutput);
            addMessageToChat('mab', 'agent', finalOutput);
            addActivityMessage('mab', 'Campaign completed successfully!', 'success');
        } else {
            addActivityMessage('mab', `Error: ${data.result || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        addActivityMessage('mab', `Connection error: ${error.message}`, 'error');
    }
}

// Fetch Models
async function fetchModels(agent) {
    const provider = document.querySelector(`.provider-select[data-agent="${agent}"]`).value;
    const apiKey = document.querySelector(`.api-key-input[data-agent="${agent}"]`).value;
    const btn = document.querySelector(`.fetch-models-btn[data-agent="${agent}"]`);
    const container = document.querySelector(`.model-input-container[data-agent="${agent}"]`);
    const originalBtnText = btn.textContent;
    
    if (provider !== 'Ollama' && !apiKey) {
        alert('Please enter an API key to fetch models for ' + provider);
        return;
    }

    try {
        btn.textContent = 'Fetching...';
        btn.disabled = true;
        
        const response = await fetch(`/models?provider=${encodeURIComponent(provider)}&api_key=${encodeURIComponent(apiKey)}`);
        const data = await response.json();
        
        if (data.success && data.models && data.models.length > 0) {
            // Replace input with select
            const currentValue = document.querySelector(`.model-input[data-agent="${agent}"]`).value;
            let selectHtml = `<select class="model-input" data-agent="${agent}">`;
            data.models.forEach(model => {
                const selected = model === currentValue ? 'selected' : '';
                selectHtml += `<option value="${model}" ${selected}>${model}</option>`;
            });
            selectHtml += `</select>`;
            container.innerHTML = selectHtml;
            
            // Add custom styling since it's injected
            const select = container.querySelector('select');
            select.addEventListener('focus', () => select.style.borderColor = 'var(--accent-mab)');
            select.addEventListener('blur', () => select.style.borderColor = 'var(--bg-border)');
            alert(`Successfully fetched ${data.models.length} models for ${provider}`);
        } else {
            alert('Could not fetch models or no models returned. ' + (data.error || ''));
            // Ensure it's a text input
            if (container.querySelector('select')) {
                container.innerHTML = `<input type="text" class="model-input" data-agent="${agent}" value="" placeholder="Type model name manually" style="width: 100%; padding: 8px; background: var(--bg-surface); border: 1px solid var(--bg-border); border-radius: 4px; color: var(--text-primary); margin-top: 5px;"/>`;
            }
        }
    } catch (error) {
        alert('Error fetching models: ' + error.message);
        // Ensure it's a text input
        if (container.querySelector('select')) {
            container.innerHTML = `<input type="text" class="model-input" data-agent="${agent}" value="" placeholder="Type model name manually" style="width: 100%; padding: 8px; background: var(--bg-surface); border: 1px solid var(--bg-border); border-radius: 4px; color: var(--text-primary); margin-top: 5px;"/>`;
        }
    } finally {
        btn.textContent = originalBtnText;
        btn.disabled = false;
    }
}

// Send Chat Message
async function sendChatMessage(agent, message) {
    const endpoint = agent === 'mab' ? '/mab/chat' : `/sab${agent.slice(3)}/chat`;
    
    // Add to local history
    if (!state.messageHistory[agent]) state.messageHistory[agent] = [];
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                history: state.messageHistory[agent],
                session_id: state.currentSessionId
            })
        });

        const data = await response.json();

        if (data.success) {
            let resultText = data.result;
            
            // Check for auto-start trigger for MAB
            if (agent === 'mab' && resultText.includes('[START_CAMPAIGN]')) {
                // Remove the trigger from the displayed text
                resultText = resultText.replace('[START_CAMPAIGN]', '').trim();
                if (resultText) {
                    addMessageToChat(agent, 'agent', resultText);
                }
                
                // Automatically start the campaign
                addActivityMessage('mab', 'Auto-starting campaign...', 'info');
                sendCampaignGoal(message);
            } else {
                addMessageToChat(agent, 'agent', resultText);
            }
            
            state.messageHistory[agent].push(
                { role: 'user', content: message },
                { role: 'assistant', content: data.result } // store original with trigger so LLM remembers
            );
        } else {
            const errMsg = data.error || data.result || 'Unknown error';
            addMessageToChat(agent, 'agent', `Error: ${errMsg}`);
        }
    } catch (error) {
        addMessageToChat(agent, 'agent', `Connection error: ${error.message}`);
    }
}

// Show Output Modal
function showOutput(output) {
    const content = document.getElementById('output-content');
    
    // Render markdown for the campaign report
    try {
        if (typeof marked !== 'undefined') {
            content.innerHTML = (typeof marked.parse === 'function') ? marked.parse(output) : marked(output);
        } else {
            content.textContent = output;
        }
    } catch (e) {
        console.error('Markdown rendering error:', e);
        content.textContent = output;
    }

    dom.modal.output.style.display = 'flex';
}

// Copy Output
function copyOutput() {
    const content = document.getElementById('output-content').textContent;
    navigator.clipboard.writeText(content).then(() => {
        alert('Copied to clipboard!');
    });
}

// Download Markdown
function downloadMarkdown() {
    const content = document.getElementById('output-content').textContent;
    downloadFile('campaign.md', 'text/markdown', content);
}

// Download Text
function downloadText() {
    const content = document.getElementById('output-content').textContent;
    downloadFile('campaign.txt', 'text/plain', content);
}

// Download File Helper
function downloadFile(filename, mimeType, content) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Add Tool
function addTool() {
    const name = document.getElementById('tool-name').value.trim();
    const path = document.getElementById('tool-path').value.trim();
    const description = document.getElementById('tool-description').value.trim();
    const assignSelect = document.getElementById('tool-assign');
    const assignedTo = Array.from(assignSelect.selectedOptions).map(opt => opt.value);

    if (!name || !path) {
        alert('Please provide tool name and path');
        return;
    }

    fetch('/tools/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, path, description, assigned_to: assignedTo })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                alert(`Tool '${name}' registered successfully!`);
                dom.modal.addTool.style.display = 'none';
                document.getElementById('tool-name').value = '';
                document.getElementById('tool-path').value = '';
                document.getElementById('tool-description').value = '';
            }
        })
        .catch(error => {
            alert(`Error: ${error.message}`);
        });
}

// Handle Tool Action
function handleToolAction(toolName, action) {
    if (action === 'remove') {
        fetch(`/tools/${toolName}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert(`Tool '${toolName}' removed`);
                }
            });
    } else if (action === 'install') {
        // Search GitHub and install
        fetch('/tools')
            .then(r => r.json())
            .then(tools => {
                alert(`Installing ${toolName} from GitHub...`);
                // In real implementation, would search GitHub API and install
            });
    }
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Connect WebSocket
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/stream`;

    state.websocket = new WebSocket(wsUrl);

    state.websocket.onopen = () => {
        console.log('WebSocket connected');
    };

    state.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    state.websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    state.websocket.onclose = () => {
        console.log('WebSocket disconnected');
        // Auto-reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
    };
}

// Handle WebSocket Message
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'mab_thinking':
            addActivityMessage('mab', data.message);
            break;
        case 'tool_check':
            addActivityMessage('mab', data.message);
            break;
        case 'task_assign':
            addActivityMessage('mab', `${data.agent}: ${data.task}`);
            break;
        case 'sab_working':
        case 'sab1_working':
            addActivityMessage('sab1', data.message);
            break;
        case 'sab2_working':
            addActivityMessage('sab2', data.message);
            break;
        case 'sab3_working':
            addActivityMessage('sab3', data.message);
            break;
        case 'sab_done':
        case 'sab1_done':
            addActivityMessage('sab1', data.message, 'success');
            break;
        case 'sab2_done':
            addActivityMessage('sab2', data.message, 'success');
            break;
        case 'sab3_done':
            addActivityMessage('sab3', data.message, 'success');
            break;
        case 'final_output':
            showOutput(data.result);
            break;
        case 'error':
            addActivityMessage('mab', data.message, 'error');
            break;
        case 'status':
            console.log('Campaign status:', data);
            break;
    }
}

// Save Agent Configuration
function saveAgentConfig(agent) {
    const provider = document.querySelector(`.provider-select[data-agent="${agent}"]`).value;
    const apiKey = document.querySelector(`.api-key-input[data-agent="${agent}"]`).value;
    const model = document.querySelector(`.model-input[data-agent="${agent}"]`).value;
    const preInstruction = document.querySelector(`.pre-instruction-textarea[data-agent="${agent}"]`).value;

    // Get current config and update it
    const config = { ...state.config };
    config[agent] = { provider, api_key: apiKey, model };

    fetch('/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                alert(`Configuration for ${agent} saved!`);
            }
        });

    // Save pre-instructions
    if (state.preInstructions[agent]) {
        state.preInstructions[agent] = preInstruction;
        fetch('/pre-instructions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state.preInstructions)
        });
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);

// WebSocket send function
function sendWebSocketMessage(type, data = {}) {
    if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
        state.websocket.send(JSON.stringify({ type, ...data }));
    }
}

// --- Session Management ---

async function initSession() {
    // Load sessions first
    await fetchSessions();
    
    // Create new session if none exist
    if (!state.currentSessionId) {
        await createNewSession();
    }
}

async function fetchSessions() {
    try {
        const res = await fetch('/sessions');
        const data = await res.json();
        if (data.success && data.sessions.length > 0) {
            renderSessions(data.sessions);
            if (!state.currentSessionId) {
                // Keep the first session id as active without clearing the chat
                state.currentSessionId = data.sessions[0].id;
                await loadSession(data.sessions[0].id);
            }
        }
    } catch (e) {
        console.error("Failed to fetch sessions", e);
    }
}

function renderSessions(sessions) {
    if (!dom.history.list) return;
    
    dom.history.list.innerHTML = '';
    sessions.forEach(s => {
        const d = new Date(s.updated_at);
        const card = document.createElement('div');
        card.className = `session-card ${s.id === state.currentSessionId ? 'active' : ''}`;
        if (s.id === state.currentSessionId) {
            card.style.borderColor = 'var(--accent-mab)';
            card.style.boxShadow = 'var(--glow-mab)';
        }
        
        card.innerHTML = `
            <div class="session-info">
                <h3>${s.title}</h3>
                <p>${d.toLocaleDateString()} ${d.toLocaleTimeString()}</p>
            </div>
            <div class="session-actions">
                <button class="btn btn-sm btn-danger delete-session-btn" data-id="${s.id}">Delete</button>
            </div>
        `;
        
        card.addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-session-btn')) {
                deleteSession(s.id);
            } else {
                loadSession(s.id);
            }
        });
        
        dom.history.list.appendChild(card);
    });
}

async function createNewSession() {
    try {
        const res = await fetch('/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: "Campaign " + new Date().toLocaleString() })
        });
        const data = await res.json();
        if (data.success) {
            state.currentSessionId = data.session_id;
            clearAllChats();
            fetchSessions();
            switchTab('mab');
        }
    } catch (e) {
        console.error("Failed to create session", e);
    }
}

async function loadSession(sessionId) {
    state.currentSessionId = sessionId;
    try {
        const res = await fetch(`/sessions/${sessionId}/history`);
        const data = await res.json();
        
        if (data.success) {
            clearAllChats();
            
            const history = data.history;
            for (const [agentName, messages] of Object.entries(history)) {
                const agentId = agentName.toLowerCase();
                messages.forEach(msg => {
                    // Update state
                    state.messageHistory[agentId].push({
                        role: msg.role,
                        content: msg.content
                    });
                    
                    // Update DOM
                    if (msg.role === 'user') {
                        addMessageToChat(agentId, 'user', msg.content);
                    } else {
                        addMessageToChat(agentId, 'agent', msg.content);
                    }
                });
            }
            
            fetchSessions(); // re-render to update active styling
            switchTab('mab');
        }
    } catch (e) {
        console.error("Failed to load session", e);
    }
}

async function deleteSession(sessionId) {
    if (!confirm("Are you sure you want to delete this session?")) return;
    try {
        const res = await fetch(`/sessions/${sessionId}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            if (state.currentSessionId === sessionId) {
                state.currentSessionId = null;
                clearAllChats();
            }
            fetchSessions();
        }
    } catch (e) {
        console.error("Failed to delete session", e);
    }
}

function clearAllChats() {
    state.messageHistory = { mab: [], sab1: [], sab2: [], sab3: [] };
    Object.values(dom.chatMessages).forEach(container => {
        // Keep the initial greeting message if it exists, clear the rest
        const greeting = container.firstElementChild;
        container.innerHTML = '';
        if (greeting && greeting.classList.contains('agent')) {
             container.appendChild(greeting);
        }
    });
}

if (dom.history.newBtn) {
    dom.history.newBtn.addEventListener('click', createNewSession);
}
