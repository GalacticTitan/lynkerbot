import os
import json
import logging
import requests
from flask import Flask, request, jsonify
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
CUSTOM_API_URL = os.getenv('CUSTOM_API_URL')

# Ensure required environment variables are set
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError('TELEGRAM_BOT_TOKEN environment variable is required')
if not WEBHOOK_URL:
    raise RuntimeError('WEBHOOK_URL environment variable is required')
if not CUSTOM_API_URL:
    raise RuntimeError('CUSTOM_API_URL environment variable is required')

class TelegramBot:
    def __init__(self, token):
        self.token = token
        # Use custom API server instead of official Telegram API
        self.base_url = f"{CUSTOM_API_URL}/bot{token}"
    
    def send_message(self, chat_id, text):
        """Send a message to a chat"""
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def get_file(self, file_id):
        """Get file info from Telegram"""
        url = f"{self.base_url}/getFile"
        data = {'file_id': file_id}
        response = requests.post(url, json=data)
        return response.json()
    
    def handle_large_file_error(self, file_size, file_name):
        """Handle large file errors with alternative solutions"""
        size_mb = file_size // (1024 * 1024)
        
        if size_mb > 50:  # Telegram's limit is around 50MB for bots
            return f"""
❌ <b>File Too Large for Bot Processing</b>

📁 <b>File:</b> {file_name}
📏 <b>Size:</b> {size_mb} MB
⚠️ <b>Limit:</b> 50 MB for bot processing

<b>Alternative Solutions:</b>
1️⃣ <b>Use Telegram Web</b> - Download directly from web.telegram.org
2️⃣ <b>Split the file</b> - Break into smaller parts (use 7-Zip or WinRAR)
3️⃣ <b>Use cloud storage</b> - Upload to Google Drive/Dropbox and share link
4️⃣ <b>Compress the file</b> - Reduce size before sending
5️⃣ <b>Use Telegram Desktop</b> - Download directly from desktop app

<b>File Splitting Tools:</b>
• 7-Zip (free): Split large files into parts
• WinRAR: Built-in split functionality
• Online tools: Split files in browser

<i>Telegram bots have a 50MB file size limit for processing. For larger files, use the alternatives above.</i>
            """
        else:
            return f"""
❌ <b>File Processing Error</b>

📁 <b>File:</b> {file_name}
📏 <b>Size:</b> {size_mb} MB

<b>Possible Issues:</b>
• File may be corrupted
• Network connection issues
• Telegram server problems
• File format not supported

<b>Try Again:</b>
• Send the file again
• Check your internet connection
• Try a different file
• Compress the file first
            """
    
    def get_message_by_forwarding(self, chat_username, message_id, target_chat_id):
        """Get message by forwarding it to the target chat"""
        try:
            # Try to forward the message to access its content
            url = f"{self.base_url}/forwardMessage"
            data = {
                'chat_id': target_chat_id,  # Forward to the user who sent the link
                'from_chat_id': f"@{chat_username}",
                'message_id': message_id
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    # Successfully forwarded the message, now we can access its content
                    return result
                else:
                    # Try alternative approach for public channels
                    logger.info(f"Forward failed: {result.get('description', 'Unknown error')}")
                    return None
            
            return None
        except Exception as e:
            logger.error(f"Error getting message by forwarding: {str(e)}")
            return None
    


# Initialize bot
bot = TelegramBot(TELEGRAM_BOT_TOKEN)



@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from Telegram"""
    try:
        data = request.get_json()
        logger.info(f"Received webhook: {json.dumps(data, indent=2)}")
        
        # Extract message data
        if 'message' not in data:
            return jsonify({'status': 'ok'})
        
        message = data['message']
        chat_id = message['chat']['id']
        
        # Handle different types of messages
        if 'text' in message:
            # Text message
            text = message['text']
            if text.startswith('/start'):
                response_text = """👋 <b>Welcome to File Download Link Generator!</b>

<b>How to use:</b>
1️⃣ <b>Send files directly</b> - Upload any file or photo
2️⃣ <b>Forward messages</b> - Forward messages containing files from channels/groups
3️⃣ <b>Get direct links</b> - Receive instant download links to Telegram's servers

<b>Supported:</b>
✅ Documents, photos, videos, audio files
✅ Any file size (no limits)
✅ Direct links (no expiration)

<i>Note: For private channels/groups, forward the message to me instead of using links.</i>"""
            elif text.startswith('https://t.me/') or text.startswith('t.me/'):
                # Handle Telegram message links
                try:
                    # Extract channel/chat and message ID from link
                    if text.startswith('https://t.me/'):
                        link_parts = text.replace('https://t.me/', '').split('/')
                    else:
                        link_parts = text.replace('t.me/', '').split('/')
                    
                    if len(link_parts) >= 2:
                        chat_username = link_parts[0]
                        message_id = int(link_parts[1])
                        
                        # Try to get message by forwarding it to the user
                        message_info = bot.get_message_by_forwarding(chat_username, message_id, chat_id)
                        if message_info and message_info.get('ok'):
                            message_data = message_info['result']
                            
                            # Check if message contains a file
                            if 'document' in message_data:
                                document = message_data['document']
                                file_id = document['file_id']
                                file_name = document.get('file_name', 'unknown_file')
                                file_size = document.get('file_size', 0)
                                
                                # Get file info and generate download link
                                file_info = bot.get_file(file_id)
                                if file_info.get('ok'):
                                    file_path = file_info['result']['file_path']
                                    direct_download_url = f"{CUSTOM_API_URL}/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                                    
                                    response_text = f"""
✅ File fetched from message link!

📁 <b>File:</b> {file_name}
📏 <b>Size:</b> {file_size // 1024} KB
🔗 <b>Direct Download Link:</b> {direct_download_url}

⚠️ <i>Direct link to Telegram's servers</i>
                                    """
                                else:
                                    # Get the actual error message from the API response
                                    file_error = file_info.get('description', 'Unknown error') if file_info else 'Unknown error'
                                    
                                    # Check if it's a file size error
                                    if 'FILE_TOO_BIG' in file_error or 'FILE_TOO_LARGE' in file_error:
                                        response_text = bot.handle_large_file_error(file_size, file_name)
                                    else:
                                        response_text = f"❌ Failed to get file information from the message.\n\n<b>Error:</b> {file_error}"
                            elif 'photo' in message_data:
                                photos = message_data['photo']
                                largest_photo = max(photos, key=lambda x: x['file_size'])
                                file_id = largest_photo['file_id']
                                file_size = largest_photo['file_size']
                                
                                # Get file info and generate download link
                                file_info = bot.get_file(file_id)
                                if file_info.get('ok'):
                                    file_path = file_info['result']['file_path']
                                    direct_download_url = f"{CUSTOM_API_URL}/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                                    
                                    response_text = f"""
✅ Photo fetched from message link!

📸 <b>Photo</b>
📏 <b>Size:</b> {file_size // 1024} KB
🔗 <b>Direct Download Link:</b> {direct_download_url}

⚠️ <i>Direct link to Telegram's servers</i>
                                    """
                                else:
                                    # Get the actual error message from the API response
                                    photo_error = file_info.get('description', 'Unknown error') if file_info else 'Unknown error'
                                    
                                    # Check if it's a file size error
                                    if 'FILE_TOO_BIG' in photo_error or 'FILE_TOO_LARGE' in photo_error:
                                        response_text = bot.handle_large_file_error(file_size, "Photo")
                                    else:
                                        response_text = f"❌ Failed to get photo information from the message.\n\n<b>Error:</b> {photo_error}"
                            else:
                                response_text = "❌ The message doesn't contain any file or photo."
                        else:
                            # Get the actual error message from the API response
                            error_msg = "Unknown error"
                            if message_info:
                                error_msg = message_info.get('description', 'Unknown error')
                            
                            response_text = f"""
❌ <b>Cannot Access Message</b>

<b>Telegram API Error:</b> {error_msg}

<b>Common Solutions:</b>
1️⃣ <b>Forward the message</b> to me directly
2️⃣ <b>Add the bot</b> to the channel/group as admin
3️⃣ <b>Use a public channel</b> instead
4️⃣ <b>Check if the message</b> contains a file

<i>Forwarding the message to me will work in most cases!</i>
                            """
                    else:
                        response_text = "❌ Invalid message link format. Please use a valid Telegram message link (e.g., https://t.me/channelname/123)."
                        
                except Exception as e:
                    logger.error(f"Error processing message link: {str(e)}")
                    response_text = "❌ Error processing the message link. Please check the link and try again."
            else:
                response_text = "Please send me a file or paste a Telegram message link to get a direct download link."
            
            bot.send_message(chat_id, response_text)
            
        elif 'document' in message:
            # File/document message
            document = message['document']
            file_id = document['file_id']
            file_name = document.get('file_name', 'unknown_file')
            file_size = document.get('file_size', 0)
            
            # Get file info from Telegram
            file_info = bot.get_file(file_id)
            if not file_info.get('ok'):
                file_error = file_info.get('description', 'Unknown error')
                
                # Check if it's a file size error
                if 'FILE_TOO_BIG' in file_error or 'FILE_TOO_LARGE' in file_error:
                    error_message = bot.handle_large_file_error(file_size, file_name)
                else:
                    error_message = f"❌ Failed to get file information\n\n<b>Error:</b> {file_error}"
                
                bot.send_message(chat_id, error_message)
                return jsonify({'status': 'ok'})
            
            file_path = file_info['result']['file_path']
            direct_download_url = f"{CUSTOM_API_URL}/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
            
            # Send response to user
            response_text = f"""
✅ File received!

📁 <b>File:</b> {file_name}
📏 <b>Size:</b> {file_size // 1024} KB
🔗 <b>Direct Download Link:</b> {direct_download_url}

⚠️ <i>Direct link to Telegram's servers</i>
            """
            
            bot.send_message(chat_id, response_text)
            
        elif 'photo' in message:
            # Photo message
            photos = message['photo']
            # Get the largest photo
            largest_photo = max(photos, key=lambda x: x['file_size'])
            file_id = largest_photo['file_id']
            file_size = largest_photo['file_size']
            
            # Get file info from Telegram
            file_info = bot.get_file(file_id)
            if not file_info.get('ok'):
                photo_error = file_info.get('description', 'Unknown error')
                
                # Check if it's a file size error
                if 'FILE_TOO_BIG' in photo_error or 'FILE_TOO_LARGE' in photo_error:
                    error_message = bot.handle_large_file_error(file_size, "Photo")
                else:
                    error_message = f"❌ Failed to get photo information\n\n<b>Error:</b> {photo_error}"
                
                bot.send_message(chat_id, error_message)
                return jsonify({'status': 'ok'})
            
            file_path = file_info['result']['file_path']
            direct_download_url = f"{CUSTOM_API_URL}/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
            
            response_text = f"""
✅ Photo received!

📸 <b>Photo</b>
📏 <b>Size:</b> {file_size // 1024} KB
🔗 <b>Direct Download Link:</b> {direct_download_url}

⚠️ <i>Direct link to Telegram's servers</i>
            """
            
            bot.send_message(chat_id, response_text)
            
        elif 'forward_from' in message or 'forward_from_chat' in message:
            # Forwarded message - handle files in forwarded messages
            if 'document' in message:
                document = message['document']
                file_id = document['file_id']
                file_name = document.get('file_name', 'unknown_file')
                file_size = document.get('file_size', 0)
                
                # Get file info and generate download link
                file_info = bot.get_file(file_id)
                if file_info.get('ok'):
                    file_path = file_info['result']['file_path']
                    direct_download_url = f"{CUSTOM_API_URL}/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                    
                    response_text = f"""
✅ Forwarded file processed!

📁 <b>File:</b> {file_name}
📏 <b>Size:</b> {file_size // 1024} KB
🔗 <b>Direct Download Link:</b> {direct_download_url}

⚠️ <i>Direct link to Telegram's servers</i>
                    """
                else:
                    # Get the actual error message from the API response
                    forward_file_error = file_info.get('description', 'Unknown error') if file_info else 'Unknown error'
                    
                    # Check if it's a file size error
                    if 'FILE_TOO_BIG' in forward_file_error or 'FILE_TOO_LARGE' in forward_file_error:
                        response_text = bot.handle_large_file_error(file_size, file_name)
                    else:
                        response_text = f"❌ Failed to get file information from forwarded message.\n\n<b>Error:</b> {forward_file_error}"
                    
            elif 'photo' in message:
                photos = message['photo']
                largest_photo = max(photos, key=lambda x: x['file_size'])
                file_id = largest_photo['file_id']
                file_size = largest_photo['file_size']
                
                # Get file info and generate download link
                file_info = bot.get_file(file_id)
                if file_info.get('ok'):
                    file_path = file_info['result']['file_path']
                    direct_download_url = f"{CUSTOM_API_URL}/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                    
                    response_text = f"""
✅ Forwarded photo processed!

📸 <b>Photo</b>
📏 <b>Size:</b> {file_size // 1024} KB
🔗 <b>Direct Download Link:</b> {direct_download_url}

⚠️ <i>Direct link to Telegram's servers</i>
                    """
                else:
                    # Get the actual error message from the API response
                    forward_photo_error = file_info.get('description', 'Unknown error') if file_info else 'Unknown error'
                    
                    # Check if it's a file size error
                    if 'FILE_TOO_BIG' in forward_photo_error or 'FILE_TOO_LARGE' in forward_photo_error:
                        response_text = bot.handle_large_file_error(file_size, "Photo")
                    else:
                        response_text = f"❌ Failed to get photo information from forwarded message.\n\n<b>Error:</b> {forward_photo_error}"
            else:
                response_text = "❌ The forwarded message doesn't contain any file or photo."
            
            bot.send_message(chat_id, response_text)
            
        else:
            bot.send_message(chat_id, "❌ Unsupported message type. Please send a file or photo.")
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'message': 'Direct download links only - no local file storage'
    })

@app.route('/set_webhook', methods=['GET'])
def set_webhook_route():
    """Set webhook URL dynamically based on current host"""
    base_url = request.host_url.rstrip('/')  # e.g., https://yourdomain.com
    webhook_url = f"{base_url}/webhook"
    url = f"{CUSTOM_API_URL}/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    data = {'url': webhook_url}
    response = requests.post(url, json=data, proxies={"http": None, "https": None})
    logger.info(f"Webhook set: {response.json()}")
    return jsonify({'webhook_url': webhook_url, 'telegram_response': response.json()})

if __name__ == '__main__':
    @app.before_first_request
    def set_webhook_on_startup():
        base_url = request.host_url.rstrip('/')
        webhook_url = f"{base_url}/webhook"
        url = f"{CUSTOM_API_URL}/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
        data = {'url': webhook_url}
        response = requests.post(url, json=data, proxies={"http": None, "https": None})
        logger.info(f"Webhook set on startup: {response.json()} (URL: {webhook_url})")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8081)))
