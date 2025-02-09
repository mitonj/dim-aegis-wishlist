# Destiny Wishlist Combiner

A tool to create DIM (Destiny Item Manager) wishlists from Google Sheets data by matching weapons and perks with Bungie API.


## Local Setup and Usage

### Prerequisites
1. Python 3.10 or higher
2. pip (Python package installer)
3. API Keys:
   - Bungie API Key (register at https://www.bungie.net/en/Application)
   - Google Sheets API Key (get from Google Cloud Console)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/mitonj/dim-wishlist-builder.git
cd dim-wishlist-builder
```

2. Create and activate virtual environment:
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure API keys:
```bash
# Copy example config
cp config/config.example.env .env

# Edit .env file with your API keys
# Use your favorite text editor (nano, vim, etc.)
nano .env
```

Add your API keys to the .env file:
```env
BUNGIE_API_KEY=your_bungie_api_key_here
GOOGLE_SHEETS_API_KEY=your_google_sheets_api_key_here
```

### Running the Script

1. Run the main script:
```bash
python src/main.py
```

2. Follow the interactive prompts:
```
Select tiers to include in wishlist:
1. S tier only
2. S and A tiers
3. S, A, and B tiers
4. All tiers
Enter your choice (1-4):

For each selected tier, choose perk configuration:
1. Only combinations with perks in both columns
2. Combinations with at least one perk
3. Include weapon even without perks
```

3. The script will:
   - Process all weapons from the spreadsheet
   - Match weapons and perks with Bungie API
   - Generate wishlist based on your configuration
   - Save the result to `dim_wishlist.txt`

### Output Format

The generated `dim_wishlist.txt` will contain entries in this format:
```
Weapon Name - Tier: S
dimwishlist:item=123456                         # Base weapon (if option 3)
dimwishlist:item=123456&perks=789              # Single perk (if option 2 or 3)
dimwishlist:item=123456&perks=789,012          # Perk combination (all options)
```

### Getting API Keys

1. Bungie API Key:
   - Go to https://www.bungie.net/en/Application
   - Sign in with your Bungie account
   - Click "Create New App"
   - Fill in the form:
     - App Name: "DIM Wishlist Builder"
     - Website: (can be blank)
     - OAuth Client Type: "Confidential"
   - Copy the API Key

2. Google Sheets API Key:
   - Go to https://console.cloud.google.com/
   - Create a new project
   - Enable Google Sheets API
   - Go to Credentials
   - Create an API key
   - Copy the API Key

### Troubleshooting

1. API Key Issues:
```
Error: BUNGIE_API_KEY not found in environment variables
```
- Make sure you've created the `.env` file
- Check that your API keys are correctly formatted
- No quotes needed around the keys in `.env`

2. Cache Issues:
```
# If you get cache-related errors, delete the cache:
rm bungie_cache.json
```

3. Python Version:
```bash
# Check your Python version
python --version  # Should be 3.10 or higher
```

4. Virtual Environment:
```bash
# Make sure you're in the virtual environment
# Your prompt should show (venv)
# If not, activate it:
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\activate   # Windows
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
