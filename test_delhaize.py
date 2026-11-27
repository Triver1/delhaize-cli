from delhaize import deltas


def test_deltas():
    assert deltas({"A": 2, "B": 1}, {"A": 5, "B": 1, "C": 3}) == [
        {"productCode": "A", "quantityDelta": "3"},
        {"productCode": "C", "quantityDelta": "3"},
    ]
    assert deltas({"A": 2}, {"A": 0}) == [{"productCode": "A", "quantityDelta": "-2"}]


if __name__ == "__main__":
    test_deltas()
    print("ok")
