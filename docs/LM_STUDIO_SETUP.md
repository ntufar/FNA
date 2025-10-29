# LM Studio Setup for FNA

The Financial Narrative Analyzer (FNA) now uses **qwen/qwen3-4b-2507** model hosted on LM Studio instead of loading the model locally.

## Prerequisites

1. **Install LM Studio**: Download from https://lmstudio.ai/
2. **Download qwen/qwen3-4b-2507 model** in LM Studio
3. **Start the local server** in LM Studio

## LM Studio Configuration

### 1. Download the Model
- Open LM Studio
- Go to the "Discover" tab
- Search for `qwen/qwen3-4b-2507`
- Download the model (recommended: Q4_K_M quantization for balance of quality/speed)

### 2. Load the Model
- Go to "Chat" tab in LM Studio
- Select `qwen/qwen3-4b-2507` from the model dropdown
- Wait for the model to load completely

### 3. Start Local Server
- Go to "Local Server" tab in LM Studio
- Click "Start Server"
- Verify server is running on `http://127.0.0.1:1234`
- Keep this window open while using FNA

## Environment Configuration

Update your `.env` files with these LM Studio-specific settings:

```bash
# LLM Configuration (qwen/qwen3-4b-2507 via LM Studio)
MODEL_NAME=qwen/qwen3-4b-2507
MODEL_API_URL=http://127.0.0.1:1234
MODEL_API_TIMEOUT=30
MODEL_MAX_TOKENS=512
MODEL_TEMPERATURE=0.1
MODEL_TOP_P=0.9
```

## Testing the Setup

Run the LM Studio connectivity test:

```bash
cd backend
python scripts/test_lm_studio.py
```

Expected output:
```
🏗️ FNA LM Studio API Test Suite
==================================================
🔌 Testing LM Studio Connection
========================================
✅ Successfully connected to LM Studio
Available models: 1
  - qwen/qwen3-4b-2507

⚙️ Testing Model Configuration
========================================
Model Configuration:
  model_name: qwen/qwen3-4b-2507
  is_connected: True
  api_url: http://127.0.0.1:1234
  ...

🤖 Testing Text Generation
===================================
✅ All text generation tests passed!

🎉 All LM Studio tests passed!
```

## Troubleshooting

### Connection Failed
- ✅ Verify LM Studio is running
- ✅ Check model is loaded (not just downloaded)
- ✅ Confirm server is active on port 1234
- ✅ Try restarting LM Studio

### Generation Errors  
- ✅ Check model hasn't crashed in LM Studio
- ✅ Verify sufficient system memory
- ✅ Restart the local server in LM Studio

### Performance Issues
- ✅ Close unnecessary applications
- ✅ Use GPU acceleration if available
- ✅ Consider smaller quantization (Q4_0 instead of Q4_K_M)

## Benefits of LM Studio Approach

✅ **No Local Model Management**: No need to download/manage model files  
✅ **Easy Model Switching**: Change models in LM Studio GUI  
✅ **GPU Acceleration**: LM Studio handles GPU optimization  
✅ **Memory Efficiency**: Model loaded once, shared across applications  
✅ **Visual Monitoring**: Monitor model performance in LM Studio interface

## API Endpoints Used

- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Generate text completions

The FNA backend uses OpenAI-compatible API format for seamless integration.
