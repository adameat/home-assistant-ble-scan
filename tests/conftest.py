"""Load the pure parser without importing Home Assistant hardware modules."""

import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).parents[1]
CUSTOM_COMPONENTS = ROOT / "custom_components"
INTEGRATION = CUSTOM_COMPONENTS / "ble_scan"

custom_components_package = ModuleType("custom_components")
custom_components_package.__path__ = [str(CUSTOM_COMPONENTS)]
sys.modules.setdefault("custom_components", custom_components_package)

integration_package = ModuleType("custom_components.ble_scan")
integration_package.__path__ = [str(INTEGRATION)]
sys.modules.setdefault("custom_components.ble_scan", integration_package)

