# telecom_agent/src/speech_enhancer.py
import re

def filter_for_tts(text: str) -> str:
    """
    Cleans text to make it suitable for Text-to-Speech (TTS) processing,
    before sending it to the MCP server.
    - Removes markdown symbols
    - Converts common technical abbreviations
    - Removes other non-pronounceable characters
    """
    # Remove markdown formatting
    text = re.sub(r'[\*_`#]', '', text)
    
    # Convert technical abbreviations (can be expanded)
    # Using word boundaries (\b) to avoid replacing parts of words
    abbreviations = {
        r'\bWi-Fi\b': 'wifi',
        r'\bVPN\b': 'V P N',
        r'\bURL\b': 'U R L',
        r'\bIP\b': 'I P',
        r'\bSSID\b': 'S S I D',
    }
    for abb, pron in abbreviations.items():
        text = re.sub(abb, pron, text, flags=re.IGNORECASE)
        
    # Remove any remaining non-alphanumeric characters that aren't spaces or punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    
    # Ensure smooth flow by removing extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
