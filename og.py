from firecrawl import FirecrawlApp
import json
from datetime import datetime
from typing import List, Dict
import time
import re
from bs4 import BeautifulSoup
from collections import Counter
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv
import streamlit as st  # Use Streamlit secrets

class LLMEnhancedAnalyzer:
    def __init__(self, firecrawl_api_key: str, openai_api_key: str):
        self.firecrawl = FirecrawlApp(api_key=firecrawl_api_key)
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.article_intent = ""
        self.secondary_keywords = []

    def set_content_parameters(self, intent: str, keywords: List[str]):
        """Set the content parameters for better LLM analysis"""
        self.article_intent = intent
        self.secondary_keywords = keywords

    def extract_serp_data(self, data: Dict) -> Dict:
        """Extract data from SERP API results"""
        return {
            'organic_results': self.extract_organic_results(data),
            'paa_questions': self.extract_paa_questions(data),
            'related_searches': self.extract_related_searches(data)
        }

    def extract_organic_results(self, data: Dict) -> List[Dict]:
        """Extract organic results from SERP data"""
        results = []
        for article in data.get('organic_results', []):
            result = {
                'title': article.get('title', ''),
                'link': article.get('link', ''),
                'date': article.get('date', ''),
                'snippet': article.get('snippet', ''),
                'position': article.get('position', ''),
                'displayed_link': article.get('displayed_link', '')
            }
            results.append(result)
        return results

    def extract_paa_questions(self, data: Dict) -> List[Dict]:
        """Extract People Also Ask questions"""
        questions = []
        for question in data.get('related_questions', []):
            questions.append({
                'question': question.get('question', ''),
                'snippet': question.get('snippet', ''),
                'title': question.get('title', '')
            })
        return questions

    def extract_related_searches(self, data: Dict) -> List[Dict]:
        """Extract related searches"""
        return [{'query': search.get('query', '')} 
                for search in data.get('related_searches', [])]

    def scrape_competitor_content(self, urls: List[str]) -> List[Dict]:
        """Scrape and analyze competitor content"""
        scraped_content = []
        
        for url in urls:
            try:
                # Basic scraping parameters
                params = {
                    'formats': ['markdown', 'html']
                }
                
                # Perform the scrape with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        result = self.firecrawl.scrape_url(url, params=params)
                        
                        # Get content with fallback
                        content = result.get('html', result.get('markdown', ''))
                        
                        # Analyze the content
                        analysis = self.analyze_content(content)
                        
                        content_data = {
                            'url': url,
                            'content': content,
                            'analysis': analysis
                        }
                        
                        scraped_content.append(content_data)
                        print(f"Successfully scraped: {url}")
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            print(f"Error scraping {url}: {str(e)}")
                        else:
                            print(f"Retry {attempt + 1} for {url}")
                            time.sleep(2)
                
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
                continue
                
        return scraped_content

    def analyze_content(self, content: str) -> Dict:
        """Analyze scraped content for insights"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            text_content = soup.get_text() if soup.get_text() else content

            analysis = {
                'word_count': len(text_content.split()),
                'common_phrases': self.extract_common_phrases(text_content),
                'content_structure': self.analyze_content_structure(text_content),
                'key_topics': self.extract_key_topics(text_content),
                'content_elements': self.identify_content_elements(content)
            }
            return analysis
        except Exception as e:
            print(f"Error in content analysis: {str(e)}")
            return {}

    def get_llm_analysis(self, context: str, system_prompt: str) -> str:
        """Get LLM analysis using OpenAI API"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in LLM analysis: {str(e)}")
            return ""

    def analyze_with_llm(self, scraped_data: List[Dict], serp_data: Dict) -> Dict:
        """Analyze content using LLM"""
        
        # Prepare context for LLM
        context = self.prepare_llm_context(scraped_data, serp_data)
        
        # Define system prompts
        prompts = {
            'outline_structure': f"""Create a comprehensive SEO article outline for: {serp_data.get('search_parameters', {}).get('q', '')}

Target Audience:
- Primary: Business owners, entrepreneurs, and startup founders in the USA
- Secondary: Business leaders and aspiring entrepreneurs
- Industry level: Intermediate

SEO Elements to Include:
1. Recommended meta title (50-60 characters)
2. Meta description (130-155 characters)
3. Primary keyword: {serp_data.get('search_parameters', {}).get('q', '')}
   Secondary keywords: {', '.join(self.secondary_keywords)}
4. Search intent: {self.article_intent}
5. Suggested internal linking topics and detailed internal linking methods (e.g., linking to pillar pages, related articles, or product pages)
6. Types of external sources to reference
7. If there is a data mentioned in H1 tag use only the present year

Please structure the output exactly as follows:

Primary keyword: [Insert primary keyword]
Secondary keywords: [Insert secondary keywords]

Meta title: [Insert optimized title]
Meta description: [Insert compelling description]

Slug: [Insert primary keyword as slug]

Outline:

H1:Options [Provide 3-5 title options]

Introduction: [Outline approach and key points]

H2: [Main section title]
  - H3: [Subsection points]
  - H3: [Subsection points]
[Continue with all H2 and H3 sections]

Conclusion: [Outline approach]

FAQ:
1. [Question 1]
2. [Question 2]
3. [Question 3]
4. [Question 4]
5. [Question 5]

Writing Guidelines:
- Word count target: [ Predict Based on the competitor analysis]
- Content tone: Professional
- Statistics/data placement
- Expert quote areas
- Visual content opportunities
- Content upgrades/lead magnets
- Key takeaways
- Internal/external linking strategy

Article Type Prediction: 

Based on SERP analysis, competitor data, and {serp_data.get('search_parameters', {}).get('q', '')}, the best article format for this topic is:  
[Insert predicted article type - e.g., "How-To Guide," "Listicle," "Comparison Blog," "Technical Article," "Product Review," etc.]  

Justification:  
- [Explain why this format is ideal based on user search behavior, top-ranking content structures, and competitor trends]  
"""
        }
        
        # Get LLM analysis for each aspect
        analysis = {}
        for aspect, prompt in prompts.items():
            print(f"Getting LLM analysis for: {aspect}")
            analysis[aspect] = self.get_llm_analysis(context, prompt)
            time.sleep(1)  # Rate limiting
        
        return analysis

    def prepare_llm_context(self, scraped_data: List[Dict], serp_data: Dict) -> str:
        """Prepare context for LLM analysis"""
        serp_analysis = self.extract_serp_data(serp_data)
        
        context = f"""
Search Query: {serp_data.get('search_parameters', {}).get('q', '')}

Content Parameters:
Article Intent: {self.article_intent}
Secondary Keywords: {', '.join(self.secondary_keywords)}

Top Ranking Articles:
{self.format_top_articles(serp_analysis['organic_results'])}

People Also Ask Questions:
{self.format_paa_questions(serp_analysis['paa_questions'])}

Related Searches:
{self.format_related_searches(serp_analysis['related_searches'])}

Competitor Content Analysis:
{self.format_competitor_content(scraped_data)}
"""
        return context

    def generate_enhanced_outline(self, serp_data: Dict, scraped_data: List[Dict]) -> str:
        """Generate enhanced marketing outline using LLM insights"""
        print("Starting LLM analysis...")
        llm_insights = self.analyze_with_llm(scraped_data, serp_data)
        
        print("Formatting final outline...")
        return self.format_llm_outline(llm_insights, serp_data)

    # Helper methods with proper error handling
    def format_top_articles(self, results: List[Dict]) -> str:
        try:
            return "\n".join([
                f"- {result['title']}\n  URL: {result['link']}"
                for result in results[:5]
            ])
        except Exception as e:
            print(f"Error formatting top articles: {str(e)}")
            return ""

    def format_paa_questions(self, questions: List[Dict]) -> str:
        try:
            return "\n".join([
                f"- {q['question']}"
                for q in questions
            ])
        except Exception as e:
            print(f"Error formatting PAA questions: {str(e)}")
            return ""

    def format_related_searches(self, searches: List[Dict]) -> str:
        try:
            return "\n".join([
                f"- {search['query']}"
                for search in searches
            ])
        except Exception as e:
            print(f"Error formatting related searches: {str(e)}")
            return ""

    def format_competitor_content(self, scraped_data: List[Dict]) -> str:
        try:
            content_summary = []
            for data in scraped_data:
                analysis = data.get('analysis', {})
                summary = f"""
URL: {data.get('url', '')}
Word Count: {analysis.get('word_count', 0)}
Key Topics: {', '.join(analysis.get('key_topics', [])[:5])}
"""
                content_summary.append(summary)
            return "\n".join(content_summary)
        except Exception as e:
            print(f"Error formatting competitor content: {str(e)}")
            return ""

    def format_llm_outline(self, llm_insights: Dict, serp_data: Dict) -> str:
        """Format LLM insights into the final outline"""
        try:
            return f"""Outline for : "{serp_data.get('search_parameters', {}).get('q', '')}"


 
{llm_insights.get('outline_structure', 'No outline structure generated')}

 


Generated for: {serp_data.get('search_parameters', {}).get('q', '')}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        except Exception as e:
            print(f"Error formatting LLM outline: {str(e)}")
            return "Error generating outline"

    def extract_common_phrases(self, text_content: str) -> List[str]:
        """Extract common phrases from text content"""
        try:
            # Basic phrase extraction using regex
            phrases = re.findall(r'\b[\w\s]{10,30}\b', text_content.lower())
            # Count and return most common phrases
            phrase_counter = Counter(phrases)
            return [phrase for phrase, count in phrase_counter.most_common(10)]
        except Exception as e:
            print(f"Error extracting common phrases: {str(e)}")
            return []

    def analyze_content_structure(self, text_content: str) -> Dict:
        """Analyze content structure including headings and sections"""
        try:
            # Basic structure analysis
            paragraphs = text_content.split('\n\n')
            structure = {
                'total_paragraphs': len(paragraphs),
                'avg_paragraph_length': sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0,
            }
            return structure
        except Exception as e:
            print(f"Error analyzing content structure: {str(e)}")
            return {}

    def extract_key_topics(self, text_content: str) -> List[str]:
        """Extract key topics from content"""
        try:
            # Simple keyword extraction
            words = re.findall(r'\b\w+\b', text_content.lower())
            # Filter common words and get most frequent
            word_counter = Counter(words)
            return [word for word, count in word_counter.most_common(10)]
        except Exception as e:
            print(f"Error extracting key topics: {str(e)}")
            return []

    def identify_content_elements(self, content: str) -> Dict:
        """Identify various content elements like lists, tables, etc."""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            elements = {
                'lists': len(soup.find_all(['ul', 'ol'])),
                'tables': len(soup.find_all('table')),
                'images': len(soup.find_all('img')),
                'links': len(soup.find_all('a')),
                'headings': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
            }
            return elements
        except Exception as e:
            print(f"Error identifying content elements: {str(e)}")
            return {}

def get_search_results(query: str, api_key: str, num_results: int = 10) -> Dict:
    """Get search results from SerpAPI with enhanced error handling and logging"""
    url = "https://serpapi.com/search"
    
    # Validate API key
    if not api_key or api_key.isspace():
        st.error("SERPAPI_KEY is not properly configured in Streamlit secrets")
        return None
        
    params = {
        "q": query,
        "api_key": api_key,
        "num": num_results,
        "hl": "en",
        "gl": "us"
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Add logging for debugging
            st.write(f"Attempting SERP API call (attempt {attempt + 1}/{max_retries})")
            
            response = requests.get(url, params=params, timeout=30)
            
            # Log response status for debugging
            st.write(f"SERP API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                st.error("SERP API Authentication failed. Please check your API key.")
                return None
            else:
                st.error(f"SERP API Error: {response.status_code}, {response.text}")
                
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                st.error(f"Failed to fetch SERP data after {max_retries} attempts: {str(e)}")
                return None
            st.warning(f"Attempt {attempt + 1} failed, retrying...")
            time.sleep(2)
    
    return None

def main():
    try:
        
        # API Keys
        FIRECRAWL_API_KEY = st.secrets["FIRECRAWL_API_KEY"]
        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
        SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
        

        # Get search query from user
        search_query = input("Enter your search query: ")

        # Get SERP data directly using SerpAPI
        print("Fetching SERP data...")
        serp_data = get_search_results(search_query, SERPAPI_KEY)
        
        if not serp_data: 
            raise Exception("Failed to fetch SERP data")

        # Initialize analyzer with API keys
        analyzer = LLMEnhancedAnalyzer(
            firecrawl_api_key=FIRECRAWL_API_KEY,
            openai_api_key=OPENAI_API_KEY
        )
        
        # Get content parameters from user
        intent = input("Enter article intent (e.g., informational, commercial): ")
        keywords = input("Enter secondary keywords (comma-separated): ").split(',')
        
        # Set content parameters
        analyzer.set_content_parameters(
            intent=intent,
            keywords=[k.strip() for k in keywords]
        )
        
        # Extract URLs to scrape
        urls_to_scrape = [
            result['link'] 
            for result in serp_data.get('organic_results', [])[:5]
        ]
        
        # Scrape competitor content
        print("Scraping competitor content...")
        scraped_data = analyzer.scrape_competitor_content(urls_to_scrape)
        
        # Generate enhanced outline with LLM insights
        print("Generating enhanced outline...")
        enhanced_outline = analyzer.generate_enhanced_outline(serp_data, scraped_data)
        
        # Save the enhanced outline
        print("Saving outline...")
        with open('simplifiedoutput3.txt', 'w', encoding='utf-8') as f:
            f.write(enhanced_outline)
        
        print("LLM-enhanced marketing outline generated successfully!")
        
    except Exception as e:
        print(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    main()


