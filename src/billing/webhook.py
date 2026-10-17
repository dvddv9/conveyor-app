# -*- coding: utf-8 -*-
"""Stripe webhook handler (v6.1)."""
import os

import stripe
from fastapi import HTTPException


def handle_stripe_webhook(payload: bytes, sig_header: str) -> dict:
    """Verify a Stripe webhook signature and dispatch by event type."""
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(status_code=500, detail="STRIPE_WEBHOOK_SECRET not set")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    etype = event["type"]
    if etype == "customer.subscription.updated":
        sub = event["data"]["object"]
        return {"ok": True, "event": etype, "subscription_id": sub["id"]}
    return {"ok": True, "ignored": etype}
