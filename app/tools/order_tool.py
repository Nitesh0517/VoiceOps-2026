"""Identity-gated order lookup tool matching official specification."""
import os
from typing import Dict, Any, Optional
from app.database.repository import DatabaseRepository


class OrderTool:
    def __init__(self, repo: Optional[DatabaseRepository] = None):
        self.repo = repo or DatabaseRepository()

    def lookup_order(self, order_id: str, verification_value: Optional[str] = None) -> Dict[str, Any]:
        """
        Lookup a synthetic order, disclosing details ONLY after caller verification.
        
        Calling with order_id alone yields a verification-required message.
        Verification requires caller to provide registered phone's last 4 digits OR delivery pincode.
        """
        oid = "".join(ch for ch in str(order_id) if "0" <= ch <= "9")
        if not oid:
            return {
                "found": False,
                "verified": False,
                "verification_required": False,
                "message": "Invalid order ID."
            }

        # If no verification proof provided yet, return verification gate
        if verification_value is None or str(verification_value).strip() == "":
            return {
                "verification_required": True,
                "order_id": oid,
                "message": "Ask for the registered phone last 4 digits OR delivery pincode."
            }

        proof = "".join(ch for ch in str(verification_value) if "0" <= ch <= "9")
        order = self.repo.get_order(oid)
        if order:
            customer = self.repo.get_customer(order["customer_id"])
            if customer:
                phone_suffix = customer["phone"][-4:]
                pincode = str(order["delivery_pincode"])
                
                is_phone_match = len(proof) == 4 and proof == phone_suffix
                is_pin_match = len(proof) == 6 and proof == pincode
                
                if is_phone_match or is_pin_match:
                    items = self.repo.get_order_items(oid)
                    first_name = customer["name"].split()[0] if customer["name"] else "Customer"
                    
                    # Return verified details (never disclose phone_last4 in output as per validate_dataset.py)
                    res = dict(order)
                    res.update({
                        "found": True,
                        "verified": True,
                        "verification_required": False,
                        "items": items,
                        "customer_first_name": first_name,
                        "is_plus": bool(customer["is_plus"])
                    })
                    if "phone" in res:
                        del res["phone"]
                    return res
                    
        return {
            "found": False,
            "verified": False,
            "verification_required": True,
            "message": "Verification failed or order not found."
        }
