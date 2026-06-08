import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
cx = os.getenv("GOOGLE_CX")

print(f"Key exists: {bool(api_key)}, CX exists: {bool(cx)}")
url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q=startup"
try:
    r = requests.get(url).json()
    if "error" in r:
        print("GOOGLE API ERROR:", r["error"])
    else:
        print("SUCCESS! Found", len(r.get("items", [])), "items.")
except Exception as e:
    print("REQUEST FAILED:", e)
