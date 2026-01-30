import os
import sys
import json

try:
    from langchain_core.documents import Document
    from langchain_community.document_loaders import TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
except ImportError as e:
    print(f"LIBRARY ERROR: {e}")
    print("Run: pip install langchain-core langchain-text-splitters langchain-community faiss-cpu sentence-transformers")
    sys.exit(1)

# --- PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
datasets_dir = os.path.join(current_dir, "Database")

POLICY_TXT_PATH = os.path.join(datasets_dir, "company_policies text.txt") # Check your filename matches exactly!
FAQ_JSON_PATH = os.path.join(datasets_dir, "product_faqs.json")
PRODUCT_CATALOG_PATH = os.path.join(datasets_dir, "product_catalog.json")

def build_knowledge_base():
    print("STARTING KNOWLEDGE BUILDER...")
    
    # Initialize Embeddings Model (Used for both indexes)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # ==========================================
    # PART 1: BUILD GENERAL INDEX (Policies & FAQs)
    # ==========================================
    print("\n--- Phase 1: General Knowledge (Policies & FAQs) ---")
    general_docs = []

    # 1. Load Policies
    if os.path.exists(POLICY_TXT_PATH):
        try:
            loader = TextLoader(POLICY_TXT_PATH, encoding="utf-8")
            loaded_docs = loader.load()
            general_docs.extend(loaded_docs)
            print(f"   Loaded Policies.")
        except Exception as e:
            print(f"   ❌ Error loading policies: {e}")
    else:
        print(f"   ⚠️ File not found: {POLICY_TXT_PATH}")

# 2. Load FAQs (Updated for Nested Structure)
    if os.path.exists(FAQ_JSON_PATH):
        try:
            with open(FAQ_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                count = 0
                
                # Loop through each PRODUCT
                for product in data:
                    p_name = product.get("product_name", "General")
                    faq_list = product.get("faqs", [])
                    
                    # Loop through each QUESTION inside that product
                    for item in faq_list:
                        q = item.get('question')
                        a = item.get('answer')
                        
                        if q and a:
                            # We add the Product Name to the text so the AI knows 
                            # which product this answer belongs to.
                            text = f"Product: {p_name}\nQ: {q}\nA: {a}"
                            
                            # Add to the list
                            general_docs.append(Document(page_content=text, metadata={"source": "faq", "product": p_name}))
                            count += 1
                            
                print(f"   Loaded {count} FAQs.")
        except Exception as e:
            print(f"   ❌ Error loading FAQs: {e}")
    else:
        print(f"   ⚠️ File not found: {FAQ_JSON_PATH}")
    # 3. Save General Index
    if general_docs:
        print("   Splitting text and saving 'faiss_index'...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_documents(general_docs)
        
        db = FAISS.from_documents(chunks, embeddings)
        db.save_local("faiss_index")
        print("   ✅ General Memory Built.")
    else:
        print("   ⚠️ No general data found. Skipping 'faiss_index' build.")

    # ==========================================
    # PART 2: BUILD PRODUCT INDEX (Hybrid Search)
    # ==========================================
    print("\n--- Phase 2: Product Knowledge (Hybrid Search) ---")
    product_docs = []

    if os.path.exists(PRODUCT_CATALOG_PATH):
        try:
            with open(PRODUCT_CATALOG_PATH, "r", encoding="utf-8") as f:
                products = json.load(f)
                
                for p in products:
                    # Content: This is what the AI searches against (Description + Category)
                    # We combine them so "Noise cancelling" or "Footwear" both work.
                    content = f"Product: {p['product_name']}\nCategory: {p['category']}\nDescription: {p['description']}"
                    
                    # Metadata: This is the KEY we need for the Hybrid Tool
                    # We store the EXACT product name so Python can find it in the Order DB later.
                    meta = {"product_name": p['product_name']}
                    
                    doc = Document(page_content=content, metadata=meta)
                    product_docs.append(doc)
                
                print(f"   Loaded {len(product_docs)} products from catalog.")

            if product_docs:
                print("   Saving 'faiss_product_index'...")
                # No text splitting needed for products (descriptions are usually short enough)
                product_db = FAISS.from_documents(product_docs, embeddings)
                product_db.save_local("faiss_product_index")
                print("   ✅ Product Memory Built.")
        except Exception as e:
            print(f"   ❌ Error processing product catalog: {e}")
    else:
        print(f"   ⚠️ File not found: {PRODUCT_CATALOG_PATH}")

    print("\n🎉 BUILD COMPLETE.")

if __name__ == "__main__":
    build_knowledge_base()