# Diagnosis: tool_patch_grid

Total calls: 20

## Failure mode (manual analysis — fill in)

_TBD: wrong trigger / unclear output / VLM misreads / mixed_

## Wins (agent better than Direct)

- `D8_0110` [D8] label=1 agent=0.85 direct=0.02 Δerr=-0.830
  > The query image shows a person in a dark uniform moving quickly or running, which deviates from the normal pedestrian behavior of walking at a normal pace. The significant difference detected by image_diff supports this observation, indicat

- `D9_0143` [D9] label=1 agent=0.50 direct=0.01 Δerr=-0.490
  > json parse failed

- `D5_0159` [D5] label=1 agent=0.50 direct=0.05 Δerr=-0.450
  > json parse failed

- `D8_0149` [D8] label=1 agent=0.15 direct=0.02 Δerr=-0.130
  > The query image shows pedestrians walking and standing in a covered walkway, consistent with the normal reference images. No anomalous behaviors like running, wrong-direction motion, or out-of-place objects are detected.

- `D9_0159` [D9] label=1 agent=0.15 direct=0.02 Δerr=-0.130
  > The query image contains 2 bolts, 2 nuts, and 2 washers, which is a plausible and consistent composition for this type of hardware bag. The subspacead anomaly score is low (0.33), and no obvious missing or extra components are visible compa

- `D9_0096` [D9] label=1 agent=0.15 direct=0.02 Δerr=-0.130
  > The query image contains 2 bolts, 2 nuts, and 2 washers, which matches the component count in all four reference images. The subspacead expert also returned a low anomaly score (0.21), indicating no significant deviation from the normal pat

- `D8_0075` [D8] label=0 agent=0.10 direct=0.02 Δerr=+0.080
  > The query image shows pedestrians walking normally along the walkway. No anomalous behaviors such as running, loitering, or wrong-direction motion are detected. The observed differences from the reference images are consistent with normal p

- `D8_0015` [D8] label=0 agent=0.15 direct=0.05 Δerr=+0.100
  > The query image shows normal pedestrian activity on a walkway. People are walking at normal pace in expected directions. No obvious anomalies like running, wrong-direction motion, dropped objects, or unusual postures are visible. The 16% pi

- `D8_0042` [D8] label=0 agent=0.15 direct=0.02 Δerr=+0.130
  > The query image shows normal pedestrian activity in a walkway/station area. No anomalies detected - people are walking at normal pace, no wrong-direction motion, no unusual postures or out-of-place objects. The 6.6% pixel difference from re

- `D8_0070` [D8] label=0 agent=0.15 direct=0.02 Δerr=+0.130
  > The query image shows normal pedestrian activity in a walkway setting. People are standing or walking at normal paces in expected directions. The pixel differences observed are consistent with normal movement between frames rather than anom

## Losses (agent worse than Direct)

- `D8_0003` [D8] label=0 agent=0.15 direct=0.02 Δerr=+0.130
  > The query image shows a pedestrian walkway scene consistent with the reference images. All visible elements (pedestrians, pillars, pavement, staircase) appear normal with no evidence of anomalous behavior like wrong-direction motion, unusua

- `D9_0018` [D9] label=0 agent=0.15 direct=0.02 Δerr=+0.130
  > The subspacead expert indicated a weak anomaly signal, and visual inspection of the patch grid confirms the presence of expected hardware components (bolts, nuts, washers) without obvious missing or extra parts. The query appears structural

- `D8_0028` [D8] label=0 agent=0.30 direct=0.02 Δerr=+0.280
  > The query image shows pedestrians walking in what appears to be normal patterns. While there are some people in different positions compared to references, their behavior (walking, standing) appears consistent with normal pedestrian activit

- `D6_0066` [D6] label=0 agent=0.50 direct=0.05 Δerr=+0.450
  > json parse failed

- `D7_0071` [D7] label=0 agent=0.50 direct=0.05 Δerr=+0.450
  > json parse failed

- `D6_0126` [D6] label=1 agent=0.50 direct=0.98 Δerr=+0.480
  > json parse failed

- `D6_0090` [D6] label=1 agent=0.30 direct=0.95 Δerr=+0.650
  > While the image_diff showed 30.4% pixel change, the visual evidence from patch grid suggests similar building structures between query and reference. The differences are likely due to seasonal/illumination variations rather than actual buil

- `D6_0109` [D6] label=1 agent=0.15 direct=0.95 Δerr=+0.800
  > After examining the query and reference images, the building footprints, road layouts, and structural elements appear consistent between query and reference. The observed differences are primarily seasonal (vegetation color changes from bro

- `D7_0072` [D7] label=0 agent=0.84 direct=0.02 Δerr=+0.820
  > The subspacead expert returned a strong anomaly signal (normalized_rank 0.837 > 0.80 threshold). While the highway scene appears visually normal with typical vehicles and road infrastructure, the expert model detected subtle anomalies that 

- `D7_0001` [D7] label=0 agent=0.95 direct=0.02 Δerr=+0.930
  > The query image shows a severely damaged and crumpled car hood in the foreground, which is a significant anomaly compared to the normal, undamaged road scenes in the reference images. This damage is a clear deviation from the expected norma
