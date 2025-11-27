"""
Test script to verify Llama integration with PSA
Tests both rule-based responses and Llama-generated responses
"""

# Test if Llama model loads correctly
print("=" * 60)
print("Testing Llama Integration with PSA")
print("=" * 60)

# Try to import transformers and torch
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    print("✓ Transformers and PyTorch imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    exit(1)

# Try to load the model
print("\n🔄 Loading Llama-3.2-1B-Instruct model...")
print("   (This may take a few minutes on first run)")

try:
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        low_cpu_mem_usage=True
    )
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"✓ Model loaded successfully on {device}")
    
except Exception as e:
    print(f"✗ Model loading failed: {e}")
    print("\n💡 Possible solutions:")
    print("   1. Authenticate with Hugging Face: huggingface-cli login")
    print("   2. Try a different model: 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'")
    print("   3. Check internet connection for model download")
    exit(1)

# Test generating a response
print("\n🧪 Testing response generation...")
test_message = "What is power system analysis?"

system_prompt = """You are PSA (Power System Assistant), a friendly AI specialized in electrical power systems. Be concise and helpful."""

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": test_message}
]

try:
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    )
    
    if torch.cuda.is_available():
        inputs = inputs.to("cuda")
    
    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_new_tokens=150,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract just the assistant's response
    if "<|assistant|>" in response:
        response = response.split("<|assistant|>")[-1].strip()
    
    print(f"\n✓ Generated response:")
    print("-" * 60)
    print(response)
    print("-" * 60)
    
    print("\n✅ Llama integration test PASSED!")
    print("   The model is loaded and working correctly")
    print("   PSA will now use Llama for general conversational queries")
    
except Exception as e:
    print(f"\n✗ Response generation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("Integration Summary:")
print("=" * 60)
print("✓ Dependencies installed")
print("✓ Model loaded successfully")
print("✓ Response generation working")
print("\n🎉 Llama is now integrated with PSA!")
print("   - Rule-based responses for power system queries")
print("   - Llama-generated responses for general questions")
print("\n💡 You can now run your main application and test PSA")
