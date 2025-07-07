from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError

from core.config import get_settings

settings = get_settings()

# This scheme is used by FastAPI to find the "Authorization" header.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

class User(BaseModel):
    id: str # Corresponds to the 'sub' (subject) claim in the Supabase JWT
    email: str
    role: str

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        # Extract user details from the JWT payload
        user_data = {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
        if user_data["id"] is None or user_data["email"] is None:
             raise credentials_exception
        
        user = User(**user_data)
        return user
        
    except (JWTError, ValidationError):
        raise credentials_exception