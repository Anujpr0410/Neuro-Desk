# Deploying NeuroDesk AMD on AMD Developer Cloud

This guide shows how to deploy NeuroDesk AMD using AMD Developer Cloud with MI300X GPUs.

## Prerequisites

- AMD Developer Cloud account
- Basic familiarity with Linux and Python

## Step 1: Sign Up for AMD Developer Cloud

1. Visit [AMD Developer Cloud](https://developer.amd.com/)
2. Sign up for an account
3. Request access to AMD Instinct MI300X instances

## Step 2: Launch an AMD MI300X VM

### Using AMD Developer Cloud Portal
1. Navigate to the VM provisioning section
2. Select **AMD Instinct MI300X** instance type
3. Choose a Quick Start image (Ubuntu 22.04 recommended)
4. Configure instance size (MI300X-24GB recommended)
5. Click "Launch Instance"

### Using CLI (if available)
```bash
# Example using AMD CLI (if available)
amd instance create \
    --type mi300x \
    --os ubuntu-22-04 \
    --name neurodesk-vm \
    --region us-east
```

## Step 3: Connect to Your Instance

```bash
ssh -i ~/.ssh/your-key.pem ubuntu@<instance-ip>
```

## Step 4: Install ROCm and Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install ROCm
wget https://repo.radeon.com/amd-configure.sh
chmod +x amd-configure.sh
sudo ./amd-configure.sh

# Verify ROCm installation
rocminfo | grep -A 10 "Agent Name"

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip
```

## Step 5: Install vLLM for LLM Serving

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install vLLM with ROCm support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0
pip install vllm

# OR install SGLang (alternative)
# pip install --force-reinstall --no-cache-dir --upgrade sgl-kernel
# pip install sglang[all]
```

## Step 6: Download and Serve a Model

### Option A: Using vLLM

```bash
# Pull and serve a model
python3.11 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype auto \
    --max-model-len 4096
```

### Option B: Using SGLang

```bash
# Serve with SGLang
python3.11 -m sglang.launch_server \
    --model-path Qwen/Qwen2.5-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000
```

### Option C: Using Llama 3.1

```bash
# Serve Llama 3.1 (8B)
python3.11 -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --host 0.0.0.0 \
    --port 8000
```

**Note:** The endpoint should now be available at `http://<instance-ip>:8000/v1` with OpenAI-compatible API.

## Step 7: Configure NeuroDesk AMD

### Option A: Using Web Setup
1. Clone the NeuroDesk AMD repository
2. Run `python setup.py --mode web`
3. Navigate to the web interface
4. Configure SAB1, SAB2, SAB3 to use:
   - Provider: **AMD Cloud (vLLM)**
   - Model: **Qwen/Qwen2.5-7B-Instruct** (or your model)
   - Base URL: **http://localhost:8000/v1**

### Option B: Manual Configuration

Edit `config/config.json`:
```json
{
  "MAB": {
    "provider": "AMD Cloud (vLLM)",
    "api_key": "",
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "base_url": "http://localhost:8000/v1"
  },
  "SAB1": {
    "provider": "AMD Cloud (vLLM)",
    "api_key": "",
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "base_url": "http://localhost:8000/v1"
  },
  "SAB2": {
    "provider": "AMD Cloud (vLLM)",
    "api_key": "",
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "base_url": "http://localhost:8000/v1"
  },
  "SAB3": {
    "provider": "AMD Cloud (vLLM)",
    "api_key": "",
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "base_url": "http://localhost:8000/v1"
  }
}
```

## Step 8: Start NeuroDesk AMD

```bash
# Clone repository (if not already done)
git clone https://github.com/neurodesk-amd/neurodesk-amd.git
cd neurodesk-amd

# Install dependencies
pip install -r requirements.txt

# Start the application
python main.py --mode web
```

The web interface will be available at `http://<instance-ip>:8000`

## Step 9: Verify AMD Acceleration

1. Navigate to the **Performance** tab
2. Run a benchmark or campaign
3. Check that "AMD Cloud (vLLM)" shows as the provider
4. Verify performance metrics in the dashboard

---

## Testing the Deployment

### Check vLLM endpoint
```bash
curl http://localhost:8000/v1/models
```

Expected output:
```json
{
  "object": "list",
  "data": [
    {
      "id": "Qwen/Qwen2.5-7B-Instruct",
      "object": "model",
      "created": 1234567890,
      "owned_by": "vllm"
    }
  ]
}
```

### Test inference
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7
  }'
```

---

## Troubleshooting

### Issue: "AMD GPU not found"
- Ensure ROCm is properly installed: `rocminfo`
- Check GPU is available: `ls /dev/kfd`
- Verify user has permissions: `usermod -a -G render,video ubuntu`

### Issue: "Model not found"
- Ensure model name matches vLLM model list
- Check model was properly downloaded to cache

### Issue: "Connection refused on port 8000"
- Verify vLLM is running: `ps aux | grep vllm`
- Check firewall settings
- Ensure binding to 0.0.0.0, not localhost

### Issue: "Out of memory"
- Reduce `max-model-len` in vLLM command
- Use smaller model (7B instead of 13B/70B)
- Increase swap space

---

## Performance Tuning

### For Maximum Throughput
```bash
python3.11 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype float16 \
    --max-model-len 32768 \
    --tensor-parallel-size 1 \
    --enable-lora
```

### For Low Latency
```bash
python3.11 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype bfloat16 \
    --enable-chunked-prefill
```

---

## Cleaning Up

When done with your session:
```bash
# Stop vLLM server (Ctrl+C)
# Stop NeuroDesk (Ctrl+C)
# Terminate instance via AMD Developer Cloud portal
```

---

## Next Steps

- Explore more open-source models on Hugging Face
- Try different model sizes (7B, 14B, 70B)
- Compare performance across different AMD GPU types
- Deploy to Hugging Face Spaces for public access

---

*For AMD Developer Cloud support, visit https://developer.amd.com/support/*