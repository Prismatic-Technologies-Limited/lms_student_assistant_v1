# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from fetch_student_data import fetch_student_profile
# from langchain_community.agent_toolkits import JsonToolkit, create_json_agent
# from langchain_community.tools.json.tool import JsonSpec
# from langchain_groq import ChatGroq
# from langchain.schema import HumanMessage
# from dotenv import load_dotenv
# import os
# import json

# load_dotenv()

# # Initialize FastAPI
# app = FastAPI()

# # Request schema
# class QuestionRequest(BaseModel):
#     student_id: str
#     question: str

# # Groq setup
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # set this in your environment
# llm = ChatGroq(
#     temperature=0.7,
#     model_name="llama-3.3-70b-versatile",
#     groq_api_key=GROQ_API_KEY
# )

# # Enhanced LMS Assistant Prompt
# LMS_ASSISTANT_PROMPT = """
# You are a helpful LMS Student Assistant. Answer student questions using their academic data.

# INSTRUCTIONS:
# 1. Use json_spec_list_keys to see what data categories are available
# 2. Use json_spec_get_value to get specific information from the student's data
# 3. Provide helpful, accurate answers based only on the available data
# 4. Be friendly and supportive in your responses
# 5. Keep reply shorter as possible 
# 6. Keep conversition like human conversation

# Important data categories you may find:
# - profile: Basic student information (name, email, course details)
# - lms: Academic data (assignments, quizzes, lecture_notes)
# - fee_invoices: Payment information
# - announcements: School announcements
# - news: School news
# - help_support: Support tickets

# Be conversational and helpful while staying focused on academic assistance."""

# def extract_summary_from_data(student_data):
#     """Extract key information for context"""
#     try:
#         summary = {}
        
#         # Basic profile info
#         if 'profile' in student_data:
#             profile = student_data['profile']
#             summary['name'] = f"{profile.get('first_name', '')} {profile.get('last_name', '')}"
#             summary['course'] = profile.get('course_name', 'N/A')
#             summary['batch'] = profile.get('batch_name', 'N/A')
        
#         # Academic summary
#         if 'lms' in student_data:
#             lms = student_data['lms']
            
#             # Assignment summary
#             if 'assignments' in lms:
#                 total_assignments = lms['assignments'].get('count', 0)
#                 completed_assignments = sum(1 for a in lms['assignments'].get('data', []) 
#                                          if a.get('obtain_marks') is not None)
#                 summary['assignments'] = f"{completed_assignments}/{total_assignments} completed"
            
#             # Quiz summary
#             if 'quizzes' in lms:
#                 total_quizzes = lms['quizzes'].get('count', 0)
#                 completed_quizzes = sum(1 for q in lms['quizzes'].get('data', []) 
#                                      if q.get('obtained_marks') is not None)
#                 quiz_scores = [int(q['obtained_marks']) for q in lms['quizzes'].get('data', []) 
#                              if q.get('obtained_marks') is not None and q['obtained_marks'].isdigit()]
#                 avg_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
#                 summary['quizzes'] = f"{completed_quizzes}/{total_quizzes} completed, avg: {avg_score:.1f}"
        
#         # Fee status
#         if 'fee_invoices' in student_data:
#             paid = student_data['fee_invoices']['paid_invoices'].get('total', 0)
#             unpaid = student_data['fee_invoices']['unpaid_invoices'].get('total', 0)
#             summary['fees'] = f"{paid} paid, {unpaid} unpaid"
        
#         return summary
#     except Exception:
#         return {}

# def generate_direct_answer(question, student_data, summary):
#     """Generate answer using direct LLM approach with context"""
    
#     # Create focused context based on question type
#     context_parts = [f"Student: {summary.get('name', 'N/A')}"]
#     context_parts.append(f"Course: {summary.get('course', 'N/A')}")
    
#     question_lower = question.lower()
    
#     # Add relevant context based on question
#     if any(word in question_lower for word in ['grade', 'score', 'mark', 'quiz', 'test']):
#         context_parts.append(f"Quiz Performance: {summary.get('quizzes', 'No quiz data')}")
#         context_parts.append(f"Assignments: {summary.get('assignments', 'No assignment data')}")
        
#         # Add specific quiz/assignment details
#         if 'lms' in student_data:
#             recent_quizzes = []
#             for quiz in student_data['lms'].get('quizzes', {}).get('data', [])[:3]:
#                 if quiz.get('obtained_marks'):
#                     recent_quizzes.append(f"{quiz['title']}: {quiz['obtained_marks']}/{quiz['marks']}")
#             if recent_quizzes:
#                 context_parts.append(f"Recent Quiz Scores: {', '.join(recent_quizzes)}")
    
#     elif any(word in question_lower for word in ['assignment', 'homework', 'submit']):
#         context_parts.append(f"Assignments: {summary.get('assignments', 'No assignment data')}")
        
#         # Add upcoming assignments
#         if 'lms' in student_data:
#             upcoming = []
#             for assignment in student_data['lms'].get('assignments', {}).get('data', [])[:3]:
#                 if assignment.get('obtain_marks') is None:  # Not submitted
#                     upcoming.append(f"{assignment['add_title']} (Due: {assignment['submission_date']})")
#             if upcoming:
#                 context_parts.append(f"Pending Assignments: {', '.join(upcoming)}")
    
#     elif any(word in question_lower for word in ['fee', 'payment', 'invoice', 'paid']):
#         context_parts.append(f"Fee Status: {summary.get('fees', 'No fee data')}")
    
#     elif any(word in question_lower for word in ['course', 'class', 'batch']):
#         context_parts.append(f"Batch: {summary.get('batch', 'N/A')}")
    
#     # Create prompt
#     context = " | ".join(context_parts)
    
#     prompt = f"""
# You are an LMS Student Assistant. Answer the student's question using the provided information.

# Context: {context}

# Student Question: {question}

# Provide a helpful, friendly response based on the available information. If specific data isn't available, say so politely and suggest how they might get that information.
#     """
    
#     try:
#         response = llm.invoke([HumanMessage(content=prompt)])
#         return response.content
#     except Exception as e:
#         return f"I'm having trouble processing your question about '{question}'. Please try rephrasing it or contact your instructor for assistance."

# @app.post("/ask")
# def ask_student_question(req: QuestionRequest):
#     try:
#         # Fetch student data
#         student_data = fetch_student_profile(req.student_id)
        
#         if "error" in student_data:
#             raise HTTPException(status_code=400, detail=student_data["error"])
        
#         # Handle simple greetings directly
#         simple_responses = {
#             "hello": "Hello! I'm your LMS Student Assistant. I can help you with questions about your courses, grades, assignments, fees, and academic progress. What would you like to know?",
#             "hi": "Hi there! I'm here to help you with your academic information. You can ask me about your quiz scores, assignment deadlines, course details, or fee status. How can I assist you?",
#             "hey": "Hey! I'm your academic assistant. Feel free to ask about your grades, upcoming assignments, course progress, or any other academic questions.",
#             "help": "I'm here to help! You can ask me about:\n\n📚 Your quiz scores and grades\n📝 Assignment deadlines and submissions\n💰 Fee payment status\n📋 Course information\n📢 Announcements and news\n\nWhat would you like to know?"
#         }
        
#         question_lower = req.question.lower().strip()
#         if question_lower in simple_responses:
#             return {"answer": simple_responses[question_lower]}
        
#         # Extract summary for better context
#         summary = extract_summary_from_data(student_data)
        
#         # Try JSON agent approach first
#         try:
#             json_spec = JsonSpec(dict_=student_data, max_value_length=3000)
#             toolkit = JsonToolkit(spec=json_spec)
            
#             agent = create_json_agent(
#                 llm=llm, 
#                 toolkit=toolkit, 
#                 verbose=False,
#                 max_iterations=2,
#                 handle_parsing_errors=True,
#                 prefix=LMS_ASSISTANT_PROMPT
#             )
            
#             result = agent.run(req.question)
#             if result and result.strip() and len(result) > 10:
#                 return {"answer": result}
#         except Exception:
#             pass  # Fall back to direct approach
        
#         # Fallback: Direct approach with focused context
#         direct_answer = generate_direct_answer(req.question, student_data, summary)
#         return {"answer": direct_answer}
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         return {
#             "answer": f"I'm experiencing some technical difficulties while processing your question: '{req.question}'. Please try asking in a different way, or contact your system administrator if the issue continues."
#         }

# @app.get("/health")
# def health_check():
#     return {"status": "healthy", "service": "LMS Student Assistant"}

# @app.get("/student/{student_id}/summary")
# def get_student_summary(student_id: str):
#     """Get a quick summary of student's academic status"""
#     try:
#         student_data = fetch_student_profile(student_id)
#         if "error" in student_data:
#             raise HTTPException(status_code=400, detail=student_data["error"])
        
#         summary = extract_summary_from_data(student_data)
        
#         return {
#             "student_id": student_id,
#             "summary": summary,
#             "data_available": True
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # Optional: Endpoint to test specific data queries
# @app.post("/query")
# def query_student_data(req: QuestionRequest):
#     """Direct query endpoint for testing specific data access"""
#     try:
#         student_data = fetch_student_profile(req.student_id)
#         if "error" in student_data:
#             raise HTTPException(status_code=400, detail=student_data["error"])
        
#         # Simple keyword-based data extraction
#         question_lower = req.question.lower()
        
#         if "quiz" in question_lower or "test" in question_lower:
#             quizzes = student_data.get('lms', {}).get('quizzes', {})
#             completed = [q for q in quizzes.get('data', []) if q.get('obtained_marks')]
#             return {
#                 "answer": f"You have completed {len(completed)} out of {quizzes.get('count', 0)} quizzes.",
#                 "data": completed[:5]  # Show recent 5
#             }
        
#         elif "assignment" in question_lower:
#             assignments = student_data.get('lms', {}).get('assignments', {})
#             pending = [a for a in assignments.get('data', []) if not a.get('obtain_marks')]
#             return {
#                 "answer": f"You have {len(pending)} pending assignments out of {assignments.get('count', 0)} total.",
#                 "data": pending[:5]  # Show recent 5
#             }
        
#         elif "fee" in question_lower or "payment" in question_lower:
#             fees = student_data.get('fee_invoices', {})
#             paid = fees.get('paid_invoices', {}).get('total', 0)
#             unpaid = fees.get('unpaid_invoices', {}).get('total', 0)
#             return {
#                 "answer": f"Fee Status: {paid} paid invoices, {unpaid} unpaid invoices.",
#                 "data": fees
#             }
        
#         else:
#             return {"answer": "Please ask about quizzes, assignments, or fees for specific data."}
            
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


from fastapi import FastAPI, Request
import requests
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq

# === CONFIG ===
GROQ_API_KEY = ""  # replace with your key
MODEL_NAME = "llama-3.3-70b-versatile"  

# === LLM Setup ===
llm = ChatGroq(
    temperature=0.7,
    model_name=MODEL_NAME,
    api_key=GROQ_API_KEY
)

# === Prompt Template ===
with open("prompt_template.txt", "r") as f:
    prompt_template = f.read()

prompt = PromptTemplate.from_template(prompt_template)

# === FastAPI App ===
app = FastAPI()

# === Formatter ===
def format_profile(json_data: dict) -> str:
    lines = []

    profile = json_data.get("profile", {})
    if profile:
        lines.append("🧑‍🎓 Basic Profile:")
        lines.extend([
            f"Name: {profile.get('first_name', '')} {profile.get('last_name', '')}",
            f"Email: {profile.get('email', 'N/A')}",
            f"Gender: {profile.get('gender', 'N/A')}",
            f"Date of Birth: {profile.get('date_of_birth', 'N/A')}",
            f"City: {profile.get('city', 'N/A')}",
            f"Course: {profile.get('course_name', 'N/A')}",
            f"Batch: {profile.get('batch_name', 'N/A')}",
            f"Branch: {profile.get('branch_name', 'N/A')}",
        ])

    assignments = json_data.get("lms", {}).get("assignments", {}).get("data", [])
    if assignments:
        lines.append("\n📚 Assignments:")
        for a in assignments:
            lines.append(f"- {a.get('add_title')} (Due: {a.get('submission_date')}, Marks: {a.get('total_marks')})")

    quizzes = json_data.get("lms", {}).get("quizzes", {}).get("data", [])
    if quizzes:
        lines.append("\n📝 Quizzes:")
        for q in quizzes:
            lines.append(f"- {q.get('title')} (Marks: {q.get('marks')}, Due: {q.get('lastDate')})")

    notes = json_data.get("lms", {}).get("lecture_notes", {}).get("data", [])
    if notes:
        lines.append("\n📄 Lecture Notes:")
        for n in notes:
            lines.append(f"- {n.get('lec_title')} (Date: {n.get('lec_date')})")

    videos = json_data.get("lms", {}).get("video_tutorials", {}).get("data", [])
    if videos:
        lines.append("\n🎥 Video Tutorials:")
        for v in videos:
            lines.append(f"- {v.get('video_title')} (Date: {v.get('lec_date')})")

    paid_fees = json_data.get("fee_invoices", {}).get("paid_invoices", {}).get("paid", [])
    if paid_fees:
        lines.append("\n💰 Fee Status:")
        for f in paid_fees:
            lines.append(f"- Paid: {f.get('fee_amount')} on {f.get('receipt_date')} (Receipt: {f.get('receipt_id')})")

    return "\n".join(lines)

# === Fetch Profile & Format ===
def fetch_student_profile(student_id: str, base_url: str) -> str:
    try:
        url = f"{base_url.rstrip('/')}/{student_id}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return format_profile(data)
    except Exception as e:
        return f"Error fetching student profile: {e}"

# === LangChain Chain Builder ===
def build_chain(student_profile: str):
    chain = (
        {
            "student_profile": lambda x: student_profile,
            "input": RunnablePassthrough()
        }
        | prompt
        | llm
    )
    return chain

# === FastAPI Endpoint ===
@app.post("/ask")
async def chat_with_student(request: Request):
    body = await request.json()
    user_question = body.get("question")
    api_base_url = body.get("api_base_url")
    student_id = body.get("student_id")

    # Validate inputs
    if not user_question:
        return {"error": "Missing 'message' in request body"}
    if not api_base_url:
        return {"error": "Missing 'api_base_url' in request body"}
    if not student_id:
        return {"error": "Missing 'student_id' in request body"}

    # Fetch profile
    profile_text = fetch_student_profile(student_id, api_base_url)

    # Build LLM chain
    chain = build_chain(profile_text)
    response = chain.invoke(user_question)

    return {
        "student_id": student_id,
        "reply": response.content
    }
