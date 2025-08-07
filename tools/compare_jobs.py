import google.generativeai as genai
import os

def compare_jobs(job1_info: str, job2_info: str, job1_title: str = None, job2_title: str = None):
    """Compare two job roles using Gemini API with enhanced prompting."""
    
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    title1 = job1_title or "Job 1"
    title2 = job2_title or "Job 2"
    
    prompt = f"""You are a professional career advisor specializing in job comparisons. I need you to provide a comprehensive comparison between two specific roles: "{title1}" and "{title2}".

Based on the following job information, create a detailed, balanced comparison:

**{title1} Information:**
{job1_info}

**{title2} Information:**
{job2_info}

Please provide a structured comparison with the following sections:

## Job Comparison: {title1} vs {title2}

### **{title1}**
- **Primary Focus:** [Main job focus and purpose]
- **Key Responsibilities:** [Top 3-4 responsibilities]
- **Required Skills:** [Essential technical and soft skills]
- **Experience Level:** [Junior/Mid/Senior requirements]
- **Work Environment:** [Remote/hybrid/onsite, team structure]

### **{title2}**
- **Primary Focus:** [Main job focus and purpose]
- **Key Responsibilities:** [Top 3-4 responsibilities]
- **Required Skills:** [Essential technical and soft skills]
- **Experience Level:** [Junior/Mid/Senior requirements]
- **Work Environment:** [Remote/hybrid/onsite, team structure]

### **Key Differences & Similarities**
- **Creative vs Technical Focus:** [How much creative vs technical work]
- **Skill Requirements:** [What skills overlap and what's unique]
- **Career Growth:** [Typical progression paths for each]
- **Day-to-day Work:** [What a typical day looks like in each role]
- **Industry Demand:** [Job market outlook for each]

### **Which Role Might Be Better For You?**
- **Choose {title1} if:** [Specific scenarios and personality fits]
- **Choose {title2} if:** [Specific scenarios and personality fits]

### **Recommendations**
[Provide actionable advice for someone deciding between these roles]

Important: Make sure to address BOTH roles equally and provide specific, practical insights that would help someone make an informed career decision."""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error comparing jobs: {str(e)}. Please try again or contact support if the issue persists."