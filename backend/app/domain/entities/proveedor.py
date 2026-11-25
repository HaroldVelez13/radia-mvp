from pydantic import BaseModel

class Proveedor(BaseModel):
    nit: str
    nombre: str
    cuenta_bancaria: str
    email_registrado: str
