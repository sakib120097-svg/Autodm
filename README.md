# Instagram Comment Auto-Reply Bot

This bot automatically monitors Instagram posts and replies to comments containing specific keywords.

## Setup Instructions

### 1. Get Instagram Access Token

1. Go to the [Meta for Developers](https://developers.facebook.com/) site
2. Create a Facebook App (Business type)
3. Add Instagram Basic Display product
4. Generate a long-lived Instagram Access Token with these permissions:
   - `instagram_basic`
   - `instagram_manage_comments`
   - `pages_read_engagement`
   - `pages_manage_metadata`
   - `pages_manage_engagement`

### 2. Get Instagram Business Account ID

1. Make a GET request to:
