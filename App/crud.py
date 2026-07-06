from datetime import datetime
from typing import Optional, Dict, Any
import secrets
from sqlalchemy.orm import Session
from App.db_models import Store,User, Sender, Label, LabelTemplate


# =========================
# USERS
# =========================

def create_user(
    db: Session,
    full_name: str,
    username: str,
    password_hash: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    role: str = "owner",
    store_id: int | None = None,
    created_by: int | None = None,
    updated_by: int | None = None,
):
    user = User(
        full_name=full_name,
        username=username,
        email=email,
        phone=phone,
        password_hash=password_hash,
        role=role,
        store_id=store_id,
        is_active=True,
        created_by=created_by,
        updated_by=updated_by,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_all_users(db: Session):
    return db.query(User).order_by(User.id.desc()).all()


def update_user(db: Session, user_id: int, updates: Dict[str, Any]):
    user = get_user_by_id(db, user_id)

    if not user:
        return None

    for key, value in updates.items():
        if hasattr(user, key):
            setattr(user, key, value)

    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: int, updated_by: int | None = None):
    return update_user(
        db,
        user_id,
        {
            "is_active": False,
            "updated_by": updated_by
        }
    )


def delete_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)

    if not user:
        return False

    db.delete(user)
    db.commit()
    return True


# =========================
# SENDERS
# =========================

def create_sender(
    db: Session,
    merchant_name: str,
    store_name: str,
    store_phone: str,
    merchant_city: Optional[str] = None,
    merchant_district: Optional[str] = None,
    merchant_address: Optional[str] = None,
    merchant_national_address: Optional[str] = None,
    store_logo: Optional[str] = None,
    sender_branch: Optional[str] = None,
    store_id: Optional[int] = None
):
    sender = Sender(
        merchant_name=merchant_name,
        store_name=store_name,
        store_phone=store_phone,
        merchant_city=merchant_city,
        merchant_district=merchant_district,
        merchant_address=merchant_address,
        merchant_national_address=merchant_national_address,
        store_logo=store_logo,
        sender_branch=sender_branch,
        store_id=store_id,
        is_active=True
    )
    print("CREATE BRANCH ID =", sender_branch)
    db.add(sender)
    db.commit()
    db.refresh(sender)
    return sender


def get_sender_by_id(db: Session, sender_id: int):
    return db.query(Sender).filter(Sender.id == sender_id).first()
def get_senders_by_store(db: Session, store_id: int):
    return (
        db.query(Sender)
        .filter(Sender.store_id == store_id)
        .order_by(Sender.id.desc())
        .all()
    )


def get_sender_by_phone(db: Session, store_phone: str):
    return db.query(Sender).filter(Sender.store_phone == store_phone).first()


def get_all_senders(db: Session):
    return db.query(Sender).order_by(Sender.id.desc()).all()


def update_sender(db: Session, sender_id: int, updates: Dict[str, Any]):
    sender = get_sender_by_id(db, sender_id)

    if not sender:
        return None

    for key, value in updates.items():
        if hasattr(sender, key):
            setattr(sender, key, value)

    sender.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(sender)
    return sender


def deactivate_sender(db: Session, sender_id: int):
    return update_sender(db, sender_id, {"is_active": False})

def get_sender_by_salla_ship_from(db: Session, store_id: int, ship_from: dict):
    branch_id = str(ship_from.get("branch_id") or "")
    print("CREATE BRANCH ID =", branch_id)
    return (
        db.query(Sender)
        .filter(
            Sender.store_id == store_id,
            Sender.sender_branch == branch_id,
        )
        .first()
    )


def get_or_create_sender_from_salla(db: Session, store: Store, ship_from: dict):
    sender = get_sender_by_salla_ship_from(db, store.id, ship_from)

    if sender:
        sender.store_phone = ship_from.get("phone") or sender.store_phone
        sender.merchant_city = ship_from.get("city") or sender.merchant_city
        sender.merchant_district = ship_from.get("district") or sender.merchant_district
        sender.merchant_address = ship_from.get("address_line") or sender.merchant_address
        sender.merchant_national_address = (
                ship_from.get("short_address") or sender.merchant_national_address
        )
        sender.store_logo = store.store_logo

        db.commit()
        db.refresh(sender)

        return sender

    return create_sender(
        db=db,
        merchant_name=store.owner_name or store.store_name,
        store_name=store.store_name,
        store_phone=ship_from.get("phone") or store.phone or "",
        merchant_city=ship_from.get("city") or "",
        merchant_district=ship_from.get("district") or "",
        merchant_address=ship_from.get("address_line") or "",
        merchant_national_address=ship_from.get("short_address") or "",
        store_logo=store.store_logo,
        sender_branch=str(ship_from.get("branch_id") or ""),
        store_id=store.id,
    )
def delete_sender(db: Session, sender_id: int):
    sender = get_sender_by_id(db, sender_id)

    if not sender:
        return False

    db.delete(sender)
    db.commit()
    return True


# =========================
# LABELS
# =========================

def create_label(
    db: Session,
    order_number: str,
    customer_name: str,
    customer_phone: str,
    customer_city: Optional[str] = None,
    customer_district: Optional[str] = None,
    customer_address: Optional[str] = None,
    customer_short_address: Optional[str] = None,
    sender_id: Optional[int] = None,
    user_id: Optional[int] = None,
    products_json: Optional[str] = None,
    payment_method: str = "paid",
    cod_amount: float = 0,
    shipment_count: Optional[str] = None,
    weight: Optional[str] = None,
    pdf_path: Optional[str] = None,
    html_path: Optional[str] = None,
    store_id: Optional[int] = None,
    status: str = "created"
):
    label = Label(
        order_number=order_number,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_city=customer_city,
        customer_district=customer_district,
        customer_address=customer_address,
        customer_short_address=customer_short_address,
        sender_id=sender_id,
        user_id=user_id,
        products_json=products_json,
        payment_method=payment_method,
        cod_amount=cod_amount,
        shipment_count=shipment_count,
        weight=weight,
        pdf_path=pdf_path,
        html_path=html_path,
        store_id=store_id,
        status=status
    )

    db.add(label)
    db.commit()
    db.refresh(label)
    return label


def get_label_by_id(db: Session, label_id: int):
    return db.query(Label).filter(Label.id == label_id).first()


def get_label_by_order_number(db: Session, order_number: str):
    return (
        db.query(Label)
        .filter(Label.order_number == order_number)
        .order_by(Label.id.desc())
        .first()
    )


def get_all_labels(db: Session):
    return db.query(Label).order_by(Label.id.desc()).all()


def search_labels_by_phone(db: Session, customer_phone: str):
    return (
        db.query(Label)
        .filter(Label.customer_phone == customer_phone)
        .order_by(Label.id.desc())
        .all()
    )


def get_labels_by_sender(db: Session, sender_id: int):
    return (
        db.query(Label)
        .filter(Label.sender_id == sender_id)
        .order_by(Label.id.desc())
        .all()
    )


def get_labels_by_user(db: Session, user_id: int):
    return (
        db.query(Label)
        .filter(Label.user_id == user_id)
        .order_by(Label.id.desc())
        .all()
    )


def update_label_by_order_number(
    db: Session,
    order_number: str,
    updates: Dict[str, Any]
):
    label = get_label_by_order_number(db, order_number)

    if not label:
        return None

    for key, value in updates.items():
        if hasattr(label, key):
            setattr(label, key, value)

    label.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(label)
    return label


def update_label_status(db: Session, order_number: str, status: str):
    return update_label_by_order_number(
        db,
        order_number,
        {"status": status}
    )


def delete_label_by_order_number(db: Session, order_number: str):
    label = get_label_by_order_number(db, order_number)

    if not label:
        return False

    db.delete(label)
    db.commit()
    return True
def get_labels_by_store(db: Session, store_id: int):
    return (
        db.query(Label)
        .filter(Label.store_id == store_id)
        .order_by(Label.id.desc())
        .all()
    )
# =========================
# STORES
# =========================

def create_store(
    db: Session,
    account_number: str,
    store_name: str,
    owner_name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    subscription_plan: str = "trial",
    subscription_status: str = "active",
    label_limit: int = 100,
    store_logo: Optional[str] = None,
    subscription_start = None,
    subscription_end = None,
    salla_store_id: Optional[str] = None,
):
    store = Store(
        account_number=account_number,
        store_name=store_name,
        owner_name=owner_name,
        email=email,
        phone=phone,
        subscription_plan=subscription_plan,
        subscription_status=subscription_status,
        label_limit=label_limit,
        labels_used=0,
        is_active=True,
        store_logo = store_logo,
        subscription_start = subscription_start,
        subscription_end = subscription_end,
        api_key=generate_store_api_key(),
        salla_store_id=salla_store_id,

    )

    db.add(store)
    db.commit()
    db.refresh(store)
    return store


def get_store_by_id(db: Session, store_id: int):
    return db.query(Store).filter(Store.id == store_id).first()


def get_store_by_account_number(db: Session, account_number: str):
    return db.query(Store).filter(Store.account_number == account_number).first()


def get_all_stores(db: Session):
    return db.query(Store).order_by(Store.id.desc()).all()


def update_store(db: Session, store_id: int, updates: Dict[str, Any]):
    store = get_store_by_id(db, store_id)

    if not store:
        return None

    for key, value in updates.items():
        if hasattr(store, key):
            setattr(store, key, value)

    store.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(store)
    return store


def deactivate_store(db: Session, store_id: int):
    return update_store(db, store_id, {"is_active": False})

def can_store_create_label(store: Store):
    if not store:
        return False, "Store not found"

    if not store.is_active:
        return False, "Store is not active"

    if store.subscription_status != "active":
        return False, "Subscription is not active"

    if store.labels_used >= store.label_limit:
        return False, "Label limit reached"

    return True, "Allowed"

def generate_store_api_key():
    return "BLS_" + secrets.token_urlsafe(32)

def increment_store_labels_used(db: Session, store_id: int):
    store = get_store_by_id(db, store_id)

    if not store:
        return None

    store.labels_used = (store.labels_used or 0) + 1
    store.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(store)

    return store

# =========================
# LABEL TEMPLATES
# =========================

def create_label_template(
    db: Session,
    name: str,
    html_code: str
):
    template = LabelTemplate(
        name=name,
        html_code=html_code,
        is_active=True
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return template


def get_label_template_by_id(db: Session, template_id: int):
    return (
        db.query(LabelTemplate)
        .filter(LabelTemplate.id == template_id)
        .first()
    )


def get_all_label_templates(db: Session):
    return (
        db.query(LabelTemplate)
        .order_by(LabelTemplate.id.desc())
        .all()
    )


def get_active_label_templates(db: Session):
    return (
        db.query(LabelTemplate)
        .filter(LabelTemplate.is_active == True)
        .order_by(LabelTemplate.id.desc())
        .all()
    )


def update_label_template(
    db: Session,
    template_id: int,
    updates: Dict[str, Any]
):
    template = get_label_template_by_id(db, template_id)

    if not template:
        return None

    for key, value in updates.items():
        if hasattr(template, key):
            setattr(template, key, value)

    template.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(template)

    return template


def deactivate_label_template(db: Session, template_id: int):
    return update_label_template(
        db,
        template_id,
        {"is_active": False}
    )
def get_store_by_salla_id(db: Session, salla_store_id: str):
    return db.query(Store).filter(Store.salla_store_id == str(salla_store_id)).first()


def create_salla_store(
    db: Session,
    salla_store_id: str,
    store_name: str,
    owner_name: str,
):
    return create_store(
        db=db,
        account_number=f"S{salla_store_id}",
        salla_store_id=str(salla_store_id),
        store_name=store_name,
        owner_name=owner_name,
        subscription_plan="trial",
        subscription_status="active",
        label_limit=100,
    )


def create_default_owner_for_store(db: Session, store: Store):
    username = f"salla_{store.salla_store_id or store.id}"

    existing = get_user_by_username(db, username)
    if existing:
        return existing

    return create_user(
        db=db,
        full_name=store.owner_name or store.store_name,
        username=username,
        password_hash="SALLA_LOGIN_DISABLED",
        email=store.email,
        phone=store.phone,
        role="store_owner",
        store_id=store.id,
    )

def create_default_sender_for_store(db: Session, store: Store, ship_from: dict | None = None):
    ship_from = ship_from or {}

    existing = get_senders_by_store(db, store.id)
    if existing:
        return existing[0]

    return create_sender(
        db=db,
        merchant_name=store.owner_name or store.store_name,
        store_name=ship_from.get("name") or store.store_name,
        store_phone=ship_from.get("phone") or store.phone or "",
        merchant_city=ship_from.get("city") or "",
        merchant_district=ship_from.get("district") or "",
        merchant_address=ship_from.get("address_line") or "",
        merchant_national_address=ship_from.get("short_address") or "",
        store_logo=store.store_logo,
        sender_branch=ship_from.get("name") or "الفرع الرئيسي",
        store_id=store.id,
    )
def update_store_from_salla(db: Session, store: Store, data: dict):
    store_data = data.get("data", data) or {}

    store.store_name = (
        store_data.get("name")
        or store_data.get("store_name")
        or store.store_name
    )

    store.owner_name = (
        store_data.get("owner")
        or store_data.get("owner_name")
        or store.owner_name
    )

    store.email = store_data.get("email") or store.email
    store.phone = store_data.get("phone") or store.phone

    store.store_logo = (
        store_data.get("logo")
        or store_data.get("avatar")
        or store_data.get("store_logo")
        or store.store_logo
    )

    store.store_domain = (
        store_data.get("domain")
        or store_data.get("store_domain")
        or store_data.get("url")
        or store.store_domain
    )

    store.store_platform = "salla"
    store.external_store_id = store.salla_store_id
    store.last_platform_sync = datetime.utcnow()
    store.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(store)
    return store
def update_store_subscription(
    db,
    store,
    *,
    plan=None,
    status=None,
    start=None,
    end=None,
):
    if plan is not None:
        store.subscription_plan = plan

    if status is not None:
        store.subscription_status = status

    if start is not None:
        store.subscription_start = start

    if end is not None:
        store.subscription_end = end

    store.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(store)

    return store
def get_label_by_order_and_store(db, order_number: str, store_id: int):
    return (
        db.query(Label)
        .filter(
            Label.order_number == str(order_number),
            Label.store_id == store_id
        )
        .first()
    )