# How to Switch to Your Crypto YouTube Channel

This guide explains how to authenticate the automation with your **crypto channel** instead of the previous channel.

## Why You Need to Do This

YouTube OAuth tokens are tied to specific channels. To upload to your crypto channel, you need to:
1. Generate new credentials while logged into your Google account
2. **Select the crypto channel** during the OAuth flow
3. Update GitHub Secrets with the new refresh token

## Step-by-Step Instructions

### 1. Run the Token Generator Locally

Open a terminal in this project directory and run:

```bash
python get_youtube_token.py
```

### 2. Follow the OAuth Flow

1. A browser window will open asking you to log in to Google
2. **Log in with the Google account that owns your crypto channel**
3. **IMPORTANT**: When prompted to select a channel, choose your **crypto channel**
4. Grant the necessary permissions
5. The script will display your new credentials

### 3. Copy the Credentials

The script will output three values:
- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

**Copy these values** - you'll need them in the next step.

### 4. Update GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Update these three secrets with the new values:
   - `YT_CLIENT_ID`
   - `YT_CLIENT_SECRET`
   - `YT_REFRESH_TOKEN`

### 5. Verify the Channel

Run this command to verify you're connected to the correct channel:

```bash
python verify_channel.py
```

This will display the channel name and ID. **Confirm it's your crypto channel.**

### 6. Test Upload

Trigger a manual workflow run on GitHub Actions:
1. Go to **Actions** tab in your repository
2. Select **Daily Auto Shorts with YouTube Upload**
3. Click **Run workflow**
4. Check that the video uploads to your **crypto channel**

## Troubleshooting

### "Wrong channel is being used"
- Delete the old `youtube_credentials.json` file
- Re-run `get_youtube_token.py` and carefully select the crypto channel

### "Invalid refresh token"
- Make sure you copied the **entire** refresh token (it's long!)
- Check for extra spaces or line breaks when pasting into GitHub Secrets

### "Quota exceeded"
- YouTube API has daily upload quotas
- Wait 24 hours and try again
- Consider requesting quota increase from Google Cloud Console

## Important Notes

> [!WARNING]
> **Do NOT commit** `youtube_credentials.json` or any credential files to GitHub. They are already in `.gitignore`.

> [!TIP]
> Keep your old credentials backed up somewhere safe in case you need to switch back to the previous channel.

## Need Help?

If you encounter issues:
1. Check the GitHub Actions logs for error messages
2. Run `python diagnose_youtube_credentials.py` for detailed diagnostics
3. Verify your Google Cloud project has YouTube Data API v3 enabled
