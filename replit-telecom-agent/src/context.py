# telecom_agent/src/context.py
from collections import deque

# A simple in-memory context manager for demonstration purposes.
# In a production system, this would be backed by a persistent store like Redis or a database.
conversation_contexts = {}

MAX_HISTORY_LEN = 10 # Max number of user/agent turns to remember

def get_context(session_id: str) -> list:
    """
    Retrieves the conversation history for a given session.
    """
    if session_id not in conversation_contexts:
        # Use a deque for efficient appends and pops from both ends
        conversation_contexts[session_id] = deque(maxlen=MAX_HISTORY_LEN)
    return list(conversation_contexts[session_id]) # Return a copy

def add_to_context(session_id: str, user_query: str, agent_response: str):
    """
    Adds a new user query and agent response to the conversation history.
    """
    if session_id not in conversation_contexts:
        conversation_contexts[session_id] = deque(maxlen=MAX_HISTORY_LEN)
    
    conversation_contexts[session_id].append(f"User: {user_query}")
    conversation_contexts[session_id].append(f"Agent: {agent_response}")

def clear_context(session_id: str):
    """
    Clears the history for a session.
    """
    if session_id in conversation_contexts:
        conversation_contexts[session_id].clear()
