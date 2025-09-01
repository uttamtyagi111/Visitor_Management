import qrcode
import os

# URL to your API (or web form)
api_url = "http://127.0.0.1:8000/api/visitors/"

# Make sure the folder exists
os.makedirs("static/qr", exist_ok=True)

# Generate QR code
img = qrcode.make(api_url)

# Save the QR code image
img.save("static/qr/visitor_api_qr.png")

print("QR code generated at static/qr/visitor_api_qr.png")
