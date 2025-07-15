# Telegram Bot File Download Link Generator

A Python Flask webhook server that receives files from a Telegram bot and generates direct download links for them.

## Features

- ✅ Receive files and photos from Telegram users
- ✅ Generate secure, time-limited download links (24 hours)
- ✅ Support for documents, photos, and various file types
- ✅ File size validation (50MB limit)
- ✅ Automatic cleanup of expired links
- ✅ Health check endpoint
- ✅ Comprehensive logging

## Setup Instructions

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Save the bot token you receive

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required
export TELEGRAM_BOT_TOKEN="your_bot_token_here"

# Optional (defaults shown)
export WEBHOOK_URL="https://your-domain.com/webhook"
export DOWNLOAD_BASE_URL="https://your-domain.com/download"
export PORT=5000
export FLASK_DEBUG=False
```

### 4. Deploy the Server

#### Option A: Local Development
```bash
python bot_server.py
```

#### Option B: Using ngrok for Testing
1. Install ngrok: https://ngrok.com/
2. Run the server: `python bot_server.py`
3. In another terminal: `ngrok http 5000`
4. Use the ngrok URL as your webhook URL

#### Option C: Production Deployment
Deploy to your preferred hosting service (Heroku, DigitalOcean, AWS, etc.)

### 5. Set Webhook URL

The server automatically sets the webhook when started, but you can also set it manually:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-domain.com/webhook"}'
```

## Usage

1. Start a conversation with your bot on Telegram
2. Send `/start` to get a welcome message
3. Send any file or photo to the bot
4. The bot will respond with a direct download link
5. The link expires after 24 hours

## API Endpoints

### Webhook Endpoint
- **URL**: `/webhook`
- **Method**: `POST`
- **Description**: Receives webhook notifications from Telegram

### Download Endpoint
- **URL**: `/download/<download_id>`
- **Method**: `GET`
- **Description**: Serves file downloads

### Health Check
- **URL**: `/health`
- **Method**: `GET`
- **Description**: Returns server health status

## File Structure

```
├── bot_server.py      # Main server file
├── requirements.txt   # Python dependencies
├── README.md         # This file
└── uploads/          # Directory for stored files (created automatically)
```

## Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Required | Your Telegram bot token |
| `WEBHOOK_URL` | `https://your-domain.com/webhook` | Webhook URL for Telegram |
| `DOWNLOAD_BASE_URL` | `https://your-domain.com/download` | Base URL for download links |
| `PORT` | `5000` | Server port |
| `FLASK_DEBUG` | `False` | Enable Flask debug mode |
| `MAX_FILE_SIZE` | `50MB` | Maximum file size limit |

## Security Considerations

- Download links expire after 24 hours
- Files are stored locally (consider cloud storage for production)
- File names are sanitized using `secure_filename`
- File size limits prevent abuse
- Consider implementing rate limiting for production use

## Production Recommendations

1. **Database Storage**: Replace the in-memory `file_mappings` with a proper database
2. **Cloud Storage**: Use services like AWS S3 or Google Cloud Storage for file storage
3. **HTTPS**: Always use HTTPS in production
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Monitoring**: Add proper monitoring and alerting
6. **Backup**: Implement regular backups of your data

## Troubleshooting

### Common Issues

1. **Webhook not receiving updates**
   - Check if your server is accessible from the internet
   - Verify the webhook URL is correct
   - Check server logs for errors

2. **File downloads failing**
   - Ensure the `uploads` directory exists and is writable
   - Check available disk space
   - Verify file permissions

3. **Bot not responding**
   - Verify the bot token is correct
   - Check if the webhook is properly set
   - Review server logs for errors

### Debug Mode

Enable debug mode for detailed logging:

```bash
export FLASK_DEBUG=True
python bot_server.py
```

## License

This project is open source and available under the MIT License. 