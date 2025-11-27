"""
Quick test for Llama 3.2 via Ollama
"""

import ollama

print("=" * 60)
print("Testing Llama 3.2 Connection")
print("=" * 60)

# List available models
print("\n📦 Checking available models...")
try:
    models = ollama.list()
    models_list = models.get('models', [])
    available_models = [model.get('name') or model.get('model') for model in models_list]
    
    print(f"\nAvailable models:")
    for model in available_models:
        if model:
            indicator = "✓" if 'llama3.2' in model.lower() else " "
            print(f"  {indicator} {model}")
    
    # Find Llama 3.2
    llama32_models = [m for m in available_models if m and 'llama3.2' in m.lower()]
    
    if llama32_models:
        test_model = llama32_models[0]
        print(f"\n✓ Found Llama 3.2: {test_model}")
    else:
        print("\n⚠️ Llama 3.2 not found!")
        print("   Install with: ollama pull llama3.2")
        exit(1)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\n💡 Make sure Ollama is running:")
    print("   Check if service is active")
    print("   Or run: ollama serve")
    exit(1)

# Test generation
print(f"\n🧪 Testing response generation with {test_model}...")
try:
    response = ollama.generate(
        model=test_model,
        prompt="Explain power system analysis in one sentence.",
        options={'temperature': 0.7, 'num_predict': 50}
    )
    
    print("\n✓ Response generated:")
    print("-" * 60)
    print(response['response'].strip())
    print("-" * 60)
    
    print("\n✅ SUCCESS! Llama 3.2 is working perfectly!")
    print(f"   Model: {test_model}")
    print("   Server: http://localhost:11434")
    
except Exception as e:
    print(f"\n✗ Generation failed: {e}")
    exit(1)

print("\n🎉 PSA can now use Llama 3.2 for conversational AI!")
