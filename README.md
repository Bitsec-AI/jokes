# Bittensor Roast Machine

A web app that generates roast jokes about the Bittensor (TAO) ecosystem, powered by decentralized AI inference.

**Live:** [bittensor-roast.fly.dev](https://bittensor-roast.fly.dev)

## How It Works

A small language model (Qwen3-0.6B) is deployed via [Basilica](https://x.com/basilic_ai) and prompted with curated comedy techniques and Bittensor factoids to produce original roast jokes on demand. No OpenAI, no centralized APIs — just a subnet owner getting roasted by decentralized compute.

- Click "Roast" and get a fresh joke in seconds
- 7 comedy styles: Misdirection, Rule of Three, Exaggeration, and more
- 100+ jokes and counting, all browsable with filtering and pagination

## Built With

### [BitSec](https://x.com/bitsecai)

AI-powered security for the Bittensor ecosystem. BitSec builds tools that keep subnets, miners, and validators safe — and occasionally roasts them. This is a fun MVP project to test Basilica's inference layer.

### [Basilica](https://x.com/basilic_ai)

Decentralized LLM inference on Bittensor. Basilica makes it dead simple to deploy and serve open-source models via vLLM — one API call and your model is live. No GPU provisioning, no infra headaches. This app runs entirely on Basilica's inference layer.

## Setup

```bash
git clone https://github.com/Bitsec-AI/jokes.git
cd jokes
python -m venv venv
pip install -r requirements.txt
echo 'BASILICA_API_TOKEN=basilica_...' > .env
python app.py
```

Get a Basilica API token at [basilica.ai](https://basilica.ai).

## Stack

- **Model:** Qwen3-0.6B via Basilica vLLM
- **Backend:** Flask + Gunicorn
- **Hosting:** Fly.io (auto-scales to zero)
- **CI/CD:** GitHub Actions → Fly.io on push to main
