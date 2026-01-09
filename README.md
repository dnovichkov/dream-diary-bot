# Dream Diary Bot

A Telegram bot for keeping a personal dream journal. Record your dreams, add tags and notes, and search through them later.

## Features

- Personal dream diary with data isolation between users
- Create, view, edit, and delete dream entries
- Search dreams by keywords (title, description, tags, notes)
- Pagination for dream lists
- Multi-step dialogs for creating and editing entries

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Register and get started |
| `/new` | Create a new dream entry |
| `/list` | View your dreams (paginated) |
| `/search <query>` | Search dreams by keywords |
| `/view <id>` | View a specific dream |
| `/edit <id>` | Edit a dream entry |
| `/delete <id>` | Delete a dream entry |
| `/cancel` | Cancel current operation |
| `/help` | Show help message |

## Dream Entry Structure

- **Title** - Brief name for the dream (required)
- **Description** - Detailed dream narrative
- **Tags** - Comma-separated keywords for categorization
- **Notes** - Personal comments or interpretations
- **Date** - When the dream occurred (defaults to today)

## Setup

### Prerequisites

- Docker and Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your values:
   ```
   BOT_TOKEN=your_bot_token_here
   POSTGRES_PASSWORD=your_secure_password
   ```

### Running

Start the bot with Docker Compose:

```bash
docker-compose up -d
```

View logs:

```bash
docker-compose logs -f bot
```

Stop the bot:

```bash
docker-compose down
```

## Project Structure

```
dream-diary-bot/
├── docker-compose.yml    # Docker services configuration
├── Dockerfile            # Bot container image
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── README.md             # This file
└── src/
    ├── __init__.py
    ├── main.py           # Application entry point
    ├── config.py         # Settings management
    ├── database.py       # Database connection
    ├── models.py         # SQLAlchemy models
    └── handlers/
        ├── __init__.py   # Router setup
        ├── start.py      # /start, /help, /cancel
        ├── dreams.py     # /new, /list, /view, /edit, /delete
        └── search.py     # /search
```

## Tech Stack

- Python 3.11+
- aiogram 3.x (Telegram Bot API)
- SQLAlchemy 2.x (ORM)
- PostgreSQL (Database)
- Docker + Docker Compose (Deployment)

## Production Deployment

Docker images are automatically built and published to GitHub Container Registry on every push to `main`.

### Deploy to your server

1. Copy files to your server:
   ```bash
   scp docker-compose.prod.yml .env.example user@your-server:~/dream-diary-bot/
   ```

2. On the server, configure environment:
   ```bash
   cd ~/dream-diary-bot
   cp .env.example .env
   nano .env  # Set BOT_TOKEN and POSTGRES_PASSWORD
   ```

3. Update the image name in `docker-compose.prod.yml`:
   ```yaml
   image: ghcr.io/YOUR_GITHUB_USERNAME/dream-diary-bot:main
   ```

4. Start the bot:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Update to latest version

```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Development

Run locally without Docker (requires PostgreSQL):

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export BOT_TOKEN=your_token
export POSTGRES_HOST=localhost
export POSTGRES_PASSWORD=your_password

# Run the bot
python -m src.main
```

## License

MIT
