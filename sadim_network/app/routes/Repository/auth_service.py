import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Repository.user_crud import get_by_email, verify_password

from models.user import User

# ---------- AUTHENTICATE USER ----------
def authenticate(email: str, password: str, role: str = None) -> User | None:
    """""مصادقة المستخدم بناءً على البريد الإلكتروني وكلمة المرور والدور الاختياري"""
    user = get_by_email(email)
    if user and verify_password(user.password_hash, password):
        if role is None or user.role == role:
            return user
    return None

# ---------- AUTHENTICATE ADMIN ----------
def authenticate_admin(email: str, password: str) -> User | None:
    """""مصادقة المسؤول بناءً على البريد الإلكتروني وكلمة المرور"""
    return authenticate(email, password, role='admin')

