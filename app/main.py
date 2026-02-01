"""FastAPI application for Order Processing System."""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import Any

import uuid
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()
api_router = APIRouter()

# In-memory order storage (spec: simple dictionary, no repository)
_orders: dict[str, dict] = {}


def _round_decimal(value: Decimal) -> Decimal:
    """Round to 2 decimal places, half-up per spec 4.2."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _validate_create_order(body: dict[str, Any]) -> tuple[bool, dict[str, str]]:
    """
    Validate create order payload per spec 4.1.
    Returns (is_valid, details). details maps field paths to error messages.
    """
    details: dict[str, str] = {}

    if "items" not in body or body["items"] is None:
        details["items"] = "Items are required"
        return False, details

    items = body["items"]
    if not isinstance(items, list):
        details["items"] = "Items must be an array"
        return False, details

    if len(items) == 0:
        details["items"] = "At least one item is required"
        return False, details

    for i, item in enumerate(items):
        prefix = f"items[{i}]"
        if not isinstance(item, dict):
            details[f"{prefix}"] = "Invalid item format"
            continue

        if "product_id" not in item:
            details[f"{prefix}.product_id"] = "Product ID is required"
        elif not isinstance(item["product_id"], str):
            details[f"{prefix}.product_id"] = "Product ID must be a string"
        elif not item["product_id"] or not item["product_id"].strip():
            details[f"{prefix}.product_id"] = "Product ID must be non-empty"

        if "quantity" not in item:
            details[f"{prefix}.quantity"] = "Quantity is required"
        elif not isinstance(item["quantity"], (int, float)):
            details[f"{prefix}.quantity"] = "Quantity must be a number"
        elif int(item["quantity"]) != item["quantity"] or item["quantity"] < 1:
            details[f"{prefix}.quantity"] = "Must be at least 1"

        if "unit_price" not in item:
            details[f"{prefix}.unit_price"] = "Unit price is required"
        elif not isinstance(item["unit_price"], (int, float)):
            details[f"{prefix}.unit_price"] = "Unit price must be a number"
        elif item["unit_price"] < 0:
            details[f"{prefix}.unit_price"] = "Must be greater than or equal to 0"

    if details:
        return False, details
    return True, {}


def _build_order_response(items: list[dict]) -> dict:
    """Build order response per spec 3.1."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    order_items = []
    total = Decimal("0")

    for item in items:
        qty = Decimal(str(item["quantity"]))
        price = Decimal(str(item["unit_price"]))
        subtotal = _round_decimal(qty * price)
        total += subtotal
        order_items.append({
            "product_id": str(item["product_id"]),
            "quantity": int(qty),
            "unit_price": float(_round_decimal(price)),
            "subtotal": float(subtotal),
        })

    return {
        "id": str(uuid.uuid4()),
        "status": "PENDING",
        "total_amount": float(_round_decimal(total)),
        "items": order_items,
        "created_at": now,
        "updated_at": now,
    }


@api_router.post("/orders")
async def create_order(request: Request):
    """Create a new order in PENDING status. Spec 3.1."""
    try:
        body = await request.json()
    except Exception:
        body = None

    if body is None or not isinstance(body, dict):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"body": "Invalid JSON body"},
                }
            },
        )

    is_valid, details = _validate_create_order(body)
    if not is_valid:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": details,
                }
            },
        )

    order = _build_order_response(body["items"])
    _orders[order["id"]] = order
    return JSONResponse(status_code=201, content=order)


def _is_valid_uuid(value: str) -> bool:
    """Check if value is a valid RFC 4122 UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


@api_router.get("/orders/{order_id}")
def get_order(order_id: str):
    """Return order by ID. Spec 3.2."""
    if not _is_valid_uuid(order_id):
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Order not found",
                    "details": {"order_id": order_id},
                }
            },
        )

    if order_id not in _orders:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Order not found",
                    "details": {"order_id": order_id},
                }
            },
        )

    return JSONResponse(status_code=200, content=_orders[order_id])


@api_router.post("/orders/{order_id}/confirm")
def confirm_order(order_id: str):
    """Transition order from PENDING to CONFIRMED. Spec 3.3."""
    if not _is_valid_uuid(order_id):
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Order not found",
                    "details": {"order_id": order_id},
                }
            },
        )

    if order_id not in _orders:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Order not found",
                    "details": {"order_id": order_id},
                }
            },
        )

    order = _orders[order_id]
    if order["status"] != "PENDING":
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "INVALID_STATE_TRANSITION",
                    "message": f"Cannot confirm order in {order['status']} state",
                    "details": {
                        "order_id": order_id,
                        "current_status": order["status"],
                        "requested_action": "confirm",
                    },
                }
            },
        )

    order["status"] = "CONFIRMED"
    now = datetime.now(timezone.utc)
    # Use millisecond precision so updated_at differs from created_at when in same second
    order["updated_at"] = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond:06d}"[:3] + "Z"
    return JSONResponse(status_code=200, content=order)


@api_router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: str):
    """Transition order from PENDING to CANCELLED. Spec 3.4."""
    if not _is_valid_uuid(order_id):
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Order not found",
                    "details": {"order_id": order_id},
                }
            },
        )

    if order_id not in _orders:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Order not found",
                    "details": {"order_id": order_id},
                }
            },
        )

    order = _orders[order_id]
    if order["status"] != "PENDING":
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "INVALID_STATE_TRANSITION",
                    "message": f"Cannot cancel order in {order['status']} state",
                    "details": {
                        "order_id": order_id,
                        "current_status": order["status"],
                        "requested_action": "cancel",
                    },
                }
            },
        )

    order["status"] = "CANCELLED"
    now = datetime.now(timezone.utc)
    order["updated_at"] = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond:06d}"[:3] + "Z"
    return JSONResponse(status_code=200, content=order)


app.include_router(api_router, prefix="/api/v1")
