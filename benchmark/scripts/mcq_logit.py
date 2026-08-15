"""MCQ logit extraction utility for MMAD experiments.

Given (image, refs, question, options), prompt the VLM to answer with
EXACTLY one letter, then extract first-token logprobs and compute a
softmax over the candidate letters (A/B/C/D or A/B for binary AD).

Used by mmad_eval_v12_mmad_logit (Implementation 1: logit-add ensemble)
and mmad_eval_v12_mmad_prior (Implementation 2: Direct-as-prior agent).
"""
from __future__ import annotations

import math
from typing import Sequence

from infer import (
    img_msg, load_and_encode, text_msg,
)


_MCQ_LETTER_PROMPT = (
    "You are an industrial-inspection visual expert. I will show you "
    "NORMAL reference images followed by a QUERY image, then ask a "
    "multiple-choice question. Pick the single best option that fits "
    "what you see in the query image.\n\n"
    "Reply with EXACTLY one letter — A, B, C, or D — and nothing else. "
    "Do not write anything before or after the letter."
)


def _build_mcq_messages(image_path, ref_paths, question, options):
    parts = [text_msg("NORMAL REFERENCE IMAGES:")]
    for rp in ref_paths[:4]:
        try:
            parts.append(img_msg(load_and_encode(rp)))
        except Exception:
            continue
    parts.append(text_msg("QUERY IMAGE:"))
    parts.append(img_msg(load_and_encode(image_path)))
    opts_lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
    parts.append(text_msg(f"QUESTION: {question}\nOPTIONS:\n{opts_lines}"))
    return [{"role": "system", "content": _MCQ_LETTER_PROMPT},
            {"role": "user", "content": parts}]


def _extract_letter_logits(top_logprobs, letters: Sequence[str]):
    """Pick the highest logprob seen for each candidate letter.

    Tokenisers may emit " A" / "A" / "A." etc. We normalise by stripping
    whitespace and trailing punctuation, then matching case-insensitively.
    """
    out = {L: None for L in letters}
    for entry in top_logprobs:
        tok = entry.token.strip().strip(".)").upper()
        if tok in out:
            cur = out[tok]
            if cur is None or entry.logprob > cur:
                out[tok] = entry.logprob
    return out


def mcq_logit_call(client, model, image_path, ref_paths, question, options,
                   max_tokens=2):
    """Run a single MCQ logit call. Returns dict with logits/scores/answer.

    options: dict like {"A": "...", "B": "...", "C": "...", "D": "..."}
    or {"A": "Yes...", "B": "No..."} for binary AD.
    """
    letters = sorted(options.keys())  # ['A','B'] or ['A','B','C','D']
    msgs = _build_mcq_messages(image_path, ref_paths, question, options)
    kwargs = dict(
        model=model, messages=msgs,
        max_tokens=max_tokens, temperature=0.0,
        logprobs=True, top_logprobs=20,
    )
    if "qwen3" in str(model).lower() or "Qwen3" in str(model):
        kwargs["extra_body"] = {
            "chat_template_kwargs": {"enable_thinking": False}}
    try:
        resp = client.chat.completions.create(**kwargs)
    except Exception as e:
        return {"answer": None, "error": f"call: {type(e).__name__}: {e}",
                "logits": None, "scores": None, "raw_text": ""}

    text = resp.choices[0].message.content or ""
    lp = resp.choices[0].logprobs
    if lp is None or not lp.content:
        # No logprob support — fall back to text parse
        first_letter = next((c for c in text.upper() if c in letters), None)
        return {"answer": first_letter, "logits": None, "scores": None,
                "raw_text": text, "error": "no_logprobs"}

    first = lp.content[0]
    logits = _extract_letter_logits(first.top_logprobs, letters)

    if all(v is None for v in logits.values()):
        # No candidate letters in top-20 — text fallback
        first_letter = next((c for c in text.upper() if c in letters), None)
        return {"answer": first_letter, "logits": None, "scores": None,
                "raw_text": text, "error": "letters_not_in_topk",
                "first_top": [(e.token, e.logprob)
                              for e in first.top_logprobs[:8]]}

    # Fill missing logits with a low fallback
    fallback = -30.0
    full = {L: (logits[L] if logits[L] is not None else fallback)
            for L in letters}
    m = max(full.values())
    exps = {L: math.exp(full[L] - m) for L in letters}
    z = sum(exps.values())
    scores = {L: exps[L] / z for L in letters}
    answer = max(scores.items(), key=lambda kv: kv[1])[0]
    return {"answer": answer, "logits": full, "scores": scores,
            "raw_text": text, "error": None,
            "first_top": [(e.token, e.logprob)
                          for e in first.top_logprobs[:8]]}


def ensemble_logits(d_logits, a_logits, letters):
    """Blend two letter→logit dicts via softmax-sum, return new (answer, scores).

    Either dict may be None — in that case fall back to the other.
    """
    if d_logits is None and a_logits is None:
        return None, None
    fallback = -30.0
    def _norm(d):
        if d is None:
            return None
        return {L: float(d.get(L) if d.get(L) is not None else fallback)
                for L in letters}
    d = _norm(d_logits); a = _norm(a_logits)
    if d is None: return _argmax_softmax(a, letters)
    if a is None: return _argmax_softmax(d, letters)
    # softmax(d) + softmax(a)
    md = max(d.values()); ma = max(a.values())
    sd = {L: math.exp(d[L] - md) for L in letters}
    sa = {L: math.exp(a[L] - ma) for L in letters}
    zd = sum(sd.values()); za = sum(sa.values())
    blended = {L: 0.5 * sd[L] / zd + 0.5 * sa[L] / za for L in letters}
    ans = max(blended.items(), key=lambda kv: kv[1])[0]
    return ans, blended


def _argmax_softmax(d, letters):
    if d is None:
        return None, None
    m = max(d.values())
    exps = {L: math.exp(d[L] - m) for L in letters}
    z = sum(exps.values())
    scores = {L: exps[L] / z for L in letters}
    return max(scores.items(), key=lambda kv: kv[1])[0], scores
