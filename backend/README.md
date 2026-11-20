# NITRO Core — self-hosted inference (v0.1)

This is the first real model-serving foundation for NITRO. The website remains static on GitHub Pages, while inference runs on a server you control. The gateway forwards requests only to the local llama.cpp service; it does not call a commercial model API.

## Starter model

- Model: `Qwen/Qwen2.5-1.5B-Instruct-GGUF`
- Quantization: `Q4_K_M`
- Context: 4,096 tokens
- Runtime: llama.cpp CPU mode
- API: OpenAI-compatible `POST /v1/chat/completions`

This small model is a starter, not a frontier-level assistant. Persian quality, reasoning, and speed will be limited compared with larger models. The 8 GB computer is not the public server: deploy this stack on a cloud machine. A 1.5B Q4 model is a low-cost starting point; public multi-user use will benefit from more RAM, CPU cores, and eventually a GPU.

## Run on a Linux server

Install Docker Engine and the Docker Compose plugin, clone this repository, then run:

```bash
docker compose up -d --build
docker compose logs -f llama
```

The first startup downloads the GGUF model and can take a while. Once both services are healthy, check:

```bash
curl http://localhost:8080/health
```

The gateway listens on port 8080. Put it behind HTTPS using Caddy, Nginx, or your cloud provider's TLS proxy. Do not expose the llama service port 8081 publicly.

## Connect GitHub Pages

Edit the root `config.js` and set:

```js
window.NITRO_CONFIG = { API_URL: "https://YOUR-HTTPS-API-DOMAIN" };
```

Commit and push that change. The browser calls the gateway's `/v1/chat/completions` endpoint. Keep this file public-safe: never place a secret key in it.

## Public launch safeguards

The starter gateway has basic per-IP in-memory limits (12 requests/minute and 200/day by default), a 12,000-character request limit, a 24-message conversation limit, and a 512-token output cap. These limits reset when the process restarts and are not shared between replicas. Before a large public launch, add Redis-backed rate limits, user accounts/quotas, abuse monitoring, request logging with privacy controls, and a managed HTTPS domain. Restrict `NITRO_CORS_ORIGINS` to the GitHub Pages origin.

## Important limitations

- This is self-hosted open-weight inference, not a model trained from scratch by NITRO.
- Model weights are downloaded from Hugging Face at first server start; after download, inference is local to your server.
- The initial deployment requires internet access to download the model and install containers.
- CPU inference can be slow, especially with concurrent users. The frontend computer's 8 GB RAM does not increase cloud capacity.
- Image and 3D generation are separate modules and are not powered by this text model yet.
