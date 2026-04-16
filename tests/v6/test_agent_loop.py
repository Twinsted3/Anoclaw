"""Smoke tests for agent_v6.ReActAgent using a stub VLM client."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmark" / "scripts"))
import agent_v6 as mod  # noqa: E402
from agent_v6 import ReActAgent, AgentResult  # noqa: E402


def _stub_call_llm(responses):
    calls = {"i": 0}
    def call_llm_stub(client, model, messages, max_tokens=700, temperature=0.0):
        r = responses[calls["i"]]
        calls["i"] += 1
        return r, 10, 10
    return call_llm_stub


def _fake_image(tmp_path, name="q.png"):
    arr = (np.random.rand(100, 100, 3) * 255).astype(np.uint8)
    p = str(tmp_path / name)
    Image.fromarray(arr).save(p)
    return p


def test_agent_final_at_turn_1(monkeypatch, tmp_path):
    qp = _fake_image(tmp_path, "q.png")
    rp = _fake_image(tmp_path, "r.png")
    responses = [
        '{"thought":"clear anomaly","action":"final","tool":null,"args":null,'
        '"confidence":92,"score":0.95,"rationale":"obvious damage"}'
    ]
    monkeypatch.setattr(mod, "call_llm", _stub_call_llm(responses))
    agent = ReActAgent(vlm_client=None, vlm_model="stub", max_turns=5)
    res = agent.run(item_id="D1_test", query_path=qp, ref_paths=[rp]*4,
                    split="calibration")
    assert isinstance(res, AgentResult)
    assert res.score == 0.95
    assert res.n_turns == 1
    assert res.tools_used == []


def test_agent_forced_final_at_K(monkeypatch, tmp_path):
    qp = _fake_image(tmp_path, "q.png")
    rp = _fake_image(tmp_path, "r.png")
    # 5 turns of texture_fft calls, then a forced-final
    responses = [
        '{"thought":"t","action":"call_tool","tool":"tool_texture_fft",'
        '"args":{},"confidence":40,"score":null,"rationale":null}'
    ] * 5 + [
        '{"thought":"budget done","action":"final","tool":null,"args":null,'
        '"confidence":55,"score":0.4,"rationale":"uncertain"}'
    ]
    monkeypatch.setattr(mod, "call_llm", _stub_call_llm(responses))
    agent = ReActAgent(vlm_client=None, vlm_model="stub", max_turns=5)
    res = agent.run(item_id="X", query_path=qp, ref_paths=[rp]*4,
                    split="calibration")
    assert res.score == 0.4
    assert res.n_turns == 5


def test_agent_malformed_json_retry(monkeypatch, tmp_path):
    qp = _fake_image(tmp_path, "q.png")
    rp = _fake_image(tmp_path, "r.png")
    responses = [
        "not json at all",
        '{"thought":"ok","action":"final","tool":null,"args":null,'
        '"confidence":70,"score":0.2,"rationale":"normal"}',
    ]
    monkeypatch.setattr(mod, "call_llm", _stub_call_llm(responses))
    agent = ReActAgent(vlm_client=None, vlm_model="stub", max_turns=5,
                       json_retries=1)
    res = agent.run(item_id="X", query_path=qp, ref_paths=[rp]*4,
                    split="calibration")
    assert res.score == 0.2
