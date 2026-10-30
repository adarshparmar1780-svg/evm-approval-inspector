# EVM Approval Inspector

A small offline Python CLI that decodes two common ERC-20 calls: `approve(address,uint256)` and `transfer(address,uint256)`. It prints the target token contract, the spender or recipient, and the amount in raw integer units. A max-`uint256` approval is called out for review.

This is a learning tool for inspecting transaction data before signing. It does not connect to a wallet, contact an RPC endpoint, sign or send transactions, inspect contract code, resolve token decimals, verify signatures, or simulate execution. A warning is a prompt to investigate, not proof that a contract is malicious. Never paste a seed phrase or private key into this tool.

## Run

Requires Python 3.10 or newer; no third-party packages are used.

```powershell
py .\evm_approval_inspector.py .\examples\approve-max.json
py .\evm_approval_inspector.py .\examples\transfer.json
py .\evm_approval_inspector.py --json .\examples\transfer.json
```

Input JSON uses `to` for the token contract, `data` for the full calldata, and optional `value_wei` for attached ETH in raw wei. Add `--json` to print a machine-readable JSON report. The two included examples use placeholder addresses and are not real transaction recommendations.

## Check

```powershell
py -m unittest -v
```

AI-assisted initial draft. Review the code, run the examples and tests, and understand its limits before presenting the project as your work.
