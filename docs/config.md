# Configuration Guide for Lead Generation AI Agent

This document explains how to configure the LLM and agent settings for the Lead Generation AI Agent system.

## Configuration Options

| Option        | Description                                 | Default (constants.py) |
|--------------|---------------------------------------------|------------------------|
| `model`      | LLM model name (e.g., gpt-4o-mini)          | gpt-4o-mini            |
| `temperature`| LLM sampling temperature (0.0 - 1.0)        | 0.0                    |
| `max_tokens` | Max tokens for LLM responses                | 500                    |
| `api_key`    | OpenAI API key                              | (from .env)            |

## Configuration Precedence

The system loads configuration in the following order of precedence (highest to lowest):

1. **Environment Variables**
   - `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `OPENAI_API_KEY`
2. **`config/config.yaml`** (if present)
3. **`config/default_config.yaml`** (auto-created if no config.yaml exists)
4. **`lib/constants.py`** (hardcoded defaults)

## How to Override Configuration

### 1. Using Environment Variables
Set environment variables before running the app:

```sh
export LLM_MODEL="gpt-4o-mini"
export LLM_TEMPERATURE="0.2"
export LLM_MAX_TOKENS="800"
export OPENAI_API_KEY="sk-..."
```

### 2. Using `config/config.yaml`
Create or edit `config/config.yaml`:

```yaml
model: gpt-4o-mini
temperature: 0.1
max_tokens: 600
api_key: sk-...
```

### 3. Fallback: `config/default_config.yaml`
If `config/config.yaml` does not exist, the system will create and use `config/default_config.yaml` with default values.

### 4. Hardcoded Defaults
If no config files or environment variables are set, the system uses values from `lib/constants.py`.

## Example: Full Precedence
If you set `LLM_MODEL` in your environment, but leave other values in `config.yaml`, only the model will be overridden by the environment variable. All other values will come from `config.yaml` or the default.

## Adding New Config Options
To add new options, update:
- `lib/constants.py` for the default
- `lib/config_loader.py` to load and merge the new option
- Document the new option here

---
For any questions, see the code in `lib/config_loader.py` or contact the project maintainer. 