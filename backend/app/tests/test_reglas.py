"""Comprehensive unit tests for business rules: duplicado, fraude, peticion plazos."""
import pytest
from datetime import date, datetime
from pathlib import Path

from app.application.services.reglas_factura import (
    es_duplicado,
    verificar_fraude_cuenta,
    verificar_fraude,
    _normalize_nit,
    _normalize_numero,
    _normalize_cuenta,
)
from app.application.services.reglas_peticion import (
    TipoPeticion,
    EntidadUrgente,
    clasificar_peticion,
)
from app.application.services.reglas_viaticos import (
    validar_formato_viatico,
    validar_firma,
    validar_antiguedad_5_dias,
    validar_viatico_completo,
    ResultadoViatico,
)
from app.application.services.vencimiento import (
    calcular_vencimiento_peticion,
    calcular_vencimiento_simple,
    es_dia_habil_colombia,
    obtener_festivos_colombia,
)


# Fixtures provided by conftest.py (data_dir, libro_path, maestro_path, etc.)


class TestNormalizacion:
    """Tests for normalization functions."""

    def test_normalize_nit_basic(self):
        assert _normalize_nit("860.555.444-3") == "8605554443"
        assert _normalize_nit("901.234.567-1") == "9012345671"

    def test_normalize_nit_with_spaces(self):
        assert _normalize_nit(" 860.555.444-3 ") == "8605554443"
        assert _normalize_nit("860 555 444 3") == "8605554443"

    def test_normalize_nit_empty(self):
        assert _normalize_nit("") == ""
        assert _normalize_nit("   ") == ""

    def test_normalize_numero_basic(self):
        assert _normalize_numero("FE-1207") == "FE-1207"
        assert _normalize_numero("SE-77790") == "SE-77790"

    def test_normalize_numero_case_spaces(self):
        assert _normalize_numero(" fe-1207 ") == "FE-1207"
        assert _normalize_numero("Fe-1207") == "FE-1207"

    def test_normalize_cuenta(self):
        assert _normalize_cuenta("123-45678-9") == "123456789"
        assert _normalize_cuenta(" 123-45678-9 ") == "123456789"
        assert _normalize_cuenta("123.45678.9") == "123456789"
        assert _normalize_cuenta("123 45678 9") == "123456789"


class TestEsDuplicado:
    """Tests for duplicate factura detection using real libro data."""

    def test_duplicado_existente(self, libro_path):
        """Test detection of existing factura in libro radicacion."""
        es_dup, radicado, motivo = es_duplicado("860.555.444-3", "FE-1207", libro_path)
        assert es_dup is True
        assert radicado == "TAC-2026-ER-04790"
        assert "Duplicado" in motivo

    def test_duplicado_case_insensitive(self, libro_path):
        """Test duplicate detection is case/space insensitive."""
        es_dup, radicado, _ = es_duplicado(" 860.555.444-3 ", " fe-1207 ", libro_path)
        assert es_dup is True
        assert radicado == "TAC-2026-ER-04790"

    def test_no_duplicado_nit_nuevo(self, libro_path):
        """Test non-duplicate with new NIT."""
        es_dup, radicado, motivo = es_duplicado("999.999.999-9", "NEW-001", libro_path)
        assert es_dup is False
        assert radicado is None
        assert "No existe" in motivo or "no encontrado" in motivo.lower()

    def test_no_duplicado_nit_existente_numero_nuevo(self, libro_path):
        """Test non-duplicate with existing NIT but new numero."""
        es_dup, radicado, motivo = es_duplicado("860.555.444-3", "NONEXISTENT", libro_path)
        assert es_dup is False
        assert radicado is None

    def test_duplicado_otro_existente(self, libro_path):
        """Test another existing factura from libro."""
        es_dup, radicado, _ = es_duplicado("900.876.543-5", "SE-77790", libro_path)
        assert es_dup is True
        assert radicado == "TAC-2026-ER-04791"

    def test_duplicado_campos_vacios(self, libro_path):
        """Test empty NIT/numero returns False."""
        es_dup, _, motivo = es_duplicado("", "FE-1207", libro_path)
        assert es_dup is False
        assert "NIT vacío" in motivo or "vacío" in motivo.lower()

        es_dup, _, motivo = es_duplicado("860.555.444-3", "", libro_path)
        assert es_dup is False
        assert "Número de factura vacío" in motivo or "vacío" in motivo.lower()

    def test_libro_no_existe(self):
        """Test handling of non-existent libro file."""
        es_dup, _, motivo = es_duplicado("860.555.444-3", "FE-1207", "/nonexistent/path.xlsx")
        assert es_dup is False
        assert "no encontrado" in motivo.lower() or "vacío" in motivo.lower()


class TestFraudeCuenta:
    """Tests for fraud detection on bank account and email using real maestro data."""

    def test_fraude_cuenta_no_coincide(self, maestro_path):
        """Test fraud when account doesn't match maestro."""
        es_fraude, motivo, accion = verificar_fraude_cuenta(
            "860.555.444-3", "999-99999-9", "fe@papeleriacolombia.example", maestro_path
        )
        assert es_fraude is True
        assert "Cuenta no coincide" in motivo
        assert accion.value == "JURIDICA"

    def test_fraude_correo_no_coincide(self, maestro_path):
        """Test fraud when email doesn't match maestro."""
        es_fraude, motivo, accion = verificar_fraude_cuenta(
            "860.555.444-3", "987-65432-1", "hacker@malicious.com", maestro_path
        )
        assert es_fraude is True
        assert "Correo no coincide" in motivo
        assert accion.value == "JURIDICA"

    def test_ok_cuenta_y_correo_coinciden(self, maestro_path):
        """Test OK when both account and email match."""
        es_fraude, motivo, accion = verificar_fraude_cuenta(
            "860.555.444-3", "987-65432-1", "fe@papeleriacolombia.example", maestro_path
        )
        assert es_fraude is False
        assert "OK" in motivo
        assert accion.value == "CUENTAS_POR_PAGAR"

    def test_ok_cuenta_formato_diferente(self, maestro_path):
        """Test OK when account format differs but numbers match."""
        es_fraude, motivo, accion = verificar_fraude_cuenta(
            "860.555.444-3", "987 65432 1", "fe@papeleriacolombia.example", maestro_path
        )
        assert es_fraude is False
        assert accion.value == "CUENTAS_POR_PAGAR"

    def test_fraude_proveedor_inactivo(self, maestro_path):
        """Test fraud when provider is inactive (Vigilancia Técnica)."""
        es_fraude, motivo, accion = verificar_fraude_cuenta(
            "800.777.666-1", "220-11122-3", "contabilidad@vigiandina.example", maestro_path
        )
        assert es_fraude is True
        assert "inactivo" in motivo.lower()
        assert accion.value == "JURIDICA"

    def test_fraude_nit_no_existe(self, maestro_path):
        """Test handling when NIT not in maestro."""
        es_fraude, motivo, accion = verificar_fraude_cuenta(
            "999.999.999-9", "123-45678-9", "test@test.com", maestro_path
        )
        assert es_fraude is False
        assert "no encontrado" in motivo.lower()
        assert accion.value == "JURIDICA"

    def test_fraude_cuenta_vacia_factura(self, maestro_path):
        """Test OK when account empty in factura (skips check)."""
        es_fraude, motivo, accion = verificar_fraude_cuenta(
            "860.555.444-3", "", "fe@papeleriacolombia.example", maestro_path
        )
        assert es_fraude is False
        assert accion.value == "CUENTAS_POR_PAGAR"

    def test_fraude_correo_vacio_factura(self, maestro_path):
        """Test OK when email empty in factura (skips check)."""
        es_fraude, motivo, accion = verificar_fraude_cuenta(
            "860.555.444-3", "987-65432-1", "", maestro_path
        )
        assert es_fraude is False
        assert accion.value == "CUENTAS_POR_PAGAR"


class TestVerificarFraudeWrapper:
    """Tests for the convenience wrapper function with default path."""

    def test_verificar_fraude_cuenta_distinta(self):
        """Test wrapper with different account."""
        es_fraude, motivo, dep = verificar_fraude(
            "860.555.444-3", "999-99999-9", "fe@papeleriacolombia.example"
        )
        assert es_fraude is True
        assert dep.value == "JURIDICA"

    def test_verificar_fraude_correo_raro(self):
        """Test wrapper with suspicious email."""
        es_fraude, motivo, dep = verificar_fraude(
            "860.555.444-3", "987-65432-1", "hacker@malicious.com"
        )
        assert es_fraude is True
        assert dep.value == "JURIDICA"

    def test_verificar_fraude_todo_ok(self):
        """Test wrapper with everything matching."""
        es_fraude, motivo, dep = verificar_fraude(
            "860.555.444-3", "987-65432-1", "fe@papeleriacolombia.example"
        )
        assert es_fraude is False
        assert dep.value == "CUENTAS_POR_PAGAR"


class TestPeticionTipo:
    """Tests for petition type classification and deadlines."""

    def test_tipo_peticion_plazos(self):
        """Test each petition type has correct deadline in business days."""
        assert TipoPeticion.GENERAL.plazo_dias_habiles == 15
        assert TipoPeticion.COPIAS.plazo_dias_habiles == 10
        assert TipoPeticion.CONSULTA.plazo_dias_habiles == 30
        assert TipoPeticion.COPIAS_OTRAS.plazo_dias_habiles == 15

    def test_tipo_peticion_valores(self):
        """Test enum values."""
        assert TipoPeticion.GENERAL.value == "general"
        assert TipoPeticion.COPIAS.value == "copias"
        assert TipoPeticion.CONSULTA.value == "consulta"
        assert TipoPeticion.COPIAS_OTRAS.value == "copias_otras"


class TestEntidadUrgente:
    """Tests for urgent entity detection."""

    def test_detectar_contraloria(self):
        """Test Contraloría detection (with accent)."""
        texto = "Oficio de la Contraloría General"
        detectadas = EntidadUrgente.detectar_en_texto(texto)
        assert EntidadUrgente.CONTRALORIA in detectadas

    def test_detectar_procuraduria(self):
        """Test Procuraduría detection (with accent)."""
        texto = "Requerimiento de la Procuraduría"
        detectadas = EntidadUrgente.detectar_en_texto(texto)
        assert EntidadUrgente.PROCURADURIA in detectadas

    def test_detectar_personeria(self):
        """Test Personería detection (with accent)."""
        texto = "Oficio de la Personería"
        detectadas = EntidadUrgente.detectar_en_texto(texto)
        assert EntidadUrgente.PERSONERIA in detectadas

    def test_detectar_juzgado(self):
        """Test Juzgado detection."""
        texto = "Juzgado Primero Civil"
        detectadas = EntidadUrgente.detectar_en_texto(texto)
        assert EntidadUrgente.JUZGADO in detectadas

    def test_no_detectar_texto_normal(self):
        """Test normal text doesn't trigger detection."""
        texto = "Petición normal sin entidades de control"
        detectadas = EntidadUrgente.detectar_en_texto(texto)
        assert len(detectadas) == 0

    def test_detectar_case_insensitive(self):
        """Test case insensitive detection."""
        texto = "CONTRALORIA general de la republica"
        detectadas = EntidadUrgente.detectar_en_texto(texto)
        assert EntidadUrgente.CONTRALORIA in detectadas

    def test_detectar_multiples(self):
        """Test detection of multiple entities."""
        texto = "Oficio de la Contraloría y la Procuraduría"
        detectadas = EntidadUrgente.detectar_en_texto(texto)
        assert EntidadUrgente.CONTRALORIA in detectadas
        assert EntidadUrgente.PROCURADURIA in detectadas


class TestClasificarPeticion:
    """Tests for petition classification and urgency detection."""

    def test_clasificar_general_por_defecto(self):
        """Test default classification is general."""
        config = clasificar_peticion("Petición cualquiera")
        assert config.tipo == TipoPeticion.GENERAL
        assert config.plazo_dias_habiles == 15

    def test_clasificar_copias(self):
        """Test copies classification."""
        config = clasificar_peticion("Solicitud de copias simples")
        assert config.tipo == TipoPeticion.COPIAS
        assert config.plazo_dias_habiles == 10

    def test_clasificar_copias_otras(self):
        """Test copies and others classification."""
        config = clasificar_peticion("Copias y otros documentos")
        assert config.tipo == TipoPeticion.COPIAS_OTRAS
        assert config.plazo_dias_habiles == 15

    def test_clasificar_consulta(self):
        """Test consultation classification."""
        config = clasificar_peticion("Consulta sobre trámite")
        assert config.tipo == TipoPeticion.CONSULTA
        assert config.plazo_dias_habiles == 30

    def test_urgente_tutela_palabra_clave(self):
        """Test tutela keyword triggers urgent."""
        config = clasificar_peticion("Acción de tutela", "Interpongo acción de tutela")
        assert config.es_urgente is True
        assert config.palabra_clave_tutela is True

    def test_urgente_entidad_control(self):
        """Test control entity triggers urgent."""
        config = clasificar_peticion("Requerimiento Contraloría", "", "contraloria@gov.co")
        assert config.es_urgente is True
        assert config.entidad_detectada == EntidadUrgente.CONTRALORIA

    def test_no_urgente_normal(self):
        """Test normal petition not urgent."""
        config = clasificar_peticion("Petición general", "Solicito información")
        assert config.es_urgente is False
        assert config.entidad_detectada is None
        assert config.palabra_clave_tutela is False


class TestCalcularVencimientoPeticion:
    """Tests for deadline calculation using habilmente."""

    def test_general_recibida_viernes(self):
        """Test general petition received Friday -> starts Monday."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=date(2024, 11, 22),  # Friday
            tipo_peticion="general"
        )
        assert resultado.fecha_recepcion == date(2024, 11, 22)
        assert resultado.fecha_inicio_plazo == date(2024, 11, 25)  # Monday
        assert resultado.fecha_vencimiento == date(2024, 12, 13)
        assert resultado.plazo_dias_habiles == 15
        assert resultado.es_urgente is False

    def test_general_recibida_lunes(self):
        """Test general petition received Monday -> starts Tuesday."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=date(2024, 11, 25),  # Monday
            tipo_peticion="general"
        )
        assert resultado.fecha_inicio_plazo == date(2024, 11, 26)  # Tuesday

    def test_general_recibida_sabado(self):
        """Test Saturday receipt -> starts Monday."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=date(2024, 11, 23),  # Saturday
            tipo_peticion="general"
        )
        assert resultado.fecha_inicio_plazo == date(2024, 11, 25)  # Monday
        assert "no hábil" in resultado.observaciones.lower()

    def test_general_recibida_domingo(self):
        """Test Sunday receipt -> starts Monday."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=date(2024, 11, 24),  # Sunday
            tipo_peticion="general"
        )
        assert resultado.fecha_inicio_plazo == date(2024, 11, 25)  # Monday

    def test_copias_10_dias(self):
        """Test copies petition 10 business days."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=date(2024, 11, 20),  # Wednesday
            tipo_peticion="copias"
        )
        assert resultado.plazo_dias_habiles == 10
        assert resultado.fecha_vencimiento == date(2024, 12, 4)

    def test_consulta_30_dias(self):
        """Test consultation petition 30 business days."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=date(2024, 11, 20),  # Wednesday
            tipo_peticion="consulta"
        )
        assert resultado.plazo_dias_habiles == 30
        assert resultado.fecha_vencimiento >= date(2025, 1, 1)

    def test_copias_otras_15_dias(self):
        """Test copies others 15 business days."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=date(2024, 11, 22),  # Friday
            tipo_peticion="copias_otras"
        )
        assert resultado.plazo_dias_habiles == 15
        assert resultado.fecha_vencimiento == date(2024, 12, 13)

    def test_urgente_tutela_marca_flag(self):
        """Test tutela petition marks urgent flag."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=date(2024, 11, 22),
            tipo_peticion="general",
            asunto="Acción de tutela",
            cuerpo="Derechos fundamentales violados"
        )
        assert resultado.es_urgente is True
        assert resultado.tutela_detectada is True
        assert "tutela" in resultado.observaciones.lower()

    def test_urgente_contraloria_marca_flag(self):
        """Test Contraloría petition marks urgent flag."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=date(2024, 11, 21),  # Thursday
            tipo_peticion="general",
            asunto="Requerimiento Contraloría",
            cuerpo="Oficio de la Contraloría General"
        )
        assert resultado.es_urgente is True
        assert resultado.entidad_detectada == "contraloria"
        assert "contraloria" in resultado.observaciones.lower()

    def test_urgente_procuraduria_marca_flag(self):
        """Test Procuraduría petition marks urgent flag."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=date(2024, 11, 21),
            tipo_peticion="general",
            asunto="Requerimiento Procuraduría",
            remitente="procuraduria@gov.co"
        )
        assert resultado.es_urgente is True
        assert resultado.entidad_detectada == "procuraduria"

    def test_urgente_personeria_marca_flag(self):
        """Test Personería petition marks urgent flag."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=date(2024, 11, 21),
            tipo_peticion="general",
            asunto="Oficio Personería"
        )
        assert resultado.es_urgente is True
        assert resultado.entidad_detectada == "personeria"

    def test_urgente_juzgado_marca_flag(self):
        """Test Juzgado petition marks urgent flag."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=date(2024, 11, 21),
            tipo_peticion="general",
            asunto="Juzgado Civil"
        )
        assert resultado.es_urgente is True
        assert resultado.entidad_detectada == "juzgado"

    def test_datetime_input(self):
        """Test datetime input works."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=datetime(2024, 11, 22, 14, 30),  # Friday 2:30 PM
            tipo_peticion="general"
        )
        assert resultado.fecha_recepcion == date(2024, 11, 22)
        assert resultado.fecha_inicio_plazo == date(2024, 11, 25)

    def test_tipo_explicito_override(self):
        """Test explicit tipo_peticion overrides classification."""
        resultado = calcular_vencimiento_peticion(
            fecha_recepcion=date(2024, 11, 20),
            tipo_peticion="copias",  # Explicit: 10 days
            asunto="Consulta sobre copias"  # Would classify as consulta
        )
        assert resultado.tipo_peticion == "copias"
        assert resultado.plazo_dias_habiles == 10


class TestCalcularVencimientoSimple:
    """Tests for simple deadline calculation."""

    def test_simple_15_dias(self):
        """Test simple 15 business days from Friday."""
        venc = calcular_vencimiento_simple(date(2024, 11, 22), 15)
        assert venc == date(2024, 12, 13)

    def test_simple_10_dias(self):
        """Test simple 10 business days from Wednesday."""
        venc = calcular_vencimiento_simple(date(2024, 11, 20), 10)
        assert venc == date(2024, 12, 4)

    def test_simple_1_dia(self):
        """Test simple 1 business day."""
        venc = calcular_vencimiento_simple(date(2024, 11, 22), 1)  # Friday
        assert venc == date(2024, 11, 25)  # Monday


class TestUtilidadesFestivos:
    """Tests for holiday utilities using habilmente."""

    def test_es_dia_habil_lunes(self):
        """Test Monday is business day."""
        assert es_dia_habil_colombia(date(2024, 11, 25)) is True

    def test_es_dia_habil_sabado(self):
        """Test Saturday is not business day."""
        assert es_dia_habil_colombia(date(2024, 11, 23)) is False

    def test_es_dia_habil_domingo(self):
        """Test Sunday is not business day."""
        assert es_dia_habil_colombia(date(2024, 11, 24)) is False

    def test_obtener_festivos_2024(self):
        """Test getting 2024 holidays."""
        festivos = obtener_festivos_colombia(2024)
        assert len(festivos) > 0
        assert date(2024, 1, 1) in festivos  # Año Nuevo
        assert date(2024, 5, 1) in festivos  # Día del Trabajo

    def test_festivo_no_es_dia_habil(self):
        """Test holiday is not business day."""
        # Jueves Santo 2024
        assert es_dia_habil_colombia(date(2024, 3, 28)) is False
        # Viernes Santo 2024
        assert es_dia_habil_colombia(date(2024, 3, 29)) is False


class TestViaticosFormato:
    """Tests for viatico TH-F-012 format validation."""

    def test_formato_valido_vi_guion(self):
        """Test valid VI-YYYY-NNNN format."""
        valido, motivo = validar_formato_viatico("VI-2026-0001")
        assert valido is True
        assert "valido" in motivo.lower()

    def test_formato_valido_viatico_guion(self):
        """Test valid VIATICO-YYYY-NNNNN format."""
        valido, motivo = validar_formato_viatico("VIATICO-2026-12345")
        assert valido is True

    def test_formato_valido_via_tico_guion(self):
        """Test valid VIÁTICO-YYYY-NNNN format."""
        valido, _ = validar_formato_viatico("VIÁTICO-2026-0999")
        assert valido is True

    def test_formato_valido_case_insensitive(self):
        """Test format is case insensitive."""
        valido, _ = validar_formato_viatico("vi-2026-0001")
        assert valido is True
        valido, _ = validar_formato_viatico("ViAtIcO-2026-0001")
        assert valido is True

    def test_formato_invalido_vacio(self):
        """Test empty viatico number."""
        valido, motivo = validar_formato_viatico("")
        assert valido is False
        assert "vacío" in motivo.lower() or "vacio" in motivo.lower()

    def test_formato_invalido_sin_guion(self):
        """Test missing dashes."""
        valido, _ = validar_formato_viatico("VI20260001")
        assert valido is False

    def test_formato_invalido_anio_corto(self):
        """Test year too short."""
        valido, _ = validar_formato_viatico("VI-26-0001")
        assert valido is False

    def test_formato_invalido_numero_corto(self):
        """Test numero too short."""
        valido, _ = validar_formato_viatico("VI-2026-12")
        assert valido is False


class TestViaticosFirma:
    """Tests for viatico firma (signature) detection."""

    def test_firma_presente(self):
        """Test firma pattern detected."""
        valido, motivo = validar_firma("Firma: Juan Perez")
        assert valido is True
        assert "presente" in motivo.lower()

    def test_firmado_por(self):
        """Test firmado por pattern."""
        valido, _ = validar_firma("firmado por Maria Gomez")
        assert valido is True

    def test_aprobado_por(self):
        """Test aprobado por pattern."""
        valido, _ = validar_firma("aprobado por Carlos Ruiz")
        assert valido is True

    def test_autorizado_por(self):
        """Test autorizado por pattern."""
        valido, _ = validar_firma("autorizado por Ana Lopez")
        assert valido is True

    def test_firma_no_presente(self):
        """Test no firma pattern."""
        valido, motivo = validar_firma("Este es un texto sin firma")
        assert valido is False
        assert "sin firma" in motivo.lower()

    def test_firma_vacio(self):
        """Test empty text."""
        valido, _ = validar_firma("")
        assert valido is False

    def test_firma_solo_espacios(self):
        """Test whitespace only text."""
        valido, _ = validar_firma("   ")
        assert valido is False


class TestViaticosAntiguedad5Dias:
    """Tests for viatico 5-business-days rule."""

    def test_dentro_5_dias_valido(self):
        """Test 5 days before trip is valid."""
        from datetime import date
        valido, motivo = validar_antiguedad_5_dias(
            date(2026, 11, 20),  # recepcion
            date(2026, 11, 25),  # viaje (5 dias despues)
        )
        assert valido is True

    def test_exacto_5_dias(self):
        """Test exactly 5 days is valid."""
        valido, _ = validar_antiguedad_5_dias(
            date(2026, 11, 20),
            date(2026, 11, 25),
        )
        assert valido is True

    def test_excede_6_dias(self):
        """Test more than 5 days is valid."""
        valido, _ = validar_antiguedad_5_dias(
            date(2026, 11, 20),
            date(2026, 11, 27),
        )
        assert valido is True

    def test_menos_de_5_dias_invalido(self):
        """Test less than 5 days is invalid."""
        valido, motivo = validar_antiguedad_5_dias(
            date(2026, 11, 22),
            date(2026, 11, 25),
        )
        assert valido is False

    def test_recepcion_antes_viatico(self):
        """Test recepcion date before viatico date is invalid."""
        valido, motivo = validar_antiguedad_5_dias(
            date(2026, 11, 26),
            date(2026, 11, 25),
        )
        assert valido is False

    def test_mismo_dia(self):
        """Test same day is invalid."""
        valido, _ = validar_antiguedad_5_dias(
            date(2026, 11, 25),
            date(2026, 11, 25),
        )
        assert valido is False

    def test_datetime_objects(self):
        """Test datetime input works."""
        from datetime import datetime
        valido, _ = validar_antiguedad_5_dias(
            datetime(2026, 11, 20, 9, 0),
            datetime(2026, 11, 26, 9, 0),
        )
        assert valido is True


class TestViaticoCompleto:
    """Tests for complete viatico validation."""

    def test_viatico_valido_completo(self):
        """Test all validations pass."""
        resultado = validar_viatico_completo(
            numero_viatico="VI-2026-0001",
            texto_documento="Firma: Juan Perez, aprobado por el jefe",
            fecha_recepcion=date(2026, 11, 20),
            fecha_viatico=date(2026, 11, 26),
        )
        assert resultado.es_valido is True
        assert "valido" in resultado.motivo.lower()

    def test_viatico_formato_invalido(self):
        """Test invalid formato fails complete validation."""
        resultado = validar_viatico_completo(
            numero_viatico="INVALIDO",
            texto_documento="Firma: Juan Perez",
            fecha_recepcion=date(2026, 11, 20),
            fecha_viatico=date(2026, 11, 26),
        )
        assert resultado.es_valido is False

    def test_viatico_sin_firma(self):
        """Test missing firma fails complete validation."""
        resultado = validar_viatico_completo(
            numero_viatico="VI-2026-0001",
            texto_documento="Sin firma ni aprobacion",
            fecha_recepcion=date(2026, 11, 20),
            fecha_viatico=date(2026, 11, 26),
        )
        assert resultado.es_valido is False

    def test_viatico_excede_5_dias(self):
        """Test less than 5 days fails complete validation."""
        resultado = validar_viatico_completo(
            numero_viatico="VI-2026-0001",
            texto_documento="Firma: Juan Perez",
            fecha_recepcion=date(2026, 11, 23),
            fecha_viatico=date(2026, 11, 25),
        )
        assert resultado.es_valido is False

    def test_viatico_recepcion_antes(self):
        """Test recepcion before viatico fails."""
        resultado = validar_viatico_completo(
            numero_viatico="VI-2026-0001",
            texto_documento="Firma: Juan Perez",
            fecha_recepcion=date(2026, 11, 26),
            fecha_viatico=date(2026, 11, 25),
        )
        assert resultado.es_valido is False

    def test_viatico_limite_exacto_5_dias(self):
        """Test exactly 5 days passes complete validation."""
        resultado = validar_viatico_completo(
            numero_viatico="VI-2026-0001",
            texto_documento="Firma: Juan Perez",
            fecha_recepcion=date(2026, 11, 20),
            fecha_viatico=date(2026, 11, 25),
        )
        assert resultado.es_valido is True

    def test_resultado_viatico_creation(self):
        """Test ResultadoViatico dataclass."""
        r = ResultadoViatico(es_valido=True, motivo="OK", observaciones=["obs1"])
        assert r.es_valido is True
        assert r.motivo == "OK"
        assert r.observaciones == ["obs1"]

        r2 = ResultadoViatico(es_valido=False, motivo="Fail")
        assert r2.observaciones == []