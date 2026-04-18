# Diagnosis: tool_hotspot_cropper

Total calls: 606

## Failure mode (manual analysis — fill in)

_TBD: wrong trigger / unclear output / VLM misreads / mixed_

## Wins (agent better than Direct)

- `D5c_0164` [D5c] label=1 agent=0.96 direct=0.02 Δerr=-0.940
  > The query image contains a clear hypodense lesion, confirmed by a high subspacead anomaly score (0.96) and visual inspection of the hotspot, indicating liver pathology.

- `D5c_0167` [D5c] label=1 agent=0.95 direct=0.02 Δerr=-0.930
  > The query image displays a small, detached component attached to the main liver structure, which is absent in all normal reference images. The subspacead expert score confirms a strong anomaly signal (normalized rank 0.92). This structural 

- `D2_0132` [D2] label=1 agent=0.92 direct=0.01 Δerr=-0.910
  > The query image shows a purple Mirinda can with a visible contamination defect: a cluster of foreign fiber-like material stuck to the can's surface, which is a clear physical anomaly compared to the clean reference images.

- `D2_0176` [D2] label=1 agent=0.92 direct=0.02 Δerr=-0.900
  > The query image shows a cigarette pack where the central circular logo is missing the detailed rose graphic present in all reference images, appearing as a plain yellow circle instead. The image_diff confirms a significant structural differ

- `D5c_0126` [D5c] label=1 agent=0.92 direct=0.02 Δerr=-0.900
  > The query image exhibits a focal lesion, as evidenced by the high anomaly score from subspacead, the dark irregular region in the hotspot crop, and the significant difference highlighted by the image_diff tool. These findings are consistent

- `D1_0057` [D1] label=0 agent=0.05 direct=0.95 Δerr=-0.900
  > The subspacead expert returned a very low normalized rank (0.0023) indicating normal. The image diff shows expected texture variation (49% change) typical for speckled surfaces, not defects. The query matches the reference pattern.

- `D5c_0098` [D5c] label=1 agent=0.94 direct=0.05 Δerr=-0.890
  > The query image displays a significant structural anomaly, a large protrusion or mass on the liver, which is quantitatively supported by the high anomaly score from the subspacead expert and visually confirmed by the hotspot analysis. This 

- `D9_0001` [D9] label=0 agent=0.10 direct=0.98 Δerr=-0.880
  > The subspacead expert score is very low (0.07), indicating no anomaly. The pixel difference from the reference is due to random pin placement, not a logical defect like missing or extra pins. The query appears normal.

- `D2_0172` [D2] label=1 agent=0.85 direct=0.01 Δerr=-0.840
  > The hotspot analysis confirms a torn/damaged seal at the top of the Lay's can, which is a clear physical packaging defect. This anomaly is visible as a jagged tear in the plastic seal, distinguishing it from the intact packaging in the refe

- `D9_0075` [D9] label=0 agent=0.15 direct=0.99 Δerr=-0.840
  > The query image shows a yellow cable with orange connectors on a mesh background, which matches the normal variations described in the reference profiler (wire color can be yellow, orange, or blue). The subspacead expert score showed a weak

## Losses (agent worse than Direct)

- `D9_0106` [D9] label=1 agent=0.10 direct=0.99 Δerr=+0.890
  > The query image shows a yellow cable with single orange connectors, which matches the normal variations seen in references. The subspacead expert returned a very low anomaly score (normalized rank 0.067), and visual inspection confirms no s

- `D5c_0079` [D5c] label=0 agent=0.92 direct=0.02 Δerr=+0.900
  > The query image displays a distinct hypodense lesion within the liver parenchyma, which is inconsistent with the uniform texture of the normal reference images. This is confirmed by a very high anomaly score (92.33) and a strong normalized 

- `D5c_0062` [D5c] label=0 agent=0.92 direct=0.02 Δerr=+0.900
  > The query image displays two distinct hypodense focal lesions within the liver parenchyma, which are absent in the normal reference images. This is confirmed by the strong anomaly signal (rank 0.86) from the subspacead expert, indicating a 

- `D5c_0052` [D5c] label=0 agent=0.92 direct=0.02 Δerr=+0.900
  > The subspacead expert returned a high anomaly score (normalized rank 0.85) with a 'strong anomaly signal' interpretation. Visually, the query image contains distinct dark hypodense regions (lesions/cysts) within the liver parenchyma, which 

- `D7_0001` [D7] label=0 agent=0.95 direct=0.02 Δerr=+0.930
  > The query image shows a severely damaged and crumpled car hood in the foreground, which is a significant anomaly compared to the normal, undamaged road scenes in the reference images. This damage is a clear deviation from the expected norma

- `D7_0084` [D7] label=0 agent=0.95 direct=0.02 Δerr=+0.930
  > The hotspot inspection revealed a motorcycle accident on the road, with a fallen bike and a person on the ground. This is a clear and significant anomaly representing a driving hazard and unexpected obstacle.

- `D9_0133` [D9] label=1 agent=0.05 direct=0.98 Δerr=+0.930
  > The subspacead expert score was very low (0.07), indicating a strong match to normal references. Visual inspection of the highlighted regions confirms the pushpins are intact, correctly colored, and arranged without obvious logical or struc

- `D9_0153` [D9] label=1 agent=0.05 direct=0.98 Δerr=+0.930
  > The subspacead expert detected a weak anomaly signal (normalized rank 0.04), and visual inspection of the hotspots confirms the pushpins and compartments appear normal, consistent with the reference images. No logical or structural anomalie

- `D5c_0076` [D5c] label=0 agent=0.95 direct=0.02 Δerr=+0.930
  > The query image is almost completely black, containing only a tiny speck, whereas all reference images show a complete liver cross-section. This indicates the liver is missing or the image is corrupted, which is a definitive anomaly.

- `D5d_0049` [D5d] label=0 agent=0.95 direct=0.02 Δerr=+0.930
  > Despite the low expert score, visual inspection clearly shows a raised, nodular polypoid lesion in the center of the query image, which is a pathological finding. The reference images show normal, flat mucosa. This structural abnormality co
