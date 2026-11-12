# Optional Offline AI for Render Browser

## Status

This is a deployment design, not an enabled feature yet. The browser image does not currently run an AI model. Keep AI disabled until a separate inference service has been deployed and tested.

## Recommended starter model

- Model: Qwen2.5-0.5B-Instruct, GGUF, Q4_K_M
- Publisher: Qwen
- Model repository: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF
- Approximate file size: 491 MB
- License shown on the model card: Apache-2.0
- Runtime: llama.cpp server (OpenAI-compatible API)

This is a small starter model, not a frontier-quality assistant. It can handle simple chat and short tasks, but its reasoning, coding, factual reliability, and Azerbaijani/Turkish output may be limited. Test it with real prompts before treating it as useful.

## Architecture

Keep the browser and model inference in separate Render services:

1. `render-browser`: Chromium/noVNC, protected by the existing browser Basic Auth.
2. `render-browser-ai`: llama.cpp server, with the GGUF model stored under `/data`.
3. The browser service may proxy an authenticated `/ai/` path to the AI service over Render's private network after that connection is configured and tested.

Do not run Chromium and the model in the same 512 MB Free instance. Render documents Free web services as 512 MB RAM, and the Q4_K_M model file itself is about 491 MB before runtime memory, context cache, and Chromium are counted. A separate AI service with more memory is the practical design; choose its plan based on measured RAM use.

## Model download and persistence

- Do not commit the `.gguf` model into Git. It is large and should be downloaded by the AI service on first startup.
- Set the model cache/model directory to `/data`.
- A persistent disk mounted at `/data` is needed if the model must survive service restarts and redeploys. Render documents persistent disks as paid-service storage; Free web services do not support them.
- The first model download requires internet. After it is cached, text generation can run locally on the AI service without calling an external model API. The overall browser still needs internet to open websites such as Replit.

## Required safeguards before enabling

- Keep the AI service private; do not expose an unauthenticated inference endpoint publicly.
- Require a long random `AI_API_KEY` and keep it only in Render Environment, never in GitHub.
- Do not enable llama.cpp's built-in file, shell, or agent tools. This project only needs text generation.
- Proxy requests through the authenticated browser service; do not put the AI key in browser JavaScript.
- Add request size, context length, output-token, and timeout limits.
- Do not use periodic pings or scripted browser actions to evade Replit or another provider's idle/session rules.

## Render constraints

- Render Free web services use 512 MB RAM, can spin down after inactivity, and do not support persistent disks or private networking.
- A separate private AI service and persistent model cache therefore require an appropriate paid Render setup. Check current plan pricing before enabling anything that may incur charges.
- A Render service staying awake does not guarantee a Replit workspace stays active. Replit controls its own session and idle behavior.

## Next implementation steps

1. Choose and provision a suitable AI service plan and persistent disk.
2. Add a pinned llama.cpp server image and startup configuration that downloads the model once into `/data`.
3. Configure the AI service API key and private networking.
4. Add an authenticated `/ai/` reverse-proxy route to the browser service.
5. Add a small chat page that calls only that same-origin proxy.
6. Test memory use, model startup, authentication, and chat end-to-end before enabling it.

No service, disk, model download, or paid resource is created by this documentation change.
