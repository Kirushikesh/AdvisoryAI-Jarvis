from langchain_core.tools import tool
from pathlib import Path
from datetime import datetime
from typing import Union
from jarvis.config import CLIENT_DATA_PATH, WORKSPACE_DIR

@tool
def find_files_updated_after(timestamp: str) -> Union[str, list]:
    """
    Find all files in the client data folder that were modified after a given timestamp.
    Paths are returned relative to the workspace directory.
    Useful during heartbeat checks to detect changes in client documents, emails, or transcripts.
    
    Args:
        timestamp (str): Timestamp in format "YYYY-MM-DD HH:MM:SS" 
                        Example: "2024-01-15 14:30:00"
                        Or just date: "2024-01-15" (assumes 00:00:00)
    
    Returns:
        list: List of dictionaries containing relative file paths and modification times
    
    Example:
        find_files_updated_after("2024-01-15 14:30:00")
        find_files_updated_after("2024-01-15")
    """
    # Parse the timestamp string
    try:
        if len(timestamp) == 10:  # Date only format "YYYY-MM-DD"
            check_time = datetime.strptime(timestamp, "%Y-%m-%d")
        else:  # Full datetime format "YYYY-MM-DD HH:MM:SS"
            check_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        return f"Invalid timestamp format. Use 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'. Error: {e}"
    
    updated_files = []
    folder = Path(CLIENT_DATA_PATH)
    
    # Check if folder exists
    if not folder.exists():
        return f"Folder not found: {CLIENT_DATA_PATH}"
    
    # Walk through all files in the directory tree
    for file_path in folder.rglob('*'):
        if file_path.is_file():
            # Get the modification time of the file
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            # Check if file was modified after the given timestamp
            if mod_time > check_time:
                # Calculate relative path to workspace
                try:
                    rel_path = file_path.relative_to(WORKSPACE_DIR)
                except ValueError:
                    # Fallback to absolute string if not under WORKSPACE_DIR
                    rel_path = file_path
                
                # Include file path and modification time for better context
                updated_files.append({
                    "path": str(rel_path),
                    "modified": mod_time.strftime("%Y-%m-%d %H:%M:%S")
                })
    
    if not updated_files:
        return f"No files modified after {timestamp}"
    
    return updated_files
