import json

from App import crud
from App.db_models import LabelTemplate
from App.label_generator import generate_shipping_label
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


def error_response(message: str):
    return {
        "success": False,
        "message": message
    }


def get_default_template(db, store):
    if store.default_template_id:
        template = crud.get_label_template_by_id(db, store.default_template_id)
        if template and template.is_active:
            return template

    return (
        db.query(LabelTemplate)
        .filter(LabelTemplate.is_active == True)
        .first()
    )


def handle_shipment_creating(db, payload: dict):
    try:
        merchant_id = get_salla_merchant_id(payload)

        if not merchant_id:
            return error_response("لم يصل رقم متجر سلة")

        store = crud.get_store_by_salla_id(db, merchant_id)

        if not store:
            return error_response("المتجر غير مربوط في بوليصتي")

        allowed, reason = crud.can_store_create_label(store)
        if not allowed:
            return error_response(reason)

        data = payload.get("data", {}) or {}

        ship_from = data.get("ship_from") or {}

        sender = crud.get_or_create_sender_from_salla(
            db=db,
            store=store,
            ship_from=ship_from,
        )

        template = get_default_template(db, store)

        if not template:
            return error_response("لا يوجد قالب ملصق فعال")

        label_data = map_salla_to_label_data(
            payload=payload,
            sender_id=sender.id,
            template_id=template.id,
        )
        print("SHIPMENT COUNT =", label_data.shipment_count)
        existing_label = crud.get_label_by_order_and_store(
            db=db,
            order_number=label_data.order_number,
            store_id=store.id,
        )

        if existing_label:
            tracking_number = str(existing_label.order_number)

            return {
                "success": True,
                "shipment_number": tracking_number,
                "tracking_number": tracking_number,
                "tracking_link": f"https://api.bolisaty.me/track/{tracking_number}",
                "pdf_label": f"https://api.bolisaty.me/download-label/{tracking_number}"
            }

        pdf_path, html_path = generate_shipping_label(
            data=label_data,
            sender=sender,
            store=store,
            template_html=template.html_code,
        )

        customer_name = (
            f"{label_data.receiver_first_name} {label_data.receiver_last_name}"
        ).strip()

        crud.create_label(
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

        tracking_number = str(label_data.order_number)

        return {
            "success": True,
            "shipment_number": tracking_number,
            "tracking_number": tracking_number,
            "tracking_link": f"https://api.bolisaty.me/track/{tracking_number}",
            "pdf_label": f"https://api.bolisaty.me/download-label/{tracking_number}"
        }

    except Exception as e:
        logger.exception("Salla shipment creating failed")

        return error_response(
            f"فشل إصدار البوليصة من بوليصتي: {str(e)}"
        )