# Perfume AI Finder

A conversational Telegram bot that helps users choose perfume from a curated catalogue and answers questions about perfumery. Built with Python, the Telegram Bot API and Anthropic's Claude API.

The project combines a structured JSON product catalogue, prompt design and per-user conversation history in a small deployable application.

**[Watch the video demo](https://drive.google.com/file/d/1Iv9Grlx2aTAagVSzos6uJSqutIIFolaw/view)**

## What the bot does

- Accepts natural-language requests about fragrance preferences, notes and occasions.
- Uses a catalogue of 20 perfumes as context for recommendations.
- Instructs Claude to suggest 2–3 fragrances from the catalogue and explain the choices.
- Answers general perfumery questions, with a prompt requesting concise answers of up to 900 characters.
- Keeps a separate conversation history for each Telegram user, allowing follow-up questions and refinement of preferences.
- Instructs Claude to reply in the user's language and redirect unrelated questions towards perfumery.

Example requests:

> I like woody fragrances with vanilla, but nothing too sweet. What would you suggest?
>
> Which of these would work better for everyday wear?
>
> What is the difference between top, middle and base notes?

## How it works

```text
Telegram user
    |
    v
bot.py: receive a text message and identify the user
    |
    v
prompt_templates.py: wrap the request
    |
    v
Claude Messages API
    - system instructions
    - full JSON perfume catalogue
    - up to 12 recent conversation messages
    |
    v
bot.py: store the answer and send it back to Telegram
```

1. At startup, `ga_utils.py` loads `GA_perfume_base.json`. The catalogue is serialized into a dedicated context message.
2. `/start` sends a welcome message and displays a start button. Text messages can also be processed without first using the command.
3. Each request is added to the history associated with the user's Telegram ID. `make_claude_prompt()` wraps the text as a user request.
4. The Claude API receives the system prompt, the full catalogue and the recent conversation. The catalogue is included with every API call, while the conversation history is trimmed to 12 messages.
5. The model's reply is stored in the user's history and returned as a Telegram message.

The system prompt defines the assistant's role, recommendation rules, language and response style. Catalogue-only recommendations and response-length limits are prompt instructions; generated replies are not validated against these rules in code.

## Repository structure

```text
perfume-AI-finder/
├── bot.py                  # Telegram handlers, Claude calls, prompts and user history
├── GA_perfume_base.json    # Catalogue of 20 perfumes with product details
├── ga_utils.py             # JSON catalogue loader
├── prompt_templates.py     # User-request prompt helper
├── requirements.txt        # Python dependencies
├── Procfile                # Worker entry point: python bot.py
├── .gitignore              # Excludes the local .env file
├── example                 # Empty placeholder file
└── README.md
```

The catalogue contains product names, brands, fragrance families, top/middle/base notes, perfume types, volumes, countries, manufacturers, prices, article numbers and product URLs. It is a static snapshot; the bot does not refresh prices or availability from the retailer.

## Technology stack

| Component | Implementation |
| --- | --- |
| Language | Python |
| Telegram interface | `python-telegram-bot==20.7`, long polling |
| Language model API | Anthropic Python SDK, Messages API |
| Product context | Local JSON catalogue supplied in the prompt |
| Conversation state | In-memory dictionary keyed by Telegram user ID |
| Configuration | Environment variables loaded with `python-dotenv` |
| Deployment entry point | `Procfile` worker |

## Run locally

You need Python 3, a Telegram bot token and an Anthropic API key with access to a supported Claude model.

### 1. Clone the repository and install dependencies

```bash
git clone https://github.com/tomabes/perfume-AI-finder.git
cd perfume-AI-finder
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure credentials

Create a `.env` file in the repository root:

```dotenv
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ANTHROPIC_API_KEY=your_anthropic_api_key
```

Create the Telegram token with [BotFather](https://t.me/BotFather). The `.env` file is excluded from Git by the existing `.gitignore`.

### 3. Check the model setting

The committed version of `bot.py` specifies `claude-3-7-sonnet-20250219` in `claude.messages.create()`. This model has been retired. Before running the bot, replace that `model` value with a supported model available to your Anthropic account. See Anthropic's [model deprecation documentation](https://platform.claude.com/docs/en/about-claude/model-deprecations).

The API call also sets `max_tokens=1024` and `temperature=0.7`.

### 4. Start the bot

Run from the repository root so the catalogue file can be found:

```bash
python bot.py
```

Open your bot in Telegram, send `/start` and describe the kind of fragrance you are looking for. Each text request makes a Claude API call and uses the account's API credits.

## Deployment

The repository includes a worker process definition:

```procfile
worker: python bot.py
```

For a worker deployment on Railway or a similar host:

1. Connect the repository and install dependencies from `requirements.txt`.
2. Set `TELEGRAM_BOT_TOKEN` and `ANTHROPIC_API_KEY` in the host's environment settings.
3. Check that the configured Claude model is supported.
4. Use `python bot.py` as the start command, with the repository root as the working directory.

The bot uses long polling and needs a continuously running worker process. A public HTTP endpoint is not required.

## Scope and limitations

- **Static catalogue:** recommendations use the 20 records bundled with the project. Product information may become outdated.
- **Prompt-based constraints:** the model is instructed to recommend catalogue items, but there is no separate output-validation step or recommendation-quality benchmark.
- **Temporary conversation state:** history is held in process memory and is lost when the worker restarts. Running multiple workers would require shared state.
- **API dependency:** responses depend on Anthropic API access, model availability and usage limits. The synchronous Claude call runs inside the asynchronous Telegram handler.
- **Data flow:** user messages, recent conversation history and the perfume catalogue are sent to Anthropic to generate responses.

The demo shows the application workflow; the repository documents the implementation and the configuration needed to run it with a currently supported model.
