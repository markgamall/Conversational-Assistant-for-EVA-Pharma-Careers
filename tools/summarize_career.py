import google.generativeai as genai
import os

def summarize_career(job_info: str, query: str):
    """Summarize career path and growth opportunities for a job using Gemini API."""
    
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""You are a career advisor. Based on the job information provided, 
summarize the career path and growth opportunities. Address the user's specific query: {query}

Job Information:
{job_info}

Provide information about:
- Career progression paths
- Skills development opportunities
- Potential next roles
- Industry growth prospects
- Long-term career outlook

Keep the response focused and actionable."""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error summarizing career information: {str(e)}"