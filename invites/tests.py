import requests

# Step 1: Create Invite
create_url = "http://127.0.0.1:8000/invites/"
create_data = {
    "visitor_name": "John Doe",
    "visitor_email": "john.doe@example.com",
    "visitor_phone": "+1234567890",
    "purpose": "Business Meeting",
    "visit_time": "2025-09-05T16:30:00+05:30",
    "expiry_time": "2025-09-05T18:00:00+05:30"
}
create_response = requests.post(create_url, json=create_data, headers={"Authorization": "Token your-auth-token"})
invite = create_response.json()
invite_code = invite["invite_code"]
print(f"Created invite with code: {invite_code}")

# Step 2: Capture Visitor Data
capture_url = "http://127.0.0.1:8000/invites/capture/"
with open("media\\visitor_images\\03ebd625cc0b9d636256ecc44c0ea324_pIcBhgK.jpg", "rb") as image_file:
    capture_response = requests.post(
        capture_url,
        files={"image": image_file},
        data={"invite_code": invite_code},
        headers={"Authorization": "Token your-auth-token"}
    )
print(f"Capture response: {capture_response.json()}")

# Step 3: Verify Pass
verify_url = f"http://127.0.0.1:8000/invites/verify-pass/{invite_code}/"
verify_response = requests.get(verify_url)
print(f"Verify response: {verify_response.status_code}, Location: {verify_response.headers.get('Location')}")