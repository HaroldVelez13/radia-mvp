"""Pytest configuration and fixtures."""
import pytest
from pathlib import Path


@pytest.fixture
def data_dir() -> Path:
    """Return the data directory path."""
    # In container (docker run -v $(pwd):/app), data is at /app/data
    container_path = Path("/app/data")
    if container_path.exists():
        return container_path
    # Fallback for local development: conftest.py is at backend/app/tests/conftest.py
    # Go up 4 levels to reach radia-mvp root, then data/
    return Path(__file__).parent.parent.parent.parent / "data"


@pytest.fixture
def bandeja_dir(data_dir) -> Path:
    """Return the bandeja directory path."""
    return data_dir / "bandeja"


@pytest.fixture
def maestro_dir(data_dir) -> Path:
    """Return the maestro directory path."""
    return data_dir / "maestro"


@pytest.fixture
def libro_dir(data_dir) -> Path:
    """Return the libro directory path."""
    return data_dir / "libro"


@pytest.fixture
def libro_path(libro_dir) -> Path:
    """Return the libro radicacion Excel path."""
    return libro_dir / "libro-radicacion-2026.xlsx"


@pytest.fixture
def maestro_path(maestro_dir) -> Path:
    """Return the maestro proveedores CSV path."""
    return maestro_dir / "maestro-proveedores.csv"


@pytest.fixture
def dependencias_path(maestro_dir) -> Path:
    """Return the dependencias CSV path."""
    return maestro_dir / "dependencias.csv"
