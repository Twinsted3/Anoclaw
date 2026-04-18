# Diagnosis: tool_rotate_align

Total calls: 12

## Failure mode (manual analysis — fill in)

_TBD: wrong trigger / unclear output / VLM misreads / mixed_

## Wins (agent better than Direct)

- `D1_0121` [D1] label=1 agent=0.35 direct=0.02 Δerr=-0.330
  > The expert anomaly score (0.67) is below the strong anomaly threshold (0.80). The image diff shows moderate differences likely due to minor positioning variations rather than physical defects. No clear scratches, dents, or structural anomal

- `D10_0126` [D10] label=1 agent=0.15 direct=0.01 Δerr=-0.140
  > The expert anomaly score was very low (0.12 rank), and visual inspection of hotspots revealed no defects. The pixel difference is attributed to non-defect variations like lighting or position, consistent with a normal sample.

- `D10_0165` [D10] label=1 agent=0.15 direct=0.01 Δerr=-0.140
  > The query image shows normal green capsules with no visible defects. The high pixel difference is due to positional variation between images, not actual anomalies. All capsules have consistent color, shape, and surface quality matching the 

- `D2_0161` [D2] label=1 agent=0.15 direct=0.02 Δerr=-0.130
  > The query image shows the back of the bottle with nutritional information, while references show the front. The label is intact with no visible defects, tears, or damage. The moderate anomaly signal is due to the different bottle sides bein

- `D1_0068` [D1] label=0 agent=0.15 direct=0.02 Δerr=+0.130
  > The query image shows a normal screw. The high pixel difference is due to orientation/position mismatch with the reference, not a physical defect. The expert anomaly score was low (0.45 rank), and visual inspection confirmed no defects.

- `D1_0075` [D1] label=0 agent=0.15 direct=0.01 Δerr=+0.140
  > The query image shows a consistent mesh pattern matching the reference images. The subspacead expert score was low (0.21 normalized rank), indicating no strong anomaly signal. The high pixel difference is due to natural texture variation in

- `D2_0000` [D2] label=0 agent=0.15 direct=0.01 Δerr=+0.140
  > The query image shows the same Lay's chip canister as the references, just rotated to display a different side. The 7.3% difference with reference 3 (side view) confirms this is a normal pose variation, not a physical defect. No anomalies d

- `D10_0040` [D10] label=0 agent=0.15 direct=0.01 Δerr=+0.140
  > The query image shows a defect-free PCB. The low subspacead anomaly score (0.21 rank), clean hotspot inspection, and consistent component placement confirm it matches the normal reference images. The pixel differences are attributed to mino

- `D1_0061` [D1] label=0 agent=0.35 direct=0.02 Δerr=+0.330
  > The subspacead normalized rank of 0.43 is below the 0.80 anomaly threshold. While image diff shows some differences, these appear to be due to lighting/positioning rather than physical defects. The screw structure, threads, and head appear 

- `D1_0018` [D1] label=0 agent=0.35 direct=0.01 Δerr=+0.340
  > The query image shows the same mesh pattern as references with only moderate anomaly signals (0.40 normalized rank). The 3 connected components among 5 hotspots suggest localized variations rather than distinct defects. The pattern appears 

## Losses (agent worse than Direct)

- `D10_0165` [D10] label=1 agent=0.15 direct=0.01 Δerr=-0.140
  > The query image shows normal green capsules with no visible defects. The high pixel difference is due to positional variation between images, not actual anomalies. All capsules have consistent color, shape, and surface quality matching the 

- `D2_0161` [D2] label=1 agent=0.15 direct=0.02 Δerr=-0.130
  > The query image shows the back of the bottle with nutritional information, while references show the front. The label is intact with no visible defects, tears, or damage. The moderate anomaly signal is due to the different bottle sides bein

- `D1_0068` [D1] label=0 agent=0.15 direct=0.02 Δerr=+0.130
  > The query image shows a normal screw. The high pixel difference is due to orientation/position mismatch with the reference, not a physical defect. The expert anomaly score was low (0.45 rank), and visual inspection confirmed no defects.

- `D1_0075` [D1] label=0 agent=0.15 direct=0.01 Δerr=+0.140
  > The query image shows a consistent mesh pattern matching the reference images. The subspacead expert score was low (0.21 normalized rank), indicating no strong anomaly signal. The high pixel difference is due to natural texture variation in

- `D2_0000` [D2] label=0 agent=0.15 direct=0.01 Δerr=+0.140
  > The query image shows the same Lay's chip canister as the references, just rotated to display a different side. The 7.3% difference with reference 3 (side view) confirms this is a normal pose variation, not a physical defect. No anomalies d

- `D10_0040` [D10] label=0 agent=0.15 direct=0.01 Δerr=+0.140
  > The query image shows a defect-free PCB. The low subspacead anomaly score (0.21 rank), clean hotspot inspection, and consistent component placement confirm it matches the normal reference images. The pixel differences are attributed to mino

- `D1_0061` [D1] label=0 agent=0.35 direct=0.02 Δerr=+0.330
  > The subspacead normalized rank of 0.43 is below the 0.80 anomaly threshold. While image diff shows some differences, these appear to be due to lighting/positioning rather than physical defects. The screw structure, threads, and head appear 

- `D1_0018` [D1] label=0 agent=0.35 direct=0.01 Δerr=+0.340
  > The query image shows the same mesh pattern as references with only moderate anomaly signals (0.40 normalized rank). The 3 connected components among 5 hotspots suggest localized variations rather than distinct defects. The pattern appears 

- `D1_0006` [D1] label=0 agent=0.35 direct=0.01 Δerr=+0.340
  > The screw appears normal with consistent thread patterns and no visible defects. The moderate anomaly score is likely due to lighting variations and normal manufacturing tolerances rather than actual defects. The hotspot analysis showed no 

- `D2_0013` [D2] label=0 agent=0.92 direct=0.01 Δerr=+0.910
  > The query bottle is missing the main 'Scream' logo and white graphics present on all reference bottles. Rotation alignment confirmed this is not a viewing angle issue but a genuine label defect (missing branding), which constitutes an anoma
