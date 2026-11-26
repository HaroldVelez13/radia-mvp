"""ChromaDB vector client for proveedores and radicados search."""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ChromaClient:
    """
    ChromaDB client with two collections:
    - proveedores: for semantic search by nombre/razon_social
    - radicados: for duplicate detection (NIT + numero_factura)
    
    Uses local sentence-transformers embeddings (paraphrase-multilingual-MiniLM-L12-v2).
    Falls back to exact match if Chroma is not available.
    """

    EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    PERSIST_DIR = "./chroma_db"
    COLLECTION_PROVEEDORES = "proveedores"
    COLLECTION_RADICADOS = "radicados"

    def __init__(self, persist_dir: str = PERSIST_DIR):
        self.persist_dir = persist_dir
        self._client: Optional[chromadb.Client] = None
        self._embedding_model: Optional[SentenceTransformer] = None
        self._proveedores_collection = None
        self._radicados_collection = None
        self._available = False

    def _get_client(self) -> chromadb.Client:
        """Get or create ChromaDB persistent client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
        return self._client

    def _get_embedding_model(self) -> SentenceTransformer:
        """Get or load the embedding model."""
        if self._embedding_model is None:
            logger.info(f"Loading embedding model: {self.EMBEDDING_MODEL}")
            self._embedding_model = SentenceTransformer(self.EMBEDDING_MODEL)
        return self._embedding_model

    def _get_proveedores_collection(self):
        """Get or create proveedores collection."""
        if self._proveedores_collection is None:
            client = self._get_client()
            self._proveedores_collection = client.get_or_create_collection(
                name=self.COLLECTION_PROVEEDORES,
                metadata={"hnsw:space": "cosine"}
            )
            # If collection has data, mark as available
            if self._proveedores_collection.count() > 0:
                self._available = True
        return self._proveedores_collection

    def _get_radicados_collection(self):
        """Get or create radicados collection."""
        if self._radicados_collection is None:
            client = self._get_client()
            self._radicados_collection = client.get_or_create_collection(
                name=self.COLLECTION_RADICADOS,
                metadata={"hnsw:space": "cosine"}
            )
            # If collection has data, mark as available
            if self._radicados_collection.count() > 0:
                self._available = True
        return self._radicados_collection

    def initialize(self, proveedores_data: list[dict] = None, radicados_data: list[dict] = None) -> bool:
        """
        Initialize collections with data.
        
        Args:
            proveedores_data: List of dicts with keys: nit, razon_social, correo_facturacion, banco, tipo_cuenta, numero_cuenta, estado, categoria
            radicados_data: List of dicts with keys: radicado, fecha_recibido, remitente, nit_documento, tipo_documental, asunto, no_documento, valor_total, dependencia, fecha_vencimiento, estado, observaciones
            
        Returns:
            True if successful, False if Chroma unavailable
        """
        try:
            # Test connection
            client = self._get_client()
            client.heartbeat()
            
            # Load embedding model
            self._get_embedding_model()
            
            # Initialize proveedores collection
            if proveedores_data:
                self._index_proveedores(proveedores_data)
            
            # Initialize radicados collection
            if radicados_data:
                self._index_radicados(radicados_data)
            
            self._available = True
            logger.info("ChromaDB initialized successfully")
            return True
            
        except Exception as e:
            logger.warning(f"ChromaDB not available, falling back to exact match: {e}")
            self._available = False
            return False

    def _index_proveedores(self, proveedores: list[dict]):
        """Index proveedores into Chroma."""
        collection = self._get_proveedores_collection()
        
        # Check if already indexed
        existing = collection.count()
        if existing > 0:
            logger.info(f"Proveedores collection already has {existing} items, skipping indexing")
            return
        
        ids = []
        documents = []
        metadatas = []
        
        for prov in proveedores:
            nit = prov.get("nit", "") or ""
            razon_social = prov.get("razon_social", "") or ""
            
            # Create searchable text: razon_social + nit
            doc_text = f"{razon_social} {nit}".strip()
            
            ids.append(nit.replace(".", "").replace("-", ""))
            documents.append(doc_text)
            metadatas.append({
                "nit": nit,
                "razon_social": razon_social,
                "correo_facturacion": prov.get("correo_facturacion", "") or "",
                "banco": prov.get("banco", "") or "",
                "tipo_cuenta": prov.get("tipo_cuenta", "") or "",
                "numero_cuenta": prov.get("numero_cuenta", "") or "",
                "estado": prov.get("estado", "") or "",
                "categoria": prov.get("categoria", "") or "",
            })
        
        if ids:
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Indexed {len(ids)} proveedores")

    def _index_radicados(self, radicados: list[dict]):
        """Index radicados into Chroma for duplicate detection."""
        collection = self._get_radicados_collection()
        
        # Check if already indexed
        existing = collection.count()
        if existing > 0:
            logger.info(f"Radicados collection already has {existing} items, skipping indexing")
            return
        
        ids = []
        documents = []
        metadatas = []
        
        for rad in radicados:
            radicado = rad.get("radicado", "") or ""
            nit = rad.get("nit_documento", "") or ""
            no_documento = rad.get("no_documento", "") or ""
            tipo = rad.get("tipo_documental", "") or ""
            
            # Create searchable text for duplicate detection: NIT + numero_factura + tipo
            doc_text = f"{nit} {no_documento} {tipo}".strip()
            
            # Use radicado as ID, or generate one
            doc_id = radicado or f"{nit}_{no_documento}".replace(".", "").replace("-", "").replace(" ", "_")
            
            ids.append(doc_id)
            documents.append(doc_text)
            # Convert all values to strings, handle None
            valor_total = rad.get("valor_total")
            if valor_total is not None:
                valor_total = str(valor_total)
            else:
                valor_total = ""
            
            metadatas.append({
                "radicado": radicado,
                "nit_documento": nit,
                "no_documento": no_documento,
                "tipo_documental": tipo,
                "fecha_recibido": str(rad.get("fecha_recibido", "")) or "",
                "remitente": rad.get("remitente", "") or "",
                "asunto": rad.get("asunto", "") or "",
                "valor_total": valor_total,
            })
        
        if ids:
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Indexed {len(ids)} radicados")

    def buscar_proveedor_por_nombre(self, nombre: str, n_results: int = 5) -> list[dict]:
        """
        Search proveedores by semantic similarity to nombre.
        
        Args:
            nombre: Name to search for (partial name, typo-tolerant)
            n_results: Maximum results to return
            
        Returns:
            List of dicts with keys: nit, razon_social, score, metadata
        """
        try:
            # Accessing collection will set _available if data exists
            collection = self._get_proveedores_collection()
            collection = self._get_proveedores_collection()
            model = self._get_embedding_model()
            
            # Generate embedding for query
            query_embedding = model.encode(nombre).tolist()
            
            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, collection.count()),
                include=["metadatas", "documents", "distances"]
            )
            
            # Format results
            formatted = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    # Convert distance to similarity score (cosine: 0=identical, 2=opposite)
                    score = 1.0 - (distance / 2.0)
                    
                    formatted.append({
                        "nit": metadata.get("nit", ""),
                        "razon_social": metadata.get("razon_social", ""),
                        "score": round(score, 4),
                        "metadata": metadata,
                    })
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error searching proveedores: {e}")
            return self._fallback_buscar_proveedor(nombre, n_results)

    def es_duplicado_semantico(self, nit: str, numero_factura: str, tipo_documental: str = "Factura", 
                               threshold: float = 0.95) -> dict:
        """
        Check if a document is a semantic duplicate (same NIT + numero_factura).
        
        Args:
            nit: Provider NIT
            numero_factura: Invoice/document number
            tipo_documental: Document type (Factura, Viático, etc.)
            threshold: Similarity threshold (0.95 = very strict)
            
        Returns:
            Dict with: es_duplicado (bool), duplicado_radicado (str|None), score (float), metadata (dict|None)
        """
        try:
            # Accessing collection will set _available if data exists
            collection = self._get_radicados_collection()
            collection = self._get_radicados_collection()
            model = self._get_embedding_model()
            
            query_nit_clean = nit.replace(".", "").replace("-", "")
            
            # First, try exact match using metadata filtering (where clause)
            # This is more reliable for exact NIT + numero_factura matching
            try:
                results = collection.query(
                    query_embeddings=[model.encode(f"{nit} {numero_factura} {tipo_documental}").tolist()],
                    n_results=20,  # Get more results to find exact match
                    where={"nit_documento": {"$eq": nit}},
                    include=["metadatas", "documents", "distances"]
                )
            except Exception:
                # Fallback if where clause not supported
                results = collection.query(
                    query_embeddings=[model.encode(f"{nit} {numero_factura} {tipo_documental}").tolist()],
                    n_results=20,
                    include=["metadatas", "documents", "distances"]
                )
            
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    score = 1.0 - (distance / 2.0)
                    
                    # Check if it's the same NIT and numero_factura (exact match on metadata)
                    stored_nit = metadata.get("nit_documento", "").replace(".", "").replace("-", "")
                    stored_no_doc = metadata.get("no_documento", "")
                    
                    if stored_nit == query_nit_clean and stored_no_doc == numero_factura:
                        return {
                            "es_duplicado": True,
                            "duplicado_radicado": metadata.get("radicado"),
                            "score": round(score, 4),
                            "metadata": metadata,
                        }
                    
                    # Also check semantic similarity above threshold
                    if score >= threshold:
                        return {
                            "es_duplicado": True,
                            "duplicado_radicado": metadata.get("radicado"),
                            "score": round(score, 4),
                            "metadata": metadata,
                        }
            
            return {
                "es_duplicado": False,
                "duplicado_radicado": None,
                "score": 0.0,
                "metadata": None,
            }
            
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return self._fallback_es_duplicado(nit, numero_factura)

    # --- Fallback methods (exact match) ---

    def _fallback_buscar_proveedor(self, nombre: str, n_results: int = 5) -> list[dict]:
        """Fallback: exact substring match on proveedores CSV."""
        # This would need access to the CSV data - for now return empty
        logger.warning("Chroma unavailable, fallback not fully implemented")
        return []

    def _fallback_es_duplicado(self, nit: str, numero_factura: str) -> dict:
        """Fallback: exact match check."""
        logger.warning("Chroma unavailable, fallback not fully implemented")
        return {
            "es_duplicado": False,
            "duplicado_radicado": None,
            "score": 0.0,
            "metadata": None,
        }

    def is_available(self) -> bool:
        """Check if ChromaDB is available."""
        return self._available

    def get_stats(self) -> dict:
        """Get collection statistics."""
        if not self._available:
            return {"available": False}
        
        try:
            prov_count = self._get_proveedores_collection().count()
            rad_count = self._get_radicados_collection().count()
            return {
                "available": True,
                "proveedores_count": prov_count,
                "radicados_count": rad_count,
            }
        except Exception:
            return {"available": False}


# Singleton instance
_chroma_client: Optional[ChromaClient] = None


def get_chroma_client() -> ChromaClient:
    """Get singleton ChromaClient instance."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaClient()
    return _chroma_client