"""Dashboard endpoints, offline. A stand-in model is used so the tests need no trained artifact."""
import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import joblib
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "dashboard"))
import server  # noqa: E402
from aegis import features  # noqa: E402
from aegis.model import RiskModel  # noqa: E402


@pytest.fixture(scope="module")
def url(tmp_path_factory):
    models = tmp_path_factory.mktemp("models")
    model = RiskModel("logistic", [1], coef=np.zeros(1), mean=np.zeros(1), scale=np.ones(1), intercept=-6.0,
                      meta={"name": "stand-in", "tier1": "fast", "tier2": "relay", "threshold": 0.01,
                            "feature_names": features.NAMES})
    joblib.dump(model, models / "aegis_router.joblib")
    server.MODELS, server.REPORTS = models, models          # no stored evaluation in this directory
    server._cache.clear()
    httpd = server.serve(port=0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def get(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.status, response.read()


def post(url, body):
    request = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def test_page_labels_every_kind_of_data(url):
    status, body = get(url + "/")
    page = body.decode()
    assert status == 200 and "QEC-Aegis" in page
    for label in ("live computation", "stored measured experiment", "reference result", "illustrative"):
        assert label in page


def test_page_and_server_are_offline():
    """No external address in the page, no outgoing-connection code in the server, local bind only."""
    page = (ROOT / "dashboard" / "index.html").read_text()
    assert "http://" not in page and "https://" not in page
    source = (ROOT / "dashboard" / "server.py").read_text()
    for forbidden in ("urllib.request", "requests", "qiskit", "socket.create_connection"):
        assert forbidden not in source
    assert '("127.0.0.1", port)' in source


def test_status_and_reference(url):
    status = json.loads(get(url + "/api/status")[1])
    assert status["source"] == "live" and status["offline"] and status["allowed_p"] == [0.003, 0.004, 0.005]
    assert status["model"]["threshold"] == 0.01
    reference = json.loads(get(url + "/api/reference")[1])
    assert reference["source"] == "reference" and len(reference["rows"]) == 6


def test_results_say_when_nothing_is_stored(url):
    results = json.loads(get(url + "/api/results")[1])
    assert results == {"source": "stored", "available": False}


def test_live_decode(url):
    status, shot = post(url + "/api/decode", {"basis": "X", "p": 0.003, "f": 0.0, "seed": 4, "baselines": ["relay"]})
    assert status == 200 and shot["source"] == "live"
    assert np.array(shot["syndrome"]).shape == (13, 72) and len(shot["true_observables"]) == 12
    assert set(shot["decoders"]) == {"QEC-Aegis", "relay-BP"}
    for outcome in shot["decoders"].values():
        assert isinstance(outcome["logical_correct"], bool) and outcome["ms"] > 0
    routing = shot["routing"]
    assert routing["threshold"] == 0.01 and 0 <= routing["risk"] <= 1
    assert routing["escalated"] == (routing["risk"] >= routing["threshold"])
    assert set(shot["features"]) == set(features.NAMES)
    assert shot["features"]["syndrome_weight"] == np.array(shot["syndrome"]).sum()
    # The same seed gives the same shot.
    again = post(url + "/api/decode", {"basis": "X", "p": 0.003, "f": 0.0, "seed": 4, "baselines": []})[1]
    assert again["syndrome"] == shot["syndrome"] and set(again["decoders"]) == {"QEC-Aegis"}


def test_live_decode_with_erasure(url):
    status, shot = post(url + "/api/decode", {"basis": "Z", "p": 0.004, "f": 0.5, "seed": 2, "baselines": []})
    assert status == 200 and shot["heralds"] > 0 and sum(shot["herald_rounds"]) == shot["heralds"]
    assert shot["features"]["heralds"] == shot["heralds"]


def test_bad_requests_are_refused(url):
    assert post(url + "/api/decode", {"basis": "X", "p": 0.5})[0] == 400
    assert post(url + "/api/decode", {"basis": "Q", "p": 0.004})[0] == 400
    assert post(url + "/api/other", {})[0] == 404
    with pytest.raises(urllib.error.HTTPError):
        get(url + "/figures/../../requirements.lock")
