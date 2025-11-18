import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from uuid import uuid4
from dotenv import load_dotenv

# এনভায়রনমেন্ট লোড
load_dotenv()

# কনফিগারেশন
QDRANT_URL = os.getenv("QDRANT_URL", ":memory:") # ডিফল্ট মেমোরি মোড
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = "eco_travel_v3"

# পাথ ফিক্স (যাতে data ফোল্ডার খুঁজে পায়)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

print("🚀 Starting Database Setup...")
print(f"📂 Looking for data in: {DATA_DIR}")

# ১. ক্লায়েন্ট কানেক্ট করা
try:
    if QDRANT_URL == ":memory:":
        client = QdrantClient(":memory:")
    else:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    print("✅ Connected to Qdrant!")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
    exit()

# ২. মডেল লোড করা
print("🧠 Loading Embedding Model (might take a moment)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# ৩. কালেকশন রিসেট করা
print("🗑️ Clearing old data...")
try:
    client.delete_collection(COLLECTION)
except:
    pass # কালেকশন না থাকলে ইগনোর করো

client.recreate_collection(
    collection_name=COLLECTION,
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
)
print("✨ New Collection Created!")

# ৪. ডাটা আপলোড করা
files = {
    "Hotel": "hotels.csv",
    "Activity": "activities.csv",
    "Place": "places.csv"
}

total_indexed = 0

for dtype, filename in files.items():
    file_path = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(file_path):
        print(f"⚠️ WARNING: File not found: {filename}")
        continue
        
    df = pd.read_csv(file_path)
    points = []
    
    print(f"📄 Indexing {len(df)} {dtype}s from {filename}...")
    
    for _, row in df.iterrows():
        # টেক্সট তৈরি (যেটা দিয়ে সার্চ হবে)
        text_data = f"{dtype}: {row.get('name', '')} in {row.get('location', '')}. {row.get('description', '')} Eco Score: {row.get('eco_score', 0)}"
        
        # ভেক্টর জেনারেট
        embedding = model.encode(text_data).tolist()
        
        # ডাটা রেডি করা
        payload = row.to_dict()
        payload['data_type'] = dtype
        # নিশ্চিত করা যে ফিল্ডগুলো আছে
        payload.setdefault('eco_score', 5.0)
        payload.setdefault('cost', 0)
        
        points.append(models.PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload=payload
        ))
    
    if points:
        client.upsert(collection_name=COLLECTION, points=points)
        total_indexed += len(points)

print("\n------------------------------------------------")
if total_indexed > 0:
    print(f"🎉 SUCCESS! Total {total_indexed} items loaded into database.")
    print("👉 Now run: streamlit run app.py")
else:
    print("❌ ERROR: No data loaded. Please check if CSV files exist inside 'data/' folder.")
print("------------------------------------------------")
