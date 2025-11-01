from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.files import append_jsonl, read_json, write_json


@dataclass(slots=True)
class PurchaseRecord:
    user_id: int
    charge_id: str
    amount: int
    payload: str
    ts: int


@dataclass(slots=True)
class OrderRecord:
    user_id: int
    payload: str
    amount: int
    status: str
    ts: int
    reason: str | None


@dataclass(slots=True)
class LedgerRecord:
    user_id: int
    amount: int
    kind: str
    charge_id: Optional[str]
    comment: Optional[str]
    ts: int


class StorageService:
    def __init__(self, purchases: Path, orders: Path, ledger: Path) -> None:
        self.purchases_path = purchases
        self.orders_path = orders
        self.ledger_path = ledger

    def add_purchase(self, user_id: int, charge_id: str, amount: int, payload: str) -> PurchaseRecord:
        record = PurchaseRecord(user_id=user_id, charge_id=charge_id, amount=amount, payload=payload, ts=int(time.time()))
        append_jsonl(self.purchases_path, record.__dict__)
        return record

    def add_order(
        self,
        user_id: int,
        payload: str,
        amount: int,
        status: str,
        *,
        reason: str | None = None,
    ) -> OrderRecord:
        record = OrderRecord(
            user_id=user_id,
            payload=payload,
            amount=amount,
            status=status,
            ts=int(time.time()),
            reason=reason,
        )
        append_jsonl(self.orders_path, record.__dict__)
        return record

    def add_ledger_entry(self, user_id: int, amount: int, kind: str, *, charge_id: Optional[str] = None, comment: Optional[str] = None) -> LedgerRecord:
        record = LedgerRecord(
            user_id=user_id,
            amount=amount,
            kind=kind,
            charge_id=charge_id,
            comment=comment,
            ts=int(time.time()),
        )
        append_jsonl(self.ledger_path, record.__dict__)
        return record

    def read_purchases(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        return _read_jsonl(self.purchases_path, limit=limit)

    def find_purchase(self, charge_id: str) -> Dict[str, Any] | None:
        if not self.purchases_path.exists():
            return None
        from services.files import locked_file
        import ujson

        with locked_file(self.purchases_path, "r") as file_obj:
            for line in file_obj:
                if not line.strip():
                    continue
                data = ujson.loads(line)
                if data.get("charge_id") == charge_id:
                    return data
        return None

    def charge_exists(self, charge_id: str) -> bool:
        if not self.purchases_path.exists():
            return False
        from services.files import locked_file

        with locked_file(self.purchases_path, "r") as file_obj:
            for line in file_obj:
                if not line.strip():
                    continue
                import ujson

                data = ujson.loads(line)
                if data.get("charge_id") == charge_id:
                    return True
        return False

    def read_orders(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        return _read_jsonl(self.orders_path, limit=limit)

    def read_ledger(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        return _read_jsonl(self.ledger_path, limit=limit)

    def compute_balance(self) -> int:
        total = 0
        for purchase in self.read_purchases():
            total += int(purchase.get("amount", 0))
        for entry in self.read_ledger():
            total += int(entry.get("amount", 0))
        return total

    def compute_user_balance(self, user_id: int) -> int:
        total = 0
        for purchase in self.read_purchases():
            if int(purchase.get("user_id", 0)) == user_id:
                total += int(purchase.get("amount", 0))
        for entry in self.read_ledger():
            if int(entry.get("user_id", 0)) == user_id:
                total += int(entry.get("amount", 0))
        return total


def _read_jsonl(path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    from services.files import locked_file

    with locked_file(path, "r") as file_obj:
        lines = file_obj.readlines()
    if limit is not None:
        lines = lines[-limit:]
    import ujson

    return [ujson.loads(line) for line in lines if line.strip()]
