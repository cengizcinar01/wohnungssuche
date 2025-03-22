# Wohnungssuche - Apartment Search Application

A modern Python application to automate apartment search on Kleinanzeigen.de with automatic notifications.

## Features

- 🔍 **Automated Searching**: Periodically searches for apartment listings matching your criteria
- 🚫 **Smart Filtering**: Filters out unsuitable apartments based on predefined negative keywords
- 💾 **Database Storage**: Stores all found apartments in a PostgreSQL database
- 📱 **Telegram Notifications**: Sends notifications about suitable apartments via Telegram
- 🤖 **Telegram Bot**: Includes a Telegram bot for interaction and sending predefined inquiry texts

## Project Structure

The application is organized into the following modules:

- `app.py`: Main application entry point
- `config.py`: Configuration parameters
- `database.py`: Database connection and repository layer
- `notifier.py`: Notification services (Telegram)
- `scraper.py`: Web scraping functionality using Selenium
- `service.py`: Core business logic
- `utils.py`: Common utility functions
- `setup_database.py`: Database initialization script

## Setup

### Docker Setup (Recommended)

1. Make sure you have Docker and Docker Compose installed on your system.

2. Create a `.env` file in the project root with the following variables:

   ```
   POSTGRES_PASSWORD=your_secure_password
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   ```

3. Build and start the containers:
   ```bash
   docker compose up -d
   ```

The application will automatically:

- Set up the PostgreSQL database
- Run database migrations
- Start the apartment search process

To view logs:

```bash
docker compose logs -f app
```

### Coolify Deployment

1. In your Coolify dashboard, create a new service and select "Docker Compose".

2. Add the following environment variables in Coolify:

   - `POSTGRES_PASSWORD`: A secure password for the database
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `TELEGRAM_CHAT_ID`: Your Telegram chat ID

3. Use the repository URL and select the main branch.

4. Deploy the application. Coolify will automatically:
   - Build the Docker images
   - Set up the PostgreSQL database
   - Start the application

### Manual Setup (Alternative)

#### Prerequisites

- Python 3.8+
- PostgreSQL database
- Chrome browser (for Selenium)
- Telegram bot token (optional, for notifications)

### Installation

1. Clone the repository:

   ```
   git clone <repository-url>
   cd wohnungssuche
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with the following variables:

   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/wohnungssuche
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   ```

4. Set up the database:
   ```
   python setup_database.py
   ```

### Configuration

Adjust the search parameters in `config.py`:

- `SEARCH_CONFIG`: Modify rooms, size, price, and districts
- `NEGATIVE_KEYWORDS`: Add or remove negative keywords for filtering
- `CHECK_INTERVAL`: Change how often the application searches for new apartments
- `HEADLESS_MODE`: Set to `False` to see the browser window during scraping

## Usage

Run the application:

```
python app.py
```

The application will:

1. Start searching for apartments matching your criteria
2. Filter out unsuitable apartments based on negative keywords
3. Store results in the database
4. Send notifications about suitable apartments via Telegram

## Telegram Bot Commands

- `/text`: Sends a predefined inquiry text that you can use when contacting apartment listers

## Development

### Testing

Run tests using pytest:

```
pytest
```

### Code Style

The code follows modern Python conventions with type annotations. Format the code with:

```
black .
```

## License

[MIT License](LICENSE)
