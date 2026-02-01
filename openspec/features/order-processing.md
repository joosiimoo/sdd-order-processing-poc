# Order Processing System – Functional Specification

> **Single source of truth** for the Order Processing POC. All implementation, tests, and documentation must conform to this spec.

---

## 1. Domain Definitions

### 1.1 Order

An Order represents a purchase request. It is the root aggregate.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | system | Unique identifier, assigned on creation |
| `status` | enum | system | One of: `PENDING`, `CONFIRMED`, `CANCELLED` |
| `total_amount` | decimal(10,2) | yes | Sum of all item subtotals; must be ≥ 0 |
| `items` | array[OrderItem] | yes | At least one item required |
| `created_at` | ISO 8601 datetime | system | Set at creation |
| `updated_at` | ISO 8601 datetime | system | Set at creation; updated on status change |

### 1.2 Order Item

An Order Item represents a product and quantity within an order.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product_id` | string | yes | Product reference (opaque identifier) |
| `quantity` | integer | yes | Must be ≥ 1 |
| `unit_price` | decimal(10,2) | yes | Price per unit; must be ≥ 0 |
| `subtotal` | decimal(10,2) | computed | `quantity * unit_price` |

---

## 2. Order States and Transitions

### 2.1 State Diagram

```
                    ┌───────────┐
                    │  PENDING  │
                    └─────┬─────┘
                          │
            ┌─────────────┼─────────────┐
            │                           │
            ▼                           ▼
    ┌───────────────┐           ┌──────────────┐
    │   CONFIRMED   │           │  CANCELLED   │
    │  (terminal)   │           │  (terminal)  │
    └───────────────┘           └──────────────┘
```

### 2.2 Allowed Transitions

| From | To | Trigger |
|------|----|---------|
| `PENDING` | `CONFIRMED` | Client calls confirm endpoint |
| `PENDING` | `CANCELLED` | Client calls cancel endpoint |
| `CONFIRMED` | *(none)* | Terminal state – no further transitions |
| `CANCELLED` | *(none)* | Terminal state – no further transitions |

### 2.3 State Semantics

- **PENDING**: Order has been created and may be confirmed or cancelled.
- **CONFIRMED**: Order is locked; items and total cannot be changed.
- **CANCELLED**: Order is voided; no further actions allowed.

---

## 3. API Endpoints

Base path: `/api/v1`

### 3.1 Create Order

**`POST /orders`**

Creates a new order in `PENDING` status.

#### Request

```json
{
  "items": [
    {
      "product_id": "PROD-001",
      "quantity": 2,
      "unit_price": 9.99
    },
    {
      "product_id": "PROD-002",
      "quantity": 1,
      "unit_price": 24.50
    }
  ]
}
```

#### Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "total_amount": 44.48,
  "items": [
    {
      "product_id": "PROD-001",
      "quantity": 2,
      "unit_price": 9.99,
      "subtotal": 19.98
    },
    {
      "product_id": "PROD-002",
      "quantity": 1,
      "unit_price": 24.50,
      "subtotal": 24.50
    }
  ],
  "created_at": "2025-01-31T10:00:00Z",
  "updated_at": "2025-01-31T10:00:00Z"
}
```

---

### 3.2 Get Order

**`GET /orders/{order_id}`**

Returns an order by ID.

#### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "total_amount": 44.48,
  "items": [
    {
      "product_id": "PROD-001",
      "quantity": 2,
      "unit_price": 9.99,
      "subtotal": 19.98
    }
  ],
  "created_at": "2025-01-31T10:00:00Z",
  "updated_at": "2025-01-31T10:00:00Z"
}
```

---

### 3.3 Confirm Order

**`POST /orders/{order_id}/confirm`**

Transitions order from `PENDING` to `CONFIRMED`.

#### Request

No body required.

#### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "CONFIRMED",
  "total_amount": 44.48,
  "items": [
    {
      "product_id": "PROD-001",
      "quantity": 2,
      "unit_price": 9.99,
      "subtotal": 19.98
    }
  ],
  "created_at": "2025-01-31T10:00:00Z",
  "updated_at": "2025-01-31T10:15:00Z"
}
```

---

### 3.4 Cancel Order

**`POST /orders/{order_id}/cancel`**

Transitions order from `PENDING` to `CANCELLED`.

#### Request

No body required.

#### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "CANCELLED",
  "total_amount": 44.48,
  "items": [
    {
      "product_id": "PROD-001",
      "quantity": 2,
      "unit_price": 9.99,
      "subtotal": 19.98
    }
  ],
  "created_at": "2025-01-31T10:00:00Z",
  "updated_at": "2025-01-31T10:15:00Z"
}
```

---

## 4. Validation Rules

### 4.1 Create Order

| Rule | Condition | Error |
|------|-----------|-------|
| Items required | `items` must be present and non-empty | `VALIDATION_ERROR` |
| Item quantity | Each `quantity` ≥ 1 | `VALIDATION_ERROR` |
| Item unit_price | Each `unit_price` ≥ 0 | `VALIDATION_ERROR` |
| Product ID | Each `product_id` non-empty string | `VALIDATION_ERROR` |
| Precision | Amounts rounded to 2 decimal places | — |

### 4.2 Total Amount Computation

- `total_amount` = sum of (`quantity` × `unit_price`) for all items
- Round to 2 decimal places (half-up)

### 4.3 State Transitions (Confirm / Cancel)

| Rule | Condition | Error |
|------|-----------|-------|
| Order exists | Order ID must reference an existing order | `NOT_FOUND` |
| Valid transition | Order must be in `PENDING` | `INVALID_STATE_TRANSITION` |

---

## 5. Error Cases

### 5.1 Error Response Format

All errors use this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {}
  }
}
```

`details` is optional and may contain field-level validation info.

### 5.2 Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Request body fails validation |
| `NOT_FOUND` | 404 | Order ID does not exist |
| `INVALID_STATE_TRANSITION` | 409 | Transition not allowed from current state |

### 5.3 Example Error Responses

**404 Not Found – Order does not exist**

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Order not found",
    "details": {
      "order_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  }
}
```

**409 Conflict – Invalid state transition (e.g. confirm a CANCELLED order)**

```json
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "Cannot confirm order in CANCELLED state",
    "details": {
      "order_id": "550e8400-e29b-41d4-a716-446655440000",
      "current_status": "CANCELLED",
      "requested_action": "confirm"
    }
  }
}
```

**422 Unprocessable Entity – Validation error**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "items[0].quantity": "Must be at least 1",
      "items[1].unit_price": "Must be greater than or equal to 0"
    }
  }
}
```

---

## 6. Non-Goals (Out of Scope)

The following are **explicitly out of scope** for this specification and implementation:

| Area | Description |
|------|-------------|
| **Payments** | No payment processing, payment methods, or payment status |
| **Shipping** | No shipping addresses, carriers, tracking, or delivery |
| **Users** | No authentication, authorization, user accounts, or user association with orders |
| **Order updates** | No updating items or quantities after creation (PENDING orders cannot be edited; only confirmed or cancelled) |
| **Order listing** | No list/search/filter orders endpoint; only get-by-id |
| **Inventory** | No stock checks, reservations, or inventory management |
| **Product catalog** | No product validation; `product_id` is an opaque string |
| **Idempotency** | No idempotency keys for create/confirm/cancel |
| **Versioning** | No optimistic locking or version field |
| **Audit log** | No history of state changes or audit trail |
| **Notifications** | No emails, webhooks, or event publishing |

---

## 7. Implementation Notes

- All rules must be enforced at the domain/service layer, not only at the API boundary.
- Status transitions must be atomic; no partial updates.
- Timestamps use UTC and ISO 8601 format.
- UUIDs use RFC 4122 format (e.g. `550e8400-e29b-41d4-a716-446655440000`).
