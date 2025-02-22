import json
import requests
from openai import OpenAI
from dotenv import load_dotenv
import os
import streamlit as st  # Use Streamlit secrets

# Load environment variables
load_dotenv()

# Get API keys from environment variables
MOZ_API_TOKEN = st.secrets('MOZ_API_TOKEN')
OPENAI_API_KEY = st.secrets('OPENAI_API_KEY')

# API Headers
HEADERS = {
    "x-moz-token": MOZ_API_TOKEN,
    "Content-Type": "application/json",
}

def get_suggested_keywords(search_query):
    """Fetch suggested keywords from Moz API."""
    data = {
        "jsonrpc": "2.0",
        "id": "a825164-a0be-44f8-9c68-02f90f49093b",
        "method": "data.keyword.suggestions.list",
        "params": {
            "data": {
                "serp_query": {
                    "keyword": search_query,
                    "locale": "en-US",
                    "device": "desktop",
                    "engine": "google"
                }
            }
        }
    }
    
    response = requests.post("https://api.moz.com/jsonrpc", headers=HEADERS, data=json.dumps(data))
    
    if response.status_code == 200:
        result = response.json()
        return result.get("result", {}).get("suggestions", [])
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return []

def get_keyword_metrics(keyword):
    """Fetch keyword metrics from Moz API."""
    data = {
        "jsonrpc": "2.0",
        "id": "285a801c-b526-4d69-8566-dd8442700639",
        "method": "data.keyword.metrics.fetch",
        "params": {
            "data": {
                "serp_query": {
                    "keyword": keyword,
                    "locale": "en-US",
                    "device": "desktop",
                    "engine": "google"
                }
            }
        }
    }
    
    response = requests.post("https://api.moz.com/jsonrpc", headers=HEADERS, data=json.dumps(data))
    
    if response.status_code == 200:
        result = response.json()
        return result.get("result", {}).get("keyword_metrics", {})
    elif response.status_code == 404:
        print(f"⚠️ No data for: {keyword} (Skipping)")
        return None  # No data for this keyword
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return {}

def analyze_keywords(primary_keyword, keywords_data):
    """Use OpenAI to analyze keywords and suggest secondary ones."""
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    system_prompt = (
    "You are an expert in SEO and keyword analysis. "
    "Given a list of suggested keywords and their metrics, determine the primary keyword and three relevant secondary keywords. " 

    "- The primary keyword is the main search query that best represents the user's intent. "
    "- The secondary keywords should complement the primary keyword, enhance content optimization, and improve search ranking. "
    "- If a suggested secondary keyword is irrelevant, redundant, or suboptimal, replace it with a more suitable one based on your SEO expertise. "
    "- If none of the suggested secondary keywords are appropriate, generate three entirely new secondary keywords that align with the primary keyword's intent and search ranking potential. "
    "- Predict three secondary keywords for the primary keyword based on your expertise, then compare them with the secondary keywords suggested by Moz (/keyword_data) and select the better/more relevant ones. "
    "- The content intent should be one of: informational, commercial, transactional, or navigational. "
    "- Do not include numbers (e.g., 2025, top 10, best 5) or dates in the primary or secondary keywords. If any suggested keyword contains numbers or dates, replace it with a more appropriate alternative. "

    "Format the output exactly as follows (maintain the exact format):"

    "Primary keyword: <primary_keyword>"
    "Secondary keywords: <keyword1>, <keyword2>, <keyword3>"
    "Intent: <content_intent>"
)


    
    user_prompt = f"Primary keyword: {primary_keyword}\nHere is the keyword data:\n{json.dumps(keywords_data, indent=2)}\n\nIdentify three secondary keywords."
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return response.choices[0].message.content

def main():
    """Main script function to get keyword suggestions, fetch their metrics, and analyze with OpenAI."""
    search_query = input("Enter your search query: ").strip()
    
    # Step 1: Get Suggested Keywords
    suggested_keywords = get_suggested_keywords(search_query)
    
    if not suggested_keywords:
        print("❌ No suggested keywords found.")
        return
    
    print("\n--- 🔍 Suggested Keywords & Metrics ---")
    
    keywords_data = []
    seen_keywords = set()  # Prevent duplicate keywords
    
    # Step 2: Fetch metrics for each suggested keyword
    for suggestion in suggested_keywords[:10]:  # Limit to first 10 suggestions
        keyword_text = suggestion["keyword"].strip()
        
        if keyword_text in seen_keywords:
            continue  # Skip duplicates
        
        seen_keywords.add(keyword_text)
        
        metrics = get_keyword_metrics(keyword_text)
        if metrics is None:
            continue  # Skip keywords with no data
        
        keyword_entry = {
            "keyword": keyword_text,
            "volume": metrics.get("volume", "N/A"),
            "difficulty": metrics.get("difficulty", "N/A"),
            "organic_ctr": metrics.get("organic_ctr", "N/A"),
            "priority": metrics.get("priority", "N/A"),
        }
        keywords_data.append(keyword_entry)
        
        print(f"\n📌 Keyword: {keyword_text}")
        print(f"   🔹 Volume: {keyword_entry['volume']}")
        print(f"   🔹 Difficulty: {keyword_entry['difficulty']}")
        print(f"   🔹 Organic CTR: {keyword_entry['organic_ctr']}")
        print(f"   🔹 Priority: {keyword_entry['priority']}")
    
    # Step 3: Analyze Keywords using OpenAI
    print("\n--- 🤖 Keyword Analysis ---")
    analysis_result = analyze_keywords(search_query, keywords_data)
    print(analysis_result)

# Run the script
if __name__ == "__main__":
    main()