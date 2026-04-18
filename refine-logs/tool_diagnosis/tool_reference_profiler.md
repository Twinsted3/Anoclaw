# Diagnosis: tool_reference_profiler

Total calls: 459

## Failure mode (manual analysis — fill in)

_TBD: wrong trigger / unclear output / VLM misreads / mixed_

## Wins (agent better than Direct)

- `D7_0148` [D7] label=1 agent=0.95 direct=0.02 Δerr=-0.930
  > The query image depicts a parked vehicle with a trailer in a parking lot, which is a static scene. In contrast, all four reference images are dynamic, street-level driving scenes captured from a dashboard camera on active roadways. This fun

- `D8_0096` [D8] label=1 agent=0.95 direct=0.02 Δerr=-0.930
  > The query image shows a person running (indicated by motion blur) in a pedestrian walkway where normal behavior is walking. This is a clear violation of the 'normal' behavior defined for this domain, making it a strong anomaly.

- `D2_0132` [D2] label=1 agent=0.92 direct=0.01 Δerr=-0.910
  > The query image shows a purple Mirinda can with a visible contamination defect: a cluster of foreign fiber-like material stuck to the can's surface, which is a clear physical anomaly compared to the clean reference images.

- `D7_0101` [D7] label=1 agent=0.95 direct=0.05 Δerr=-0.900
  > The query image depicts a horse-drawn carriage, which is a significant anomaly compared to the reference images that exclusively show modern cars and urban road infrastructure. This object is unexpected in the context of the defined normal 

- `D8_0049` [D8] label=0 agent=0.05 direct=0.95 Δerr=-0.900
  > The patchknn expert score of 0.048 with low normalized rank (0.038) indicates weak anomaly signal. The query shows a uniformed person walking normally through the pedestrian walkway, consistent with normal behavior defined in the domain.

- `D8_0153` [D8] label=1 agent=0.95 direct=0.05 Δerr=-0.900
  > The query image shows a person standing still on the grass, which violates the domain definition of normal behavior (walking at a normal pace on the walkway). This constitutes loitering and off-path behavior, making it a clear anomaly.

- `D8_0145` [D8] label=1 agent=0.95 direct=0.05 Δerr=-0.900
  > The query image shows a person standing still and facing the camera, which is a clear deviation from the normal behavior of pedestrians walking through the walkway. This static posture indicates loitering or an unusual behavior, classifying

- `D9_0017` [D9] label=0 agent=0.10 direct=0.99 Δerr=-0.890
  > The subspacead expert score shows a very low normalized rank (0.058) with 'weak signal' interpretation, indicating the query image matches the normal reference patterns. The yellow cable with single-row orange connectors appears to be a val

- `D9_0025` [D9] label=0 agent=0.10 direct=0.99 Δerr=-0.890
  > The subspacead expert score shows a very low normalized rank (0.043) indicating weak anomaly signal. The query image shows a yellow cable with orange connectors on a mesh background, which matches the variations described in the reference p

- `D7_0168` [D7] label=1 agent=0.90 direct=0.02 Δerr=-0.880
  > The query image contains a red telephone booth on the roadside, which is an unexpected object not found in the normal reference images and could pose a driving hazard, making it anomalous according to the domain definition.

## Losses (agent worse than Direct)

- `D5d_0119` [D5d] label=1 agent=0.10 direct=0.98 Δerr=+0.880
  > The query image displays smooth, pink mucosal folds with normal specular reflections, consistent with the first normal reference image. It lacks any visible pathological features such as polyps, ulcers, or bleeding seen in the other referen

- `D6_0074` [D6] label=0 agent=0.91 direct=0.02 Δerr=+0.890
  > The subspacead expert tool identified a strong anomaly signal (normalized rank 0.91), and the image diff showed 42% change between reference and query. The hotspot reveals a structured pattern that likely represents new construction or orga

- `D9_0106` [D9] label=1 agent=0.10 direct=0.99 Δerr=+0.890
  > The query image shows a yellow cable with single orange connectors, which matches the normal variations seen in references. The subspacead expert returned a very low anomaly score (normalized rank 0.067), and visual inspection confirms no s

- `D5c_0086` [D5c] label=0 agent=0.91 direct=0.02 Δerr=+0.890
  > The subspacead expert model identified a strong anomaly signal (normalized rank 0.91 > 0.80). The query image shows a significantly smaller and simpler white shape compared to the larger, more complex liver-like structures in the reference 

- `D5c_0049` [D5c] label=0 agent=0.93 direct=0.02 Δerr=+0.910
  > The expert score (rank 0.93) indicates a strong anomaly. The query image displays a significantly smaller and less complex biological structure compared to the reference liver slices, suggesting a major deviation from normal anatomy.

- `D5c_0059` [D5c] label=0 agent=0.93 direct=0.02 Δerr=+0.910
  > The expert model (subspacead) flagged the query as a strong anomaly with a normalized rank of 0.93. The query image shows a very small, thin liver slice that lacks the typical size and internal texture seen in the normal reference images, c

- `D9_0153` [D9] label=1 agent=0.05 direct=0.98 Δerr=+0.930
  > The subspacead expert detected a weak anomaly signal (normalized rank 0.04), and visual inspection of the hotspots confirms the pushpins and compartments appear normal, consistent with the reference images. No logical or structural anomalie

- `D5d_0079` [D5d] label=0 agent=0.95 direct=0.02 Δerr=+0.930
  > The query image displays a distinct, raised polypoid lesion, which is a clear pathological anomaly compared to the smooth, normal mucosa described in the reference images. The expert model's low score is incorrect in this context.

- `D5c_0074` [D5c] label=0 agent=0.98 direct=0.02 Δerr=+0.960
  > The query image displays a small, thin, elongated structure, which is structurally inconsistent with the large, substantial liver cross-sections seen in all four reference images. The expert model confirms this with a strong anomaly signal 

- `D5b_0038` [D5b] label=0 agent=1.00 direct=0.02 Δerr=+0.980
  > The query image is a sagittal MRI slice of a brain, whereas all four normal reference images are axial slices. This difference in anatomical orientation constitutes a clear structural anomaly relative to the reference set.
