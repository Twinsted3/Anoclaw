# Per-Item Flip Analysis — dev n=480

## Headline: do any tools have exploitable per-item gains?

| tool | flips→correct | flips→wrong | net_flips | n_wins (flips+improved) | n_losses | win/loss |
|---|---|---|---|---|---|---|
| tool_texture_fft | 8 | 16 | -8 | 9 | 16 | 0.56 |
| tool_patch_grid | 42 | 64 | -22 | 43 | 71 | 0.61 |
| tool_image_diff | 51 | 83 | -32 | 58 | 95 | 0.61 |
| tool_segment_and_count | 47 | 81 | -34 | 56 | 106 | 0.53 |
| tool_hotspot_cropper | 55 | 90 | -35 | 60 | 110 | 0.55 |
| tool_rotate_align | 47 | 86 | -39 | 56 | 107 | 0.52 |
| tool_side_by_side | 67 | 107 | -40 | 72 | 121 | 0.60 |
| tool_zoom_bbox | 55 | 95 | -40 | 58 | 110 | 0.53 |
| tool_expert_score | 52 | 93 | -41 | 77 | 190 | 0.41 |
| tool_reference_profiler | 48 | 89 | -41 | 50 | 93 | 0.54 |
| tool_component_counter | 46 | 95 | -49 | 56 | 123 | 0.46 |
| tool_domain_knowledge | 50 | 110 | -60 | 52 | 114 | 0.46 |

## Per-tool trigger analysis

For each tool, comparing WIN items vs LOSS items reveals whether a
distinguishable pattern exists that could be injected as a trigger
hint in the agent prompt.

### tool_texture_fft  (net flips -8, wins 9, losses 16)

**Win items** (n=9): domains={'D1': 6, 'D2': 3}; label_pos_rate=[(0, 7), (1, 2)]; rank(hi/mid/lo)=1/1/7; direct_mid(uncertain)=0; direct_conf(extreme)=9; tool_used=4/9

**Loss items** (n=16): domains={'D2': 8, 'D1': 4, 'D4': 4}; label_pos_rate=[(1, 13), (0, 3)]; rank(hi/mid/lo)=6/5/5; direct_mid(uncertain)=0; direct_conf(extreme)=16; tool_used=11/16

**Keywords distinctive in WIN rationales** (word: n_wins n_losses score):

- `appearance`: wins=4 losses=0 score=+1.00
- `clear`: wins=4 losses=0 score=+1.00
- `expected`: wins=3 losses=0 score=+1.00
- `obvious`: wins=3 losses=0 score=+1.00
- `liquid`: wins=3 losses=0 score=+1.00

**Sample WIN items (tool flipped correctly):**

- `D1_0038` [D1] label=0 direct=0.98→tool=0.10  rank=0.26  used_tool=False
  > The query image appears normal as it shows a standard capsule with expected markings. The absence of 'actavis' in some reference images might be due to different angles or lighting, but the query imag
- `D1_0084` [D1] label=0 direct=0.95→tool=0.10  rank=0.02  used_tool=False
  > The query image exhibits the same random speckled texture as the reference images, with no obvious visual defects or deviations. The texture is non-periodic, so the FFT tool would not be discriminativ
- `D1_0064` [D1] label=0 direct=0.98→tool=0.10  rank=0.24  used_tool=False
  > The query image appears normal as it matches the expected appearance of the capsule with both 'actavis' and '500' markings, similar to some of the reference images.
- `D1_0088` [D1] label=0 direct=0.95→tool=0.10  rank=0.29  used_tool=False
  > The query image appears visually consistent with the normal reference images. The transistor is properly mounted, pins are intact, and the PCB traces and pads look standard. No obvious anomalies are d
- `D1_0009` [D1] label=0 direct=0.95→tool=0.05  rank=0.13  used_tool=True
  > The low periodicity score indicates an irregular texture, which the tool's disconfirm clause states is normal for this type of object. Visually, the query image matches the reference images in structu

**Sample LOSS items (tool flipped wrong):**

- `D1_0094` [D1] label=1 direct=0.98→tool=0.05  rank=0.77  used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard 'actavis 500' capsule with no apparent defects or anomalies.
- `D1_0142` [D1] label=1 direct=0.95→tool=0.05  rank=0.32  used_tool=True
  > The low periodicity score indicates an irregular texture, but the tool's disconfirm clause states this is normal for natural scenes like wood. Visual inspection confirms the query image is a standard 
- `D1_0111` [D1] label=1 direct=0.98→tool=0.05  rank=0.77  used_tool=True
  > The low periodicity score is expected for woven fabric textures and the interpretation explicitly warns against using this alone to flag anomalies. Visual inspection confirms the query image matches t
- `D2_0056` [D2] label=0 direct=0.01→tool=0.95  rank=0.05  used_tool=False
  > The query image displays a distinctly different packaging design with a blue grid pattern and different text arrangement compared to the consistent blueberry milk drink packaging in all reference imag
- `D1_0179` [D1] label=1 direct=0.95→tool=0.05  rank=0.54  used_tool=True
  > The low periodicity score indicates irregular texture, but the tool's disconfirm clause states this is normal for such domains. Visual inspection confirms the query image is consistent with the normal

### tool_patch_grid  (net flips -22, wins 43, losses 71)

**Win items** (n=43): domains={'D9': 7, 'D5c': 7, 'D1': 5, 'D6': 5, 'D2': 4, 'D10': 4}; label_pos_rate=[(0, 26), (1, 17)]; rank(hi/mid/lo)=14/14/15; direct_mid(uncertain)=0; direct_conf(extreme)=43; tool_used=18/43

**Loss items** (n=71): domains={'D6': 18, 'D9': 11, 'D5': 9, 'D2': 7, 'D8': 6, 'D5d': 6}; label_pos_rate=[(1, 44), (0, 27)]; rank(hi/mid/lo)=19/38/14; direct_mid(uncertain)=0; direct_conf(extreme)=71; tool_used=53/71

**Keywords distinctive in WIN rationales** (word: n_wins n_losses score):

- `object`: wins=11 losses=0 score=+1.00
- `different`: wins=10 losses=0 score=+1.00
- `contains`: wins=8 losses=0 score=+1.00
- `expected`: wins=7 losses=0 score=+1.00
- `visible`: wins=7 losses=0 score=+1.00
- `shape`: wins=7 losses=0 score=+1.00
- `standard`: wins=6 losses=0 score=+1.00
- `appearance`: wins=6 losses=0 score=+1.00

**Sample WIN items (tool flipped correctly):**

- `D1_0084` [D1] label=0 direct=0.95→tool=0.05  rank=0.02  used_tool=False
  > The query image exhibits the same speckled pattern and texture as the normal reference images, with no discernible anomalies.
- `D1_0038` [D1] label=0 direct=0.98→tool=0.10  rank=0.26  used_tool=True
  > The query image shows a standard two-toned capsule with the 'actavis' logo, matching the majority of the reference images. The difference between the black and orange halves is a natural feature of th
- `D1_0088` [D1] label=0 direct=0.95→tool=0.05  rank=0.29  used_tool=False
  > The query image displays a standard transistor component mounted on a PCB, which is visually consistent with the provided normal reference images. No anomalies such as missing components, broken leads
- `D1_0064` [D1] label=0 direct=0.98→tool=0.10  rank=0.24  used_tool=True
  > The patch grid tiles show expected variations corresponding to different parts of the capsule (black cap, orange body with text, background). No single tile exhibits an anomalous texture or content th
- `D1_0114` [D1] label=1 direct=0.02→tool=0.95  rank=0.19  used_tool=False
  > The query image has yellow bristles while all reference images have either blue or red bristles, indicating a clear color anomaly that deviates from the established normal pattern.

**Sample LOSS items (tool flipped wrong):**

- `D1_0094` [D1] label=1 direct=0.98→tool=0.05  rank=0.77  used_tool=False
  > The query capsule matches the reference capsules in color, text, and overall appearance with no visible anomalies.
- `D2_0029` [D2] label=0 direct=0.01→tool=0.90  rank=0.51  used_tool=False
  > The query image displays the back label of the bottle, whereas all reference images show the front label. This difference in the primary visual content (label side) is a clear anomaly in the context o
- `D2_0087` [D2] label=0 direct=0.01→tool=0.95  rank=0.08  used_tool=True
  > The query image is upside-down compared to the normal references, with inverted text on the cigarette pack, which is a clear anomaly.
- `D2_0080` [D2] label=0 direct=0.02→tool=1.00  rank=0.02  used_tool=False
  > The query image displays the back of the package (with nutritional information and barcode), whereas all reference images display the front of the package (with branding and product view). This is a d
- `D2_0170` [D2] label=1 direct=0.98→tool=0.10  rank=0.13  used_tool=False
  > The query image appears to be a normal front view of the snack package, matching the appearance of the first and last reference images. There are no obvious defects, missing elements, or unusual marki

### tool_image_diff  (net flips -32, wins 58, losses 95)

**Win items** (n=58): domains={'D1': 7, 'D6': 7, 'D9': 7, 'D5d': 6, 'D5b': 5, 'D5c': 5}; label_pos_rate=[(0, 30), (1, 28)]; rank(hi/mid/lo)=14/27/17; direct_mid(uncertain)=0; direct_conf(extreme)=58; tool_used=30/58

**Loss items** (n=95): domains={'D6': 19, 'D2': 12, 'D5': 11, 'D4': 10, 'D5d': 9, 'D9': 8}; label_pos_rate=[(1, 57), (0, 38)]; rank(hi/mid/lo)=29/46/20; direct_mid(uncertain)=0; direct_conf(extreme)=95; tool_used=65/95

**Keywords distinctive in WIN rationales** (word: n_wins n_losses score):

- `contains`: wins=11 losses=0 score=+1.00
- `clear`: wins=10 losses=0 score=+1.00
- `object`: wins=9 losses=0 score=+1.00
- `scene`: wins=9 losses=0 score=+1.00

**Sample WIN items (tool flipped correctly):**

- `D1_0084` [D1] label=0 direct=0.95→tool=0.05  rank=0.02  used_tool=False
  > The query image exhibits the same speckled texture pattern as the reference images with no visible defects or anomalies.
- `D1_0038` [D1] label=0 direct=0.98→tool=0.05  rank=0.26  used_tool=True
  > The query image matches the majority of reference images, displaying the 'actavis' logo and '500' text. The difference observed against reference 3 is due to the presence of the logo, which is a norma
- `D1_0064` [D1] label=0 direct=0.98→tool=0.05  rank=0.24  used_tool=True
  > The query image matches the majority of reference images (0, 1, 2) which include the 'actavis' logo. The difference with reference 3 is due to the missing logo in that reference, not an anomaly in the
- `D1_0088` [D1] label=0 direct=0.95→tool=0.05  rank=0.29  used_tool=False
  > Visual inspection confirms the query image matches the reference images in component type, orientation, and PCB layout. No defects or anomalies are visible.
- `D1_0009` [D1] label=0 direct=0.95→tool=0.15  rank=0.13  used_tool=True
  > Despite high pixel differences detected by the tool, the visual appearance of the query image matches the reference images closely. The differences are attributed to lighting variations rather than ac

**Sample LOSS items (tool flipped wrong):**

- `D1_0008` [D1] label=0 direct=0.02→tool=0.95  rank=0.12  used_tool=False
  > The query image displays a brush with yellow and white bristles, whereas all reference images show brushes with either blue/white or red/white bristles. This significant color deviation from the refer
- `D1_0094` [D1] label=1 direct=0.98→tool=0.05  rank=0.77  used_tool=True
  > The observed pixel differences are attributed to benign lighting or focus variations as indicated by the tool's disconfirm clause, and the capsule visually matches the normal references.
- `D1_0111` [D1] label=1 direct=0.98→tool=0.05  rank=0.77  used_tool=True
  > The pixel diff tool was unreliable due to misalignment. Visual inspection shows the query image has a normal, consistent fabric texture with no visible anomalies.
- `D2_0056` [D2] label=0 direct=0.01→tool=1.00  rank=0.05  used_tool=False
  > The query image displays a different product packaging design than the normal reference images, indicating an anomaly.
- `D1_0179` [D1] label=1 direct=0.95→tool=0.15  rank=0.54  used_tool=True
  > The pixel differences are consistent across multiple references (~21%) and scattered throughout the image, indicating benign lighting/positioning variations rather than a true defect. No localized ano

### tool_segment_and_count  (net flips -34, wins 56, losses 106)

**Win items** (n=56): domains={'D5c': 8, 'D9': 7, 'D1': 6, 'D6': 6, 'D8': 6, 'D2': 5}; label_pos_rate=[(0, 31), (1, 25)]; rank(hi/mid/lo)=17/24/15; direct_mid(uncertain)=0; direct_conf(extreme)=56; tool_used=48/56

**Loss items** (n=106): domains={'D6': 14, 'D5': 13, 'D2': 12, 'D9': 11, 'D5d': 10, 'D8': 9}; label_pos_rate=[(1, 62), (0, 44)]; rank(hi/mid/lo)=25/54/27; direct_mid(uncertain)=0; direct_conf(extreme)=106; tool_used=96/106

**Keywords distinctive in WIN rationales** (word: n_wins n_losses score):

- `different`: wins=13 losses=0 score=+1.00
- `scene`: wins=11 losses=0 score=+1.00
- `clear`: wins=10 losses=0 score=+1.00
- `actual`: wins=9 losses=0 score=+1.00

**Sample WIN items (tool flipped correctly):**

- `D1_0084` [D1] label=0 direct=0.95→tool=0.05  rank=0.02  used_tool=False
  > The query image exhibits the same speckled texture and pattern distribution as the normal reference images. No structural anomalies or deviations are visible.
- `D1_0038` [D1] label=0 direct=0.98→tool=0.10  rank=0.26  used_tool=True
  > The tool confirms no structural anomalies, and the apparent difference in the 'actavis' logo is likely due to lighting or image quality, not a defect.
- `D1_0064` [D1] label=0 direct=0.98→tool=0.10  rank=0.24  used_tool=True
  > The segmentation tool found no coarse structural differences. The visual difference (presence of 'actavis' logo) appears to be a normal variation in printing or orientation rather than a defect, as th
- `D1_0088` [D1] label=0 direct=0.95→tool=0.10  rank=0.29  used_tool=True
  > The structural differences detected by the tool are likely due to lighting or exposure variations, as indicated by the disconfirm clause. Visual inspection confirms the component and PCB structure are
- `D2_0037` [D2] label=0 direct=0.98→tool=0.10  rank=0.19  used_tool=True
  > The query image shows a normal view of the product's back, consistent with reference images. The detected differences are likely due to lighting and angle variations, not actual defects.

**Sample LOSS items (tool flipped wrong):**

- `D1_0094` [D1] label=1 direct=0.98→tool=0.05  rank=0.77  used_tool=False
  > The query image matches the reference images in shape, color, and text markings. No anomalies are detected.
- `D1_0111` [D1] label=1 direct=0.98→tool=0.05  rank=0.77  used_tool=True
  > The segmentation tool found no structural anomalies (0/64 cells changed). The weave pattern in the query image matches the reference images, with only minor pixel-level variations that are within norm
- `D1_0179` [D1] label=1 direct=0.95→tool=0.05  rank=0.54  used_tool=False
  > The query image is visually consistent with the normal reference images, showing the same component type without any apparent anomalies.
- `D2_0056` [D2] label=0 direct=0.01→tool=1.00  rank=0.05  used_tool=False
  > The query image displays a fundamentally different product packaging design compared to the normal reference images, indicating a certain anomaly.
- `D2_0029` [D2] label=0 direct=0.01→tool=0.95  rank=0.51  used_tool=False
  > The query image displays the back label of the bottle, whereas all reference images display the front label. This significant difference in the visible content (label side) indicates an anomaly.

### tool_hotspot_cropper  (net flips -35, wins 60, losses 110)

**Win items** (n=60): domains={'D9': 8, 'D5c': 8, 'D1': 6, 'D6': 6, 'D8': 6, 'D5b': 5}; label_pos_rate=[(0, 31), (1, 29)]; rank(hi/mid/lo)=16/27/17; direct_mid(uncertain)=0; direct_conf(extreme)=60; tool_used=6/60

**Loss items** (n=110): domains={'D5': 18, 'D6': 15, 'D4': 13, 'D5c': 12, 'D5d': 12, 'D9': 10}; label_pos_rate=[(1, 63), (0, 47)]; rank(hi/mid/lo)=29/54/27; direct_mid(uncertain)=0; direct_conf(extreme)=110; tool_used=18/110

**Keywords distinctive in WIN rationales** (word: n_wins n_losses score):

- `deviation`: wins=12 losses=0 score=+1.00
- `compared`: wins=8 losses=0 score=+1.00
- `standard`: wins=8 losses=0 score=+1.00
- `defects`: wins=7 losses=0 score=+1.00
- `variation`: wins=7 losses=0 score=+1.00
- `liquid`: wins=7 losses=0 score=+1.00
- `obvious`: wins=6 losses=0 score=+1.00
- `structures`: wins=6 losses=0 score=+1.00

**Sample WIN items (tool flipped correctly):**

- `D1_0084` [D1] label=0 direct=0.95→tool=0.05  rank=0.02  used_tool=False
  > The query image appears visually identical to the normal reference images, showing the same consistent speckled pattern without any detectable defects or anomalies.
- `D1_0038` [D1] label=0 direct=0.98→tool=0.10  rank=0.26  used_tool=False
  > The query image displays a capsule with 'actavis' and '500' markings, which is consistent with three out of the four provided normal reference images. The only difference is one reference image lackin
- `D1_0088` [D1] label=0 direct=0.95→tool=0.05  rank=0.29  used_tool=False
  > The query image is visually consistent with the normal reference images, showing a properly mounted transistor with no apparent anomalies.
- `D1_0009` [D1] label=0 direct=0.95→tool=0.05  rank=0.13  used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard three-core cable cross-section with no apparent anomalies.
- `D1_0064` [D1] label=0 direct=0.98→tool=0.10  rank=0.24  used_tool=True
  > The query image displays a capsule with 'actavis' and '500' printed on it, which matches the majority of the reference images. The cropped region shows standard printing without defects. The absence o

**Sample LOSS items (tool flipped wrong):**

- `D1_0179` [D1] label=1 direct=0.95→tool=0.05  rank=0.54  used_tool=False
  > The query image is visually consistent with the normal reference images, showing no detectable anomalies in shape, texture, or structure.
- `D2_0056` [D2] label=0 direct=0.01→tool=1.00  rank=0.05  used_tool=False
  > The query image displays a significantly different packaging design and text layout compared to the normal reference images, indicating an anomaly.
- `D1_0137` [D1] label=1 direct=0.98→tool=0.10  rank=0.72  used_tool=False
  > The query image is visually consistent with three of the four normal reference images, showing both the 'actavis' logo and '500' imprint. The fourth reference image lacks the 'actavis' logo, but this 
- `D2_0087` [D2] label=0 direct=0.01→tool=0.95  rank=0.08  used_tool=False
  > The query image displays the cigarette pack upside down, with the warning text and logo inverted relative to the normal reference images, indicating a clear anomaly.
- `D2_0080` [D2] label=0 direct=0.02→tool=1.00  rank=0.02  used_tool=False
  > The query image shows the back of the product packaging, while the reference images show the front, making it an anomaly.

### tool_rotate_align  (net flips -39, wins 56, losses 107)

**Win items** (n=56): domains={'D1': 7, 'D4': 6, 'D6': 6, 'D5c': 6, 'D8': 5, 'D9': 5}; label_pos_rate=[(1, 29), (0, 27)]; rank(hi/mid/lo)=16/25/15; direct_mid(uncertain)=0; direct_conf(extreme)=56; tool_used=37/56

**Loss items** (n=107): domains={'D5': 17, 'D2': 16, 'D6': 13, 'D4': 10, 'D9': 10, 'D1': 8}; label_pos_rate=[(1, 54), (0, 53)]; rank(hi/mid/lo)=25/49/33; direct_mid(uncertain)=0; direct_conf(extreme)=107; tool_used=75/107

**Keywords distinctive in WIN rationales** (word: n_wins n_losses score):

- `content`: wins=10 losses=0 score=+1.00
- `confirms`: wins=9 losses=0 score=+1.00
- `contains`: wins=9 losses=0 score=+1.00
- `direct`: wins=9 losses=0 score=+1.00

**Sample WIN items (tool flipped correctly):**

- `D1_0084` [D1] label=0 direct=0.95→tool=0.05  rank=0.02  used_tool=False
  > The query image exhibits the same speckled texture and pattern distribution as the reference images, with no detectable anomalies.
- `D1_0038` [D1] label=0 direct=0.98→tool=0.10  rank=0.26  used_tool=True
  > The query image matches the reference images in content (logo and text). The small difference detected by the tool is likely due to minor lighting or color variations, as suggested by the tool's disco
- `D1_0088` [D1] label=0 direct=0.95→tool=0.05  rank=0.29  used_tool=False
  > The query image is visually consistent with the normal reference images, showing a correctly mounted transistor with no apparent anomalies.
- `D1_0064` [D1] label=0 direct=0.98→tool=0.10  rank=0.24  used_tool=True
  > The low mean difference and the tool's disconfirm clause indicating potential lighting variations suggest the query image is normal. Visual inspection confirms the capsule matches the reference.
- `D1_0114` [D1] label=1 direct=0.02→tool=0.95  rank=0.19  used_tool=False
  > The query image has yellow bristles, whereas all reference images have either blue or red bristles. This color discrepancy strongly suggests the query is anomalous.

**Sample LOSS items (tool flipped wrong):**

- `D1_0008` [D1] label=0 direct=0.02→tool=0.95  rank=0.12  used_tool=False
  > The query image has yellow bristles, whereas all reference images have either blue or red bristles. This color difference is a definitive visual anomaly.
- `D1_0019` [D1] label=0 direct=0.02→tool=0.85  rank=0.36  used_tool=True
  > The query image displays a hazelnut with a distinctly dark, jagged, and irregular scar at the base, which contrasts sharply with the smoother, lighter, and more uniform scars seen on the normal refere
- `D1_0142` [D1] label=1 direct=0.95→tool=0.10  rank=0.32  used_tool=True
  > The visual difference is a variation in wood grain pattern (lighter streaks), which is a natural characteristic of wood textures. The tool's interpretation also suggests the signal is likely due to no
- `D1_0111` [D1] label=1 direct=0.98→tool=0.15  rank=0.77  used_tool=True
  > The rotation alignment showed differences but the interpretation explicitly states these could be lighting/color variations and the query is likely normal. No clear structural anomalies are visible in
- `D2_0056` [D2] label=0 direct=0.01→tool=1.00  rank=0.05  used_tool=False
  > The query image displays a different product packaging design than the normal reference images, indicating an anomaly.

### tool_side_by_side  (net flips -40, wins 72, losses 121)

**Win items** (n=72): domains={'D8': 11, 'D5c': 10, 'D4': 7, 'D5': 7, 'D9': 7, 'D1': 6}; label_pos_rate=[(1, 45), (0, 27)]; rank(hi/mid/lo)=19/34/19; direct_mid(uncertain)=0; direct_conf(extreme)=72; tool_used=60/72

**Loss items** (n=121): domains={'D5': 19, 'D6': 16, 'D4': 15, 'D5d': 14, 'D9': 11, 'D8': 10}; label_pos_rate=[(1, 64), (0, 57)]; rank(hi/mid/lo)=30/63/28; direct_mid(uncertain)=0; direct_conf(extreme)=121; tool_used=109/121

**Keywords distinctive in WIN rationales** (word: n_wins n_losses score):

- `four`: wins=8 losses=0 score=+1.00
- `deviation`: wins=8 losses=0 score=+1.00
- `one`: wins=7 losses=0 score=+1.00

**Sample WIN items (tool flipped correctly):**

- `D1_0084` [D1] label=0 direct=0.95→tool=0.10  rank=0.02  used_tool=True
  > The query image exhibits the same speckled texture as the reference images, with no unique structural or textural anomalies detected. The observed variations are consistent with natural texture variat
- `D1_0038` [D1] label=0 direct=0.98→tool=0.05  rank=0.26  used_tool=True
  > The query image contains the 'actavis' logo, matching three of the four reference images. The fourth reference image lacks the logo, suggesting it is the anomaly, not the query. Therefore, the query i
- `D1_0009` [D1] label=0 direct=0.95→tool=0.05  rank=0.13  used_tool=True
  > The query image displays a standard three-core cable cross-section. The side-by-side comparison confirms that any minor differences are within the range of natural variation observed in the reference 
- `D1_0114` [D1] label=1 direct=0.02→tool=0.95  rank=0.19  used_tool=False
  > The query image has yellow bristles while all reference images have either blue or red bristles, indicating a clear color anomaly that deviates from the established pattern.
- `D1_0064` [D1] label=0 direct=0.98→tool=0.10  rank=0.24  used_tool=True
  > The query image displays the 'actavis' logo, which is also present in three of the four reference images. The single reference image lacking the logo appears to be the outlier in the reference set, no

**Sample LOSS items (tool flipped wrong):**

- `D1_0117` [D1] label=1 direct=0.98→tool=0.10  rank=0.68  used_tool=True
  > The query image shows a hazelnut with a cap on the side, which is a normal variation compared to the reference images where caps are on the bottom or top. No anomalous features like cracks or discolor
- `D1_0179` [D1] label=1 direct=0.95→tool=0.10  rank=0.54  used_tool=True
  > The query image shows a metallic component that is structurally and texturally consistent with the four reference images. No unique defects or anomalies were identified in the query image compared to 
- `D2_0029` [D2] label=0 direct=0.01→tool=0.95  rank=0.51  used_tool=False
  > The query image displays the back label of the bottle, whereas all reference images display the front label. This fundamental difference in the object's orientation and visible content makes the query
- `D1_0137` [D1] label=1 direct=0.98→tool=0.10  rank=0.72  used_tool=True
  > The query image matches the majority of the reference images, showing a capsule with 'actavis' and '500' printed on it. The absence of the 'actavis' logo in one reference image is an anomaly, but the 
- `D2_0072` [D2] label=0 direct=0.02→tool=1.00  rank=0.06  used_tool=False
  > The query image displays the back of the chip bag, whereas all four reference images display the front of the bag. This difference in orientation and visible content (nutritional info/barcode vs. logo

### tool_zoom_bbox  (net flips -40, wins 58, losses 110)

**Win items** (n=58): domains={'D5c': 9, 'D1': 7, 'D9': 7, 'D2': 6, 'D5d': 6, 'D6': 5}; label_pos_rate=[(0, 32), (1, 26)]; rank(hi/mid/lo)=17/24/17; direct_mid(uncertain)=0; direct_conf(extreme)=58; tool_used=34/58

**Loss items** (n=110): domains={'D5': 17, 'D6': 17, 'D2': 12, 'D8': 10, 'D9': 10, 'D5d': 10}; label_pos_rate=[(1, 66), (0, 44)]; rank(hi/mid/lo)=25/64/21; direct_mid(uncertain)=0; direct_conf(extreme)=110; tool_used=78/110

**Keywords distinctive in WIN rationales** (word: n_wins n_losses score):

- `different`: wins=11 losses=0 score=+1.00
- `compared`: wins=9 losses=0 score=+1.00
- `detected`: wins=8 losses=0 score=+1.00
- `without`: wins=7 losses=0 score=+1.00
- `obvious`: wins=6 losses=0 score=+1.00
- `label`: wins=6 losses=0 score=+1.00
- `two`: wins=6 losses=0 score=+1.00
- `object`: wins=6 losses=0 score=+1.00
- `standard`: wins=5 losses=0 score=+1.00
- `appearance`: wins=5 losses=0 score=+1.00

**Sample WIN items (tool flipped correctly):**

- `D1_0084` [D1] label=0 direct=0.95→tool=0.05  rank=0.02  used_tool=False
  > The query image exhibits the same speckled pattern and texture as the normal reference images, with no detectable anomalies.
- `D1_0088` [D1] label=0 direct=0.95→tool=0.10  rank=0.29  used_tool=False
  > The query image is visually consistent with the provided normal reference images, showing a standard transistor mounted on a PCB without any apparent anomalies.
- `D1_0174` [D1] label=1 direct=0.02→tool=0.95  rank=0.15  used_tool=False
  > The query image displays a flat-packaged component on a PCB with different trace and pad geometry compared to the cylindrical components and PCB layout in the reference images, indicating a significan
- `D1_0038` [D1] label=0 direct=0.98→tool=0.05  rank=0.26  used_tool=True
  > The query image displays the 'actavis' logo and '500' imprint clearly, matching three of the four normal reference images. The zoomed inspection revealed no printing defects or anomalies. The single r
- `D1_0009` [D1] label=0 direct=0.95→tool=0.10  rank=0.13  used_tool=True
  > The blue conductor's strand pattern and condition appear normal, consistent with the reference images. The observed variations are attributed to lighting and reflection rather than a defect.

**Sample LOSS items (tool flipped wrong):**

- `D1_0008` [D1] label=0 direct=0.02→tool=0.95  rank=0.12  used_tool=False
  > The query image displays a brush with yellow bristles, whereas all normal reference images show brushes with either blue or red bristles. This significant color difference indicates an anomaly.
- `D2_0056` [D2] label=0 direct=0.01→tool=1.00  rank=0.05  used_tool=False
  > The query image displays a significantly different packaging design (blue background, different text layout) compared to the consistent white-background design in all normal reference images, indicati
- `D1_0179` [D1] label=1 direct=0.95→tool=0.10  rank=0.54  used_tool=True
  > Both zoomed regions show normal surface texture and clean edges consistent with reference images. No defects like cracks, chips, or irregularities were observed, suggesting the query image is normal.
- `D2_0087` [D2] label=0 direct=0.01→tool=0.95  rank=0.08  used_tool=True
  > Despite failed zoom attempts, the query image visibly shows the cigarette pack placed upside down relative to the normal reference images, which is a definitive anomaly in orientation.
- `D2_0083` [D2] label=0 direct=0.02→tool=0.95  rank=0.09  used_tool=False
  > The query image displays the back of the bottle with a barcode and text, while all reference images show the front with the main character logo. This represents a clear anomaly in the object's present

### tool_expert_score  (net flips -41, wins 77, losses 190)

**Win items** (n=77): domains={'D2': 10, 'D1': 9, 'D10': 9, 'D8': 8, 'D5d': 8, 'D6': 7}; label_pos_rate=[(1, 47), (0, 30)]; rank(hi/mid/lo)=20/38/19; direct_mid(uncertain)=0; direct_conf(extreme)=77; tool_used=67/77

**Loss items** (n=190): domains={'D6': 28, 'D5d': 25, 'D5b': 18, 'D8': 17, 'D1': 16, 'D5': 16}; label_pos_rate=[(0, 107), (1, 83)]; rank(hi/mid/lo)=42/114/34; direct_mid(uncertain)=0; direct_conf(extreme)=190; tool_used=183/190

**Keywords distinctive in WIN rationales** (word: n_wins n_losses score):

- `contains`: wins=12 losses=0 score=+1.00
- `difference`: wins=9 losses=0 score=+1.00
- `variations`: wins=9 losses=0 score=+1.00
- `deviation`: wins=9 losses=0 score=+1.00

**Sample WIN items (tool flipped correctly):**

- `D1_0084` [D1] label=0 direct=0.95→tool=0.05  rank=0.02  used_tool=False
  > The query image exhibits the same speckled texture pattern as the normal reference images, with no visible anomalies or deviations.
- `D1_0038` [D1] label=0 direct=0.98→tool=0.10  rank=0.26  used_tool=False
  > The query image displays the 'actavis' logo and '500' marking, consistent with three of the four reference images. The only difference is one reference image missing the logo, which makes that referen
- `D1_0064` [D1] label=0 direct=0.98→tool=0.15  rank=0.24  used_tool=True
  > The expert model indicates a weak anomaly signal (rank 0.24), and visual inspection confirms the query image is consistent with the normal reference images, showing expected variations in logo presenc
- `D1_0088` [D1] label=0 direct=0.95→tool=0.15  rank=0.29  used_tool=True
  > The expert model indicates a weak anomaly signal (rank 0.29), and visual inspection confirms the query image is consistent with the normal reference images, showing no obvious defects.
- `D1_0009` [D1] label=0 direct=0.95→tool=0.15  rank=0.13  used_tool=True
  > The subspacead expert returned a low anomaly score (rank 0.13), indicating the query is consistent with normal samples. Although the blue conductor appeared slightly different visually, the quantitati

**Sample LOSS items (tool flipped wrong):**

- `D1_0008` [D1] label=0 direct=0.02→tool=0.95  rank=0.12  used_tool=False
  > The query image has yellow bristles while all reference images have either blue or red bristles, indicating a clear color anomaly in the product.
- `D1_0094` [D1] label=1 direct=0.98→tool=0.05  rank=0.77  used_tool=False
  > The query image matches the reference images in terms of color, shape, and text markings. No anomalies are detected.
- `D1_0111` [D1] label=1 direct=0.98→tool=0.45  rank=0.77  used_tool=True
  > The query image shows a small dark spot that differs from the reference images, but the subspacead tool's moderate signal (rank 0.77) with its disconfirm clause suggests this could be normal texture v
- `D1_0137` [D1] label=1 direct=0.98→tool=0.15  rank=0.72  used_tool=True
  > The moderate anomaly signal is explained by normal variation in the reference set (some refs have text, some don't). The query image matches the 'with text' normal variant, so it is not anomalous.
- `D2_0056` [D2] label=0 direct=0.01→tool=0.95  rank=0.05  used_tool=False
  > The query image displays a different product packaging design than the reference images, indicating an anomaly in the product line.

### tool_reference_profiler  (net flips -41, wins 50, losses 93)

**Win items** (n=50): domains={'D5c': 10, 'D9': 7, 'D5d': 7, 'D6': 6, 'D1': 5, 'D8': 4}; label_pos_rate=[(0, 34), (1, 16)]; rank(hi/mid/lo)=17/19/14; direct_mid(uncertain)=0; direct_conf(extreme)=50; tool_used=49/50

**Loss items** (n=93): domains={'D6': 19, 'D5c': 11, 'D9': 10, 'D2': 9, 'D4': 9, 'D5d': 9}; label_pos_rate=[(1, 70), (0, 23)]; rank(hi/mid/lo)=30/46/17; direct_mid(uncertain)=0; direct_conf(extreme)=93; tool_used=92/93

**Keywords distinctive in WIN rationales** (word: n_wins n_losses score):

- `size`: wins=11 losses=0 score=+1.00
- `detected`: wins=9 losses=0 score=+1.00
- `structural`: wins=8 losses=0 score=+1.00

**Sample WIN items (tool flipped correctly):**

- `D1_0084` [D1] label=0 direct=0.95→tool=0.05  rank=0.02  used_tool=False
  > The query image is visually consistent with the normal reference images, showing the same speckled pattern without any distinct defects or deviations.
- `D1_0038` [D1] label=0 direct=0.98→tool=0.05  rank=0.26  used_tool=True
  > The query image matches the visual characteristics of the majority of the reference images (black/orange capsule with 'actavis' and '500' text). Any minor differences are consistent with the allowed v
- `D1_0016` [D1] label=0 direct=0.98→tool=0.10  rank=0.06  used_tool=True
  > The query image matches the normal baseline of a three-core cable. The increased brightness on the green conductor falls under the 'lighting shift' and 'slight color variation' allowed by the referenc
- `D1_0064` [D1] label=0 direct=0.98→tool=0.10  rank=0.24  used_tool=True
  > The query image matches the expected color and shape. The absence of the 'actavis' logo is not an anomaly because one of the four reference images also lacks the logo, indicating it is an allowed vari
- `D1_0009` [D1] label=0 direct=0.95→tool=0.10  rank=0.13  used_tool=True
  > The query image matches the normal baseline profile with three colored cores in a white sheath. Any differences fall within allowed variations (lighting, slight color variation). No structural anomali

**Sample LOSS items (tool flipped wrong):**

- `D1_0094` [D1] label=1 direct=0.98→tool=0.00  rank=0.77  used_tool=False
  > The query image is visually consistent with the normal reference images, showing the expected object, colors, and markings without any anomalies.
- `D1_0142` [D1] label=1 direct=0.95→tool=0.10  rank=0.32  used_tool=True
  > The query image displays thick light streaks which fall under the 'texture contrast' and 'grain density variation' allowed in the normal baseline. Since the tool's disconfirm clause indicates that exh
- `D1_0137` [D1] label=1 direct=0.98→tool=0.10  rank=0.72  used_tool=True
  > The query image matches the normal baseline profile (black/orange bipartite capsule) and does not exhibit any disallowed variations. The potential difference in logo visibility is not flagged as an an
- `D1_0179` [D1] label=1 direct=0.95→tool=0.05  rank=0.54  used_tool=True
  > The query image matches the normal baseline profile (metallic cross-shaped component with central hole). Observed differences are limited to rotation and lighting, which are explicitly listed as allow
- `D2_0027` [D2] label=0 direct=0.01→tool=0.95  rank=0.19  used_tool=True
  > The query image displays a different flavor variant (blueberry) with a distinct label color scheme compared to the lime flavor shown in all reference images. Since 'flavor variant' is not listed as an

### tool_component_counter  (net flips -49, wins 56, losses 123)

**Win items** (n=56): domains={'D5c': 9, 'D1': 8, 'D9': 7, 'D6': 6, 'D2': 5, 'D4': 4}; label_pos_rate=[(0, 30), (1, 26)]; rank(hi/mid/lo)=17/21/18; direct_mid(uncertain)=0; direct_conf(extreme)=56; tool_used=33/56

**Loss items** (n=123): domains={'D6': 20, 'D5': 16, 'D2': 13, 'D9': 13, 'D5c': 13, 'D5d': 13}; label_pos_rate=[(1, 68), (0, 55)]; rank(hi/mid/lo)=34/52/37; direct_mid(uncertain)=0; direct_conf(extreme)=123; tool_used=94/123

**Keywords distinctive in WIN rationales** (word: n_wins n_losses score):

- `multiple`: wins=9 losses=0 score=+1.00
- `clear`: wins=9 losses=0 score=+1.00
- `object`: wins=9 losses=0 score=+1.00
- `variation`: wins=8 losses=0 score=+1.00
- `false`: wins=8 losses=0 score=+1.00

**Sample WIN items (tool flipped correctly):**

- `D1_0084` [D1] label=0 direct=0.95→tool=0.05  rank=0.02  used_tool=False
  > The query image exhibits the same speckled texture pattern as the reference images with no visible anomalies or deviations.
- `D1_0038` [D1] label=0 direct=0.98→tool=0.30  rank=0.26  used_tool=True
  > The component counter signal is likely due to the 'actavis' text, which is a normal feature on some capsules but not others. This appears to be a normal variation rather than a defect, so the anomaly 
- `D1_0016` [D1] label=0 direct=0.98→tool=0.10  rank=0.06  used_tool=True
  > The visual difference in conductor brightness is likely due to lighting or oxidation, which falls under normal variance. The tool's detection of multiple blobs is consistent with the disconfirm clause
- `D1_0088` [D1] label=0 direct=0.95→tool=0.15  rank=0.29  used_tool=True
  > The component counter signal is likely a false positive due to normal high-variance regions (solder joints/component edges). Visual inspection shows no obvious defects compared to references, so the s
- `D1_0009` [D1] label=0 direct=0.95→tool=0.40  rank=0.13  used_tool=True
  > While the component counter suggests potential anomaly, the disconfirm clause indicates this could be normal variation in high-variance regions. The visual difference in strand pattern is subtle and c

**Sample LOSS items (tool flipped wrong):**

- `D1_0008` [D1] label=0 direct=0.02→tool=0.95  rank=0.12  used_tool=True
  > The query image displays yellow bristles, whereas all reference images show blue or red bristles. This significant color difference is a clear visual anomaly. The tool's detection of multiple componen
- `D1_0142` [D1] label=1 direct=0.95→tool=0.30  rank=0.32  used_tool=True
  > While the component counter found 4 components, the disconfirm clause indicates these could be normal high-variance regions in wood texture. The light streaks appear to be natural wood grain variation
- `D1_0094` [D1] label=1 direct=0.98→tool=0.00  rank=0.77  used_tool=False
  > The query image matches the reference images in all key features (logo, imprint, color, shape). No anomalies are detected.
- `D2_0133` [D2] label=1 direct=0.98→tool=0.05  rank=0.08  used_tool=False
  > The query image is visually indistinguishable from the normal reference images, showing the same product packaging and contents without any apparent anomalies.
- `D2_0170` [D2] label=1 direct=0.98→tool=0.10  rank=0.13  used_tool=False
  > The query image is a standard front view of the snack package, consistent with the normal reference images showing the same product. No visual defects or anomalies are apparent.

### tool_domain_knowledge  (net flips -60, wins 52, losses 114)

**Win items** (n=52): domains={'D5c': 7, 'D9': 6, 'D5d': 6, 'D1': 5, 'D2': 5, 'D5': 5}; label_pos_rate=[(0, 26), (1, 26)]; rank(hi/mid/lo)=14/22/16; direct_mid(uncertain)=0; direct_conf(extreme)=52; tool_used=27/52

**Loss items** (n=114): domains={'D5': 17, 'D6': 17, 'D4': 13, 'D5c': 13, 'D9': 11, 'D2': 10}; label_pos_rate=[(1, 67), (0, 47)]; rank(hi/mid/lo)=32/54/28; direct_mid(uncertain)=0; direct_conf(extreme)=114; tool_used=76/114

**Keywords distinctive in WIN rationales** (word: n_wins n_losses score):

- `evidence`: wins=7 losses=0 score=+1.00
- `showing`: wins=6 losses=0 score=+1.00
- `standard`: wins=6 losses=0 score=+1.00
- `detected`: wins=6 losses=0 score=+1.00
- `liquid`: wins=6 losses=0 score=+1.00
- `confirms`: wins=6 losses=0 score=+1.00
- `lesions`: wins=6 losses=0 score=+1.00
- `object`: wins=6 losses=0 score=+1.00

**Sample WIN items (tool flipped correctly):**

- `D1_0084` [D1] label=0 direct=0.95→tool=0.05  rank=0.02  used_tool=False
  > The query image is visually consistent with the normal reference images, showing the same speckled texture without any apparent anomalies.
- `D1_0038` [D1] label=0 direct=0.98→tool=0.10  rank=0.26  used_tool=False
  > The query image appears identical to the normal reference images. The capsule has the same black and orange color scheme, the 'actavis' logo is present and correctly oriented, and the '500' imprint is
- `D1_0174` [D1] label=1 direct=0.02→tool=0.95  rank=0.15  used_tool=False
  > The component in the query image has a flat, rectangular body, whereas all reference images show a cylindrical component. This significant difference in component type indicates an anomaly.
- `D1_0009` [D1] label=0 direct=0.95→tool=0.05  rank=0.13  used_tool=True
  > The query image shows a standard three-core cable with correct color coding (brown, blue, green/yellow) and healthy copper strands, consistent with the reference images and domain knowledge. No anomal
- `D1_0064` [D1] label=0 direct=0.98→tool=0.05  rank=0.24  used_tool=True
  > The query image is visually identical to 3 out of 4 reference images, showing the 'actavis' logo on the black half and '500' on the orange half. The tool's claim of a 'standard' swap is contradicted b

**Sample LOSS items (tool flipped wrong):**

- `D1_0008` [D1] label=0 direct=0.02→tool=0.95  rank=0.12  used_tool=True
  > The query image displays yellow and white bristles, whereas all reference images show either blue/white or red/white bristles. The domain knowledge tool confirmed that yellow/white is not a standard c
- `D1_0094` [D1] label=1 direct=0.98→tool=0.05  rank=0.77  used_tool=False
  > The query image appears visually identical to the normal reference images. The capsule has the same black and orange color scheme, the 'actavis' logo and '500' text are in the same position and style,
- `D1_0179` [D1] label=1 direct=0.95→tool=0.05  rank=0.54  used_tool=False
  > The query image appears visually consistent with the normal reference images. The component's shape, texture, lighting, and central hole are all within the expected variation seen in the reference set
- `D2_0056` [D2] label=0 direct=0.01→tool=0.95  rank=0.05  used_tool=False
  > The query image displays a fundamentally different packaging design (stylized/comic style) compared to the normal reference images (standard product packaging with realistic fruit imagery), indicating
- `D2_0087` [D2] label=0 direct=0.01→tool=1.00  rank=0.08  used_tool=False
  > The query image displays the cigarette pack upside down, with inverted text and logo, which is a significant deviation from the normal orientation shown in the reference images.
