#!/bin/bash

echo "🚀 Creating public deployment repository..."

# Create a new directory for public deployment repo
mkdir -p /tmp/telegram-bot-deploy
cd /tmp/telegram-bot-deploy

# Initialize new git repo
git init
git branch -m main

# Copy only deployment files
cp -r "/Users/victorivros/Documents/Analyte/Python/Telegram/simple-direct/"* .

# Remove sensitive files (keep .env.example instead of .env)
rm -f .env
cp .env.example .env

echo "# MT5 Telegram Trading Bot - Hostinger Deployment

## 🚀 Quick Deploy to Hostinger VPS

### Deployment URL for Hostinger Dashboard:
\`\`\`
https://github.com/Denivros/telegram-bot-deploy
\`\`\`

### Setup Instructions:
1. Clone this repository
2. Copy \`.env.example\` to \`.env\`
3. Fill in your credentials in \`.env\`
4. Deploy via Hostinger Docker Compose from URL

### Configuration Required:
- Telegram API credentials
- MT5 VPS connection details
- N8N webhook URL

See \`HOSTINGER_DEPLOY.md\` for detailed instructions.
" > README.md

# Add all files
git add .
git commit -m "Initial deployment setup for Hostinger"

echo "✅ Repository prepared!"
echo "📝 Next steps:"
echo "1. Create new GitHub repository: https://github.com/new"
echo "2. Name it: telegram-bot-deploy"
echo "3. Make it PUBLIC"
echo "4. Run these commands:"
echo ""
echo "   git remote add origin https://github.com/Denivros/telegram-bot-deploy.git"
echo "   git push -u origin main"
echo ""
echo "5. Use this URL in Hostinger: https://github.com/Denivros/telegram-bot-deploy"