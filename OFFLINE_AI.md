# Optional Offline AI for Render Browser

## Status

This is an optional, separate inference service. It is not part of the browser container and is not deployed until you explicitly create it from `render-ai.yaml` in Render.

## Model

- Qwen2.5-0.5B-Instruct GGUF, Q4_K_M quantization.
- Official model: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF
- The Q4_K_M variant is listed at approximately 491 MB and the model is Apache-2.0 licensed.
- llama.cpp provides an official server container and supports Hugging Face model downloads with `-hf`.

This is a small starter model, not a high-capability assistant. It may make mistakes and its Azerbaijani/Turkish quality must be tested; do not rely on it for important decisions.

## Deploy the AI service (manual opt-in)

1. In Render, create a new Blueprint from this repository and set the Blueprint file to `render-ai.yaml`.
2. Select the same region as the existing browser service so private networking can work.
3. Review the selected compute plan and persistent-disk cost in Render before applying. This Blueprint creates a paid private service and a 2 GB persistent disk; do not apply it unless you approve those costs.
4. Enter a new, unique, long random value for `LLAMA_API_KEY` when prompted. Do not reuse the browser password or any account password.
5. Apply the Blueprint and wait for the AI service health check at `/health` to pass.
6. The first boot downloads the model and needs internet. The cache is stored under `/data/huggingface-cache`; subsequent starts reuse the persisted cache.

The service is private and has no public URL. Keep `LLAMA_API_KEY` secret. The model server's built-in file/agent tools are not enabled.

## Connect the browser to the AI service

After the AI service is healthy, open its Render Dashboard **Connect > Internal** section and copy its internal HTTP address. In the existing browser Web Service Environment, set:

- `AI_SERVICE_URL`: the AI service internal address, including `http://` and port `10000`, with no trailing slash.
- `AI_API_KEY`: the exact same base64-style key entered as `LLAMA_API_KEY` for the AI service.

Redeploy the browser service. Open `/ai/` on the browser URL while signed in with the browser Basic Auth credentials. The page sends requests to the browser service's `/ai-api/` route; Nginx injects the API key server-side and forwards requests over Render private networking. The key is not sent to browser JavaScript. Keep the AI service private and do not expose it publicly.

The chat UI is intentionally minimal and sends non-streaming chat requests with a short output limit.

## Offline meaning

After the model is downloaded and cached, text generation runs on the AI service without calling an external model API. The browser itself still needs internet to access websites such as Replit. Initial setup/model download also needs internet.

## Important limitations

- This small model is not comparable to a large hosted assistant.
- Model file size is not the same as required RAM; inference also needs memory for runtime, context, and KV cache. Measure on the selected Render plan.
- A Render service staying awake does not guarantee a Replit workspace stays active. Replit controls its own idle/session behavior.
- Do not use periodic pings or scripted browser actions to evade another provider's idle/session rules.
- Do not commit model weights, browser profiles, credentials, or API keys to Git.
