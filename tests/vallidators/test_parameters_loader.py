from sinner.Parameters import Parameters


def test_init() -> None:
    params = Parameters.command_line_to_namespace('--key4 --key1=value1 --key2=value2 --key3 value3 value4 --key10')
    assert params.key1 == 'value1'
    assert params.key2 == 'value2'
    assert params.key3 == ['value3', 'value4']
    assert params.key4 is True
    assert params.key10 is True
