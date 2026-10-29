import unittest

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

    def test_decodes_transfer_amount_as_raw_units(self):
        result = inspect_transaction({
            "to": TOKEN,
            "data": "0xa9059cbb" + word(int(RECIPIENT, 16)) + word(42),
        })
        self.assertEqual(result["recipient"], RECIPIENT)
        self.assertEqual(result["amount_raw"], "42")

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

    def test_warns_when_native_value_is_attached(self):
        result = inspect_transaction({
            "to": TOKEN,
            "data": "0xa9059cbb" + word(int(RECIPIENT, 16)) + word(1),
            "value_wei": "1",
        })
        self.assertIn("ETH is also attached", result["native_value_note"])


if __name__ == "__main__":
    unittest.main()
