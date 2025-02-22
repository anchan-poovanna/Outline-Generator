import streamlit as st
from og import LLMEnhancedAnalyzer, get_search_results
from key_pred2 import get_suggested_keywords, get_keyword_metrics, analyze_keywords
import json
from datetime import datetime
import time
from dotenv import load_dotenv
import os
from typing import List, Dict

def safe_split(text, delimiter1, delimiter2=None):
    """Safely split text between two delimiters"""
    try:
        if delimiter2:
            split1 = text.split(delimiter1, 1)
            if len(split1) > 1:
                split2 = split1[1].split(delimiter2, 1)
                return split2[0].strip() if len(split2) > 1 else ""
        else:
            split1 = text.split(delimiter1, 1)
            return split1[1].strip() if len(split1) > 1 else ""
    except Exception as e:
        st.error(f"Error processing content: {str(e)}")
        return ""

def display_enhanced_outline(enhanced_outline):
    """Display enhanced outline with structured format"""
    try:
        if not enhanced_outline:
            st.error("No outline content available")
            return

        sections = {
            "Primary keyword": ("Primary keyword:", "Secondary keywords:"),
            "Secondary keywords": ("Secondary keywords:", "Meta title:"),
            "Meta Title": ("Meta title:", "Meta description:"),
            "Meta Description": ("Meta description:", "Slug:"),
            "Slug": ("Slug:", "Outline:"),
            "Outline": ("Outline:", "Writing Guidelines:"),
            "Writing Guidelines": ("Writing Guidelines:", "Article Type Prediction:"),
            "Article Type Prediction": ("Article Type Prediction:", "Justification:"),
            "Justification": ("Justification:", None)
        }

        st.markdown("<p class='big-font'>Enhanced Content Outline:</p>", unsafe_allow_html=True)

        for section_name, (start_delimiter, end_delimiter) in sections.items():
            try:
                content = safe_split(enhanced_outline, start_delimiter, end_delimiter)
                
                if section_name == "Outline":
                    st.markdown("<div class='medium-font'>", unsafe_allow_html=True)
                    st.markdown("<p><strong>Outline:</strong></p>", unsafe_allow_html=True)
                    
                    # Split the outline content into sections
                    outline_parts = content.split("H2:")
                    
                    # Handle H1 and Introduction if present
                    if outline_parts[0]:
                        h1_intro = outline_parts[0].split("Introduction:")
                        if len(h1_intro) > 0:
                            st.markdown("<p><strong>H1 Options:</strong></p>", unsafe_allow_html=True)
                            h1_options = [opt.strip() for opt in h1_intro[0].split('-') if opt.strip()]
                            for opt in h1_options:
                                st.markdown(f"• {opt}", unsafe_allow_html=True)
                        
                        if len(h1_intro) > 1:
                            st.markdown("<p><strong>Introduction:</strong></p>", unsafe_allow_html=True)
                            st.markdown(h1_intro[1].strip(), unsafe_allow_html=True)
                    
                    # Handle H2 and H3 sections
                    for section in outline_parts[1:]:
                        if section.strip():
                            lines = section.split('\n')
                            # First line is H2 title
                            st.markdown(f"<p><strong>H2:</strong> {lines[0].strip()}</p>", unsafe_allow_html=True)
                            # Following lines are H3 points
                            for line in lines[1:]:
                                if line.strip().startswith('H3:'):
                                    st.markdown(f"  • {line.strip()[3:]}", unsafe_allow_html=True)
                    
                    # Handle FAQ section if present
                    if "FAQ:" in content:
                        st.markdown("<p><strong>FAQ:</strong></p>", unsafe_allow_html=True)
                        faq_content = content.split("FAQ:")[1].split("Writing Guidelines:")[0]
                        faq_items = [q.strip() for q in faq_content.split('\n') if q.strip()]
                        for i, question in enumerate(faq_items, 1):
                            st.markdown(f"{i}. {question}", unsafe_allow_html=True)

                elif section_name == "Writing Guidelines":
                    st.markdown("<div class='medium-font'>", unsafe_allow_html=True)
                    st.markdown("<p><strong>Writing Guidelines:</strong></p>", unsafe_allow_html=True)
                    guidelines = [g.strip() for g in content.split('-') if g.strip()]
                    for guideline in guidelines:
                        st.markdown(f"• {guideline}", unsafe_allow_html=True)

                elif section_name == "Article Type Prediction":
                    st.markdown("<div class='medium-font'>", unsafe_allow_html=True)
                    st.markdown("<p><strong>Article Type Prediction:</strong></p>", unsafe_allow_html=True)
                    st.markdown(content, unsafe_allow_html=True)

                elif section_name == "Justification":
                    st.markdown("<div class='medium-font'>", unsafe_allow_html=True)
                    st.markdown("<p><strong>Justification:</strong></p>", unsafe_allow_html=True)
                    justification_points = [j.strip() for j in content.split('-') if j.strip()]
                    for point in justification_points:
                        st.markdown(f"• {point}", unsafe_allow_html=True)

                else:
                    st.markdown("<div class='medium-font'>", unsafe_allow_html=True)
                    st.markdown(f"<p><strong>{section_name}:</strong> {content}</p>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error displaying {section_name}: {str(e)}")
                continue

    except Exception as e:
        st.error(f"Error displaying outline: {str(e)}")
        st.error("Detailed error info:", exc_info=True)

# Load environment variables
load_dotenv()

# Get API keys from environment variables
FIRECRAWL_API_KEY = st.secrets["FIRECRAWL_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
MOZ_API_TOKEN = st.secrets["MOZ_API_TOKEN"]


# Configure page
st.set_page_config(page_title="Outline Generator", layout="wide")

# Add custom CSS
st.markdown("""
    <style>
    .big-font {
        font-size:24px !important;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .medium-font {
        font-size:16px !important;
        line-height: 1.6;
    }
    .medium-font p {
        margin-bottom: 20px;
    }
    .medium-font strong {
        color: #1f77b4;
    }
    .log-font {
        font-family: 'Courier New', Courier, monospace;
        font-size:14px;
        color: #00ff00;  /* Bright green color for logs */
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        background-color: rgba(0, 0, 0, 0.2);
        border-left: 3px solid #00ff00;
        box-shadow: 0 2px 4px rgba(0, 255, 0, 0.1);
        transition: all 0.3s ease;
    }
    .log-font:hover {
        transform: translateX(5px);
        box-shadow: 2px 2px 8px rgba(0, 255, 0, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.markdown("<h1 style='text-align: center;'>Content Analyzer</h1>", unsafe_allow_html=True)
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 2])
    
    # Left column - Input fields
    with col1:
        st.markdown("<p class='big-font'>Input Parameters</p>", unsafe_allow_html=True)
        initial_query = st.text_input("Enter your search query:", key="search_query")
        analyze_button = st.button("Generate Analysis")

        # Add log section in left column
        st.markdown("<p class='big-font'>Analysis Logs</p>", unsafe_allow_html=True)
        log_placeholder = st.empty()

    # Right column - Results
    with col2:
        if analyze_button:
            try:
                # Initialize progress bar
                progress_bar = st.progress(0)
                
                def update_log(message, progress_value):
                    current_time = datetime.now().strftime("%H:%M:%S")
                    messages = {
                        0.05: """
                            <div class='log-font'>
                                [⏱️ {time}] 🤖 Hey there! I'm your AI Content Assistant.
                                <br>🚀 Let's create something amazing together!
                                <br>🎯 Analyzing your query: "{query}"...
                                <div style='height: 2px; background: linear-gradient(to right, #00ff00 {progress}%, transparent {progress}%); margin-top: 5px;'></div>
                            </div>
                        """,
                        0.1: """
                            <div class='log-font'>
                                [⏱️ {time}] 🔍 Diving into the keyword universe...
                                <br>📊 Looking for the most valuable keyword opportunities.
                                <br>⚡ This might take a moment, but it'll be worth it!
                                <div style='height: 2px; background: linear-gradient(to right, #00ff00 {progress}%, transparent {progress}%); margin-top: 5px;'></div>
                            </div>
                        """,
                        0.2: """
                            <div class='log-font'>
                                [⏱️ {time}] 📈 Crunching the numbers...
                                <br>🎲 Analyzing search volumes and competition metrics
                                <br>🎯 Finding the perfect balance for your content strategy
                                <div style='height: 2px; background: linear-gradient(to right, #00ff00 {progress}%, transparent {progress}%); margin-top: 5px;'></div>
                            </div>
                        """,
                        0.3: """
                            <div class='log-font'>
                                [⏱️ {time}] 🧠 Engaging advanced AI analysis...
                                <br>🎯 Determining content intent and focus
                                <br>🔄 Processing keyword relationships and patterns
                                <div style='height: 2px; background: linear-gradient(to right, #00ff00 {progress}%, transparent {progress}%); margin-top: 5px;'></div>
                            </div>
                        """,
                        0.5: """
                            <div class='log-font'>
                                [⏱️ {time}] 🌐 Exploring the digital landscape...
                                <br>🔍 Analyzing top-performing content
                                <br>📊 Gathering competitive insights
                                <div style='height: 2px; background: linear-gradient(to right, #00ff00 {progress}%, transparent {progress}%); margin-top: 5px;'></div>
                            </div>
                        """,
                        0.6: """
                            <div class='log-font'>
                                [⏱️ {time}] ⚙️ Powering up the content engine...
                                <br>🤖 Initializing advanced content analysis
                                <br>🎯 Preparing to craft your perfect outline
                                <div style='height: 2px; background: linear-gradient(to right, #00ff00 {progress}%, transparent {progress}%); margin-top: 5px;'></div>
                            </div>
                        """,
                        0.7: """
                            <div class='log-font'>
                                [⏱️ {time}] 🔎 Investigating competitor strategies...
                                <br>📝 Learning from the best in your niche
                                <br>💡 Discovering unique opportunities
                                <div style='height: 2px; background: linear-gradient(to right, #00ff00 {progress}%, transparent {progress}%); margin-top: 5px;'></div>
                            </div>
                        """,
                        0.9: """
                            <div class='log-font'>
                                [⏱️ {time}] ✍️ Almost there! Crafting your masterpiece...
                                <br>🎨 Adding creative touches
                                <br>🎯 Ensuring SEO optimization
                                <div style='height: 2px; background: linear-gradient(to right, #00ff00 {progress}%, transparent {progress}%); margin-top: 5px;'></div>
                            </div>
                        """,
                        1.0: """
                            <div class='log-font'>
                                [⏱️ {time}] 🎉 Success! Your content strategy is ready!
                                <br>⭐ Thanks for your patience
                                <br>📈 Let's review your personalized content plan below
                                <div style='height: 2px; background: linear-gradient(to right, #00ff00 {progress}%, transparent {progress}%); margin-top: 5px;'></div>
                            </div>
                        """
                    }
                    
                    styled_message = messages.get(progress_value, """
                        <div class='log-font'>
                            [⏱️ {time}] {message}
                            <div style='height: 2px; background: linear-gradient(to right, #00ff00 {progress}%, transparent {progress}%); margin-top: 5px;'></div>
                        </div>
                    """)
                    
                    log_placeholder.markdown(
                        styled_message.format(
                            time=current_time,
                            progress=progress_value * 100,
                            message=message,
                            query=initial_query
                        ),
                        unsafe_allow_html=True
                    )
                    progress_bar.progress(progress_value)

                update_log("🚀 Initializing analysis process...", 0.05)
                time.sleep(0.5)

                update_log("🔍 Getting keyword suggestions and analysis...", 0.1)
                suggested_keywords = get_suggested_keywords(initial_query)
                if not suggested_keywords:
                    st.error("❌ No suggested keywords found.")
                    return

                update_log("📊 Processing keyword metrics...", 0.2)
                keywords_data = []
                seen_keywords = set()

                for suggestion in suggested_keywords[:10]:
                    keyword_text = suggestion["keyword"].strip()
                    if keyword_text in seen_keywords:
                        continue
                    
                    seen_keywords.add(keyword_text)
                    metrics = get_keyword_metrics(keyword_text)
                    
                    if metrics is None:
                        continue

                    keyword_entry = {
                        "keyword": keyword_text,
                        "volume": metrics.get("volume", "N/A"),
                        "difficulty": metrics.get("difficulty", "N/A"),
                        "organic_ctr": metrics.get("organic_ctr", "N/A"),
                        "priority": metrics.get("priority", "N/A"),
                    }
                    keywords_data.append(keyword_entry)

                update_log("🎯 Analyzing keywords...", 0.3)
                analysis_result = analyze_keywords(initial_query, keywords_data)
                
                # Parse the analysis result to get intent along with keywords
                primary_keyword = ""
                secondary_keywords = []
                content_intent = ""
                
                for line in analysis_result.split('\n'):
                    if line.startswith("Primary keyword:"):
                        primary_keyword = line.split(":")[1].strip()
                    elif line.startswith("Secondary keywords:"):
                        secondary_keywords = [k.strip() for k in line.split(":")[1].split(",")]
                    elif line.startswith("Intent:"):
                        content_intent = line.split(":")[1].strip()

                update_log("🌐 Fetching SERP data...", 0.5)
                serp_data = get_search_results(primary_keyword, SERPAPI_KEY)
                
                if not serp_data:
                    st.error("Failed to fetch SERP data")
                    return

                update_log("⚙️ Initializing content analyzer...", 0.6)
                analyzer = LLMEnhancedAnalyzer(
                    firecrawl_api_key=FIRECRAWL_API_KEY,
                    openai_api_key=OPENAI_API_KEY
                )
                
                # Use the automatically determined intent
                analyzer.set_content_parameters(
                    intent=content_intent,
                    keywords=secondary_keywords
                )
                
                # Filter out unsupported sites from SERP results
                urls_to_scrape = [
                    result['link'] 
                    for result in serp_data.get('organic_results', [])[:7]  # Get more results to compensate for filtered ones
                    if not any(domain in result['link'].lower() 
                             for domain in ['youtube.com', 'reddit.com', 'twitter.com', 'facebook.com'])
                ][:5]  # Keep only first 5 supported URLs
                
                update_log("🔎 Scanning competitor content...", 0.7)
                scraped_data = analyzer.scrape_competitor_content(urls_to_scrape)
                
                update_log("✍️ Crafting enhanced content outline...", 0.9)
                enhanced_outline = analyzer.generate_enhanced_outline(serp_data, scraped_data)
                
                update_log("🎉 Analysis completed successfully! Preparing results...", 1.0)
                time.sleep(0.5)  # Add small delay for visual effect
                
                st.markdown("<p class='big-font'>Keyword Analysis Result:</p>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div class='medium-font'>
                        <p><strong>Primary keyword:</strong><br>{primary_keyword}</p>
                        <p><strong>Secondary keywords:</strong><br>{', '.join(secondary_keywords)}</p>
                    </div>
                """, unsafe_allow_html=True)

               # Replace with this new code
                if enhanced_outline:
                    display_enhanced_outline(enhanced_outline)
                else:
                    st.error("Failed to generate enhanced outline.")
                
                st.success("Analysis completed successfully!")
                
            except Exception as e:
                update_log(f"❌ Error encountered: {str(e)}", 1.0)
                st.error(f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    main() 
