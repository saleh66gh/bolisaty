import os
import json
from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from fastapi import Request
from App.salla.shipment import handle_shipment_creating
from App.models import LabelData
from App.label_generator import generate_shipping_label
from App.database import init_db, get_db
from App import crud
from App.salla_service import handle_salla_event
from App.schemas import (
    StoreCreate,
    StoreUpdate,
    StoreResponse,
    SenderCreate,
    SenderUpdate,
    SenderResponse,
    UserCreate,
    UserResponse,
    LoginRequest,
    TokenResponse,
    UserUpdate,
    CurrentUserResponse,
    StoreFullCreate,
    LabelTemplateCreate,
    LabelTemplateUpdate,
    LabelTemplateResponse
)
from App.logger import logger
from App.exceptions import SenderNotFound
from App.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from datetime import datetime
app = FastAPI(title="Bolisaty API")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")

    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = crud.get_user_by_username(db, username)

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not active")

    return user
def require_roles(*allowed_roles):
    def checker(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission"
            )
        return current_user

    return checker

@app.get("/")
def home():
    return {
        "app": "Bolisaty",
        "status": "running"
    }


@app.post("/create-label")
def create_label(
    data: LabelData,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin", "employee", "store_owner")),
):
    try:
        sender = crud.get_sender_by_id(db, data.sender_id)

        if sender is None:
            raise SenderNotFound(f"Sender {data.sender_id} not found")

        if current_user.role == "store_owner":
            if sender.store_id != current_user.store_id:
                raise HTTPException(status_code=403, detail="Access denied")

            store_id = current_user.store_id
        else:
            store_id = sender.store_id

        store = crud.get_store_by_id(db, store_id)

        allowed, reason = crud.can_store_create_label(store)

        if not allowed:
            raise HTTPException(
                status_code=403,
                detail=reason
            )
        template = crud.get_label_template_by_id(db, data.template_id)

        if not template or not template.is_active:
            raise HTTPException(status_code=404, detail="Template not found")

        pdf_path, html_path = generate_shipping_label(
            data=data,
            sender=sender,
            store=store,
            template_html=template.html_code
        )

        customer_name = f"{data.receiver_first_name} {data.receiver_last_name}".strip()

        label = crud.create_label(
            db=db,
            order_number=data.order_number,
            customer_name=customer_name,
            customer_phone=data.receiver_phone,
            customer_city=data.receiver_city,
            customer_district=data.receiver_district,
            customer_address=data.receiver_address,
            customer_short_address=data.receiver_national_address,
            sender_id=data.sender_id,
            user_id=current_user.id,
            store_id=store_id,
            products_json=json.dumps(
                [product.model_dump() for product in data.products],
                ensure_ascii=False
            ),
            payment_method="cash" if data.cod_enabled else "paid",
            cod_amount=data.cod_amount or 0,
            shipment_count=str(data.shipment_count),
            weight=str(data.weight),
            pdf_path=pdf_path,
            html_path=html_path,
            status="created"
        )

        crud.increment_store_labels_used(db, store_id)

        logger.info(
            f"Label created successfully | order_number={data.order_number} | user_id={current_user.id}"
        )

        return {
            "status": "success",
            "message": "Shipping label created and saved",
            "label_id": label.id,
            "order_number": label.order_number,
            "pdf_path": label.pdf_path,
            "html_path": label.html_path
        }

    except SenderNotFound as e:
        logger.error(str(e))
        raise HTTPException(status_code=404, detail="Sender not found")

    except HTTPException:
        raise

    except Exception:
        logger.exception(f"Failed to create label | order_number={data.order_number}")
        raise HTTPException(status_code=500, detail="Failed to create label")

@app.get("/labels")
def labels(
    db: Session = Depends(get_db),
        current_user=Depends(require_roles("owner", "admin", "employee", "support")),
):
    if current_user.role == "store_owner":
        labels_list = crud.get_labels_by_store(
            db,
            current_user.store_id
        )
    else:
        labels_list = crud.get_all_labels(db)

    return [
        {
            "id": label.id,
            "order_number": label.order_number,
            "customer_name": label.customer_name,
            "customer_phone": label.customer_phone,
            "payment_method": label.payment_method,
            "cod_amount": label.cod_amount,
            "shipment_count": label.shipment_count,
            "weight": label.weight,
            "pdf_path": label.pdf_path,
            "html_path": label.html_path,
            "status": label.status,
            "created_at": label.created_at,
            "updated_at": label.updated_at
        }
        for label in labels_list
    ]


@app.get("/labels/{order_number}")
def get_label(
    order_number: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin", "employee", "support")),
):
    label = crud.get_label_by_order_number(db, order_number)

    if label is None:

        raise HTTPException(status_code=404, detail="Label not found")
    if current_user.role == "store_owner":
        if label.store_id != current_user.store_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
    return {
        "id": label.id,
        "order_number": label.order_number,
        "customer_name": label.customer_name,
        "customer_phone": label.customer_phone,
        "customer_city": label.customer_city,
        "customer_district": label.customer_district,
        "customer_address": label.customer_address,
        "customer_short_address": label.customer_short_address,
        "sender_id": label.sender_id,
        "user_id": label.user_id,
        "products": json.loads(label.products_json or "[]"),
        "payment_method": label.payment_method,
        "cod_amount": label.cod_amount,
        "shipment_count": label.shipment_count,
        "weight": label.weight,
        "pdf_path": label.pdf_path,
        "html_path": label.html_path,
        "status": label.status,
        "created_at": label.created_at,
        "updated_at": label.updated_at
    }


@app.get("/download/{order_number}")
def download_label(
    order_number: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin", "employee", "support")),
):
    label = crud.get_label_by_order_number(db, order_number)

    if label is None:
        raise HTTPException(status_code=404, detail="Label not found")

    if not label.pdf_path or not os.path.exists(label.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    if current_user.role == "store_owner":
        if label.store_id != current_user.store_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
    return FileResponse(
        path=label.pdf_path,
        media_type="application/pdf",
        filename=f"label_{order_number}.pdf"
    )


@app.put("/labels/{order_number}")
def update_label(
    order_number: str,
    data: LabelData,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin")),
):
    old_label = crud.get_label_by_order_number(db, order_number)

    if old_label is None:
        raise HTTPException(status_code=404, detail="Label not found")

    sender = crud.get_sender_by_id(db, data.sender_id)

    if sender is None:
        raise HTTPException(status_code=404, detail="Sender not found")
    if current_user.role == "store_owner":
        if sender.store_id != current_user.store_id:
            raise HTTPException(status_code=403, detail="Access denied")

        store_id = current_user.store_id
    else:
        store_id = sender.store_id

    store = crud.get_store_by_id(db, store_id)

    allowed, reason = crud.can_store_create_label(store)

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=reason
        )

    for path in [
        old_label.pdf_path,
        old_label.html_path,
        f"Assets/qr/phone_qr_{order_number}.png",
        f"Assets/qr/location_qr_{order_number}.png",
    ]:
        if path and os.path.exists(path):
            os.remove(path)

    pdf_path, html_path = generate_shipping_label(data, sender)

    customer_name = f"{data.receiver_first_name} {data.receiver_last_name}".strip()

    updated = crud.update_label_by_order_number(
        db=db,
        order_number=order_number,
        updates={
            "order_number": data.order_number,
            "customer_name": customer_name,
            "customer_phone": data.receiver_phone,
            "customer_city": data.receiver_city,
            "customer_district": data.receiver_district,
            "customer_address": data.receiver_address,
            "customer_short_address": data.receiver_national_address,
            "sender_id": data.sender_id,
            "user_id": current_user.id,
            "products_json": json.dumps(
                [product.model_dump() for product in data.products],
                ensure_ascii=False
            ),
            "payment_method": "cash" if data.cod_enabled else "paid",
            "cod_amount": data.cod_amount or 0,
            "shipment_count": str(data.shipment_count),
            "weight": str(data.weight),
            "pdf_path": pdf_path,
            "html_path": html_path,
            "status": "updated"
        }
    )

    return {
        "status": "success",
        "message": "Label updated",
        "label_id": updated.id,
        "old_order_number": order_number,
        "new_order_number": updated.order_number,
        "pdf_path": updated.pdf_path,
        "html_path": updated.html_path
    }


@app.delete("/labels/{order_number}")
def delete_label(
    order_number: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin")),
):
    label = crud.get_label_by_order_number(db, order_number)

    if label is None:
        raise HTTPException(status_code=404, detail="Label not found")

    for path in [
        label.pdf_path,
        label.html_path,
        f"Assets/qr/phone_qr_{order_number}.png",
        f"Assets/qr/location_qr_{order_number}.png",
    ]:
        if path and os.path.exists(path):
            os.remove(path)

    crud.delete_label_by_order_number(db, order_number)

    return {
        "status": "success",
        "message": "Label deleted",
        "order_number": order_number
    }


@app.post("/senders", response_model=SenderResponse)
def create_sender(
    sender: SenderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin", "store_owner")),
):
    store_id = current_user.store_id if current_user.role == "store_owner" else sender.store_id

    return crud.create_sender(
        db=db,
        merchant_name=sender.merchant_name,
        store_name=sender.store_name,
        store_phone=sender.store_phone,
        merchant_city=sender.merchant_city,
        merchant_district=sender.merchant_district,
        merchant_address=sender.merchant_address,
        merchant_national_address=sender.merchant_national_address,
        store_logo=sender.store_logo,
        sender_branch=sender.sender_branch,
        store_id = store_id
    )


@app.get("/senders", response_model=list[SenderResponse])
def get_senders(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin", "store_owner"))
):
    if current_user.role == "store_owner":
        return crud.get_senders_by_store(db, current_user.store_id)

    return crud.get_all_senders(db)

@app.put("/senders/{sender_id}", response_model=SenderResponse)
def update_sender(
    sender_id: int,
    sender: SenderUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin")),
):
    updates = sender.model_dump(exclude_unset=True)

    updated_sender = crud.update_sender(db, sender_id, updates)

    if updated_sender is None:
        raise HTTPException(status_code=404, detail="Sender not found")

    return updated_sender


@app.delete("/senders/{sender_id}")
def delete_sender(
    sender_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin")),
):
    deleted = crud.delete_sender(db, sender_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Sender not found")

    return {
        "status": "success",
        "message": "Sender deleted",
        "sender_id": sender_id
    }


@app.post("/users", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin"))
):
    existing_user = crud.get_user_by_username(db, user.username)

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    role = user.role.lower()

    allowed_roles = ["admin", "store_owner"]

    if role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Invalid role")

    if role == "store_owner":
        if not user.store_id:
            raise HTTPException(status_code=400, detail="store_id is required for store_owner")

        store = crud.get_store_by_id(db, user.store_id)

        if not store:
            raise HTTPException(status_code=404, detail="Store not found")

    if role == "admin":
        user.store_id = None

    return crud.create_user(
        db=db,
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        phone=user.phone,
        password_hash=hash_password(user.password),
        role=role,
        store_id=user.store_id,
        created_by=current_user.id,
        updated_by=current_user.id
    )
@app.get("/users", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner"))
):
    return crud.get_all_users(db)
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner"))
):
    user = crud.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner"))
):
    updates = data.model_dump(exclude_unset=True)

    updates["updated_by"] = current_user.id

    user = crud.update_user(
        db,
        user_id,
        updates
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user
@app.patch("/users/{user_id}/status")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner"))
):
    user = crud.deactivate_user(
        db,
        user_id,
        updated_by=current_user.id
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "status": "success",
        "message": "User deactivated"
    }
@app.get("/me", response_model=CurrentUserResponse)
def get_current_user(
    current_user=Depends(get_current_user)
):
    return current_user
@app.post("/stores", response_model=StoreResponse)
def create_store(
    store: StoreCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin"))
):
    existing_store = crud.get_store_by_account_number(db, store.account_number)

    if existing_store:
        raise HTTPException(
            status_code=400,
            detail="Store account number already exists"
        )

    if not store.account_number.isdigit() or len(store.account_number) != 5:
        raise HTTPException(
            status_code=400,
            detail="Account number must be exactly 5 digits"
        )

    return crud.create_store(
        db=db,
        account_number=store.account_number,
        store_name=store.store_name,
        owner_name=store.owner_name,
        email=store.email,
        phone=store.phone,
        store_logo=store.store_logo,
        subscription_plan=store.subscription_plan,
        subscription_status=store.subscription_status,
        subscription_start=store.subscription_start,
        subscription_end=store.subscription_end,
        label_limit=store.label_limit
    )


@app.get("/stores", response_model=list[StoreResponse])
def get_stores(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin", "support"))
):
    return crud.get_all_stores(db)


@app.get("/stores/{store_id}", response_model=StoreResponse)
def get_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin", "support"))
):
    store = crud.get_store_by_id(db, store_id)

    if not store:
        raise HTTPException(
            status_code=404,
            detail="Store not found"
        )

    return store


@app.put("/stores/{store_id}", response_model=StoreResponse)
def update_store(
    store_id: int,
    store: StoreUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin"))
):
    updates = store.model_dump(exclude_unset=True)

    updated_store = crud.update_store(db, store_id, updates)

    if not updated_store:
        raise HTTPException(
            status_code=404,
            detail="Store not found"
        )

    return updated_store


@app.patch("/stores/{store_id}/status")
def deactivate_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin"))
):
    store = crud.deactivate_store(db, store_id)

    if not store:
        raise HTTPException(
            status_code=404,
            detail="Store not found"
        )

    return {
        "status": "success",
        "message": "Store deactivated",
        "store_id": store_id
    }


@app.post("/stores/create-full")
def create_full_store(
    data: StoreFullCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin"))
):
    existing_store = crud.get_store_by_account_number(db, data.store.account_number)

    if existing_store:
        raise HTTPException(status_code=400, detail="Store account number already exists")

    if not data.store.account_number.isdigit() or len(data.store.account_number) != 5:
        raise HTTPException(status_code=400, detail="Account number must be exactly 5 digits")

    existing_user = crud.get_user_by_username(db, data.owner.username)

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    try:
        store = crud.create_store(
            db=db,
            account_number=data.store.account_number,
            store_name=data.store.store_name,
            owner_name=data.store.owner_name,
            email=data.store.email,
            phone=data.store.phone,
            store_logo=data.store.store_logo,
            subscription_plan=data.store.subscription_plan,
            subscription_status=data.store.subscription_status,
            subscription_start=data.store.subscription_start,
            subscription_end=data.store.subscription_end,
            label_limit=data.store.label_limit
        )

        owner_user = crud.create_user(
            db=db,
            full_name=data.owner.full_name,
            username=data.owner.username,
            email=data.owner.email,
            phone=data.owner.phone,
            password_hash=hash_password(data.owner.password),
            role="store_owner",
            store_id=store.id,
            created_by=current_user.id,
            updated_by=current_user.id
        )

        sender = crud.create_sender(
            db=db,
            merchant_name=data.sender.merchant_name,
            store_name=data.sender.store_name,
            store_phone=data.sender.store_phone,
            merchant_city=data.sender.merchant_city,
            merchant_district=data.sender.merchant_district,
            merchant_address=data.sender.merchant_address,
            merchant_national_address=data.sender.merchant_national_address,
            store_logo=None,
            sender_branch=data.sender.sender_branch,
            store_id=store.id
        )

        return {
            "status": "success",
            "message": "Store, owner and sender created successfully",
            "store_id": store.id,
            "user_id": owner_user.id,
            "sender_id": sender.id
        }

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create full store")

@app.get("/stores/{store_id}/api-key")
def get_store_api_key(
    store_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner"))
):
    store = crud.get_store_by_id(db, store_id)

    if not store:
        raise HTTPException(
            status_code=404,
            detail="Store not found"
        )

    return {
        "store_id": store.id,
        "account_number": store.account_number,
        "store_name": store.store_name,
        "api_key": store.api_key
    }

@app.post("/label-templates", response_model=LabelTemplateResponse)
def create_label_template(
    template: LabelTemplateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin"))
):
    return crud.create_label_template(
        db=db,
        name=template.name,
        html_code=template.html_code
    )


@app.get("/label-templates", response_model=list[LabelTemplateResponse])
def get_label_templates(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin", "support"))
):
    return crud.get_all_label_templates(db)


@app.get("/label-templates/active", response_model=list[LabelTemplateResponse])
def get_active_label_templates(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin", "support"))
):
    return crud.get_active_label_templates(db)


@app.get("/label-templates/{template_id}", response_model=LabelTemplateResponse)
def get_label_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin", "support"))
):
    template = crud.get_label_template_by_id(db, template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@app.put("/label-templates/{template_id}", response_model=LabelTemplateResponse)
def update_label_template(
    template_id: int,
    template: LabelTemplateUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin"))
):
    updates = template.model_dump(exclude_unset=True)

    updated_template = crud.update_label_template(db, template_id, updates)

    if not updated_template:
        raise HTTPException(status_code=404, detail="Template not found")

    return updated_template


@app.patch("/label-templates/{template_id}/status")
def deactivate_label_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("owner", "admin"))
):
    template = crud.deactivate_label_template(db, template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "status": "success",
        "message": "Template deactivated",
        "template_id": template_id
    }

@app.post("/salla/shipment/create")
async def salla_shipment_create(
    request: Request,
    db: Session = Depends(get_db),
):
    payload = await request.json()

    logger.warning("===== FUNCTION PAYLOAD START =====")
    logger.warning(json.dumps(payload, ensure_ascii=False, indent=2))
    logger.warning("===== FUNCTION PAYLOAD END =====")

    return 0
@app.post("/salla/app/events")
async def salla_app_events(
    request: Request,
    db: Session = Depends(get_db),
):
    payload = await request.json()

    logger.warning("===== SALLA APP EVENT START =====")
    logger.warning(json.dumps(payload, ensure_ascii=False, indent=2))
    logger.warning("===== SALLA APP EVENT END =====")

    result = handle_salla_event(db, payload)
    return result
@app.get("/download-label/{order_number}")
def download_label(order_number: str):
    pdf_path = f"Labels/label_{order_number}.pdf"

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Label not found")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"label_{order_number}.pdf"
    )
@app.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, data.username)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    token = create_access_token({
        "sub": user.username,
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }
