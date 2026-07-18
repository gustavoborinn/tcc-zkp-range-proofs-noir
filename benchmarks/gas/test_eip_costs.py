"""Hand-computed vectors for the EIP cost module (spec 005, AC-3)."""

import unittest

from eip_costs import (
    BLOB_SIZE_BYTES,
    blob_projection,
    calldata_floor_cost,
    calldata_standard_cost,
    decompose_gas_used,
    floor_binds,
    tokens_in_calldata,
)


class TestTokens(unittest.TestCase):
    def test_all_zero_bytes(self):
        # 10 zero bytes -> 10 tokens
        self.assertEqual(tokens_in_calldata(bytes(10)), 10)

    def test_all_nonzero_bytes(self):
        # 10 nonzero bytes -> 40 tokens
        self.assertEqual(tokens_in_calldata(b"\x01" * 10), 40)

    def test_mixed(self):
        # 3 zero + 2 nonzero = 3 + 8 = 11 tokens
        data = b"\x00\x01\x00\xff\x00"
        self.assertEqual(tokens_in_calldata(data), 11)
        self.assertEqual(calldata_standard_cost(data), 44)
        self.assertEqual(calldata_floor_cost(data), 110)


class TestDecomposition(unittest.TestCase):
    def test_execution_heavy_standard_branch(self):
        # calldata: 4 nonzero bytes -> 16 tokens; standard = 64, floor = 160
        # execution = 100000 -> gasUsed = 21000 + 64 + 100000 = 121064
        data = b"\xde\xad\xbe\xef"
        parts = decompose_gas_used(121_064, data)
        self.assertEqual(parts["pure_execution_gas"], 100_000)
        self.assertEqual(parts["calldata_standard_cost"], 64)
        self.assertEqual(parts["calldata_floor_cost"], 160)
        self.assertFalse(floor_binds(121_064, data))

    def test_floor_binding_case_rejected(self):
        # Same calldata, tiny execution (10 gas): standard branch total = 74,
        # floor = 160 -> gasUsed = 21000 + 160 = 21160; decomposition must
        # refuse because execution gas is not recoverable.
        data = b"\xde\xad\xbe\xef"
        self.assertTrue(floor_binds(21_160, data))
        with self.assertRaises(ValueError):
            decompose_gas_used(21_160, data)

    def test_inconsistent_gas_used_rejected(self):
        with self.assertRaises(ValueError):
            decompose_gas_used(20_000, b"\x01")  # below base cost


class TestBlobProjection(unittest.TestCase):
    def test_full_blob(self):
        parts = blob_projection(BLOB_SIZE_BYTES)
        self.assertEqual(parts["blob_fraction"], 1.0)
        self.assertEqual(parts["fractional_blob_gas"], BLOB_SIZE_BYTES)

    def test_u64_proof_payload(self):
        # 7232-byte proof + 64-byte public inputs = 7296 bytes
        parts = blob_projection(7_296)
        self.assertAlmostEqual(parts["blob_fraction"], 7_296 / 131_072)
        self.assertEqual(parts["fractional_blob_gas"], 7_296)


if __name__ == "__main__":
    unittest.main()
