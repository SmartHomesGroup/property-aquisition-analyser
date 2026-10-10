import json
from pathlib import Path

import httpx
import pytest

from paa.api.routes.listings import EngineError, call_engine, parse_address
from paa.config import Settings
from paa.listings import (
    ListingUrlError,
    find_postcode,
    normalise_url,
    property_type_code,
    summarise,
    to_int,
    unwrap_result,
)

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "n8n_response.json").read_text())


def test_normalise_url_strips_fragment_and_tracking() -> None:
    clean, key = normalise_url("https://www.rightmove.co.uk/properties/91660647/?utm_source=x#/")
    assert clean == "https://www.rightmove.co.uk/properties/91660647"
    assert key == "www.rightmove.co.uk/properties/91660647"


def test_normalise_url_adds_scheme() -> None:
    clean, _ = normalise_url("rightmove.co.uk/properties/1")
    assert clean == "https://rightmove.co.uk/properties/1"


@pytest.mark.parametrize(
    "bad", ["", "not a url", "ftp://rightmove.co.uk/x", "https://example.com/1"]
)
def test_normalise_url_rejects(bad: str) -> None:
    with pytest.raises(ListingUrlError):
        normalise_url(bad)


def test_unwrap_real_engine_response() -> None:
    fields = unwrap_result(FIXTURE)
    assert fields["Asking Price"] == 165000
    assert unwrap_result([{"json": {"fields": {"a": 1}}}]) == {"a": 1}
    assert unwrap_result({"a": 1}) == {"a": 1}
    assert unwrap_result("junk") == {}


def test_summarise_real_engine_response() -> None:
    s = summarise(unwrap_result(FIXTURE))
    assert s["address"] == "Christ Church Street, Preston, Lancashire, PR1"
    assert s["postcode"] is None  # the engine gave the outward code only
    assert s["asking_price"] == 165000
    assert s["property_type"] == "T"
    assert s["bedrooms"] == 3


def test_find_postcode() -> None:
    assert find_postcode("12 High St, Barnet EN5 5XY") == "EN55XY"
    assert find_postcode(None, "N11 2AB") == "N112AB"
    assert find_postcode("Preston PR1") is None


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("Terraced", "T"),
        ("End of Terrace House", "T"),
        ("Semi-Detached", "S"),
        ("Detached bungalow", "D"),
        ("2 bed flat", "F"),
        ("Apartment", "F"),
        ("Land", None),
        (None, None),
    ],
)
def test_property_type_code(text: str | None, code: str | None) -> None:
    assert property_type_code(text) == code


def test_to_int() -> None:
    assert to_int("£165,000") == 165000
    assert to_int(165000.4) == 165000
    assert to_int("Offers over £120,000") == 120000
    assert to_int("") is None
    assert to_int(True) is None


def test_parse_address() -> None:
    assert parse_address("12 Christ Church Street, Preston, Lancashire, PR1") == (
        "CHRIST CHURCH STREET",
        "PRESTON",
        "PR1",
    )
    assert parse_address("Flat 3, 10 High Road, London, N11 2AB") == (
        "FLAT 3",
        "10 HIGH ROAD",
        None,
    )
    assert parse_address("Christ Church Street, Preston") == (
        "CHRIST CHURCH STREET",
        "PRESTON",
        None,
    )
    assert parse_address(None) == (None, None, None)


def _settings() -> Settings:
    return Settings(listing_webhook_url="https://engine.test/hook", listing_timeout_s=5)


def test_call_engine_ok() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content) == {"url": "https://www.rightmove.co.uk/properties/1"}
        return httpx.Response(200, json=FIXTURE)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    payload, ms = call_engine(
        "https://www.rightmove.co.uk/properties/1", settings=_settings(), client=client
    )
    assert payload["fields"]["Asking Price"] == 165000
    assert ms >= 0


def test_call_engine_http_error() -> None:
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(500)))
    with pytest.raises(EngineError, match="HTTP 500"):
        call_engine("https://www.rightmove.co.uk/properties/1", settings=_settings(), client=client)


def test_call_engine_not_json() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text="<html>"))
    )
    with pytest.raises(EngineError):
        call_engine("https://www.rightmove.co.uk/properties/1", settings=_settings(), client=client)
