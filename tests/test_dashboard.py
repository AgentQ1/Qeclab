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
    joblib.dump(model, models / "aegis_router_loss.joblib")
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
    assert results == {"source": "stored", "available": False, "studies": [], "predecoder": None}


def test_without_a_model_only_the_baselines_run(url, tmp_path, monkeypatch):
    monkeypatch.setattr(server, "MODELS", tmp_path)       # no model file here
    status = json.loads(get(url + "/api/status")[1])
    assert status["model"] is None and status["loss_model"] is None
    code, shot = post(url + "/api/decode", {"basis": "Z", "p": 0.003, "seed": 1, "baselines": ["relay"]})
    assert code == 200 and set(shot["decoders"]) == {"relay-BP"}
    assert shot["routing"] is None and shot["features"] is None and shot["aegis_available"] is False


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


# ---------------------------------------------------------------- research-lab payloads (dashboard/lab_api.py)
def test_gross_structure_is_computed_from_the_kit(url):
    import make_circuit as mc
    s = json.loads(get(url + "/api/gross/structure")[1])
    assert s["source"] == "live" and (s["n"], s["k"], s["ell"], s["m"], s["rounds"]) == (144, 12, 12, 6, 12)
    assert s["commute"] and s["rank_hx"] == s["rank_hz"] == 66
    assert s["row_weights"] == {"hx": [6], "hz": [6]} and s["column_weights"] == {"hx": [3], "hz": [3]}
    layout = mc.code_layout("gross")
    for i in (0, 17, 71):
        assert sorted(s["x_checks"][i]) == np.flatnonzero(layout.hx[i]).tolist()
        assert sorted(s["z_checks"][i]) == np.flatnonzero(layout.hz[i]).tolist()
    hz, hx = layout.hz.astype(int), layout.hx.astype(int)
    for support in s["logical_x"]:              # X logicals commute with every Z check
        v = np.zeros(144, int); v[support] = 1
        assert not (hz @ v % 2).any()
    for support in s["logical_z"]:
        v = np.zeros(144, int); v[support] = 1
        assert not (hx @ v % 2).any()
    assert len(s["logical_x"]) == len(s["logical_z"]) == 12
    x = s["circuits"]["X"]
    assert x["H_shape"] == [936, 8784] and x["detectors_total"] == 1728 and x["qubits"] == 288
    assert sum(map(sum, x["H_block_counts"])) == x["H_nonzeros"]


def test_records_summary_uses_the_pair_convention(tmp_path, monkeypatch):
    import lab_api
    rng = np.random.default_rng(0)
    for basis in "XZ":
        failed = np.zeros(100, bool); failed[:3 if basis == "X" else 2] = True
        np.savez(tmp_path / f"val_{basis}_p0.004.npz", **{"relay/failed": failed, "relay/seconds": rng.uniform(0.01, 0.02, 100),
                 "relay/converged": np.ones(100, bool)}, shots=100, seed=3, basis=basis, p=0.004, f=0.0)
    np.savez(tmp_path / "val_X_p0.005.npz", shots=1)          # no Z partner yet
    monkeypatch.setattr(lab_api, "RECORDS", tmp_path)
    lab_api._summary_cache.clear()
    out = lab_api.records_summary()
    assert out["source"] == "stored" and out["incomplete"] == [{"split": "val", "p": 0.005, "f": 0.0, "have": ["X"]}]
    (setting,) = out["settings"]
    relay = setting["tiers"]["relay"]
    assert relay["failures_X"] == 3 and relay["failures_Z"] == 2 and relay["failures_pair"] == 3   # shots 0-1 fail in both
    assert abs(relay["ler"] - (1 - (1 - 0.03) ** (1 / 12))) < 1e-12
    assert relay["ler_ci95"][0] < relay["ler"] < relay["ler_ci95"][1]
    assert sum(relay["latency_counts"]) == 100 and len(out["latency_edges_ms"]) == len(relay["latency_counts"]) + 1


def test_manifest_and_calibration_routes(url):
    assert json.loads(get(url + "/api/manifest")[1])["source"] == "stored"
    assert json.loads(get(url + "/api/calibration")[1])["source"] == "stored"
    assert json.loads(get(url + "/api/training")[1])["source"] == "stored"
