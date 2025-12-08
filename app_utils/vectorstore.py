import chromadb
import shutil
import time
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .embeddings import get_embeddings
from pathlib import Path


def _force_cleanup_directory(db_path: str, max_retries: int = 3):
    """
    Forcefully remove directory with retries to handle locked files.
    """
    db_path_obj = Path(db_path)
    
    if not db_path_obj.exists():
        return True
    
    for attempt in range(max_retries):
        try:
            # Try to remove the directory
            shutil.rmtree(db_path, ignore_errors=True)
            
            # Wait a bit to ensure files are released
            time.sleep(0.5)
            
            # Verify it's gone
            if not db_path_obj.exists():
                return True
                
            # If still exists, try again with more force
            if attempt < max_retries - 1:
                # Try removing individual files
                for root, dirs, files in os.walk(db_path, topdown=False):
                    for name in files:
                        try:
                            file_path = os.path.join(root, name)
                            os.chmod(file_path, 0o777)
                            os.remove(file_path)
                        except Exception:
                            pass
                    for name in dirs:
                        try:
                            dir_path = os.path.join(root, name)
                            os.chmod(dir_path, 0o777)
                            os.rmdir(dir_path)
                        except Exception:
                            pass
                try:
                    os.rmdir(db_path)
                except Exception:
                    pass
                    
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed
                raise RuntimeError(
                    f"Failed to clean up directory {db_path} after {max_retries} attempts. "
                    f"Please manually delete the directory. Error: {str(e)}"
                )
            time.sleep(1)  # Wait before retry
    
    return False


def get_client(db_path: str):
    """
    Get ChromaDB PersistentClient with error handling for corrupted data.
    """
    db_path_obj = Path(db_path)
    
    # Ensure parent directory exists
    db_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Try to create client
    try:
        return chromadb.PersistentClient(path=db_path)
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check for data corruption errors
        if any(keyword in error_msg for keyword in [
            "null bytes", "cannot contain null", "corrupt", 
            "invalid", "malformed", "decode"
        ]):
            # Force cleanup and retry
            try:
                _force_cleanup_directory(db_path)
                # Wait a moment for file system to sync
                time.sleep(0.5)
                # Create fresh directory
                db_path_obj.mkdir(parents=True, exist_ok=True)
                # Retry client creation
                return chromadb.PersistentClient(path=db_path)
            except Exception as retry_error:
                raise RuntimeError(
                    f"Failed to initialize ChromaDB client at {db_path} even after cleanup. "
                    f"Please manually delete the '{db_path}' directory and try again. "
                    f"Original error: {str(e)}, Cleanup error: {str(retry_error)}"
                )
        
        # For other errors, raise with helpful message
        raise RuntimeError(
            f"Error initializing ChromaDB client at {db_path}. "
            f"Error: {str(e)}"
        )


def save_to_vector_db(university: str, text: str):
    """
    Save text data to ChromaDB vector database for the given university.
    """
    db_path = f"data/{university}"
    
    # Forcefully clean up old data directory before creating new one
    # This is safe since we're rebuilding the entire database
    try:
        _force_cleanup_directory(db_path)
        time.sleep(0.3)  # Brief pause to ensure cleanup is complete
    except Exception as e:
        # Log but continue - get_client will handle it if needed
        print(f"Warning: Could not fully clean up {db_path}: {e}")
    
    # Ensure fresh directory exists
    Path(db_path).mkdir(parents=True, exist_ok=True)
    
    # Get client (will handle any remaining issues)
    client = get_client(db_path)
    
    # Delete existing collection if it exists
    try:
        client.delete_collection(name="university_data")
    except Exception:
        pass  # Collection doesn't exist, which is fine
    
    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500, 
        chunk_overlap=200
    )
    chunks = splitter.split_text(text)
    
    if not chunks:
        raise ValueError("No text chunks generated from the input text.")
    
    # Generate embeddings
    embeddings = get_embeddings()
    vectors = embeddings.embed_documents(chunks)
    
    # Create new collection
    collection = client.create_collection(
        name="university_data"
    )
    
    # Add documents in batches for better performance
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        batch_vectors = vectors[i:i+batch_size]
        batch_ids = [f"id_{j}" for j in range(i, min(i+batch_size, len(chunks)))]
        
        try:
            collection.add(
                ids=batch_ids,
                documents=batch_chunks,
                embeddings=batch_vectors,
            )
        except Exception as e:
            raise RuntimeError(
                f"Error adding documents to collection: {str(e)}"
            )
    
    return collection


def load_collection(university: str):
    """
    Load existing ChromaDB collection for the given university.
    """
    db_path = f"data/{university}"
    
    if not Path(db_path).exists():
        raise ValueError(
            f"Database directory not found for university '{university}'. "
            f"Please build the database first using 'Build / Update Database'."
        )
    
    client = get_client(db_path)
    
    try:
        return client.get_collection("university_data")
    except Exception as e:
        raise ValueError(
            f"Collection 'university_data' not found for university '{university}'. "
            f"Please build the database first. Error: {str(e)}"
        )
