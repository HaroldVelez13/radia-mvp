"""Initialize ChromaDB with proveedores and radicados data."""

import csv
import openpyxl
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.vector.chroma_client import ChromaClient


def load_proveedores(csv_path: str) -> list[dict]:
    """Load proveedores from CSV."""
    proveedores = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            proveedores.append({
                "nit": row["nit"],
                "razon_social": row["razon_social"],
                "correo_facturacion": row["correo_facturacion"],
                "banco": row["banco"],
                "tipo_cuenta": row["tipo_cuenta"],
                "numero_cuenta": row["numero_cuenta"],
                "estado": row["estado"],
                "categoria": row["categoria"],
            })
    return proveedores


def load_radicados(xlsx_path: str) -> list[dict]:
    """Load radicados from Excel."""
    radicados = []
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb["Radicación 2026"]
    
    # Skip header row
    for row in ws.iter_rows(min_row=2, values_only=True):
        radicado, fecha_recibido, remitente, nit_documento, tipo_documental, asunto, no_documento, valor_total, dependencia, fecha_vencimiento, estado, observaciones = row
        
        radicados.append({
            "radicado": radicado,
            "fecha_recibido": fecha_recibido,
            "remitente": remitente,
            "nit_documento": nit_documento,
            "tipo_documental": tipo_documental,
            "asunto": asunto,
            "no_documento": no_documento,
            "valor_total": valor_total,
            "dependencia": dependencia,
            "fecha_vencimiento": fecha_vencimiento,
            "estado": estado,
            "observaciones": observaciones,
        })
    return radicados


def main():
    print("Loading data...")
    
    # Data is mounted at /data in container
    import os
    data_dir = "/data" if os.path.exists("/data/maestro") else "data"
    
    proveedores = load_proveedores(os.path.join(data_dir, "maestro/maestro-proveedores.csv"))
    print(f"Loaded {len(proveedores)} proveedores")
    
    radicados = load_radicados(os.path.join(data_dir, "libro/libro-radicacion-2026.xlsx"))
    print(f"Loaded {len(radicados)} radicados")
    
    print("\nInitializing ChromaDB...")
    client = ChromaClient()
    
    success = client.initialize(proveedores_data=proveedores, radicados_data=radicados)
    
    if success:
        stats = client.get_stats()
        print(f"\nChromaDB initialized successfully!")
        print(f"  Proveedores: {stats['proveedores_count']}")
        print(f"  Radicados: {stats['radicados_count']}")
        
        # Test search
        print("\n--- Test search: 'Suministros' ---")
        results = client.buscar_proveedor_por_nombre("Suministros")
        for r in results:
            print(f"  {r['razon_social']} (NIT: {r['nit']}) - score: {r['score']}")
        
        print("\n--- Test search: 'Ferreteria' ---")
        results = client.buscar_proveedor_por_nombre("Ferreteria")
        for r in results:
            print(f"  {r['razon_social']} (NIT: {r['nit']}) - score: {r['score']}")
        
        # Test duplicate check
        print("\n--- Test duplicate: NIT 860.555.444-3, FE-1207 (exists) ---")
        dup = client.es_duplicado_semantico("860.555.444-3", "FE-1207")
        print(f"  Es duplicado: {dup['es_duplicado']}")
        print(f"  Radicado: {dup['duplicado_radicado']}")
        print(f"  Score: {dup['score']}")
        
        print("\n--- Test duplicate: NIT 901.234.567-1, COT-2026-0861 (exists) ---")
        dup = client.es_duplicado_semantico("901.234.567-1", "COT-2026-0861")
        print(f"  Es duplicado: {dup['es_duplicado']}")
        print(f"  Radicado: {dup['duplicado_radicado']}")
        print(f"  Score: {dup['score']}")
        
        print("\n--- Test duplicate: NIT 901.234.567-1, FE-9999 (new) ---")
        dup = client.es_duplicado_semantico("901.234.567-1", "FE-9999")
        print(f"  Es duplicado: {dup['es_duplicado']}")
        print(f"  Radicado: {dup['duplicado_radicado']}")
        print(f"  Score: {dup['score']}")
        
    else:
        print("ChromaDB initialization failed, using fallback mode")
        sys.exit(1)


if __name__ == "__main__":
    main()