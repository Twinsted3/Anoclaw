# Diagnosis: tool_image_diff

Total calls: 285

## Failure mode (manual analysis — fill in)

_TBD: wrong trigger / unclear output / VLM misreads / mixed_

## Wins (agent better than Direct)

- `D5c_0144` [D5c] label=1 agent=0.97 direct=0.02 Δerr=-0.950
  > The subspacead expert score indicates a strong anomaly signal (normalized_rank=0.9676), confirming the presence of a significant deviation from normal liver parenchyma, consistent with a focal lesion.

- `D2_0176` [D2] label=1 agent=0.92 direct=0.02 Δerr=-0.900
  > The query image shows a cigarette pack where the central circular logo is missing the detailed rose graphic present in all reference images, appearing as a plain yellow circle instead. The image_diff confirms a significant structural differ

- `D5c_0126` [D5c] label=1 agent=0.92 direct=0.02 Δerr=-0.900
  > The query image exhibits a focal lesion, as evidenced by the high anomaly score from subspacead, the dark irregular region in the hotspot crop, and the significant difference highlighted by the image_diff tool. These findings are consistent

- `D1_0057` [D1] label=0 agent=0.05 direct=0.95 Δerr=-0.900
  > The subspacead expert returned a very low normalized rank (0.0023) indicating normal. The image diff shows expected texture variation (49% change) typical for speckled surfaces, not defects. The query matches the reference pattern.

- `D9_0001` [D9] label=0 agent=0.10 direct=0.98 Δerr=-0.880
  > The subspacead expert score is very low (0.07), indicating no anomaly. The pixel difference from the reference is due to random pin placement, not a logical defect like missing or extra pins. The query appears normal.

- `D1_0041` [D1] label=0 agent=0.15 direct=0.98 Δerr=-0.830
  > The query image shows a normal capsule with no visible defects. The subspacead expert gave a low anomaly score (0.24), and the pixel diff with reference 0 shows minimal differences (1.63% change), consistent with normal variation in lightin

- `D6_0004` [D6] label=0 agent=0.15 direct=0.98 Δerr=-0.830
  > The differences between query and reference are primarily agricultural field patterns (plowing/cultivation changes) rather than building-level changes. The structures at the bottom appear consistent between images. This represents normal se

- `D6_0070` [D6] label=0 agent=0.15 direct=0.98 Δerr=-0.830
  > Despite high pixel-level differences (49%), the subspacead expert detected only weak structural anomaly signals (rank=0.22), indicating the changes are primarily radiometric/seasonal variations rather than actual building-level changes like

- `D8_0110` [D8] label=1 agent=0.85 direct=0.02 Δerr=-0.830
  > The query image shows a person in a dark uniform moving quickly or running, which deviates from the normal pedestrian behavior of walking at a normal pace. The significant difference detected by image_diff supports this observation, indicat

- `D9_0049` [D9] label=0 agent=0.15 direct=0.98 Δerr=-0.830
  > The query image shows a yellow cable with single-position orange connectors, which matches the configuration of reference image 1. The subspacead expert score indicates a weak anomaly signal (rank 0.31), and the reference profiler confirms 

## Losses (agent worse than Direct)

- `D9_0109` [D9] label=1 agent=0.15 direct=0.98 Δerr=+0.830
  > The subspacead expert detected only a weak anomaly signal (normalized rank 0.086), and visual inspection shows the query image contains yellow pushpins in a compartmentalized box similar to the references, with no obvious missing or extra c

- `D5b_0049` [D5b] label=0 agent=0.85 direct=0.02 Δerr=+0.830
  > The query image contains two distinct hyperintense lesions not present in normal references. The image_diff confirms significant structural differences (31.88% change), providing strong evidence of pathology despite the moderate subspacead 

- `D5b_0063` [D5b] label=0 agent=0.85 direct=0.02 Δerr=+0.830
  > The query image exhibits significant structural and intensity differences compared to the normal reference (22% change), along with visible asymmetry and a dark irregular region. These features are consistent with brain pathology such as a 

- `D5c_0020` [D5c] label=0 agent=0.85 direct=0.02 Δerr=+0.830
  > The expert score (81.34) and normalized rank (0.858) indicate a strong anomaly signal, confirming the presence of a lesion or abnormality in the liver slice. The image diff also showed a significant structural difference (13.58% change) bet

- `D6_0053` [D6] label=0 agent=0.86 direct=0.02 Δerr=+0.840
  > The subspacead expert returned a strong anomaly signal with normalized rank 0.86 (above 0.80 threshold), and image_diff showed 37.56% pixel change between query and reference. These indicators strongly suggest building-level changes (constr

- `D6_0013` [D6] label=0 agent=0.90 direct=0.05 Δerr=+0.850
  > The subspacead expert score (89.96) and high normalized rank (0.88) indicate a strong anomaly. The visual change from green vegetation to bare soil is significant and flagged as anomalous by the model, suggesting it deviates from the expect

- `D6_0023` [D6] label=0 agent=0.88 direct=0.02 Δerr=+0.860
  > The subspacead expert detected a strong anomaly signal with normalized rank 0.875 (above 0.80 threshold), indicating significant structural differences between reference and query images consistent with building changes in this change detec

- `D6_0074` [D6] label=0 agent=0.91 direct=0.02 Δerr=+0.890
  > The subspacead expert tool identified a strong anomaly signal (normalized rank 0.91), and the image diff showed 42% change between reference and query. The hotspot reveals a structured pattern that likely represents new construction or orga

- `D2_0013` [D2] label=0 agent=0.92 direct=0.01 Δerr=+0.910
  > The query bottle is missing the main 'Scream' logo and white graphics present on all reference bottles. Rotation alignment confirmed this is not a viewing angle issue but a genuine label defect (missing branding), which constitutes an anoma

- `D9_0153` [D9] label=1 agent=0.05 direct=0.98 Δerr=+0.930
  > The subspacead expert detected a weak anomaly signal (normalized rank 0.04), and visual inspection of the hotspots confirms the pushpins and compartments appear normal, consistent with the reference images. No logical or structural anomalie
