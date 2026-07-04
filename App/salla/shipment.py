from fastapi import HTTPException
import json
from App import crud
from App.db_models import LabelTemplate
from App.label_generator import generate_shipping_label
from App.salla.models import SallaShipmentPayloadData
from App.salla.mapper import map_salla_to_label_data
from App.logger import logger


def get_salla_merchant_id(payload: dict) -> str:
    return str(
        payload.get("merchant")
        or payload.get("merchant_id")
        or payload.get("data", {}).get("merchant")
        or payload.get("data", {}).get("merchant_id")
        or ""
    )


def handle_shipment_creating(db, payload: dict):
    merchant_id = get_salla_merchant_id(payload)

    if not merchant_id:
        raise HTTPException(status_code=400, detail="Missing merchant id")

    store = crud.get_store_by_salla_id(db, merchant_id)

    if not store:
        raise HTTPException(status_code=404, detail="Store not connected")

    if not store.is_active:
        raise HTTPException(status_code=403, detail="Store is inactive")

    raw_data = payload.get("data", payload)
    data = SallaShipmentPayloadData(**raw_data)

    shipment = data.shipments[0] if data.shipments else None
    ship_from = shipment.ship_from.model_dump() if shipment and shipment.ship_from else {}

    sender = crud.get_or_create_sender_from_salla(
        db=db,
        store=store,
        ship_from=ship_from,
    )

    template = None

    if store.default_template_id:
        template = crud.get_label_template_by_id(db, store.default_template_id)

    if not template:
        template = db.query(LabelTemplate).filter(
            LabelTemplate.is_active == True
        ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    label_data = map_salla_to_label_data(
        data=data,
        sender_id=sender.id,
        template_id=template.id,
    )


    pdf_path, html_path = generate_shipping_label(
        data=label_data,
        sender=sender,
        store=store,
        template_html=template.html_code,
    )
    customer_name = f"{label_data.receiver_first_name} {label_data.receiver_last_name}".strip()

    label = crud.create_label(
        db=db,
        order_number=label_data.order_number,
        customer_name=customer_name,
        customer_phone=label_data.receiver_phone,
        customer_city=label_data.receiver_city,
        customer_district=label_data.receiver_district,
        customer_address=label_data.receiver_address,
        customer_short_address=label_data.receiver_national_address,
        sender_id=sender.id,
        user_id=None,
        store_id=store.id,
        products_json=json.dumps(
            [product.model_dump() for product in label_data.products],
            ensure_ascii=False
        ),
        payment_method="cash" if label_data.cod_enabled else "paid",
        cod_amount=label_data.cod_amount or 0,
        shipment_count=str(label_data.shipment_count),
        weight=str(label_data.weight),
        pdf_path=pdf_path,
        html_path=html_path,
        status="created"
    )

    crud.increment_store_labels_used(db, store.id)

    tracking_number = label_data.order_number

    return {
  "success": True,
  "shipment_number": "267472546",
  "tracking_number": "267472546",
  "tracking_link": "https://api.bolisaty.me/track/267472546",
  "pdf_label": "https://api.bolisaty.me/download-label/267472546"
}