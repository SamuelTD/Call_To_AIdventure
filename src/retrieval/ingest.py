from chunker import chunk_character_json_file, chunk_location_json_file
from client import upsert_chunks
from embedder import embed
import os

# ------------------ Helper Functions ------------------

def get_folders(path: str):
    """
    Return a list of names of all subfolders in the given directory.
    """
    subfolders = [
        name for name in os.listdir(path)
        if os.path.isdir(os.path.join(path, name))
    ]
    print(f"[get_folders] Found {len(subfolders)} folders in '{path}': {subfolders}")
    return subfolders


def get_files(path: str):
    """
    Return a list of file names in the given directory.
    """
    files = [
        name for name in os.listdir(path)
        if os.path.isfile(os.path.join(path, name))
    ]
    print(f"[get_files] Found {len(files)} files in '{path}': {files}")
    return files

# ------------------ Configuration ------------------

BASE_DIR = "data/world/"
print(f"[ingest] Starting ingestion from base directory: {BASE_DIR}")
FOLDERS = get_folders(BASE_DIR)

# ------------------ Ingestion Logic ------------------

def ingest_folder(collection_name: str):
    folder_path = os.path.join(BASE_DIR, collection_name)
    files = get_files(folder_path)
    print(f"[ingest_folder] Ingesting collection '{collection_name}' with {len(files)} files...")

    for file in files:
        file_path = os.path.join(folder_path, file)
        print(f"[ingest_folder] Processing file: {file_path}")

        # 1) Chunk the file
        match collection_name:
            case "characters":
                chunks = chunk_character_json_file(file_path)
            case "locations":
                chunks = chunk_location_json_file(file_path)
      
        print(f"[ingest_folder] chunk_json_file returned {len(chunks)} chunks for {file}")

        # 2) Embed each chunk
        embeddings = []
        for idx, chunk in enumerate(chunks):
            print(f"[ingest_folder] Embedding chunk {idx} for '{file}' ({len(chunk['page_content'].split())} words)")
            vec = embed(chunk["page_content"])
            embeddings.append(vec)
        print(f"[ingest_folder] Generated {len(embeddings)} embedding vectors")

        # 3) Upsert into ChromaDB
        upsert_chunks(collection_name, embeddings, chunks)
        print(f"[ingest_folder] Upserted all chunks for '{file}' into collection '{collection_name}'\n")

# ------------------ Main Script ------------------

if __name__ == "__main__":
    for folder in FOLDERS:
        ingest_folder(folder)
    print(f"[ingest] Completed ingestion for all collections: {FOLDERS}")
