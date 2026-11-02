
from pydantic import BaseModel, Field, field_validator


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    mot_de_passe: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if value.count("@") != 1 or any(char.isspace() for char in value):
            raise ValueError("Adresse email invalide.")
        local, domain = value.split("@")
        if not local or not domain:
            raise ValueError("Adresse email invalide.")
        return value

    @field_validator("mot_de_passe")
    @classmethod
    def password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Le mot de passe ne doit pas dépasser 72 octets UTF-8.")
        return value


class UserCreate(Credentials):
    pass


class LoginRequest(Credentials):
    pass


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
