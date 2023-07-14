from sinner.utilities import get_all_base_names


def test_get_all_base_names() -> None:
    # prepare search structures
    class A:
        pass

    class B:
        pass

    class C(A):
        pass

    class D(A, B):
        pass

    class E(D, C):
        pass

    class F(D):
        pass

    # try to search if class have this parent
    assert 'A' not in get_all_base_names(B)
    assert 'A' in get_all_base_names(C)
    assert 'B' not in get_all_base_names(C)
    assert 'A' in get_all_base_names(D)
    assert 'B' in get_all_base_names(D)
    assert 'C' not in get_all_base_names(D)
    assert 'A' in get_all_base_names(E)
    assert 'B' in get_all_base_names(E)
    assert 'C' in get_all_base_names(E)
    assert 'D' in get_all_base_names(F)
    assert 'A' in get_all_base_names(F)
    assert 'B' in get_all_base_names(F)
    assert 'E' not in get_all_base_names(F)
    assert 'C' not in get_all_base_names(F)
