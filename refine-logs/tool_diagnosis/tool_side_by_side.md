# Diagnosis: tool_side_by_side

Total calls: 422

## Failure mode (manual analysis — fill in)

_TBD: wrong trigger / unclear output / VLM misreads / mixed_

## Wins (agent better than Direct)

- `D5c_0167` [D5c] label=1 agent=0.95 direct=0.02 Δerr=-0.930
  > The query image displays a small, detached component attached to the main liver structure, which is absent in all normal reference images. The subspacead expert score confirms a strong anomaly signal (normalized rank 0.92). This structural 

- `D8_0146` [D8] label=1 agent=0.95 direct=0.05 Δerr=-0.900
  > The query image contains a person standing still (loitering) in the middle of the walkway, which violates the normal behavior of pedestrians walking at a normal pace as seen in the reference images. This matches the anomaly definition of 'l

- `D8_0145` [D8] label=1 agent=0.95 direct=0.05 Δerr=-0.900
  > The query image shows a person standing still and facing the camera, which is a clear deviation from the normal behavior of pedestrians walking through the walkway. This static posture indicates loitering or an unusual behavior, classifying

- `D9_0017` [D9] label=0 agent=0.10 direct=0.99 Δerr=-0.890
  > The subspacead expert score shows a very low normalized rank (0.058) with 'weak signal' interpretation, indicating the query image matches the normal reference patterns. The yellow cable with single-row orange connectors appears to be a val

- `D9_0025` [D9] label=0 agent=0.10 direct=0.99 Δerr=-0.890
  > The subspacead expert score shows a very low normalized rank (0.043) indicating weak anomaly signal. The query image shows a yellow cable with orange connectors on a mesh background, which matches the variations described in the reference p

- `D9_0023` [D9] label=0 agent=0.10 direct=0.98 Δerr=-0.880
  > The subspacead expert tool indicates a very weak anomaly signal (normalized rank 0.08), suggesting the query image is structurally and logically consistent with the normal reference images. No significant deviations in component count, type

- `D9_0011` [D9] label=0 agent=0.10 direct=0.98 Δerr=-0.880
  > Expert analysis shows weak anomaly signal (rank 0.074), and visual inspection confirms the query contains the expected components (2 oranges, 1 nectarine, granola, dried banana slices, almonds) in proper arrangement matching the references.

- `D2_0011` [D2] label=0 agent=0.10 direct=0.95 Δerr=-0.850
  > The query image shows a Mengniu Red Date Milk carton with celebrity endorsement design, which the reference profiler explicitly identifies as a normal variation. No physical defects (tears, dents, missing text/logo) are visible. The product

- `D8_0000` [D8] label=0 agent=0.10 direct=0.95 Δerr=-0.850
  > The query image depicts a normal pedestrian walkway scene with people walking at a normal pace in expected directions, consistent with the reference images. No obvious anomalies such as abnormal behavior, wrong-direction motion, or out-of-p

- `D8_0140` [D8] label=1 agent=0.95 direct=0.10 Δerr=-0.850
  > The query image shows a person standing still (loitering) in the middle of a pedestrian walkway, which is defined as anomalous behavior. The reference images show people walking normally, confirming the deviation.

## Losses (agent worse than Direct)

- `D5b_0088` [D5b] label=0 agent=0.85 direct=0.02 Δerr=+0.830
  > Despite the low subspacead score and tool failures, the query image clearly displays a hyperintense lesion in the periventricular white matter, which is a significant deviation from the normal, symmetric appearance of the reference brain MR

- `D9_0131` [D9] label=1 agent=0.15 direct=0.99 Δerr=+0.840
  > The query image shows a yellow cable with single orange connectors, which matches the normal pattern seen in references 0, 1, and 3. The subspacead expert score (normalized rank 0.258) indicates a weak anomaly signal, confirming the query i

- `D9_0148` [D9] label=1 agent=0.15 direct=0.99 Δerr=+0.840
  > The expert score indicates a weak anomaly signal (rank 0.297 << 0.80), and the cable sag matches the 'cable curvature' variation noted in the reference profiler. The query appears to be a normal configuration.

- `D6_0013` [D6] label=0 agent=0.90 direct=0.05 Δerr=+0.850
  > The subspacead expert score (89.96) and high normalized rank (0.88) indicate a strong anomaly. The visual change from green vegetation to bare soil is significant and flagged as anomalous by the model, suggesting it deviates from the expect

- `D6_0023` [D6] label=0 agent=0.88 direct=0.02 Δerr=+0.860
  > The subspacead expert detected a strong anomaly signal with normalized rank 0.875 (above 0.80 threshold), indicating significant structural differences between reference and query images consistent with building changes in this change detec

- `D5d_0119` [D5d] label=1 agent=0.10 direct=0.98 Δerr=+0.880
  > The query image displays smooth, pink mucosal folds with normal specular reflections, consistent with the first normal reference image. It lacks any visible pathological features such as polyps, ulcers, or bleeding seen in the other referen

- `D5c_0052` [D5c] label=0 agent=0.92 direct=0.02 Δerr=+0.900
  > The subspacead expert returned a high anomaly score (normalized rank 0.85) with a 'strong anomaly signal' interpretation. Visually, the query image contains distinct dark hypodense regions (lesions/cysts) within the liver parenchyma, which 

- `D5d_0015` [D5d] label=0 agent=0.95 direct=0.02 Δerr=+0.930
  > The query image contains a large, dark, non-mucosal object or lesion that is completely absent in all normal reference images, which show healthy pink tissue. This represents a clear and significant pathological or foreign body anomaly.

- `D5d_0049` [D5d] label=0 agent=0.95 direct=0.02 Δerr=+0.930
  > Despite the low expert score, visual inspection clearly shows a raised, nodular polypoid lesion in the center of the query image, which is a pathological finding. The reference images show normal, flat mucosa. This structural abnormality co

- `D2_0042` [D2] label=0 agent=0.95 direct=0.01 Δerr=+0.940
  > The query image shows a large white plastic object (straw/clip) attached to the front of the milk carton, which is a foreign object contamination not present in any reference images. This is a clear packaging defect.
