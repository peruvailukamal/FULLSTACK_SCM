from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re
class UserSchema(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr = Field(...)
    # This definition allows any string as long as it is 3+ chars
    password: str = Field(..., min_length=3) 
    # Admin fields (not provided by regular signup, but present in DB)
    is_admin: bool = False
    admin_request_status: Optional[str] = "none"  # none | pending | approved | rejected
    admin_requested_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "username": "scm_admin", 
                "email": "admin@scm.com",
                "password": "strongpassword"
            }
        }

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """
        Enforces password policy:
        - Min 8 characters
        - At least 1 Uppercase
        - At least 1 Digit
        - At least 1 Special Character (@$!%*?&)
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[@$!%*?&]', v):
            raise ValueError('Password must contain at least one special character (@$!%*?&)')
        return v
    
class UserLoginSchema(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)

class ForgotPasswordSchema(BaseModel):
    email: EmailStr

class VerifyOTPSchema(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordSchema(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(..., min_length=8)