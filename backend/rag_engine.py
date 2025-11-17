# ============================
# RAG ENGINE (FINAL FIXED VERSION)
# ============================
import shutil

class RAGEngine:
    def __init__(self):
        self.embedder = SafeEmbedder()
        
        # CSV paths
        self.csv_hotels = os.path.join(DATA_DIR, "hotels.csv")
        self.csv_activities = os.path.join(DATA_DIR, "activities.csv")
        self.csv_places = os.path.join(DATA_DIR, "places.csv")

        # ✳️ STEP 1 — DELETE LOCAL QDRANT FOLDER (real fix)
        if os.path.exists("qdrant_local"):
            print("🧹 Cleaning old Qdrant DB…")
            shutil.rmtree("qdrant_local")   # ← full delete

        # STEP 2 — Recreate Qdrant client (empty fresh DB)
        self.client = QdrantClient(path="qdrant_local")

        # STEP 3 — Recreate collection fresh
        print("🔄 Recreating fresh collection…")
        self._init_collection()

        # STEP 4 — Reindex all CSV files
        print("📦 Re-indexing all CSV files…")
        self._index_all()

        print("✅ Database reset complete. Fresh index is ready!")


    # Create collection
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIMENSION,
                distance=models.Distance.COSINE,
            ),
        )

    # Index CSV
    def _index_file(self, file_path, data_type):
        if not os.path.exists(file_path):
            logger.warning(f"Missing file: {file_path}")
            return

        df = pd.read_csv(file_path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))

            # text to embed
            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')}"
            vec = self.embedder.encode(text)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vec,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)
            print(f"Indexed {len(points)} items from {file_path}")

    # Index all
    def _index_all(self):
        self._index_file(self.csv_hotels, "Hotel")
        self._index_file(self.csv_activities, "Activity")
        self._index_file(self.csv_places, "Place")
