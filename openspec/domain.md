# Domain – Order Processing (SDD POC)

## Purpose
This domain models a minimal order processing system used to demonstrate
Spec-Driven Development with AI-assisted workflows.

## Core Concepts

### Order
An Order represents a purchase request made by a customer.

An Order has:
- An identifier
- A status
- A total amount
- A list of order items
- Timestamps

### Order Item
An Order Item represents a product and quantity within an order.

## Order Lifecycle (High Level)

1. Order is created in `PENDING` state
2. Order can be:
   - CONFIRMED
   - CANCELLED
3. Once CONFIRMED, the order is immutable
4. CANCELLED orders cannot be confirmed

## Design Constraints
- Orders cannot be modified after confirmation
- Status transitions must be validated
- All rules must be enforced at the domain/service level
