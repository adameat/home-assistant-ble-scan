"""Parser for ATC custom-format Bluetooth advertisements."""

from __future__ import annotations

from dataclasses import dataclass

from .const import ATC_LOCAL_NAME_PREFIX, ATC_SERVICE_UUID


@dataclass(frozen=True, slots=True)
class ATCSensorUpdate:
    """Decoded ATC custom-format sensor update."""

    address: str
    name: str
    temperature: float
    humidity: int
    battery: int
    voltage: float
    packet_counter: int


def normalize_address(address: str) -> str:
    """Return a normalized uppercase Bluetooth address."""
    return address.replace("-", ":").upper()


def parse_atc_advertisement(
    address: str,
    local_name: str | None,
    service_data: dict[str, bytes],
) -> ATCSensorUpdate | None:
    """Decode the 13-byte ATC custom advertising format.

    Layout: MAC (6), signed temperature x10 (2), humidity (1), battery
    percent (1), battery millivolts (2), packet counter (1).
    """
    if not local_name or not local_name.startswith(ATC_LOCAL_NAME_PREFIX):
        return None

    payload = next(
        (
            value
            for uuid, value in service_data.items()
            if uuid.lower() == ATC_SERVICE_UUID
        ),
        None,
    )
    if payload is None or len(payload) != 13:
        return None

    normalized_address = normalize_address(address)
    try:
        address_bytes = bytes.fromhex(normalized_address.replace(":", ""))
    except ValueError:
        return None

    if payload[:6] != address_bytes:
        return None

    temperature = int.from_bytes(payload[6:8], "big", signed=True) / 10
    humidity = payload[8]
    battery = payload[9]
    voltage = int.from_bytes(payload[10:12], "big") / 1000

    if not (-50 <= temperature <= 100 and humidity <= 100 and battery <= 100):
        return None

    return ATCSensorUpdate(
        address=normalized_address,
        name=local_name,
        temperature=temperature,
        humidity=humidity,
        battery=battery,
        voltage=voltage,
        packet_counter=payload[12],
    )

