import os
import json
import re
import requests
import sys
from datetime import datetime

# Meta Graph API base URL
GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

def load_json_file(filename, default_data):
    """Load JSON file or create if doesn't exist"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        with open(filename, 'w') as f:
            json.dump(default_data, f, indent=2)
        return default_data
    except json.JSONDecodeError:
        print(f"⚠️ Error reading {filename}, using default")
        return default_data

def save_json_file(filename, data):
    """Save data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def extract_shortcode_from_url(url):
    """Extract Instagram shortcode from /p/ or /reel/ URLs"""
    patterns = [
        r'instagram\.com/p/([A-Za-z0-9_-]+)',
        r'instagram\.com/reel/([A-Za-z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def add_rule(rules, shortcode, keyword, reply):
    """Add a new rule to rules.json"""
    if shortcode not in rules:
        rules[shortcode] = []
    
    # Check if rule already exists
    for rule in rules[shortcode]:
        if rule['keyword'].lower() == keyword.lower():
            print(f"⚠️ Rule already exists for {shortcode} with keyword '{keyword}'")
            return False
    
    rules[shortcode].append({
        'keyword': keyword,
        'reply': reply
    })
    print(f"✅ Added rule: {shortcode} | keyword='{keyword}' | reply='{reply}'")
    return True

def get_media_items(access_token, ig_user_id):
    """Fetch user's 50 most recent media items"""
    url = f"{GRAPH_API_BASE}/{ig_user_id}/media"
    params = {
        'access_token': access_token,
        'fields': 'id,shortcode,timestamp',
        'limit': 50
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'data' not in data:
            print(f"⚠️ No media data found in response: {data}")
            return []
        
        print(f"📸 Found {len(data['data'])} media items")
        return data['data']
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching media: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return []

def get_comments(access_token, media_id):
    """Fetch comments for a specific media item"""
    url = f"{GRAPH_API_BASE}/{media_id}/comments"
    params = {
        'access_token': access_token,
        'fields': 'id,text,timestamp,username',
        'limit': 50
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'data' not in data:
            return []
        
        return data['data']
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error fetching comments for media {media_id}: {e}")
        return []

def post_reply(access_token, comment_id, reply_text):
    """Post a public reply to a comment"""
    url = f"{GRAPH_API_BASE}/{comment_id}/replies"
    params = {
        'access_token': access_token,
        'message': reply_text
    }
    
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error posting reply: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return False

def process_media(access_token, media_item, rules, processed_comments):
    """Process a single media item for comments matching rules"""
    shortcode = media_item.get('shortcode')
    media_id = media_item.get('id')
    
    if shortcode not in rules:
        return
    
    print(f"\n📝 Processing post: https://instagram.com/p/{shortcode}")
    
    # Get all comments for this media
    comments = get_comments(access_token, media_id)
    if not comments:
        print(f"   No comments found")
        return
    
    # Check each rule for this shortcode
    for rule in rules[shortcode]:
        keyword = rule['keyword'].lower()
        reply_text = rule['reply']
        replied_count = 0
        
        for comment in comments:
            comment_id = comment.get('id')
            comment_text = comment.get('text', '').lower()
            username = comment.get('username', 'unknown')
            
            # Skip if already processed
            if comment_id in processed_comments:
                continue
            
            # Check if comment contains keyword
            if keyword in comment_text:
                print(f"   💬 Found match: @{username} - '{comment_text[:50]}...'")
                
                # Post reply
                if post_reply(access_token, comment_id, reply_text):
                    print(f"   ✅ Replied: '{reply_text}'")
                    processed_comments.append(comment_id)
                    replied_count += 1
                else:
                    print(f"   ❌ Failed to reply")
        
        if replied_count > 0:
            print(f"   📊 Replied to {replaced_count} comments for keyword '{keyword}'")

def main():
    print("🤖 Instagram Comment Auto-Reply Bot Starting...")
    print(f"🕐 Run time: {datetime.now().isoformat()}")
    
    # Read environment variables
    access_token = os.getenv('ACCESS_TOKEN')
    ig_user_id = os.getenv('IG_USER_ID')
    input_post_url = os.getenv('INPUT_POST_URL')
    input_keyword = os.getenv('INPUT_KEYWORD')
    input_reply = os.getenv('INPUT_REPLY')
    
    # Validate required credentials
    if not access_token or not ig_user_id:
        print("❌ Missing required environment variables: ACCESS_TOKEN and IG_USER_ID")
        sys.exit(1)
    
    print("✅ Credentials loaded")
    
    # Load JSON databases
    rules = load_json_file('rules.json', {})
    processed_comments = load_json_file('processed_comments.json', [])
    
    print(f"📋 Loaded {len(rules)} rules for {len(rules)} posts")
    print(f"💬 Loaded {len(processed_comments)} processed comments")
    
    # Handle adding new rule from workflow inputs
    if input_post_url and input_keyword and input_reply:
        print("\n➕ Adding new rule from workflow input...")
        shortcode = extract_shortcode_from_url(input_post_url)
        
        if not shortcode:
            print(f"❌ Invalid Instagram URL: {input_post_url}")
            sys.exit(1)
        
        print(f"📍 Extracted shortcode: {shortcode}")
        
        if add_rule(rules, shortcode, input_keyword, input_reply):
            save_json_file('rules.json', rules)
            print("💾 Rules saved to rules.json")
    
    # Only process comments if we have rules
    if rules:
        print("\n🔍 Checking for new comments...")
        
        # Get recent media items
        media_items = get_media_items(access_token, ig_user_id)
        
        if not media_items:
            print("⚠️ No media items found or failed to fetch")
        else:
            # Process each media item
            for media_item in media_items:
                process_media(access_token, media_item, rules, processed_comments)
            
            # Save updated processed comments
            save_json_file('processed_comments.json', processed_comments)
            print(f"\n💾 Saved {len(processed_comments)} total processed comments")
    else:
        print("\n📭 No rules configured. Add rules via GitHub Actions workflow_dispatch.")
    
    # Commit flag for GitHub Actions
    commit_needed = False
    if os.getenv('GITHUB_ACTIONS') == 'true':
        # Check if files were modified
        if os.path.exists('rules.json'):
            with open('rules.json', 'r') as f:
                current_rules = json.load(f)
                if current_rules != rules:
                    commit_needed = True
        
        if os.path.exists('processed_comments.json'):
            with open('processed_comments.json', 'r') as f:
                current_processed = json.load(f)
                if current_processed != processed_comments:
                    commit_needed = True
        
        # Set output for GitHub Actions
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"commit_needed={str(commit_needed).lower()}\n")
    
    print("\n✨ Bot execution completed successfully!")

if __name__ == "__main__":
    main()
