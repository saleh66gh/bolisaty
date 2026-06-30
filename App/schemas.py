from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ==================================
# USERS
# ==================================

class UserCreate(BaseModel):
    full_name: str
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str
    role: str
    store_id: Optional[int] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    username: str
    email: Optional[str]
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    store_id: Optional[int] = None

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
# ==================================
# SENDERS
# ==================================

class SenderCreate(BaseModel):
    merchant_name: str
    store_name: str
    store_phone: str
    store_id: Optional[int] = None
    merchant_city: Optional[str] = None
    merchant_district: Optional[str] = None
    merchant_address: Optional[str] = None
    merchant_national_address: Optional[str] = None

    store_logo: Optional[str] = None
    sender_branch: Optional[str] = None


class SenderUpdate(BaseModel):
    merchant_name: Optional[str] = None
    store_name: Optional[str] = None
    store_phone: Optional[str] = None
    store_id: Optional[int] = None
    merchant_city: Optional[str] = None
    merchant_district: Optional[str] = None
    merchant_address: Optional[str] = None
    merchant_national_address: Optional[str] = None

    store_logo: Optional[str] = None
    sender_branch: Optional[str] = None

    is_active: Optional[bool] = None


class SenderResponse(BaseModel):
    id: int
    store_id: Optional[int] = None
    merchant_name: str
    store_name: str
    store_phone: str

    merchant_city: Optional[str]
    merchant_district: Optional[str]
    merchant_address: Optional[str]
    merchant_national_address: Optional[str]

    store_logo: Optional[str]
    sender_branch: Optional[str]

    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================================
# LABELS
# ==================================

class LabelUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None

    customer_city: Optional[str] = None
    customer_district: Optional[str] = None
    customer_address: Optional[str] = None
    customer_short_address: Optional[str] = None

    payment_method: Optional[str] = None
    cod_amount: Optional[float] = None

    shipment_count: Optional[str] = None
    weight: Optional[str] = None

    status: Optional[str] = None


class LabelResponse(BaseModel):
    id: int
    store_id: Optional[int]
    order_number: str

    customer_name: str
    customer_phone: str

    customer_city: Optional[str]
    customer_district: Optional[str]
    customer_address: Optional[str]
    customer_short_address: Optional[str]

    sender_id: Optional[int]
    user_id: Optional[int]

    products_json: Optional[str]

    payment_method: str
    cod_amount: float

    shipment_count: Optional[str]
    weight: Optional[str]

    pdf_path: Optional[str]
    html_path: Optional[str]

    status: str
    default_template_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ==================================
# STORES
# ==================================

class StoreCreate(BaseModel):
    account_number: str
    store_name: str
    owner_name: str
    email: Optional[str] = None
    phone: Optional[str] = None

    subscription_plan: str = "trial"
    subscription_status: str = "active"
    label_limit: int = 100
    store_logo: Optional[str] = None
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None


class StoreUpdate(BaseModel):
    store_name: Optional[str] = None
    owner_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    label_limit: Optional[int] = None
    labels_used: Optional[int] = None

    salla_store_id: Optional[str] = None
    salla_connected: Optional[bool] = None
    salla_access_token: Optional[str] = None
    salla_refresh_token: Optional[str] = None

    is_active: Optional[bool] = None
    store_logo: Optional[str] = None
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    default_template_id: Optional[int] = None

class StoreResponse(BaseModel):
    id: int
    account_number: str
    store_name: str
    owner_name: str
    email: Optional[str]
    phone: Optional[str]

    subscription_plan: str
    subscription_status: str
    label_limit: int
    labels_used: int

    salla_store_id: Optional[str]
    salla_connected: bool
    subscription_plan: str
    subscription_status: str
    label_limit: int
    labels_used: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    api_key: Optional[str] = None
    default_template_id: Optional[int] = None

    class Config:
        from_attributes = True

class CurrentUserResponse(BaseModel):
    id: int
    full_name: str
    username: str
    role: str
    store_id: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True

class StoreFullCreate(BaseModel):
    store: StoreCreate
    owner: UserCreate
    sender: SenderCreate


# ==================================
# LABEL TEMPLATES
# ==================================

class LabelTemplateCreate(BaseModel):
    name: str
    html_code: str


class LabelTemplateUpdate(BaseModel):
    name: Optional[str] = None
    html_code: Optional[str] = None
    is_active: Optional[bool] = None


class LabelTemplateResponse(BaseModel):
    id: int
    name: str
    html_code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True