# Diagnosis: tool_zoom_bbox

Total calls: 41

## Failure mode (manual analysis — fill in)

_TBD: wrong trigger / unclear output / VLM misreads / mixed_

## Wins (agent better than Direct)

- `D2_0172` [D2] label=1 agent=0.85 direct=0.01 Δerr=-0.840
  > The hotspot analysis confirms a torn/damaged seal at the top of the Lay's can, which is a clear physical packaging defect. This anomaly is visible as a jagged tear in the plastic seal, distinguishing it from the intact packaging in the refe

- `D6_0004` [D6] label=0 agent=0.15 direct=0.98 Δerr=-0.830
  > The differences between query and reference are primarily agricultural field patterns (plowing/cultivation changes) rather than building-level changes. The structures at the bottom appear consistent between images. This represents normal se

- `D4_0160` [D4] label=1 agent=0.85 direct=0.05 Δerr=-0.800
  > The subspacead expert returned a strong anomaly signal (score 80.79, rank 0.86), indicating the query image contains a defect significantly different from the normal concrete surfaces in the reference images. This aligns with the domain def

- `D4_0116` [D4] label=1 agent=0.85 direct=0.05 Δerr=-0.800
  > The query image contains a distinct dark patch identified as a significant deviation by the image_diff tool. This feature is consistent with spalling or a hole in the concrete surface, which is defined as an anomaly in the domain guidelines

- `D5b_0001` [D5b] label=0 agent=0.20 direct=0.95 Δerr=-0.750
  > The query image is a midbrain slice, anatomically distinct from the cortical reference slices. The dark region is consistent with normal midbrain structures (e.g., cerebral aqueduct) rather than a pathological lesion. No clear signs of glio

- `D8_0134` [D8] label=1 agent=0.60 direct=0.02 Δerr=-0.580
  > The person in the white hoodie on the left exhibits an unusual posture (arms raised, standing still) that deviates from the normal walking behavior observed in the reference images, suggesting a potential anomaly.

- `D6_0022` [D6] label=0 agent=0.75 direct=0.98 Δerr=-0.230
  > The image_diff showed 37% pixel change between query and reference, which is substantial for a rural scene. While some change could be seasonal, the magnitude suggests potential building-level changes such as new construction or modificatio

- `D10_0018` [D10] label=0 agent=0.72 direct=0.95 Δerr=-0.230
  > Query PCB shows visible white contamination/residue on bottom left corner near U3 component, confirmed by 17.9% pixel difference from reference. This is a physical defect (contamination) not present in normal reference images.

- `D5d_0080` [D5d] label=0 agent=0.75 direct=0.95 Δerr=-0.200
  > The query image displays a focal area of white/yellowish material on the mucosa, contrasting with the clean pink tissue in the reference images. This suggests a pathological finding such as exudate or inflammation, warranting an anomaly cla

- `D4_0157` [D4] label=1 agent=0.20 direct=0.05 Δerr=-0.150
  > Both the subspacead expert score (0.36) and the image difference analysis (9% change) indicate weak anomaly signals. The dark linear feature is likely a shadow or normal surface variation, not a structural crack.

## Losses (agent worse than Direct)

- `D2_0177` [D2] label=1 agent=0.72 direct=0.95 Δerr=+0.230
  > The hotspot crop revealed smudged or damaged text on the label, which is a physical defect. The moderate subspacead score supports this, indicating the query is anomalous due to label damage.

- `D6_0082` [D6] label=1 agent=0.72 direct=0.95 Δerr=+0.230
  > The 28.5% pixel difference between query and reference images suggests significant changes in this rural scene. Given the change detection task focuses on building-level modifications, and the substantial pixel-level differences observed, t

- `D7_0044` [D7] label=0 agent=0.25 direct=0.02 Δerr=+0.230
  > The query image shows a typical night-time urban driving scene with oncoming traffic, streetlights, and a traffic signal, all consistent with the normal reference patterns. The moderate subspacead score (0.70 rank) does not indicate a stron

- `D4_0089` [D4] label=0 agent=0.35 direct=0.05 Δerr=+0.300
  > The query image shows a concrete surface with a vertical construction joint, which is a normal feature. The expert anomaly score (0.667) is below the strong anomaly threshold (0.80), and the visual characteristics of the vertical line are c

- `D7_0004` [D7] label=0 agent=0.35 direct=0.02 Δerr=+0.330
  > The expert anomaly score was moderate (0.53), and visual inspection of the flagged hotspot revealed normal scene elements (part of a vehicle and building wall) rather than an unexpected obstacle. The anomaly signal is likely due to scene co

- `D8_0143` [D8] label=1 agent=0.50 direct=0.95 Δerr=+0.450
  > json parse failed

- `D5d_0153` [D5d] label=1 agent=0.30 direct=0.98 Δerr=+0.680
  > The yellow patch appears to be bile staining, a common normal finding in gastrointestinal endoscopy, rather than a pathological lesion. The moderate subspacead score (0.41) supports this ambiguous but likely normal classification.

- `D6_0062` [D6] label=0 agent=0.75 direct=0.05 Δerr=+0.700
  > The image_diff showed 59.4% change with high pixel differences, indicating significant changes between reference and query. In a building change detection task, such high change percentages typically indicate structural modifications like n

- `D7_0070` [D7] label=0 agent=0.87 direct=0.05 Δerr=+0.820
  > The subspacead expert detected a strong anomaly signal (normalized rank 0.87). The hotspot analysis revealed stairs with a railing, which is an unexpected structure in a highway scene and represents a potential driving hazard. This is clear

- `D5b_0088` [D5b] label=0 agent=0.85 direct=0.02 Δerr=+0.830
  > Despite the low subspacead score and tool failures, the query image clearly displays a hyperintense lesion in the periventricular white matter, which is a significant deviation from the normal, symmetric appearance of the reference brain MR
