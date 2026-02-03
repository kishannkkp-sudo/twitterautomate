import tweepy

client = tweepy.Client(
    bearer_token="AAAAAAAAAAAAAAAAAAAAANiY5AEAAAAAkJJhLjeojcJ%2FPxTHkHIJjBCUPUk%3Dt1n7060cxAJapcD9fkoWTLEMNnwq76V6L8PwdvEq9SBHp09Jmq",
    consumer_key="tnsNt7TrgQZVV175BHxSFhV8i",
    consumer_secret="kKh9U0wxSjTPHfCsdnTCzemjgztMXHX2PBWvoc4vjyf7taFiw3",
    access_token="1255749963054583810-TGNveUSdXizvNFqf9UZ4WvsDAukIZT",
    access_token_secret="OsYXonvg8soqdQGAP2WBM1MJV31ogVwJzOdPQ0SL2O5ok"
)

try:
    response = client.create_tweet(text="✅ Test tweet via API v2 Tweepy Client!")
    print("✅ Posted successfully, tweet ID:", response.data["id"])
except Exception as e:
    print("❌ Error:", e)
