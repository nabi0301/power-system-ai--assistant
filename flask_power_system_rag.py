#!/usr/bin/env python3
"""
Simple Flask-based Powe        <div class="header">
        <div class="header">
            <h1>🏦 IEEE 118-Bus Power System Analysis with RAG</h1>
            <p>Real-time database exploration with AI-enhanced responses and interactive visualizations</p>
        </div>        <h1>🏦 IEEE 118-Bus Power System Analysis with RAG</h1>
            <p>Real-time database exploration with AI-enhanced responses and interactive visualizations</p>
        </div>
        
        <div class="section visualization-section">
            <h3>📊 System Overview Visualizations</h3>
            <div class="chart-grid">
                <div class="chart-card">
                    <h4>Voltage Distribution</h4>
                    <canvas id="voltageChart"></canvas>
                </div>
                <div class="chart-card">
                    <h4>Loading Distribution</h4>
                    <canvas id="loadingChart"></canvas>
                </div>
                <div class="chart-card">
                    <h4>Generation vs Load</h4>
                    <canvas id="genLoadChart"></canvas>
                </div>
                <div class="chart-card">
                    <h4>Violations by Case</h4>
                    <canvas id="violationsChart"></canvas>
                </div>
            </div>
        </div>stem Visualization with RAG
Lightweight alternative to Dash with RAG capabilities
"""
from flask import Flask, render_template_string, request, jsonify
import sqlite3
import json
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
import plotly.io as pio
import math
from simple_rag import get_rag_response, initialize_rag
import sys
import os
import sqlite3
import pandas as pd
import numpy as np
import networkx as nx



app = Flask(__name__)

# Initialize RAG system
initialize_rag()

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Power System Visualization</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; margin-bottom: 30px; }
        .section { margin: 20px 0; padding: 15px; border-radius: 5px; }
        .chat-section { background-color: #f0f8ff; border: 1px solid #ddd; position: relative; }
        .query-section { background-color: #e8f5e8; }
        .chat-box { height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin: 10px 0; background: white; }
        .chat-toggle { position: absolute; top: 10px; right: 15px; background: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 12px; }
        .chat-toggle:hover { background: #0056b3; }
        .chat-content { transition: all 0.3s ease; }
        .chat-content.collapsed { display: none; }
        .chat-section.collapsed { min-height: 60px; }
        .message { margin: 5px 0; padding: 8px; border-radius: 5px; }
        .user-message { background-color: #e3f2fd; text-align: right; }
        .ai-message { background-color: #f0f8ff; }
        .rag-message { background-color: #e8f5e8; border-left: 4px solid #4caf50; }
        input[type="text"] { width: 70%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; margin-left: 5px; }
        button:hover { background-color: #0056b3; }
        .data-table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        .data-table th, .data-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .data-table th { background-color: #f2f2f2; }
        .stats { display: flex; justify-content: space-around; margin: 20px 0; }
        .stat-box { text-align: center; padding: 15px; background: #f8f9fa; border-radius: 5px; flex: 1; margin: 0 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏭 Power System Visualization</h1>
            <p>AI-enhanced power system analysis with real-time database exploration</p>
        </div>
        
        <div class="section chat-section" id="chat-section">
            <button class="chat-toggle" onclick="toggleChat()" id="chat-toggle">Hide Chat</button>
            <h3>🧠 AI Assistant</h3>
            <div class="chat-content" id="chat-content">
                <p>Ask questions about the power system data. The AI will search the database and provide data-grounded responses with case-wise analysis.</p>
                
                <div class="chat-box" id="chat-messages">
                <div class="message ai-message">
                    👋 Hi! I'm your Power System AI Assistant with advanced power system visualization capabilities. I can create sophisticated charts including:
                    <br><strong> Critical Analysis:</strong>
                    <br>• "Show me critical path flow maps" - Transmission corridor visualization
                    <br>• "Create N-1 reliability heat matrix" - Contingency impact analysis
                    <br>• "Generate vulnerability maps" - Geographic risk assessment
                    <br><strong>📊 Capacity & Performance:</strong>
                    <br>• "Show capacity utilization sunburst chart" - Hierarchical system view
                    <br>• "Create violin plot rating comparison" - SLR vs DLR distributions
                    <br>• "Display loading duration curves" - Utilization patterns
                    <br><strong>⚖️ Decision Support:</strong>
                    <br>• "Show upgrade priority quadrant chart" - Investment guidance
                    <br>• "Create reliability capacity trade-off curve" - Optimal operating points
                    <br>• "Generate scenario comparison radar" - What-if analysis
                    <br><br><em>Enable visualization above and ask for any of these advanced charts!</em>
                </div>
            </div>
            
                <div id="analysis-visualization" style="display: none; margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; border: 1px solid #ddd;">
                    <h4 style="margin: 0 0 10px 0; color: #333;">📈 Analysis Visualization</h4>
                    <div id="analysis-chart" style="width: 100%; height: 400px;"></div>
                </div>
            
                <div>
                    <input type="text" id="user-input" placeholder="Ask about power systems..." onkeydown="handleKeyPress(event)" onclick="console.log('Input clicked!')">
                    <button onclick="sendMessage()">Send</button>
                    <button onclick="clearChat()">Clear</button>
                    <button onclick="testChat()" style="background: #28a745; color: white; margin-left: 10px;">🧪 Test Chat</button>
                    <button onclick="console.log('Debug: Functions check - sendMessage:', typeof sendMessage, 'handleKeyPress:', typeof handleKeyPress)" style="background: #ffc107; color: black; margin-left: 10px;">🐛 Debug</button>
                </div>
            </div>
        </div>
        
        <div class="section query-section">
            <h3>🔍 Case-wise Analysis Queries</h3>
            <p>Click any button to see real data analysis across multiple cases:</p>
            <button onclick="executeQuery('case_list')">Available Cases</button>
            <button onclick="executeQuery('contingency_analysis')">Contingency Cases</button>
            <button onclick="executeQuery('case_comparison')">Case Comparison</button>
            <button onclick="executeQuery('high_load_buses')">High Load Buses</button>
            <button onclick="executeQuery('overloaded_lines')">Overloaded Lines</button>
            <button onclick="executeQuery('voltage_violations')">Voltage Violations</button>
            <button onclick="executeQuery('generators')">Generator Buses</button>
            <button onclick="executeQuery('slr_dlr_comparison')">SLR vs DLR</button>
            <button onclick="executeQuery('worst_violations')">Worst Violations</button>
            <button onclick="executeQuery('efficiency_analysis')">DLR Efficiency</button>
            
            <div id="query-results" style="margin-top: 20px;"></div>
        </div>
    </div>

    <script>
        let networkGraphs = {};
        
        // Analysis Visualization Functions
        let analysisVisualizationEnabled = false;
        
        function toggleAnalysisVisualization() {
            console.log('Toggle function called!'); // Debug log
            analysisVisualizationEnabled = !analysisVisualizationEnabled;
            const vizContainer = document.getElementById('analysis-visualization');
            const toggleBtn = document.getElementById('viz-toggle-btn');
            
            console.log('Elements found:', vizContainer, toggleBtn); // Debug log
            
            if (analysisVisualizationEnabled) {
                if (vizContainer) vizContainer.style.display = 'block';
                if (toggleBtn) {
                    toggleBtn.textContent = '📊 Disable Analysis Visualization';
                    toggleBtn.style.background = '#f44336';
                }
                console.log('Visualization enabled'); // Debug log
            } else {
                if (vizContainer) vizContainer.style.display = 'none';
                if (toggleBtn) {
                    toggleBtn.textContent = '📊 Enable Analysis Visualization';
                    toggleBtn.style.background = '#4CAF50';
                }
                console.log('Visualization disabled'); // Debug log
            }
        }
        
        function visualizeAnalysisData(response, context) {
            if (!analysisVisualizationEnabled) return;
            
            try {
                // Parse the context data for visualization
                if (context && context.length > 0) {
                    const data = context;
                    
                    // Determine chart type based on response content
                    if (response.includes('violation') || response.includes('VIO')) {
                        createViolationChart(data);
                    } else if (response.includes('efficiency') || response.includes('improvement')) {
                        createEfficiencyChart(data);
                    } else if (response.includes('case') && response.includes('comparison')) {
                        createCaseComparisonChart(data);
                    } else if (response.includes('contingency')) {
                        createContingencyChart(data);
                    } else {
                        createGeneralDataChart(data);
                    }
                }
            } catch (error) {
                console.error('Error creating analysis visualization:', error);
            }
        }
        
        function createViolationChart(data) {
            const traces = [];
            
            if (data.length > 0 && data[0].avg_slr_violation !== undefined) {
                // SLR vs DLR violations
                const slrViolations = data.map(d => d.avg_slr_violation || 0);
                const dlrViolations = data.map(d => d.avg_dlr_violation || 0);
                const labels = data.map(d => `Case ${d.base_case_id}-${d.contingency_case_id}`);
                
                traces.push({
                    x: labels,
                    y: slrViolations,
                    type: 'bar',
                    name: 'SLR Violations',
                    marker: { color: '#ff6b6b' }
                });
                
                traces.push({
                    x: labels,
                    y: dlrViolations,
                    type: 'bar',
                    name: 'DLR Violations',
                    marker: { color: '#4ecdc4' }
                });
            } else if (data.length > 0 && data[0].VIO !== undefined) {
                // Individual violation data
                const violations = data.map(d => d.VIO);
                const labels = data.map((d, i) => `Line ${d.From_Bus}-${d.To_Bus}` || `Item ${i+1}`);
                
                traces.push({
                    x: labels,
                    y: violations,
                    type: 'bar',
                    name: 'Violations (%)',
                    marker: { color: '#ff6b6b' }
                });
            }
            
            const layout = {
                title: 'Violation Analysis',
                xaxis: { title: 'Cases/Lines' },
                yaxis: { title: 'Violation (%)' },
                margin: { t: 40, b: 60, l: 60, r: 40 }
            };
            
            Plotly.newPlot('analysis-chart', traces, layout);
        }
        
        function createEfficiencyChart(data) {
            if (data.length === 0) return;
            
            const improvements = data.map(d => d.avg_rating_improvement || 0);
            const reductions = data.map(d => d.avg_violation_reduction || 0);
            const labels = data.map(d => `Case ${d.base_case_id}-${d.contingency_case_id}`);
            
            const trace1 = {
                x: labels,
                y: improvements,
                type: 'bar',
                name: 'Rating Improvement',
                marker: { color: '#4CAF50' }
            };
            
            const trace2 = {
                x: labels,
                y: reductions,
                type: 'bar',
                name: 'Violation Reduction',
                yaxis: 'y2',
                marker: { color: '#2196F3' }
            };
            
            const layout = {
                title: 'DLR Efficiency Analysis',
                xaxis: { title: 'Cases' },
                yaxis: { title: 'Rating Improvement', side: 'left' },
                yaxis2: { title: 'Violation Reduction (%)', side: 'right', overlaying: 'y' },
                margin: { t: 40, b: 60, l: 60, r: 60 }
            };
            
            Plotly.newPlot('analysis-chart', [trace1, trace2], layout);
        }
        
        function createCaseComparisonChart(data) {
            if (data.length === 0) return;
            
            const totalBuses = data.map(d => d.total_buses || 0);
            const totalLoad = data.map(d => d.total_load || 0);
            const avgVoltage = data.map(d => d.avg_voltage || 0);
            const labels = data.map(d => `Case ${d.base_case_id}`);
            
            const trace1 = {
                x: labels,
                y: totalBuses,
                type: 'bar',
                name: 'Total Buses',
                marker: { color: '#FF9800' }
            };
            
            const trace2 = {
                x: labels,
                y: totalLoad,
                type: 'bar',
                name: 'Total Load (MW)',
                yaxis: 'y2',
                marker: { color: '#9C27B0' }
            };
            
            const layout = {
                title: 'Case Comparison Analysis',
                xaxis: { title: 'Cases' },
                yaxis: { title: 'Total Buses', side: 'left' },
                yaxis2: { title: 'Total Load (MW)', side: 'right', overlaying: 'y' },
                margin: { t: 40, b: 60, l: 60, r: 60 }
            };
            
            Plotly.newPlot('analysis-chart', [trace1, trace2], layout);
        }
        
        function createContingencyChart(data) {
            if (data.length === 0) return;
            
            const affectedBranches = data.map(d => d.affected_branches || 0);
            const labels = data.map(d => `${d.base_case_id}-${d.contingency_case_id}`);
            
            const trace = {
                x: labels,
                y: affectedBranches,
                type: 'bar',
                name: 'Affected Branches',
                marker: { color: '#E91E63' }
            };
            
            const layout = {
                title: 'Contingency Impact Analysis',
                xaxis: { title: 'Contingency Cases' },
                yaxis: { title: 'Affected Branches' },
                margin: { t: 40, b: 60, l: 60, r: 40 }
            };
            
            Plotly.newPlot('analysis-chart', [trace], layout);
        }
        
        function createGeneralDataChart(data) {
            if (data.length === 0) return;
            
            // Create a simple table visualization for general data
            const keys = Object.keys(data[0]);
            const numericKeys = keys.filter(key => typeof data[0][key] === 'number');
            
            if (numericKeys.length > 0) {
                const firstNumericKey = numericKeys[0];
                const values = data.map(d => d[firstNumericKey]);
                const labels = data.map((d, i) => `Item ${i + 1}`);
                
                const trace = {
                    x: labels,
                    y: values,
                    type: 'bar',
                    name: firstNumericKey,
                    marker: { color: '#607D8B' }
                };
                
                const layout = {
                    title: 'Data Analysis',
                    xaxis: { title: 'Items' },
                    yaxis: { title: firstNumericKey },
                    margin: { t: 40, b: 60, l: 60, r: 40 }
                };
                
                Plotly.newPlot('analysis-chart', [trace], layout);
            }
        }
                vizContainer.style.display = 'block';
                toggleBtn.textContent = '📊 Disable Analysis Visualization';
                toggleBtn.style.background = '#f44336';
            } else {
                vizContainer.style.display = 'none';
                toggleBtn.textContent = '📊 Enable Analysis Visualization';
                toggleBtn.style.background = '#4CAF50';
            }
        }
        
        function visualizeAnalysisData(response, context) {
            if (!analysisVisualizationEnabled) return;
            
            try {
                // Parse the context data for visualization
                if (context && context.length > 0) {
                    const data = context;
                    
                    // Determine chart type based on response content
                    if (response.includes('violation') || response.includes('VIO')) {
                        createViolationChart(data);
                    } else if (response.includes('efficiency') || response.includes('improvement')) {
                        createEfficiencyChart(data);
                    } else if (response.includes('case') && response.includes('comparison')) {
                        createCaseComparisonChart(data);
                    } else if (response.includes('contingency')) {
                        createContingencyChart(data);
                    } else {
                        createGeneralDataChart(data);
                    }
                }
            } catch (error) {
                console.error('Error creating analysis visualization:', error);
            }
        }
        
        function createViolationChart(data) {
            const traces = [];
            
            if (data.length > 0 && data[0].avg_slr_violation !== undefined) {
                // SLR vs DLR violations
                const slrViolations = data.map(d => d.avg_slr_violation || 0);
                const dlrViolations = data.map(d => d.avg_dlr_violation || 0);
                const labels = data.map(d => `Case ${d.base_case_id}-${d.contingency_case_id}`);
                
                traces.push({
                    x: labels,
                    y: slrViolations,
                    type: 'bar',
                    name: 'SLR Violations',
                    marker: { color: '#ff6b6b' }
                });
                
                traces.push({
                    x: labels,
                    y: dlrViolations,
                    type: 'bar',
                    name: 'DLR Violations',
                    marker: { color: '#4ecdc4' }
                });
            } else if (data.length > 0 && data[0].VIO !== undefined) {
                // Individual violation data
                const violations = data.map(d => d.VIO);
                const labels = data.map((d, i) => `Line ${d.From_Bus}-${d.To_Bus}` || `Item ${i+1}`);
                
                traces.push({
                    x: labels,
                    y: violations,
                    type: 'bar',
                    name: 'Violations (%)',
                    marker: { color: '#ff6b6b' }
                });
            }
            
            const layout = {
                title: 'Violation Analysis',
                xaxis: { title: 'Cases/Lines' },
                yaxis: { title: 'Violation (%)' },
                margin: { t: 40, b: 60, l: 60, r: 40 }
            };
            
            Plotly.newPlot('analysis-chart', traces, layout);
        }
        
        function createEfficiencyChart(data) {
            if (data.length === 0) return;
            
            const improvements = data.map(d => d.avg_rating_improvement || 0);
            const reductions = data.map(d => d.avg_violation_reduction || 0);
            const labels = data.map(d => `Case ${d.base_case_id}-${d.contingency_case_id}`);
            
            const trace1 = {
                x: labels,
                y: improvements,
                type: 'bar',
                name: 'Rating Improvement',
                marker: { color: '#4CAF50' }
            };
            
            const trace2 = {
                x: labels,
                y: reductions,
                type: 'bar',
                name: 'Violation Reduction',
                yaxis: 'y2',
                marker: { color: '#2196F3' }
            };
            
            const layout = {
                title: 'DLR Efficiency Analysis',
                xaxis: { title: 'Cases' },
                yaxis: { title: 'Rating Improvement', side: 'left' },
                yaxis2: { title: 'Violation Reduction (%)', side: 'right', overlaying: 'y' },
                margin: { t: 40, b: 60, l: 60, r: 60 }
            };
            
            Plotly.newPlot('analysis-chart', [trace1, trace2], layout);
        }
        
        function createCaseComparisonChart(data) {
            if (data.length === 0) return;
            
            const totalBuses = data.map(d => d.total_buses || 0);
            const totalLoad = data.map(d => d.total_load || 0);
            const avgVoltage = data.map(d => d.avg_voltage || 0);
            const labels = data.map(d => `Case ${d.base_case_id}`);
            
            const trace1 = {
                x: labels,
                y: totalBuses,
                type: 'bar',
                name: 'Total Buses',
                marker: { color: '#FF9800' }
            };
            
            const trace2 = {
                x: labels,
                y: totalLoad,
                type: 'bar',
                name: 'Total Load (MW)',
                yaxis: 'y2',
                marker: { color: '#9C27B0' }
            };
            
            const layout = {
                title: 'Case Comparison Analysis',
                xaxis: { title: 'Cases' },
                yaxis: { title: 'Total Buses', side: 'left' },
                yaxis2: { title: 'Total Load (MW)', side: 'right', overlaying: 'y' },
                margin: { t: 40, b: 60, l: 60, r: 60 }
            };
            
            Plotly.newPlot('analysis-chart', [trace1, trace2], layout);
        }
        
        function createContingencyChart(data) {
            if (data.length === 0) return;
            
            const affectedBranches = data.map(d => d.affected_branches || 0);
            const labels = data.map(d => `${d.base_case_id}-${d.contingency_case_id}`);
            
            const trace = {
                x: labels,
                y: affectedBranches,
                type: 'bar',
                name: 'Affected Branches',
                marker: { color: '#E91E63' }
            };
            
            const layout = {
                title: 'Contingency Impact Analysis',
                xaxis: { title: 'Contingency Cases' },
                yaxis: { title: 'Affected Branches' },
                margin: { t: 40, b: 60, l: 60, r: 40 }
            };
            
            Plotly.newPlot('analysis-chart', [trace], layout);
        }
        
        function createGeneralDataChart(data) {
            if (data.length === 0) return;
            
            // Create a simple table visualization for general data
            const keys = Object.keys(data[0]);
            const numericKeys = keys.filter(key => typeof data[0][key] === 'number');
            
            if (numericKeys.length > 0) {
                const firstNumericKey = numericKeys[0];
                const values = data.map(d => d[firstNumericKey]);
                const labels = data.map((d, i) => `Item ${i + 1}`);
                
                const trace = {
                    x: labels,
                    y: values,
                    type: 'bar',
                    name: firstNumericKey,
                    marker: { color: '#607D8B' }
                };
                
                const layout = {
                    title: 'Data Analysis',
                    xaxis: { title: 'Items' },
                    yaxis: { title: firstNumericKey },
                    margin: { t: 40, b: 60, l: 60, r: 40 }
                };
                
                Plotly.newPlot('analysis-chart', [trace], layout);
            }
        }
        
        function testChat() {
            console.log('Test chat function called!');
            addMessage('Testing chat functionality...', 'user');
            
            // Test API call
            fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: 'show me available cases'})
            })
            .then(response => {
                console.log('Test API response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Test API response data:', data);
                if (data.rag_response) {
                    addMessage(data.rag_response, 'rag');
                } else if (data.ai_response) {
                    addMessage(data.ai_response, 'ai');
                } else {
                    addMessage('No response from API', 'ai');
                }
            })
            .catch(error => {
                console.error('Test API error:', error);
                addMessage('Test failed: ' + error.message, 'ai');
            });
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                event.preventDefault(); // Prevent form submission if in a form
                sendMessage();
            }
        }
        
        function sendMessage() {
            console.log('sendMessage() called'); // Debug log
            
            try {
                const input = document.getElementById('user-input');
                if (!input) {
                    console.error('Input element not found!');
                    return;
                }
                
                const message = input.value.trim();
                console.log('Message:', message); // Debug log
                
                if (!message) {
                    console.log('Empty message, returning'); // Debug log
                    // Focus back on input
                    input.focus();
                    return;
                }
                
                // Add user message to chat
                addMessage(message, 'user');
                
                // Clear input and focus back
                input.value = '';
                input.focus();
                
                // Add loading message
                addMessage('Thinking...', 'ai');
                
                // Send to server
                console.log('Sending message to server...'); // Debug log
                fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                })
                .then(response => {
                    console.log('Server response status:', response.status); // Debug log
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Server response data:', data); // Debug log
                    
                    // Remove the "Thinking..." message
                    const chatBox = document.getElementById('chat-messages');
                    const lastMessage = chatBox.lastElementChild;
                    if (lastMessage && lastMessage.textContent.includes('Thinking...')) {
                        chatBox.removeChild(lastMessage);
                    }
                    
                    if (data.rag_response) {
                        addMessage(data.rag_response, 'rag');
                        // Visualize the analysis data if available
                        if (typeof visualizeAnalysisData === 'function') {
                            visualizeAnalysisData(data.rag_response, data.context);
                        }
                    } else if (data.ai_response) {
                        addMessage(data.ai_response, 'ai');
                    } else {
                        addMessage('No response available', 'ai');
                    }
                })
                .catch(error => {
                    console.error('Fetch error:', error); // Debug log
                    
                    // Remove the "Thinking..." message
                    const chatBox = document.getElementById('chat-messages');
                    const lastMessage = chatBox.lastElementChild;
                    if (lastMessage && lastMessage.textContent.includes('Thinking...')) {
                        chatBox.removeChild(lastMessage);
                    }
                    
                    addMessage('Error: Unable to get response. Please try again.', 'ai');
                });
                
            } catch (error) {
                console.error('SendMessage error:', error);
                addMessage('Error: Something went wrong. Please try again.', 'ai');
            }
        }
        
        function addMessage(message, type) {
            const chatBox = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + type + '-message';
            
            if (type === 'user') {
                messageDiv.textContent = 'You: ' + message;
            } else if (type === 'rag') {
                messageDiv.innerHTML = '🧠 <strong>AI Response:</strong><br>' + message.replace(/\\n/g, '<br>');
            } else {
                messageDiv.innerHTML = '🤖 <strong>AI:</strong><br>' + message.replace(/\\n/g, '<br>');
            }
            
            chatBox.appendChild(messageDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        function clearChat() {
            const chatBox = document.getElementById('chat-messages');
            chatBox.innerHTML = '<div class="message ai-message">Chat cleared. Ask me anything about the power system!</div>';
        }
        
        function executeQuery(queryType) {
            fetch('/api/query/' + queryType)
                .then(response => response.json())
                .then(data => {
                    displayQueryResults(data, queryType);
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('query-results').innerHTML = '<p style="color: red;">Error executing query</p>';
                });
        }
        
        function displayQueryResults(data, queryType) {
            const resultsDiv = document.getElementById('query-results');
            
            if (!data.results || data.results.length === 0) {
                resultsDiv.innerHTML = '<p>No results found for this query.</p>';
                return;
            }
            
            let html = '<h4>' + data.title + '</h4>';
            html += '<table class="data-table"><thead><tr>';
            
            // Create header
            const keys = Object.keys(data.results[0]);
            keys.forEach(key => {
                html += '<th>' + key + '</th>';
            });
            html += '</tr></thead><tbody>';
            
            // Create rows
            data.results.forEach(row => {
                html += '<tr>';
                keys.forEach(key => {
                    let value = row[key];
                    if (typeof value === 'number') {
                        value = Number(value).toFixed(3);
                    }
                    html += '<td>' + value + '</td>';
                });
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            resultsDiv.innerHTML = html;
        }
        
        function toggleChat() {
            const chatContent = document.getElementById('chat-content');
            const chatSection = document.getElementById('chat-section');
            const toggleButton = document.getElementById('chat-toggle');
            
            if (chatContent.classList.contains('collapsed')) {
                // Show chat
                chatContent.classList.remove('collapsed');
                chatSection.classList.remove('collapsed');
                toggleButton.textContent = 'Hide Chat';
            } else {
                // Hide chat
                chatContent.classList.add('collapsed');
                chatSection.classList.add('collapsed');
                toggleButton.textContent = 'Show Chat';
            }
        }
        
        // Initialize when page loads
        window.addEventListener('DOMContentLoaded', function() {
            console.log('Page loaded, initializing chat interface...');
            
            // Ensure input field is ready and focused
            const input = document.getElementById('user-input');
            if (input) {
                input.focus();
                console.log('Input field found and focused');
                
                // Add additional enter key handler as backup
                input.addEventListener('keydown', function(event) {
                    if (event.key === 'Enter') {
                        event.preventDefault();
                        sendMessage();
                    }
                });
            } else {
                console.error('Input field not found!');
            }
            
            // Test if functions are available
            if (typeof sendMessage === 'function') {
                console.log('sendMessage function is available');
            } else {
                console.error('sendMessage function not found!');
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/system_stats')
def system_stats():
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            COUNT(*) as total_buses,
            ROUND(AVG(VM), 3) as avg_voltage,
            ROUND(SUM(PD), 1) as total_load_mw,
            ROUND(SUM(PG), 1) as total_generation_mw
        FROM BaseBusData 
        WHERE base_case_id = 0;
        """)
        bus_stats = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM BaseBranchData WHERE base_case_id = 0;")
        branch_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_buses': bus_stats[0],
            'total_branches': branch_count,
            'total_load': bus_stats[2],
            'avg_voltage': bus_stats[1]
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        print(f"Chat request received: '{user_message}'")  # Debug log
        
        # Try RAG response first
        try:
            rag_response, context = get_rag_response(user_message)
            print(f"RAG response: {bool(rag_response)}, Context length: {len(context) if context else 0}")  # Debug log
        except Exception as rag_error:
            print(f"RAG error: {rag_error}")  # Debug log
            rag_response, context = None, []
        
        if rag_response:
            return jsonify({
                'rag_response': rag_response,
                'context': context
            })
        else:
            # Fallback to simple response
            return jsonify({
                'ai_response': f"I understand you're asking about '{user_message}'. Try asking about specific topics like 'high load buses', 'overloaded lines', or 'system summary'.",
                'context': context
            })
            
    except Exception as e:
        print(f"Chat endpoint error: {e}")  # Debug log
        return jsonify({'error': str(e)})

@app.route('/api/query/<query_type>')
def execute_query(query_type):
    try:
        conn = sqlite3.connect('data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        queries = {
            'case_list': {
                'title': 'Available Base Cases',
                'query': """
                SELECT DISTINCT base_case_id, 
                       COUNT(*) as total_buses,
                       MIN(BUS_NUMBER) as min_bus,
                       MAX(BUS_NUMBER) as max_bus,
                       ROUND(AVG(VM), 3) as avg_voltage,
                       ROUND(SUM(PD), 1) as total_load
                FROM BaseBusData 
                GROUP BY base_case_id
                ORDER BY base_case_id
                LIMIT 20;
                """
            },
            'contingency_analysis': {
                'title': 'Contingency Analysis Summary',
                'query': """
                SELECT DISTINCT s.base_case_id, s.contingency_case_id,
                       COUNT(*) as affected_branches,
                       ROUND(AVG(s.VIO), 2) as avg_slr_violation,
                       ROUND(AVG(d.VIO), 2) as avg_dlr_violation,
                       COUNT(CASE WHEN s.VIO > 100 THEN 1 END) as slr_overloads,
                       COUNT(CASE WHEN d.VIO > 100 THEN 1 END) as dlr_overloads
                FROM SLR_Branches s
                LEFT JOIN DLR_Branches d ON s.base_case_id = d.base_case_id 
                    AND s.contingency_case_id = d.contingency_case_id
                    AND s.From_Bus = d.From_Bus AND s.To_Bus = d.To_Bus
                GROUP BY s.base_case_id, s.contingency_case_id
                ORDER BY s.base_case_id, s.contingency_case_id
                LIMIT 15;
                """
            },
            'case_comparison': {
                'title': 'Case-by-Case System Comparison',
                'query': """
                SELECT base_case_id,
                       COUNT(*) as total_buses,
                       ROUND(AVG(VM), 4) as avg_voltage,
                       ROUND(SUM(PD), 1) as total_load_mw,
                       ROUND(SUM(PG), 1) as total_generation_mw,
                       COUNT(CASE WHEN VM < 0.95 OR VM > 1.05 THEN 1 END) as voltage_violations
                FROM BaseBusData 
                GROUP BY base_case_id
                ORDER BY base_case_id
                LIMIT 10;
                """
            },
            'high_load_buses': {
                'title': 'High Load Buses Across Cases',
                'query': """
                SELECT base_case_id, BUS_NUMBER, 
                       ROUND(PD, 1) as Load_MW, 
                       ROUND(VM, 3) as Voltage_pu, BASE_KV
                FROM BaseBusData 
                WHERE PD > 50
                ORDER BY base_case_id, PD DESC
                LIMIT 15;
                """
            },
            'overloaded_lines': {
                'title': 'Overloaded Lines Across Cases',
                'query': """
                SELECT base_case_id, From_Bus, To_Bus, 
                       ROUND(MVA, 1) as Flow_MVA, 
                       ROUND(RATE, 1) as Rating_MVA, 
                       ROUND((MVA/RATE*100), 1) as Loading_Percent
                FROM BaseBranchData 
                WHERE RATE > 0 AND (MVA/RATE) > 0.8
                ORDER BY base_case_id, (MVA/RATE) DESC
                LIMIT 15;
                """
            },
            'voltage_violations': {
                'title': 'Voltage Violations Across Cases',
                'query': """
                SELECT base_case_id, BUS_NUMBER, 
                       ROUND(VM, 3) as Voltage_pu, BASE_KV,
                       CASE 
                           WHEN VM < 0.95 THEN 'Low Voltage'
                           WHEN VM > 1.05 THEN 'High Voltage'
                       END as Violation_Type
                FROM BaseBusData 
                WHERE (VM < 0.95 OR VM > 1.05)
                ORDER BY base_case_id, ABS(VM - 1.0) DESC
                LIMIT 15;
                """
            },
            'generators': {
                'title': 'Generator Buses Across Cases',
                'query': """
                SELECT base_case_id, BUS_NUMBER, 
                       ROUND(PG, 1) as Generation_MW, 
                       ROUND(VM, 3) as Voltage_pu, BASE_KV
                FROM BaseBusData 
                WHERE PG > 0
                ORDER BY base_case_id, PG DESC
                LIMIT 15;
                """
            },
            'slr_dlr_comparison': {
                'title': 'SLR vs DLR Comparison Across Cases',
                'query': """
                SELECT s.base_case_id, s.contingency_case_id, s.From_Bus, s.To_Bus, 
                       ROUND(s.RATE, 1) as SLR_Rating, 
                       ROUND(d.RATE, 1) as DLR_Rating,
                       ROUND((d.RATE - s.RATE), 1) as Improvement_MVA,
                       ROUND(s.VIO, 1) as SLR_Violation, 
                       ROUND(d.VIO, 1) as DLR_Violation
                FROM SLR_Branches s
                JOIN DLR_Branches d ON s.From_Bus = d.From_Bus 
                    AND s.To_Bus = d.To_Bus 
                    AND s.base_case_id = d.base_case_id
                    AND s.contingency_case_id = d.contingency_case_id
                WHERE d.RATE > s.RATE
                ORDER BY s.base_case_id, s.contingency_case_id, (d.RATE - s.RATE) DESC
                LIMIT 20;
                """
            },
            'worst_violations': {
                'title': 'Critical Violations Across Cases',
                'query': """
                SELECT s.base_case_id, s.contingency_case_id, s.From_Bus, s.To_Bus,
                       ROUND(s.VIO, 1) as SLR_Violation, 
                       ROUND(d.VIO, 1) as DLR_Violation,
                       ROUND((s.VIO - d.VIO), 1) as Violation_Reduction
                FROM SLR_Branches s
                JOIN DLR_Branches d ON s.From_Bus = d.From_Bus 
                    AND s.To_Bus = d.To_Bus 
                    AND s.base_case_id = d.base_case_id
                    AND s.contingency_case_id = d.contingency_case_id
                WHERE s.VIO > 100 OR d.VIO > 100
                ORDER BY GREATEST(s.VIO, d.VIO) DESC
                LIMIT 15;
                """
            },
            'efficiency_analysis': {
                'title': 'DLR Efficiency Analysis by Case',
                'query': """
                SELECT s.base_case_id, s.contingency_case_id,
                       COUNT(*) as total_lines,
                       ROUND(AVG(d.RATE - s.RATE), 2) as avg_rating_improvement,
                       ROUND(MAX(d.RATE - s.RATE), 2) as max_rating_improvement,
                       COUNT(CASE WHEN d.RATE > s.RATE THEN 1 END) as lines_improved,
                       ROUND(AVG(s.VIO - d.VIO), 2) as avg_violation_reduction
                FROM SLR_Branches s
                JOIN DLR_Branches d ON s.From_Bus = d.From_Bus 
                    AND s.To_Bus = d.To_Bus 
                    AND s.base_case_id = d.base_case_id
                    AND s.contingency_case_id = d.contingency_case_id
                GROUP BY s.base_case_id, s.contingency_case_id
                HAVING COUNT(*) > 10
                ORDER BY avg_rating_improvement DESC
                LIMIT 10;
                """
            }
        }
        
        if query_type not in queries:
            return jsonify({'error': 'Unknown query type'})
        
        query_info = queries[query_type]
        cursor.execute(query_info['query'])
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'title': query_info['title'],
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/network_data/<network_type>/<base_case>')
@app.route('/api/network_data/<network_type>/<base_case>/<contingency>')
def get_network_data(network_type, base_case, contingency=None):
    try:
        # Use direct database access for network data generation
        return get_data_viz_network(network_type, base_case, contingency)
    except Exception as e:
        return jsonify({'error': str(e), 'nodes': [], 'edges': []})

def get_data_viz_network(network_type, base_case, contingency=None):
    """Generate network data using direct database access with exact styling"""
    try:
        conn = sqlite3.connect('data.db')
        tripped_branch_info = None
        case_id = None
        
        # Map our network types to database case types
        if network_type == 'base':
            title = "Base Case"
            buses, branches = load_base_case_data(conn, base_case)
            case_id = DEFAULT_BASE_CASE_ID
        elif network_type == 'contingency':
            title = "Contingency Case"
            buses, branches = load_contingency_case_data(conn, base_case, contingency)
            case_id = int(contingency) if contingency else 1
            # Get tripped branch information for contingency cases
            if contingency and int(contingency) in CONTINGENCY_BRANCH_MAPPING:
                tripped_branch_id = CONTINGENCY_BRANCH_MAPPING[int(contingency)]
                tripped_branch_info = get_tripped_branch_info(conn, tripped_branch_id)
        elif network_type == 'slr':
            title = "SLR"
            buses, branches = load_slr_case_data(conn, base_case, contingency)
            # Use the actual SLR case ID mapping
            case_id = SLR_CASE_MAPPING.get(int(contingency), SLR_CASE_MAPPING[1]) if contingency else SLR_CASE_MAPPING[1]
        elif network_type == 'dlr':
            title = "DLR"
            buses, branches = load_dlr_case_data(conn, base_case, contingency)
            # Use the actual DLR case ID mapping
            case_id = DLR_CASE_MAPPING.get(int(contingency), DLR_CASE_MAPPING[1]) if contingency else DLR_CASE_MAPPING[1]
        else:
            return jsonify({'error': 'Invalid network type'})
        
        # Create the figure using direct database access instead of data_viz_fall
        fig = create_network_graph_direct(buses, branches, title, case_id, tripped_branch_info)
        
        # Convert Plotly figure to our JSON format
        fig_json = fig.to_dict()
        
        conn.close()
        return jsonify({
            'plotly_figure': fig_json,
            'nodes': extract_nodes_from_figure(fig_json),
            'edges': extract_edges_from_figure(fig_json)
        })
        
    except Exception as e:
        print(f"Error in get_data_viz_network: {e}")
        return jsonify({'error': str(e), 'nodes': [], 'edges': []})

def create_base_network_data(conn, base_case):
    try:
        # Get bus data
        bus_query = """
        SELECT BUS_NUMBER, VM, VA as ANGLE, PD, QD, 0.0 as GS, 0.0 as BS, 1 as AREA, 1 as ZONE, 1.1 as VM_MAX, 0.9 as VM_MIN, BASE_KV as BASEKV
        FROM BaseBusData
        WHERE base_case_id = ?
        ORDER BY BUS_NUMBER
        """
        buses_df = pd.read_sql_query(bus_query, conn, params=[base_case])
        
        # Get branch data
        branch_query = """
        SELECT From_Bus as FBUS, To_Bus as TBUS, 0.01 as R, 0.1 as X, 0.0 as B, RATE as RATEA, RATE as RATEB, RATE as RATEC, 1.0 as TAP, 0.0 as SHIFT, PF, QF, 0.0 as PT, 0.0 as QT, 0.0 as SLR, VIO
        FROM BaseBranchData 
        WHERE base_case_id = ?
        """
        branches_df = pd.read_sql_query(branch_query, conn, params=[base_case])
        
        if buses_df.empty or branches_df.empty:
            print(f"No data found for base case {base_case}")
            return [], []
        
        return create_network_layout(buses_df, branches_df, network_type='base')
    except Exception as e:
        print(f"Error in create_base_network_data: {e}")
        return [], []

def create_contingency_network_data(conn, base_case, contingency):
    try:
        # First try contingency tables
        bus_query = """
        SELECT bus_number as BUS_NUMBER, VM, VA as ANGLE, PD, QD, 0.0 as GS, 0.0 as BS, 1 as AREA, 1 as ZONE, 1.1 as VM_MAX, 0.9 as VM_MIN, BASE_KV as BASEKV
        FROM ContingencyBusData 
        WHERE base_case_id = ? AND contingency_case_id = ?
        ORDER BY bus_number
        """
        try:
            buses_df = pd.read_sql_query(bus_query, conn, params=[base_case, contingency])
        except:
            # Fallback to base data
            bus_query = """
            SELECT BUS_NUMBER, VM, ANGLE, PD, QD, GS, BS, AREA, ZONE, VM_MAX, VM_MIN, BASEKV
            FROM BaseBusData 
            WHERE base_case_id = ?
            ORDER BY BUS_NUMBER
            """
            buses_df = pd.read_sql_query(bus_query, conn, params=[base_case])
        
        # Get contingency branch data
        branch_query = """
        SELECT FBUS, TBUS, R, X, B, RATEA, RATEB, RATEC, TAP, SHIFT, PF, QF, PT, QT, SLR, VIO
        FROM ContingencyBranchData 
        WHERE base_case_id = ? AND contingency_case_id = ?
        """
        try:
            branches_df = pd.read_sql_query(branch_query, conn, params=[base_case, contingency])
        except:
            # Fallback to base data
            branch_query = """
            SELECT FBUS, TBUS, R, X, B, RATEA, RATEB, RATEC, TAP, SHIFT, PF, QF, PT, QT, SLR, VIO
            FROM BaseBranchData 
            WHERE base_case_id = ?
            """
            branches_df = pd.read_sql_query(branch_query, conn, params=[base_case])
        
        if buses_df.empty or branches_df.empty:
            return [], []
        
        return create_network_layout(buses_df, branches_df, network_type='contingency')
    except Exception as e:
        print(f"Error in create_contingency_network_data: {e}")
        return [], []

def create_slr_network_data(conn, base_case, contingency):
    try:
        # Try SLR tables first
        bus_query = """
        SELECT BUS_NUMBER, VM, VA as ANGLE, PD, QD, 0.0 as GS, 0.0 as BS, 1 as AREA, 1 as ZONE, 1.1 as VM_MAX, 0.9 as VM_MIN, BASE_KV as BASEKV
        FROM SLR_Buses 
        WHERE case_id = ?
        ORDER BY BUS_NUMBER
        """
        try:
            buses_df = pd.read_sql_query(bus_query, conn, params=[base_case, contingency])
        except:
            # Fallback to base data
            bus_query = """
            SELECT BUS_NUMBER, VM, ANGLE, PD, QD, GS, BS, AREA, ZONE, VM_MAX, VM_MIN, BASEKV
            FROM BaseBusData 
            WHERE base_case_id = ?
            ORDER BY BUS_NUMBER
            """
            buses_df = pd.read_sql_query(bus_query, conn, params=[base_case])
        
        # Get SLR branch data
        branch_query = """
        SELECT FBUS, TBUS, R, X, B, RATEA, RATEB, RATEC, TAP, SHIFT, PF, QF, PT, QT, SLR, VIO
        FROM SLR_BranchData 
        WHERE base_case_id = ? AND contingency_case_id = ?
        """
        try:
            branches_df = pd.read_sql_query(branch_query, conn, params=[base_case, contingency])
        except:
            # Fallback to base data
            branch_query = """
            SELECT FBUS, TBUS, R, X, B, RATEA, RATEB, RATEC, TAP, SHIFT, PF, QF, PT, QT, SLR, VIO
            FROM BaseBranchData 
            WHERE base_case_id = ?
            """
            branches_df = pd.read_sql_query(branch_query, conn, params=[base_case])
        
        if buses_df.empty or branches_df.empty:
            return [], []
        
        return create_network_layout(buses_df, branches_df, network_type='slr')
    except Exception as e:
        print(f"Error in create_slr_network_data: {e}")
        return [], []

def create_dlr_network_data(conn, base_case, contingency):
    try:
        # Try DLR tables first
        bus_query = """
        SELECT BUS_NUMBER, VM, VA as ANGLE, PD, QD, 0.0 as GS, 0.0 as BS, 1 as AREA, 1 as ZONE, 1.1 as VM_MAX, 0.9 as VM_MIN, BASE_KV as BASEKV
        FROM DLR_Buses 
        WHERE case_id = ?
        ORDER BY BUS_NUMBER
        """
        try:
            buses_df = pd.read_sql_query(bus_query, conn, params=[base_case, contingency])
        except:
            # Fallback to base data
            bus_query = """
            SELECT BUS_NUMBER, VM, ANGLE, PD, QD, GS, BS, AREA, ZONE, VM_MAX, VM_MIN, BASEKV
            FROM BaseBusData 
            WHERE base_case_id = ?
            ORDER BY BUS_NUMBER
            """
            buses_df = pd.read_sql_query(bus_query, conn, params=[base_case])
        
        # Get DLR branch data
        branch_query = """
        SELECT FBUS, TBUS, R, X, B, RATEA, RATEB, RATEC, TAP, SHIFT, PF, QF, PT, QT, DLR, VIO
        FROM DLR_BranchData 
        WHERE base_case_id = ? AND contingency_case_id = ?
        """
        try:
            branches_df = pd.read_sql_query(branch_query, conn, params=[base_case, contingency])
        except:
            # Fallback to base data (use SLR as DLR)
            branch_query = """
            SELECT FBUS, TBUS, R, X, B, RATEA, RATEB, RATEC, TAP, SHIFT, PF, QF, PT, QT, SLR as DLR, VIO
            FROM BaseBranchData 
            WHERE base_case_id = ?
            """
            branches_df = pd.read_sql_query(branch_query, conn, params=[base_case])
        
        if buses_df.empty or branches_df.empty:
            return [], []
        
        return create_network_layout(buses_df, branches_df, network_type='dlr')
    except Exception as e:
        print(f"Error in create_dlr_network_data: {e}")
        return [], []

def create_network_layout(buses_df, branches_df, network_type='base'):
    try:
        if buses_df.empty:
            print(f"No bus data available for {network_type}")
            return [], []
        
        if branches_df.empty:
            print(f"No branch data available for {network_type}")
            return [], []
        
        # Create NetworkX graph for layout
        G = nx.Graph()
        
        # Add nodes
        for _, bus in buses_df.iterrows():
            G.add_node(bus['BUS_NUMBER'])
        
        # Add edges
        for _, branch in branches_df.iterrows():
            if pd.notna(branch['FBUS']) and pd.notna(branch['TBUS']):
                G.add_edge(branch['FBUS'], branch['TBUS'])
        
        # Generate layout
        if len(G.nodes()) > 0:
            try:
                pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
            except:
                # Fallback to random layout
                pos = {node: (np.random.random(), np.random.random()) for node in G.nodes()}
        else:
            pos = {}
        
        # Create nodes list
        nodes = []
        for _, bus in buses_df.iterrows():
            bus_num = bus['BUS_NUMBER']
            if bus_num in pos:
                x, y = pos[bus_num]
                
                # Determine node color based on voltage
                voltage = bus.get('VM', 1.0) if pd.notna(bus.get('VM', 1.0)) else 1.0
                if voltage > 1.05:
                    color = 'red'  # High voltage
                elif voltage < 0.95:
                    color = 'orange'  # Low voltage
                else:
                    color = 'lightblue'  # Normal voltage
                
                # Determine node size based on load
                load = abs(bus.get('PD', 0)) if pd.notna(bus.get('PD', 0)) else 0
                size = max(8, min(20, 8 + load * 0.1))
                
                nodes.append({
                    'id': int(bus_num),
                    'x': float(x),
                    'y': float(y),
                    'color': color,
                    'size': float(size),
                    'label': str(int(bus_num)),
                    'voltage': f"{voltage:.3f}",
                    'load': f"{load:.1f}"
                })
        
        # Create edges list
        edges = []
        for _, branch in branches_df.iterrows():
            fbus = branch['FBUS']
            tbus = branch['TBUS']
            
            if pd.notna(fbus) and pd.notna(tbus) and fbus in pos and tbus in pos:
                x0, y0 = pos[fbus]
                x1, y1 = pos[tbus]
                
                # Determine edge color based on loading
                pf = abs(branch.get('PF', 0)) if pd.notna(branch.get('PF', 0)) else 0
                slr = branch.get('SLR', 1) if pd.notna(branch.get('SLR', 1)) else 1
                dlr = branch.get('DLR', slr) if pd.notna(branch.get('DLR', slr)) else slr
                
                # Use appropriate rating based on network type
                rating = dlr if network_type == 'dlr' else slr
                
                if rating > 0:
                    loading = pf / rating
                    if loading > 1.0:
                        color = 'red'  # Overloaded
                    elif loading > 0.9:
                        color = 'orange'  # High loading
                    elif loading > 0.7:
                        color = 'yellow'  # Moderate loading
                    else:
                        color = 'green'  # Low loading
                    
                    width = max(1, min(5, loading * 3))
                else:
                    color = 'gray'
                    width = 1
                    loading = 0
                
                edges.append({
                    'x0': float(x0), 'y0': float(y0),
                    'x1': float(x1), 'y1': float(y1),
                    'color': color,
                    'width': float(width),
                    'loading': f"{loading:.2f}" if rating > 0 else "N/A"
                })
        
        print(f"Created {network_type} layout: {len(nodes)} nodes, {len(edges)} edges")
        return nodes, edges
        
    except Exception as e:
        print(f"Error in create_network_layout: {e}")
        return [], []

def create_network_graph_direct(buses, branches, title, case_id, tripped_branch_info=None):
    """Create network graph directly without data_viz_fall dependency"""
    import plotly.graph_objects as go
    import numpy as np
    
    try:
        # Convert to numpy arrays for easier handling
        if hasattr(buses, 'to_numpy'):
            buses_array = buses.to_numpy()
            branches_array = branches.to_numpy()
        else:
            buses_array = buses
            branches_array = branches
        
        # Create a simple circular layout for nodes
        n_buses = len(buses_array)
        if n_buses == 0:
            return go.Figure()
        
        # Generate positions in a circle
        angles = np.linspace(0, 2*np.pi, n_buses, endpoint=False)
        x_pos = np.cos(angles) * 100
        y_pos = np.sin(angles) * 100
        
        # Create edge traces for transmission lines
        edge_x = []
        edge_y = []
        
        for branch in branches_array:
            if len(branch) >= 2:
                from_bus = int(branch[0]) if not np.isnan(float(branch[0])) else 1
                to_bus = int(branch[1]) if not np.isnan(float(branch[1])) else 1
                
                # Find positions (bus numbers are 1-indexed)
                from_idx = from_bus - 1 if from_bus <= n_buses else 0
                to_idx = to_bus - 1 if to_bus <= n_buses else 0
                
                edge_x.extend([x_pos[from_idx], x_pos[to_idx], None])
                edge_y.extend([y_pos[from_idx], y_pos[to_idx], None])
        
        # Create edge trace
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Create node trace
        node_trace = go.Scatter(
            x=x_pos, y=y_pos,
            mode='markers+text',
            hoverinfo='text',
            text=[f'Bus {i+1}' for i in range(n_buses)],
            textposition="middle center",
            marker=dict(
                size=15,
                color='lightblue',
                line=dict(width=2, color='black')
            )
        )
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title=f'{title} Network Topology',
                           titlefont_size=16,
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Power System Network",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor="left", yanchor="bottom",
                               font=dict(color="#888", size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                       ))
        
        return fig
        
    except Exception as e:
        print(f"Error creating network graph: {e}")
        # Return empty figure on error
        return go.Figure()

def load_base_case_data(conn, base_case):
    """Load base case data using direct SQL"""
    # Direct SQL implementation
    buses_query = """
    SELECT BUS_NUMBER, VM, ANGLE as VA, BASEKV as BASE_KV, 
           0 as PG, 0 as QG, PD, QD
    FROM BaseBusData 
    WHERE base_case_id = ?
    ORDER BY BUS_NUMBER
    """
    
    branches_query = """
    SELECT FBUS as FROM_BUS, TBUS as TO_BUS, PF, QF, 
           0 as LOAD_LEVEL, VIO, 0 as MVA, SLR as RATE,
           'N/A' as LINE_ID
    FROM BaseBranchData 
    WHERE base_case_id = ?
    """
    
    buses = pd.read_sql_query(buses_query, conn, params=[base_case])
    branches = pd.read_sql_query(branches_query, conn, params=[base_case])
    
    return buses, branches

def load_contingency_case_data(conn, base_case, contingency):
    """Load contingency case data using direct SQL"""
    # Direct SQL implementation using proper case ID
    try:
        print(f"Contingency fallback SQL: using base_case_id={DEFAULT_BASE_CASE_ID}, contingency_case_id={contingency}")
        
        buses_query = """
        SELECT BUS_NUMBER, VM, ANGLE as VA, BASEKV as BASE_KV, 
               0 as PG, 0 as QG, PD, QD
        FROM ContingencyBusData 
        WHERE base_case_id = ? AND contingency_case_id = ?
        ORDER BY BUS_NUMBER
        """
        
        branches_query = """
        SELECT FBUS as FROM_BUS, TBUS as TO_BUS, PF, QF, 
               0 as LOAD_LEVEL, VIO, 0 as MVA, SLR as RATE,
               contingency_case_id as BRANCH_NUMBER
        FROM ContingencyBranchData 
        WHERE base_case_id = ? AND contingency_case_id = ?
        """
        
        buses = pd.read_sql_query(buses_query, conn, params=[DEFAULT_BASE_CASE_ID, contingency])
        branches = pd.read_sql_query(branches_query, conn, params=[DEFAULT_BASE_CASE_ID, contingency])
        
        if buses.empty or branches.empty:
            print(f"Contingency fallback failed, using base case data")
            return load_base_case_data(conn, base_case)
        
        return buses, branches
    except Exception as e:
        print(f"Contingency fallback SQL failed: {e}")
        return load_base_case_data(conn, base_case)
        return load_base_case_data(conn, base_case)

def get_tripped_branch_info(conn, branch_id):
    """Get information about a tripped branch for contingency visualization"""
    try:
        # First, try to find the branch in the base case data
        # Look for branches where the branch number or a similar identifier matches
        branch_query = """
        SELECT FBUS, TBUS 
        FROM BaseBranchData 
        WHERE base_case_id = ? 
        ORDER BY ABS(FBUS - ?) + ABS(TBUS - ?)
        LIMIT 1
        """
        
        cursor = conn.cursor()
        cursor.execute(branch_query, [DEFAULT_BASE_CASE_ID, branch_id, branch_id])
        result = cursor.fetchone()
        
        if result:
            from_bus, to_bus = result
            return {
                'from_bus': from_bus,
                'to_bus': to_bus,
                'status': 'OUTAGE',
                'branch_id': branch_id
            }
        
        # Fallback: use approximate mapping based on branch numbers common in IEEE 118-bus system
        fallback_mappings = {
            56: (55, 56),
            90: (89, 90),
            123: (100, 103),  # Common IEEE 118 branch
            124: (100, 104),  # Common IEEE 118 branch  
            158: (110, 111)   # Common IEEE 118 branch
        }
        
        if branch_id in fallback_mappings:
            from_bus, to_bus = fallback_mappings[branch_id]
            return {
                'from_bus': from_bus,
                'to_bus': to_bus,
                'status': 'OUTAGE',
                'branch_id': branch_id
            }
        
        return None
    except Exception as e:
        print(f"Error getting tripped branch info: {e}")
        return None

def load_slr_case_data(conn, base_case, contingency):
    """Load SLR case data using direct SQL"""
    # Direct SQL using mapped case ID
    try:
        slr_case_id = SLR_CASE_MAPPING.get(int(contingency), SLR_CASE_MAPPING[1]) if contingency else SLR_CASE_MAPPING[1]
        print(f"SLR fallback SQL: using case_id={slr_case_id} for contingency={contingency}")
        
        buses_query = """
        SELECT BUS_NUMBER, VM, ANGLE as VA, BASEKV as BASE_KV, 
               PG, QG, PD, QD
        FROM SLR_BusData 
        WHERE base_case_id = ? AND contingency_case_id = ?
        ORDER BY BUS_NUMBER
        """
        
        branches_query = """
        SELECT FBUS as FROM_BUS, TBUS as TO_BUS, PF, QF, 
               0 as LOAD_LEVEL, VIO, 0 as MVA, SLR as RATE,
               'SLR' as LINE_ID
        FROM SLR_BranchData 
        WHERE base_case_id = ? AND contingency_case_id = ?
        """
        
        buses = pd.read_sql_query(buses_query, conn, params=[DEFAULT_BASE_CASE_ID, slr_case_id])
        branches = pd.read_sql_query(branches_query, conn, params=[DEFAULT_BASE_CASE_ID, slr_case_id])
        
        if buses.empty or branches.empty:
            print(f"SLR fallback failed, using base case data")
            return load_base_case_data(conn, base_case)
        
        return buses, branches
    except Exception as e:
        print(f"SLR fallback SQL failed: {e}")
        return load_base_case_data(conn, base_case)

def load_dlr_case_data(conn, base_case, contingency):
    """Load DLR case data using direct SQL"""
    # Direct SQL using mapped case ID
    try:
        dlr_case_id = DLR_CASE_MAPPING.get(int(contingency), DLR_CASE_MAPPING[1]) if contingency else DLR_CASE_MAPPING[1]
        print(f"DLR fallback SQL: using case_id={dlr_case_id} for contingency={contingency}")
        
        buses_query = """
        SELECT BUS_NUMBER, VM, ANGLE as VA, BASEKV as BASE_KV, 
               PG, QG, PD, QD
        FROM DLR_BusData 
        WHERE base_case_id = ? AND contingency_case_id = ?
        ORDER BY BUS_NUMBER
        """
        
        branches_query = """
        SELECT FBUS as FROM_BUS, TBUS as TO_BUS, PF, QF, 
               0 as LOAD_LEVEL, VIO, 0 as MVA, DLR as RATE,
               'DLR' as LINE_ID
        FROM DLR_BranchData 
        WHERE base_case_id = ? AND contingency_case_id = ?
        """
        
        buses = pd.read_sql_query(buses_query, conn, params=[DEFAULT_BASE_CASE_ID, dlr_case_id])
        branches = pd.read_sql_query(branches_query, conn, params=[DEFAULT_BASE_CASE_ID, dlr_case_id])
        
        if buses.empty or branches.empty:
            print(f"DLR fallback failed, using base case data with DLR modifications")
            buses, branches = load_base_case_data(conn, base_case)
            # For DLR, modify branch RATE column to simulate DLR values
            branches['RATE'] = branches['RATE'] * 1.2  # Assume 20% increase
        
        return buses, branches
    except Exception as e:
        print(f"DLR fallback SQL failed: {e}")
        buses, branches = load_base_case_data(conn, base_case)
        # For DLR, modify branch RATE column to simulate DLR values
        branches['RATE'] = branches['RATE'] * 1.2  # Assume 20% increase
        return buses, branches

def extract_nodes_from_figure(fig_json):
    """Extract node data from Plotly figure for compatibility"""
    nodes = []
    try:
        for trace in fig_json.get('data', []):
            if trace.get('mode') == 'markers' and 'Bus' in trace.get('name', ''):
                x_coords = trace.get('x', [])
                y_coords = trace.get('y', [])
                colors = trace.get('marker', {}).get('color', [])
                sizes = trace.get('marker', {}).get('size', [])
                
                for i, (x, y) in enumerate(zip(x_coords, y_coords)):
                    nodes.append({
                        'id': i + 1,
                        'x': x,
                        'y': y,
                        'color': colors[i] if i < len(colors) else 'blue',
                        'size': sizes[i] if i < len(sizes) else 10,
                        'label': str(i + 1)
                    })
                break
    except Exception as e:
        print(f"Error extracting nodes: {e}")
    return nodes

def extract_edges_from_figure(fig_json):
    """Extract edge data from Plotly figure for compatibility"""
    edges = []
    try:
        for trace in fig_json.get('data', []):
            if trace.get('mode') == 'lines':
                x_coords = trace.get('x', [])
                y_coords = trace.get('y', [])
                colors = trace.get('line', {}).get('color', 'gray')
                
                # Parse line segments (separated by None values)
                i = 0
                while i < len(x_coords) - 2:
                    if x_coords[i] is not None and x_coords[i+1] is not None:
                        edges.append({
                            'x0': x_coords[i],
                            'y0': y_coords[i],
                            'x1': x_coords[i+1],
                            'y1': y_coords[i+1],
                            'color': colors if isinstance(colors, str) else 'gray',
                            'width': 2
                        })
                    i += 3  # Skip to next line segment
                break
    except Exception as e:
        print(f"Error extracting edges: {e}")
    return edges

if __name__ == '__main__':
    print("🚀 Starting Flask-based Power System Visualization with RAG")
    print("📊 Database: IEEE 118-bus system")
    print("🧠 RAG System: Simple SQL-based retrieval")
    print("🌐 URL: http://127.0.0.1:5000")
    print("✨ Features: Interactive chat, database queries, real-time data")
    app.run(debug=True, host='127.0.0.1', port=5000)