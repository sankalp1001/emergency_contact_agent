import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env (must be at top)
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("GROQ_API_KEY not found in environment or .env")

client = Groq(api_key=API_KEY)

def call_llm(full_prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful emergency assistant."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content
if __name__ == "__main__":
    # Example usage
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the weather like today?"}
    ]
    
    response = call_llm(messages)
    print("LLM Response:", response)  # Print the LLM's response content