new version: https://github.com/shareui/tele-stats

# GitLab Statistics Bot

A Telegram bot that automatically collects and displays programming language statistics from your GitLab repositories.

## Features

- **Automatic Statistics Collection**: Periodically scans all your personal GitLab repositories
- **Language Analysis**: Counts lines of code for each programming language
- **Telegram Integration**: Posts formatted statistics to your Telegram channel
- **Message Updates**: Updates the same message instead of spamming new ones
- **Customizable**: Configure update intervals, language mappings, and display limits
- **Health Check**: Built-in HTTP endpoint for monitoring

## What It Does

The bot analyzes all your personal GitLab repositories and generates statistics including:
- Total lines of code
- Percentage breakdown by programming language
- Favorite (most-used) language
- Repository count (total and public)
- Last activity timestamp

Statistics are automatically posted to your specified Telegram channel and updated on schedule.

## Installation

### Prerequisites

- Python 3.8 or higher
- GitLab account with personal access token
- Telegram bot token (from [@BotFather](https://t.me/botfather))
- Telegram channel where you want to post statistics

### Step 1: Clone the Repository

```bash
git clone https://github.com/shareui/GitLab-statistic.git
cd gitstats
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure the Bot

Create configuration file at `scl/config.scl`

### Step 4: Get Required Tokens

#### Telegram Bot Token:
1. Open [@BotFather](https://t.me/botfather) in Telegram
2. Send `/newbot` and follow instructions
3. Copy the token provided

#### Telegram Channel ID:
1. Create a channel or use existing one
2. Add your bot as administrator
3. Forward any message from the channel to [@userinfobot](https://t.me/userinfobot)
4. Copy the channel ID (starts with -100)

#### GitLab Private Token:
1. Go to GitLab → Settings → Access Tokens
2. Create new token with `read_api` and `read_repository` scopes
3. Copy the generated token

### Step 5: Run the Bot

```bash
python main.py
```

The bot will:
- Start immediately and post first statistics after 10 seconds
- Continue updating statistics every 24 hours (configurable)
- Run health check server on port 8000

## Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `interval_hours` | Hours between statistics updates | 24 |
| `max_displayed_languages` | Maximum languages shown in output | 10 |
| `force_message_id` | Pin to specific message ID (0 = auto) | 0 |
| `max_file_lines` | Maximum lines to count per file | 10000 |
| `health_check.port` | Health check HTTP server port | 8000 |

## Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Build and run:

```bash
docker build -t gitlab-stats-bot .
docker run -d --name gitlab-stats -p 8000:8000 -v ./scl:/app/scl gitlab-stats-bot
```

## Troubleshooting

### Bot doesn't respond to /start
- Make sure bot is running
- Check bot has permission to read messages
- Verify aiogram version is 3.x or higher

### Statistics show 0 repositories
- Verify GitLab token has correct permissions
- Check `target_username` matches your GitLab username
- Ensure you have personal repositories (not just organization repos)

### Message not updating
- Check `target_channel_id` is correct
- Verify bot is administrator in the channel
- If using `force_message_id`, ensure message exists

## Health Check

The bot exposes health check endpoints:
- `http://localhost:8000/` - Basic health check
- `http://localhost:8000/health` - Health status

Returns `200 OK` when bot is running.

## Commands

- `/start` - Display bot information and links

## Project Structure

```
gitstats/
├── main.py              # Entry point
├── src/
│   ├── config.py        # Configuration loader
│   ├── gitlab_service.py # GitLab API integration
│   ├── telegram_service.py # Telegram bot service
│   └── commands.py      # Bot commands
├── scl/
│   └── config.scl       # Configuration file
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## License

Open source project. Feel free to modify and use.

## Author

Created by [@shareui](https://gitlab.com/shareui)
