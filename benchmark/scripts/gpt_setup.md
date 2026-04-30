# GPT API Setup via Sub2API

## Option A: Use Sub2API relay service (推荐)

Sub2API converts ChatGPT/Claude subscriptions to OpenAI-compatible API keys.

### If self-hosting sub2api:
Sub2API is a full web service (Go + Vue + PostgreSQL + Redis).
Requires Docker Compose deployment — not feasible to run inline.

**Quick check: does user have an existing sub2api endpoint?**
If you have an endpoint like `https://your-sub2api.com/v1`, just set:
```bash
export GPT_API_KEY="your-key-from-sub2api"
export GPT_API_BASE="https://your-sub2api.com/v1"
export GPT_MODEL="gpt-4o"
```

### If using official sub2api demo / PinCC:
1. Visit https://shop.pincc.ai/ (official sub2api partner)
2. Or try https://demo.sub2api.org/ (shared demo, limited quota)
3. Get an API key
4. Set env vars above

## Option B: Direct OpenAI API
If you have an OpenAI API key directly:
```bash
export GPT_API_KEY="sk-..."
export GPT_API_BASE=""   # leave empty for official endpoint
export GPT_MODEL="gpt-4o"   # or gpt-4.1 when available
```

## Option C: Any OpenAI-compatible relay
Any relay that supports `/v1/chat/completions` with image inputs works:
```bash
export GPT_API_KEY="your-relay-key"
export GPT_API_BASE="https://your-relay.com/v1"
export GPT_MODEL="gpt-4o"
```

## Test GPT connection:
```bash
env -u HTTP_PROXY -u HTTPS_PROXY \
python3 benchmark/scripts/infer.py \
    --manifest benchmark/manifests/full_manifest.json \
    --split calibration \
    --backend gpt \
    --variant v1_normal_first \
    --output benchmark/results/sanity_gpt_v1.json \
    --domains D1 \
    --max_items 3 \
    --max_workers 1
```

## Cost estimate for full experiment (D1+D5 only):
- Calibration (40 items × 4 variants × 2 backends): ~$5-10 GPT + ~$1 SeedVL
- Development (80 items × 3 variants × 2 backends): ~$8-15 GPT + ~$2 SeedVL
- Full test (240 items × 3 variants × 2 backends): ~$20-40 GPT + ~$5 SeedVL
- Total (D1+D5 only): ~$35-65 GPT
- With all 8 domains: scale up 4x → ~$140-260 GPT (within $280 budget)
