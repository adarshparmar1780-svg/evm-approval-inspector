#!/usr/bin/env python3
"""Explain a small, explicit set of ERC-20 transaction calls offline."""

import argparse
import json
import re
import sys
from pathlib import Path


UINT256_MAX = (1 << 256) - 1
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
HEX_RE = re.compile(r"^0x(?:[0-9a-fA-F]{2})*$")
CALLS = {
    "095ea7b3": ("approve", ("spender",), "allowance_raw"),
    "a9059cbb": ("transfer", ("recipient",), "amount_raw"),
    "23b872dd": ("transferFrom", ("owner", "recipient"), "amount_raw"),
}


def _address_word(word):
    if len(word) != 64 or word[:24] != "0" * 24:
        raise ValueError("address argument is not correctly ABI-padded")
    return "0x" + word[24:].lower()


def inspect_transaction(transaction):
    if not isinstance(transaction, dict):
        raise ValueError("input JSON must be an object")

    token = transaction.get("to")
    if not isinstance(token, str) or not ADDRESS_RE.fullmatch(token):
        raise ValueError("'to' must be a 20-byte 0x-prefixed token address")

    data = transaction.get("data")
    if not isinstance(data, str) or not HEX_RE.fullmatch(data):
        raise ValueError("'data' must be 0x-prefixed even-length hexadecimal")
    if len(data) < 10:
        raise ValueError("'data' must contain a 4-byte function selector")

    value_text = transaction.get("value_wei", "0")
    if not isinstance(value_text, (str, int)) or isinstance(value_text, bool):
        raise ValueError("'value_wei' must be a non-negative decimal integer")
    try:
        value_wei = int(value_text, 10) if isinstance(value_text, str) else value_text
    except ValueError as exc:
        raise ValueError("'value_wei' must be a non-negative decimal integer") from exc
    if value_wei < 0:
        raise ValueError("'value_wei' must be non-negative")
    if value_wei > UINT256_MAX:
        raise ValueError("'value_wei' must fit in uint256")

    selector = data[2:10].lower()
    if selector not in CALLS:
        raise ValueError(f"unsupported selector 0x{selector}; only approve and transfer are decoded")
    function, address_names, amount_name = CALLS[selector]
    expected_words = len(address_names) + 1
    if len(data) != 10 + expected_words * 64:
        word_count = "two" if expected_words == 2 else "three"
        raise ValueError(f"call data must contain exactly {word_count} ABI words for this function")

    arguments = data[10:]
    addresses = [
        _address_word(arguments[offset:offset + 64])
        for offset in range(0, len(address_names) * 64, 64)
    ]
    amount = int(arguments[len(address_names) * 64:], 16)
    report = {
        "token_contract": token.lower(),
        "function": function,
    }
    report.update(zip(address_names, addresses))
    report[amount_name] = str(amount)
    report["value_wei"] = str(value_wei)

    if function == "approve":
        report["allowance_note"] = (
            "max uint256 allowance; review the spender and whether this approval is needed"
            if amount == UINT256_MAX
            else "zero allowance; this call sets the spender's allowance to zero"
            if amount == 0
            else "finite allowance; review the spender and raw amount"
        )
    if value_wei:
        report["native_value_note"] = "ETH is also attached to this call; verify why before signing"
    if function == "transferFrom":
        report["transfer_note"] = "Review the owner, recipient, and sender authorization; this tool cannot verify allowance offline"
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Decode one ERC-20 approve, transfer, or transferFrom call from a JSON transaction (offline, read-only)."
    )
    parser.add_argument("transaction_json", type=Path, help="JSON file with to, data, and optional value_wei")
    parser.add_argument("--json", action="store_true", dest="json_output", help="print the decoded report as JSON")
    args = parser.parse_args()

    try:
        transaction = json.loads(args.transaction_json.read_text(encoding="utf-8"))
        report = inspect_transaction(transaction)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Could not inspect transaction: {exc}", file=sys.stderr)
        return 2

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        print("Offline ERC-20 call preview")
        for key, value in report.items():
            label = key.replace("_", " ").capitalize()
            print(f"{label}: {value}")
        print("This preview does not verify contract code, token decimals, signatures, or execution effects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
