<p align="center">
  <img src="assets/reconnator-banner.jpeg" alt="ReconnatoR" width="972">
</p>

# Reconnator 2.1.0: The AI Powered Reconnaisance Tool

**Reconnator** has evolved. What started as a simple, scheduled passive reconnaissance script is now a fully interactive, AI-driven Reconnaisance assistant. Powered by a provider-agnostic agent core and the Model Context Protocol (MCP), Reconnator can use local or hosted models through an OpenAI-compatible API.

It orchestrates vulnerability scanning, dynamically routes tools, and seamlessly integrates into modern infrastructure (Docker/Kubernetes) using a container-native attack architecture.

---

#### A Quick Note on the Codebase
   *If you dive into this tool's directory, you might notice something intense. I've added massive, obnoxious `# ==================== #` comment banners to the top of **literally every single file** (Python, Dockerfiles, YAMLs, you name it) so  you (and I) don't get lost in the sauce.*

---

## Key Features (v2.x Architecture)

- 🧠 **Provider-Agnostic AI + MCP:** Use local Qwen models through Ollama, vLLM, LM Studio, or llama.cpp, connect another OpenAI-compatible endpoint, or retain Gemini as an optional provider.
- 🔐 **Policy-Gated Tool Calls:** Active scanners require a configured Telegram operator, explicit target scope, and runtime approval. Unknown and out-of-scope tools are denied before reaching MCP.
- 🐳 **Ephemeral Docker Workers (DooD):** Attack engines (Nmap, Ffuf, Nuclei, Subfinder) are executed asynchronously inside disposable Docker containers (`--rm`). This prevents dependency hell and keeps the host system squeaky clean.
- 📄 **PDF Reporting:** Automatically compiles raw JSON scan data into a clean, professional PDF report sent directly to your Telegram chat.
- ☸️ **Always-On Kubernetes Daemon:** Transitioned from a legacy CronJob to a 24/7 Kubernetes `Deployment` using Docker-out-of-Docker (DooD) socket mounting for enterprise-grade scalability.
- 🛡️ **Resilient Tooling:** Built-in fallbacks (e.g., if Subfinder fails, automatically queries AlienVault OTX) and automated template baking for tools like Nuclei.

---

## 📚 Documentation

The complete operational and development documentation is available in the
[Reconnator Wiki](https://github.com/amiencoy/Reconnator/wiki).

Start with:

- [Getting Started](https://github.com/amiencoy/Reconnator/wiki/Getting-Started)
- [Architecture Overview](https://github.com/amiencoy/Reconnator/wiki/Architecture-Overview)
- [Deployment](https://github.com/amiencoy/Reconnator/wiki/Deployment)
- [Security and Responsible Use](https://github.com/amiencoy/Reconnator/wiki/Security-and-Responsible-Use)
- [Troubleshooting](https://github.com/amiencoy/Reconnator/wiki/Troubleshooting)
- [Local and Self-Hosted Models](docs/LOCAL_MODELS.md)

---

## Quick Start

Ensure you have Python 3.11+ installed and the **Docker Engine** running on your host (Reconnator needs access to the Docker daemon to spawn its tools' containers).

### Option 1: Running Locally (Docker-out-of-Docker)

```bash
# Clone the repository
git clone [https://github.com/yourusername/reconnator.git](https://github.com/yourusername/reconnator.git)
cd reconnator

# Setup Environment Variables (Rename the example file)
cp .env.example .env

# Edit .env. Configure Telegram plus your selected local or hosted AI provider.
nano .env

# Build the main Reconnator bot image
docker build -t reconnator:2.1.0 .

# Run the Bot 24/7 (CRITICAL: Mount the docker.sock!)
docker run -d \
  --name reconnator-bot \
  --add-host=host.docker.internal:host-gateway \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --env-file .env \
  reconnator:2.1.0

```

For a host Ollama instance, set `AI_BASE_URL=http://host.docker.internal:11434/v1/chat/completions`
inside `.env`. Before scanning, authorize an exact engagement scope:

```text
/authorize example.com ticket=ENG-001
scan example.com with nmap, ffuf and nuclei
/revoke
```

### Option 2: Kubernetes & Helm

Deploy Reconnator in your Kubernetes cluster (e.g., K3s, Minikube, EKS). *Note: Ensure your node's runtime supports Docker sockets.*

```bash
# Navigate to the Helm directory
cd deploy/helm

# Install the chart and inject secrets dynamically
helm install recon-bot . \
  --set telegram.botToken="YOUR_TELEGRAM_TOKEN" \
  --set telegram.allowedChatIds="YOUR_TELEGRAM_CHAT_ID" \
  --set ai.provider="ollama" \
  --set ai.model="qwen3:8b" \
  --set ai.baseUrl="http://ollama.default.svc.cluster.local:11434/v1/chat/completions"

```

---

## 📂 Project Structure

```text
.
├── .github/workflows/    # CI/CD pipelines (Auto GHCR publishing)
├── deploy/helm/          # Kubernetes Helm Chart (Deployment + DooD)
├── src/                  # Core Application
│   ├── agent_core/       # Provider, MCP, prompt, and policy runtime
│   ├── config/           # Agent policy-as-code
│   ├── modules/          # Ephemeral Engines (nmap, ffuf, nuclei, subfinder, otx, report)
│   ├── modules/agent_core.py # Reconnator consumer adapter
│   ├── mcp_server.py     # The Arsenal: MCP tool registration & schema mapping
│   └── bot.py            # The Mouth & Ears: Telegram ChatOps entrypoint
├── Dockerfile            # Main Alpine-based bot container
├── Dockerfile.ffuf       # Custom multi-stage build for Ffuf + SecLists
├── Dockerfile.nmap       # Minimal Nmap + NSE container
├── Dockerfile.nuclei     # Nuclei container with pre-baked vulnerability templates
├── .env.example          # Environment variable blueprint
└── requirements.txt      # Python dependencies (aiogram, fastmcp, httpx)

```

---

## 🗺️ Roadmap

* [x] Integrate Nmap for deep port & service mapping.
* [x] Integrate Ffuf with baked-in SecLists for directory fuzzing.
* [x] **Layer 3 AI Analysis:** Implement provider-agnostic AI and MCP orchestration.
* [x] Support self-hosted OpenAI-compatible models with policy-gated tool calls.
* [x] Automated report generation (PDF output).
* [ ] Implement multi-target parallel scanning capabilities.
* [ ] Add continuous monitoring diffs (alerting only on *new* vulnerabilities).

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Before participating,
read the [Contributing Guidelines](CONTRIBUTING.md) and
[Code of Conduct](CODE_OF_CONDUCT.md).

Do not report vulnerabilities through public issues. Follow the
[Security Policy](SECURITY.md) for private disclosure.

## 💖 Support Reconnator

Reconnator is developed and maintained as an open-source project. Sponsorships help support ongoing maintenance, security-tool integrations, testing, documentation, and future releases.

[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?logo=githubsponsors)](https://github.com/sponsors/amiencoy)

Sponsorship supports the project's open-source development and does not include guaranteed support, service-level agreements, custom integrations, or consulting. Commercial deployment and engineering services are handled separately through Draxis Digital.

## 📦 Releases and Versioning

Reconnator follows [Semantic Versioning](https://semver.org/). The current
release is **v2.1.0**. See the [GitHub Releases](https://github.com/amiencoy/Reconnator/releases),
[Changelog](CHANGELOG.md), and [Release Guide](RELEASING.md) for details.

## 📄 License

Reconnator is dual-licensed under either the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), at your option. See [LICENSE](LICENSE) for the dual-license declaration.

SPDX license expression: `MIT OR Apache-2.0`.

---


<p align="center">
  <i><small>Built with code and coffee by amiencoy</small></i>
</p>
