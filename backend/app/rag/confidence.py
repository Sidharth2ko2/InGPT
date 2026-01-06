from app.config import CONFIDENCE_THRESHOLD

def confident(distances):
    # Check if distances is empty or the first result set is empty
    if not distances or len(distances) == 0 or len(distances[0]) == 0:
        return False
        
    return min(distances[0]) < CONFIDENCE_THRESHOLD