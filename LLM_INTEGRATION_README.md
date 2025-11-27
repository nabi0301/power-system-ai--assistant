# Power System Visualization Tool with LLM Integration

This document describes the LLM integration added to the existing power system visualization tool.

## Overview

The LLM (Large Language Model) integration enhances the existing AI assistant with more advanced natural language understanding and visualization intent detection capabilities. The integration is designed to be fallback-friendly, meaning the application will still function even if LLM API access is not available.

## Mock LLM Mode

If you don't have access to an OpenAI API key, you can still use the enhanced features in "Mock LLM" mode. This mode provides many of the same enhanced capabilities using sophisticated rule-based approaches instead of API calls.

## Features Added

- **Enhanced Natural Language Understanding**: More accurate interpretation of user queries
- **Advanced Visualization Intent Detection**: Better detection of what type of visualization the user wants
- **Technical Response Generation**: More detailed and accurate responses to complex power system questions
- **Context-Aware Conversation**: Improved understanding of conversation context and user requirements
- **Fallback Mechanism**: Graceful degradation to rule-based assistant when LLM is unavailable

## Architecture

The LLM integration consists of three main components:

1. **`llm_integration.py`**: Core integration with LLM APIs
   - Handles API communication
   - Provides visualization intent detection
   - Manages context generation and response processing
   - Includes fallback mechanisms

2. **`llm_assistant.py`**: Enhanced assistant class 
   - Extends the existing `ConversationalAIAssistant`
   - Provides seamless integration with the existing codebase
   - Handles switching between LLM and rule-based approaches

3. **`mock_llm.py`**: Mock LLM implementation for API-free environments
   - Provides enhanced rule-based capabilities without requiring API access
   - Includes improved visualization intent detection
   - Offers better response generation and suggestions
   - Seamlessly integrates with the existing application

## Setup and Usage

### Requirements

- Python 3.8 or higher
- An OpenAI API key or compatible LLM API
- All existing requirements for the power system visualization tool

### Running with LLM Integration

To run the application with LLM integration:

```
start_llm_app.bat YOUR_API_KEY
```

Or if you already have the API key in your environment:

```
start_llm_app.bat
```

### Running with Mock LLM (No API Key Required)

To run the application with enhanced features but without an API key:

```
start_llm_app.bat
```

The system will automatically detect if you don't have an API key and switch to Mock LLM mode.

### Configuration

You can configure the LLM integration via the UI in the AI Assistant tab:

1. Click on the "Settings" button
2. Enter your API key (if not already set)
3. Select the LLM model to use
4. Save settings

## Fallback Behavior

If the LLM API is not available or encounters an error:

1. The application will automatically fall back to the rule-based AI assistant
2. The user interface will indicate that LLM enhancement is not available
3. Basic functionality will continue to work without interruption

## Development and Extension

To extend the LLM integration:

1. Modify the system prompt in `llm_integration.py` to improve responses
2. Add new visualization types to both `ai_assistant.py` and the rule-based detection in `llm_assistant.py`
3. Enhance context gathering in the LLM integration for more accurate responses

## Troubleshooting

Common issues:

- **LLM Not Available**: Check that your API key is valid and correctly set
- **Slow Responses**: Consider switching to a faster model like GPT-3.5-Turbo
- **Inaccurate Visualization Detection**: Add more examples to the system prompt