from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from typing import List, Dict, Any, TypedDict, Annotated
from tools.rag_retriever import JobRetriever
import os
from dotenv import load_dotenv
import operator
from datetime import datetime
import json
from colorama import Fore, Back, Style, init
import re
from tools.compare_jobs import compare_jobs
from tools.summarize_career import summarize_career
from tools.location_filter import filter_by_location

init(autoreset=True)

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[List[Dict], operator.add]
    rag_context: str 

class FlowTracer:
    """Enhanced visual tracer for LangGraph execution flow"""
    def __init__(self):
        self.step_count = 0
        self.indent_level = 0
        self.start_time = datetime.now()
        
    def log_step(self, step_type: str, description: str, data: Any = None):
        """Log a step with visual formatting"""
        self.step_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        indent = "  " * self.indent_level
        
        colors = {
            "USER": Fore.CYAN,
            "AGENT": Fore.GREEN, 
            "TOOL": Fore.YELLOW,
            "DECISION": Fore.MAGENTA,
            "ERROR": Fore.RED,
            "INFO": Fore.BLUE,
            "RAG": Fore.LIGHTMAGENTA_EX
        }
        
        color = colors.get(step_type, Fore.WHITE)
        
        print(f"\n{color}{'='*60}")
        print(f"{color}[{timestamp}] STEP {self.step_count}: {step_type}")
        print(f"{color}{'='*60}")
        print(f"{color}{indent}📝 {description}")
        
        if data:
            print(f"{color}{indent}📊 Data:")
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"{color}{indent}   {key}: {value}")
            elif isinstance(data, str):
                preview = data[:200] + "..." if len(data) > 200 else data
                print(f"{color}{indent}   {preview}")
            else:
                print(f"{color}{indent}   {str(data)}")
        
        print(f"{color}{'='*60}{Style.RESET_ALL}")
    
    def log_flow_transition(self, from_node: str, to_node: str, condition: str = None):
        print(f"\n{Fore.BLUE}🔄 FLOW: {from_node} → {to_node}")
        if condition:
            print(f"{Fore.BLUE}   Condition: {condition}")
        print(f"{Fore.BLUE}{'─'*40}")
    
    def indent(self):
        self.indent_level += 1
    
    def dedent(self):
        self.indent_level = max(0, self.indent_level - 1)
    
    def log_summary(self, messages: List[Dict]):
        """Log a summary of the conversation"""
        print(f"\n{Back.BLUE}{Fore.WHITE}📋 CONVERSATION SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'='*50}")
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])
            if role == "user":
                print(f"{Fore.CYAN}👤 User: {content}")
            elif role == "assistant":
                if tool_calls:
                    print(f"{Fore.GREEN}🤖 Assistant: [Tool calls made]")
                    for tc in tool_calls:
                        print(f"{Fore.GREEN}   🔧 {tc.get('name', 'unknown')}({tc.get('args', {})})")
                else:
                    preview = content[:100] + "..." if len(content) > 100 else content
                    print(f"{Fore.GREEN}🤖 Assistant: {preview}")
            elif role == "tool":
                preview = content[:100] + "..." if len(content) > 100 else content
                print(f"{Fore.YELLOW}🔧 Tool Result: {preview}")
        print(f"{Fore.BLUE}{'='*50}{Style.RESET_ALL}")

tracer = FlowTracer()



retriever = JobRetriever()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)

@tool
def retrieve_jobs(query: str) -> str:
    """Retrieve relevant job information from the database based on a specific query. Best for targeted searches about specific roles, skills, or departments."""
    tracer.log_step("TOOL", "Retrieving jobs from database", {"query": query})
    tracer.indent()
    
    docs = retriever.retrieve(query, k=5)
    result = "\n\n".join([doc.page_content for doc in docs])
    
    tracer.log_step("INFO", f"Retrieved {len(docs)} documents, {len(result)} characters total")
    tracer.dedent()
    return result

@tool
def list_all_jobs() -> str:
    """Retrieve a comprehensive list of all available job positions at EVA Pharma. Use this when users want to see all open positions, available jobs, or get a broad overview of opportunities."""
    tracer.log_step("TOOL", "Listing all available jobs")
    tracer.indent()
    
    broad_queries = [
        "job position role",
        "department location",
        "engineer manager analyst",
        "coordinator specialist assistant",
        "pharma medical sales",
        "all available jobs",
        "full-time part-time",
        "remote onsite hybrid"
    ]
    
    all_docs = []
    seen_job_ids = set()
    
    for query in broad_queries:
        docs = retriever.retrieve(query, k=50)  
        for doc in docs:
            job_id = doc.metadata.get("job_id")
            if job_id and job_id not in seen_job_ids:
                all_docs.append(doc)
                seen_job_ids.add(job_id)
    
    all_docs.sort(key=lambda x: x.metadata.get("job_id", ""))
    
    result = "\n\n".join([doc.page_content for doc in all_docs])
    
    tracer.log_step("INFO", f"Retrieved {len(all_docs)} unique jobs, {len(result)} characters total")
    tracer.dedent()
    return result

@tool
def compare_jobs_tool(job_titles: str) -> str:
    """Compare two job roles. Input should be two job titles separated by 'vs' or 'and'."""
    tracer.log_step("TOOL", "Comparing job roles", {"job_titles": job_titles})
    tracer.indent()
    
    job_titles_clean = job_titles.lower().strip()
    
    jobs = []
    if ' vs ' in job_titles_clean:
        jobs = [job.strip() for job in job_titles_clean.split(' vs ')]
    elif ' versus ' in job_titles_clean:
        jobs = [job.strip() for job in job_titles_clean.split(' versus ')]
    elif ' and ' in job_titles_clean:
        jobs = [job.strip() for job in job_titles_clean.split(' and ')]
    elif ',' in job_titles_clean:
        jobs = [job.strip() for job in job_titles_clean.split(',')]
    else:
        words = job_titles_clean.split()
        if len(words) >= 4: 
            mid_point = len(words) // 2
            jobs = [' '.join(words[:mid_point]), ' '.join(words[mid_point:])]
        else:
            tracer.log_step("ERROR", "Could not identify two distinct job titles")
            tracer.dedent()
            return "Please specify two jobs to compare using format like 'UX Designer vs Motion Graphics Designer' or 'UX Designer and Motion Graphics Designer'"
    
    if len(jobs) < 2:
        tracer.log_step("ERROR", "Less than 2 jobs identified")
        tracer.dedent()
        return "Please specify exactly two jobs to compare. Example: 'UX Designer vs Motion Graphics Designer'"
    
    job1_title = jobs[0].strip()
    job2_title = jobs[1].strip()
    
    tracer.log_step("INFO", f"Comparing: '{job1_title}' vs '{job2_title}'")
    
    def get_comprehensive_job_info(job_title: str) -> str:
        """Get comprehensive information about a specific job."""
        
        queries = [
            job_title, 
            f"{job_title} responsibilities duties",  
            f"{job_title} requirements qualifications skills",  
            f"{job_title} job description role",  
            f"{job_title} experience level career" 
        ]
        
        all_docs = []
        seen_content = set()
        
        for query in queries:
            docs = retriever.retrieve(query, k=3)
            for doc in docs:
                content_hash = hash(doc.page_content[:200]) 
                if content_hash not in seen_content:
                    all_docs.append(doc)
                    seen_content.add(content_hash)
        
        job_specific_docs = []
        general_docs = []
        
        for doc in all_docs:
            if job_title.lower() in doc.page_content.lower():
                job_specific_docs.append(doc)
            else:
                general_docs.append(doc)
        
        prioritized_docs = job_specific_docs + general_docs[:3] 
        
        return "\n\n".join([doc.page_content for doc in prioritized_docs[:5]]) 
    

    tracer.log_step("INFO", f"Retrieving comprehensive info for '{job1_title}'")
    job1_info = get_comprehensive_job_info(job1_title)
    
    tracer.log_step("INFO", f"Retrieving comprehensive info for '{job2_title}'")  
    job2_info = get_comprehensive_job_info(job2_title)
    

    if not job1_info.strip():
        tracer.log_step("ERROR", f"No information found for '{job1_title}'")
        tracer.dedent()
        return f"I couldn't find detailed information about '{job1_title}'. Please check the job title spelling or try a more general term."
    
    if not job2_info.strip():
        tracer.log_step("ERROR", f"No information found for '{job2_title}'")
        tracer.dedent()
        return f"I couldn't find detailed information about '{job2_title}'. Please check the job title spelling or try a more general term."
    

    tracer.log_step("INFO", "Generating detailed comparison")
    result = compare_jobs(job1_info, job2_info, job1_title, job2_title)
    
    tracer.log_step("INFO", f"Comparison completed, {len(result)} characters")
    tracer.dedent()
    return result

@tool
def summarize_career_tool(query: str) -> str:
    """Summarize career path and growth opportunities for a job."""
    tracer.log_step("TOOL", "Summarizing career path", {"query": query})
    tracer.indent()
    
    docs = retriever.retrieve(query, k=5)
    job_info = "\n\n".join([doc.page_content for doc in docs])
    
    result = summarize_career(job_info, query)
    tracer.log_step("INFO", f"Career summary completed, {len(result)} characters")
    tracer.dedent()
    return result

@tool
def location_filter_tool(location: str) -> str:
    """Filter jobs by specific location."""
    tracer.log_step("TOOL", "Filtering jobs by location", {"location": location})
    tracer.indent()
    
    docs = retriever.retrieve(f"location {location}", k=10)
    jobs_info = "\n\n".join([doc.page_content for doc in docs])
    
    result = filter_by_location(jobs_info, location)
    tracer.log_step("INFO", f"Location filtering completed, {len(result)} characters")
    tracer.dedent()
    return result


tools = [retrieve_jobs, list_all_jobs, compare_jobs_tool, summarize_career_tool, location_filter_tool]


llm_with_tools = llm.bind_tools(tools)

def retrieve_job_context(query: str) -> str:
    """Retrieve job context for the query."""
    tracer.log_step("RAG", "Retrieving job context", {"query": query})
    tracer.indent()
    
    try:
        docs = retriever.retrieve(query, k=5)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        tracer.log_step("INFO", f"Retrieved {len(docs)} documents for context", {
            "context_length": len(context),
            "preview": context[:200] + "..." if len(context) > 200 else context
        })
        
        tracer.dedent()
        return context
        
    except Exception as e:
        tracer.log_step("ERROR", f"Failed to retrieve context: {str(e)}")
        tracer.dedent()
        return ""

def should_continue(state: AgentState) -> str:
    """Determine if we should continue to tools, retrieve context, or end."""
    tracer.log_step("DECISION", "Evaluating next step")
    tracer.indent()
    
    messages = state["messages"]
    last_message = messages[-1]
    
    message_role = None
    has_tool_calls = False
    
    if isinstance(last_message, dict):
        message_role = last_message.get("role")
        has_tool_calls = bool(last_message.get("tool_calls"))
    elif hasattr(last_message, 'role'):
        message_role = getattr(last_message, 'role', None)
    
    if hasattr(last_message, 'tool_calls'):
        has_tool_calls = bool(last_message.tool_calls)
    
    tracer.log_step("INFO", "Message analysis", {
        "role": message_role,
        "has_tool_calls": has_tool_calls,
        "message_type": type(last_message).__name__
    })
    
    if message_role == "assistant" and has_tool_calls:
        tracer.log_step("DECISION", "Assistant message with tool calls → Going to tools")
        tracer.log_flow_transition("agent", "tools", "tool_calls found")
        tracer.dedent()
        return "tools"
    
    if message_role == "tool":
        tracer.log_step("DECISION", "Tool message found → Going back to agent for response refinement")
        tracer.log_flow_transition("tools", "agent", "tool response needs refinement")
        tracer.dedent()
        return "agent" 
    
    if message_role == "assistant" and not has_tool_calls:
        tracer.log_step("DECISION", "Final assistant response → Ending conversation")
        tracer.log_flow_transition("agent", "END", "final response")
        tracer.dedent()
        return END
    
    tracer.log_step("DECISION", "Continuing conversation flow")
    tracer.dedent()
    return "agent"

def rag_retrieval_node(state: AgentState) -> Dict[str, Any]:
    """Node to retrieve job context using RAG."""
    tracer.log_step("RAG", "RAG Retrieval Node")
    tracer.indent()
    
    messages = state["messages"]
    user_query = ""
    
    for msg in messages:
        if msg.get("role") == "user":
            user_query = msg.get("content", "")
            break
    
    context = retrieve_job_context(user_query)
    
    tracer.log_step("INFO", "RAG context retrieved", {
        "context_length": len(context),
        "query": user_query
    })
    
    tracer.dedent()
    return {"rag_context": context}

def call_model(state: AgentState) -> Dict[str, List]:
    """Call the model with the current state - enhanced to handle tool responses better."""
    tracer.log_step("AGENT", "Calling language model")
    tracer.indent()
    
    messages = state["messages"]
    rag_context = state.get("rag_context", "")
    
    has_recent_tool_results = any(
        msg.get("role") == "tool" for msg in messages[-3:] 
        if isinstance(msg, dict)
    )
    
    tracer.log_step("INFO", f"Processing {len(messages)} messages", {
        "has_rag_context": bool(rag_context),
        "context_length": len(rag_context) if rag_context else 0,
        "has_recent_tool_results": has_recent_tool_results
    })
    
    system_content = """You are EVA Pharma's AI Career Assistant, a professional virtual agent designed to help users explore job opportunities, understand application requirements, and navigate career paths within the company.

Tools Available:
- retrieve_jobs: Fetch relevant job listings for specific queries about roles, skills, requirements, responsibilities, type, workplace or departments
- list_all_jobs: Get a comprehensive overview of ALL available positions at EVA Pharma
- compare_jobs_tool: Compare responsibilities and qualifications of two job roles
- summarize_career_tool: Provide information on typical career growth paths
- location_filter_tool: Show jobs available in a specific city or region

STRICT INSTRUCTION:
Under no circumstances should you mention or reference any internal tools, tool names (e.g., summarize_career_tool, compare_jobs_tool, etc.), or describe how the system works behind the scenes. All responses must appear as if written by a knowledgeable and helpful human career assistant. Focus only on providing professional, polished guidance without exposing internal mechanics.

HANDLING VAGUE QUERIES:
When user queries are vague or lack specific details, DO NOT make assumptions.

RESPONSE BEHAVIOR:
- Execute requested actions immediately without asking for permission or saying you need a moment
- Do not use phrases like "let me", "give me a moment" or "please wait"
- Directly provide the information or execute the task requested
- No acknowledgments about what you're about to do - just do it

CRITICAL INSTRUCTION FOR TOOL RESULTS:
When you receive tool results, you MUST:
1. Analyze and interpret the raw data
2. Structure it in a user-friendly format
3. Add relevant context and explanations
4. Provide actionable insights
5. NEVER just repeat the raw tool output

If tool results contain job listings:
- Organize them by categories or relevance
- Highlight key requirements and qualifications
- Mention application processes or next steps
- Point out particularly relevant matches

If tool results contain comparisons:
- Summarize key differences clearly
- Provide recommendations based on user needs
- Explain which role might be better for different career goals

RESPONSE FORMATTING:
- Use clear headings and bullet points
- Keep paragraphs short and scannable
- Always end with helpful next steps or questions
- Maintain professional but friendly tone

PRIMARY OBJECTIVE:
Transform raw job data into meaningful, actionable career guidance that helps users make informed decisions about their career at EVA Pharma. For vague queries, focus on getting specific details before providing job information."""

    if rag_context:
        system_content += f"""

RELEVANT JOB INFORMATION:
{rag_context}

Use this information to provide accurate, specific answers about available positions, requirements, and opportunities."""
    
    if has_recent_tool_results:
        system_content += """

IMPORTANT: You have just received tool results. Your task is to process this raw data and present it as a helpful, structured response to the user. Do NOT simply repeat the tool output - interpret, organize, and enhance it for the user."""

    system_message = {"role": "system", "content": system_content}
    
    formatted_messages = [system_message]
    for msg in messages:
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                formatted_messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                if msg.get("tool_calls"):
                    ai_msg = AIMessage(content=msg.get("content", ""))
                    ai_msg.tool_calls = msg["tool_calls"]
                    formatted_messages.append(ai_msg)
                else:
                    formatted_messages.append(AIMessage(content=msg["content"]))
            elif msg.get("role") == "tool":
                formatted_messages.append(ToolMessage(
                    content=msg["content"],
                    tool_call_id=msg.get("tool_call_id", "")
                ))
    
    try:
        response = llm_with_tools.invoke(formatted_messages)
        
        tracer.log_step("INFO", "LLM response received", {
            "content_length": len(response.content) if response.content else 0,
            "has_tool_calls": bool(hasattr(response, 'tool_calls') and response.tool_calls),
            "processing_tool_results": has_recent_tool_results
        })
        
    except Exception as e:
        tracer.log_step("ERROR", f"LLM invocation failed: {str(e)}")
        tracer.dedent()
        raise
    
    response_dict = {
        "role": "assistant",
        "content": response.content
    }
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        response_dict["tool_calls"] = response.tool_calls
    
    tracer.dedent()
    return {"messages": [response_dict]}

def handle_tools(state: AgentState) -> Dict[str, List]:
    """Handle tool execution and return tool messages."""
    tracer.log_step("TOOL", "Executing tools")
    tracer.indent()
    
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_node = ToolNode(tools)
    
    formatted_messages = []
    for msg in messages:
        if isinstance(msg, dict):
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                ai_msg = AIMessage(content=msg.get("content", ""))
                ai_msg.tool_calls = msg["tool_calls"]
                formatted_messages.append(ai_msg)
    
    tracer.log_step("INFO", f"Executing {len(formatted_messages)} tool messages")
    
    try:
        tool_result = tool_node.invoke({"messages": formatted_messages})
        
        tracer.log_step("INFO", f"Tools executed successfully, {len(tool_result['messages'])} results")
        
    except Exception as e:
        tracer.log_step("ERROR", f"Tool execution failed: {str(e)}")
        tracer.dedent()
        raise
    
    tool_messages = []
    for i, msg in enumerate(tool_result["messages"]):
        if isinstance(msg, ToolMessage):
            tool_messages.append({
                "role": "tool",
                "content": msg.content,
                "tool_call_id": msg.tool_call_id
            })
            tracer.log_step("INFO", f"Tool result {i+1}", {
                "content_length": len(msg.content),
                "tool_call_id": msg.tool_call_id
            })
    
    tracer.dedent()
    return {"messages": tool_messages}

def get_agent():
    """Create and return the agent workflow with improved flow logic."""
    tracer.log_step("INFO", "Creating enhanced agent workflow with improved flow")
    
    checkpointer = InMemorySaver()
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", handle_tools)
    workflow.add_node("rag_retrieval", rag_retrieval_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "rag_retrieval": "rag_retrieval", 
            "agent": "agent",  
            END: END
        }
    )
    
    workflow.add_edge("tools", "agent")
    
    workflow.add_edge("rag_retrieval", "agent")
    
    return workflow.compile(checkpointer=checkpointer)

def run_agent_with_tracing(query: str):
    """Run the agent with enhanced tracing"""
    tracer.log_step("USER", "Starting new conversation", {"query": query})
    
    agent = get_agent()
    
    config = {"configurable": {"thread_id": "default_session"}}
    
    initial_state = {
        "messages": [{"role": "user", "content": query}],
        "rag_context": ""
    }
    
    result = agent.invoke(initial_state, config)
    
    tracer.log_summary(result["messages"])
    
    return result

if __name__ == "__main__":
    
    print(f"\n{Back.CYAN}{Fore.WHITE} Welcome to the EVA Pharma Career Assistant{Style.RESET_ALL}")
