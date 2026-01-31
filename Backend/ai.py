import os
import sys
import json
import shutil
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
from thefuzz import process, fuzz 

# --- 1. SETUP & IMPORTS ---
try:
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError:
    print("❌ Error: Libraries missing. Run: pip install langchain-community faiss-cpu sentence-transformers thefuzz")
    sys.exit(1)

load_dotenv()

# API KEY
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or ""   #Get your own API key 

if not GOOGLE_API_KEY:
    print("❌ Error: Key is missing.")
    sys.exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

# --- 2. AUTHENTICATION (SIMULATED) ---
print("\n🔒 --- SECURITY LOGIN ---")
CURRENT_USER_ID = "C0010"
if not CURRENT_USER_ID:
    CURRENT_USER_ID = "C0010" # Default for testing
print(f"✅ Logged in as: {CURRENT_USER_ID}\n")


# --- 3. LOAD RESOURCES ---
print("🔹 Loading Databases...")
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datasets_dir = os.path.join(current_dir, "Database")
    
    cat_path = os.path.join(datasets_dir, "product_catalog.json")
    original_ord_path = os.path.join(datasets_dir, "order_database.json")
    copy_ord_path = os.path.join(datasets_dir, "order_database_copy.json")
    
    # Auto-Create Copy
    if os.path.exists(original_ord_path) and not os.path.exists(copy_ord_path):
        print(f"   Creating working copy: {copy_ord_path}")
        shutil.copy(original_ord_path, copy_ord_path)
    
    # Load Dataframes
    products_df = pd.read_json(cat_path) if os.path.exists(cat_path) else pd.DataFrame()
    orders_df = pd.read_json(copy_ord_path) if os.path.exists(copy_ord_path) else pd.DataFrame()

    if not products_df.empty:
        products_df.columns = [c.lower().replace(" ", "_") for c in products_df.columns]
    if not orders_df.empty:
        orders_df.columns = [c.lower().replace(" ", "_") for c in orders_df.columns]

    # --- FLATTEN ORDERS FOR SEARCH ---
    searchable_orders = pd.DataFrame()
    if not orders_df.empty and 'products' in orders_df.columns:
        searchable_orders = orders_df.explode('products')
        searchable_orders['product_name'] = searchable_orders['products'].apply(lambda x: x.get('product_name') if isinstance(x, dict) else None)
        print(f"   ✅ Flattened {len(orders_df)} orders into {len(searchable_orders)} searchable items.")
    else:
        print("   ⚠️ Warning: Could not flatten order products.")

    # Load AI Models
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    index_path = os.path.join(current_dir, "faiss_index")
    vector_db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    
    prod_index_path = os.path.join(current_dir, "faiss_product_index")
    if os.path.exists(prod_index_path):
        product_vector_db = FAISS.load_local(prod_index_path, embeddings, allow_dangerous_deserialization=True)
        print("   ✅ Product Hybrid Index Loaded.")
    else:
        product_vector_db = None

    print("✅ System Ready.")

except Exception as e:
    print(f"⚠️ Warning during load: {e}")
    products_df = pd.DataFrame()
    orders_df = pd.DataFrame()
    searchable_orders = pd.DataFrame()


# Assuming your chat object is named 'chat'
def reset_session():
    global chat
    print("🧹 System: Purging chat history...")
    # This restarts the chat session with an empty history
    chat = model.start_chat(history=[], enable_automatic_function_calling=True)
# --- 4. HELPER: SAVE TO DISK ---
def save_to_disk():
    try:
        orders_df.to_json(copy_ord_path, orient="records", indent=2)
        return True
    except Exception as e:
        print(f"❌ Error saving database: {e}")
        return False

# --- 5. DEFINE TOOLS (WITH PRIVACY) ---

def search_products(query: str):
    """Searches product catalog using fuzzy matching (Public Data)."""
    if products_df.empty: return "Catalog unavailable."
    product_names = products_df['product_name'].tolist()
    matches = process.extract(query, product_names, limit=3, scorer=fuzz.partial_ratio)
    final_results = []
    for match_name, score in matches:
        if score >= 60:
            row = products_df[products_df['product_name'] == match_name]
            if not row.empty:
                item = row.iloc[0].to_dict()
                final_results.append(item)
    if not final_results: return f"I couldn't find any products matching '{query}'."
    return json.dumps(final_results)

def browse_catalog(description: str):
    """
    Vector Search: Finds products in the catalog by meaning/description.
    Useful for: "Show me red shoes", "Do you have any gaming laptops?", "Something for hiking".
    """
    if product_vector_db is None: return "Product Search unavailable."
    
    # 1. Use Vector Search to find the top 3 matches
    docs = product_vector_db.similarity_search(description, k=3)
    
    if not docs:
        return f"I couldn't find any products matching '{description}'."
    
    # 2. Format the results for the user
    results = []
    for d in docs:
        results.append(d.page_content) 
        
    return "\n---\n".join(results)

def find_orders_by_description(description: str):
    """
    Hybrid Search: Finds USER'S orders based on a vague description.
    """
    if product_vector_db is None: return "Product Search unavailable."
    if searchable_orders.empty: return "Order DB unavailable."

    # 1. Vector Search
    docs = product_vector_db.similarity_search(description, k=1)
    if not docs:
        return f"I couldn't find any products matching '{description}'."
    
    matched_name = docs[0].metadata.get("product_name")
    
    # 2. PRIVACY FILTER + MATCH
    matches = searchable_orders[
        (searchable_orders['product_name'] == matched_name) & 
        (searchable_orders['customer_id'] == CURRENT_USER_ID) # <--- PRIVACY LOCK
    ]
    
    if matches.empty:
        return f"I found the product '{matched_name}' in our catalog, but YOU ({CURRENT_USER_ID}) haven't ordered it."
    
    results = matches[['order_id', 'order_status', 'product_name', 'order_date']].to_dict(orient="records")
    return json.dumps(results)

def check_order_status(order_id: str):
    """Checks status of a specific order ID (If owned by user)."""
    if orders_df.empty: return "Order DB unavailable."
    clean_id = str(order_id).replace(" ", "").strip()
    
    # PRIVACY FILTER
    res = orders_df[
        (orders_df['order_id'].astype(str) == clean_id) & 
        (orders_df['customer_id'] == CURRENT_USER_ID)
    ]
    
    if res.empty: return "Order not found (or it does not belong to you)."
    return res.to_json(orient="records")

def cancel_order(order_id: str):
    """Cancels an order (If owned by user)."""
    if orders_df.empty: return "Order DB unavailable."
    clean_id = str(order_id).replace(" ", "").strip()
    
    # PRIVACY FILTER
    matches = orders_df.index[
        (orders_df['order_id'].astype(str) == clean_id) & 
        (orders_df['customer_id'] == CURRENT_USER_ID)
    ].tolist()
    
    if not matches: return "Order not found (or permission denied)."
    idx = matches[0]
    
    current_status = orders_df.at[idx, 'order_status']
    if current_status.lower() in ["delivered", "shipped", "out for delivery", "cancelled"]:
        return f"Cannot cancel order {clean_id}. It is currently '{current_status}'."
    
    orders_df.at[idx, 'order_status'] = "Cancelled"
    save_to_disk()
    return f"Success. Order {clean_id} has been cancelled."

def initiate_return(order_id: str, reason: str = "ns"):
    """Returns a delivered order (If owned by user)."""
    if orders_df.empty: return "Order DB unavailable."
    clean_id = str(order_id).replace(" ", "").strip()
    
    # PRIVACY FILTER
    matches = orders_df.index[
        (orders_df['order_id'].astype(str) == clean_id) & 
        (orders_df['customer_id'] == CURRENT_USER_ID)
    ].tolist()
    
    if not matches: return "Order not found (or permission denied)."
    idx = matches[0]
    
    current_status = orders_df.at[idx, 'order_status']
    if current_status.lower() != "delivered":
        return f"Cannot return order {clean_id}. It is '{current_status}' (must be Delivered)."
        
    orders_df.at[idx, 'order_status'] = "Return Requested"
    save_to_disk()
    return f"Return initiated for Order {clean_id}."

def get_order_history():
    """Retrieves full order history sorted by newest date."""
    if orders_df.empty: 
        return "No orders found."
    
    # 1. Filter by current user
    user_orders = orders_df[orders_df['customer_id'] == CURRENT_USER_ID].copy()
    
    if user_orders.empty: 
        return f"No order history found for customer {CURRENT_USER_ID}."

    user_orders['order_date'] = pd.to_datetime(user_orders['order_date'])

    # 3. Sort by date (ascending=False puts newest at the top)
    user_orders = user_orders.sort_values(by='order_date', ascending=False)


    return user_orders.to_json(orient="records", date_format='iso')

def admin_update_order(order_id: str, new_status: str):
    """God Mode: Forces an order to any status (Bypasses Privacy - For Admin Demo Only)."""
    if orders_df.empty: return "Order DB unavailable."
    clean_id = str(order_id).replace(" ", "").strip()
    
    matches = orders_df.index[orders_df['order_id'].astype(str) == clean_id].tolist()
    if not matches: return "Order not found."
    idx = matches[0]
    
    orders_df.at[idx, 'order_status'] = new_status
    save_to_disk()
    return f"Admin Update: Order {clean_id} is now '{new_status}'."

def get_policy_info(question: str):
    docs = vector_db.similarity_search(question, k=2)
    return "\n".join([d.page_content for d in docs])

# --- 6. REGISTER TOOLS ---
tools = [
    search_products, 
    browse_catalog, # <--- General Shopping
    find_orders_by_description, # <--- Personal History
    check_order_status, 
    cancel_order, 
    initiate_return, 
    get_order_history, 
    admin_update_order,
    get_policy_info
]

system_instruction = f"""
You are a helpful Voice Support Agent for Customer {CURRENT_USER_ID}.
1. Use 'search_products' to find items by exact name (e.g. "Iphone").
2. Use 'browse_catalog' for VAGUE shopping queries (e.g. "show me red shoes", "gifts for dad").
3. Use 'find_orders_by_description' ONLY when the user asks about THEIR PAST ORDERS (e.g. "Where are my shoes?").
4. Use 'check_order_status' for specific ID tracking.
5. Use 'cancel_order' IF the user explicitly asks to cancel.
6. Use 'initiate_return' IF the user wants to return a delivered item.
7. Use 'get_order_history' to see all past orders. Do not recite the order details in text, just say, "Here are your orders".
8. Use 'admin_update_order' ONLY if user says "Force update" or "Admin mode".
9. Keep answers SHORT (max 4 sentences) and spoken-style.
"""

# Use Flash for speed
model = genai.GenerativeModel('gemini-2.5-flash', tools=tools, system_instruction=system_instruction)
chat = model.start_chat(enable_automatic_function_calling=True)

# --- 7. INTERFACE ---
def process_user_input(user_text):
    try:
        response = chat.send_message(user_text)
        
        # Initialize our custom data payload
        structured_data = {
            "bot_text": response.text,
            "type": None,
            "items": []
        }

        # Check the last message in chat history for tool outputs
        # Gemini history: [UserMsg, ModelMsg(call), UserMsg(response), ModelMsg(final text)]
        for part in chat.history[-2].parts: # Look at the tool response part
            if part.function_response:
                raw_content = part.function_response.response['result']
                
                # Check if it looks like Order data or Product data
                if "order_id" in raw_content:
                    structured_data["type"] = "orders"
                    structured_data["items"] = json.loads(raw_content)
                elif "product_name" in raw_content:
                    structured_data["type"] = "products"
                    structured_data["items"] = json.loads(raw_content)

        return structured_data
    except Exception as e:
        return {"bot_text": f"Error: {str(e)}", "type": None, "items": []}

if __name__ == "__main__":
    print(f"\n💬 AI Agent active for user {CURRENT_USER_ID} (Type 'quit' to exit)")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["quit", "exit"]: break
        
        response = process_user_input(user_input)
        print(f"AI: {response}")