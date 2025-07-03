from chunker import chunk_json_file
from client import upsert_chunks
from embedder import embed
import os

def get_folders(path: str):
    """
    Return a list of names of all subfolders in the given directory.
    """
    return [
        name for name in os.listdir(path)
        if os.path.isdir(os.path.join(path, name))
    ]

def get_files(path: str):
    """
    Return a list of file names in the given directory.
    """
    return [
        name for name in os.listdir(path)
        if os.path.isfile(os.path.join(path, name))
    ]

BASE_DIR = "data/world/"
FOLDERS = get_folders(BASE_DIR)

def ingest_folder(path: str):
    files = get_files(BASE_DIR+path)
    print("PATH = ", path)
    for file in files:
        # Chunks down the file
        chunks = chunk_json_file(BASE_DIR+path+"/"+file)
        
        #Create the embeddings from the chunks
        embeddings = [embed(c["page_content"]) for c in chunks]
        
        #Write the file into the collection
        upsert_chunks(path, embeddings, chunks)
        
if __name__ == "__main__":
    for folder in FOLDERS:
        ingest_folder(folder)
    
    
