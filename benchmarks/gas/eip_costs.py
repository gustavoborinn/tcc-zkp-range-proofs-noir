"""Pure gas-cost arithmetic for the post-Pectra EVM (methodology section 3.4).

Implements the EIP-7623 calldata pricing/decomposition and the EIP-4844
fractional blob projection directly from the EIP specifications. No I/O:
everything here is unit-testable against hand-computed vectors.

EIP-7623 (https://eips.ethereum.org/EIPS/eip-7623), non-creation tx:
    tokens_in_calldata = zero_bytes + 4 * nonzero_bytes
    tx.gasUsed = 21000 + max(4 * tokens + execution_gas, 10 * tokens)

EIP-4844 (https://eips.ethereum.org/EIPS/eip-4844):
    one blob = 131,072 bytes, costing GAS_PER_BLOB = 131,072 blob gas
    (1 blob-gas per byte at full utilization).
"""

TX_BASE_COST = 21_000
STANDARD_TOKEN_COST = 4
TOTAL_COST_FLOOR_PER_TOKEN = 10
BLOB_SIZE_BYTES = 131_072
GAS_PER_BLOB = 131_072


def tokens_in_calldata(calldata: bytes) -> int:
    zero = calldata.count(0)
    nonzero = len(calldata) - zero
    return zero + 4 * nonzero


def calldata_standard_cost(calldata: bytes) -> int:
    return STANDARD_TOKEN_COST * tokens_in_calldata(calldata)


def calldata_floor_cost(calldata: bytes) -> int:
    return TOTAL_COST_FLOOR_PER_TOKEN * tokens_in_calldata(calldata)


def floor_binds(gas_used: int, calldata: bytes) -> bool:
    """True when the EIP-7623 floor branch determined tx.gasUsed."""
    return gas_used - TX_BASE_COST == calldata_floor_cost(calldata)


def decompose_gas_used(gas_used: int, calldata: bytes) -> dict:
    """Split a receipt's gasUsed into base, calldata, and pure execution.

    Only valid when the standard branch of EIP-7623 binds (execution-heavy
    transactions); raises otherwise, because in the floor branch the receipt
    does not reveal execution gas.
    """
    tokens = tokens_in_calldata(calldata)
    standard = STANDARD_TOKEN_COST * tokens
    floor = TOTAL_COST_FLOOR_PER_TOKEN * tokens
    execution = gas_used - TX_BASE_COST - standard
    if TX_BASE_COST + max(standard + execution, floor) != gas_used or execution < 0:
        raise ValueError("gasUsed inconsistent with EIP-7623 standard branch")
    if standard + execution <= floor:
        # At or below the floor the receipt does not uniquely reveal
        # execution gas (any execution <= floor - standard yields the same
        # gasUsed), so the decomposition is refused.
        raise ValueError("EIP-7623 floor branch binds; execution gas not recoverable from receipt")
    return {
        "gas_used": gas_used,
        "tx_base_cost": TX_BASE_COST,
        "calldata_bytes": len(calldata),
        "tokens_in_calldata": tokens,
        "calldata_standard_cost": standard,
        "calldata_floor_cost": floor,
        "pure_execution_gas": execution,
    }


def blob_projection(payload_bytes: int) -> dict:
    """Fractional EIP-4844 projection under the batching premise: the payload
    occupies a fraction of a sequencer's blob rather than a standalone
    Type-3 transaction."""
    fraction = payload_bytes / BLOB_SIZE_BYTES
    return {
        "payload_bytes": payload_bytes,
        "blob_size_bytes": BLOB_SIZE_BYTES,
        "blob_fraction": fraction,
        "fractional_blob_gas": payload_bytes * GAS_PER_BLOB // BLOB_SIZE_BYTES,
    }
