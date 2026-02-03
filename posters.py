# posters.py (Handles LinkedIn posting)
import requests
import os
import re
from config import LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN

def get_linkedin_person_urn():
    """Fetch person URN from LinkedIn API using /v2/userinfo (OIDC-compatible)"""
    if not LINKEDIN_ACCESS_TOKEN:
        print("⚠️ LinkedIn: Missing access token")
        return None
    
    try:
        headers = {
            'Authorization': f'Bearer {LINKEDIN_ACCESS_TOKEN}',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        response = requests.get(
            'https://api.linkedin.com/v2/userinfo',  # Updated endpoint for OIDC
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            person_id = data.get('sub')  # 'sub' is the person ID in OIDC response
            if person_id:
                urn = f"urn:li:person:{person_id}"
                print(f"✅ Your LinkedIn Person URN: {urn}")
                print(f"💡 Add to .env: LINKEDIN_PERSON_URN={urn}")
                return urn
            else:
                print("❌ No 'sub' in response—check 'profile' scope")
                return None
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            print("💡 Ensure scopes include 'openid' and 'profile'; regenerate token if needed")
            return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def upload_image_to_linkedin(image_path):
    """Upload image to LinkedIn and return asset URN"""
    if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_PERSON_URN:
        print("⚠️ Missing LinkedIn token or URN for image upload")
        return None
    
    headers = {
        'Authorization': f'Bearer {LINKEDIN_ACCESS_TOKEN}',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json'
    }
    
    # Step 1: Register upload
    register_url = 'https://api.linkedin.com/v2/assets?action=registerUpload'
    register_payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": LINKEDIN_PERSON_URN,
            "serviceRelationships": [
                {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
            ]
        }
    }
    
    try:
        reg_response = requests.post(register_url, headers=headers, json=register_payload)
        if reg_response.status_code != 200:
            print(f"❌ Register upload error: {reg_response.status_code} - {reg_response.text}")
            return None
        
        reg_data = reg_response.json()
        asset_urn = reg_data['value']['asset']
        
        # Fixed: Correct path to uploadUrl
        upload_url = reg_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        
        print(f"✅ Registered upload: Asset URN {asset_urn}")
        
        # Step 2: Upload image binary
        upload_headers = {
            'Authorization': f'Bearer {LINKEDIN_ACCESS_TOKEN}',
            'Content-Type': 'image/png'  # Assuming PNG
        }
        
        with open(image_path, 'rb') as img_file:
            upload_response = requests.put(upload_url, headers=upload_headers, data=img_file)
        
        if upload_response.status_code != 201:
            print(f"❌ Image upload error: {upload_response.status_code} - {upload_response.text}")
            return None
        
        print("✅ Image uploaded successfully")
        return asset_urn
        
    except KeyError as ke:
        print(f"❌ KeyError in response structure: {ke}")
        print(f"Response data: {reg_data}")
        return None
    except Exception as e:
        print(f"❌ Image upload exception: {e}")
        return None

def post_to_linkedin(caption, image_path=None):
    """Post to LinkedIn with optional image"""
    global LINKEDIN_PERSON_URN  # Allow mutation
    if not LINKEDIN_ACCESS_TOKEN:
        print("⚠️ LinkedIn: Missing access token")
        return False
    
    # Auto-fetch URN if missing
    if not LINKEDIN_PERSON_URN or not LINKEDIN_PERSON_URN.startswith('urn:li:person:'):
        person_urn = get_linkedin_person_urn()
        if person_urn:
            LINKEDIN_PERSON_URN = person_urn
        else:
            print("❌ Failed to fetch URN—check token scopes (w_member_social)")
            return False
    
    headers = {
        'Authorization': f'Bearer {LINKEDIN_ACCESS_TOKEN}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }
    
    try:
        image_urn = None
        if image_path:
            # Upload image and get asset URN
            image_urn = upload_image_to_linkedin(image_path)
            if not image_urn:
                print("❌ Failed to upload image, posting text only")
        
        # Prepare post data
        specific_content = {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": caption
                }
            }
        }
        
        if image_urn:
            specific_content["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            specific_content["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "media": image_urn,
                    "title": {"text": "Job Opportunity Image"}
                }
            ]
        else:
            specific_content["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "NONE"
        
        data = {
            "author": LINKEDIN_PERSON_URN,
            "lifecycleState": "PUBLISHED",
            "specificContent": specific_content,
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        response = requests.post(
            'https://api.linkedin.com/v2/ugcPosts',
            headers=headers,
            json=data
        )
        
        if response.status_code == 201:
            print("✅ LinkedIn posted successfully!")
            return True
        else:
            print(f"❌ LinkedIn Error {response.status_code}: {response.text}")
            if "author" in response.text:
                print("💡 Fix: Run get_linkedin_person_urn() and update .env")
            return False
        
    except Exception as e:
        print(f"❌ LinkedIn Error: {str(e)}")
        return False