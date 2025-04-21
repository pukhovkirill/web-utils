import pytest
from network.icmp import icmp_utils as utils
from unittest.mock import patch


def test_to_ip():
    # Arrange
    invalid_domain = "invalid.domain"
    valid_domain = "google.com"
    expected_ip = "8.8.8.8"

    # Act & Assert
    with pytest.raises(ValueError, match="Unable to resolve invalid.domain"):
        utils.to_ip(invalid_domain)

    with patch("socket.gethostbyname", return_value=expected_ip):
        result = utils.to_ip(valid_domain)
        assert result == expected_ip


def test_is_valid_ip4_address():
    # Arrange
    valid_ips = ["192.168.1.1", "255.255.255.255"]
    invalid_ips = ["256.256.256.256", "invalid_ip"]

    # Act & Assert
    for ip in valid_ips:
        assert utils.is_valid_ip4_address(ip) is True

    for ip in invalid_ips:
        assert utils.is_valid_ip4_address(ip) is False


def test_calculate_checksum():
    # Arrange
    data = b'\x08\x00\x00\x00'  # Example ICMP header bytes
    expected_checksum = 0xF7FF
    empty_data = b''
    expected_empty_checksum = 0xFFFF

    # Act
    result = utils.calculate_checksum(data)
    empty_result = utils.calculate_checksum(empty_data)

    # Assert
    assert result == expected_checksum
    assert empty_result == expected_empty_checksum


def test_calculate_rtt():
    # Arrange
    rtt_values = [10, 20, 30]
    empty_rtt_values = []
    single_rtt_value = [50]
    expected_avg_rtt = 20.0
    expected_empty_rtt = float("inf")
    expected_single_rtt = 50.0

    # Act
    result = utils.calculate_rtt(rtt_values)
    empty_result = utils.calculate_rtt(empty_rtt_values)
    single_result = utils.calculate_rtt(single_rtt_value)

    # Assert
    assert result == expected_avg_rtt
    assert empty_result == expected_empty_rtt
    assert single_result == expected_single_rtt

