import os
import urllib.request
import json
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Không tìm thấy API Key!")
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("\n✅ TÌM THẤY CÁC MÔ HÌNH HỖ TRỢ DỊCH VECTOR (EMBEDDING):\n")
            
            for m in data.get("models", []):
                # Lưu ý: Lần này chúng ta tìm chữ embedContent
                if "embedContent" in m.get("supportedGenerationMethods", []):
                    print(f"👉 {m['name']}")
                    
    except Exception as e:
        print("\n❌ Lỗi khi gọi API:", e)