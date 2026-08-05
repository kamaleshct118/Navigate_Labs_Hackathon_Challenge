import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.data_build.chroma_builder import ChromaDatabaseBuilder

def main():
    print("=" * 60)
    print("  Enterprise Compliance Assistant - ChromaDB Vector Builder")
    print("  Embedding Model: Nomic Embed Text (nomic-ai/nomic-embed-text-v1.5)")
    print("=" * 60)
    
    builder = ChromaDatabaseBuilder()
    builder.build_chroma_database()

if __name__ == "__main__":
    main()
