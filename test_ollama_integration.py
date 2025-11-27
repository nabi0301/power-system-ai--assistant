"""
Test script to verify Ollama integration with PSA
Tests connection to Ollama and response generation
"""

print("=" * 60)
print("Testing Ollama Integration with PSA")
print("=" * 60)

# Try to import ollama
try:
    import ollama
    print("✓ Ollama library imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    print("\n💡 Install with: pip install ollama")
    exit(1)

# Try to connect to Ollama
print("\n🔄 Connecting to Ollama...")

try:
    # List available models
    models_response = ollama.list()
    models_list = models_response.get('models', [])
    available_models = [model.get('name') or model.get('model') for model in models_list]
    
    if not available_models:
        print("✗ No models found in Ollama")
        print("\n💡 Download a model:")
        print("   ollama pull llama3.2:1b")
        print("   ollama pull llama2")
        print("   ollama pull mistral")
        exit(1)
    
    print(f"✓ Ollama connected successfully")
    print(f"\n📦 Available models:")
    for model in available_models:
        print(f"   • {model}")
    
    # Use first available model for testing
    test_model = available_models[0]
    print(f"\n🧪 Testing with model: {test_model}")
    
except Exception as e:
    print(f"✗ Could not connect to Ollama: {e}")
    print("\n💡 Possible solutions:")
    print("   1. Start Ollama: ollama serve")
    print("   2. Or Ollama may already be running as a service")
    print("   3. Check if Ollama is installed: ollama --version")
    exit(1)

# Test generating a response
print("\n🧪 Testing response generation...")
test_message = "What is power system analysis?"

try:
    system_prompt = """You are PSA (Power System Assistant), a friendly AI specialized in electrical power systems. Be concise and helpful."""
    
    full_prompt = f"{system_prompt}\n\nUser: {test_message}\n\nAssistant:"
    
    response = ollama.generate(
        model=test_model,
        prompt=full_prompt,
        options={
            'temperature': 0.7,
            'top_p': 0.9,
            'num_predict': 200,
        }
    )
    
    response_text = response['response'].strip()
    
    print(f"\n✓ Generated response:")
    print("-" * 60)
    print(response_text)
    print("-" * 60)
    
    print("\n✅ Ollama integration test PASSED!")
    print("   Ollama is connected and working correctly")
    print("   PSA will now use Ollama for general conversational queries")
    
except Exception as e:
    print(f"\n✗ Response generation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("Integration Summary:")
print("=" * 60)
print("✓ Ollama library installed")
print("✓ Ollama service connected")
print(f"✓ Model '{test_model}' working")
print("✓ Response generation successful")
print("\n🎉 Ollama is now integrated with PSA!")
print("   - Rule-based responses for power system queries")
print("   - Ollama-generated responses for general questions")
print("\n💡 You can now run your main application and test PSA")
print("   python power_viz_with_database.py")
