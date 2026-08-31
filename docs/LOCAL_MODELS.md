# Local and Self-Hosted AI Providers

Reconnator uses an OpenAI-compatible chat-completions contract. Gemini remains an
optional provider, but the default configuration runs Qwen through Ollama.

## Optional Gemini fallback

Keep the local or OpenAI-compatible provider as the primary configuration, then add:

```env
GEMINI_API_KEY=your-google-ai-studio-key
GEMINI_MODEL=gemini-3.5-flash-lite
```

The key's presence opts in to automatic failover. Reconnator calls Gemini only when
the primary provider cannot connect, times out, returns an HTTP error, or produces an
invalid chat-completions response. If a custom provider is selected but its endpoint
or model is missing, Gemini starts directly. When the primary provider is healthy,
no prompt or tool schema is sent to Gemini.

Fallback changes only model transport. Authorization, scope validation, tool policy,
and MCP execution remain enforced by the same agent runtime. Remove
`GEMINI_API_KEY` to guarantee local-only inference.

## Ollama

```bash
ollama pull qwen3:8b
ollama serve
```

When Reconnator runs directly on the same host:

```dotenv
AI_PROVIDER=ollama
AI_MODEL=qwen3:8b
AI_BASE_URL=http://localhost:11434/v1/chat/completions
AI_API_KEY=
AI_TEMPERATURE=0
AI_TIMEOUT_SECONDS=300
```

When Reconnator runs in Docker, use the host gateway:

```dotenv
AI_BASE_URL=http://host.docker.internal:11434/v1/chat/completions
```

Run the container with `--add-host=host.docker.internal:host-gateway` on Linux.

## vLLM

Start vLLM with a model and tool-calling configuration supported by that model. Then:

```dotenv
AI_PROVIDER=vllm
AI_MODEL=Qwen/Qwen3-8B
AI_BASE_URL=http://localhost:8000/v1/chat/completions
AI_API_KEY=
```

## LM Studio

Load a tool-capable model, start LM Studio's local API server, and configure:

```dotenv
AI_PROVIDER=lmstudio
AI_MODEL=the-model-identifier-shown-by-lm-studio
AI_BASE_URL=http://localhost:1234/v1/chat/completions
AI_API_KEY=
```

## llama.cpp

Run `llama-server` with an appropriate chat template and tool-capable model:

```dotenv
AI_PROVIDER=llamacpp
AI_MODEL=local-model
AI_BASE_URL=http://localhost:8080/v1/chat/completions
AI_API_KEY=
```

## Custom endpoint

```dotenv
AI_PROVIDER=openai-compatible
AI_MODEL=your-model-id
AI_BASE_URL=https://your-endpoint.example/v1/chat/completions
AI_API_KEY=optional-or-required-by-your-server
```

## Model requirements

The selected model and server must support OpenAI-style function/tool calling. A model
that only returns prose can still answer questions, but cannot reliably invoke MCP
tools. Keep `AI_TEMPERATURE=0` for more deterministic tool arguments.

Local inference improves privacy and removes a hosted-provider dependency. It does not
eliminate hallucinations. Reconnator therefore filters tool schemas through an
allowlist and validates approval plus target scope before any MCP call executes.

Increase `AI_TIMEOUT_SECONDS` when a local model needs more time for its initial load.
