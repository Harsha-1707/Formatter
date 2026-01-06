import google.generativeai as genai

API_KEY = "AIzaSyC3RQ-85UgnNjcFqyPzUFlUUwyo9gtth1M"
genai.configure(api_key=API_KEY)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
