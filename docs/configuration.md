# Configuration

All configuration is read from a `.env` file in the project root (or next to the `.exe` for built distributions).

```bash
cp .env.example .env
# Edit .env with your credentials and preferences
```

## All Variables

| Variable | Default | Required | Description |
|---|---|---|---|
| `HOTKEY` | `right ctrl` | yes | Push-to-talk key name |
| `STT_ENGINE` | `yandex` | yes | Active STT engine: `yandex` or `openai` |
| `LANGUAGE` | `ru-RU` | no | BCP-47 recognition language code |
| `SAMPLE_RATE` | `16000` | no | Microphone sample rate in Hz |
| `MICROPHONE_INDEX` | *(empty)* | no | sounddevice device index; empty = system default |
| `HISTORY_SIZE` | `20` | no | Max items in tray recognition history |
| `SA_KEY_PATH` | `sa-key.json` | if Yandex | Path to Yandex service account authorized key JSON |
| `OPENAI_API_KEY` | *(empty)* | if OpenAI | OpenAI platform API key |

## Hotkey Examples

The `HOTKEY` value must be a key name recognized by the [`keyboard`](https://github.com/boppreh/keyboard) library.

```env
HOTKEY=right ctrl    # Right Control key (default)
HOTKEY=f9            # F9 function key
HOTKEY=scroll lock   # Scroll Lock
HOTKEY=pause         # Pause/Break key
HOTKEY=insert        # Insert key
HOTKEY=caps lock     # Caps Lock (disables its normal function)
```

Use keys that are unlikely to conflict with other applications. Media keys and function keys work well.

## Language Codes

| Code | Language |
|---|---|
| `ru-RU` | Russian (default) |
| `en-US` | English (US) |
| `en-GB` | English (UK) |
| `de-DE` | German |
| `fr-FR` | French |
| `es-ES` | Spanish |
| `tr-TR` | Turkish |

Yandex SpeechKit and OpenAI Whisper support different language sets. Whisper is generally language-agnostic; Yandex has explicit language model selection.

## Yandex SpeechKit Setup

Yandex SpeechKit requires a Yandex Cloud service account with the `ai.speechkit-stt.user` role.

### Step 1 — Create a service account

```bash
# Install Yandex Cloud CLI (yc)
# https://yandex.cloud/en/docs/cli/quickstart

yc iam service-account create --name push2talk-stt
```

### Step 2 — Grant the STT role

```bash
yc resource-manager folder add-access-binding <FOLDER_ID> \
  --role ai.speechkit-stt.user \
  --subject serviceAccount:<SERVICE_ACCOUNT_ID>
```

### Step 3 — Create an authorized key

```bash
yc iam key create \
  --service-account-name push2talk-stt \
  --output sa-key.json
```

Place `sa-key.json` in the project root (or next to the `.exe`) and set:

```env
STT_ENGINE=yandex
SA_KEY_PATH=sa-key.json
LANGUAGE=ru-RU
```

The app generates a JWT from this key, exchanges it for an IAM token, and refreshes automatically before expiry. The key file is never transmitted — only the derived IAM token is sent with API requests.

## OpenAI Whisper Setup

### Step 1 — Get an API key

Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys) and create a new secret key.

### Step 2 — Configure `.env`

```env
STT_ENGINE=openai
OPENAI_API_KEY=sk-...
LANGUAGE=ru-RU
```

The app uses the `gpt-4o-mini-transcribe` model endpoint.

## Microphone Selection

Leave `MICROPHONE_INDEX` empty to use the Windows system default microphone.

To use a specific device:

1. Run the app
2. Right-click the tray icon → **Microphone** submenu — device names and indices are listed
3. Note the index of the desired device (e.g. `[2] Headset Microphone`)
4. Set `MICROPHONE_INDEX=2` in `.env`

The microphone can also be switched at runtime from the tray without restarting.

Only WASAPI devices are listed (deduplicated; virtual devices and non-microphone inputs are filtered out).

## Switching Engines at Runtime

The tray menu **STT Engine** submenu allows switching between Yandex and OpenAI without restarting. The switch is validated — if the target engine lacks credentials it is silently rejected and a warning is logged.
