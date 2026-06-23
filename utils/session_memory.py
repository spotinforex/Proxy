import logging

logging.basicConfig(level=logging.INFO)

memory = {}

def log_memory(phone: str, message: str, response: str = None):
    """
    Stores the user's message in memory for the given phone number.
    """
    try:
        global memory
        if phone not in memory:
            memory[phone] = []
        memory[phone].append(f"User: {message}")
        if response:
            memory[phone].append(f"Response: {response}")
    except Exception as e:
        logging.error(f"Error storing message for {phone}: {e}")
    
def get_memory(phone: str) -> list:
    """
    Retrieves the stored messages for the given phone number.
    """
    try:
        global memory
        return memory.get(phone, [])
    except Exception as e:
        logging.error(f"Error retrieving messages for {phone}: {e}")
        return []