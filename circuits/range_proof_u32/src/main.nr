// Range proof variant with 32-bit width restriction (methodology section 3.3).
// Proves `a <= v <= b` with `v` private; comparison operators over sized
// integers compile to bit-width constraints handled by the backend's
// lookup-oriented range machinery, which is the cost under measurement.
fn main(v: u32, a: pub u32, b: pub u32) {
    assert(v >= a, "value below lower bound");
    assert(v <= b, "value above upper bound");
}

#[test]
fn test_interior_value() {
    main(50, 10, 100);
}

#[test]
fn test_at_lower_bound() {
    main(10, 10, 100);
}

#[test]
fn test_at_upper_bound() {
    main(100, 10, 100);
}

#[test(should_fail_with = "value below lower bound")]
fn test_below_range() {
    main(5, 10, 100);
}

#[test(should_fail_with = "value above upper bound")]
fn test_above_range() {
    main(150, 10, 100);
}
