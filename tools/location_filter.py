import google.generativeai as genai
import os

def filter_by_location(jobs_info: str, location: str):
    """Filter jobs by specified location using Gemini API."""
    
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""Filter and analyze these jobs by location. Return only jobs that are in or near: {location}

Jobs Information:
{jobs_info}

For each matching job, provide:
- Job Title
- Exact Location
- Brief job summary
- Department
- Job Type (Full-time, Part-time, etc.)

If no exact matches, suggest similar locations or nearby areas.
Format the response clearly with job titles as headers."""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0
            )
        )
        return response.text
    except Exception as e:
        return f"Error filtering jobs by location: {str(e)}"