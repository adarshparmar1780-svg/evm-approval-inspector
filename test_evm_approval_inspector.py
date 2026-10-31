import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evm_approval_inspector import UINT256_MAX, inspect_transaction


TOKEN = "0x1111111111111111111111111111111111111111"
SPENDER = "0x2222222222222222222222222222222222222222"
RECIPIENT = "0x3333333333333333333333333333333333333333"


def word(value):
    return f"{value:064x}"


class InspectTransactionTests(unittest.TestCase):
    def test_flags_max_approval(self):
        result = inspect_transaction({
            "to": TOKEN,
            "data": "0x095ea7b3" + word(int(SPENDER, 16)) + word(UINT256_MAX),
        })
        self.assertEqual(result["function"], "approve")
        self.assertEqual(result["spender"], SPENDER)
        self.assertIn("max uint256", result["allowance_note"])

    def test_labels_zero_approval_as_zero_allowance(self):
        result = inspect_transaction({
            "to": TOKEN,
            "data": "0x095ea7b3" + word(int(SPENDER, 16)) + word(0),
        })
        self.assertIn("sets the spender's allowance to zero", result["allowance_note"])

    def test_decodes_transfer_amount_as_raw_units(self):
        result = inspect_transaction({
            "to": TOKEN,
            "data": "0xa9059cbb" + word(int(RECIPIENT, 16)) + word(42),
        })
        self.assertEqual(result["recipient"], RECIPIENT)
        self.assertEqual(result["amount_raw"], "42")

    def test_decodes_transfer_from_owner_recipient_and_amount(self):
        result = inspect_transaction({
            "to": TOKEN,
            "data": "0x23b872dd" + word(int(SPENDER, 16)) + word(int(RECIPIENT, 16)) + word(75),
        })
        self.assertEqual(result["function"], "transferFrom")
        self.assertEqual(result["owner"], SPENDER)
        self.assertEqual(result["recipient"], RECIPIENT)
        self.assertEqual(result["amount_raw"], "75")
        self.assertIn("cannot verify allowance offline", result["transfer_note"])

    def test_rejects_short_transfer_from_calldata(self):
        with self.assertRaisesRegex(ValueError, "exactly three ABI words"):
            inspect_transaction({"to": TOKEN, "data": "0x23b872dd"})

    def test_rejects_unsupported_selector(self):
        with self.assertRaisesRegex(ValueError, "unsupported selector"):
            inspect_transaction({"to": TOKEN, "data": "0xdeadbeef" + "0" * 128})

    def test_rejects_short_calldata(self):
        with self.assertRaisesRegex(ValueError, "exactly two ABI words"):
            inspect_transaction({"to": TOKEN, "data": "0xa9059cbb"})

    def test_rejects_malformed_address_padding(self):
        with self.assertRaisesRegex(ValueError, "ABI-padded"):
            inspect_transaction({"to": TOKEN, "data": "0xa9059cbb" + "f" * 64 + word(1)})

    def test_rejects_negative_native_value(self):
        with self.assertRaisesRegex(ValueError, "non-negative"):
            inspect_transaction({
                "to": TOKEN,
                "data": "0xa9059cbb" + word(int(RECIPIENT, 16)) + word(1),
                "value_wei": "-1",
            })

    def test_rejects_boolean_native_value(self):
        with self.assertRaisesRegex(ValueError, "non-negative decimal integer"):
            inspect_transaction({
                "to": TOKEN,
                "data": "0xa9059cbb" + word(int(RECIPIENT, 16)) + word(1),
                "value_wei": True,
            })

    def test_rejects_non_decimal_native_value(self):
        with self.assertRaisesRegex(ValueError, "non-negative decimal integer"):
            inspect_transaction({
                "to": TOKEN,
                "data": "0xa9059cbb" + word(int(RECIPIENT, 16)) + word(1),
                "value_wei": "one",
            })

    def test_accepts_maximum_uint256_native_value(self):
        result = inspect_transaction({
            "to": TOKEN,
            "data": "0xa9059cbb" + word(int(RECIPIENT, 16)) + word(1),
            "value_wei": str(UINT256_MAX),
        })
        self.assertEqual(result["value_wei"], str(UINT256_MAX))

    def test_rejects_native_value_above_uint256(self):
        with self.assertRaisesRegex(ValueError, "fit in uint256"):
            inspect_transaction({
                "to": TOKEN,
                "data": "0xa9059cbb" + word(int(RECIPIENT, 16)) + word(1),
                "value_wei": str(UINT256_MAX + 1),
            })

    def test_warns_when_native_value_is_attached(self):
        result = inspect_transaction({
            "to": TOKEN,
            "data": "0xa9059cbb" + word(int(RECIPIENT, 16)) + word(1),
            "value_wei": "1",
        })
        self.assertIn("ETH is also attached", result["native_value_note"])

    def test_json_flag_prints_parseable_report(self):
        project_dir = Path(__file__).parent
        result = subprocess.run(
            [
                sys.executable,
                str(project_dir / "evm_approval_inspector.py"),
                "--json",
                str(project_dir / "examples" / "transfer.json"),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        report = json.loads(result.stdout)
        self.assertEqual(report["function"], "transfer")
        self.assertEqual(report["amount_raw"], "42")


    def test_cli_rejects_duplicate_json_fields(self):
        project_dir = Path(__file__).parent
        with tempfile.TemporaryDirectory() as temp_dir:
            transaction_path = Path(temp_dir) / "duplicate.json"
            transaction_path.write_text(
                '{"to":"' + TOKEN + '","to":"' + RECIPIENT + '","data":"0x"}',
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(project_dir / "evm_approval_inspector.py"), str(transaction_path)],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate JSON key: 'to'", result.stderr)

if __name__ == "__main__":
    unittest.main()
