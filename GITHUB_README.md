# Power System Visualization Tool with AI Assistant

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Dash-2.0%2B-green.svg)](https://dash.plotly.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An advanced power system visualization and analysis tool featuring an AI-powered assistant for the IEEE 118-bus test system.

## 🌟 Key Features

### 📊 Power System Analysis
- **Network Topology Visualization**: Interactive network graphs with bus and branch data
- **Voltage Analysis**: Bus voltage profile monitoring and violation detection
- **Loading Analysis**: Real-time thermal loading assessment
- **Contingency Analysis**: N-1 contingency scenarios evaluation
- **SLR vs DLR Comparison**: Static vs Dynamic Line Rating comparison

### 🤖 AI-Powered Assistant
- **Natural Language Interface**: Chat-based system interaction
- **Predictive Analysis**: Identify potential violations before they occur
- **Optimization Recommendations**: Specific MW/MVAR adjustment suggestions
- **Multi-Case Comparison**: Intelligent comparison across contingency scenarios
- **Custom Preferences**: Context-aware, view-specific suggestions

### 🔮 Advanced AI Features
- **Lines Approaching Capacity**: Identifies branches at 80-90% loading
- **Risk Level Assessment**: HIGH/MODERATE risk categorization
- **Generator Redispatch**: Optimal power flow recommendations
- **Load Management**: Demand response and load shedding strategies
- **Reactive Power Optimization**: Capacitor/reactor placement suggestions

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
Ollama (for local LLM)
PostgreSQL (optional)
```

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/dlr-database-project.git
cd dlr-database-project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Ollama and pull Llama 3.2
# Visit: https://ollama.ai
ollama pull llama3.2
```

### Running the Application
```bash
# Start the application
python power_viz_with_database.py

# Open browser to http://127.0.0.1:8054
```

## 📖 Documentation

- **[Features Overview](FEATURES.md)** - Complete feature list
- **[Technical Architecture](TECHNICAL_ARCHITECTURE.md)** - System design
- **[AI Suggestions Guide](SUGGESTION_FEATURE.md)** - AI assistant features
- **[Advanced Features](ADVANCED_FEATURES_SUMMARY.md)** - Predictive & optimization
- **[Quick Reference](QUICK_REFERENCE.md)** - One-page guide

## 💡 AI Assistant Usage

### Basic Suggestions
Click the **💡** button in the chat interface to get:
- Current system health assessment
- Violation detection and analysis
- Predictive warnings for approaching limits
- Optimization recommendations
- Multi-case comparison suggestions

### Example Queries
```
"Show me critical lines"
"What are the voltage violations?"
"Compare base case with contingency 1"
"What will fail if load increases 10%?"
"How should I redispatch generators?"
```

## 🎯 Use Cases

1. **Power System Operators**: Real-time monitoring and decision support
2. **Planning Engineers**: Contingency analysis and capacity assessment
3. **Researchers**: Power system analysis and algorithm development
4. **Students**: Learning tool for power system concepts

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│        Web Interface (Dash)             │
│  ┌────────────┐      ┌────────────┐    │
│  │ Network    │      │ AI Chat    │    │
│  │ Viz        │      │ Interface  │    │
│  └────────────┘      └────────────┘    │
└─────────────────────────────────────────┘
           │                    │
           ▼                    ▼
┌─────────────────┐   ┌──────────────────┐
│ Database Layer  │   │ AI Engine        │
│ • SQLite        │   │ • Llama 3.2      │
│ • PostgreSQL    │   │ • Ollama         │
└─────────────────┘   └──────────────────┘
```

## 📊 Data Structure

The application uses IEEE 118-bus test system data:
- **Base Case**: Normal operating conditions
- **Contingency Cases**: N-1 outage scenarios
- **SLR/DLR Cases**: Different line rating methodologies

**Note**: Data files (*.db) are not included in this repository. Use your own power system data or IEEE test cases.

## 🛠️ Technology Stack

- **Backend**: Python, Pandas, NumPy
- **Frontend**: Dash, Plotly
- **AI**: Ollama, Llama 3.2
- **Database**: SQLite, PostgreSQL
- **Visualization**: Plotly, NetworkX

## 📁 Project Structure

```
dlr-database-project/
├── power_viz_with_database.py    # Main application
├── ai_chat_interface.py           # AI assistant
├── network_comparison.py          # Network visualization
├── comprehensive_trend_analyzer.py # Analysis tools
├── requirements.txt               # Dependencies
├── README.md                      # This file
└── docs/                          # Documentation
```

## 🔧 Configuration

Create a `.env` file (not tracked in Git):
```env
# Database configuration
DATABASE_PATH=data.db

# PostgreSQL (optional)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=power_system
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

# Ollama configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- IEEE 118-bus test system data
- Ollama team for local LLM infrastructure
- Dash/Plotly for visualization framework

## 📧 Contact

For questions or support:
- Open an issue on GitHub
- Contact: [Your Email]

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Built with ❤️ for the power systems community**
