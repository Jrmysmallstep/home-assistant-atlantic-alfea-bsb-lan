"""Validated BSB-LAN JSON access for per-circuit operating regimes.

Independent of the 40 MQTT log slots. Writes are restricted to 700/1000 and
enumeration values 1/2/3. Protection (0) remains controlled by the existing
climate OFF path, never by a preset.
"""
from __future__ import annotations

import asyncio
import logging
from urllib.parse import urlparse

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)
PARAMETERS = {1: 700, 2: 1000}
PRESETS = {"Auto": 1, "ECO": 2, "Confort": 3}
REVERSE_PRESETS = {value: key for key, value in PRESETS.items()}


def valid_base_url(value: str) -> bool:
    """Only allow an explicitly configured HTTP(S) BSB-LAN origin."""
    parsed = urlparse(value.strip())
    return (parsed.scheme in ("http", "https") and bool(parsed.hostname)
            and parsed.username is None and parsed.password is None
            and not parsed.query and not parsed.fragment)


class RegimeAPI:
    """Read and set native Siemens 700/1000 with confirmed readback."""

    def __init__(self, hass: HomeAssistant, base_url: str) -> None:
        if not valid_base_url(base_url):
            raise ValueError("Adresse BSB-LAN invalide")
        self._session = async_get_clientsession(hass)
        self._base = base_url.rstrip("/")
        self._lock = asyncio.Lock()

    async def read(self, circuit: int) -> int | None:
        parameter = PARAMETERS[circuit]
        async with asyncio.timeout(8):
            async with self._session.get(f"{self._base}/JQ={parameter}") as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        item = data.get(str(parameter))
        if not isinstance(item, dict) or item.get("error") != 0:
            return None
        try:
            code = int(item["value"])
        except (TypeError, ValueError, KeyError):
            return None
        return code if code in (0, 1, 2, 3) else None

    async def set_preset(self, circuit: int, preset: str) -> int:
        """Write only safe regimes and confirm actual value via a fresh JQ."""
        if preset not in PRESETS:
            raise ValueError("Régime non pris en charge")
        parameter = PARAMETERS[circuit]
        desired = PRESETS[preset]
        async with self._lock:
            # Refuse writes if current status is unreadable.
            before = await self.read(circuit)
            if before is None:
                raise ValueError(f"Lecture BSB {parameter} impossible, écriture refusée")
            if before == desired:
                return desired
            payload = {
                "parameter": parameter, "value": str(desired),
                "type": 1, "destination": 0,
            }
            async with asyncio.timeout(8):
                async with self._session.post(f"{self._base}/JS", json=payload) as response:
                    response.raise_for_status()
                    result = await response.json(content_type=None)
            # BSB-LAN /JS returns {"700": {"status": 1, "destination": 0}}.
            # Still read back the actual value with /JQ below.
            outcome = result.get(str(parameter)) if isinstance(result, dict) else None
            if not isinstance(outcome, dict) or outcome.get("status") != 1:
                raise ValueError(f"BSB-LAN did not acknowledge {parameter}: {result!r}")
            for _ in range(5):
                confirmed = await self.read(circuit)
                if confirmed == desired:
                    return desired
                await asyncio.sleep(0.5)
            raise ValueError(f"Retour BSB {parameter} non confirmé après écriture")
