# LangChain Integration for Power System Analysis

## Overview

This project integrates LangChain framework for advanced Retrieval-Augmented Generation (RAG) capabilities within the Power System Analysis application. LangChain provides a powerful set of tools for building applications with large language models (LLMs), including:

- Document processing and chunking
- Vector embeddings and similarity search
- Retrieval chains for context-aware responses
- Agents for complex reasoning tasks
- SQL database integration
- Conversation memory

## Key Features

- **Advanced RAG System**: Context-aware responses using vector similarity search
- **Database Integration**: Direct querying of power system database through natural language
- **Agent-based Analysis**: LangChain agents for complex power system analysis tasks
- **Conversational Memory**: Remembers context from previous interactions
- **Tool Integration**: Custom tools for power system-specific tasks

## Getting Started

1. **Installation**:
   ```
   python install_langchain_dependencies.py
   ```

2. **Starting the Application**:
   ```
   python start_with_langchain.py
   ```
   
3. **API Key Setup**:
   - You'll be prompted to enter your OpenAI API key
   - This is required for some LangChain features
   - Set the `OPENAI_API_KEY` environment variable to avoid the prompt

## Components

### 1. LangChain RAG (`langchain_rag.py`)
The core LangChain implementation that replaces the previous SimpleRAG system. It uses:
- ChromaDB for vector storage
- SentenceTransformers for embeddings
- LangChain chains for document retrieval and generation

### 2. Power System LangChain Demo (`power_system_langchain_demo.py`)
A standalone demo showcasing advanced LangChain capabilities:
- SQL Database agents for complex database queries
- Conversational memory for context-aware interactions
- Custom tools for power system tasks

### 3. Dependencies Installer (`install_langchain_dependencies.py`)
Installs all required dependencies for the LangChain implementation.

### 4. Application Launcher (`start_with_langchain.py`)
Sets up the environment and launches the main application with LangChain integration.

## Usage Examples

Example power system questions you can ask:
- "What are the most overloaded transmission lines in the system?"
- "Compare SLR and DLR for contingency case 5"
- "Show me all buses with voltage violations"
- "What is the average loading across all transmission lines?"
- "Explain what dynamic line rating means for this system"

## Advanced Features

### SQL Database Querying
LangChain can translate natural language questions into SQL queries:

```
"What's the average voltage magnitude across all buses in the system?"
```

### Agent-Based Analysis
For complex tasks, LangChain uses agents that can:
- Break down complex questions
- Choose appropriate tools
- Execute multiple steps of reasoning
- Provide detailed explanations

### Memory Integration
The system remembers previous interactions:
```
User: "Show me the most overloaded lines"
System: [Shows overloaded lines]
User: "Why are they overloaded?" 
System: [Explains the specific lines from the previous question]
```

## Troubleshooting

- **ImportError**: Run `python install_langchain_dependencies.py`
- **API Key Issues**: Set the `OPENAI_API_KEY` environment variable
- **Memory Issues**: ChromaDB may require significant RAM for large datasets