// Baseline circuit for the bit-width experiment (methodology section 3.3).
//
// `Field` has no ordering over BN254, so this baseline cannot express
// `a <= v <= b`. It instead binds the private witness to both public bounds
// through multiplicative arithmetic and a single inverse check, involving no
// bit decomposition or lookup-oriented range machinery. Trivial algebraic
// identities are eliminated by the compiler (0 ACIR opcodes), which would
// invalidate the baseline; this formulation compiles to a nonzero circuit.
fn main(v: Field, a: pub Field, b: pub Field) {
    assert((v - a) * (b - v) != 0, "value equals an interval bound");
}

#[test]
fn test_interior_value() {
    main(50, 10, 100);
}

#[test(should_fail_with = "value equals an interval bound")]
fn test_value_at_lower_bound() {
    main(10, 10, 100);
}

#[test(should_fail_with = "value equals an interval bound")]
fn test_value_at_upper_bound() {
    main(100, 10, 100);
}
