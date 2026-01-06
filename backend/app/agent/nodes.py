import re
import asyncio
import ollama
from typing import List

LLM_MODEL = "llama3.1:8b"

# Detect memory/summarization questions - EXPANDED
MEMORY_PATTERN = re.compile(
    r"(what\s+were\s+we\s+(talking|discussing)|"
    r"what\s+were\s+we\s+discussing|"
    r"what\s+did\s+we\s+discuss|"
    r"summarize|summary|"
    r"what\s+we\s+discussed|"
    r"explain\s+what\s+we\s+discussed|"
    r"tell\s+me\s+what\s+we\s+talked\s+about|"
    r"recap|"
    r"what\s+have\s+we\s+covered|"
    r"what\s+topics\s+did\s+we\s+cover|"
    r"review\s+our\s+conversation|"
    r"go\s+over\s+what\s+we\s+discussed)",
    re.IGNORECASE
)


async def summarize_conversation_llm(all_messages: List):
    """
    Summarize the conversation in paragraph format.
    """
    system_prompt = """
You are a conversation summarizer for an Internal Company Policy Assistant.

Create a HIGH-LEVEL summary of what topics were discussed in 2-3 concise sentences.
DO NOT list every detail - just mention what was asked about and the key takeaway.

Write in paragraph format, not bullet points.
Be brief and natural.

Example: "We discussed the SI-12 policy regarding employee conduct and professional behavior standards. I also explained media downgrading as unauthorized modification of company devices."
"""

    # Build conversation pairs (user question + assistant answer)
    conversation_pairs = []
    
    for i in range(len(all_messages)):
        # Handle tuple format: (role, content) or object format
        if isinstance(all_messages[i], tuple):
            role, content = all_messages[i]
        else:
            role = getattr(all_messages[i], 'type', getattr(all_messages[i], 'role', None))
            content = getattr(all_messages[i], 'content', str(all_messages[i]))
        
        if role in ["user", "human"]:
            user_content = content.strip()
            
            # Skip greetings only
            if user_content.lower() in {"hi", "hello", "hey"}:
                continue
            
            # Skip questions about "how are you" or similar chitchat
            if any(phrase in user_content.lower() for phrase in ["how are you", "how's it going", "what's up"]):
                continue
            
            # Find corresponding assistant response
            assistant_content = ""
            if i + 1 < len(all_messages):
                next_msg = all_messages[i + 1]
                if isinstance(next_msg, tuple):
                    next_role, next_content = next_msg
                else:
                    next_role = getattr(next_msg, 'type', getattr(next_msg, 'role', None))
                    next_content = getattr(next_msg, 'content', str(next_msg))
                
                if next_role in ["assistant", "ai"]:
                    assistant_content = next_content
            
            if assistant_content:
                # Truncate long answers
                truncated_answer = assistant_content[:200] + "..." if len(assistant_content) > 200 else assistant_content
                conversation_pairs.append(f"Q: {user_content}\nA: {truncated_answer}")
    
    if not conversation_pairs:
        return "No substantive discussion to summarize."

    conversation_text = "\n\n".join(conversation_pairs)

    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Summarize this conversation in 2-3 sentences:\n\n{conversation_text}"}
            ],
            options={"temperature": 0.3, "num_predict": 200}
        )

        summary = response["message"]["content"].strip()
        return summary if summary else "No content to summarize."
    
    except Exception as e:
        return f"Error generating summary: {str(e)}"


def ask_node(state: dict):
    """
    Handles user questions with paragraph-based responses.
    """
    import asyncio

    messages = state.get("messages", [])
    user_input_msg = messages[-1]
    
    # Extract content from message
    if isinstance(user_input_msg, tuple):
        user_input = user_input_msg[1].strip()
    else:
        user_input = getattr(user_input_msg, 'content', str(user_input_msg)).strip()
    
    context = state.get("context", "").strip()

    # ---- GREETING HANDLER ----
    if user_input.lower() in {"hi", "hello", "hey"}:
        return {"messages": [("assistant", "How can I help you today?")]}

    # ---- MEMORY / SUMMARIZATION ----
    if MEMORY_PATTERN.search(user_input):
        all_messages = messages[:-1]  # Exclude current summarization request

        if not all_messages or len(all_messages) < 2:
            return {"messages": [("assistant", "No prior discussion exists in this session.")]}

        # Call async LLM summarization
        summary = asyncio.run(summarize_conversation_llm(all_messages))
        
        return {"messages": [("assistant", summary)]}

    # ---- SYSTEM PROMPT FOR NORMAL QUESTIONS (PARAGRAPH FORMAT) ----
    system_prompt = (
        "You are an Internal Company Policy Assistant.\n"
        "Answer ONLY using the provided context.\n\n"

        "OUTPUT RULES:\n"
        "- Write your answer in natural paragraph format\n"
        "- Use 2-4 sentences\n"
        "- Be clear and concise\n"
        "- No bullet points, no numbered lists\n"
        "- Write in a professional but conversational tone\n\n"

        "If the answer is not present in the context, reply exactly:\n"
        "'I am a chatbot for this specific task only. I do not have information on that topic.'\n\n"

        "--- CONTEXT ---\n"
        f"{context}"
    )

    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            options={"temperature": 0.0, "num_predict": 300}
        )

        answer = response["message"]["content"].strip()
        
        if not answer:
            answer = "No answer could be generated from the context."

        return {"messages": [("assistant", answer)]}

    except Exception as e:
        return {"messages": [("assistant", f"Error: Internal AI connection failed. {str(e)}")]}


# ---- PLACEHOLDER NODES ----
def checklist_node(state: dict):
    return {"messages": [("assistant", "Checklist active.")]}


def draft_node(state: dict):
    return {"messages": [("assistant", "Drafting active.")]}