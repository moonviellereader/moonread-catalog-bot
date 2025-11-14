#!/usr/bin/env python3
"""
Moon Read Catalog Bot
Bot: @MoonCatalogBot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import csv
import logging
from telegraph import Telegraph
import threading
from flask import Flask

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration - MoonCatalogBot
BOT_TOKEN = '8278022191:AAHK_mm_cVMwF5Hz-vDoKzOpzlRS8mPOXec'

# Initialize Telegraph
telegraph = Telegraph()
telegraph.create_account(short_name='MoonRead', author_name='Moon Read Catalog')

# Initialize Flask for health check (required by Choreo)
app = Flask(__name__)

@app.route('/')
def health_check():
    return {'status': 'Bot is running', 'books': len(BOOKS)}, 200

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

# Load catalog data
BOOKS = []
TELEGRAPH_LINKS = {}  # Cache for Telegraph links

def load_catalog():
    """Load books from CSV file"""
    global BOOKS
    try:
        with open('titles_and_links_alphabetical.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            BOOKS = list(reader)
        logger.info(f"✅ Loaded {len(BOOKS)} books from catalog")
    except Exception as e:
        logger.error(f"❌ Error loading catalog: {e}")
        BOOKS = []


def generate_telegraph_pages():
    """Generate Telegraph pages for catalog (called once at startup)"""
    global TELEGRAPH_LINKS
    import time
    
    logger.info("📝 Generating Telegraph pages...")
    
    try:
        # Group books by first letter
        books_by_letter = {}
        for book in BOOKS:
            first_letter = book['title'][0].upper()
            if not first_letter.isalpha():
                first_letter = '#'  # For numbers and special characters
            
            if first_letter not in books_by_letter:
                books_by_letter[first_letter] = []
            books_by_letter[first_letter].append(book)
        
        # Sort letters
        sorted_letters = sorted([l for l in books_by_letter.keys() if l != '#']) + (['#'] if '#' in books_by_letter else [])
        
        # Create Telegraph pages for each letter with delay to avoid flood control
        for i, letter in enumerate(sorted_letters):
            books = books_by_letter[letter]
            
            # Create HTML content for this letter
            html_content = f'<h3>📚 Moon Read Catalog - Letter {letter}</h3>'
            html_content += f'<p><strong>Books starting with "{letter}": {len(books)}</strong></p>'
            html_content += '<hr>'
            
            for idx, book in enumerate(books, 1):
                html_content += f'<p>{idx}. <a href="{book["link"]}">{book["title"]}</a></p>'
            
            # Create Telegraph page for this letter
            title = f'Moon Read Catalog - {letter}' if letter != '#' else 'Moon Read Catalog - Numbers & Special'
            
            try:
                response = telegraph.create_page(
                    title=title,
                    html_content=html_content,
                    author_name='Moon Read',
                    author_url='https://t.me/moon_read'
                )
                
                TELEGRAPH_LINKS[letter] = {
                    'url': f"https://telegra.ph/{response['path']}",
                    'count': len(books)
                }
                
                logger.info(f"✅ Created Telegraph page for letter {letter} ({len(books)} books)")
                
                # Add delay between requests to avoid flood control (10 seconds)
                if i < len(sorted_letters) - 1:  # Don't delay after last one
                    time.sleep(10)
                    
            except Exception as e:
                logger.error(f"❌ Error creating page for {letter}: {e}")
                # Continue with other letters even if one fails
        
        logger.info(f"✅ Generated {len(TELEGRAPH_LINKS)} Telegraph pages successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error generating Telegraph pages: {e}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    welcome_text = """
🌙 **Welcome to Moon Read Catalog Bot!** 📚

I can help you find novels from our collection of **997+ EPUBs**!

**How to use:**

🔍 **Search for a book:**
`/search tempest`
Example: `/search villainess`

📋 **Browse full catalog:**
`KATALOG` or `/katalog` - Get a Telegraph link with ALL 997 books!

📖 **Random book:**
`/random`

ℹ️ **Help:**
`/help`

Start searching now! 🚀
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = """
📚 **Moon Read Catalog Bot - Help**

**Available Commands:**

🔍 **Search:**
• `/search keyword` - Search for books
• Example: `/search romance`
• Example: `/search villainess tempest`

📋 **Catalog:**
• `KATALOG` or `/katalog` - Get Telegraph link with ALL 997 books
• Complete catalog organized alphabetically
• No spam in the chat!

📖 **Random:**
• `/random` - Get a random book recommendation

**Search Tips:**
• Search is case-insensitive
• Use multiple keywords: `/search fantasy romance`
• Partial matches work (e.g., "temp" finds "Tempest")

**Need help?** Contact channel admin!
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for books using /search command"""
    
    # Get search keyword from command arguments
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a search keyword!\n\n"
            "**Example:**\n"
            "`/search tempest`\n"
            "`/search villainess romance`",
            parse_mode='Markdown'
        )
        return
    
    # Join all arguments as keyword
    keyword = ' '.join(context.args).lower()
    
    # Search for matches
    results = [book for book in BOOKS if keyword in book['title'].lower()]
    
    if not results:
        await update.message.reply_text(
            f"📭 No books found for: **{keyword}**\n\n"
            "Try different keywords!",
            parse_mode='Markdown'
        )
        return
    
    # Limit to first 20 results
    limited_results = results[:20]
    
    message = f"🔍 **Search Results for: {keyword}**\n\n"
    message += f"Found **{len(results)}** book(s)\n"
    if len(results) > 20:
        message += f"_(Showing first 20 results)_\n"
    message += "\n"
    
    for i, book in enumerate(limited_results, 1):
        message += f"{i}. [{book['title']}]({book['link']})\n\n"
    
    if len(results) > 20:
        message += f"_...and {len(results) - 20} more results_\n"
        message += f"\n💡 Tip: Use more specific keywords to narrow results"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def random_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random book"""
    if not BOOKS:
        await update.message.reply_text("❌ Catalog not loaded. Please try again later.")
        return
    
    import random
    book = random.choice(BOOKS)
    
    message = f"""
📖 **Random Book Recommendation**

[{book['title']}]({book['link']})

Want another? Type `/random` again!
"""
    await update.message.reply_text(message, parse_mode='Markdown')


async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Telegraph catalog links (using pre-generated links)"""
    
    # Check if Telegraph links are ready
    if not TELEGRAPH_LINKS:
        await update.message.reply_text(
            "⏳ Catalog is being prepared... Please try again in a moment.\n\n"
            "You can use `/search keyword` to find books in the meantime!"
        )
        return
    
    # Create message with all Telegraph links organized
    message = f"📚 **Moon Read Full Catalog**\n\n"
    message += f"Total Books: **{len(BOOKS)}**\n\n"
    message += "🔤 **Browse by Letter:**\n\n"
    
    # Get sorted letters
    sorted_letters = sorted([l for l in TELEGRAPH_LINKS.keys() if l != '#']) + (['#'] if '#' in TELEGRAPH_LINKS else [])
    
    # Group letters in rows for cleaner display
    row = []
    for letter in sorted_letters:
        data = TELEGRAPH_LINKS[letter]
        row.append(f"[{letter}]({data['url']}) ({data['count']})")
        
        if len(row) == 5 or letter == sorted_letters[-1]:  # 5 letters per row
            message += " • ".join(row) + "\n"
            row = []
    
    message += f"\n💡 **Tips:**\n"
    message += f"• Click any letter to see all books starting with that letter\n"
    message += f"• Use `/search keyword` to find specific books\n"
    message += f"• Try `/random` for a random recommendation"
    
    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages"""
    text = update.message.text
    
    # Handle KATALOG keyword
    if text.lower() == 'katalog':
        await show_catalog(update, context)


def main():
    """Start the bot"""
    print("=" * 70)
    print("🤖 MOON READ CATALOG BOT - @MoonCatalogBot")
    print("=" * 70)
    print("🚀 Ready to serve!")
    print("=" * 70)
    
    # Load catalog
    print("📚 Loading catalog...")
    load_catalog()
    
    if not BOOKS:
        print("❌ Failed to load catalog! Make sure titles_and_links_alphabetical.csv is in the same folder.")
        input("Press Enter to exit...")
        return
    
    print(f"✅ Loaded {len(BOOKS)} books")
    
    # Generate Telegraph pages
    print("\n📝 Generating Telegraph catalog pages...")
    print("⏳ This will take about 4-5 minutes (10 sec delay between pages to avoid flood control)")
    print("💡 The bot will start accepting commands after generation is complete\n")
    
    if not generate_telegraph_pages():
        print("⚠️  Warning: Failed to generate some Telegraph pages")
        print("Bot will still work, but /katalog might have issues")
    
    print(f"✅ Telegraph pages ready!")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("random", random_book))
    application.add_handler(CommandHandler("katalog", show_catalog))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Start bot
    print("\n" + "=" * 70)
    print("✅ Bot started successfully!")
    print("=" * 70)
    print("🔍 Users can search: /search keyword")
    print("📋 Users can browse: KATALOG or /katalog (Telegraph link)")
    print("📖 Users can get random: /random")
    print("=" * 70)
    print("\nBot is running! Press Ctrl+C to stop.\n")
    
    # Run bot in separate thread
    def run_bot():
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Run Flask server (Choreo requires this)
    print("🌐 Starting web server for Choreo health checks...")
    app.run(host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
