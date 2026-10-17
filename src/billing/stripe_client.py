# -*- coding: utf-8 -*-
"""Stripe client wrapper (v6.1), lazy init."""
import os
import time

import stripe


class BillingError(Exception):
    """Raised when Stripe billing is misconfigured."""


def _stripe():
    """Lazy-init the Stripe module with the API key from env."""
    key = os.getenv("STRIPE_SECRET_KEY", "")
    if not key:
        raise BillingError("STRIPE_SECRET_KEY not set")
    stripe.api_key = key
    return stripe


def create_checkout_session(customer_email: str, success_url: str, cancel_url: str) -> dict:
    """Create a Stripe Checkout Session (subscription mode)."""
    s = _stripe()
    session = s.checkout.Session.create(
        mode="subscription",
        customer_email=customer_email,
        line_items=[{"price": os.getenv("STRIPE_PRICE_ID"), "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return {"session_id": session.id, "url": session.url}


def get_customer(email: str) -> dict:
    """Look up a Stripe customer by email (first match)."""
    s = _stripe()
    customers = s.Customer.list(email=email, limit=1)
    if customers.data:
        return {"customer_id": customers.data[0].id}
    return {"customer_id": None}


def record_usage(customer_id: str, quantity: int = 1) -> dict:
    """Record usage. NOTE: ``customer_id`` must be a Stripe customer id (cus_...).

    stripe>=16 removed ``SubscriptionItem.create_usage_record``; usage is now
    reported via ``billing.MeterEvent`` (see STRIPE_METER_EVENT env, default
    ``vishap_analysis``).
    """
    s = _stripe()
    record = s.billing.MeterEvent.create(
        event_name=os.getenv("STRIPE_METER_EVENT", "vishap_analysis"),
        payload={
            "stripe_customer_id": customer_id,
            "value": str(quantity),
        },
        timestamp=int(time.time()),
    )
    return {"usage_record_id": record.identifier}
