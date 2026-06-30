from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Float,
    ForeignKey
)
from sqlalchemy.orm import relationship

from App.database import Base
class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)

    account_number = Column(String, unique=True, nullable=False, index=True)  # 5 digits

    store_name = Column(String, nullable=False)
    owner_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    subscription_plan = Column(String, default="trial")
    subscription_status = Column(String, default="active")

    label_limit = Column(Integer, default=100)
    labels_used = Column(Integer, default=0)

    salla_store_id = Column(String, nullable=True)
    salla_connected = Column(Boolean, default=False)
    salla_access_token = Column(Text, nullable=True)
    salla_refresh_token = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    store_logo = Column(String, nullable=True)

    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    users = relationship("User", back_populates="store")
    senders = relationship("Sender", back_populates="store")
    labels = relationship("Label", back_populates="store")
    api_key = Column(String, unique=True, nullable=True, index=True)
    default_template_id = Column(Integer, ForeignKey("label_templates.id"), nullable=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=True, index=True)
    phone = Column(String, nullable=True)

    password_hash = Column(String, nullable=False)

    role = Column(String, default="owner")  # owner / admin / staff
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    labels = relationship("Label", back_populates="user")
    last_login = Column(DateTime, nullable=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)
    store = relationship("Store", back_populates="users")
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    updated_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

class Sender(Base):
    __tablename__ = "senders"

    id = Column(Integer, primary_key=True, index=True)

    merchant_name = Column(String, nullable=False)
    store_name = Column(String, nullable=False)
    store_phone = Column(String, nullable=False)

    merchant_city = Column(String, nullable=True)
    merchant_district = Column(String, nullable=True)
    merchant_address = Column(Text, nullable=True)
    merchant_national_address = Column(String, nullable=True)

    store_logo = Column(String, nullable=True)
    sender_branch = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    labels = relationship("Label", back_populates="sender")
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)
    store = relationship("Store", back_populates="senders")

class Label(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)

    order_number = Column(String, nullable=False, index=True)

    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False, index=True)

    customer_city = Column(String, nullable=True)
    customer_district = Column(String, nullable=True)
    customer_address = Column(Text, nullable=True)
    customer_short_address = Column(String, nullable=True)

    sender_id = Column(Integer, ForeignKey("senders.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    products_json = Column(Text, nullable=True)

    payment_method = Column(String, nullable=False, default="paid")  # paid / cash
    cod_amount = Column(Float, default=0)

    shipment_count = Column(String, nullable=True)
    weight = Column(String, nullable=True)

    pdf_path = Column(String, nullable=True)
    html_path = Column(String, nullable=True)

    status = Column(String, default="created")  # created / failed / deleted

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("Sender", back_populates="labels")
    user = relationship("User", back_populates="labels")
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)
    store = relationship("Store", back_populates="labels")
    template_id = Column(Integer, ForeignKey("label_templates.id"), nullable=True)

class LabelTemplate(Base):
    __tablename__ = "label_templates"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    html_code = Column(Text, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)