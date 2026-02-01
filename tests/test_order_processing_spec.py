"""
Order Processing System – Comprehensive Test Suite

Spec reference: /openspec/features/order-processing.md

Test organization maps to spec sections:
- Section 3.1: Create Order (POST /orders)
- Section 3.2: Get Order (GET /orders/{order_id})
- Section 3.3: Confirm Order (POST /orders/{order_id}/confirm)
- Section 3.4: Cancel Order (POST /orders/{order_id}/cancel)
- Section 4: Validation Rules
- Section 5: Error Cases
- Section 2: State Transitions & Immutability
"""

import re
import uuid

import pytest


# --- Helpers ---

def valid_create_payload(items=None):
    """Valid create order payload per spec 3.1."""
    if items is None:
        items = [
            {"product_id": "PROD-001", "quantity": 2, "unit_price": 9.99},
            {"product_id": "PROD-002", "quantity": 1, "unit_price": 24.50},
        ]
    return {"items": items}


def assert_valid_uuid(value: str) -> None:
    """Assert value is RFC 4122 UUID format per spec 7."""
    pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    assert pattern.match(value), f"Expected UUID format, got: {value}"


def assert_valid_iso8601_datetime(value: str) -> None:
    """Assert value is ISO 8601 datetime format per spec 7."""
    # Basic ISO 8601 pattern (e.g. 2025-01-31T10:00:00Z)
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
    assert pattern.match(value), f"Expected ISO 8601 datetime, got: {value}"


def assert_order_structure(data: dict, expected_status: str = None) -> None:
    """Assert response has full order structure per spec 1.1 and 1.2."""
    assert "id" in data
    assert_valid_uuid(data["id"])
    assert "status" in data
    if expected_status:
        assert data["status"] == expected_status
    assert data["status"] in ("PENDING", "CONFIRMED", "CANCELLED")
    assert "total_amount" in data
    assert isinstance(data["total_amount"], (int, float))
    assert data["total_amount"] >= 0
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1
    assert "created_at" in data
    assert_valid_iso8601_datetime(data["created_at"])
    assert "updated_at" in data
    assert_valid_iso8601_datetime(data["updated_at"])

    for item in data["items"]:
        assert "product_id" in item
        assert "quantity" in item
        assert "unit_price" in item
        assert "subtotal" in item
        assert isinstance(item["subtotal"], (int, float))
        assert item["subtotal"] == round(item["quantity"] * item["unit_price"], 2)


def assert_error_structure(data: dict, expected_code: str) -> None:
    """Assert error response format per spec 5.1."""
    assert "error" in data
    err = data["error"]
    assert "code" in err
    assert err["code"] == expected_code
    assert "message" in err
    assert isinstance(err["message"], str)


# --- Section 3.1: Create Order ---


class TestCreateOrder:
    """Spec 3.1 – POST /orders"""

    def test_create_order_returns_201_and_valid_order(
        self, client, base_path
    ):
        """3.1 – Creates new order in PENDING status with computed fields."""
        resp = client.post(f"{base_path}/orders", json=valid_create_payload())
        assert resp.status_code == 201
        data = resp.json()
        assert_order_structure(data, expected_status="PENDING")
        assert data["total_amount"] == 44.48  # 2*9.99 + 1*24.50
        assert data["items"][0]["subtotal"] == 19.98
        assert data["items"][1]["subtotal"] == 24.50
        assert data["created_at"] == data["updated_at"]

    def test_create_order_single_item(self, client, base_path):
        """3.1 – At least one item required; single item is valid."""
        payload = valid_create_payload(
            [{"product_id": "PROD-X", "quantity": 1, "unit_price": 10.00}]
        )
        resp = client.post(f"{base_path}/orders", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert_order_structure(data, expected_status="PENDING")
        assert data["total_amount"] == 10.00
        assert len(data["items"]) == 1

    def test_create_order_amounts_rounded_to_2_decimals(
        self, client, base_path
    ):
        """4.1, 4.2 – total_amount and subtotals rounded to 2 decimal places (half-up)."""
        payload = valid_create_payload(
            [
                {"product_id": "P1", "quantity": 3, "unit_price": 3.333},  # 9.999 -> 10.00
                {"product_id": "P2", "quantity": 1, "unit_price": 0.015},  # 0.015 -> 0.02
            ]
        )
        resp = client.post(f"{base_path}/orders", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["items"][0]["subtotal"] == 10.00
        assert data["items"][1]["subtotal"] == 0.02
        assert data["total_amount"] == 10.02

    def test_create_order_zero_total_allowed(self, client, base_path):
        """4.2 – total_amount >= 0; zero is valid when unit_price is 0."""
        payload = valid_create_payload(
            [{"product_id": "FREE", "quantity": 1, "unit_price": 0}]
        )
        resp = client.post(f"{base_path}/orders", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_amount"] == 0


# --- Section 3.2: Get Order ---


class TestGetOrder:
    """Spec 3.2 – GET /orders/{order_id}"""

    def test_get_order_returns_200_and_order(
        self, client, base_path
    ):
        """3.2 – Returns order by ID."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        assert create_resp.status_code == 201
        order_id = create_resp.json()["id"]

        get_resp = client.get(f"{base_path}/orders/{order_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert_order_structure(data)
        assert data["id"] == order_id

    def test_get_order_not_found_returns_404(self, client, base_path):
        """5.2 – NOT_FOUND when order ID does not exist."""
        order_id = str(uuid.uuid4())
        resp = client.get(f"{base_path}/orders/{order_id}")
        assert resp.status_code == 404
        assert_error_structure(resp.json(), "NOT_FOUND")

    def test_get_order_not_found_error_format(self, client, base_path):
        """5.1, 5.3 – Error response includes code, message, details."""
        order_id = str(uuid.uuid4())
        resp = client.get(f"{base_path}/orders/{order_id}")
        data = resp.json()
        assert "error" in data
        assert "details" in data["error"]
        assert "order_id" in data["error"]["details"]


# --- Section 3.3 & 3.4: Confirm / Cancel ---


class TestConfirmOrder:
    """Spec 3.3 – POST /orders/{order_id}/confirm"""

    def test_confirm_pending_order_transitions_to_confirmed(
        self, client, base_path
    ):
        """2.2, 3.3 – PENDING -> CONFIRMED on confirm."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        order_id = create_resp.json()["id"]

        resp = client.post(f"{base_path}/orders/{order_id}/confirm")
        assert resp.status_code == 200
        data = resp.json()
        assert_order_structure(data, expected_status="CONFIRMED")

    def test_confirm_updates_updated_at(self, client, base_path):
        """1.1 – updated_at changes on status change."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        order_id = create_resp.json()["id"]
        created_updated = create_resp.json()["updated_at"]

        resp = client.post(f"{base_path}/orders/{order_id}/confirm")
        assert resp.status_code == 200
        assert resp.json()["updated_at"] != created_updated

    def test_confirm_not_found_returns_404(self, client, base_path):
        """4.3, 5.2 – Order must exist."""
        order_id = str(uuid.uuid4())
        resp = client.post(f"{base_path}/orders/{order_id}/confirm")
        assert resp.status_code == 404
        assert_error_structure(resp.json(), "NOT_FOUND")

    def test_confirm_cancelled_order_returns_409(
        self, client, base_path
    ):
        """2.2, 4.3, 5.2 – CANCELLED is terminal; cannot confirm."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        order_id = create_resp.json()["id"]
        client.post(f"{base_path}/orders/{order_id}/cancel")

        resp = client.post(f"{base_path}/orders/{order_id}/confirm")
        assert resp.status_code == 409
        assert_error_structure(resp.json(), "INVALID_STATE_TRANSITION")

    def test_confirm_already_confirmed_order_returns_409(
        self, client, base_path
    ):
        """2.2 – CONFIRMED is terminal; no further transitions."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        order_id = create_resp.json()["id"]
        client.post(f"{base_path}/orders/{order_id}/confirm")

        resp = client.post(f"{base_path}/orders/{order_id}/confirm")
        assert resp.status_code == 409
        assert_error_structure(resp.json(), "INVALID_STATE_TRANSITION")


class TestCancelOrder:
    """Spec 3.4 – POST /orders/{order_id}/cancel"""

    def test_cancel_pending_order_transitions_to_cancelled(
        self, client, base_path
    ):
        """2.2, 3.4 – PENDING -> CANCELLED on cancel."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        order_id = create_resp.json()["id"]

        resp = client.post(f"{base_path}/orders/{order_id}/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert_order_structure(data, expected_status="CANCELLED")

    def test_cancel_updates_updated_at(self, client, base_path):
        """1.1 – updated_at changes on status change."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        order_id = create_resp.json()["id"]

        resp = client.post(f"{base_path}/orders/{order_id}/cancel")
        assert resp.status_code == 200
        assert resp.json()["updated_at"] != create_resp.json()["updated_at"]

    def test_cancel_not_found_returns_404(self, client, base_path):
        """4.3, 5.2 – Order must exist."""
        order_id = str(uuid.uuid4())
        resp = client.post(f"{base_path}/orders/{order_id}/cancel")
        assert resp.status_code == 404
        assert_error_structure(resp.json(), "NOT_FOUND")

    def test_cancel_confirmed_order_returns_409(
        self, client, base_path
    ):
        """2.2, 4.3, 5.2 – CONFIRMED is terminal; cannot cancel."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        order_id = create_resp.json()["id"]
        client.post(f"{base_path}/orders/{order_id}/confirm")

        resp = client.post(f"{base_path}/orders/{order_id}/cancel")
        assert resp.status_code == 409
        assert_error_structure(resp.json(), "INVALID_STATE_TRANSITION")

    def test_cancel_already_cancelled_order_returns_409(
        self, client, base_path
    ):
        """2.2 – CANCELLED is terminal; no further transitions."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        order_id = create_resp.json()["id"]
        client.post(f"{base_path}/orders/{order_id}/cancel")

        resp = client.post(f"{base_path}/orders/{order_id}/cancel")
        assert resp.status_code == 409
        assert_error_structure(resp.json(), "INVALID_STATE_TRANSITION")


# --- Section 4: Validation Rules ---


class TestCreateOrderValidation:
    """Spec 4.1 – Create Order validation"""

    def test_create_order_items_required(self, client, base_path):
        """4.1 – items must be present and non-empty."""
        resp = client.post(f"{base_path}/orders", json={})
        assert resp.status_code == 422
        assert_error_structure(resp.json(), "VALIDATION_ERROR")

    def test_create_order_items_empty_array(self, client, base_path):
        """4.1 – items must be non-empty."""
        resp = client.post(f"{base_path}/orders", json={"items": []})
        assert resp.status_code == 422
        assert_error_structure(resp.json(), "VALIDATION_ERROR")

    def test_create_order_quantity_below_one(self, client, base_path):
        """4.1 – Each quantity >= 1."""
        payload = valid_create_payload(
            [{"product_id": "P1", "quantity": 0, "unit_price": 10}]
        )
        resp = client.post(f"{base_path}/orders", json=payload)
        assert resp.status_code == 422
        assert_error_structure(resp.json(), "VALIDATION_ERROR")

    def test_create_order_quantity_negative(self, client, base_path):
        """4.1 – Each quantity >= 1."""
        payload = valid_create_payload(
            [{"product_id": "P1", "quantity": -1, "unit_price": 10}]
        )
        resp = client.post(f"{base_path}/orders", json=payload)
        assert resp.status_code == 422
        assert_error_structure(resp.json(), "VALIDATION_ERROR")

    def test_create_order_unit_price_negative(self, client, base_path):
        """4.1 – Each unit_price >= 0."""
        payload = valid_create_payload(
            [{"product_id": "P1", "quantity": 1, "unit_price": -0.01}]
        )
        resp = client.post(f"{base_path}/orders", json=payload)
        assert resp.status_code == 422
        assert_error_structure(resp.json(), "VALIDATION_ERROR")

    def test_create_order_product_id_empty_string(self, client, base_path):
        """4.1 – Each product_id must be non-empty string."""
        payload = valid_create_payload(
            [{"product_id": "", "quantity": 1, "unit_price": 10}]
        )
        resp = client.post(f"{base_path}/orders", json=payload)
        assert resp.status_code == 422
        assert_error_structure(resp.json(), "VALIDATION_ERROR")

    def test_create_order_product_id_missing(self, client, base_path):
        """4.1 – product_id required."""
        payload = {"items": [{"quantity": 1, "unit_price": 10}]}
        resp = client.post(f"{base_path}/orders", json=payload)
        assert resp.status_code == 422
        assert_error_structure(resp.json(), "VALIDATION_ERROR")

    def test_create_order_quantity_missing(self, client, base_path):
        """4.1 – quantity required."""
        payload = {"items": [{"product_id": "P1", "unit_price": 10}]}
        resp = client.post(f"{base_path}/orders", json=payload)
        assert resp.status_code == 422
        assert_error_structure(resp.json(), "VALIDATION_ERROR")

    def test_create_order_unit_price_missing(self, client, base_path):
        """4.1 – unit_price required."""
        payload = {"items": [{"product_id": "P1", "quantity": 1}]}
        resp = client.post(f"{base_path}/orders", json=payload)
        assert resp.status_code == 422
        assert_error_structure(resp.json(), "VALIDATION_ERROR")

    def test_create_order_validation_error_includes_details(
        self, client, base_path
    ):
        """5.3 – 422 validation errors may include field-level details."""
        payload = valid_create_payload(
            [{"product_id": "P1", "quantity": 0, "unit_price": -1}]
        )
        resp = client.post(f"{base_path}/orders", json=payload)
        data = resp.json()
        assert "error" in data
        assert "details" in data["error"]


# --- Section 5: Error Response Format ---


class TestErrorResponseFormat:
    """Spec 5.1, 5.2 – Error structure and HTTP status mapping"""

    def test_not_found_returns_404(self, client, base_path):
        """5.2 – NOT_FOUND maps to HTTP 404."""
        resp = client.get(f"{base_path}/orders/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_validation_error_returns_422(self, client, base_path):
        """5.2 – VALIDATION_ERROR maps to HTTP 422."""
        resp = client.post(f"{base_path}/orders", json={"items": []})
        assert resp.status_code == 422

    def test_invalid_state_transition_returns_409(self, client, base_path):
        """5.2 – INVALID_STATE_TRANSITION maps to HTTP 409."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        order_id = create_resp.json()["id"]
        client.post(f"{base_path}/orders/{order_id}/confirm")
        resp = client.post(f"{base_path}/orders/{order_id}/cancel")
        assert resp.status_code == 409

    def test_invalid_state_transition_error_includes_details(
        self, client, base_path
    ):
        """5.3 – 409 errors include order_id, current_status, requested_action."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        order_id = create_resp.json()["id"]
        client.post(f"{base_path}/orders/{order_id}/confirm")
        resp = client.post(f"{base_path}/orders/{order_id}/cancel")
        data = resp.json()
        assert "error" in data
        details = data["error"].get("details", {})
        assert "order_id" in details
        assert "current_status" in details
        assert "requested_action" in details


# --- Section 2.3: Immutability ---


class TestImmutability:
    """Spec 2.3 – CONFIRMED orders are locked; items and total cannot change"""

    def test_confirmed_order_preserves_items_and_total(
        self, client, base_path
    ):
        """2.3 – CONFIRMED order preserves items and total (read-only semantics)."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        order_id = create_resp.json()["id"]
        initial_items = create_resp.json()["items"]
        initial_total = create_resp.json()["total_amount"]

        confirm_resp = client.post(f"{base_path}/orders/{order_id}/confirm")
        assert confirm_resp.status_code == 200
        data = confirm_resp.json()
        assert data["items"] == initial_items
        assert data["total_amount"] == initial_total

    def test_get_confirmed_order_returns_unchanged_data(
        self, client, base_path
    ):
        """2.3 – GET on CONFIRMED order returns same items/total as at confirm time."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        order_id = create_resp.json()["id"]
        confirm_resp = client.post(f"{base_path}/orders/{order_id}/confirm")
        confirmed_data = confirm_resp.json()

        get_resp = client.get(f"{base_path}/orders/{order_id}")
        assert get_resp.json()["items"] == confirmed_data["items"]
        assert get_resp.json()["total_amount"] == confirmed_data["total_amount"]
        assert get_resp.json()["status"] == "CONFIRMED"


# --- Section 2: State Semantics ---


class TestStateSemantics:
    """Spec 2.1, 2.3 – State diagram and semantics"""

    def test_new_order_is_pending(self, client, base_path):
        """2.1 – New orders start in PENDING."""
        resp = client.post(f"{base_path}/orders", json=valid_create_payload())
        assert resp.json()["status"] == "PENDING"

    def test_cancelled_order_get_returns_cancelled(
        self, client, base_path
    ):
        """2.3 – CANCELLED order remains CANCELLED; no further actions."""
        create_resp = client.post(
            f"{base_path}/orders", json=valid_create_payload()
        )
        order_id = create_resp.json()["id"]
        client.post(f"{base_path}/orders/{order_id}/cancel")

        get_resp = client.get(f"{base_path}/orders/{order_id}")
        assert get_resp.json()["status"] == "CANCELLED"

    def test_invalid_order_id_format_get_returns_404_or_422(
        self, client, base_path
    ):
        """Order ID must be valid UUID; non-UUID may return 404 or 422."""
        resp = client.get(f"{base_path}/orders/not-a-valid-uuid")
        # Spec does not mandate format validation; 404 (not found) is acceptable
        assert resp.status_code in (404, 422)
