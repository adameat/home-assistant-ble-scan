"""Tests for the ATC custom-format parser."""

from custom_components.ble_scan.const import ATC_SERVICE_UUID
from custom_components.ble_scan.parser import parse_atc_advertisement


def test_parse_real_atc_packet() -> None:
    """Decode a packet captured from an ATC LYWSD03MMC."""
    update = parse_atc_advertisement(
        "A4:C1:38:6E:3E:9A",
        "ATC_6E3E9A",
        {
            ATC_SERVICE_UUID: bytes.fromhex(
                "a4c1386e3e9a012032450b1887"
            )
        },
    )

    assert update is not None
    assert update.temperature == 28.8
    assert update.humidity == 50
    assert update.battery == 69
    assert update.voltage == 2.84
    assert update.packet_counter == 135


def test_parse_negative_temperature() -> None:
    """Decode signed big-endian temperatures."""
    update = parse_atc_advertisement(
        "A4:C1:38:00:00:01",
        "ATC_000001",
        {
            ATC_SERVICE_UUID: bytes.fromhex(
                "a4c138000001ff9c2a630bb800"
            )
        },
    )

    assert update is not None
    assert update.temperature == -10.0


def test_reject_smart_tag_and_wrong_mac() -> None:
    """Ignore non-ATC names and payloads that do not belong to the address."""
    payload = bytes.fromhex("a4c1386e3e9a012032450b1887")
    assert (
        parse_atc_advertisement(
            "A4:C1:38:6E:3E:9A", "SmartTag", {ATC_SERVICE_UUID: payload}
        )
        is None
    )
    assert (
        parse_atc_advertisement(
            "A4:C1:38:00:00:00", "ATC_6E3E9A", {ATC_SERVICE_UUID: payload}
        )
        is None
    )
