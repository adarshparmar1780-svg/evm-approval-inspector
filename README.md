# EVM Approval Inspector

A small offline Python CLI that decodes ERC-20 `approve(address,uint256)`, `transfer(address,uint256)`, and `transferFrom(address,address,uint256)` calls. It prints the target token contract, relevant addresses, and amount in raw integer units. A max-`uint256` approval is called out for review.

This is a learning tool for inspecting transaction data before signing. It does not connect to a wallet, contact an RPC endpoint, sign or send transactions, inspect contract code, resolve token decimals, verify signatures, or simulate execution. A warning is a prompt to investigate, not proof that a contract is malicious. Never paste a seed phrase or private key into this tool.

## Run

Requires Python 3.10 or newer; no third-party packages are used.

```powershell
py .\evm_approval_inspector.py .\examples\approve-max.json
py .\evm_approval_inspector.py .\examples\transfer.json
py .\evm_approval_inspector.py --json .\examples\transfer.json
py .\evm_approval_inspector.py .\examples\transfer-from.json
```

Input JSON uses `to` for the token contract, `data` for the full calldata, and optional `value_wei` for attached ETH in raw wei. Add `--json` to print a machine-readable JSON report. The included examples use placeholder addresses and are not real transaction recommendations.

The `transferFrom` preview shows the token owner, recipient, and raw amount. It cannot check whether the transaction sender has the required allowance. Function details follow the [ERC-20 specification](https://eips.ethereum.org/EIPS/eip-20).

## Check

```powershell
py -m unittest -v
```

AI-assisted initial draft. Review the code, run the examples and tests, and understand its limits before presenting the project as your work.
