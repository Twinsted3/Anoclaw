# Per-Tool Empirical Usage Rules (derived from dev n=480 flip analysis)

_Generated 2026-04-18. Each rule cites specific win items. Use these
to inject into agent_v7.5 prompt as actionable triggers._

## Summary of exploitable tool×domain combos (net_flips ≥ +2)

| Tool | Domain | Net | Win:Loss | Scene type | Failure mode tool corrects |
|---|---|---|---|---|---|
| patch_grid | D5c (liver CT) | +5 | 7:2 | 2D abdominal CT slices showing small oval/elongated tissue shapes | Direct=0.95 FP on normal anatomical variants (holes, shape differences that appear in some refs) |
| zoom_bbox | D1 (industrial) | +4 | 7:3 | capsules, transistors, PCB components, cables | Direct=0.95-0.98 FP triggered by logo orientation, lighting, minor texture |
| hotspot_cropper | D1 | +4 | 6:2 | same as above | same; tool's re-inspection of hotspot confirms no defect |
| patch_grid | D1 | +4 | 5:1 | same | tiling image into 3×3 reveals texture consistency |
| image_diff | D7 (road) | +3 | 3:0 | driving scenes with unexpected object (vintage car, horse carriage, rural landscape) | Direct=0.02 FN on scene-level content anomaly; diff vs refs shows high change |
| reference_retriever | D7 | +3 | 3:0 | same | retrieves perfect match (sim=1.0) for normal, or no match for anomalous |
| image_diff | D1 | +3 | 7:4 | industrial | FP correction (same as hotspot_cropper) |
| segment_and_count | D1 | +3 | 6:3 | industrial | coarse grid confirms structural match with refs |
| patch_grid | D10 (VisA) | +2 | 4:2 | ultrasonic sensor modules, tea candles, retail objects | FP corrections + one FN (exposed transducer) |
| reference_profiler | D10 | +2 | 3:1 | same | forces structured "allowed variation" list that rules in normals |
| segment_and_count | D7 | +2 | 3:1 | road | scene-level structural diff correctly flags unexpected scenes |
| texture_fft | D1 | +2 | 6:4 | industrial textures | confirms periodicity/irregularity consistent with refs |
| texture_fft | D5b (brain MRI) | +2 | 4:2 | brain slices | periodic/irregular texture signal rules in normal brain scan variants |
| domain_knowledge | D1 | +2 | 5:3 | industrial | LLM answer about "what's normal for this type of component" |

## Rule 1 — D1 (Industrial products / capsules / PCB)

**When agent sees**: a small manufactured product (capsule, transistor, cable,
connector, tile) on a plain background, AND Direct's initial impression
strongly suggests ANOMALY (0.9+) despite query appearing visually
consistent with refs (correct shape, correct colors, correct logos).

**Call one of**: `tool_zoom_bbox` (on the suspicious region) OR
`tool_hotspot_cropper` (if subspacead rank is moderate-high) OR
`tool_patch_grid(3x3)` to confirm structural match.

**Expected effect**: confirm no defect → finalize score=0.05-0.10 (normal).

**Typical win items**: D1_0084 (speckled texture), D1_0038 (actavis capsule),
D1_0088 (transistor), D1_0009 (three-core cable), D1_0064 (capsule logo).

## Rule 2 — D7 (Road / driving scenes)

**When agent sees**: a road/driving scene where the query's SCENE CONTENT
differs fundamentally from refs (e.g. refs are urban dashcam views, query
shows tourist square / rural highway / vintage vehicle / horse carriage).

**Call**: `tool_image_diff(ref_idx=0)` — a large change_percent confirms
scene-level anomaly. OR `tool_reference_retriever` — low top_similarity
confirms no normal scene matches.

**Expected effect**: bring score UP to 0.9-0.95 (FN correction for a
content-level anomaly Direct missed).

**Typical win items**: D7_0022 (daytime scene vs night refs), D7_0135
(horse carriage), D7_0159 (vintage car+trailer).

## Rule 3 — D5c (Liver CT — 2D slices)

**When agent sees**: a 2D CT slice with small tissue shapes (oval, elongated,
irregular), AND Direct says ANOMALY (0.95) but query's general texture
matches refs except for shape variation.

**Call**: `tool_patch_grid(3x3)` — tiling helps isolate whether the
"anomalous" region is localized or global tissue variation.

**Expected effect**: downweight Direct's FP, output 0.10-0.20.

**Typical win items**: D5c_0035, D5c_0038, D5c_0070, D5c_0131.

## Rule 4 — D10 (VisA-style sensor modules / retail / PCB)

**When agent sees**: electronic sensor modules (HC-SR04, transducers) or
retail objects (candles) and Direct says ANOMALY.

**Call**: `tool_reference_profiler()` once to get the allowed_variation
list, then match query against it. OR `tool_patch_grid(3x3)` to tile.

**Expected effect**: if query variation matches allowed_variation list
→ score 0.05-0.10 (FP correction). If query has exposed/missing
components → score 0.85-0.95 (FN correction).

**Typical win items**: D10_0076 (HC-SR04 FP), D10_0002 (candles FP),
D10_0156 (exposed transducer FN).

## Rule 5 — D5b (Brain MRI)

**When agent sees**: a brain MRI slice and Direct says ANOMALY but query
shows similar gray-matter / white-matter distribution and similar
ventricle shape as refs.

**Call**: `tool_texture_fft` — periodicity score is a weak but domain-
appropriate signal for brain tissue.

**Expected effect**: downweight Direct's FP.

## Rule 6 — General (domain-free)

For ALL domains not covered above, and ALL items where Direct margin is
moderate (|direct - 0.5| < 0.3), the tool audit shows NO net positive
effect. The agent's best policy is to **finalize on turn 1 using pure
visual comparison**, unless it has a specific hypothesis matching one of
the rules above.

Put bluntly: adding tools for generic uncertain cases HURTS — the
disconfirm mechanism over-corrects Direct on items where Direct was
actually right.

## Caveat

These rules are dev-derived. The wins/losses counts are not corrected
for multiple testing. Expected false positive niches across 13 tools ×
12 domains ≈ 39 spurious Win>Loss cells at α=0.05 uncorrected — but the
strong patterns (D1 wins dominated by 5 items across ALL tools, D7 3-0
perfect record on content-level anomalies) are unlikely to be noise.
