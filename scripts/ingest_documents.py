#!/usr/bin/env python3
"""
Script to ingest client documents into ChromaDB vector store.

This script:
1. Scans the datasets/ folder for all client directories
2. Loads .docx files from each client's folder
3. Extracts metadata (client name, document type)
4. Splits documents into chunks
5. Stores them in a persistent ChromaDB collection

Usage:
    python scripts/ingest_documents.py
"""

from jarvis.utils.vector_store import ingest_documents

if __name__ == "__main__":
    print("=" * 60)
    print("JARVIS - Document Ingestion Script")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Scan datasets/ for client folders")
    print("  2. Load all .docx files")
    print("  3. Chunk and embed documents")
    print("  4. Store in ChromaDB\n")
    
    input("Press Enter to continue...")
    
    print("\nStarting ingestion...")
    ingest_documents()
    
    print("\n" + "=" * 60)
    print("Ingestion complete!")
    print("=" * 60)
