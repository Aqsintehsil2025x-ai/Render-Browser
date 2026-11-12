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

## First test on your own PC (Linux)

You do not need Render for this test. The first setup/download needs internet, but after the model is cached you can disconnect and run it locally.

1. On Linux, install the official llama.cpp command-line app with `curl -LsSf https://llama.app/install.sh | sh`, then open a new terminal and check `llama --version`. This install command is from the llama.cpp team's official installation guide.
2. In this repository, run `bash local-ai.sh`. It downloads/caches Qwen2.5-0.5B-Instruct Q4_K_M and starts the local model API on `127.0.0.1:8080`, plus this chat page on `127.0.0.1:8000`.
4. Open `http://127.0.0.1:8000`, set API base URL to `http://127.0.0.1:8080/v1`, model ID to `Qwen/Qwen2.5-0.5B-Instruct-GGUF:Q4_K_M`, leave API key blank, and press Apply settings.
5. After the first download has completed, stop the script with Ctrl+C, disconnect from the internet, run `bash local-ai.sh` again and test another message. The model should use its local cache. Keep the local server running while chatting.

The script binds both services to `127.0.0.1` so they are not exposed to your LAN. It allows the localhost origin because the chat page and local model API use different local ports. The model is assigned the same alias as the Model ID field.

## Add another API

Open **Model / API settings** on the chat page. Enter the provider's OpenAI-compatible base URL, model ID, and (if required) API key, then apply. The key is held only in the current tab's memory and is cleared when the tab is closed or refreshed; it is not written to local storage or Git. Only use providers you trust. Provider API use requires internet and may have separate costs. Some providers block browser-origin requests (CORS); use their supported client or a trusted same-origin backend rather than disabling browser security.

## Offline meaning

After the model is downloaded and cached, text generation runs on the AI service without calling an external model API. The browser itself still needs internet to access websites such as Replit. Initial setup/model download also needs internet.

## Important limitations

- This small model is not comparable to a large hosted assistant.
- Model file size is not the same as required RAM; inference also needs memory for runtime, context, and KV cache. Measure on the selected Render plan.
- A Render service staying awake does not guarantee a Replit workspace stays active. Replit controls its own idle/session behavior.
- Do not use periodic pings or scripted browser actions to evade another provider's idle/session rules.
- Do not commit model weights, browser profiles, credentials, or API keys to Git.
