from sinner.Parameters import Parameters


def test_init() -> None:
    params = Parameters('--key1=value1 --key2 = value2 --key3 value3 value4 --key4').parameters
    assert params.key1 == 'value1'
    assert params.key2 == 'value2'
    assert params.key3 == ['value3', 'value4']
    assert hasattr(params, 'key4') is False  # todo: need to do something with parameters without a value
