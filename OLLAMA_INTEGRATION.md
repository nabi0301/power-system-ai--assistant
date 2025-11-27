# Ollama Integration with PSA (Power System Assistant)

## Overview
PSA now uses **Ollama** for enhanced conversational AI capabilities! Ollama provides a simple, fast, and local way to run large language models without needing cloud services or complex setups.

## What is Ollama?

Ollama is a lightweight, extensible framework for running large language models locally. It makes it easy to run models like Llama 3, Mistral, and others on your own machine.

**Key Benefits:**
- ✅ **Local execution** - Your data never leaves your machine
- ✅ **Fast responses** - Optimized for CPU and GPU
- ✅ **Easy model management** - Simple commands to download and switch models
- ✅ **No API keys needed** - Completely self-hosted
- ✅ **Multiple models supported** - Llama, Mistral, CodeLlama, and more

## Installation

### 1. Install Ollama Application
Download and install Ollama from: https://ollama.com

**Windows:** Download the installer and run it
**Mac:** `brew install ollama`
**Linux:** `curl -fsSL https://ollama.com/install.sh | sh`

### 2. Install Python Package
```bash
pip install ollama
```

### 3. Download a Model
```bash
# Recommended lightweight model (1.3 GB)
ollama pull llama3.2:1b

# Or the 3B model (better quality, 2 GB)
ollama pull llama3.2:3b

# Other options
ollama pull llama2
ollama pull mistral
ollama pull codellama
```

## Configuration

### Default Model
The system will automatically use the first available model. You can change the preferred model in `power_viz_with_database.py`:

```python
# Line ~41
OLLAMA_MODEL = "llama3.2:3b"  # Change to your preferred model
```

### Available Models
Check your installed models:
```bash
ollama list
```

## How It Works

### Architecture: Hybrid Response System

```
User Query
    ↓
┌─────────────────────────────────────────┐
│   Query Intent Classification           │
│   • Pattern matching on keywords        │
│   • Entity extraction (case, bus, etc.) │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│          Decision Router                │
├─────────────────┬───────────────────────┤
│ Power System    │ General/Conversational│
│ Keywords Found? │ Query?                │
└────────┬────────┴──────────┬────────────┘
         ↓ YES               ↓ NO
┌────────────────┐   ┌──────────────────┐
│  Rule-Based    │   │  Ollama LLM      │
│  Response      │   │  Generation      │
│  (~instant)    │   │  (~1-2 seconds)  │
└────────────────┘   └──────────────────┘
         ↓                   ↓
┌─────────────────────────────────────────┐
│       Formatted Response to User         │
└─────────────────────────────────────────┘
```

### Code Implementation

**Initialization (Lines 38-70):**
```python
import ollama

# Connect to Ollama
models = ollama.list()
available_models = [model.get('name') for model in models.get('models', [])]

if available_models:
    OLLAMA_AVAILABLE = True
    OLLAMA_MODEL = "llama3.2:3b"  # or first available
```

**Response Generation (Lines 6906-6952):**
```python
def generate_llama_response(user_message, context_info=""):
    """Generate conversational response using Ollama"""
    
    import ollama
    
    system_prompt = """You are PSA (Power System Assistant), 
    a friendly AI specialized in electrical power systems..."""
    
    if context_info:
        system_prompt += f"\n\nCurrent context: {context_info}"
    
    full_prompt = f"{system_prompt}\n\nUser: {user_message}\n\nAssistant:"
    
    response = ollama.generate(
        model=OLLAMA_MODEL,
        prompt=full_prompt,
        options={
            'temperature': 0.7,
            'top_p': 0.9,
            'num_predict': 200,
        }
    )
    
    return f"🔋 {response['response'].strip()}"
```

**Hybrid Decision Logic (Lines 9425-9450):**
```python
def get_ai_response(user_message, ...):
    # Priority 1: Rule-based for power system queries
    if 'critical lines' in message_lower:
        return analyze_critical_lines()  # Instant
    
    # Priority 2: Ollama for general questions
    if OLLAMA_AVAILABLE:
        return generate_llama_response(user_message, context)
    
    # Priority 3: Static fallback
    return static_response()
```

## Performance

### Model Comparison

| Model | Size | RAM Usage | Speed (CPU) | Quality |
|-------|------|-----------|-------------|---------|
| **llama3.2:1b** | 1.3 GB | ~2 GB | ~1 sec | Good |
| **llama3.2:3b** | 2 GB | ~3 GB | ~2 sec | Better |
| **llama2:7b** | 3.8 GB | ~5 GB | ~4 sec | Excellent |
| **mistral:7b** | 4.1 GB | ~5 GB | ~3 sec | Excellent |

### Response Times

- **Rule-based queries:** < 100ms (instant)
  - "show critical lines"
  - "voltage analysis"
  - "list cases"

- **Ollama queries:** 1-3 seconds
  - "what is power factor?"
  - "explain contingency analysis"
  - General conversation

### Resource Requirements

- **Minimum:** 4 GB RAM (llama3.2:1b)
- **Recommended:** 8 GB RAM (llama3.2:3b)
- **Optimal:** 16 GB RAM (llama2:7b)
- **GPU:** Optional (NVIDIA CUDA for 2-3x faster inference)

## Usage Examples

### Power System Query (Rule-Based)
```
User: "show me critical lines"
PSA: ⚡ Critical Lines & Violations Analysis
     Case 42 | Database: main
     
     ⚠ THERMAL VIOLATIONS (3 lines)
     1. Bus 77 → 80
        • Loading: 127.5% ⚠ OVERLOAD
        ...
     [Response time: <100ms]
```

### General Query (Ollama)
```
User: "what is power system analysis?"
PSA: 🔋 Power system analysis involves the examination, 
     modeling, and optimization of electrical power 
     generation, transmission, distribution, and 
     consumption networks to ensure reliability, 
     efficiency, and safety...
     
     💡 Power System Commands:
     • 'Smart analysis' - AI-powered system insights
     • 'Show critical lines' - Find overloaded branches
     [Response time: ~2 seconds]
```

## Testing

Run the test script to verify your setup:
```bash
python test_ollama_integration.py
```

**Expected output:**
```
============================================================
Testing Ollama Integration with PSA
============================================================
✓ Ollama library imported successfully
✓ Ollama connected successfully

📦 Available models:
   • llama3.2:3b
   • llama2:latest

✓ Model 'llama3.2:3b' working
✓ Response generation successful
✅ Ollama integration test PASSED!
```

## Model Management

### List Models
```bash
ollama list
```

### Download New Model
```bash
ollama pull llama3.2:3b
```

### Remove Model
```bash
ollama rm llama2
```

### Switch Models
Edit `power_viz_with_database.py`:
```python
OLLAMA_MODEL = "mistral"  # Use Mistral instead
```

## Troubleshooting

### "Could not connect to Ollama"
**Solution:** Make sure Ollama is running
```bash
# Windows: Should auto-start, or run
ollama serve

# Check status
ollama list
```

### "No models found"
**Solution:** Download a model
```bash
ollama pull llama3.2:1b
```

### Slow Responses
**Solutions:**
1. Use a smaller model: `llama3.2:1b`
2. Reduce `num_predict` in options (shorter responses)
3. Enable GPU if available (automatic with CUDA)

### High Memory Usage
**Solutions:**
1. Use smaller model: `llama3.2:1b` (1.3 GB)
2. Close other applications
3. Only keep one model downloaded

## Advantages Over Transformers

| Feature | Ollama | Transformers |
|---------|--------|--------------|
| **Setup** | Simple (one command) | Complex (dependencies) |
| **Model Download** | `ollama pull` | Manual download or HF auth |
| **Speed** | Optimized inference | Standard PyTorch |
| **Memory** | Efficient | Higher overhead |
| **Model Switching** | Easy (`ollama pull`) | Re-download models |
| **Updates** | Automatic | Manual |
| **Privacy** | 100% local | Local (after download) |

## Context Awareness

PSA provides context to Ollama for better responses:
```python
context_info = f"Currently viewing: {current_viz_type}, Case: {current_case_id}"
```

**Example:**
```
User: "what am I looking at?"
PSA: 🔋 You're currently viewing the network topology 
     visualization for Case 42. This shows the IEEE 
     118-bus power system with transmission lines 
     color-coded by loading level...
```

## Advanced Configuration

### Temperature Control
Edit `generate_llama_response()` function:
```python
options={
    'temperature': 0.7,  # 0.0 = deterministic, 1.0 = creative
    'top_p': 0.9,        # Nucleus sampling
    'num_predict': 200,  # Max response length
}
```

### Custom System Prompt
Modify the system prompt in `generate_llama_response()` to change PSA's personality:
```python
system_prompt = """You are PSA, an expert power systems engineer
with 20 years of experience. Be technical but friendly..."""
```

## Integration Status

✅ **Fully Integrated**
- Ollama client initialized at startup
- Hybrid response system active
- Context-aware responses
- Automatic fallback to rule-based
- Error handling and recovery

✅ **Tested**
- Model listing works
- Response generation works
- Context passing works
- Fallback system works

✅ **Production Ready**
- Graceful degradation
- No breaking changes
- All existing features preserved
- Optional enhancement (works without Ollama)

## Summary

🎉 **Ollama integration complete!**

**Benefits:**
- ✅ Local, private AI responses
- ✅ Fast inference (1-2 seconds)
- ✅ Easy model management
- ✅ No cloud dependencies
- ✅ Seamless fallback

**Setup:**
1. Install Ollama: https://ollama.com
2. `pip install ollama`
3. `ollama pull llama3.2:3b`
4. `python power_viz_with_database.py`

**You're ready to go!** 🚀
