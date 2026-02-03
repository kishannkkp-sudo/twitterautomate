# x_posters.py (Updated: Fixed Tweepy API initialization)
import tweepy
from config import (
    TWITTER_BEARER_TOKEN, TWITTER_API_KEY, TWITTER_API_KEY_SECRET,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
)
import os
import time

def post_to_x(caption, image_path=None):
    """Post to X.com using Tweepy (v2 tweet + v1.1 media upload); fallback to text-only"""
    if not all([TWITTER_API_KEY, TWITTER_API_KEY_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        print("⚠️ X.com: Missing credentials")
        return False

    # Tweepy setup: Client for v2 tweets, API for v1.1 media
    try:
        client = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_KEY_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True  # Auto-wait on limits
        )
        
        # Fixed: Use OAuth1UserHandler for API authentication
        auth = tweepy.OAuth1UserHandler(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_KEY_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
        )
        api = tweepy.API(auth, wait_on_rate_limit=True)
    except Exception as e:
        print(f"❌ Tweepy init error: {e}")
        return False

    # Step 1: If image, upload via v1.1 API
    media_ids = []
    if image_path and os.path.exists(image_path):
        try:
            media = api.media_upload(image_path)
            media_ids = [media.media_id]
            print("✅ Media uploaded to X.com")
        except tweepy.TweepyException as e:
            print(f"⚠️ Media upload failed: {str(e)}. Posting text-only.")
            # Proceed to text post
        except Exception as e:
            print(f"⚠️ Media upload exception: {e}. Posting text-only.")
    else:
        print("ℹ️ No image provided; posting text-only.")

    # Step 2: Create tweet via v2 Client
    try:
        if media_ids:
            response = client.create_tweet(text=caption, media_ids=media_ids)
        else:
            response = client.create_tweet(text=caption)

        if response.data:
            print(f"✅ X.com post successful! Tweet ID: {response.data['id']} (with image: {'Yes' if media_ids else 'No'})")
            return True
        else:
            print("❌ No response data from X.com")
            return False
    except tweepy.TooManyRequests as e:
        reset_time = e.response.headers.get('x-ratelimit-reset', time.time() + 3600)
        wait_sec = max(300, int(reset_time) - int(time.time()) + 1)
        print(f"⚠️ Rate limited! Waiting {wait_sec} sec before retry...")
        time.sleep(wait_sec)
        return post_to_x(caption, image_path)  # Retry once
    except tweepy.Forbidden as e:
        print(f"❌ 403 Forbidden: {str(e)} | Check permissions (Read + Write, Bot type)")
        return False
    except tweepy.Unauthorized as e:
        print(f"❌ 401 Unauthorized: {str(e)} | Regenerate Access Token with Read + Write")
        return False
    except tweepy.TweepyException as e:
        print(f"❌ X.com Tweepy Error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ X.com Exception: {str(e)}")
        return False