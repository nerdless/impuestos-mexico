from pydantic import BaseModel

class Localconfig(BaseModel):
    host: str
    user: str
    password: str
    db: str