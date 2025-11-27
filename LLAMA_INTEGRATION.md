# Llama Integration with PSA (Power System Assistant)

## Overview
PSA now includes Llama model integration for enhanced conversational AI capabilities! The system uses a **hybrid approach**:

- **Rule-based responses** for specific power system queries (voltage analysis, line loading, violations, etc.)
- **Llama-generated responses** for general questions and conversational queries

## Model Used
- **TinyLlama/TinyLlama-1.1B-Chat-v1.0**
  - Lightweight (2.2 GB)
  - Efficient on CPU (no GPU required)
  - Openly available (no authentication needed)
  - Good conversational capabilities

## How It Works

### 1. Model Loading (Startup)
When the application starts, it attempts to load the Llama model:
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, low_cpu_mem_usage=True)
```

### 2. Response Generation
PSA uses a two-tier response system:

#### Tier 1: Rule-Based (Priority)
For power system specific queries, PSA uses pre-defined patterns:
- "show critical lines" → Analyzes database, finds overloaded branches
- "voltage analysis" → Queries voltage data, switches visualization
- "show generators" → Displays generator dispatch data
- "list cases" → Shows available scenarios from database

#### Tier 2: Llama-Generated (Fallback)
For general questions, PSA uses the Llama model:
- "how are you?" → Llama generates friendly response
- "explain power systems" → Llama provides educational content
- "what is a transformer?" → Llama explains electrical concepts
- General conversation → Llama handles naturally

### 3. Hybrid Response Example
```python
def get_ai_response(user_message, ...):
    # Check for power system keywords first
    if 'critical lines' in user_message:
        return analyze_critical_lines()  # Rule-based
    
    # Check for database queries
    if 'show buses' in user_message:
        return query_database()  # Rule-based
    
    # Fallback to Llama for everything else
    if LLAMA_AVAILABLE:
        return generate_llama_response(user_message)  # AI-generated
```

## Installation

All dependencies are already installed:
```bash
pip install transformers torch accelerate sentencepiece
```

## Testing

Run the test script to verify integration:
```bash
python test_llama_integration.py
```

Expected output:
```
✓ Transformers and PyTorch imported successfully
✓ Model loaded successfully on cpu
✓ Generated response: [Llama's response]
✅ Llama integration test PASSED!
```

## Performance

**First Run:**
- Downloads model (~2.2 GB) - takes 2-5 minutes depending on internet
- Model cached at: `C:\Users\<user>\.cache\huggingface\hub\`

**Subsequent Runs:**
- Loads from cache (~5-10 seconds)
- Response generation: ~1-3 seconds per query on CPU

## Configuration

The model can be configured in `power_viz_with_database.py`:

```python
# Line ~40: Change model
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Current
# Alternatives:
# model_name = "microsoft/DialoGPT-medium"  # Faster, smaller
# model_name = "meta-llama/Llama-3.2-1B-Instruct"  # Requires auth

# Generation parameters
max_new_tokens=200,     # Response length
temperature=0.7,        # Creativity (0.0-1.0)
top_p=0.9,             # Nucleus sampling
```

## Features Preserved

✅ **All existing functionality works unchanged:**
- Database queries and analysis
- Network visualization controls
- Critical line identification
- Voltage and loading analysis
- Generator dispatch analysis
- Multi-database support
- Case and contingency switching
- Performance metrics
- Network comparison (Base/Cont/SLR/DLR)

## Benefits of Integration

1. **Natural Conversation**: Users can ask questions in plain English
2. **Educational**: Llama can explain power system concepts
3. **Fallback Intelligence**: Unknown queries get smart responses instead of "I don't understand"
4. **Context-Aware**: Llama receives context (current case, view type, etc.)
5. **Seamless**: Users don't need to know which system is responding

## Example Conversations

### Power System Query (Rule-Based)
```
User: "show me critical lines"
PSA: ⚡ **Critical Lines & Violations Analysis**
     **Case 42** | Database: **main**
     
     ⚠ **THERMAL VIOLATIONS (3 lines)**
     1. **Bus 77 → 80**
        • Loading: **127.5%** ⚠ OVERLOAD
        ...
```

### General Query (Llama-Generated)
```
User: "what is power system analysis?"
PSA: 🔋 Power system analysis (PSA) is a scientific field 
     that involves modeling and analyzing power systems to 
     study their behavior, performance, and reliability...
     
     💡 **Power System Commands:**
     • 'Smart analysis' - AI-powered system insights
     • 'Show critical lines' - Find overloaded branches
```

## Troubleshooting

**Model won't load:**
- Check internet connection (first download)
- Ensure 3+ GB free disk space
- Try clearing cache: `rm -rf ~/.cache/huggingface/`

**Slow responses:**
- Normal on CPU (~2-3 seconds)
- Consider using GPU if available
- Reduce `max_new_tokens` for faster responses

**Import errors:**
- Reinstall: `pip install --upgrade transformers torch`
- Check Python version: 3.8+ required

## Disabling Llama

If you prefer rule-based only, set at startup:
```python
LLAMA_AVAILABLE = False  # Force disable
```

## Summary

✅ **Llama successfully integrated**
✅ **TinyLlama-1.1B-Chat model loaded**
✅ **Hybrid response system working**
✅ **All existing features preserved**
✅ **No breaking changes**

🎉 **PSA is now more intelligent and conversational!**
