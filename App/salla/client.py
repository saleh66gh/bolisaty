import requests
from datetime import datetime, timedelta

from App.config import (
    SALLA_API_URL,
    SALLA_CLIENT_ID,
    SALLA_CLIENT_SECRET,
)


class SallaApiError(Exception):
    pass


def refresh_access_token(db, store):
    if not store.salla_refresh_token:
        raise SallaApiError("Salla refresh token is missing")

    response = requests.post(
        "https://accounts.salla.sa/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": store.salla_refresh_token,
            "client_id": SALLA_CLIENT_ID,
            "client_secret": SALLA_CLIENT_SECRET,
        },
        timeout=20,
    )

    if response.status_code >= 400:
        raise SallaApiError(
            f"Refresh token failed ({response.status_code}) : {response.text}"
        )

    data = response.json()

    store.salla_access_token = data["access_token"]

    if data.get("refresh_token"):
        store.salla_refresh_token = data["refresh_token"]

    expires_in = data.get("expires_in")

    if expires_in:
        store.token_expires_at = (
            datetime.utcnow() + timedelta(seconds=int(expires_in))
        )

    store.last_platform_sync = datetime.utcnow()

    db.commit()
    db.refresh(store)

    return data


def salla_request(
    store,
    method: str,
    endpoint: str,
    db=None,
    json_data=None,
    params=None,
    retry=True,
):
    if not store.salla_access_token:
        raise SallaApiError("Missing Salla access token")

    url = f"{SALLA_API_URL.rstrip('/')}/{endpoint.lstrip('/')}"

    headers = {
        "Authorization": f"Bearer {store.salla_access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=json_data,
            params=params,
            timeout=20,
        )
    except requests.RequestException as e:
        raise SallaApiError(str(e))

    if (
        response.status_code == 401
        and retry
        and db
        and store.salla_refresh_token
    ):
        refresh_access_token(db, store)

        return salla_request(
            store=store,
            method=method,
            endpoint=endpoint,
            db=db,
            json_data=json_data,
            params=params,
            retry=False,
        )

    if response.status_code >= 400:
        raise SallaApiError(
            f"Salla API {response.status_code}: {response.text}"
        )

    try:
        return response.json()
    except Exception:
        return response.text


def get_store_info(store, db=None):
    return salla_request(
        store=store,
        method="GET",
        endpoint="/store/info",
        db=db,
    )


def get_order(store, order_id, db=None):
    return salla_request(
        store=store,
        method="GET",
        endpoint=f"/orders/{order_id}",
        db=db,
    )


def get_customer(store, customer_id, db=None):
    return salla_request(
        store=store,
        method="GET",
        endpoint=f"/customers/{customer_id}",
        db=db,
    )


def get_branches(store, db=None):
    return salla_request(
        store=store,
        method="GET",
        endpoint="/branches",
        db=db,
    )