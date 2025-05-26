from unittest.mock import patch

import pytest

from network.icmp import icmp_utils as utils


def test_to_ip():
    """
    Test the to_ip function for domain name resolution:
    - Should raise ValueError when the domain cannot be resolved.
    - Should return the correct IP address for a valid domain.
    """
    # Arrange: define an invalid and a valid domain, and the expected IP
    invalid_domain = "invalid.domain"
    valid_domain = "google.com"
    expected_ip = "8.8.8.8"

    # Act & Assert: invalid domain resolution should raise ValueError
    with pytest.raises(ValueError, match="Unable to resolve invalid.domain"):
        utils.to_ip(invalid_domain)

    # Act: patch socket.gethostbyname to return the expected IP for the valid domain
    with patch("socket.gethostbyname", return_value=expected_ip):
        result = utils.to_ip(valid_domain)
        # Assert: the result matches the expected IP
        assert result == expected_ip


def test_is_valid_ip4_address():
    """
    Test the is_valid_ip4_address function:
    - Returns True for syntactically valid IPv4 addresses.
    - Returns False for invalid IPv4 strings.
    """
    # Arrange: lists of valid and invalid IPv4 addresses
    valid_ips = ["192.168.1.1", "255.255.255.255"]
    invalid_ips = ["256.256.256.256", "invalid_ip"]

    # Act & Assert: valid addresses should return True
    for ip in valid_ips:
        assert utils.is_valid_ip4_address(ip) is True

    # Act & Assert: invalid addresses should return False
    for ip in invalid_ips:
        assert utils.is_valid_ip4_address(ip) is False


def test_calculate_checksum():
    """
    Test the calculate_checksum function:
    - Produces the correct checksum for non-empty data.
    - Produces 0xFFFF for empty data input.
    """
    # Arrange: sample data and expected checksums
    data = b'\x08\x00\x00\x00'  # Example ICMP header bytes
    expected_checksum = 0xF7FF
    empty_data = b''
    expected_empty_checksum = 0xFFFF

    # Act: compute checksums
    result = utils.calculate_checksum(data)
    empty_result = utils.calculate_checksum(empty_data)

    # Assert: checksum matches expected values
    assert result == expected_checksum
    assert empty_result == expected_empty_checksum


def test_calculate_rtt():
    """
    Test the calculate_rtt function:
    - Computes the average RTT for a list of values.
    - Returns infinity for an empty list.
    - Returns the single RTT value when only one measurement is given.
    """
    # Arrange: RTT sample lists and expected outcomes
    rtt_values = [10, 20, 30]
    empty_rtt_values = []
    single_rtt_value = [50]
    expected_avg_rtt = 20.0
    expected_empty_rtt = float("inf")
    expected_single_rtt = 50.0

    # Act: calculate RTT statistics
    result = utils.calculate_rtt(rtt_values)
    empty_result = utils.calculate_rtt(empty_rtt_values)
    single_result = utils.calculate_rtt(single_rtt_value)

    # Assert: results match the expected average, infinity, and single value
    assert result == expected_avg_rtt
    assert empty_result == expected_empty_rtt
    assert single_result == expected_single_rtt
