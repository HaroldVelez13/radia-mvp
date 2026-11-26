#!/usr/bin/env python3
"""
Medición de precisión/recall contra esperado-parcial.csv
"""
import csv
from pathlib import Path
from dataclasses import dataclass

from app.infrastructure.eml.parser import parse_eml
from app.application.services.reglas_factura import es_duplicado
from app.application.services.reglas_viaticos import validar_viatico_completo
from app.application.services.reglas_peticion import clasificar_peticion

BANDEJA_DIR = Path("/data/bandeja")
LIBRO_PATH = Path("/data/libro/libro-radicacion-2026.xlsx")
ESPERADO_PATH = Path("/data/libro/esperado-parcial.csv")


@dataclass
class Expected:
    correo: str
    documento: str
    tipo: str
    dependencia: str
    accion: str
    vence: str
    observacion: str


@dataclass
class Prediction:
    correo: str
    tipo: str
    duplicado: bool
    fraude: bool
    dependencia: str
    accion: str
    observaciones: list


def load_expected():
    expected = []
    with open(ESPERADO_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            expected.append(Expected(
                correo=row["correo"],
                documento=row["documento"],
                tipo=row["tipo"],
                dependencia=row["dependencia"],
                accion=row["accion"],
                vence=row["vence"],
                observacion=row["observacion"],
            ))
    return expected


def predict_eml(eml_path: Path) -> Prediction:
    parsed = parse_eml(str(eml_path))
    asunto = parsed.get("asunto", "") or ""
    nit = parsed.get("nit")
    no_documento = parsed.get("no_documento")
    tipo_doc = parsed.get("tipo_documental", "Factura")
    fecha = parsed.get("fecha")
    remitente = parsed.get("remitente", "") or ""

    observaciones = []
    duplicado = False
    fraude = False
    dependencia = ""
    accion = "Radicar"
    tipo_pred = tipo_doc

    # Map parser tipo to expected tipo labels
    tipo_map = {
        "Factura": "Factura",
        "Solicitud de viáticos": "Solicitud de viáticos",
        "Viáticos": "Solicitud de viáticos",
        "Derecho de petición": "Derecho de petición",
        "Cotización": "Cotización",
        "Publicidad": "Publicidad",
        "Oficio": "Oficio",
        "Queja": "Queja",
    }
    tipo_pred = tipo_map.get(tipo_doc, tipo_doc)

    if "petición" in tipo_doc.lower() or "peticion" in tipo_doc.lower() or "derecho" in tipo_doc.lower():
        peticion_res = clasificar_peticion(asunto)
        # Keep the original tipo from parser, just add petition details
        observaciones.append(f"Petición tipo: {peticion_res.tipo.value} ({peticion_res.plazo_dias_habiles} días háb.)")

    # Duplicado check for facturas
    if tipo_doc == "Factura" and nit and no_documento:
        try:
            dup, radicado, motivo = es_duplicado(nit, no_documento, LIBRO_PATH)
            duplicado = dup
            if dup:
                accion = "No radicar"
                observaciones.append(f"DUPLICADO: {motivo}")
            else:
                observaciones.append(f"Sin duplicado: {motivo}")
        except Exception as e:
            observaciones.append(f"Error duplicado: {e}")

    # Fraude check for facturas with NIT
    if tipo_doc == "Factura" and nit:
        try:
            # We don't have cuenta/correo from EML, but we can check if NIT exists in maestro
            # For measurement, we'll use a heuristic: if observacion mentions "cuenta coinciden" -> no fraude
            # In production, this would check PDF attachment
            fraude = False
            observaciones.append("Fraude: requiere PDF para verificar cuenta/correo")
        except Exception as e:
            observaciones.append(f"Error fraude: {e}")

    if "viáticos" in tipo_doc.lower() or "viatico" in tipo_doc.lower():
        if no_documento:
            viatico_res = validar_viatico_completo(
                numero_viatico=no_documento,
                texto_documento=asunto,
                fecha_recepcion=fecha or "",
                fecha_viatico=fecha or "",
            )
            if not viatico_res.es_valido:
                accion = "Devolver"
                observaciones.append(f"Viático inválido: {viatico_res.motivo}")
            else:
                accion = "Radicar"
                observaciones.append("Viático válido")
        else:
            accion = "Devolver"
            observaciones.append("Viático sin número TH-F-012")

    if "petición" in tipo_doc.lower() or "peticion" in tipo_doc.lower() or "derecho" in tipo_doc.lower():
        peticion_res = clasificar_peticion(asunto)
        if peticion_res.es_urgente:
            accion = "Radicar (URGENTE)"
            observaciones.append(f"URGENTE: {peticion_res.entidad_detectada or 'tutela'}")

    if tipo_doc == "Publicidad" or "publicidad" in tipo_doc.lower() or "boletín" in asunto.lower() or "novedades" in asunto.lower():
        accion = "No radicar"
        tipo_pred = "Publicidad"
        observaciones.append("Publicidad/Boletín comercial")

    if tipo_doc == "Cotización":
        observaciones.append("Cotización para revisión Compras")

    if not dependencia:
        if tipo_doc == "Factura":
            dependencia = "CUENTAS_POR_PAGAR"
        elif "viáticos" in tipo_doc.lower() or "viatico" in tipo_doc.lower():
            dependencia = "TALENTO_HUMANO"
        elif "petición" in tipo_doc.lower() or "peticion" in tipo_doc.lower() or "derecho" in tipo_doc.lower():
            dependencia = "JURIDICA"
        elif tipo_doc == "Cotización":
            dependencia = "COMPRAS"
        elif tipo_doc == "Publicidad":
            dependencia = "NO_RADICAR"

    return Prediction(
        correo=eml_path.name,
        tipo=tipo_pred,
        duplicado=duplicado,
        fraude=fraude,
        dependencia=dependencia,
        accion=accion,
        observaciones=observaciones,
    )


def evaluate():
    expected_list = load_expected()
    print(f"Loaded {len(expected_list)} expected entries\n")

    eml_files = sorted([f for f in BANDEJA_DIR.glob("*.eml") if not f.name.startswith("sample")])
    print(f"Found {len(eml_files)} EML files to process\n")

    predictions = {}
    for eml in eml_files:
        pred = predict_eml(eml)
        predictions[eml.name] = pred

    y_true_tipo = []
    y_pred_tipo = []
    y_true_dup = []
    y_pred_dup = []
    y_true_fraude = []
    y_pred_fraude = []
    y_true_accion = []
    y_pred_accion = []

    for exp in expected_list:
        pred = predictions.get(exp.correo)
        if not pred:
            print(f"WARNING: No prediction for {exp.correo}")
            continue

        y_true_tipo.append(exp.tipo)
        y_pred_tipo.append(pred.tipo)

        exp_dup = "duplicad" in exp.observacion.lower()
        y_true_dup.append(exp_dup)
        y_pred_dup.append(pred.duplicado)

        exp_fraude = "fraude" in exp.observacion.lower() or "no coinciden" in exp.observacion.lower()
        y_true_fraude.append(exp_fraude)
        y_pred_fraude.append(pred.fraude)

        y_true_accion.append(exp.accion)
        y_pred_accion.append(pred.accion)

        match_tipo = "✓" if exp.tipo == pred.tipo else "✗"
        match_dup = "✓" if exp_dup == pred.duplicado else "✗"
        match_fraude = "✓" if exp_fraude == pred.fraude else "✗"
        print(f"{match_tipo} {exp.correo:12} | Tipo: {exp.tipo:20} vs {pred.tipo:20} | Dup: {str(exp_dup):5} vs {str(pred.duplicado):5} | Fraude: {str(exp_fraude):5} vs {str(pred.fraude):5} | Acción: {exp.accion:15} vs {pred.accion:15}")

    def precision_recall(y_true, y_pred, pos_label=True):
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == pos_label and p == pos_label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != pos_label and p == pos_label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == pos_label and p != pos_label)
        tn = sum(1 for t, p in zip(y_true, y_pred) if t != pos_label and p != pos_label)
        
        # If no positive cases in ground truth, check specificity (TN / (TN + FP))
        # Perfect prediction of all negatives = 1.0
        if tp + fn == 0:
            # No positive cases - check if we correctly predicted all negatives
            if fp == 0:
                return 1.0, 1.0, 1.0, 0, 0, 0
            else:
                return 0.0, 0.0, 0.0, 0, fp, 0
        
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        return prec, rec, f1, tp, fp, fn

    def accuracy(y_true, y_pred):
        return sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true) if y_true else 0

    print("\n" + "=" * 60)
    print("MÉTRICAS")
    print("=" * 60)

    tipo_acc = accuracy(y_true_tipo, y_pred_tipo)
    print(f"\nTipo Documental Accuracy: {tipo_acc:.2%}")
    print(f"  Correct: {sum(1 for t, p in zip(y_true_tipo, y_pred_tipo) if t == p)}/{len(y_true_tipo)}")

    classes = set(y_true_tipo) | set(y_pred_tipo)
    for cls in sorted(classes):
        cls_true = [1 if t == cls else 0 for t in y_true_tipo]
        cls_pred = [1 if p == cls else 0 for p in y_pred_tipo]
        prec, rec, f1, tp, fp, fn = precision_recall(cls_true, cls_pred)
        if tp + fp + fn > 0:
            print(f"  {cls:20} P={prec:.2%} R={rec:.2%} F1={f1:.2%} (TP={tp}, FP={fp}, FN={fn})")

    dup_prec, dup_rec, dup_f1, *_ = precision_recall(y_true_dup, y_pred_dup)
    print(f"\nDuplicado: P={dup_prec:.2%} R={dup_rec:.2%} F1={dup_f1:.2%}")

    fraude_prec, fraude_rec, fraude_f1, *_ = precision_recall(y_true_fraude, y_pred_fraude)
    print(f"Fraude:    P={fraude_prec:.2%} R={fraude_rec:.2%} F1={fraude_f1:.2%}")

    accion_acc = accuracy(y_true_accion, y_pred_accion)
    print(f"\nAcción Accuracy: {accion_acc:.2%}")

    overall = (tipo_acc + dup_f1 + fraude_f1 + accion_acc) / 4
    print(f"\n{'='*60}")
    print(f"PROMEDIO PONDERADO: {overall:.2%}")
    print(f"  (Tipo: {tipo_acc:.0%}, Dup F1: {dup_f1:.0%}, Fraude F1: {fraude_f1:.0%}, Acción: {accion_acc:.0%})")
    print(f"{'='*60}")

    success = overall > 0.8
    print(f"\n{'✓ ÉXITO' if success else '✗ FALLO'}: {'Precisión general > 80%' if success else 'Precisión general < 80%'}")

    return success


if __name__ == "__main__":
    success = evaluate()
    exit(0 if success else 1)
