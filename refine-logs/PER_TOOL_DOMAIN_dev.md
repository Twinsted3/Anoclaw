# Per-Tool × Per-Domain Sample Analysis — dev n=480

For each tool, the WIN items (tool flipped to correct or improved the score) and LOSS items (tool broke correct or worsened) are listed by domain, with the specific item IDs and rationale snippets.

Sample types:
- `FP_corrected`: Direct said anomaly on a normal; tool brought down
- `FN_corrected`: Direct missed an anomaly; tool brought up
- `TP_lost_to_FN`: Direct correctly flagged anomaly; tool wrongly dismissed
- `TN_lost_to_FP`: Direct correctly said normal; tool wrongly flagged

## tool_component_counter  (56 wins, 123 losses, net flips -49 on n=480)

### D1  (wins 8, losses 7)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 2, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 2, 'other': 4}

**WINS** (item · direct→tool · rank · type · rationale):

- `D1_0114` L=1 direct=0.02→tool=0.95 rank=0.19 **FN_corrected** used_tool=True
  > The query image displays yellow bristles, whereas all reference images show blue or red bristles. This color difference is a definitive anomaly relative to the provided normal class. The tool's detection of 5 components 
- `D1_0084` L=0 direct=0.95→tool=0.05 rank=0.02 **FP_corrected** used_tool=False
  > The query image exhibits the same speckled texture pattern as the reference images with no visible anomalies or deviations.
- `D1_0016` L=0 direct=0.98→tool=0.10 rank=0.06 **FP_corrected** used_tool=True
  > The visual difference in conductor brightness is likely due to lighting or oxidation, which falls under normal variance. The tool's detection of multiple blobs is consistent with the disconfirm clause for high-variance r
- `D1_0159` L=1 direct=0.02→tool=0.85 rank=0.35 **FN_corrected** used_tool=True
  > The query image contains a distinct, larger reddish-brown defect below the 'FF' marking, which is not present in the reference images that only show smaller, scattered specks. The tool's detection of a localized defect a
- `D1_0088` L=0 direct=0.95→tool=0.15 rank=0.29 **FP_corrected** used_tool=True
  > The component counter signal is likely a false positive due to normal high-variance regions (solder joints/component edges). Visual inspection shows no obvious defects compared to references, so the sample is likely norm
- `D1_0038` L=0 direct=0.98→tool=0.30 rank=0.26 **FP_corrected** used_tool=True
  > The component counter signal is likely due to the 'actavis' text, which is a normal feature on some capsules but not others. This appears to be a normal variation rather than a defect, so the anomaly score is low.
- `D1_0009` L=0 direct=0.95→tool=0.40 rank=0.13 **FP_corrected** used_tool=True
  > While the component counter suggests potential anomaly, the disconfirm clause indicates this could be normal variation in high-variance regions. The visual difference in strand pattern is subtle and could be within norma
- `D1_0156` L=1 direct=0.02→tool=0.15 rank=0.47 **other** used_tool=True
  > The detected hotspots correspond to the natural speckling present on all pills in the dataset, including the normal references. Since the pattern is consistent with the normal class, the signal is likely a false positive

**LOSSES**:

- `D1_0094` L=1 direct=0.98→tool=0.00 rank=0.77 **TP_lost_to_FN** used_tool=False
  > The query image matches the reference images in all key features (logo, imprint, color, shape). No anomalies are detected.
- `D1_0008` L=0 direct=0.02→tool=0.95 rank=0.12 **TN_lost_to_FP** used_tool=True
  > The query image displays yellow bristles, whereas all reference images show blue or red bristles. This significant color difference is a clear visual anomaly. The tool's detection of multiple components likely correspond
- `D1_0142` L=1 direct=0.95→tool=0.30 rank=0.32 **TP_lost_to_FN** used_tool=True
  > While the component counter found 4 components, the disconfirm clause indicates these could be normal high-variance regions in wood texture. The light streaks appear to be natural wood grain variations rather than manufa
- `D1_0111` L=1 direct=0.98→tool=0.75 rank=0.77 **other** used_tool=True
  > The query image shows a distinct dark spot that differs from the uniform woven pattern in the reference images. The component counter confirmed localized hotspots, and visual inspection suggests this is a genuine defect 
- `D1_0179` L=1 direct=0.95→tool=0.75 rank=0.54 **other** used_tool=True
  > The query image shows a small defect on the right protrusion that is not present in the reference images. The tool's detection of 2 connected components supports this observation, and the defect appears to be a true anom
- `D1_0044` L=0 direct=0.01→tool=0.20 rank=0.37 **other** used_tool=True
  > While the component counter detected some hotspots, the visual similarity between query and reference images is strong, and the disconfirm clause suggests these could be normal high-variance regions. The slight score inc
- `D1_0023` L=0 direct=0.02→tool=0.15 rank=0.09 **other** used_tool=True
  > The query image shows normal color variation (yellow/white vs blue/white/red/white in references) with identical bristle structure and arrangement. The component counter signal is likely due to normal color differences r

### D10  (wins 3, losses 4)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 1}
Loss sample-types: {'TP_lost_to_FN': 2, 'other': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D10_0172` L=1 direct=0.01→tool=0.95 rank=0.21 **FN_corrected** used_tool=False
  > The query image displays the sensor module upside down compared to the reference images, with the pins pointing downwards and the text inverted, which is a clear anomaly.
- `D10_0076` L=0 direct=0.98→tool=0.05 rank=0.12 **FP_corrected** used_tool=False
  > The query image matches the normal reference images in component layout, labeling, and overall appearance. No anomalies are detected.
- `D10_0002` L=0 direct=0.95→tool=0.05 rank=0.07 **FP_corrected** used_tool=False
  > The query image matches the pattern of the normal reference images with four intact candles in a standard arrangement. No anomalies are detected.

**LOSSES**:

- `D10_0097` L=1 direct=0.99→tool=0.05 rank=0.34 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard HC-SR04 ultrasonic sensor module with all expected components intact and no visible anomalies.
- `D10_0139` L=1 direct=0.98→tool=0.05 rank=0.20 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing no apparent anomalies in the objects' shape, color, or arrangement.
- `D10_0136` L=1 direct=0.98→tool=0.75 rank=0.23 **other** used_tool=True
  > The query image shows visible white residue/contamination on the left side of the PCB near component U3 and capacitors, which is not present in any of the reference images. This is a clear visual anomaly indicating a def
- `D10_0069` L=0 direct=0.02→tool=0.20 rank=0.27 **other** used_tool=True
  > The component counter signal is likely due to the naturally textured surface rather than a true defect, as the query image appears visually consistent with the normal reference images.

### D2  (wins 5, losses 13)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2, 'other': 2}
Loss sample-types: {'TP_lost_to_FN': 7, 'TN_lost_to_FP': 2, 'other': 4}

**WINS** (item · direct→tool · rank · type · rationale):

- `D2_0095` L=1 direct=0.02→tool=1.00 rank=0.86 **FN_corrected** used_tool=False
  > The query image depicts a filled bottle, which is inconsistent with the empty/clear bottles shown in the reference images, confirming an anomaly.
- `D2_0092` L=1 direct=0.01→tool=0.95 rank=0.63 **FN_corrected** used_tool=False
  > The query image contains an attached plastic straw wrapper on the front of the carton, which is absent in all normal reference images, indicating a clear anomaly.
- `D2_0037` L=0 direct=0.98→tool=0.10 rank=0.19 **FP_corrected** used_tool=True
  > The detected components likely correspond to the normal high-contrast text and barcode on the back of the package, which differs from the front shown in references. This is a normal variation in package orientation, not 
- `D2_0137` L=1 direct=0.02→tool=0.20 rank=0.68 **other** used_tool=True
  > The tool signal is likely a false positive due to the high-variance diagonal design pattern. The query image matches the design characteristics of the reference images, indicating it is normal.
- `D2_0145` L=1 direct=0.02→tool=0.15 rank=0.71 **other** used_tool=True
  > After visual inspection, the query image appears consistent with the reference images. The detected components likely correspond to normal design elements (text, logo, dotted pattern) rather than actual defects. The slig

**LOSSES**:

- `D2_0027` L=0 direct=0.01→tool=0.95 rank=0.19 **TN_lost_to_FP** used_tool=True
  > The query image displays a blueberry-flavored bottle, whereas all reference images show a lime-flavored bottle. This difference in product variant (flavor graphics) constitutes a clear anomaly, despite the tool's signal 
- `D2_0133` L=1 direct=0.98→tool=0.05 rank=0.08 **TP_lost_to_FN** used_tool=False
  > The query image is visually indistinguishable from the normal reference images, showing the same product packaging and contents without any apparent anomalies.
- `D2_0080` L=0 direct=0.02→tool=0.95 rank=0.02 **TN_lost_to_FP** used_tool=False
  > The query image shows the back of the product package, which is visually inconsistent with the reference images that all show the front. This constitutes a clear anomaly relative to the provided normal examples.
- `D2_0167` L=1 direct=0.98→tool=0.05 rank=0.18 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard bottle of juice with no apparent anomalies.
- `D2_0097` L=1 direct=0.98→tool=0.05 rank=0.73 **TP_lost_to_FN** used_tool=False
  > The query image displays a normal, undamaged breakfast milk carton with clear labeling, matching the expected appearance of the product seen in the reference images.
- `D2_0170` L=1 direct=0.98→tool=0.10 rank=0.13 **TP_lost_to_FN** used_tool=False
  > The query image is a standard front view of the snack package, consistent with the normal reference images showing the same product. No visual defects or anomalies are apparent.
- `D2_0153` L=1 direct=0.95→tool=0.10 rank=0.74 **TP_lost_to_FN** used_tool=True
  > The component counter signal is likely due to the high-variance text and graphics on the carton, as warned by the disconfirm clause. Visual inspection confirms the product appears undamaged and consistent with normal ref
- `D2_0107` L=1 direct=0.95→tool=0.10 rank=0.32 **TP_lost_to_FN** used_tool=True
  > The tool signal is likely a false positive caused by normal high-variance regions (plastic wrap reflections), as warned in the disconfirm clause. Visual inspection confirms the product matches the reference images with n
  ... and 5 more losses.

### D4  (wins 4, losses 10)

Win sample-types: {'FN_corrected': 2, 'other': 2}
Loss sample-types: {'TN_lost_to_FP': 5, 'TP_lost_to_FN': 4, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D4_0105` L=1 direct=0.05→tool=0.95 rank=0.06 **FN_corrected** used_tool=True
  > The query image exhibits a large, dark shadow or discoloration covering the lower half, which is absent in the uniform reference images. The component counter tool supports this by identifying multiple active patches and
- `D4_0176` L=1 direct=0.05→tool=0.85 rank=0.82 **FN_corrected** used_tool=True
  > The query image displays large, distinct rocks and debris at the bottom, creating a significantly different texture and structure compared to the uniform, fine-grained surfaces in the reference images. The tool's detecti
- `D4_0110` L=1 direct=0.05→tool=0.30 rank=0.70 **other** used_tool=True
  > The tool indicates multiple small hotspots, but the disconfirm clause suggests these could be in normal high-variance regions. Visually, the dark spot in the query image is small and could be a normal texture variation s
- `D4_0121` L=1 direct=0.05→tool=0.20 rank=0.47 **other** used_tool=True
  > The detected components likely correspond to normal texture variations rather than true defects, as the query image's appearance is consistent with the reference images showing similar small dark spots and texture patter

**LOSSES**:

- `D4_0086` L=0 direct=0.05→tool=0.95 rank=0.76 **TN_lost_to_FP** used_tool=False
  > The query image contains a prominent vertical linear defect that is absent in all normal reference images, indicating a clear anomaly.
- `D4_0106` L=1 direct=0.95→tool=0.10 rank=0.49 **TP_lost_to_FN** used_tool=False
  > The query image appears consistent with the normal reference images, showing a standard textured surface without any distinct defects or anomalies.
- `D4_0155` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The tool detected 5 components, but the disconfirm clause suggests this could be normal high-variance texture. Visual inspection confirms the pits and spots in the query image are consistent with the natural variations s
- `D4_0026` L=0 direct=0.05→tool=0.85 rank=0.28 **TN_lost_to_FP** used_tool=True
  > The query image contains a distinct dark spot at the bottom center that is not present in the reference images. The component counter detected 2 connected components, supporting the presence of a localized defect rather 
- `D4_0037` L=0 direct=0.05→tool=0.80 rank=0.18 **TN_lost_to_FP** used_tool=True
  > The query image is visually uniform and lacks the textured patterns seen in the reference images. While the tool detected some components, the disconfirm clause suggests these could be false positives in high-variance re
- `D4_0126` L=1 direct=0.95→tool=0.20 rank=0.63 **TP_lost_to_FN** used_tool=True
  > The query image shows texture and spot patterns consistent with the normal reference images. The single connected component detected is likely a natural variation rather than a true defect, as the spots appear similar in
- `D4_0028` L=0 direct=0.05→tool=0.70 rank=0.29 **TN_lost_to_FP** used_tool=True
  > The query image displays a few distinct, elongated dark marks, differing from the numerous small specks in the reference images. The tool confirmed 3 connected components, supporting the visual evidence of a localized an
- `D4_0016` L=0 direct=0.05→tool=0.70 rank=0.28 **TN_lost_to_FP** used_tool=True
  > The query image contains distinct, elongated dark marks that are not present in the normal reference images, which only show small, scattered specks. The component counter supports this by identifying multiple connected 
  ... and 2 more losses.

### D5  (wins 4, losses 16)

Win sample-types: {'FN_corrected': 2, 'other': 2}
Loss sample-types: {'TN_lost_to_FP': 5, 'TP_lost_to_FN': 8, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5_0119` L=1 direct=0.05→tool=0.85 rank=0.32 **FN_corrected** used_tool=True
  > The component counter indicates multiple disconnected hotspots (diffuse anomaly), and visual inspection confirms irregular borders and color variegation distinct from the normal reference images.
- `D5_0179` L=1 direct=0.05→tool=0.85 rank=0.27 **FN_corrected** used_tool=True
  > The query lesion exhibits significant color variegation (black center, brown periphery) and structural complexity (5 components) that deviates from the uniform appearance of the normal reference images, indicating an ano
- `D5_0125` L=1 direct=0.05→tool=0.20 rank=0.19 **other** used_tool=True
  > Although the component counter found 4 components, the visual appearance of the query lesion is consistent with the normal reference images (specifically the last one), showing a uniform color and shape. The disconfirm c
- `D5_0136` L=1 direct=0.08→tool=0.20 rank=0.65 **other** used_tool=True
  > The tool indicated 3 components, which could suggest a diffuse anomaly, but the disconfirm clause notes this can occur in normal high-variance regions. Visually, the query lesion is similar in appearance to the reference

**LOSSES**:

- `D5_0032` L=0 direct=0.05→tool=0.90 rank=0.87 **TN_lost_to_FP** used_tool=True
  > The query image displays a pink, homogeneous lesion, which is visually distinct from the brown, pigmented lesions in the reference set. While the component counter found 3 blobs, the disconfirm clause suggests this could
- `D5_0117` L=1 direct=0.95→tool=0.10 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The tool indicated 1 connected component, but the disconfirm clause warns that this can occur in normal high-variance regions. Visually, the lesion is a single, uniform nevus similar to the reference images, suggesting t
- `D5_0176` L=1 direct=0.95→tool=0.10 rank=0.46 **TP_lost_to_FN** used_tool=False
  > The query image shows a benign-appearing globular nevus with features consistent with the provided normal reference images. There are no obvious signs of asymmetry, irregular borders, or color variegation that would sugg
- `D5_0112` L=1 direct=0.95→tool=0.10 rank=0.75 **TP_lost_to_FN** used_tool=True
  > Although the tool detected multiple components, the disconfirm clause indicates this can occur in normal high-variance regions. Visual inspection confirms the lesion's appearance is consistent with the normal reference i
- `D5_0115` L=1 direct=0.95→tool=0.10 rank=0.57 **TP_lost_to_FN** used_tool=False
  > The query image displays a lesion with characteristics consistent with the normal reference images, including symmetry and uniform pigmentation. No obvious anomalies are detected visually.
- `D5_0167` L=1 direct=0.95→tool=0.10 rank=0.48 **TP_lost_to_FN** used_tool=False
  > The query image appears visually consistent with the normal reference images, showing no obvious signs of anomaly such as irregular borders, asymmetry, or unusual color variations.
- `D5_0158` L=1 direct=0.95→tool=0.10 rank=0.35 **TP_lost_to_FN** used_tool=True
  > Although the component counter found 3 blobs, the disconfirm clause notes this can occur in normal high-variance regions. Visual inspection confirms the lesion is a uniform, benign-looking nevus similar to the reference 
- `D5_0066` L=0 direct=0.05→tool=0.85 rank=0.83 **TN_lost_to_FP** used_tool=True
  > The component counter indicates multiple hotspots (4 components), and visual inspection confirms irregular borders and color variegation in the query lesion compared to the more uniform reference images, strongly suggest
  ... and 8 more losses.

### D5b  (wins 4, losses 7)

Win sample-types: {'FP_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5b_0045` L=0 direct=0.98→tool=0.10 rank=0.31 **FP_corrected** used_tool=False
  > The query image appears normal with no visible anomalies compared to the reference images. The ventricular system and cortical structures are intact and symmetrical.
- `D5b_0067` L=0 direct=0.98→tool=0.10 rank=0.53 **FP_corrected** used_tool=True
  > The tool's detection of multiple components is likely due to the high variance of normal brain anatomy (gyri/sulci) rather than a true defect, as cautioned in the disconfirm clause. Visual inspection confirms no obvious 
- `D5b_0031` L=0 direct=0.98→tool=0.10 rank=0.51 **FP_corrected** used_tool=True
  > The tool's signal is likely a false positive as per the disconfirm clause, and the image visually matches normal brain MRI scans.
- `D5b_0058` L=0 direct=0.95→tool=0.10 rank=0.52 **FP_corrected** used_tool=False
  > The query image displays standard brain anatomy consistent with the normal reference images, showing no clear signs of anomaly such as tumors, hemorrhages, or significant structural deformities.

**LOSSES**:

- `D5b_0066` L=0 direct=0.02→tool=0.95 rank=0.55 **TN_lost_to_FP** used_tool=True
  > The query image exhibits a distinct horizontal split dividing the brain structure, which is absent in all normal reference images. This represents a significant structural anomaly or artifact, warranting a high anomaly s
- `D5b_0149` L=1 direct=0.98→tool=0.10 rank=0.72 **TP_lost_to_FN** used_tool=True
  > Although the tool flagged 2 components, the disconfirm clause notes this can occur in normal high-variance regions. Visual inspection shows no obvious defects compared to references, so the signal is likely a false posit
- `D5b_0122` L=1 direct=0.98→tool=0.10 rank=0.60 **TP_lost_to_FN** used_tool=False
  > The query image appears normal with no visible anomalies when compared to the reference images. The brain structures are intact and there are no unusual patterns or regions that suggest an anomaly.
- `D5b_0160` L=1 direct=0.95→tool=0.10 rank=0.44 **TP_lost_to_FN** used_tool=False
  > The query image displays a typical brain MRI slice with normal ventricular anatomy and no obvious focal abnormalities compared to the general appearance of the reference images, suggesting it is likely normal.
- `D5b_0069` L=0 direct=0.02→tool=0.85 rank=0.53 **TN_lost_to_FP** used_tool=True
  > The query image displays a significantly enlarged and abnormally shaped central ventricular system compared to the reference images, suggesting a potential pathological condition like hydrocephalus or atrophy. While the 
- `D5b_0068` L=0 direct=0.05→tool=0.85 rank=0.86 **TN_lost_to_FP** used_tool=True
  > The query image exhibits significant blurring and loss of detail compared to the sharp reference images, resulting in fragmented structural components (5 blobs) detected by the tool. This visual degradation and structura
- `D5b_0059` L=0 direct=0.02→tool=0.70 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image displays scattered hyperintense spots and less defined anatomical structures compared to the clear ventricles in the reference images. While the component counter flagged 5 hotspots, the visual evidence o

### D5c  (wins 9, losses 13)

Win sample-types: {'FP_corrected': 4, 'FN_corrected': 3, 'other': 2}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 8, 'other': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5c_0131` L=1 direct=0.02→tool=0.95 rank=0.90 **FN_corrected** used_tool=True
  > The query image displays a small, simple oval object, which is fundamentally different in shape and size from the large, kidney-shaped structures seen in all reference images. This gross morphological difference indicate
- `D5c_0165` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=True
  > The query image contains a clear dark hole (a separate connected component) not present in the normal reference images, which the tool confirmed by detecting multiple components. This structural difference is a definitiv
- `D5c_0035` L=0 direct=0.95→tool=0.05 rank=0.81 **FP_corrected** used_tool=False
  > The query image displays a single, coherent object with texture consistent with the majority of the normal reference images. There are no obvious visual anomalies such as missing parts, extra objects, or significant text
- `D5c_0174` L=1 direct=0.05→tool=0.95 rank=0.97 **FN_corrected** used_tool=False
  > The query image contains a single, small, isolated object that is drastically different in size and morphology compared to the larger, complex organ-like structures seen in all reference images. This strong visual discre
- `D5c_0038` L=0 direct=0.95→tool=0.10 rank=0.89 **FP_corrected** used_tool=False
  > The query image displays a single object with texture consistent with the normal reference images. There are no obvious signs of multiple disconnected components or other anomalies that the component counter tool would d
- `D5c_0003` L=0 direct=0.95→tool=0.10 rank=0.97 **FP_corrected** used_tool=False
  > The query image displays a single connected component, similar in nature to the objects in the reference images, although smaller. The available tool is not applicable as it requires at least 3 hotspot patches, and the v
- `D5c_0070` L=0 direct=0.95→tool=0.10 rank=0.91 **FP_corrected** used_tool=True
  > Although the component counter found 2 components, the visual evidence shows a single coherent object consistent with the normal reference images. The disconfirm clause suggests this signal may be due to normal high-vari
- `D5c_0100` L=1 direct=0.05→tool=0.20 rank=0.79 **other** used_tool=True
  > Although the component counter found 3 components, the visual evidence shows a single coherent object similar to the reference images. The disconfirm clause suggests this signal could be due to normal high-variance regio
  ... and 1 more wins.

**LOSSES**:

- `D5c_0004` L=0 direct=0.02→tool=0.98 rank=0.94 **TN_lost_to_FP** used_tool=False
  > The query image contains a tiny, isolated speck, which is drastically different from the large, complex shapes seen in all normal reference images. This indicates a severe anomaly, likely a missing object or a detection 
- `D5c_0042` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=True
  > The query image exhibits distinct internal voids (holes) not present in the solid reference images. The component counter confirmed multiple components (3), supporting the visual evidence of a structural defect rather th
- `D5c_0061` L=0 direct=0.02→tool=0.95 rank=0.84 **TN_lost_to_FP** used_tool=True
  > The query image exhibits 4 distinct connected components, indicating a fragmented object, whereas all reference images show single, contiguous objects. This topological difference is a clear sign of an anomaly.
- `D5c_0102` L=1 direct=0.95→tool=0.10 rank=0.91 **TP_lost_to_FN** used_tool=True
  > Although the tool detected 3 components, the visual evidence shows a single coherent object consistent with the normal references. The disconfirm clause indicates that spread hotspots in high-variance regions do not nece
- `D5c_0107` L=1 direct=0.95→tool=0.10 rank=0.99 **TP_lost_to_FN** used_tool=True
  > Although the tool detected 5 components, the visual evidence shows a single coherent shape consistent with most reference images. The tool's disconfirm clause warns that spread hotspots in high-variance regions do not ne
- `D5c_0145` L=1 direct=0.95→tool=0.10 rank=0.91 **TP_lost_to_FN** used_tool=True
  > Although the tool detected 3 components, the query image visually resembles the compact, single-object reference images (3 and 5). The disconfirm clause suggests the signal could be due to normal high-variance regions, a
- `D5c_0159` L=1 direct=0.95→tool=0.10 rank=0.95 **TP_lost_to_FN** used_tool=False
  > The query image displays a single, continuous object with texture consistent with the normal reference images. No clear anomalies such as fragmentation or foreign objects are visible.
- `D5c_0170` L=1 direct=0.95→tool=0.10 rank=0.97 **TP_lost_to_FN** used_tool=False
  > The query image displays a small, single, textured object similar to the third and fourth reference images. The larger, more complex objects in the second and fifth reference images appear to be the anomalies. Therefore,
  ... and 5 more losses.

### D5d  (wins 3, losses 13)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 6, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5d_0135` L=1 direct=0.02→tool=0.95 rank=0.48 **FN_corrected** used_tool=True
  > The query image contains a distinct, dark, raised lesion (polyp) in the center, which is a clear structural anomaly compared to the smooth, healthy mucosa in the reference images. The tool's detection of connected hotspo
- `D5d_0173` L=1 direct=0.02→tool=0.95 rank=0.57 **FN_corrected** used_tool=True
  > The query image clearly shows a dark, solid object in the lumen, which is absent in all normal reference images. This is a strong visual indicator of an anomaly (likely a foreign body or clot), overriding the tool's pote
- `D5d_0045` L=0 direct=0.92→tool=0.05 rank=0.40 **FP_corrected** used_tool=False
  > The query image shows healthy gastric mucosa with normal folds and no visible anomalies, matching the characteristics of the provided normal reference images.

**LOSSES**:

- `D5d_0069` L=0 direct=0.02→tool=0.95 rank=0.36 **TN_lost_to_FP** used_tool=True
  > The query image contains a prominent, raised polypoid lesion, which is a clear structural anomaly not present in the normal reference images. The component counter tool supports this by identifying a localized defect.
- `D5d_0166` L=1 direct=0.98→tool=0.05 rank=0.47 **TP_lost_to_FN** used_tool=True
  > The image displays a normal endoscopic view of the colon with a scope tip. The detected components are consistent with normal anatomical features and lighting reflections, not pathological defects, as confirmed by the to
- `D5d_0010` L=0 direct=0.05→tool=0.95 rank=0.40 **TN_lost_to_FP** used_tool=True
  > The query image contains a distinct dark circular lesion not present in the normal reference images, indicating a localized anomaly. The tool's detection of 5 components supports the presence of an anomaly, and the visua
- `D5d_0129` L=1 direct=0.98→tool=0.10 rank=0.31 **TP_lost_to_FN** used_tool=True
  > The yellow discoloration appears to be bile staining, a common and normal finding in endoscopic images, rather than a pathological defect. The tool's signal is likely a false positive triggered by the color contrast in a
- `D5d_0154` L=1 direct=0.98→tool=0.10 rank=0.38 **TP_lost_to_FN** used_tool=False
  > The query image displays normal colonic mucosa with typical endoscopic artifacts (text, green box) and no visible pathological anomalies like polyps or ulcers, consistent with the normal reference images.
- `D5d_0146` L=1 direct=0.98→tool=0.10 rank=0.38 **TP_lost_to_FN** used_tool=True
  > The tool's signal of multiple small blobs is likely due to normal anatomical folds and residue (bile/food) in the pylorus, which are high-variance regions. The disconfirm clause explicitly states this can happen in norma
- `D5d_0112` L=1 direct=0.95→tool=0.10 rank=0.33 **TP_lost_to_FN** used_tool=True
  > The single connected component detected by the tool is likely due to normal high-variance regions (text, green box, reflections) rather than a true defect, as suggested by the disconfirm clause. Visual inspection confirm
- `D5d_0040` L=0 direct=0.02→tool=0.85 rank=0.21 **TN_lost_to_FP** used_tool=True
  > The query image contains an endoscope tip and a yellowish region (likely bile/stool), which are distinct from the clean, instrument-free mucosal surfaces in the reference images. The component counter's detection of mult
  ... and 5 more losses.

### D6  (wins 6, losses 20)

Win sample-types: {'FP_corrected': 6}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 11, 'other': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D6_0039` L=0 direct=0.95→tool=0.05 rank=0.85 **FP_corrected** used_tool=False
  > The query image displays typical features of an agricultural landscape (field, road, small building) consistent with the normal reference images. No distinct anomalies are visible.
- `D6_0000` L=0 direct=0.95→tool=0.10 rank=0.82 **FP_corrected** used_tool=False
  > The query image displays a standard agricultural landscape consistent with the normal reference images, showing fields, roads, and buildings without any detectable anomalies.
- `D6_0064` L=0 direct=0.95→tool=0.10 rank=0.39 **FP_corrected** used_tool=True
  > The detected components correspond to the distinct commercial/industrial area in the upper right, which is a high-variance but structurally consistent part of the scene, not a defect. The disconfirm clause indicates this
- `D6_0017` L=0 direct=0.95→tool=0.15 rank=0.75 **FP_corrected** used_tool=True
  > The tool signal of 5 components is likely a false positive caused by the high natural variance in the aerial scene (houses, trees, parking lots), as warned by the disconfirm clause. No obvious structural defect is visibl
- `D6_0063` L=0 direct=0.98→tool=0.20 rank=0.60 **FP_corrected** used_tool=True
  > The tool detected multiple small connected components, but the disconfirm clause suggests this could be due to normal high-variance regions. Visual inspection shows no clear defects, and differences appear to be within n
- `D6_0015` L=0 direct=0.98→tool=0.30 rank=0.62 **FP_corrected** used_tool=True
  > While the tool detected 5 components, the disconfirm clause suggests this could be normal variation in high-variance terrain. Visual inspection shows the query image is consistent with the reference images in terms of la

**LOSSES**:

- `D6_0018` L=0 direct=0.02→tool=0.95 rank=0.55 **TN_lost_to_FP** used_tool=True
  > The query image contains a large, rectangular cleared patch of land that is not present in the normal reference images. This represents a significant structural change (deforestation/clearing) compared to the continuous 
- `D6_0027` L=0 direct=0.02→tool=0.95 rank=0.57 **TN_lost_to_FP** used_tool=True
  > The query image contains a distinct bright green pond in the upper left, which is absent in the normal reference images. Although the component counter flagged multiple hotspots, the interpretation warns of potential fal
- `D6_0117` L=1 direct=0.99→tool=0.10 rank=0.78 **TP_lost_to_FN** used_tool=False
  > The query image depicts a rural scene similar to parts of the reference images, with no obvious anomalies detected.
- `D6_0111` L=1 direct=0.98→tool=0.10 rank=0.66 **TP_lost_to_FN** used_tool=False
  > The query image shows a similar rural landscape with trees, roads, and buildings as the reference images. No obvious anomalies are visible in the overall structure or layout. The slight differences in building positions 
- `D6_0110` L=1 direct=0.98→tool=0.10 rank=0.36 **TP_lost_to_FN** used_tool=True
  > Although the tool detected 5 components, the disconfirm clause suggests this could be due to normal high-variance regions. Visual inspection confirms the query image is structurally identical to the normal references, sh
- `D6_0148` L=1 direct=0.98→tool=0.10 rank=0.66 **TP_lost_to_FN** used_tool=False
  > Visual inspection shows no clear anomalies; the scene appears consistent with normal aerial imagery variations seen in reference images.
- `D6_0047` L=0 direct=0.02→tool=0.85 rank=0.86 **TN_lost_to_FP** used_tool=True
  > The query image exhibits a distinct color difference between the upper and lower field sections, unlike the uniform reference images. The tool confirmed multiple hotspot components, and despite the disconfirm clause abou
- `D6_0130` L=1 direct=0.98→tool=0.15 rank=0.54 **TP_lost_to_FN** used_tool=True
  > The component counter signal is likely a false positive caused by the high-texture, high-variance nature of the dirt paths and vegetation, which matches the normal reference images. No distinct structural defect is visib
  ... and 12 more losses.

### D7  (wins 2, losses 2)

Win sample-types: {'FN_corrected': 1, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 1, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D7_0135` L=1 direct=0.02→tool=0.95 rank=0.97 **FN_corrected** used_tool=True
  > The query image depicts a horse-drawn carriage in a park, which is semantically distinct from all reference images showing car traffic on streets. The tool's detection of multiple anomaly components supports this, and th
- `D7_0022` L=0 direct=0.95→tool=0.70 rank=0.21 **other** used_tool=True
  > The query image contains a prominent orange construction barrier not present in any of the normal reference images. While the component counter tool flagged potential anomalies, its disconfirm clause suggests caution for

**LOSSES**:

- `D7_0055` L=0 direct=0.02→tool=0.65 rank=0.61 **TN_lost_to_FP** used_tool=True
  > The presence of a pedestrian crossing the road at night is a notable event that differs from the other driving scenes, suggesting a potential anomaly. The tool's signal of multiple small blobs supports this, but the disc
- `D7_0086` L=0 direct=0.02→tool=0.15 rank=0.67 **other** used_tool=True
  > The query image depicts a normal night-time highway scene. The tool's signal of 5 components is likely due to the high variance in lighting conditions (streetlights, headlights) rather than a true structural defect, as c

### D8  (wins 1, losses 5)

Win sample-types: {'FP_corrected': 1}
Loss sample-types: {'TP_lost_to_FN': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D8_0072` L=0 direct=0.95→tool=0.10 rank=0.50 **FP_corrected** used_tool=False
  > The query image appears visually consistent with the normal reference images, showing typical pedestrian activity in a public space without any discernible anomalies.

**LOSSES**:

- `D8_0126` L=1 direct=0.95→tool=0.05 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The tool is not applicable due to lack of hotspots, and the visual content (a person walking) appears normal and consistent with the reference images.
- `D8_0138` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The tool was not applicable. Visual inspection shows the scene is consistent with the reference images, depicting normal pedestrian activity in the same location. The debris on the ground is minor and does not appear to 
- `D8_0133` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The component counter tool was not applicable due to a lack of detected hotspots. The interpretation advises that ignoring this signal suggests the image is normal. Visually, the scene depicts a standard public area with
- `D8_0179` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The query image depicts a typical scene of people moving through a station or building entrance, similar to the normal reference images. No distinct anomalies are visible.
- `D8_0119` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The component counter tool was not applicable (0 patches). The interpretation suggests the query is likely normal in this case. Visually, the scene shows normal human activity in a public space without obvious anomalies.

### D9  (wins 7, losses 13)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 6, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D9_0121` L=1 direct=0.01→tool=1.00 rank=0.58 **FN_corrected** used_tool=False
  > The query image has a cherry label and red liquid, whereas all reference images have banana labels and light-colored liquid, indicating a clear anomaly.
- `D9_0168` L=1 direct=0.01→tool=1.00 rank=0.73 **FN_corrected** used_tool=False
  > The query image displays a bottle with red liquid and a cherry label, whereas all reference images show bottles with light-colored liquid and a banana label. This significant deviation in both content and label indicates
- `D9_0057` L=0 direct=0.99→tool=0.05 rank=0.35 **FP_corrected** used_tool=False
  > The query image is visually consistent with the provided normal reference images, showing a standard patch cable on a mesh background with no apparent anomalies.
- `D9_0078` L=0 direct=0.99→tool=0.05 rank=0.11 **FP_corrected** used_tool=False
  > The query image matches the pattern of the normal reference images featuring a single jumper wire. There are no visible defects or anomalies.
- `D9_0039` L=0 direct=0.98→tool=0.05 rank=0.05 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing the same types of food items in a similar container. The minor differences in item placement are natural variations and do not indicate an 
- `D9_0022` L=0 direct=0.99→tool=0.10 rank=0.28 **FP_corrected** used_tool=False
  > The query image matches the pattern of the reference images: a cable connecting terminal blocks on a mesh background. The only differences are the cable color and the number of terminal blocks, which are present in the r
- `D9_0079` L=0 direct=0.98→tool=0.10 rank=0.16 **FP_corrected** used_tool=False
  > The query image contains the same set of hardware components (two bolts, two nuts, two washers) as the normal reference images. The variation in arrangement is consistent with the normal examples, indicating no anomaly.

**LOSSES**:

- `D9_0047` L=0 direct=0.02→tool=1.00 rank=0.13 **TN_lost_to_FP** used_tool=False
  > The query image displays a cherry-labeled bottle with dark liquid, whereas all normal references show banana-labeled bottles with light liquid. This distinct difference in label and content color confirms the query is an
- `D9_0032` L=0 direct=0.02→tool=1.00 rank=0.07 **TN_lost_to_FP** used_tool=False
  > The query image displays a red liquid with a cherry label, whereas all reference images show a white liquid with a banana label, indicating a definite anomaly.
- `D9_0100` L=1 direct=0.99→tool=0.05 rank=0.41 **TP_lost_to_FN** used_tool=False
  > The query image depicts a single yellow jumper wire, which matches the pattern seen in the normal reference images (specifically images 2 and 4). There are no visible defects, missing parts, or unexpected objects. The sl
- `D9_0176` L=1 direct=0.99→tool=0.05 rank=0.31 **TP_lost_to_FN** used_tool=True
  > The query image visually matches the normal reference images showing a single yellow jumper wire. The tool's signal of 1 component is explained by the disconfirm clause as likely being the normal wire/connector features 
- `D9_0041` L=0 direct=0.02→tool=0.95 rank=0.79 **TN_lost_to_FP** used_tool=False
  > The query image displays a red cherry juice bottle, whereas all reference images show light-colored banana or orange juice bottles. This represents a significant deviation in both liquid color and label imagery, indicati
- `D9_0065` L=0 direct=0.02→tool=0.95 rank=0.15 **TN_lost_to_FP** used_tool=True
  > The component counter detected 5 items, while the normal reference images and visual count of the query show 6 items (2 bolts, 2 nuts, 2 washers). The missing component indicates an anomaly.
- `D9_0128` L=1 direct=0.99→tool=0.10 rank=0.24 **TP_lost_to_FN** used_tool=False
  > The query image displays a standard single-wire connection between terminal blocks, which matches the pattern seen in the normal reference images. No obvious anomalies are present.
- `D9_0129` L=1 direct=0.98→tool=0.10 rank=0.04 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard arrangement of fruit and granola in a lunchbox. No obvious anomalies are detected.
  ... and 5 more losses.

---

## tool_domain_knowledge  (52 wins, 114 losses, net flips -60 on n=480)

### D1  (wins 5, losses 3)

Win sample-types: {'FP_corrected': 4, 'FN_corrected': 1}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D1_0174` L=1 direct=0.02→tool=0.95 rank=0.15 **FN_corrected** used_tool=False
  > The component in the query image has a flat, rectangular body, whereas all reference images show a cylindrical component. This significant difference in component type indicates an anomaly.
- `D1_0064` L=0 direct=0.98→tool=0.05 rank=0.24 **FP_corrected** used_tool=True
  > The query image is visually identical to 3 out of 4 reference images, showing the 'actavis' logo on the black half and '500' on the orange half. The tool's claim of a 'standard' swap is contradicted by the provided refer
- `D1_0084` L=0 direct=0.95→tool=0.05 rank=0.02 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing the same speckled texture without any apparent anomalies.
- `D1_0009` L=0 direct=0.95→tool=0.05 rank=0.13 **FP_corrected** used_tool=True
  > The query image shows a standard three-core cable with correct color coding (brown, blue, green/yellow) and healthy copper strands, consistent with the reference images and domain knowledge. No anomalies are detected.
- `D1_0038` L=0 direct=0.98→tool=0.10 rank=0.26 **FP_corrected** used_tool=False
  > The query image appears identical to the normal reference images. The capsule has the same black and orange color scheme, the 'actavis' logo is present and correctly oriented, and the '500' imprint is clear. There are no

**LOSSES**:

- `D1_0008` L=0 direct=0.02→tool=0.95 rank=0.12 **TN_lost_to_FP** used_tool=True
  > The query image displays yellow and white bristles, whereas all reference images show either blue/white or red/white bristles. The domain knowledge tool confirmed that yellow/white is not a standard color combination for
- `D1_0094` L=1 direct=0.98→tool=0.05 rank=0.77 **TP_lost_to_FN** used_tool=False
  > The query image appears visually identical to the normal reference images. The capsule has the same black and orange color scheme, the 'actavis' logo and '500' text are in the same position and style, and there are no vi
- `D1_0179` L=1 direct=0.95→tool=0.05 rank=0.54 **TP_lost_to_FN** used_tool=False
  > The query image appears visually consistent with the normal reference images. The component's shape, texture, lighting, and central hole are all within the expected variation seen in the reference set. No obvious defects

### D10  (wins 4, losses 6)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D10_0002` L=0 direct=0.95→tool=0.01 rank=0.07 **FP_corrected** used_tool=False
  > The query image is visually indistinguishable from the normal reference images, showing standard tea light candles with no anomalies.
- `D10_0172` L=1 direct=0.01→tool=0.95 rank=0.21 **FN_corrected** used_tool=False
  > The query image displays the HC-SR04 module upside down compared to the normal reference images, where the pins are at the top and the text is upright. This orientation difference is a clear anomaly.
- `D10_0156` L=1 direct=0.01→tool=0.95 rank=0.51 **FN_corrected** used_tool=True
  > The query image shows an HC-SR04 module missing the standard protective black mesh grilles on the transducers, which are present in all reference images. Domain knowledge confirms this is a non-standard and likely defect
- `D10_0076` L=0 direct=0.98→tool=0.05 rank=0.12 **FP_corrected** used_tool=True
  > The query image is visually identical to the normal reference images in terms of component placement, silkscreen, and board layout. The tool's output was inconsistent with the visual evidence and thus ignored. No anomali

**LOSSES**:

- `D10_0057` L=0 direct=0.01→tool=0.95 rank=0.08 **TN_lost_to_FP** used_tool=False
  > The query image contains the text 'HW-168' near the IN+ label, which is absent in all reference images. This is a definitive visual difference indicating an anomaly.
- `D10_0009` L=0 direct=0.01→tool=0.95 rank=0.12 **TN_lost_to_FP** used_tool=False
  > The query image displays the HC-SR04 module with the text 'HC-SR04' oriented upside down relative to the pin headers, while all reference images show the text right-side up relative to the pins. This consistent orientati
- `D10_0069` L=0 direct=0.02→tool=0.95 rank=0.27 **TN_lost_to_FP** used_tool=True
  > The query image shows a clear rotation anomaly compared to the strictly horizontal alignment of the reference images, which is confirmed by the tool and visual inspection.
- `D10_0139` L=1 direct=0.98→tool=0.05 rank=0.20 **TP_lost_to_FN** used_tool=False
  > The query image shows four yellow crescent-shaped objects on a green background, which is consistent with the normal reference images. There are no obvious defects, color variations, or shape irregularities visible in th
- `D10_0043` L=0 direct=0.01→tool=0.90 rank=0.09 **TN_lost_to_FP** used_tool=False
  > The query image displays the HC-SR04 module with the text 'HC-SR04' and pin labels oriented upside down relative to the pin headers, while all reference images show the text right-side up relative to the pins. This consi
- `D10_0136` L=1 direct=0.98→tool=0.15 rank=0.23 **TP_lost_to_FN** used_tool=True
  > The white residue is likely normal flux residue or handling marks common on uncleaned PCBs, as suggested by domain knowledge. While the texture is slightly distinct from a perfect board, it does not clearly show signs of

### D2  (wins 5, losses 10)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 6}

**WINS** (item · direct→tool · rank · type · rationale):

- `D2_0173` L=1 direct=0.01→tool=1.00 rank=0.76 **FN_corrected** used_tool=False
  > The query image displays a significant dent on the side of the can, which is a physical anomaly not present in the normal reference images.
- `D2_0146` L=1 direct=0.01→tool=0.95 rank=0.29 **FN_corrected** used_tool=False
  > The query image displays a 'Golden Leaf' (黄金叶) brand cigarette pack, which is visually distinct in color (orange) and branding from all four reference images (which show 'Tianzi' and 'Jinmen' brands). This significant de
- `D2_0092` L=1 direct=0.01→tool=0.95 rank=0.63 **FN_corrected** used_tool=True
  > The query image contains a clear plastic straw/wrapper wrapped around the carton, which is explicitly stated as abnormal by domain knowledge and is visually distinct from the clean packaging in the reference images.
- `D2_0095` L=1 direct=0.02→tool=0.95 rank=0.86 **FN_corrected** used_tool=True
  > The query image displays a white-labeled Genki Forest bottle filled with dark liquid. Domain knowledge confirms this label is exclusively for clear/light beverages, making the dark liquid content a definitive anomaly com
- `D2_0068` L=0 direct=0.95→tool=0.05 rank=0.30 **FP_corrected** used_tool=False
  > The query image appears visually identical to the normal reference images. The cup, label, text, and background are consistent with the reference set, showing no signs of damage, tampering, or manufacturing defects.

**LOSSES**:

- `D2_0087` L=0 direct=0.01→tool=1.00 rank=0.08 **TN_lost_to_FP** used_tool=False
  > The query image displays the cigarette pack upside down, with inverted text and logo, which is a significant deviation from the normal orientation shown in the reference images.
- `D2_0080` L=0 direct=0.02→tool=1.00 rank=0.02 **TN_lost_to_FP** used_tool=False
  > The query image displays the back of the package with nutritional information and barcodes, whereas all reference images display the front of the package with branding and product visibility. This constitutes a significa
- `D2_0056` L=0 direct=0.01→tool=0.95 rank=0.05 **TN_lost_to_FP** used_tool=False
  > The query image displays a fundamentally different packaging design (stylized/comic style) compared to the normal reference images (standard product packaging with realistic fruit imagery), indicating this is an anomalou
- `D2_0083` L=0 direct=0.02→tool=0.95 rank=0.09 **TN_lost_to_FP** used_tool=False
  > The query image displays the back/side of the bottle, while all reference images display the front. This significant difference in the visible face of the product constitutes an anomaly.
- `D2_0133` L=1 direct=0.98→tool=0.05 rank=0.08 **TP_lost_to_FN** used_tool=False
  > The query image is visually indistinguishable from the normal reference images, showing the same product packaging and contents without any apparent anomalies.
- `D2_0162` L=1 direct=0.98→tool=0.05 rank=0.80 **TP_lost_to_FN** used_tool=True
  > The query image depicts a standard closed pack of YunYan cigarettes with Chinese characters, which is a known normal variant of the product as confirmed by the tool. It matches the visual characteristics of the other clo
- `D2_0097` L=1 direct=0.98→tool=0.05 rank=0.73 **TP_lost_to_FN** used_tool=False
  > The query image displays a normal front view of the product carton without any visible anomalies such as damage, leakage, or foreign objects. The reference images provide context (back view, crushed view) but do not indi
- `D2_0130` L=1 direct=0.98→tool=0.05 rank=0.70 **TP_lost_to_FN** used_tool=True
  > The query image displays a known variant ('Sunshine PRIDE') of the brand shown in the references ('Panda PRIDE'). The differences in logo and text are consistent with normal product line variations, not defects or anomal
  ... and 2 more losses.

### D4  (wins 1, losses 13)

Win sample-types: {'FN_corrected': 1}
Loss sample-types: {'TN_lost_to_FP': 7, 'TP_lost_to_FN': 6}

**WINS** (item · direct→tool · rank · type · rationale):

- `D4_0176` L=1 direct=0.05→tool=0.95 rank=0.82 **FN_corrected** used_tool=True
  > The query image contains large rocks and debris at the bottom, which is a significant structural deviation from the uniform, fine-grained texture seen in all normal reference images. This confirms the image is anomalous.

**LOSSES**:

- `D4_0046` L=0 direct=0.05→tool=0.95 rank=0.23 **TN_lost_to_FP** used_tool=True
  > The query image contains distinct elongated dark marks (scratches) that are absent in the normal reference images, which only exhibit a uniform speckled pattern. This matches the definition of an anomaly provided by the 
- `D4_0021` L=0 direct=0.05→tool=0.90 rank=0.52 **TN_lost_to_FP** used_tool=True
  > The query image contains distinct elongated dark marks (likely scratches) that are absent in the normal reference images, which only show small, scattered specks. This deviation from the expected texture pattern indicate
- `D4_0028` L=0 direct=0.05→tool=0.90 rank=0.29 **TN_lost_to_FP** used_tool=True
  > The query image contains distinct elongated dark marks that deviate from the random, granular speckle pattern seen in the normal reference images. This non-random, linear feature is consistent with a defect like a scratc
- `D4_0126` L=1 direct=0.95→tool=0.10 rank=0.63 **TP_lost_to_FN** used_tool=False
  > The query image displays a texture and spot distribution consistent with the provided normal reference images. No distinct anomalies such as large cracks, foreign objects, or unusual patterns are visible that would devia
- `D4_0044` L=0 direct=0.05→tool=0.90 rank=0.24 **TN_lost_to_FP** used_tool=True
  > The query image contains distinct elongated dark streaks that are absent in the normal reference images, which only show small, scattered spots. This deviation from the established normal pattern indicates an anomaly.
- `D4_0035` L=0 direct=0.05→tool=0.90 rank=0.02 **TN_lost_to_FP** used_tool=True
  > The query image contains distinct elongated dark marks in the top right corner that are absent in all reference images, which only show small, scattered speckles. This visual discrepancy confirms the presence of an anoma
- `D4_0128` L=1 direct=0.95→tool=0.10 rank=0.42 **TP_lost_to_FN** used_tool=False
  > The query image displays features (pitting, small dark spots) that are consistent with the normal variations observed in the reference images. No distinct anomaly is apparent.
- `D4_0106` L=1 direct=0.95→tool=0.10 rank=0.49 **TP_lost_to_FN** used_tool=True
  > The query image shows a shadow and a texture variation but lacks the specific defect patterns (cracks, rough edges) present in the reference images. Based on the tool's guidance and visual evidence, this is likely a norm
  ... and 5 more losses.

### D5  (wins 5, losses 17)

Win sample-types: {'FN_corrected': 3, 'other': 2}
Loss sample-types: {'TN_lost_to_FP': 9, 'TP_lost_to_FN': 8}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5_0179` L=1 direct=0.05→tool=0.95 rank=0.27 **FN_corrected** used_tool=True
  > The query image exhibits marked color variegation (black/dark brown center, lighter brown periphery) and structural asymmetry, which are key dermoscopic indicators of malignancy (melanoma). This contrasts sharply with th
- `D5_0119` L=1 direct=0.05→tool=0.85 rank=0.32 **FN_corrected** used_tool=False
  > The query image displays a lesion with asymmetry, irregular borders, and color variation (multiple shades of brown), which are classic ABCD criteria for melanoma. In contrast, the reference images show more symmetric, un
- `D5_0136` L=1 direct=0.08→tool=0.65 rank=0.65 **FN_corrected** used_tool=True
  > The query image displays a lesion with significantly lighter coloration and a less defined pigment network compared to the darker, more structured 'normal' reference images. This visual deviation from the established nor
- `D5_0166` L=1 direct=0.05→tool=0.20 rank=0.31 **other** used_tool=True
  > Although the tool mentions the 'fried egg' pattern can be a sign of malignancy, the interpretation warns to cross-check visually. The query lesion appears relatively symmetric with regular borders, and similar central pi
- `D5_0114` L=1 direct=0.05→tool=0.20 rank=0.27 **other** used_tool=True
  > Although the tool suggests redness is a warning sign, the interpretation warns against relying on this without visual confirmation. The lesion's structure appears relatively organized (reticular pattern) without obvious 

**LOSSES**:

- `D5_0030` L=0 direct=0.05→tool=0.95 rank=0.21 **TN_lost_to_FP** used_tool=False
  > The query image shows a diffuse, non-pigmented, reddish lesion (likely a bruise or vascular anomaly) which is structurally and chromatically distinct from the well-defined, pigmented melanocytic nevi shown in the referen
- `D5_0004` L=0 direct=0.05→tool=0.95 rank=0.28 **TN_lost_to_FP** used_tool=True
  > The query image exhibits significant asymmetry and color variegation (dark center, lighter periphery), which the domain knowledge tool identified as strong indicators of an anomaly. These features are distinct from the m
- `D5_0032` L=0 direct=0.05→tool=0.95 rank=0.87 **TN_lost_to_FP** used_tool=True
  > The query image displays a predominantly pink lesion, which visually deviates significantly from the brown, pigmented lesions in the normal reference images. This color difference aligns with the tool's indication that p
- `D5_0051` L=0 direct=0.05→tool=0.90 rank=0.46 **TN_lost_to_FP** used_tool=True
  > The query image (small, dark, symmetric) is visually distinct from the normal reference images (larger, irregular, lighter brown). In the context of anomaly detection where references define the 'normal' class, this sign
- `D5_0061` L=0 direct=0.05→tool=0.90 rank=0.22 **TN_lost_to_FP** used_tool=False
  > The query image displays a lesion with asymmetry, irregular borders, and color variation (dark brown to black), which are classic ABCD criteria for melanoma. In contrast, the reference images show lesions that are more s
- `D5_0176` L=1 direct=0.95→tool=0.10 rank=0.46 **TP_lost_to_FN** used_tool=False
  > The query image shows a benign-appearing reticular pigment network consistent with the normal reference images, lacking the chaotic features of an anomaly.
- `D5_0112` L=1 direct=0.95→tool=0.10 rank=0.75 **TP_lost_to_FN** used_tool=True
  > The query image displays features consistent with a benign melanocytic nevus (symmetry, uniform color, reticular network), matching the tool's assessment and resembling the benign reference images. No clear signs of anom
- `D5_0155` L=1 direct=0.95→tool=0.10 rank=0.65 **TP_lost_to_FN** used_tool=True
  > Although the tool flagged the reddish hue and diffuse borders as anomalous, visual inspection reveals that Reference Image 4 exhibits nearly identical features (reddish-brown color, diffuse borders) and is part of the no
  ... and 9 more losses.

### D5b  (wins 3, losses 4)

Win sample-types: {'FP_corrected': 3}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5b_0045` L=0 direct=0.98→tool=0.05 rank=0.31 **FP_corrected** used_tool=False
  > The query image displays normal brain anatomy, specifically the lateral ventricles, which are clearly visible and symmetric. There are no signs of hemorrhage, mass effect, or abnormal signal intensity that would suggest 
- `D5b_0031` L=0 direct=0.98→tool=0.05 rank=0.51 **FP_corrected** used_tool=True
  > Visual inspection confirms the query image shows a normal brain MRI with symmetric structures and no visible lesions or abnormal signal intensities, contradicting the tool's hallucinated claim of a hyperintense lesion.
- `D5b_0058` L=0 direct=0.95→tool=0.10 rank=0.52 **FP_corrected** used_tool=True
  > Visual inspection reveals no focal lesions, mass effects, or asymmetry in the query image compared to the normal references, aligning with the tool's criteria for a normal scan.

**LOSSES**:

- `D5b_0066` L=0 direct=0.02→tool=0.95 rank=0.55 **TN_lost_to_FP** used_tool=True
  > The query image displays a sagittal view of the brain, whereas all four reference images display axial views. In the context of visual anomaly detection where 'normal' is defined by the reference set, this significant de
- `D5b_0020` L=0 direct=0.02→tool=0.95 rank=0.33 **TN_lost_to_FP** used_tool=True
  > The query image displays a hyperintense signal pattern (bright areas) typical of acute ischemia on a DWI sequence, which is visually distinct from the normal anatomical appearance in the reference images. This indicates 
- `D5b_0059` L=0 direct=0.02→tool=0.90 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a distinct focal hyperintense lesion in the right hemisphere, which is absent in the normal reference images and is indicative of a pathological anomaly such as a tumor, hemorrhage, or infarct.
- `D5b_0137` L=1 direct=0.98→tool=0.10 rank=0.59 **TP_lost_to_FN** used_tool=True
  > The apparent blurriness in the query image is a known characteristic of certain MRI sequences (e.g., DWI/ADC) and not an anomaly, as confirmed by domain knowledge and visual consistency with a brain scan.

### D5c  (wins 7, losses 13)

Win sample-types: {'FP_corrected': 3, 'FN_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 9}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5c_0131` L=1 direct=0.02→tool=1.00 rank=0.90 **FN_corrected** used_tool=False
  > The query image contains a fundamentally different object (small, simple oval) compared to the consistent object in the reference images (large, complex kidney-bean shape), indicating a certain anomaly.
- `D5c_0174` L=1 direct=0.05→tool=0.98 rank=0.97 **FN_corrected** used_tool=False
  > The query image contains a tiny, indistinct fragment that is drastically different in size and morphology compared to the large, well-defined J-shaped structures in all reference images, indicating a clear anomaly.
- `D5c_0165` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=False
  > The query image contains a prominent dark hole and a significantly different shape and size compared to the normal reference images, which are smaller and lack such features.
- `D5c_0100` L=1 direct=0.05→tool=0.95 rank=0.79 **FN_corrected** used_tool=False
  > The query image exhibits a clear 'J' shape, which is morphologically distinct from the rounded, amorphous shapes seen in all four normal reference images. This strong visual discrepancy indicates an anomaly.
- `D5c_0083` L=0 direct=0.95→tool=0.10 rank=1.00 **FP_corrected** used_tool=False
  > The query image displays a single, crescent-shaped object that is visually consistent with the objects in the majority of the normal reference images. While there are variations in size and exact shape among the referenc
- `D5c_0035` L=0 direct=0.95→tool=0.10 rank=0.81 **FP_corrected** used_tool=True
  > The query image visually matches the majority of the reference images (small, textured blobs). The single reference image with a large, complex shape is the outlier/anomaly in the reference set, not the query. Thus, the 
- `D5c_0070` L=0 direct=0.95→tool=0.10 rank=0.91 **FP_corrected** used_tool=True
  > The tool's assertion that reference images have 'uniform, smooth patterns' is visually incorrect; all images (query and references) share the same noisy, textured appearance and irregular shapes. The query image is consi

**LOSSES**:

- `D5c_0004` L=0 direct=0.02→tool=0.95 rank=0.94 **TN_lost_to_FP** used_tool=False
  > The query image contains only a tiny speck, which is drastically different from the larger, complex shapes seen in all normal reference images, indicating a clear anomaly.
- `D5c_0042` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=True
  > The query image exhibits significant morphological deviations from the reference images, including a much larger size, irregular boundary, and prominent internal voids, which are strong indicators of an anomaly in segmen
- `D5c_0061` L=0 direct=0.02→tool=0.95 rank=0.84 **TN_lost_to_FP** used_tool=False
  > The query image exhibits a complex, multi-part structure with an internal void that is not present in any of the simpler, solid reference images, indicating a clear deviation from the normal class.
- `D5c_0151` L=1 direct=0.95→tool=0.05 rank=0.92 **TP_lost_to_FN** used_tool=True
  > The query image displays a single, solid, contiguous object, which aligns with the definition of a normal instance provided by the domain knowledge tool. It lacks the holes or fragmentation seen in some reference images,
- `D5c_0161` L=1 direct=0.95→tool=0.05 rank=0.92 **TP_lost_to_FN** used_tool=True
  > The query image shows an object with the same texture as the references. The domain knowledge tool confirmed that variations in size and shape are normal for this dataset, so the visual differences do not constitute an a
- `D5c_0015` L=0 direct=0.02→tool=0.90 rank=0.88 **TN_lost_to_FP** used_tool=True
  > The query image displays a significant morphological deviation (a long, thin protrusion and irregular boundary) compared to the compact, smoother shapes in the reference images. This structural difference is consistent w
- `D5c_0102` L=1 direct=0.95→tool=0.10 rank=0.91 **TP_lost_to_FN** used_tool=False
  > The query image is consistent with the majority of the normal reference images, showing a similar small, textured object. The variation in size and shape among the reference images suggests that the object in the query i
- `D5c_0120` L=1 direct=0.95→tool=0.10 rank=0.96 **TP_lost_to_FN** used_tool=False
  > The query image displays a single, connected object with a texture and general morphology consistent with the provided normal reference images. There are no obvious visual deviations such as unexpected shapes, textures, 
  ... and 5 more losses.

### D5d  (wins 6, losses 10)

Win sample-types: {'FP_corrected': 3, 'FN_corrected': 3}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 7}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5d_0150` L=1 direct=0.02→tool=0.95 rank=0.59 **FN_corrected** used_tool=False
  > The query image contains a clear polypoid lesion, which is a structural anomaly not present in the normal reference images showing healthy colonic mucosa.
- `D5d_0135` L=1 direct=0.02→tool=0.95 rank=0.48 **FN_corrected** used_tool=True
  > The query image shows a distinct dark, oval-shaped object in the lumen that is not present in any of the normal reference images. This object appears to be a foreign body, clot, or lesion, which is a clear deviation from
- `D5d_0128` L=1 direct=0.02→tool=0.95 rank=0.35 **FN_corrected** used_tool=True
  > The query image displays a clear, raised, lobulated mass (polyp) protruding into the colonic lumen, which is a distinct anomaly compared to the smooth mucosal folds in the normal reference images. The tool's confirmation
- `D5d_0023` L=0 direct=0.98→tool=0.10 rank=0.39 **FP_corrected** used_tool=True
  > The yellow discoloration appears as a flat, smooth patch consistent with benign bile staining, lacking the raised texture or surrounding erythema associated with pathological exudate.
- `D5d_0071` L=0 direct=0.95→tool=0.10 rank=0.47 **FP_corrected** used_tool=True
  > Although the tool suggests yellow patches can be anomalies, visual inspection indicates the discoloration in the query image is superficial residue (similar to reference image 3) rather than a fixed tissue lesion, making
- `D5d_0045` L=0 direct=0.92→tool=0.10 rank=0.40 **FP_corrected** used_tool=False
  > The query image displays normal mucosal folds and coloration typical of a healthy endoscopic view, with no visible anomalies such as lesions, bleeding, or abnormal growths when compared to the provided normal reference i

**LOSSES**:

- `D5d_0074` L=0 direct=0.02→tool=0.95 rank=0.57 **TN_lost_to_FP** used_tool=False
  > The query image displays a clear, raised, nodular mass (likely a polyp) within the colonic lumen, which is a significant deviation from the smooth, healthy mucosal folds seen in the normal reference images.
- `D5d_0069` L=0 direct=0.02→tool=0.95 rank=0.36 **TN_lost_to_FP** used_tool=True
  > The query image displays a prominent, raised, nodular lesion (polyp) that disrupts the normal smooth mucosal architecture seen in the reference images. This visual evidence, supported by the domain knowledge tool, confir
- `D5d_0075` L=0 direct=0.02→tool=0.95 rank=0.64 **TN_lost_to_FP** used_tool=True
  > The query image displays a distinct flat, depressed, and discolored lesion on the colonic mucosa, which is absent in the normal reference images. This visual finding aligns with the domain knowledge tool's indication of 
- `D5d_0170` L=1 direct=0.98→tool=0.05 rank=0.44 **TP_lost_to_FN** used_tool=True
  > The query image displays normal gastric mucosa with smooth folds and uniform color, consistent with healthy anatomy and lacking the specific anomalies present in the reference images.
- `D5d_0146` L=1 direct=0.98→tool=0.05 rank=0.38 **TP_lost_to_FN** used_tool=True
  > The query image shows a normal pylorus with a patent opening and physiological bile staining. There are no visual signs of pathology such as ulcers, tumors, or strictures. The difference in anatomy from the reference ima
- `D5d_0154` L=1 direct=0.98→tool=0.05 rank=0.38 **TP_lost_to_FN** used_tool=True
  > The query image shows healthy colonic mucosa with normal vascular patterns, consistent with the normal reference images. The green overlay is an artificial annotation, not a biological anomaly. No pathological features a
- `D5d_0166` L=1 direct=0.98→tool=0.05 rank=0.47 **TP_lost_to_FN** used_tool=True
  > The query image displays normal colonic mucosa with a visible endoscope tip, showing no signs of inflammation, ulcers, or polyps. It is consistent with the normal reference images and distinct from the pathological refer
- `D5d_0129` L=1 direct=0.98→tool=0.10 rank=0.31 **TP_lost_to_FN** used_tool=True
  > The yellow discoloration in the query image appears to be superficial bile staining on otherwise healthy, intact mucosa, which is a common and normal finding in endoscopy, rather than a pathological lesion like a xanthom
  ... and 2 more losses.

### D6  (wins 4, losses 17)

Win sample-types: {'FP_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 10, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D6_0015` L=0 direct=0.98→tool=0.05 rank=0.62 **FP_corrected** used_tool=False
  > The query image appears visually consistent with the normal reference images, showing similar rural landscape features, road patterns, and building placements. No obvious anomalies are detected.
- `D6_0063` L=0 direct=0.98→tool=0.10 rank=0.60 **FP_corrected** used_tool=True
  > The perceived 'circular anomaly' is actually a natural variation in the farmstead layout (buildings and a pond in a clearing) compared to the reference images. The overall scene structure (fields, road, vegetation) is co
- `D6_0000` L=0 direct=0.95→tool=0.10 rank=0.82 **FP_corrected** used_tool=True
  > The query image displays normal agricultural field characteristics with uniform texture and faint linear patterns consistent with farming activities. No anomalous features like irregular patches or sudden color shifts ar
- `D6_0039` L=0 direct=0.95→tool=0.10 rank=0.85 **FP_corrected** used_tool=True
  > The dark spot appears to be a small tree or bush, a common natural feature in agricultural fields. The absence in reference images is likely due to seasonal changes or minor variations in vegetation, not an anomaly. The 

**LOSSES**:

- `D6_0024` L=0 direct=0.02→tool=0.95 rank=0.71 **TN_lost_to_FP** used_tool=True
  > The query image contains a large, irregular patch of light-colored ground that is visually distinct from the uniform dark soil in all reference images. This significant deviation in texture and color confirms the presenc
- `D6_0137` L=1 direct=0.95→tool=0.05 rank=0.38 **TP_lost_to_FN** used_tool=False
  > After comparing the query image with the normal reference images, the overall layout, buildings, roads, and vegetation appear consistent. There are no obvious structural changes, missing objects, or unusual patterns that
- `D6_0117` L=1 direct=0.99→tool=0.10 rank=0.78 **TP_lost_to_FN** used_tool=True
  > The query image depicts a standard rural landscape consistent with the rural portions of the reference images. The absence of the suburban development seen in other reference images is a normal variation in land use, not
- `D6_0116` L=1 direct=0.99→tool=0.10 rank=0.70 **TP_lost_to_FN** used_tool=True
  > Although the query image (construction site) differs visually from the reference images (completed homes), the disconfirm clause in the tool output suggests that such generic 'discontinuity' signals might not indicate an
- `D6_0051` L=0 direct=0.02→tool=0.90 rank=0.72 **TN_lost_to_FP** used_tool=True
  > The query image shows a significant visual deviation from the normal reference images: the body of water present in the references is dry or covered in sediment in the query. While this could be a seasonal change, relati
- `D6_0111` L=1 direct=0.98→tool=0.10 rank=0.66 **TP_lost_to_FN** used_tool=False
  > After comparing the query image with the normal reference images, the overall scene composition, building locations, and vegetation patterns appear consistent. There are no obvious structural anomalies, missing objects, 
- `D6_0133` L=1 direct=0.98→tool=0.10 rank=0.82 **TP_lost_to_FN** used_tool=True
  > The visual difference is due to the field being in an active growth stage (green with planting rows) versus the reference fields being dormant/fallow (brown). The striping is consistent with normal agricultural patterns 
- `D6_0110` L=1 direct=0.98→tool=0.10 rank=0.36 **TP_lost_to_FN** used_tool=True
  > The 'anomaly' identified by the tool (winding dirt path) appears to be a natural feature like a dry creek bed or trail, which is consistent with the topography and not indicative of damage or illegal activity. The visual
  ... and 9 more losses.

### D7  (wins 2, losses 2)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 1}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D7_0135` L=1 direct=0.02→tool=1.00 rank=0.97 **FN_corrected** used_tool=False
  > The query image features a horse-drawn carriage in a park-like square, which is fundamentally different from the car-centric urban street scenes in the reference images. This constitutes a significant anomaly.
- `D7_0022` L=0 direct=0.95→tool=0.10 rank=0.21 **FP_corrected** used_tool=True
  > Although the tool suggests construction barriers are anomalies, the interpretation warns to cross-check with visual evidence. The barrier is a static, expected part of the environment on the side of the road and does not

**LOSSES**:

- `D7_0055` L=0 direct=0.02→tool=0.95 rank=0.61 **TN_lost_to_FP** used_tool=True
  > The query image contains a pedestrian crossing the street at night, which is a high-risk anomalous event confirmed by domain knowledge and clearly visible in the image, unlike the normal reference images.
- `D7_0134` L=1 direct=0.98→tool=0.10 rank=0.88 **TP_lost_to_FN** used_tool=True
  > Although the query image (rural village with sheep) differs significantly from the urban reference images, the tool's disconfirm clause warns that the LLM's 'anomalous' verdict may be generic and that the scene is likely

### D8  (wins 4, losses 8)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 3}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 4, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D8_0072` L=0 direct=0.95→tool=0.10 rank=0.50 **FP_corrected** used_tool=True
  > The query image depicts a scene consistent with the normal reference images in terms of location and context. The presence of a uniformed individual, while not seen in the specific reference frames, is confirmed by domai
- `D8_0159` L=1 direct=0.02→tool=0.85 rank=0.50 **FN_corrected** used_tool=True
  > Although the tool states uniformed personnel are common, the visual evidence shows a distinct deviation: the query image contains a uniformed individual in the foreground, whereas all four normal reference images show on
- `D8_0175` L=1 direct=0.02→tool=0.85 rank=0.50 **FN_corrected** used_tool=False
  > The query image features a person in a distinct uniform walking in the center of the frame, whereas all reference images show only civilians in casual attire. This deviation in the type of person present suggests an anom
- `D8_0177` L=1 direct=0.02→tool=0.85 rank=0.50 **FN_corrected** used_tool=True
  > Although uniformed officers are common in public areas, the provided normal reference images exclusively show civilians. The query image's prominent uniformed officer is a significant visual deviation from the establishe

**LOSSES**:

- `D8_0020` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > Although the tool states uniformed officers are generally normal, the visual evidence shows that none of the four normal reference images contain a uniformed individual. The query image is the only one with this feature,
- `D8_0133` L=1 direct=0.95→tool=0.05 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The query image shows a uniformed individual walking through a public area, which is a normal occurrence for security or police personnel in such locations. The visual context matches the reference images perfectly, with
- `D8_0138` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The tool flagged the blue pants as unusual, but the disconfirm clause warned of potential hallucination. Visually, the scene depicts a person walking normally in a public area, consistent with the activity in the referen
- `D8_0179` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The query image shows a person in what appears to be a security or police uniform walking through the area. While this is different from the casual pedestrians in the reference images, uniformed personnel are commonly pr
- `D8_0126` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The query image shows a person in a uniform (likely security or police) in a public plaza. While distinct from the civilians in the reference images, the presence of such personnel is a normal, expected occurrence in pub
- `D8_0038` L=0 direct=0.02→tool=0.85 rank=0.50 **TN_lost_to_FP** used_tool=True
  > Although the tool states uniformed personnel are generally normal in such locations, the four reference images (which define the 'normal' class for this specific task) exclusively show people in casual clothing. The quer
- `D8_0029` L=0 direct=0.02→tool=0.85 rank=0.50 **TN_lost_to_FP** used_tool=True
  > Although the tool suggests uniformed personnel are generally normal, the provided normal reference images exclusively show civilians in casual clothing. The query image distinctly features a person in a formal uniform (l
- `D8_0014` L=0 direct=0.02→tool=0.20 rank=0.50 **other** used_tool=True
  > The query image shows a uniformed person walking in a station area, which is consistent with normal security presence. No obvious anomalies detected when compared to reference images showing typical civilian activities.

### D9  (wins 6, losses 11)

Win sample-types: {'FP_corrected': 4, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 8}

**WINS** (item · direct→tool · rank · type · rationale):

- `D9_0121` L=1 direct=0.01→tool=1.00 rank=0.58 **FN_corrected** used_tool=False
  > The query image displays a cherry-flavored juice (red liquid, cherry icon), whereas all reference images display banana-flavored juice (light liquid, banana icon). This is a definitive mismatch in product type.
- `D9_0168` L=1 direct=0.01→tool=0.95 rank=0.73 **FN_corrected** used_tool=False
  > The query image displays a bottle with a dark red liquid and a cherry label, whereas all reference images show bottles with light-colored liquids and banana or orange labels. This significant difference in both liquid co
- `D9_0022` L=0 direct=0.99→tool=0.10 rank=0.28 **FP_corrected** used_tool=False
  > The query image shows a standard jumper wire setup identical in structure to the reference images, with only the wire color varying across references. No visual anomalies detected.
- `D9_0078` L=0 direct=0.99→tool=0.10 rank=0.11 **FP_corrected** used_tool=False
  > The query image matches the pattern of the normal reference images (single yellow wire with orange connectors on mesh). No visual defects or deviations are apparent.
- `D9_0079` L=0 direct=0.98→tool=0.10 rank=0.16 **FP_corrected** used_tool=False
  > The query image shows similar hardware components (bolts, nuts, washers) in a plastic bag as the reference images. The arrangement and types of components appear consistent with normal variations in how such parts might 
- `D9_0057` L=0 direct=0.99→tool=0.40 rank=0.35 **FP_corrected** used_tool=True
  > The query image shows text printed on the cable jacket, while all four reference images show cables with no visible text. Although the tool claimed the references also have text, visual inspection confirms they do not. T

**LOSSES**:

- `D9_0047` L=0 direct=0.02→tool=1.00 rank=0.13 **TN_lost_to_FP** used_tool=False
  > The query image displays a bottle with dark liquid and a cherry label, whereas all reference images show bottles with light-colored liquid and a banana label. This clear visual discrepancy in both content (liquid color) 
- `D9_0032` L=0 direct=0.02→tool=1.00 rank=0.07 **TN_lost_to_FP** used_tool=False
  > The query image displays a cherry-labeled bottle with dark liquid, whereas all reference images show banana-labeled bottles with light liquid. This fundamental difference in product appearance confirms the query is anoma
- `D9_0176` L=1 direct=0.99→tool=0.05 rank=0.31 **TP_lost_to_FN** used_tool=True
  > The query image depicts a standard single yellow jumper wire configuration, which is confirmed as normal by domain knowledge and visually matches the first reference image. No anomalies such as damage or incorrect wiring
- `D9_0041` L=0 direct=0.02→tool=0.95 rank=0.79 **TN_lost_to_FP** used_tool=False
  > The query image displays a cherry juice bottle with dark liquid, whereas all reference images show banana or orange juice bottles with light-colored liquids. This clear deviation in both liquid color and label content in
- `D9_0090` L=1 direct=0.98→tool=0.05 rank=0.03 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard arrangement of healthy food items in a lunchbox. There are no signs of anomalies such as damage, contamination, or incorrect ite
- `D9_0129` L=1 direct=0.98→tool=0.05 rank=0.04 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing the expected food items in a standard arrangement. No anomalies are detected.
- `D9_0146` L=1 direct=0.95→tool=0.05 rank=0.10 **TP_lost_to_FN** used_tool=True
  > Visual inspection confirms the query image contains standard food items (oranges, nectarine, granola, banana chips, almonds) with no visible defects like mold, bruising, or foreign objects compared to the reference image
- `D9_0128` L=1 direct=0.99→tool=0.10 rank=0.24 **TP_lost_to_FN** used_tool=False
  > The query image depicts a standard jumper wire setup identical in structure to the normal reference images. There are no visible defects, misalignments, or unexpected components.
  ... and 3 more losses.

---

## tool_expert_score  (77 wins, 190 losses, net flips -41 on n=480)

### D1  (wins 9, losses 16)

Win sample-types: {'FP_corrected': 5, 'other': 4}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 4, 'other': 11}

**WINS** (item · direct→tool · rank · type · rationale):

- `D1_0084` L=0 direct=0.95→tool=0.05 rank=0.02 **FP_corrected** used_tool=False
  > The query image exhibits the same speckled texture pattern as the normal reference images, with no visible anomalies or deviations.
- `D1_0038` L=0 direct=0.98→tool=0.10 rank=0.26 **FP_corrected** used_tool=False
  > The query image displays the 'actavis' logo and '500' marking, consistent with three of the four reference images. The only difference is one reference image missing the logo, which makes that reference the outlier, not 
- `D1_0064` L=0 direct=0.98→tool=0.15 rank=0.24 **FP_corrected** used_tool=True
  > The expert model indicates a weak anomaly signal (rank 0.24), and visual inspection confirms the query image is consistent with the normal reference images, showing expected variations in logo presence.
- `D1_0088` L=0 direct=0.95→tool=0.15 rank=0.29 **FP_corrected** used_tool=True
  > The expert model indicates a weak anomaly signal (rank 0.29), and visual inspection confirms the query image is consistent with the normal reference images, showing no obvious defects.
- `D1_0009` L=0 direct=0.95→tool=0.15 rank=0.13 **FP_corrected** used_tool=True
  > The subspacead expert returned a low anomaly score (rank 0.13), indicating the query is consistent with normal samples. Although the blue conductor appeared slightly different visually, the quantitative evidence strongly
- `D1_0016` L=0 direct=0.98→tool=0.85 rank=0.06 **other** used_tool=True
  > Visual inspection reveals a clear anomaly: the copper strands in the top conductor are bright and shiny, contrasting with the dark, oxidized strands in all reference images. Although the subspacead tool indicated a norma
- `D1_0114` L=1 direct=0.02→tool=0.15 rank=0.19 **other** used_tool=True
  > The expert tool indicates a weak anomaly signal (rank 0.19), suggesting the query is normal. Although the bristle color (yellow) differs from the provided references (blue/red), this is a global feature that the subspace
- `D1_0156` L=1 direct=0.02→tool=0.15 rank=0.47 **other** used_tool=True
  > The subspacead expert indicates a weak anomaly signal (rank 0.47), and visual inspection confirms the query image's speckle pattern and embossing are consistent with the normal reference images, showing only natural vari
  ... and 1 more wins.

**LOSSES**:

- `D1_0008` L=0 direct=0.02→tool=0.95 rank=0.12 **TN_lost_to_FP** used_tool=False
  > The query image has yellow bristles while all reference images have either blue or red bristles, indicating a clear color anomaly in the product.
- `D1_0094` L=1 direct=0.98→tool=0.05 rank=0.77 **TP_lost_to_FN** used_tool=False
  > The query image matches the reference images in terms of color, shape, and text markings. No anomalies are detected.
- `D1_0137` L=1 direct=0.98→tool=0.15 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The moderate anomaly signal is explained by normal variation in the reference set (some refs have text, some don't). The query image matches the 'with text' normal variant, so it is not anomalous.
- `D1_0179` L=1 direct=0.95→tool=0.15 rank=0.54 **TP_lost_to_FN** used_tool=True
  > The expert tool indicates a weak anomaly signal (rank 0.54), and visual inspection confirms the query image appears consistent with the normal reference images without any obvious defects.
- `D1_0111` L=1 direct=0.98→tool=0.45 rank=0.77 **TP_lost_to_FN** used_tool=True
  > The query image shows a small dark spot that differs from the reference images, but the subspacead tool's moderate signal (rank 0.77) with its disconfirm clause suggests this could be normal texture variation rather than
- `D1_0142` L=1 direct=0.95→tool=0.75 rank=0.32 **other** used_tool=True
  > Despite a low global subspacead score, the query image exhibits distinct, irregular light streaks not present in the reference images, indicating a localized surface anomaly that the global metric likely missed.
- `D1_0165` L=1 direct=0.95→tool=0.75 rank=0.80 **other** used_tool=True
  > The query image contains a visible dark smudge/stain on the fabric to the left of the zipper, which is absent in all reference images. This represents a clear defect, supported by the moderate anomaly signal from subspac
- `D1_0044` L=0 direct=0.01→tool=0.15 rank=0.37 **other** used_tool=True
  > The expert score indicates a weak anomaly signal (rank 0.37), and visual inspection confirms the mesh structure is intact with no localized defects. The difference in orientation is likely a normal variation rather than 
  ... and 8 more losses.

### D10  (wins 9, losses 8)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 1, 'other': 6}
Loss sample-types: {'TP_lost_to_FN': 3, 'other': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D10_0156` L=1 direct=0.01→tool=0.95 rank=0.51 **FN_corrected** used_tool=False
  > The query image is anomalous because the protective mesh grilles on the ultrasonic transducers are missing, which are present in all normal reference images.
- `D10_0076` L=0 direct=0.98→tool=0.05 rank=0.12 **FP_corrected** used_tool=False
  > The query image shows a standard HC-SR04 module with all components present and correctly placed, matching the normal reference images. No anomalies are detected.
- `D10_0002` L=0 direct=0.95→tool=0.05 rank=0.07 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing four intact tea light candles with no apparent anomalies.
- `D10_0160` L=1 direct=0.01→tool=0.15 rank=0.60 **other** used_tool=True
  > The expert tool indicates a weak anomaly signal, and visual inspection confirms the query image matches the normal reference images without any obvious defects.
- `D10_0172` L=1 direct=0.01→tool=0.15 rank=0.21 **other** used_tool=True
  > The expert model indicates a weak anomaly signal (rank 0.21), suggesting the query is normal. The observed difference in pin orientation is consistent with a simple rotation of the component, not a defect.
- `D10_0098` L=1 direct=0.01→tool=0.15 rank=0.25 **other** used_tool=True
  > The subspacead expert tool indicated a weak anomaly signal (rank 0.25), and visual inspection confirms the capsules in the query image are consistent with the normal reference images, showing no obvious defects.
- `D10_0178` L=1 direct=0.02→tool=0.15 rank=0.43 **other** used_tool=True
  > The expert score indicates a weak anomaly signal (rank 0.43), and visual inspection confirms the query image contains normal objects consistent with the reference set.
- `D10_0094` L=1 direct=0.02→tool=0.15 rank=0.41 **other** used_tool=True
  > The expert tool indicates a weak anomaly signal (rank 0.41), consistent with the query being a normal sample, possibly just rotated. No visible defects contradict this.
  ... and 1 more wins.

**LOSSES**:

- `D10_0097` L=1 direct=0.99→tool=0.05 rank=0.34 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard HC-SR04 ultrasonic sensor module with all expected components intact and no visible anomalies.
- `D10_0139` L=1 direct=0.98→tool=0.10 rank=0.20 **TP_lost_to_FN** used_tool=True
  > The subspacead expert indicates a weak anomaly signal (rank 0.2), and visual inspection confirms the objects in the query image are consistent with the normal reference images, showing no visible defects or irregularitie
- `D10_0136` L=1 direct=0.98→tool=0.15 rank=0.23 **TP_lost_to_FN** used_tool=True
  > The subspacead expert returned a low anomaly rank (0.23), suggesting the query is normal. Although there are minor visual differences (potential residue), the tool's interpretation warns that global scores might not shif
- `D10_0153` L=1 direct=0.98→tool=0.85 rank=0.62 **other** used_tool=True
  > The query image displays a distinct protrusion on one of the wheel spokes near the center, which is not present in any of the normal reference images. This structural defect confirms the image is anomalous.
- `D10_0106` L=1 direct=0.98→tool=0.85 rank=0.62 **other** used_tool=True
  > The query image contains a distinct white spot on the bottom right of the object, which is not present in any of the normal reference images. Although the expert score was moderate, the visual evidence of a specific fore
- `D10_0158` L=1 direct=0.98→tool=0.85 rank=0.48 **other** used_tool=True
  > Despite the weak global score from subspacead, a clear localized defect (dark spot) is visible on the cashew in the query image, which is not present in the normal reference images. The tool's interpretation explicitly a
- `D10_0069` L=0 direct=0.02→tool=0.15 rank=0.27 **other** used_tool=True
  > The expert tool indicates a weak anomaly signal (rank 0.27), suggesting the query is normal. The slight rotation observed is likely within normal variation and not a defect.
- `D10_0029` L=0 direct=0.02→tool=0.15 rank=0.17 **other** used_tool=True
  > Both visual inspection and the subspacead expert score (rank 0.175) indicate the query image is normal with no significant anomalies.

### D2  (wins 10, losses 15)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 3, 'other': 6}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 6, 'other': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D2_0092` L=1 direct=0.01→tool=0.95 rank=0.63 **FN_corrected** used_tool=True
  > The query image contains a plastic straw wrapper attached to the front of the carton, which is a distinct physical object not present in any of the normal reference images. This constitutes a clear anomaly despite the to
- `D2_0159` L=1 direct=0.01→tool=0.95 rank=0.99 **FN_corrected** used_tool=True
  > The query image displays the back of the bottle, whereas the reference images consistently show the front. This represents a significant deviation from the 'normal' state defined by the references. The subspacead expert 
- `D2_0095` L=1 direct=0.02→tool=0.92 rank=0.86 **FN_corrected** used_tool=True
  > The query image shows a bottle filled with dark liquid, which is a fundamental difference from the reference images showing the same bottle type with a white label and no dark liquid. The strong anomaly score from the to
- `D2_0037` L=0 direct=0.98→tool=0.15 rank=0.19 **FP_corrected** used_tool=True
  > The subspacead expert indicates a weak anomaly signal (rank 0.19), and the visual content of the package back appears standard with no obvious defects.
- `D2_0137` L=1 direct=0.02→tool=0.25 rank=0.68 **other** used_tool=True
  > The moderate anomaly signal is explained by natural variation in pack designs seen across reference images. The query image matches one of the normal design variants, so it is not anomalous.
- `D2_0145` L=1 direct=0.02→tool=0.25 rank=0.71 **other** used_tool=True
  > The moderate anomaly signal likely reflects normal text variations between product batches rather than actual defects. All key visual elements (logo, colors, pattern) are consistent with reference images.
- `D2_0146` L=1 direct=0.01→tool=0.15 rank=0.29 **other** used_tool=True
  > The subspacead expert score indicates a weak anomaly signal (rank 0.29), suggesting the query image is consistent with the normal reference images. Visually, the query matches the first reference image, confirming it is 
- `D2_0173` L=1 direct=0.01→tool=0.15 rank=0.76 **other** used_tool=True
  > Despite a moderate anomaly score from subspacead, visual inspection confirms the can is intact with no physical defects. The signal is attributed to benign variation (lighting/angle) as per the tool's disconfirm clause.
  ... and 2 more wins.

**LOSSES**:

- `D2_0056` L=0 direct=0.01→tool=0.95 rank=0.05 **TN_lost_to_FP** used_tool=False
  > The query image displays a different product packaging design than the reference images, indicating an anomaly in the product line.
- `D2_0087` L=0 direct=0.01→tool=0.95 rank=0.08 **TN_lost_to_FP** used_tool=True
  > Despite the low global anomaly score from the tool, the query image is visually upside down relative to the reference images, with inverted text and logo. This orientation difference is a clear anomaly that the global su
- `D2_0029` L=0 direct=0.01→tool=0.95 rank=0.51 **TN_lost_to_FP** used_tool=True
  > The query image displays the back of the bottle with nutritional information, whereas all reference images show the front with a cartoon character. This is a clear content anomaly (different label side) that the global s
- `D2_0133` L=1 direct=0.98→tool=0.05 rank=0.08 **TP_lost_to_FN** used_tool=True
  > The subspacead expert returned a very low anomaly rank (0.08), strongly suggesting the query image is normal and consistent with the reference set. No visual defects were apparent to contradict this finding.
- `D2_0080` L=0 direct=0.02→tool=0.95 rank=0.02 **TN_lost_to_FP** used_tool=True
  > The query image shows the back of the package, while all reference images show the front. This is a clear and significant deviation from the normal reference distribution, indicating an anomaly despite the tool's weak si
- `D2_0167` L=1 direct=0.98→tool=0.10 rank=0.18 **TP_lost_to_FN** used_tool=True
  > Both visual inspection and the subspacead expert score (rank 0.18) indicate the query image is normal with no detectable anomalies.
- `D2_0170` L=1 direct=0.98→tool=0.15 rank=0.13 **TP_lost_to_FN** used_tool=True
  > The expert tool strongly indicates normality with rank 0.13, and visual inspection confirms the query matches the normal front-view reference images without any visible defects or anomalies.
- `D2_0162` L=1 direct=0.98→tool=0.15 rank=0.80 **TP_lost_to_FN** used_tool=True
  > The moderate anomaly score is likely caused by the presence of an open pack in the reference images, creating a distribution shift for the closed query pack. Since the query matches the other closed reference images and 
  ... and 7 more losses.

### D4  (wins 3, losses 9)

Win sample-types: {'other': 3}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 4, 'other': 4}

**WINS** (item · direct→tool · rank · type · rationale):

- `D4_0176` L=1 direct=0.05→tool=0.35 rank=0.82 **other** used_tool=True
  > The query image displays a rocky texture similar to the references, though with larger stones at the bottom. The expert score was moderate (0.82) with a strong disconfirm clause regarding reference variation. Since the r
- `D4_0122` L=1 direct=0.05→tool=0.25 rank=0.79 **other** used_tool=True
  > The moderate anomaly signal is explained by the disconfirm clause - the reference images show comparable texture variations and small dark spots, indicating the query image's features are within normal variation.
- `D4_0121` L=1 direct=0.05→tool=0.20 rank=0.47 **other** used_tool=True
  > The expert score indicates a weak anomaly signal (rank 0.475), suggesting the query image is consistent with normal samples. While a small dark spot is visible, the low score implies it is likely a natural texture variat

**LOSSES**:

- `D4_0106` L=1 direct=0.95→tool=0.10 rank=0.49 **TP_lost_to_FN** used_tool=True
  > The expert tool indicates a weak anomaly signal (rank 0.49), and visual inspection confirms the query image texture is consistent with the normal reference images, showing no obvious defects.
- `D4_0126` L=1 direct=0.95→tool=0.15 rank=0.63 **TP_lost_to_FN** used_tool=True
  > The expert score was moderate (0.63) and the interpretation's disconfirm clause noted that comparable variation in references implies normality. Visual inspection confirms the query texture matches the references, indica
- `D4_0128` L=1 direct=0.95→tool=0.15 rank=0.42 **TP_lost_to_FN** used_tool=True
  > The subspacead score indicates a weak anomaly signal, and visual inspection confirms the features in the query image (spots, texture) are consistent with the normal reference images. The larger dark patch is similar to d
- `D4_0155` L=1 direct=0.95→tool=0.20 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The subspacead expert indicated a weak anomaly signal (rank 0.50), and visual inspection confirms the features (pits, small dark spots) are consistent with the normal variations seen in the reference images. The failed p
- `D4_0086` L=0 direct=0.05→tool=0.75 rank=0.76 **TN_lost_to_FP** used_tool=True
  > The query image contains a distinct vertical scratch/line defect not present in the normal reference images, overriding the moderate tool score which flagged potential texture variation.
- `D4_0021` L=0 direct=0.05→tool=0.35 rank=0.52 **other** used_tool=True
  > While the global subspacead score suggests normality, the elongated marks in the query image appear slightly different from the typical scattered spots in reference images. However, without stronger evidence of anomaly, 
- `D4_0076` L=0 direct=0.05→tool=0.35 rank=0.69 **other** used_tool=True
  > The subspacead tool indicated a moderate/ambiguous signal (rank 0.69) with a strong disconfirm clause suggesting normal variation. Visually, the query's marks are a plausible variation of the texture seen in references, 
- `D4_0152` L=1 direct=0.95→tool=0.75 rank=0.75 **other** used_tool=True
  > The query image contains a visible vertical crack and a dark spot, which are distinct defects not present in the normal reference images. Although the subspacead tool gave a moderate score with a warning about normal var
  ... and 1 more losses.

### D5  (wins 2, losses 16)

Win sample-types: {'other': 2}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 10, 'other': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5_0166` L=1 direct=0.05→tool=0.20 rank=0.31 **other** used_tool=True
  > The subspacead tool indicates a weak anomaly signal (rank 0.31), suggesting the query image is consistent with the normal reference images. The visual features, while potentially concerning to a human observer, are not f
- `D5_0136` L=1 direct=0.08→tool=0.20 rank=0.65 **other** used_tool=True
  > The tool's moderate anomaly signal is likely due to natural variation in benign lesions, as the reference images show similar diversity in shape and texture. The disconfirm clause indicates this is not a true defect.

**LOSSES**:

- `D5_0032` L=0 direct=0.05→tool=0.87 rank=0.87 **TN_lost_to_FP** used_tool=True
  > The query image displays a pink, non-pigmented lesion, which is visually distinct from the dark brown, pigmented lesions in the reference set. The subspacead tool confirms this with a high anomaly rank (0.87), and the di
- `D5_0117` L=1 direct=0.95→tool=0.15 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The tool's moderate anomaly signal is explained by the disconfirm clause as likely benign variation, which aligns with the visual appearance of the lesion as a normal nevus consistent with the reference images.
- `D5_0177` L=1 direct=0.95→tool=0.15 rank=0.27 **TP_lost_to_FN** used_tool=True
  > The subspacead expert returned a low anomaly score (rank 0.27), indicating the query image is consistent with the normal reference distribution. Visual inspection confirms the lesion lacks severe anomalous features like 
- `D5_0158` L=1 direct=0.95→tool=0.15 rank=0.35 **TP_lost_to_FN** used_tool=True
  > Both visual inspection and the subspacead expert score (rank 0.35) strongly indicate the lesion is normal, showing no signs of asymmetry, irregular borders, or color variegation.
- `D5_0167` L=1 direct=0.95→tool=0.15 rank=0.48 **TP_lost_to_FN** used_tool=True
  > The expert tool indicates a weak anomaly signal, and visual inspection confirms the lesion has symmetric borders and uniform coloration consistent with the normal reference images.
- `D5_0099` L=1 direct=0.95→tool=0.20 rank=0.65 **TP_lost_to_FN** used_tool=True
  > The subspacead tool indicated a moderate signal but explicitly noted that comparable variation in references implies normality. The query lesion is visually consistent with a benign nevus, and the reference images show a
- `D5_0115` L=1 direct=0.95→tool=0.20 rank=0.57 **TP_lost_to_FN** used_tool=True
  > The query image shows a symmetric, uniformly pigmented lesion with well-defined borders, consistent with the normal reference images. The subspacead score supports this, indicating a weak anomaly signal.
- `D5_0112` L=1 direct=0.95→tool=0.25 rank=0.75 **TP_lost_to_FN** used_tool=True
  > The tool indicated a moderate anomaly signal, but the disconfirm clause noted that such signals can arise from normal variation present in the reference set. Visual inspection confirms the query lesion's characteristics 
  ... and 8 more losses.

### D5b  (wins 4, losses 18)

Win sample-types: {'FP_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 4, 'other': 11}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5b_0045` L=0 direct=0.98→tool=0.15 rank=0.31 **FP_corrected** used_tool=True
  > The expert tool indicates a low anomaly score (rank 0.31), and visual inspection confirms the brain structure in the query image is normal with no visible defects or abnormalities.
- `D5b_0031` L=0 direct=0.98→tool=0.15 rank=0.51 **FP_corrected** used_tool=True
  > The subspacead score indicates a weak anomaly signal, and visual inspection confirms the query image resembles the normal reference images with no obvious defects.
- `D5b_0067` L=0 direct=0.98→tool=0.15 rank=0.53 **FP_corrected** used_tool=True
  > The expert tool indicates a weak anomaly signal (rank 0.53), suggesting the image is normal. Visual inspection confirms no obvious defects or abnormalities in the query image compared to the normal references.
- `D5b_0058` L=0 direct=0.95→tool=0.15 rank=0.52 **FP_corrected** used_tool=True
  > The subspacead score indicates a weak anomaly signal (rank 0.52), and visual inspection does not reveal any obvious large-scale defects or structural abnormalities compared to the reference images. The slight differences

**LOSSES**:

- `D5b_0066` L=0 direct=0.02→tool=0.95 rank=0.55 **TN_lost_to_FP** used_tool=True
  > Despite the weak global anomaly score, the query image exhibits a prominent horizontal split through the brain tissue that is not present in any of the normal reference images. This is a clear structural anomaly.
- `D5b_0149` L=1 direct=0.98→tool=0.15 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The moderate anomaly score is explained by the disconfirm clause: the reference images show significant natural variation in slice level and contrast, making the query's deviation benign.
- `D5b_0137` L=1 direct=0.98→tool=0.15 rank=0.59 **TP_lost_to_FN** used_tool=True
  > The subspacead expert returned a weak anomaly signal (rank 0.59), suggesting the query is consistent with normal samples. Although the image appears blurrier than references, no specific localized defect was identified, 
- `D5b_0072` L=0 direct=0.05→tool=0.85 rank=0.71 **TN_lost_to_FP** used_tool=True
  > The query image exhibits severe blurring and low resolution compared to the sharp, high-quality reference images, indicating a significant anomaly likely due to corruption or acquisition error.
- `D5b_0068` L=0 direct=0.05→tool=0.85 rank=0.86 **TN_lost_to_FP** used_tool=True
  > The query image exhibits severe blurring and low resolution compared to the sharp reference images, which is a significant structural anomaly confirmed by the strong subspacead signal (rank 0.86).
- `D5b_0160` L=1 direct=0.95→tool=0.15 rank=0.44 **TP_lost_to_FN** used_tool=True
  > The expert score indicates a weak anomaly signal (rank 0.44), and visual inspection confirms the brain structure appears normal without obvious defects.
- `D5b_0156` L=1 direct=0.98→tool=0.20 rank=0.56 **TP_lost_to_FN** used_tool=True
  > The subspacead expert returned a weak anomaly signal (rank 0.56), indicating the query is likely normal. The patchknn tool was unavailable. Visual inspection does not reveal obvious gross anomalies, and the weak global s
- `D5b_0069` L=0 direct=0.02→tool=0.35 rank=0.53 **other** used_tool=True
  > The subspacead expert score indicated a weak anomaly signal (rank 0.53), suggesting the image is likely normal. Although the patchknn tool failed, the global assessment and visual inspection do not reveal definitive path
  ... and 10 more losses.

### D5c  (wins 7, losses 10)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 5}
Loss sample-types: {'TN_lost_to_FP': 7, 'TP_lost_to_FN': 2, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5c_0131` L=1 direct=0.02→tool=0.95 rank=0.90 **FN_corrected** used_tool=False
  > The query image contains a distinctly different object (small, oval) compared to the consistent kidney-like structures in the reference images, indicating a clear anomaly.
- `D5c_0174` L=1 direct=0.05→tool=0.97 rank=0.97 **FN_corrected** used_tool=True
  > The query image displays a significantly smaller and fragmented object compared to the large, coherent structures in the reference images. The expert tool confirms this with a high anomaly rank of 0.97.
- `D5c_0118` L=1 direct=0.02→tool=0.92 rank=0.96 **FN_corrected** used_tool=True
  > The subspacead expert provided a very strong anomaly signal (rank 0.96). Although there is a warning about texture variations, the query object's distinct shape compared to the reference images supports the conclusion th
- `D5c_0165` L=1 direct=0.02→tool=0.87 rank=0.87 **FN_corrected** used_tool=True
  > The query image exhibits a distinct structural anomaly (a large void) not present in the solid reference shapes, which is confirmed by the high anomaly score from the subspacead expert.
- `D5c_0035` L=0 direct=0.95→tool=0.20 rank=0.81 **FP_corrected** used_tool=True
  > The query image is visually consistent with three of the four reference images in terms of size and shape. The moderate anomaly score is likely due to the high variance in the reference set (specifically the second image
- `D5c_0032` L=0 direct=0.95→tool=0.20 rank=0.84 **FP_corrected** used_tool=True
  > The subspacead expert returned a borderline rank (0.84) with a strong disconfirm clause stating that if references show comparable variation, the image is likely normal. The visual difference (size/orientation) appears t
- `D5c_0100` L=1 direct=0.05→tool=0.75 rank=0.79 **FN_corrected** used_tool=True
  > The query image exhibits a significantly different morphology (elongated hook shape) compared to the compact, rounded shapes in the normal reference images. While the subspacead tool indicated a moderate signal with a wa

**LOSSES**:

- `D5c_0004` L=0 direct=0.02→tool=0.94 rank=0.94 **TN_lost_to_FP** used_tool=True
  > The query image contains a significantly smaller and sparser point cloud compared to the large, dense structures in the reference images. The expert tool confirmed this with a high anomaly rank of 0.94.
- `D5c_0054` L=0 direct=0.02→tool=0.93 rank=0.93 **TN_lost_to_FP** used_tool=True
  > The subspacead expert flagged a strong anomaly (rank 0.93). Visual inspection confirms a structural difference: the query is a single connected object, while some references are fragmented. This supports the anomaly clas
- `D5c_0039` L=0 direct=0.02→tool=0.92 rank=0.90 **TN_lost_to_FP** used_tool=True
  > The query image displays a large, textured object, which is visually distinct in size and shape from the objects in the reference images, particularly the very small object in one reference. The expert tool confirms this
- `D5c_0015` L=0 direct=0.02→tool=0.91 rank=0.88 **TN_lost_to_FP** used_tool=True
  > The query image exhibits a distinct structural shape with a protrusion that deviates significantly from the compact, rounded shapes in the reference images, supported by a strong anomaly score from the expert tool.
- `D5c_0042` L=0 direct=0.02→tool=0.88 rank=0.88 **TN_lost_to_FP** used_tool=True
  > The query image exhibits distinct morphological anomalies (large internal voids, irregular shape) compared to the solid, compact reference objects, which is strongly supported by the high anomaly score from the subspacea
- `D5c_0055` L=0 direct=0.02→tool=0.85 rank=0.86 **TN_lost_to_FP** used_tool=True
  > The subspacead expert provided a strong anomaly signal (rank 0.86). Visually, the query object is small and simple, differing significantly in scale and complexity from two of the four reference images. While two referen
- `D5c_0061` L=0 direct=0.02→tool=0.82 rank=0.84 **TN_lost_to_FP** used_tool=True
  > The query image exhibits a complex, multi-lobed structure with a significant internal void, which is a clear structural deviation from the simpler, solid shapes seen in the normal reference images. Although the subspacea
- `D5c_0120` L=1 direct=0.95→tool=0.15 rank=0.96 **TP_lost_to_FN** used_tool=True
  > Although the subspacead tool flagged a strong anomaly (rank 0.96), the visual evidence shows the query object shares the same fundamental characteristics (single connected component, similar texture) as the normal refere
  ... and 2 more losses.

### D5d  (wins 8, losses 25)

Win sample-types: {'FP_corrected': 3, 'FN_corrected': 3, 'other': 2}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 8, 'other': 16}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5d_0173` L=1 direct=0.02→tool=0.98 rank=0.57 **FN_corrected** used_tool=False
  > The query image contains a prominent dark foreign object in the center of the lumen, which is a significant deviation from the normal anatomical structures seen in the reference images.
- `D5d_0150` L=1 direct=0.02→tool=0.92 rank=0.59 **FN_corrected** used_tool=True
  > The query image contains a distinct, raised polypoid lesion, which is a clear visual anomaly not present in the normal reference images. The weak global signal from subspacead is consistent with the tool's warning that l
- `D5d_0023` L=0 direct=0.98→tool=0.15 rank=0.39 **FP_corrected** used_tool=True
  > The global anomaly score is low (0.39 rank), and the visible yellow patch appears to be bile staining or a minor artifact rather than a pathological lesion, consistent with normal endoscopic findings.
- `D5d_0135` L=1 direct=0.02→tool=0.85 rank=0.48 **FN_corrected** used_tool=True
  > Despite the weak global anomaly score, the query image contains a clear, localized dark lesion not present in the normal reference images. The tool's disconfirm clause specifically notes that such localized defects may b
- `D5d_0071` L=0 direct=0.95→tool=0.15 rank=0.47 **FP_corrected** used_tool=True
  > The expert model indicates a weak anomaly signal (rank 0.47), and the visible yellow discoloration is consistent with benign bile staining seen in normal endoscopic procedures, not a pathological anomaly.
- `D5d_0045` L=0 direct=0.92→tool=0.15 rank=0.40 **FP_corrected** used_tool=True
  > The expert tool indicates a weak anomaly signal (rank 0.40), and visual inspection confirms the mucosal surface appears healthy and consistent with the normal reference images.
- `D5d_0177` L=1 direct=0.02→tool=0.15 rank=0.30 **other** used_tool=True
  > The expert tool suggests a normal classification with a low anomaly rank. Visual confirmation shows typical gastric anatomy (pylorus) with benign bile residue, supporting the conclusion that the image is normal.
- `D5d_0128` L=1 direct=0.02→tool=0.15 rank=0.35 **other** used_tool=True
  > The expert tool indicates a weak anomaly signal (rank 0.35), and visual inspection confirms normal colonic mucosa without obvious defects, supporting a normal classification.

**LOSSES**:

- `D5d_0169` L=1 direct=0.95→tool=0.10 rank=0.40 **TP_lost_to_FN** used_tool=True
  > The expert tool indicates a weak anomaly signal (rank 0.40), suggesting the image is normal. Visual inspection confirms healthy mucosa without obvious defects, aligning with the tool's assessment.
- `D5d_0065` L=0 direct=0.02→tool=0.85 rank=0.32 **TN_lost_to_FP** used_tool=True
  > Despite the low global anomaly score from the tool, the query image contains a clearly visible polypoid lesion (a raised, rounded mass) which is a distinct anomaly compared to the normal colonic folds in the reference im
- `D5d_0129` L=1 direct=0.98→tool=0.15 rank=0.31 **TP_lost_to_FN** used_tool=True
  > The subspacead expert indicates a weak anomaly signal (rank 0.31), and the visible yellowish patch appears to be benign bile staining rather than a pathological defect, consistent with normal endoscopic findings.
- `D5d_0146` L=1 direct=0.98→tool=0.15 rank=0.38 **TP_lost_to_FN** used_tool=True
  > The expert tool indicates a low probability of anomaly (rank 0.38), and visual inspection confirms the image resembles the normal reference set, showing a healthy pyloric sphincter with typical residue.
- `D5d_0112` L=1 direct=0.95→tool=0.15 rank=0.33 **TP_lost_to_FN** used_tool=True
  > The expert tool indicates a weak anomaly signal (rank 0.33), and visual inspection confirms the image shows normal colonic mucosa without obvious defects, consistent with the reference images.
- `D5d_0166` L=1 direct=0.98→tool=0.20 rank=0.47 **TP_lost_to_FN** used_tool=True
  > The subspacead expert indicates a weak anomaly signal (rank 0.47), and visual inspection shows no obvious pathological features - the yellowish material appears to be normal bile/mucus and the tissue structure looks heal
- `D5d_0093` L=1 direct=0.92→tool=0.15 rank=0.30 **TP_lost_to_FN** used_tool=True
  > The expert score indicates a weak anomaly signal (rank 0.30), and the yellow discoloration appears to be bile staining, which is a normal finding seen in some reference images. Therefore, the query is classified as norma
- `D5d_0161` L=1 direct=0.98→tool=0.25 rank=0.51 **TP_lost_to_FN** used_tool=True
  > The subspacead expert model indicated a weak anomaly signal (rank 0.51), suggesting the query is consistent with normal samples. The visual feature (yellow patch) appears to be bile staining, which is a common normal fin
  ... and 17 more losses.

### D6  (wins 7, losses 28)

Win sample-types: {'FP_corrected': 6, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 14, 'other': 12}

**WINS** (item · direct→tool · rank · type · rationale):

- `D6_0015` L=0 direct=0.98→tool=0.15 rank=0.62 **FP_corrected** used_tool=True
  > The expert tool indicated a moderate anomaly signal, but the interpretation's disconfirm clause suggests this is likely normal variation given the similar appearance of the reference images. The visual content of the que
- `D6_0000` L=0 direct=0.95→tool=0.15 rank=0.82 **FP_corrected** used_tool=True
  > The moderate anomaly score from the tool is likely due to natural texture variations common in aerial imagery, as the reference images show similar patterns. No actual defects or foreign objects are visible in the query 
- `D6_0039` L=0 direct=0.95→tool=0.15 rank=0.85 **FP_corrected** used_tool=True
  > Although subspacead flagged a strong anomaly, the disconfirm clause warns of texture over-flagging in this domain. Visual inspection confirms the query matches the reference scene structure, suggesting the signal is a fa
- `D6_0017` L=0 direct=0.95→tool=0.15 rank=0.75 **FP_corrected** used_tool=True
  > The expert tool indicated a moderate anomaly signal, but the interpretation noted this could be benign variation. Visual inspection confirms the query image is consistent with the normal reference images, showing no obvi
- `D6_0064` L=0 direct=0.95→tool=0.15 rank=0.39 **FP_corrected** used_tool=True
  > The subspacead expert score indicates a weak anomaly signal (rank 0.39), and visual inspection confirms the query image is consistent with the normal reference images, showing a typical residential layout with a commerci
- `D6_0063` L=0 direct=0.98→tool=0.20 rank=0.60 **FP_corrected** used_tool=True
  > The query image shows the same location as the references with only natural variations in vegetation and lighting. The moderate anomaly score from subspacead is explained by the disconfirm clause as likely benign variati
- `D6_0100` L=1 direct=0.02→tool=0.25 rank=0.68 **other** used_tool=True
  > The field color difference is consistent with seasonal variation (green vs. brown vegetation) rather than a true anomaly. The moderate tool signal is explained by the disconfirm clause about normal variation in reference

**LOSSES**:

- `D6_0116` L=1 direct=0.99→tool=0.10 rank=0.70 **TP_lost_to_FN** used_tool=True
  > The visual difference (construction site vs. finished neighborhood) represents a domain shift or expected variation in land use stages, not a defect. The tool's moderate score is explained by this variation, satisfying t
- `D6_0110` L=1 direct=0.98→tool=0.15 rank=0.36 **TP_lost_to_FN** used_tool=True
  > The subspacead expert returned a low anomaly score (rank 0.36), indicating the query is consistent with normal samples. Visual inspection confirms no significant structural anomalies, and the perceived differences are li
- `D6_0130` L=1 direct=0.98→tool=0.15 rank=0.54 **TP_lost_to_FN** used_tool=True
  > The expert tool provided a weak anomaly signal (rank 0.54) suggesting the image is normal, which aligns with the visual observation of no obvious defects.
- `D6_0047` L=0 direct=0.02→tool=0.83 rank=0.86 **TN_lost_to_FP** used_tool=True
  > The query image exhibits a significant color anomaly (green vs. brown fields) compared to the uniform brown fields in the reference images, which is confirmed by the high anomaly score from the subspacead expert.
- `D6_0145` L=1 direct=0.95→tool=0.15 rank=0.65 **TP_lost_to_FN** used_tool=True
  > The subspacead tool indicated a moderate/ambiguous signal (rank 0.65), but the interpretation warned this could be normal variation. Visual inspection confirms the query image is structurally consistent with the referenc
- `D6_0137` L=1 direct=0.95→tool=0.15 rank=0.38 **TP_lost_to_FN** used_tool=True
  > The subspacead expert indicates a weak anomaly signal (rank 0.38), and visual inspection confirms the query image is consistent with the normal reference images, showing no obvious defects.
- `D6_0156` L=1 direct=0.98→tool=0.20 rank=0.40 **TP_lost_to_FN** used_tool=True
  > The expert score indicates a weak anomaly signal (rank 0.4), and visual inspection shows the construction state is consistent with normal commercial development phases seen in reference images.
- `D6_0117` L=1 direct=0.99→tool=0.25 rank=0.78 **TP_lost_to_FN** used_tool=True
  > The query image shows a typical rural landscape consistent with the rural portions of the reference images. The moderate anomaly signal from subspacead is likely due to normal variation in rural textures and patterns, no
  ... and 20 more losses.

### D7  (wins 3, losses 14)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2}
Loss sample-types: {'other': 14}

**WINS** (item · direct→tool · rank · type · rationale):

- `D7_0135` L=1 direct=0.02→tool=0.95 rank=0.97 **FN_corrected** used_tool=False
  > The query image depicts a tourist scene with a horse-drawn carriage in a square, whereas all reference images show standard car-centric street views. This fundamental difference in scene content and context indicates a s
- `D7_0159` L=1 direct=0.02→tool=0.92 rank=0.87 **FN_corrected** used_tool=True
  > The query image shows a rural scene with a car towing a trailer, which is a distinct deviation from the urban street scenes in all reference images. The high subspacead score confirms this significant contextual differen
- `D7_0022` L=0 direct=0.95→tool=0.15 rank=0.21 **FP_corrected** used_tool=True
  > The subspacead expert scored the image as normal (rank 0.21). Although an orange barrier is present, the global model does not flag it as anomalous, suggesting it may be a common feature or the model is robust to such va

**LOSSES**:

- `D7_0076` L=0 direct=0.02→tool=0.25 rank=0.74 **other** used_tool=True
  > The query image shows a normal night driving scene at an intersection. The moderate anomaly signal from subspacead (rank 0.74) is explained by the tool's disconfirm clause as likely normal variation due to different ligh
- `D7_0055` L=0 direct=0.02→tool=0.20 rank=0.61 **other** used_tool=True
  > The query image depicts a standard night driving scene with no obvious anomalies. The moderate anomaly score from the tool is likely due to lighting variations rather than actual defects, as confirmed by the disconfirm c
- `D7_0043` L=0 direct=0.02→tool=0.20 rank=0.59 **other** used_tool=True
  > The expert tool indicates weak anomaly signal (rank 0.59), and visual inspection shows a normal urban driving scene with a delivery truck that, while unusual with hay advertisement, doesn't constitute an anomaly.
- `D7_0054` L=0 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The expert score indicates a weak anomaly signal (rank 0.50), and visual inspection confirms the scene is a typical urban street with no visible defects or anomalies.
- `D7_0014` L=0 direct=0.02→tool=0.15 rank=0.52 **other** used_tool=True
  > The expert tool indicates a weak anomaly signal (rank 0.52), and visual inspection reveals no suspicious regions or defects. The scene appears to be a normal night driving situation.
- `D7_0028` L=0 direct=0.02→tool=0.15 rank=0.25 **other** used_tool=True
  > The subspacead tool indicates a weak anomaly signal (rank 0.25), and visual inspection reveals no suspicious regions or unusual elements in this standard urban driving scene.
- `D7_0045` L=0 direct=0.02→tool=0.15 rank=0.47 **other** used_tool=True
  > The expert tool indicates a weak anomaly signal (rank 0.47), and visual inspection shows no suspicious regions - the query image depicts a normal highway underpass traffic scene consistent with typical driving conditions
- `D7_0038` L=0 direct=0.02→tool=0.15 rank=0.73 **other** used_tool=True
  > The query image shows a normal city street scene. The moderate anomaly signal from subspacead was flagged as potentially benign variation, and visual inspection confirms no actual defects or anomalies are present.
  ... and 6 more losses.

### D8  (wins 8, losses 17)

Win sample-types: {'FN_corrected': 7, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 8, 'other': 9}

**WINS** (item · direct→tool · rank · type · rationale):

- `D8_0102` L=1 direct=0.02→tool=0.90 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a uniformed individual (security/police) which is a significant deviation from the civilians seen in all reference images, indicating an anomaly.
- `D8_0114` L=1 direct=0.02→tool=0.85 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a uniformed individual (security/police) which is not present in the reference images showing only civilians, indicating a deviation from the normal pattern.
- `D8_0159` L=1 direct=0.02→tool=0.85 rank=0.50 **FN_corrected** used_tool=True
  > The query image features a uniformed individual, which is a significant deviation from the civilian subjects seen in all normal reference images, indicating an anomalous event or subject.
- `D8_0112` L=1 direct=0.02→tool=0.85 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a uniformed individual (likely security or police) walking in the foreground, which is a distinct visual deviation from the reference images that only show civilians. This suggests an anomalous e
- `D8_0175` L=1 direct=0.02→tool=0.85 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a uniformed individual, which is a distinct visual anomaly compared to the reference images that exclusively show civilians in casual clothing.
- `D8_0115` L=1 direct=0.05→tool=0.85 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a uniformed individual (security/police) which is not present in the normal reference images showing only civilians, indicating a deviation from the normal pattern.
- `D8_0130` L=1 direct=0.02→tool=0.75 rank=0.50 **FN_corrected** used_tool=True
  > The query image features a uniformed individual, which is a distinct visual deviation from the civilians seen in all reference images. While security presence can be normal, the lack of such figures in the reference set 
- `D8_0107` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > Visual inspection shows a uniformed individual in a public station setting, which is a plausible normal occurrence (security/police) rather than a defect or anomaly. Expert tools were unavailable, so the decision is base

**LOSSES**:

- `D8_0009` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed individual (security/police) which is a distinct deviation from the normal reference images showing only civilians in casual clothing.
- `D8_0032` L=0 direct=0.02→tool=0.92 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed individual, which is a significant visual deviation from the reference images that exclusively show civilians. This suggests an anomalous event or presence.
- `D8_0006` L=0 direct=0.02→tool=0.92 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed individual, which is a distinct visual difference from the reference images that only show civilians. This deviation in subject type strongly indicates an anomaly.
- `D8_0008` L=0 direct=0.05→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed person (security/police) walking in the foreground, which is a significant deviation from the normal reference images that only show civilians.
- `D8_0050` L=0 direct=0.02→tool=0.90 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed individual (security/police) which is a significant deviation from the civilians seen in all reference images, indicating an anomaly.
- `D8_0047` L=0 direct=0.05→tool=0.92 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image displays a high-density crowd, which is a stark contrast to the sparse, normal traffic patterns seen in all reference images, indicating a significant anomaly in the scene's activity level.
- `D8_0029` L=0 direct=0.02→tool=0.85 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed individual (security/police) walking through the scene, which is a significant deviation from the reference images that only show civilians in casual attire. This change in the type o
- `D8_0020` L=0 direct=0.02→tool=0.85 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image features a uniformed individual (security/police) which is visually distinct from the civilians seen in the reference images, suggesting an anomalous event in this context.
  ... and 9 more losses.

### D9  (wins 7, losses 14)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 7, 'other': 4}

**WINS** (item · direct→tool · rank · type · rationale):

- `D9_0078` L=0 direct=0.99→tool=0.05 rank=0.11 **FP_corrected** used_tool=True
  > The expert tool indicates a strong match to normal samples (rank 0.11), and visual inspection confirms the query image is a standard configuration consistent with the reference set.
- `D9_0121` L=1 direct=0.01→tool=0.95 rank=0.58 **FN_corrected** used_tool=False
  > The query image differs significantly from the reference images in both the label (cherry vs banana) and the liquid color (dark red vs light beige), indicating a clear anomaly.
- `D9_0168` L=1 direct=0.01→tool=0.95 rank=0.73 **FN_corrected** used_tool=False
  > The query image displays a cherry-labeled bottle with dark red liquid, which is completely different from all reference images showing banana/orange labels with light-colored liquids. This represents a clear product mism
- `D9_0039` L=0 direct=0.98→tool=0.05 rank=0.05 **FP_corrected** used_tool=True
  > The expert tool strongly indicates the image is normal (rank 0.05), and visual inspection confirms the food items and container match the reference patterns without obvious defects.
- `D9_0079` L=0 direct=0.98→tool=0.10 rank=0.16 **FP_corrected** used_tool=True
  > The expert tool indicates a strong similarity to normal samples (rank 0.16). Visual inspection confirms the query contains the expected hardware components in a standard packaging, with no visible defects or anomalies.
- `D9_0057` L=0 direct=0.99→tool=0.15 rank=0.35 **FP_corrected** used_tool=True
  > The subspacead expert score is low (rank 0.35), indicating the query image is consistent with the normal reference images. The visible text on the cable is a minor variation that does not constitute a significant anomaly
- `D9_0022` L=0 direct=0.99→tool=0.15 rank=0.28 **FP_corrected** used_tool=True
  > The subspacead expert score shows a weak anomaly signal (rank 0.28), and visual inspection confirms the query image matches the pattern of normal reference images with no obvious defects.

**LOSSES**:

- `D9_0032` L=0 direct=0.02→tool=1.00 rank=0.07 **TN_lost_to_FP** used_tool=False
  > The query image is anomalous because the liquid color (red vs. white) and the label icon (cherry vs. banana) differ significantly from the normal reference images.
- `D9_0047` L=0 direct=0.02→tool=0.95 rank=0.13 **TN_lost_to_FP** used_tool=False
  > The query image differs significantly from the reference images in both the label (cherry vs banana) and the liquid color (dark red vs light beige), indicating a clear anomaly.
- `D9_0041` L=0 direct=0.02→tool=0.95 rank=0.79 **TN_lost_to_FP** used_tool=False
  > The query image displays a bottle with a dark reddish-brown liquid and a cherry label, which is visually distinct from the reference images showing light-colored liquids with banana or orange labels. This significant dif
- `D9_0090` L=1 direct=0.98→tool=0.05 rank=0.03 **TP_lost_to_FN** used_tool=True
  > The expert tool indicates a very low anomaly score (rank 0.03), and visual inspection confirms the query image matches the normal reference patterns with no visible defects.
- `D9_0129` L=1 direct=0.98→tool=0.05 rank=0.04 **TP_lost_to_FN** used_tool=True
  > The expert tool indicates a very low anomaly score (rank 0.04), and visual inspection confirms the query image matches the normal reference patterns with no visible defects.
- `D9_0146` L=1 direct=0.95→tool=0.05 rank=0.10 **TP_lost_to_FN** used_tool=True
  > The expert tool indicates a strong match to normal samples (rank 0.10), and visual inspection confirms the food items and their arrangement are consistent with the reference images, showing no anomalies.
- `D9_0128` L=1 direct=0.99→tool=0.10 rank=0.24 **TP_lost_to_FN** used_tool=True
  > The expert tool indicates a strong match to normal samples (rank 0.24). Visually, the single yellow wire configuration is consistent with the normal reference images, showing no defects or anomalies.
- `D9_0157` L=1 direct=0.99→tool=0.15 rank=0.48 **TP_lost_to_FN** used_tool=True
  > The query image shows a normal single cable configuration similar to reference images. The expert tool confirms weak anomaly signal, and no visible defects are present.
  ... and 6 more losses.

---

## tool_hotspot_cropper  (60 wins, 110 losses, net flips -35 on n=479)

### D1  (wins 6, losses 2)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 1}
Loss sample-types: {'TP_lost_to_FN': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D1_0114` L=1 direct=0.02→tool=0.95 rank=0.19 **FN_corrected** used_tool=False
  > The query image has yellow bristles, whereas all reference images have either blue or red bristles. This color deviation is a clear anomaly given the otherwise identical structure and pattern.
- `D1_0084` L=0 direct=0.95→tool=0.05 rank=0.02 **FP_corrected** used_tool=False
  > The query image appears visually identical to the normal reference images, showing the same consistent speckled pattern without any detectable defects or anomalies.
- `D1_0088` L=0 direct=0.95→tool=0.05 rank=0.29 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a properly mounted transistor with no apparent anomalies.
- `D1_0009` L=0 direct=0.95→tool=0.05 rank=0.13 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard three-core cable cross-section with no apparent anomalies.
- `D1_0038` L=0 direct=0.98→tool=0.10 rank=0.26 **FP_corrected** used_tool=False
  > The query image displays a capsule with 'actavis' and '500' markings, which is consistent with three out of the four provided normal reference images. The only difference is one reference image lacking the 'actavis' logo
- `D1_0064` L=0 direct=0.98→tool=0.10 rank=0.24 **FP_corrected** used_tool=True
  > The query image displays a capsule with 'actavis' and '500' printed on it, which matches the majority of the reference images. The cropped region shows standard printing without defects. The absence of the logo in some r

**LOSSES**:

- `D1_0179` L=1 direct=0.95→tool=0.05 rank=0.54 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing no detectable anomalies in shape, texture, or structure.
- `D1_0137` L=1 direct=0.98→tool=0.10 rank=0.72 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with three of the four normal reference images, showing both the 'actavis' logo and '500' imprint. The fourth reference image lacks the 'actavis' logo, but this does not make the qu

→ RULE candidate: on D1, tool tends to correctly down-weight FPs when subspacead rank ∈ [0.02, 0.29].

### D10  (wins 4, losses 4)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 1, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D10_0156` L=1 direct=0.01→tool=1.00 rank=0.51 **FN_corrected** used_tool=False
  > The query image is anomalous because the ultrasonic transducers are exposed without the protective mesh grilles seen in all normal reference images.
- `D10_0002` L=0 direct=0.95→tool=0.01 rank=0.07 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing no signs of anomalies.
- `D10_0172` L=1 direct=0.01→tool=0.95 rank=0.21 **FN_corrected** used_tool=False
  > The query image displays the sensor module upside down compared to the normal reference images, with the pins pointing downwards and the text inverted.
- `D10_0076` L=0 direct=0.98→tool=0.05 rank=0.12 **FP_corrected** used_tool=False
  > The query image shows a standard HC-SR04 module with all components present and correctly placed, matching the normal reference images. No anomalies are detected.

**LOSSES**:

- `D10_0009` L=0 direct=0.01→tool=0.95 rank=0.12 **TN_lost_to_FP** used_tool=False
  > The query image displays the HC-SR04 module with the text 'HC-SR04' oriented upside down relative to the pin headers, while all reference images show the text right-side up relative to the pins. This consistent orientati
- `D10_0097` L=1 direct=0.99→tool=0.05 rank=0.34 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard HC-SR04 ultrasonic sensor module with all expected components in their correct positions. No anomalies are detected.
- `D10_0069` L=0 direct=0.02→tool=0.70 rank=0.27 **TN_lost_to_FP** used_tool=False
  > The query image is rotated relative to the reference images, which is a clear visual difference. While the object itself appears similar, the orientation is inconsistent with the normal references.
- `D10_0016` L=0 direct=0.02→tool=0.15 rank=0.20 **other** used_tool=True
  > The hotspot region shows normal texture patterns consistent with the reference images. No defects, damage, or anomalous features are visible in the extracted region. The object appears to be in normal condition.

### D2  (wins 3, losses 9)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 6}

**WINS** (item · direct→tool · rank · type · rationale):

- `D2_0095` L=1 direct=0.02→tool=1.00 rank=0.86 **FN_corrected** used_tool=False
  > The query image displays a bottle filled with dark liquid, which is a significant deviation from the reference images showing the same bottle model with a white label and no dark liquid.
- `D2_0092` L=1 direct=0.01→tool=0.95 rank=0.63 **FN_corrected** used_tool=False
  > The query image contains an attached plastic straw wrapper that is absent in all normal reference images, indicating a clear packaging anomaly.
- `D2_0037` L=0 direct=0.98→tool=0.10 rank=0.19 **FP_corrected** used_tool=False
  > The query image displays the back of a standard snack package with expected features like text and barcodes. No obvious anomalies such as tears, stains, or foreign objects are visible.

**LOSSES**:

- `D2_0056` L=0 direct=0.01→tool=1.00 rank=0.05 **TN_lost_to_FP** used_tool=False
  > The query image displays a significantly different packaging design and text layout compared to the normal reference images, indicating an anomaly.
- `D2_0080` L=0 direct=0.02→tool=1.00 rank=0.02 **TN_lost_to_FP** used_tool=False
  > The query image shows the back of the product packaging, while the reference images show the front, making it an anomaly.
- `D2_0087` L=0 direct=0.01→tool=0.95 rank=0.08 **TN_lost_to_FP** used_tool=False
  > The query image displays the cigarette pack upside down, with the warning text and logo inverted relative to the normal reference images, indicating a clear anomaly.
- `D2_0170` L=1 direct=0.98→tool=0.05 rank=0.13 **TP_lost_to_FN** used_tool=False
  > The query image displays a standard front view of the snack package that is consistent with the normal reference images showing the same product. No anomalies such as damage, incorrect labeling, or foreign objects are de
- `D2_0167` L=1 direct=0.98→tool=0.05 rank=0.18 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard bottle of juice with no apparent anomalies.
- `D2_0107` L=1 direct=0.95→tool=0.05 rank=0.32 **TP_lost_to_FN** used_tool=False
  > The query image displays a standard instant noodle cup with intact packaging and clear labeling, consistent with the normal reference images. No physical defects or anomalies are visible.
- `D2_0133` L=1 direct=0.98→tool=0.10 rank=0.08 **TP_lost_to_FN** used_tool=False
  > The query image is visually indistinguishable from the normal reference images. All key features (branding, product type, packaging design) match perfectly, indicating this is a normal sample.
- `D2_0097` L=1 direct=0.98→tool=0.10 rank=0.73 **TP_lost_to_FN** used_tool=False
  > The query image displays a standard breakfast milk carton with no visible anomalies compared to the reference images. The packaging, text, and overall appearance are consistent with normal products.
  ... and 1 more losses.

### D4  (wins 4, losses 13)

Win sample-types: {'FN_corrected': 2, 'other': 2}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 6, 'other': 6}

**WINS** (item · direct→tool · rank · type · rationale):

- `D4_0176` L=1 direct=0.05→tool=0.95 rank=0.82 **FN_corrected** used_tool=False
  > The query image contains large rocks and debris at the bottom, which is a clear deviation from the uniform, fine-grained texture seen in all four normal reference images. This structural difference indicates an anomaly.
- `D4_0156` L=1 direct=0.05→tool=0.80 rank=0.20 **FN_corrected** used_tool=False
  > The query image exhibits a significant shadow and a darker, potentially different texture compared to the three uniform, light-colored normal reference images. This visual discrepancy suggests an anomaly, likely due to l
- `D4_0110` L=1 direct=0.05→tool=0.30 rank=0.70 **other** used_tool=False
  > The query image contains a small dark spot that is slightly more pronounced than the minor variations in the reference images, but it could still be within the range of normal surface imperfections. Without more context 
- `D4_0121` L=1 direct=0.05→tool=0.30 rank=0.47 **other** used_tool=False
  > The query image contains a small dark spot that is slightly more pronounced than the minor variations in the reference images, but it could still be within the range of normal surface imperfections. Without more context 

**LOSSES**:

- `D4_0086` L=0 direct=0.05→tool=0.95 rank=0.76 **TN_lost_to_FP** used_tool=False
  > The query image contains a prominent vertical linear defect that is absent in the normal reference images, indicating a clear anomaly.
- `D4_0128` L=1 direct=0.95→tool=0.10 rank=0.42 **TP_lost_to_FN** used_tool=False
  > The query image exhibits texture and imperfections (small dark spots, minor irregularities) that are consistent with the patterns observed in the normal reference images. No distinct anomaly is detected.
- `D4_0133` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The query image displays a concrete surface with a shadow and minor texture variations, which are consistent with normal conditions. Unlike the reference image showing a clear crack, the query image lacks any definitive 
- `D4_0106` L=1 direct=0.95→tool=0.10 rank=0.49 **TP_lost_to_FN** used_tool=False
  > The query image displays a textured surface consistent with the normal reference images. The prominent shadow appears to be a lighting condition rather than a defect, and no other anomalies are visible.
- `D4_0155` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The query image displays a texture consistent with the normal reference images, showing typical surface imperfections like small pits and minor discolorations without any distinct anomalous features.
- `D4_0130` L=1 direct=0.95→tool=0.15 rank=0.57 **TP_lost_to_FN** used_tool=False
  > The query image displays a small, dark spot on a textured surface. While this spot is distinct, it does not appear to be a significant structural defect like the crack seen in one of the reference images. It could be a m
- `D4_0126` L=1 direct=0.95→tool=0.15 rank=0.63 **TP_lost_to_FN** used_tool=True
  > The highlighted region shows a dark patch consistent with the natural texture and inclusions seen in the reference images, albeit slightly larger. It does not exhibit clear signs of a defect like a crack or damage, and f
- `D4_0006` L=0 direct=0.05→tool=0.30 rank=0.10 **other** used_tool=False
  > The query image contains elongated dark marks that differ slightly from the more circular specks in the reference images, but the overall texture and appearance are similar. The difference is not significant enough to cl
  ... and 5 more losses.

### D5  (wins 3, losses 18)

Win sample-types: {'FN_corrected': 1, 'other': 2}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 9, 'other': 7}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5_0119` L=1 direct=0.05→tool=0.92 rank=0.32 **FN_corrected** used_tool=True
  > The extracted hotspot shows significant border irregularity and color heterogeneity, which are strong indicators of an anomalous skin lesion, failing the disconfirm clause for normal texture or benign edges.
- `D5_0179` L=1 direct=0.05→tool=0.40 rank=0.27 **other** used_tool=False
  > The query lesion shows some asymmetry and color variation compared to the more uniform reference lesions, suggesting a potential anomaly, but the features are not definitively malignant without expert analysis.
- `D5_0136` L=1 direct=0.08→tool=0.20 rank=0.65 **other** used_tool=False
  > The query image displays features (pigmentation, shape, border) that are within the range of variation observed in the provided normal reference images. No obvious signs of anomaly (like extreme asymmetry, very irregular

**LOSSES**:

- `D5_0032` L=0 direct=0.05→tool=0.95 rank=0.87 **TN_lost_to_FP** used_tool=False
  > The query image exhibits a distinct pink coloration and lacks the brown pigmentation and structural complexity seen in all reference images, indicating a clear deviation from the normal class.
- `D5_0030` L=0 direct=0.05→tool=0.95 rank=0.21 **TN_lost_to_FP** used_tool=False
  > The query image shows a diffuse, reddish lesion that contrasts sharply with the well-defined, brown pigmented nevi in the reference images, indicating a likely anomaly.
- `D5_0099` L=1 direct=0.95→tool=0.10 rank=0.65 **TP_lost_to_FN** used_tool=False
  > The query image displays a pigmented lesion that is relatively symmetric and uniform in color, which are characteristics often associated with benign nevi. In contrast, several reference images exhibit features such as a
- `D5_0155` L=1 direct=0.95→tool=0.10 rank=0.65 **TP_lost_to_FN** used_tool=False
  > The query image shows a pigmented lesion that is visually similar to the normal reference images in terms of color uniformity and lack of highly irregular or chaotic features typically associated with anomalies in this c
- `D5_0176` L=1 direct=0.95→tool=0.10 rank=0.46 **TP_lost_to_FN** used_tool=False
  > The query image exhibits a symmetric, uniformly pigmented lesion with a regular reticular network, matching the characteristics of the normal reference images and lacking the irregular features of the anomalous examples.
- `D5_0115` L=1 direct=0.95→tool=0.10 rank=0.57 **TP_lost_to_FN** used_tool=False
  > The query image displays a lesion with characteristics consistent with the normal reference images, including symmetry and uniform pigmentation. Without access to the hotspot tool and based on visual inspection, the lesi
- `D5_0167` L=1 direct=0.95→tool=0.10 rank=0.48 **TP_lost_to_FN** used_tool=False
  > The query image displays a symmetric, uniformly pigmented lesion with a regular reticular pattern, consistent with benign characteristics observed in the normal reference images.
- `D5_0177` L=1 direct=0.95→tool=0.15 rank=0.27 **TP_lost_to_FN** used_tool=False
  > The query image displays a pigmented lesion with relatively uniform color and a border that, while slightly irregular, is not highly atypical compared to the variety of normal nevi shown in the reference images. There ar
  ... and 10 more losses.

### D5b  (wins 5, losses 7)

Win sample-types: {'FP_corrected': 5}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 4}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5b_0045` L=0 direct=0.98→tool=0.05 rank=0.31 **FP_corrected** used_tool=False
  > The query image displays a normal axial brain MRI slice at the level of the lateral ventricles. The ventricular system appears symmetric and within normal size limits, and there are no visible masses, hemorrhages, or oth
- `D5b_0067` L=0 direct=0.98→tool=0.05 rank=0.53 **FP_corrected** used_tool=False
  > The query image displays normal brain anatomy without any visible anomalies such as tumors, hemorrhages, or significant structural deformities when compared to the provided normal reference images.
- `D5b_0017` L=0 direct=0.98→tool=0.10 rank=0.64 **FP_corrected** used_tool=True
  > The hotspot cropper extracted a region showing normal texture (midline fissure). The tool's interpretation explicitly states that if the attention region shows normal texture, the query should be treated as normal, overr
- `D5b_0031` L=0 direct=0.98→tool=0.10 rank=0.51 **FP_corrected** used_tool=False
  > The query image displays normal brain anatomy consistent with the reference images, with no visible signs of significant pathology or structural defects.
- `D5b_0058` L=0 direct=0.95→tool=0.10 rank=0.52 **FP_corrected** used_tool=False
  > The query image displays a brain MRI slice with anatomical structures (ventricles, sulci, gyri) that are consistent with the provided normal reference images. No obvious pathological features are detected visually.

**LOSSES**:

- `D5b_0072` L=0 direct=0.05→tool=1.00 rank=0.71 **TN_lost_to_FP** used_tool=False
  > The query image is visually distinct from the normal references due to severe blurriness, low resolution, and lack of anatomical detail, indicating a clear anomaly.
- `D5b_0122` L=1 direct=0.98→tool=0.05 rank=0.60 **TP_lost_to_FN** used_tool=False
  > The query image displays a standard brain MRI slice with normal anatomical features and no visible anomalies such as lesions or abnormal signal intensities, consistent with the provided normal reference images.
- `D5b_0068` L=0 direct=0.05→tool=0.95 rank=0.86 **TN_lost_to_FP** used_tool=True
  > The query image is significantly blurred and lacks the anatomical detail present in the normal reference images, indicating a severe anomaly in image quality or acquisition.
- `D5b_0156` L=1 direct=0.98→tool=0.10 rank=0.56 **TP_lost_to_FN** used_tool=False
  > The query image displays a brain MRI slice with anatomical structures (sulci, gyri, ventricles) that are consistent with the provided normal reference images. No obvious anomalies such as masses, significant asymmetry, o
- `D5b_0152` L=1 direct=0.98→tool=0.10 rank=0.78 **TP_lost_to_FN** used_tool=False
  > The query image displays a normal brain MRI slice with typical anatomical structures and no visible abnormalities. The appearance is consistent with healthy brain tissue.
- `D5b_0059` L=0 direct=0.02→tool=0.90 rank=0.50 **TN_lost_to_FP** used_tool=False
  > The query image displays a posterior fossa slice (cerebellum), whereas all reference images display supratentorial slices (cerebrum). This significant anatomical mismatch suggests the query image is anomalous relative to
- `D5b_0160` L=1 direct=0.95→tool=0.10 rank=0.44 **TP_lost_to_FN** used_tool=False
  > The query image displays a normal axial brain MRI slice at the level of the lateral ventricles, which is consistent with the first reference image. No obvious pathological features are detected.

### D5c  (wins 8, losses 12)

Win sample-types: {'FP_corrected': 4, 'FN_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 5, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5c_0131` L=1 direct=0.02→tool=0.95 rank=0.90 **FN_corrected** used_tool=False
  > The query image contains a distinctly different object (small, oval) compared to the consistent kidney-like structures in the reference images, indicating a clear anomaly.
- `D5c_0165` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=False
  > The query image contains a prominent black circular hole in the center of the object, whereas all reference images show solid, continuous textures without such voids.
- `D5c_0100` L=1 direct=0.05→tool=0.95 rank=0.79 **FN_corrected** used_tool=False
  > The query image exhibits a fundamentally different shape (elongated hook) compared to the compact, rounded shapes seen in all normal reference images, indicating a clear anomaly.
- `D5c_0174` L=1 direct=0.05→tool=0.95 rank=0.97 **FN_corrected** used_tool=False
  > The query image contains a tiny, isolated object that is drastically different in scale and morphology compared to the larger, organ-like structures present in all normal reference images.
- `D5c_0035` L=0 direct=0.95→tool=0.10 rank=0.81 **FP_corrected** used_tool=False
  > The query image is visually consistent with three of the four normal reference images, showing a similar small, textured object. The deviation from the second reference image is likely due to natural variation or a diffe
- `D5c_0003` L=0 direct=0.95→tool=0.10 rank=0.97 **FP_corrected** used_tool=False
  > The query image displays a single object with texture and shape characteristics consistent with the smaller objects seen in the normal reference images. There are no obvious visual defects or deviations from the pattern 
- `D5c_0083` L=0 direct=0.95→tool=0.10 rank=1.00 **FP_corrected** used_tool=False
  > The query image displays a single, coherent object that is visually consistent with at least two of the normal reference images (the first and fourth). While some reference images show fragmented objects, the query objec
- `D5c_0070` L=0 direct=0.95→tool=0.10 rank=0.91 **FP_corrected** used_tool=False
  > The query image displays a shape and texture consistent with the smaller, elongated objects in the reference set. While there is variation in the reference images, the query does not exhibit any obvious defects or deviat

**LOSSES**:

- `D5c_0004` L=0 direct=0.02→tool=1.00 rank=0.94 **TN_lost_to_FP** used_tool=False
  > The query image lacks the large, dense point cloud structure present in all normal reference images, showing only a negligible fragment instead.
- `D5c_0042` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=False
  > The query image is anomalous because the object is significantly larger, has an irregular shape, and contains large internal voids, unlike the smaller, solid, and more uniform objects in the reference images.
- `D5c_0061` L=0 direct=0.02→tool=0.95 rank=0.84 **TN_lost_to_FP** used_tool=False
  > The query image exhibits a significant structural deviation from the reference images, characterized by fragmentation and a large internal void, which is not present in the normal samples.
- `D5c_0120` L=1 direct=0.95→tool=0.10 rank=0.96 **TP_lost_to_FN** used_tool=False
  > The query image displays a single, textured object similar to the normal reference images, with no apparent anomalies in shape, texture, or composition.
- `D5c_0107` L=1 direct=0.95→tool=0.10 rank=0.99 **TP_lost_to_FN** used_tool=False
  > The query image displays a shape and texture consistent with the normal reference images, differing mainly in size, which is within the observed variation of the reference set.
- `D5c_0170` L=1 direct=0.95→tool=0.10 rank=0.97 **TP_lost_to_FN** used_tool=False
  > The query image displays a small, textured object similar to those in reference images 1, 3, and 4. No obvious anomalies are detected visually.
- `D5c_0015` L=0 direct=0.02→tool=0.85 rank=0.88 **TN_lost_to_FP** used_tool=False
  > The query image exhibits a distinct irregular shape and texture compared to the reference images, which are more compact and uniform. This structural difference strongly suggests an anomaly.
- `D5c_0102` L=1 direct=0.95→tool=0.15 rank=0.91 **TP_lost_to_FN** used_tool=True
  > The highlighted hotspot region displays a texture consistent with the rest of the object and the reference images, showing no signs of a genuine defect. The disconfirm clause suggests treating such normal texture as evid
  ... and 4 more losses.

### D5d  (wins 5, losses 12)

Win sample-types: {'FP_corrected': 3, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 8, 'other': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5d_0173` L=1 direct=0.02→tool=0.98 rank=0.57 **FN_corrected** used_tool=False
  > The query image contains a dark, solid foreign body obstructing the lumen, which is a clear deviation from the normal anatomical structures seen in the reference images.
- `D5d_0135` L=1 direct=0.02→tool=0.95 rank=0.48 **FN_corrected** used_tool=False
  > The query image contains a clear, dark, raised mass (likely a polyp) in the center of the field of view, which is absent in the normal reference images showing healthy intestinal lining. This distinct structural abnormal
- `D5d_0023` L=0 direct=0.98→tool=0.10 rank=0.39 **FP_corrected** used_tool=False
  > The yellowish patch in the query image appears to be bile staining or residual fluid, which is a common and often normal finding in endoscopic images, similar to the discoloration seen in reference image 2. There are no 
- `D5d_0045` L=0 direct=0.92→tool=0.05 rank=0.40 **FP_corrected** used_tool=False
  > The query image shows healthy, smooth mucosa with normal anatomical folds and no visible lesions, inflammation, or abnormalities, making it consistent with the normal reference images.
- `D5d_0071` L=0 direct=0.95→tool=0.10 rank=0.47 **FP_corrected** used_tool=True
  > The hotspot region shows the scope tip and normal-appearing mucosa. The yellowish area in the query image resembles bile staining seen in normal reference images, and the tool's disconfirm clause indicates that artifacts

**LOSSES**:

- `D5d_0040` L=0 direct=0.02→tool=0.95 rank=0.21 **TN_lost_to_FP** used_tool=False
  > The query image contains a visible endoscope instrument and a yellowish discoloration/fluid accumulation that are absent in all normal reference images, indicating a clear anomaly.
- `D5d_0069` L=0 direct=0.02→tool=0.95 rank=0.36 **TN_lost_to_FP** used_tool=True
  > The query image displays a large, raised, nodular mass on the colonic mucosa, which is a significant deviation from the smooth, folded appearance of the normal reference images. The tool output was an overexposed white p
- `D5d_0170` L=1 direct=0.98→tool=0.10 rank=0.44 **TP_lost_to_FN** used_tool=False
  > The query image displays normal-appearing mucosal folds with smooth texture and uniform coloration, lacking any visible signs of pathology such as lesions, polyps, or inflammation found in the other images.
- `D5d_0146` L=1 direct=0.98→tool=0.10 rank=0.38 **TP_lost_to_FN** used_tool=False
  > The query image displays a normal view of the pylorus with typical mucosal folds and some residual bile/food, which is not an anomaly. The appearance is consistent with a healthy gastrointestinal tract.
- `D5d_0129` L=1 direct=0.98→tool=0.10 rank=0.31 **TP_lost_to_FN** used_tool=True
  > The highlighted hotspot is a shadowed area at the edge of a mucosal fold, which is a common lighting artifact in endoscopy and not a genuine defect. The disconfirm clause in the tool's interpretation supports treating th
- `D5d_0166` L=1 direct=0.98→tool=0.10 rank=0.47 **TP_lost_to_FN** used_tool=False
  > The query image displays healthy colonic mucosa with normal vascular patterns and folds, and the presence of the scope tip is typical for this procedure. It does not exhibit the pathological features seen in the anomalou
- `D5d_0161` L=1 direct=0.98→tool=0.10 rank=0.51 **TP_lost_to_FN** used_tool=True
  > The highlighted region appears to be a lighting artifact or reflection, and the yellow discoloration is consistent with normal bile staining seen in reference images. No genuine defect is observed.
- `D5d_0169` L=1 direct=0.95→tool=0.10 rank=0.40 **TP_lost_to_FN** used_tool=False
  > The query image displays normal colonic mucosa with typical vascular patterns and minor residue, similar to the provided normal reference images. No distinct anomalies such as polyps or lesions are visible.
  ... and 4 more losses.

### D6  (wins 6, losses 15)

Win sample-types: {'FP_corrected': 6}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 11}

**WINS** (item · direct→tool · rank · type · rationale):

- `D6_0000` L=0 direct=0.95→tool=0.05 rank=0.82 **FP_corrected** used_tool=False
  > The query image shows a typical agricultural landscape consistent with the normal reference images, with no visible defects or unusual features.
- `D6_0039` L=0 direct=0.95→tool=0.05 rank=0.85 **FP_corrected** used_tool=False
  > The query image displays a typical rural landscape with a field, road, and small building, consistent with the normal reference images. No distinct anomalies are visible.
- `D6_0015` L=0 direct=0.98→tool=0.10 rank=0.62 **FP_corrected** used_tool=False
  > The query image matches the normal reference images in terms of landscape features and overall appearance, with no evident anomalies detected.
- `D6_0063` L=0 direct=0.98→tool=0.10 rank=0.60 **FP_corrected** used_tool=True
  > The hotspot analysis focused on the road and fields, revealing normal textures and structures consistent with the reference images. No genuine defects or anomalies were found in the high-attention regions.
- `D6_0017` L=0 direct=0.95→tool=0.10 rank=0.75 **FP_corrected** used_tool=False
  > The query image shows a typical suburban landscape with no discernible deviations from the normal reference images. The structures, vegetation, and road patterns are consistent with expected variations in aerial imagery.
- `D6_0064` L=0 direct=0.95→tool=0.10 rank=0.39 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a typical suburban layout with no apparent deviations.

**LOSSES**:

- `D6_0047` L=0 direct=0.02→tool=0.95 rank=0.86 **TN_lost_to_FP** used_tool=False
  > The query image exhibits a significant color anomaly where one half of the field is green while the other is brown, contrasting with the uniform brown fields in the reference images.
- `D6_0027` L=0 direct=0.02→tool=0.95 rank=0.57 **TN_lost_to_FP** used_tool=False
  > The query image contains a prominent bright green pond in the top-left area, which is absent in the normal reference images, indicating a clear visual anomaly.
- `D6_0018` L=0 direct=0.02→tool=0.95 rank=0.55 **TN_lost_to_FP** used_tool=False
  > The query image contains a distinct rectangular area of cleared land or altered vegetation that is not present in the normal reference images, indicating a significant structural anomaly.
- `D6_0117` L=1 direct=0.99→tool=0.10 rank=0.78 **TP_lost_to_FN** used_tool=False
  > The query image displays a typical rural scene with fields, dirt roads, and scattered structures, which is consistent with the rural areas seen in the reference images. No obvious anomalies such as unexpected objects, st
- `D6_0110` L=1 direct=0.98→tool=0.10 rank=0.36 **TP_lost_to_FN** used_tool=False
  > The query image displays a residential area with road networks and building patterns that are highly consistent with the provided normal reference images. No significant visual anomalies are detected upon comparison.
- `D6_0130` L=1 direct=0.98→tool=0.10 rank=0.54 **TP_lost_to_FN** used_tool=False
  > The query image matches the normal reference images in structure and content, with no visible anomalies detected.
- `D6_0149` L=1 direct=0.98→tool=0.10 rank=0.55 **TP_lost_to_FN** used_tool=True
  > The hotspot region extracted by the tool shows a normal residential street scene with houses and trees, which aligns with the 'benign edge' or 'normal texture' disconfirm clause. Therefore, despite the initial difference
- `D6_0106` L=1 direct=0.98→tool=0.10 rank=0.64 **TP_lost_to_FN** used_tool=False
  > The query image displays typical features of a rural/industrial area with no clear deviations from normal patterns. The differences from reference images are likely due to location variation rather than anomalies.
  ... and 7 more losses.

### D7  (wins 2, losses 1)

Win sample-types: {'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D7_0159` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=False
  > The query image depicts a rural scene with a small car towing a trailer, whereas all reference images show urban/suburban street views from a standard vehicle dashboard. This fundamental difference in scene context and v
- `D7_0135` L=1 direct=0.02→tool=0.95 rank=0.97 **FN_corrected** used_tool=False
  > The query image depicts a tourist scene with a horse-drawn carriage in a square, whereas all reference images show standard car-centric street views. This fundamental difference in scene content and context indicates the

**LOSSES**:

- `D7_0086` L=0 direct=0.02→tool=0.95 rank=0.67 **TN_lost_to_FP** used_tool=False
  > The query image depicts a night-time highway, which is visually inconsistent with the four reference images that all show daytime urban or suburban driving scenes. This significant difference in lighting and setting clas

### D8  (wins 6, losses 7)

Win sample-types: {'FN_corrected': 6}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 4}

**WINS** (item · direct→tool · rank · type · rationale):

- `D8_0107` L=1 direct=0.02→tool=0.95 rank=0.50 **FN_corrected** used_tool=False
  > The query image contains a person in a uniform (security/police), which is a distinct deviation from the civilians seen in all normal reference images. This constitutes a clear visual anomaly.
- `D8_0159` L=1 direct=0.02→tool=0.95 rank=0.50 **FN_corrected** used_tool=False
  > The query image contains a uniformed individual (security/police) which is a significant deviation from the civilian subjects seen in all normal reference images, indicating a clear anomaly.
- `D8_0130` L=1 direct=0.02→tool=0.95 rank=0.50 **FN_corrected** used_tool=False
  > The query image contains a uniformed individual (likely security or police) walking in the foreground, which is a significant deviation from the reference images that only show civilians in casual clothing. This presence
- `D8_0168` L=1 direct=0.05→tool=0.95 rank=0.50 **FN_corrected** used_tool=False
  > The query image contains a person in a uniform (security/police) walking in the center, which is a significant deviation from the reference images that show only civilians or no one in that specific location. This consti
- `D8_0175` L=1 direct=0.02→tool=0.90 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a person in a uniform, which is a significant deviation from the reference images that only show civilians in casual clothing. This suggests an anomalous event or presence.
- `D8_0115` L=1 direct=0.05→tool=0.85 rank=0.50 **FN_corrected** used_tool=False
  > The query image contains a uniformed individual (security/police) which is a significant deviation from the reference images that only show civilians in casual clothing, indicating an anomalous event or presence.

**LOSSES**:

- `D8_0014` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=False
  > The query image contains a uniformed individual, which is a significant deviation from the pattern of civilians seen in all four normal reference images, indicating a high probability of anomaly.
- `D8_0009` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed security or police officer, which is a distinct deviation from the normal reference images that only feature civilians in casual attire. This presence of a uniformed individual is the
- `D8_0050` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=False
  > The query image contains a uniformed officer walking in the foreground, which is a distinct visual deviation from the reference images that only show civilians. This suggests an anomalous event or object presence.
- `D8_0138` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The scene depicts normal pedestrian activity in a public area, consistent with the reference images. No visual anomalies are detected.
- `D8_0126` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The query image depicts normal pedestrian activity with a uniformed person walking through what appears to be a public building entrance. No anomalous objects, behaviors, or safety concerns are visible. The scene is cons
- `D8_0119` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The query image depicts a person in motion (possibly jumping) which is a normal human activity in a public space. While the specific pose is unique compared to the static or walking poses in reference images, it does not
- `D8_0179` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The query image depicts a typical scene at a public station entrance with people moving and standing, consistent with the normal reference images. No visual anomalies are detected.

### D9  (wins 8, losses 10)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 2, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 6, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D9_0121` L=1 direct=0.01→tool=1.00 rank=0.58 **FN_corrected** used_tool=False
  > The query image contains a cherry label and red liquid, whereas all normal reference images contain banana labels and light-colored liquid. This deviation in both label content and liquid appearance confirms the image is
- `D9_0168` L=1 direct=0.01→tool=1.00 rank=0.73 **FN_corrected** used_tool=False
  > The query image is anomalous because the liquid color (red) and label icon (cherry) differ significantly from the normal reference images (light liquid, banana icon).
- `D9_0057` L=0 direct=0.99→tool=0.05 rank=0.35 **FP_corrected** used_tool=False
  > The query image matches the normal reference images (specifically images 1, 2, and 4) in terms of object type, color, and arrangement. No anomalies are detected.
- `D9_0022` L=0 direct=0.99→tool=0.05 rank=0.28 **FP_corrected** used_tool=False
  > The query image displays a standard configuration of connectors and a cable on a mesh background, matching the patterns seen in the normal reference images. No anomalies are detected.
- `D9_0078` L=0 direct=0.99→tool=0.05 rank=0.11 **FP_corrected** used_tool=False
  > The query image matches the pattern of normal single-wire configurations seen in the reference images. No anomalies are detected.
- `D9_0039` L=0 direct=0.98→tool=0.05 rank=0.05 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard arrangement of healthy food items in a lunchbox with no detectable anomalies.
- `D9_0079` L=0 direct=0.98→tool=0.05 rank=0.16 **FP_corrected** used_tool=False
  > The query image contains the same types and counts of hardware (2 bolts, 2 nuts, 2 washers) as the reference images. The arrangement varies naturally as expected for loose parts in a bag. No missing, extra, or damaged it
- `D9_0174` L=1 direct=0.02→tool=0.15 rank=0.25 **other** used_tool=False
  > The query image shows 2 bolts, 2 nuts, and 2 washers in a plastic bag, which appears consistent with the normal reference images that also show similar hardware components. The arrangement and components look typical for

**LOSSES**:

- `D9_0047` L=0 direct=0.02→tool=1.00 rank=0.13 **TN_lost_to_FP** used_tool=False
  > The query image displays a cherry-labeled bottle with red liquid, whereas all normal references are banana-labeled with light liquid. This fundamental difference in product type confirms the query is anomalous.
- `D9_0032` L=0 direct=0.02→tool=1.00 rank=0.07 **TN_lost_to_FP** used_tool=False
  > The query image is anomalous because the liquid color (red) and label icon (cherry) differ significantly from the normal reference images (white liquid, banana icon).
- `D9_0176` L=1 direct=0.99→tool=0.05 rank=0.31 **TP_lost_to_FN** used_tool=False
  > The query image displays a standard jumper wire configuration similar to the provided normal reference images. There are no visible anomalies such as broken wires, missing connectors, or unexpected objects.
- `D9_0041` L=0 direct=0.02→tool=0.95 rank=0.79 **TN_lost_to_FP** used_tool=False
  > The query image contains a red liquid with a cherry label, whereas all reference images contain light-colored liquids with banana or orange labels. This clear deviation in both liquid color and label content indicates th
- `D9_0129` L=1 direct=0.98→tool=0.05 rank=0.04 **TP_lost_to_FN** used_tool=False
  > The query image displays a standard arrangement of food items (oranges, peach, granola, banana chips, almonds) in a compartmentalized container, matching the content and layout of the normal reference images. No anomalie
- `D9_0128` L=1 direct=0.99→tool=0.10 rank=0.24 **TP_lost_to_FN** used_tool=False
  > The query image displays a standard single-wire connection similar to one of the reference images. There are no visible defects, misalignments, or unexpected components that would indicate an anomaly.
- `D9_0157` L=1 direct=0.99→tool=0.10 rank=0.48 **TP_lost_to_FN** used_tool=False
  > The query image shows a standard cable connection similar to the normal reference images. The cable is intact, properly connected to both terminal blocks, and there are no visible defects, breaks, or unusual features tha
- `D9_0100` L=1 direct=0.99→tool=0.10 rank=0.41 **TP_lost_to_FN** used_tool=False
  > The query image matches the normal reference image with a single yellow wire and two connectors. There are no visible defects, misalignments, or unexpected elements.
  ... and 2 more losses.

---

## tool_image_diff  (58 wins, 95 losses, net flips -32 on n=480)

### D1  (wins 7, losses 4)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 1, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D1_0038` L=0 direct=0.98→tool=0.05 rank=0.26 **FP_corrected** used_tool=True
  > The query image matches the majority of reference images, displaying the 'actavis' logo and '500' text. The difference observed against reference 3 is due to the presence of the logo, which is a normal feature in the oth
- `D1_0064` L=0 direct=0.98→tool=0.05 rank=0.24 **FP_corrected** used_tool=True
  > The query image matches the majority of reference images (0, 1, 2) which include the 'actavis' logo. The difference with reference 3 is due to the missing logo in that reference, not an anomaly in the query.
- `D1_0114` L=1 direct=0.02→tool=0.95 rank=0.19 **FN_corrected** used_tool=False
  > The query image displays a brush with yellow and white bristles, whereas all provided normal reference images show brushes with either blue/white or red/white bristles. This significant color deviation from the establish
- `D1_0084` L=0 direct=0.95→tool=0.05 rank=0.02 **FP_corrected** used_tool=False
  > The query image exhibits the same speckled texture pattern as the reference images with no visible defects or anomalies.
- `D1_0088` L=0 direct=0.95→tool=0.05 rank=0.29 **FP_corrected** used_tool=False
  > Visual inspection confirms the query image matches the reference images in component type, orientation, and PCB layout. No defects or anomalies are visible.
- `D1_0009` L=0 direct=0.95→tool=0.15 rank=0.13 **FP_corrected** used_tool=True
  > Despite high pixel differences detected by the tool, the visual appearance of the query image matches the reference images closely. The differences are attributed to lighting variations rather than actual anomalies, as w
- `D1_0174` L=1 direct=0.02→tool=0.15 rank=0.15 **other** used_tool=True
  > The pixel differences are consistent across references and likely due to lighting/position variation rather than actual defects. The component appears structurally normal.

**LOSSES**:

- `D1_0008` L=0 direct=0.02→tool=0.95 rank=0.12 **TN_lost_to_FP** used_tool=False
  > The query image displays a brush with yellow and white bristles, whereas all reference images show brushes with either blue/white or red/white bristles. This significant color deviation from the reference set indicates a
- `D1_0094` L=1 direct=0.98→tool=0.05 rank=0.77 **TP_lost_to_FN** used_tool=True
  > The observed pixel differences are attributed to benign lighting or focus variations as indicated by the tool's disconfirm clause, and the capsule visually matches the normal references.
- `D1_0111` L=1 direct=0.98→tool=0.05 rank=0.77 **TP_lost_to_FN** used_tool=True
  > The pixel diff tool was unreliable due to misalignment. Visual inspection shows the query image has a normal, consistent fabric texture with no visible anomalies.
- `D1_0179` L=1 direct=0.95→tool=0.15 rank=0.54 **TP_lost_to_FN** used_tool=True
  > The pixel differences are consistent across multiple references (~21%) and scattered throughout the image, indicating benign lighting/positioning variations rather than a true defect. No localized anomaly is visible in t

### D10  (wins 2, losses 4)

Win sample-types: {'FP_corrected': 2}
Loss sample-types: {'TP_lost_to_FN': 3, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D10_0076` L=0 direct=0.98→tool=0.05 rank=0.12 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard HC-SR04 module with no apparent anomalies.
- `D10_0002` L=0 direct=0.95→tool=0.10 rank=0.07 **FP_corrected** used_tool=True
  > The detected differences are likely due to benign lighting variations as suggested by the tool's disconfirm clause, and no obvious physical anomalies are visible in the query image compared to the references.

**LOSSES**:

- `D10_0097` L=1 direct=0.99→tool=0.05 rank=0.34 **TP_lost_to_FN** used_tool=True
  > The query image is a mirror image of the reference images, causing a high pixel difference score. However, the physical components and traces appear intact and correctly placed relative to the mirrored layout, indicating
- `D10_0136` L=1 direct=0.98→tool=0.10 rank=0.23 **TP_lost_to_FN** used_tool=True
  > The high pixel difference percentages are attributed to global lighting and imaging variations rather than physical defects, as indicated by the noisy diff masks and the disconfirm clause. The query image appears structu
- `D10_0139` L=1 direct=0.98→tool=0.20 rank=0.20 **TP_lost_to_FN** used_tool=True
  > The pixel differences are likely due to normal variations in object positioning and lighting rather than actual defects. All four objects appear structurally similar to the reference images with no obvious anomalies.
- `D10_0069` L=0 direct=0.02→tool=0.15 rank=0.27 **other** used_tool=True
  > The observed pixel differences are small and likely due to benign variations like lighting or slight rotation, not a true defect.

### D2  (wins 4, losses 12)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 5, 'TP_lost_to_FN': 7}

**WINS** (item · direct→tool · rank · type · rationale):

- `D2_0095` L=1 direct=0.02→tool=1.00 rank=0.86 **FN_corrected** used_tool=False
  > The query image shows a bottle filled with dark liquid, which is a significant deviation from the reference images that show the bottle with a white label and no dark liquid.
- `D2_0092` L=1 direct=0.01→tool=0.95 rank=0.63 **FN_corrected** used_tool=False
  > The query image contains an additional object (plastic straw wrapper) not present in any of the normal reference images, indicating a clear anomaly in the product presentation.
- `D2_0037` L=0 direct=0.98→tool=0.10 rank=0.19 **FP_corrected** used_tool=False
  > The query image shows the back of a normal snack package with standard labeling, barcode, and nutritional information. The difference from reference images (which show the front) is expected for product photography and d
- `D2_0145` L=1 direct=0.02→tool=0.15 rank=0.71 **other** used_tool=True
  > The query image is a normal cigarette pack variant with Chinese text matching reference 2's style. The pixel differences from references 0 and 1 are due to different text content (product variants), not anomalies.

**LOSSES**:

- `D2_0056` L=0 direct=0.01→tool=1.00 rank=0.05 **TN_lost_to_FP** used_tool=False
  > The query image displays a different product packaging design than the normal reference images, indicating an anomaly.
- `D2_0087` L=0 direct=0.01→tool=1.00 rank=0.08 **TN_lost_to_FP** used_tool=True
  > The query image is upside down compared to the normal reference images, which is a clear structural anomaly confirmed by the high pixel difference and reliable alignment from the tool.
- `D2_0080` L=0 direct=0.02→tool=1.00 rank=0.02 **TN_lost_to_FP** used_tool=False
  > The query image displays the back of the product packaging, whereas the reference images consistently show the front. This represents a significant deviation from the established normal pattern.
- `D2_0169` L=1 direct=0.98→tool=0.00 rank=0.83 **TP_lost_to_FN** used_tool=False
  > The query image displays the back of the cigarette pack, whereas the reference images display the front. This is a normal variation in viewing angle/side of the object, not an anomaly.
- `D2_0038` L=0 direct=0.01→tool=0.95 rank=0.62 **TN_lost_to_FP** used_tool=True
  > The query image shows the product box upside down compared to the normal reference images (e.g., barcode and QR code are at the top instead of the bottom). This orientation is a clear anomaly.
- `D2_0089` L=0 direct=0.01→tool=0.95 rank=0.16 **TN_lost_to_FP** used_tool=False
  > The query image displays the front branding of the can, whereas all reference images display the back/side with nutritional information. This represents a fundamental difference in the object's orientation and content re
- `D2_0170` L=1 direct=0.98→tool=0.05 rank=0.13 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images showing the front of the package. No anomalies such as tears, discoloration, or missing text are visible.
- `D2_0097` L=1 direct=0.98→tool=0.05 rank=0.73 **TP_lost_to_FN** used_tool=True
  > The query image shows a standard front view of a milk carton. The reference images show the back of the carton, making pixel-based comparison invalid for defect detection. Visually, the query image shows no signs of dama
  ... and 4 more losses.

### D4  (wins 4, losses 10)

Win sample-types: {'FN_corrected': 3, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 5, 'other': 4}

**WINS** (item · direct→tool · rank · type · rationale):

- `D4_0176` L=1 direct=0.05→tool=0.95 rank=0.82 **FN_corrected** used_tool=False
  > The query image displays a coarse, rocky terrain with large distinct stones, whereas all reference images show a consistent, fine-grained, uniform surface texture. This fundamental difference in texture and content indic
- `D4_0115` L=1 direct=0.05→tool=0.95 rank=0.12 **FN_corrected** used_tool=False
  > The query image contains a large, dark shadow that is absent in all normal reference images, indicating a significant deviation from the expected appearance.
- `D4_0105` L=1 direct=0.05→tool=0.95 rank=0.06 **FN_corrected** used_tool=False
  > The query image contains a large, dark shadow that is absent in all normal reference images, indicating a significant deviation from the expected appearance.
- `D4_0110` L=1 direct=0.05→tool=0.20 rank=0.70 **other** used_tool=True
  > The high pixel difference is likely due to lighting or texture variation as warned by the tool's disconfirm clause, and the diff mask does not show a clear, localized defect.

**LOSSES**:

- `D4_0075` L=0 direct=0.02→tool=0.95 rank=0.01 **TN_lost_to_FP** used_tool=False
  > The query image exhibits a distinctly different texture and color palette compared to all provided normal reference images, indicating a clear deviation from the expected normal pattern.
- `D4_0126` L=1 direct=0.95→tool=0.10 rank=0.63 **TP_lost_to_FN** used_tool=True
  > The pixel difference detected by the tool is likely due to natural texture variations and lighting differences common in such surfaces, as warned by the tool's disconfirm clause. No distinct structural anomaly is visible
- `D4_0106` L=1 direct=0.95→tool=0.10 rank=0.49 **TP_lost_to_FN** used_tool=True
  > The pixel differences are minimal and the tool's interpretation explicitly states that such changes can be benign lighting variations. The query image appears to be the same textured surface as the references, just with 
- `D4_0128` L=1 direct=0.95→tool=0.10 rank=0.42 **TP_lost_to_FN** used_tool=True
  > The query image features (dark spots and patches) are consistent with the normal variation seen in the reference images. Pixel diffs are unreliable for this random texture and likely reflect benign variations.
- `D4_0155` L=1 direct=0.95→tool=0.15 rank=0.50 **TP_lost_to_FN** used_tool=True
  > Despite high pixel difference scores, the visual features in the query image (pits, small dark spots) are consistent with the natural texture variations seen in the normal reference images (especially refs 2 and 3). The 
- `D4_0130` L=1 direct=0.95→tool=0.20 rank=0.57 **TP_lost_to_FN** used_tool=True
  > The image diff tool reported unreliable alignment, so its high difference score is noise. Visually, the query image's texture and the small dark spot are consistent with natural variations seen in the reference images, s
- `D4_0042` L=0 direct=0.02→tool=0.20 rank=0.14 **other** used_tool=True
  > Tool output marked as unreliable due to misalignment; visual differences between query and references likely represent different normal material samples rather than defects.
- `D4_0021` L=0 direct=0.05→tool=0.20 rank=0.52 **other** used_tool=True
  > The pixel differences are relatively low (1.8% and 5.4%), and the tool interpretation suggests these could be benign variations. The query image's texture and features appear consistent with the natural variation seen ac
  ... and 2 more losses.

### D5  (wins 4, losses 11)

Win sample-types: {'FN_corrected': 2, 'other': 2}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 6, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5_0104` L=1 direct=0.05→tool=0.85 rank=0.42 **FN_corrected** used_tool=True
  > The query image displays a distinct pattern of multiple dark dots/globules, which is morphologically different from the uniform or reticular patterns in the normal reference images. High pixel difference scores (25% and 
- `D5_0166` L=1 direct=0.05→tool=0.85 rank=0.31 **FN_corrected** used_tool=True
  > The pixel diff tool was unreliable due to misalignment. Visually, the query image shows a dark, asymmetric pigmented lesion that is morphologically and chromatically distinct from all four reference images (which show li
- `D5_0119` L=1 direct=0.05→tool=0.20 rank=0.32 **other** used_tool=True
  > The image diff tool was unreliable due to misalignment. Visually, while the lesion has some irregular features, the lack of a valid comparison and the tool's warning suggest it is likely a normal variation rather than a 
- `D5_0136` L=1 direct=0.08→tool=0.20 rank=0.65 **other** used_tool=True
  > The pixel differences are likely due to benign variations in lighting, color, or natural lesion morphology rather than a true anomaly, as cautioned by the tool's disconfirm clause.

**LOSSES**:

- `D5_0030` L=0 direct=0.05→tool=0.95 rank=0.21 **TN_lost_to_FP** used_tool=False
  > The query image displays a large, diffuse erythematous/purpuric patch, which is visually distinct from the well-circumscribed, pigmented melanocytic lesions (moles) present in all four reference images. The difference in
- `D5_0032` L=0 direct=0.05→tool=0.90 rank=0.87 **TN_lost_to_FP** used_tool=False
  > The query image exhibits a distinct color (pink vs. brown) and texture (homogeneous vs. reticular/pigmented network) compared to all reference images, indicating a significant deviation from the normal class.
- `D5_0112` L=1 direct=0.95→tool=0.10 rank=0.75 **TP_lost_to_FN** used_tool=True
  > The image diff tool returned an unreliable alignment flag, indicating the high pixel difference is due to misalignment rather than an anomaly. Following the tool's disconfirm clause, the query is considered normal.
- `D5_0172` L=1 direct=0.95→tool=0.10 rank=0.49 **TP_lost_to_FN** used_tool=True
  > The image diff tool returned an unreliable alignment flag, indicating the high difference is due to misalignment rather than a defect. The tool's interpretation explicitly states to ignore the signal and suggests the que
- `D5_0158` L=1 direct=0.95→tool=0.10 rank=0.35 **TP_lost_to_FN** used_tool=True
  > The pixel diff tool was unreliable due to misalignment. Visual inspection shows the query lesion is a uniform brown macule, consistent with benign variations seen in the reference set, and lacks the chaotic asymmetry or 
- `D5_0066` L=0 direct=0.05→tool=0.85 rank=0.83 **TN_lost_to_FP** used_tool=True
  > The query image shows a lesion with irregular borders and color variegation, differing significantly from the more uniform reference lesions. The first reliable pixel diff comparison confirmed substantial differences, su
- `D5_0167` L=1 direct=0.95→tool=0.15 rank=0.48 **TP_lost_to_FN** used_tool=True
  > The pixel diff tool was unreliable due to misalignment. Visually, the query lesion resembles the normal references (especially ref0 and ref2) more than it deviates into the highly irregular pattern of ref3, suggesting it
- `D5_0051` L=0 direct=0.05→tool=0.80 rank=0.46 **TN_lost_to_FP** used_tool=False
  > The query lesion is significantly smaller, darker, and more symmetric compared to the larger, more irregular, and lighter-colored lesions in the reference set. This distinct morphological difference suggests it is anomal
  ... and 3 more losses.

### D5b  (wins 5, losses 5)

Win sample-types: {'FP_corrected': 5}
Loss sample-types: {'TP_lost_to_FN': 2, 'TN_lost_to_FP': 2, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5b_0015` L=0 direct=0.98→tool=0.10 rank=0.56 **FP_corrected** used_tool=False
  > The query image appears to be a normal axial MRI slice of the brain. The differences from the reference images are due to different anatomical levels (slice positions) and possibly different MRI sequences, not pathologic
- `D5b_0045` L=0 direct=0.98→tool=0.10 rank=0.31 **FP_corrected** used_tool=False
  > The query image appears to be a normal brain MRI slice showing typical ventricular anatomy. The differences from reference images are due to different slice levels rather than pathological anomalies.
- `D5b_0067` L=0 direct=0.98→tool=0.10 rank=0.53 **FP_corrected** used_tool=False
  > The query image appears to be a normal axial brain MRI slice showing the lateral ventricles. It is structurally consistent with Reference Image 0, which shows a similar anatomical level. There are no obvious signs of gro
- `D5b_0031` L=0 direct=0.98→tool=0.10 rank=0.51 **FP_corrected** used_tool=True
  > The high pixel differences are attributed to global color/contrast variations (different MRI sequence or post-processing) rather than structural anomalies. The anatomical features in the query image appear normal and con
- `D5b_0058` L=0 direct=0.95→tool=0.10 rank=0.52 **FP_corrected** used_tool=False
  > The query image shows a brain MRI slice that is structurally consistent with the reference images, likely representing a different axial slice level rather than an anomaly. The variations in ventricle shape and size are 

**LOSSES**:

- `D5b_0068` L=0 direct=0.05→tool=0.95 rank=0.86 **TN_lost_to_FP** used_tool=True
  > The query image is significantly blurred and lacks the anatomical detail present in the reference images. The high pixel difference percentage confirms this discrepancy, indicating a severe image quality anomaly.
- `D5b_0072` L=0 direct=0.05→tool=0.95 rank=0.71 **TN_lost_to_FP** used_tool=True
  > The query image is visually distinct from all reference images, appearing extremely dark, low-resolution, and potentially a different slice or modality. While the diff tool flagged a high change percentage, the disconfir
- `D5b_0156` L=1 direct=0.98→tool=0.10 rank=0.56 **TP_lost_to_FN** used_tool=False
  > The query image is a normal brain MRI slice at a different anatomical level than the reference images. The differences are due to slice position rather than pathology. No obvious anomalies are visible in the query image 
- `D5b_0160` L=1 direct=0.95→tool=0.10 rank=0.44 **TP_lost_to_FN** used_tool=True
  > The query image shows a normal brain MRI slice at a different anatomical level than the references. The high pixel differences are due to normal anatomical variation between slice levels, not an anomaly.
- `D5b_0050` L=0 direct=0.02→tool=0.15 rank=0.49 **other** used_tool=True
  > The query image shows a normal brain MRI slice with typical anatomical structures. The pixel differences from references are explained by different slice levels and potential lighting variations, not pathological anomali

### D5c  (wins 5, losses 8)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 4}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5c_0131` L=1 direct=0.02→tool=0.98 rank=0.90 **FN_corrected** used_tool=False
  > The query image contains a fundamentally different object (small oval) compared to the consistent kidney-shaped structures in all reference images, indicating a severe anomaly.
- `D5c_0174` L=1 direct=0.05→tool=1.00 rank=0.97 **FN_corrected** used_tool=False
  > The query image contains a tiny object that is completely different in shape and size from the large stomach-like structures present in all reference images, indicating a severe anomaly.
- `D5c_0165` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=False
  > The query image displays a significantly larger and more complex object with a prominent hole, whereas all reference images show small, solid, and simpler shapes. This clear deviation in morphology and the presence of a 
- `D5c_0100` L=1 direct=0.05→tool=0.95 rank=0.79 **FN_corrected** used_tool=True
  > The query image displays a fundamentally different object structure and position compared to the reference images, indicating a clear anomaly rather than benign variation.
- `D5c_0035` L=0 direct=0.95→tool=0.10 rank=0.81 **FP_corrected** used_tool=False
  > The query image is visually consistent with the majority of the normal reference images (0, 2, 3, 4), showing a small, similarly shaped object in the same location. Reference 1 appears to be an outlier or a different cla

**LOSSES**:

- `D5c_0004` L=0 direct=0.02→tool=0.98 rank=0.94 **TN_lost_to_FP** used_tool=False
  > The query image contains a significantly smaller and less defined object compared to the large, textured objects in all reference images, indicating a clear anomaly.
- `D5c_0042` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=False
  > The query image contains a significantly larger object with prominent dark voids (holes) that are absent in the normal reference images, which show smaller, solid-looking objects. This structural difference indicates an 
- `D5c_0015` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=False
  > The query image displays a significantly larger and morphologically different object compared to the small, consistent shapes in the reference images, indicating a clear anomaly.
- `D5c_0061` L=0 direct=0.02→tool=0.95 rank=0.84 **TN_lost_to_FP** used_tool=False
  > The query image exhibits a significantly different morphology (complex, multi-part structure with a large internal void) compared to the simpler, more solid shapes seen in all four reference images, indicating a clear an
- `D5c_0102` L=1 direct=0.95→tool=0.10 rank=0.91 **TP_lost_to_FN** used_tool=False
  > All images show similar textured objects against black background, but with different shapes and orientations. The query image shows a shape consistent with the variation seen in reference images, suggesting normal varia
- `D5c_0170` L=1 direct=0.95→tool=0.10 rank=0.97 **TP_lost_to_FN** used_tool=False
  > The query image displays an object consistent in texture and style with the reference images. The differences in size and position appear to be normal variations rather than anomalies, as seen in the diverse reference se
- `D5c_0107` L=1 direct=0.95→tool=0.15 rank=0.99 **TP_lost_to_FN** used_tool=True
  > The query image shows a shape similar to the normal references, with only minor size/orientation differences. The tool interpretations explicitly suggest these variations are benign and the query is likely normal.
- `D5c_0159` L=1 direct=0.95→tool=0.20 rank=0.95 **TP_lost_to_FN** used_tool=True
  > The query image is visually very similar to reference image 0, both showing a textured object with a dark internal region. The pixel difference of 5.6% is likely due to minor variations in the dark region's shape or posi

### D5d  (wins 6, losses 9)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 4, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5d_0173` L=1 direct=0.02→tool=0.95 rank=0.57 **FN_corrected** used_tool=False
  > The query image contains a prominent dark foreign object in the center of the lumen, which is a clear anomaly compared to the normal mucosal tissue seen in the reference images.
- `D5d_0135` L=1 direct=0.02→tool=0.95 rank=0.48 **FN_corrected** used_tool=False
  > The query image contains a prominent dark foreign object in the center of the lumen, which is a clear deviation from the normal mucosal appearance seen in the reference images. This object is not a natural anatomical fea
- `D5d_0150` L=1 direct=0.02→tool=0.95 rank=0.59 **FN_corrected** used_tool=True
  > The tool output was flagged as unreliable due to misalignment. Visual inspection confirms the presence of a distinct polypoid lesion in the query image, which is a clear anomaly compared to the normal mucosal folds in th
- `D5d_0128` L=1 direct=0.02→tool=0.95 rank=0.35 **FN_corrected** used_tool=True
  > The tool was unreliable due to misalignment. Visual inspection confirms the query image contains a prominent polypoid mass, which is a clear anomaly compared to the normal mucosal surfaces in the reference images.
- `D5d_0023` L=0 direct=0.98→tool=0.10 rank=0.39 **FP_corrected** used_tool=True
  > The tool output was unreliable due to misalignment. Visual inspection reveals the query image contains only a small amount of benign yellow fluid, which is a common variation and not an anomaly.
- `D5d_0045` L=0 direct=0.92→tool=0.10 rank=0.40 **FP_corrected** used_tool=False
  > The query image displays normal-appearing gastrointestinal mucosa with smooth folds and no obvious lesions, ulcers, or abnormal growths. The visual characteristics are consistent with the healthy tissue seen in the refer

**LOSSES**:

- `D5d_0069` L=0 direct=0.02→tool=0.95 rank=0.36 **TN_lost_to_FP** used_tool=False
  > The query image contains a clear polypoid lesion (a raised, nodular mass) which is a pathological anomaly. The reference images display normal anatomical features (pylorus, folds, junctions) without such lesions. The too
- `D5d_0065` L=0 direct=0.02→tool=0.95 rank=0.32 **TN_lost_to_FP** used_tool=True
  > The query image contains a prominent polypoid lesion, which is a structural anomaly absent in the normal reference images. The high pixel difference score confirms this structural discrepancy.
- `D5d_0075` L=0 direct=0.02→tool=0.95 rank=0.64 **TN_lost_to_FP** used_tool=False
  > The query image shows a flat mucosal surface with a different texture and lack of prominent folds compared to the reference images, which clearly display folded anatomy and endoscope presence. This structural discrepancy
- `D5d_0042` L=0 direct=0.02→tool=0.95 rank=0.36 **TN_lost_to_FP** used_tool=True
  > The query image displays a distinct dark, irregular lesion in the lumen, which is a clear structural anomaly compared to the healthy mucosa in the reference images. The reliable pixel diff from the first reference confir
- `D5d_0129` L=1 direct=0.98→tool=0.10 rank=0.31 **TP_lost_to_FN** used_tool=False
  > The query image displays normal endoscopic appearance with smooth mucosal surface and minor fluid residue, consistent with the normal reference images. No obvious pathological features are present.
- `D5d_0161` L=1 direct=0.98→tool=0.10 rank=0.51 **TP_lost_to_FN** used_tool=True
  > The pixel diff tool was unreliable due to misalignment. Visual inspection shows the yellowish fluid in the query image is also present in reference image 3, indicating it is a normal finding rather than an anomaly.
- `D5d_0166` L=1 direct=0.98→tool=0.10 rank=0.47 **TP_lost_to_FN** used_tool=True
  > The image diff tool flagged unreliable alignment, so its output was ignored. Visually, the query image shows a standard endoscopic view with an instrument, and the tissue texture appears consistent with normal anatomy, l
- `D5d_0093` L=1 direct=0.92→tool=0.10 rank=0.30 **TP_lost_to_FN** used_tool=True
  > The image diff tool was unreliable due to misalignment. Visual inspection shows the query image contains typical endoscopic features (mucosa, fluid) consistent with the reference set, suggesting it is normal.
  ... and 1 more losses.

### D6  (wins 7, losses 19)

Win sample-types: {'FP_corrected': 7}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 15, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D6_0035` L=0 direct=0.98→tool=0.10 rank=0.64 **FP_corrected** used_tool=True
  > The tool indicated unreliable alignment, meaning the large differences are due to misalignment or temporal changes, not an anomaly. The query image appears to be a normal variation of the scene.
- `D6_0063` L=0 direct=0.98→tool=0.10 rank=0.60 **FP_corrected** used_tool=True
  > The image diff tool flagged unreliable alignment, meaning the observed differences are artifacts of misalignment, not anomalies. Visual inspection confirms the scene is consistent with the references.
- `D6_0017` L=0 direct=0.95→tool=0.10 rank=0.75 **FP_corrected** used_tool=True
  > The pixel diff tool was unreliable due to misalignment. Visual inspection shows the query image is a standard aerial view consistent with the reference images, with no obvious anomalies.
- `D6_0064` L=0 direct=0.95→tool=0.10 rank=0.39 **FP_corrected** used_tool=True
  > The image diff tool flagged unreliable alignment, meaning the high difference values are due to misalignment rather than actual anomalies. Visual inspection shows the query image is consistent with the reference images o
- `D6_0015` L=0 direct=0.98→tool=0.15 rank=0.62 **FP_corrected** used_tool=True
  > The pixel differences detected are likely due to benign lighting or color variations rather than structural anomalies, as indicated by the scattered nature of the diff mask and the tool's disconfirm clause warning.
- `D6_0039` L=0 direct=0.95→tool=0.15 rank=0.85 **FP_corrected** used_tool=True
  > The pixel differences detected are likely due to benign lighting or texture variations rather than structural anomalies, as indicated by the tool's disconfirm clause and the scattered nature of the diff mask.
- `D6_0000` L=0 direct=0.95→tool=0.25 rank=0.82 **FP_corrected** used_tool=True
  > The 13% pixel difference likely represents normal variation in agricultural fields (soil moisture, vegetation growth, lighting conditions) rather than a true anomaly, as indicated by the tool's disconfirm clause about be

**LOSSES**:

- `D6_0144` L=1 direct=1.00→tool=0.00 rank=0.98 **TP_lost_to_FN** used_tool=False
  > The query image is a natural field scene, whereas the references are urban/suburban layouts. Since there is no spatial alignment or shared context, the query cannot be considered anomalous relative to the references in a
- `D6_0024` L=0 direct=0.02→tool=0.95 rank=0.71 **TN_lost_to_FP** used_tool=True
  > Despite tool failures, the query image clearly shows a large, irregular light-colored patch in the field that is absent in the uniform dark reference images, indicating a significant anomaly in land condition or use.
- `D6_0145` L=1 direct=0.95→tool=0.05 rank=0.65 **TP_lost_to_FN** used_tool=True
  > The pixel diff tool flagged unreliable alignment due to significant scene changes (likely seasonal), and the interpretation advises treating the query as normal. Visual inspection confirms the scene structure is consiste
- `D6_0149` L=1 direct=0.98→tool=0.10 rank=0.55 **TP_lost_to_FN** used_tool=True
  > The pixel diff tool flagged unreliable alignment, meaning the high difference is due to scene mismatch (different land use) rather than an anomaly. The query image shows a consistent, normal aerial view of an undeveloped
- `D6_0110` L=1 direct=0.98→tool=0.10 rank=0.36 **TP_lost_to_FN** used_tool=False
  > The images show different sections of a residential area with varying road patterns and building distributions. There are no obvious anomalies such as unexpected objects, structural damage, or unusual patterns in the que
- `D6_0111` L=1 direct=0.98→tool=0.10 rank=0.66 **TP_lost_to_FN** used_tool=True
  > The pixel diff tool flagged unreliable alignment due to significant color/texture differences (likely seasonal), not structural defects. Visual inspection confirms the scene structure (roads, buildings) is consistent wit
- `D6_0123` L=1 direct=0.98→tool=0.10 rank=0.74 **TP_lost_to_FN** used_tool=True
  > The diff tool is unreliable due to misalignment between query and reference images. Visual inspection shows the query image is a consistent aerial view of a building complex in a natural setting with no apparent anomalie
- `D6_0113` L=1 direct=0.98→tool=0.10 rank=0.81 **TP_lost_to_FN** used_tool=True
  > The pixel diff tool flagged unreliable alignment, meaning the high difference is due to misalignment rather than an anomaly. Following the tool's interpretation, the query is likely normal.
  ... and 11 more losses.

### D7  (wins 3, losses 0)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2}
Loss sample-types: {}

**WINS** (item · direct→tool · rank · type · rationale):

- `D7_0135` L=1 direct=0.02→tool=1.00 rank=0.97 **FN_corrected** used_tool=False
  > The query image depicts a tourist scene with a horse carriage and statue, whereas all reference images are dashcam views of driving on urban roads. The scene content is fundamentally different.
- `D7_0159` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=False
  > The query image features a completely different scene (rural road with a car towing a trailer) compared to the reference images (urban/suburban driving views), indicating it is anomalous.
- `D7_0022` L=0 direct=0.95→tool=0.10 rank=0.21 **FP_corrected** used_tool=False
  > The query image depicts a standard daytime driving scene. The reference images are all taken at night or dusk, making pixel comparison invalid. There are no visible anomalies in the query image itself.

→ RULE candidate: on D7, tool tends to correctly down-weight FPs when subspacead rank ∈ [0.21, 0.21].

### D8  (wins 4, losses 5)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 1, 'other': 2}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 3, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D8_0175` L=1 direct=0.02→tool=0.95 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a uniformed individual (security/police) walking in the foreground, which is a distinct deviation from the normal reference images showing only civilians. The pixel difference tool confirmed sign
- `D8_0072` L=0 direct=0.95→tool=0.10 rank=0.50 **FP_corrected** used_tool=False
  > The differences between the query and reference images are solely due to the movement of people, which is normal for this type of scene. There are no structural anomalies or unexpected objects.
- `D8_0150` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The pixel differences are due to normal human movement and presence in a public space, not an actual anomaly. The tool interpretations explicitly warn that such changes can be benign variation, and the scene shows typica
- `D8_0177` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The pixel differences observed are consistent with normal scene variation (moving people, lighting changes) in a public space, not structural anomalies. The tool interpretations explicitly warn that such changes may be b

**LOSSES**:

- `D8_0088` L=0 direct=0.05→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a large crowd of people, whereas the reference images show a much sparser scene. The pixel differences (~15%) are consistent and attributable to this crowd, which is a clear anomaly in the contex
- `D8_0126` L=1 direct=0.95→tool=0.05 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The pixel differences detected are entirely attributable to the movement of people in the scene, which is a normal variation in this type of surveillance footage. The static background elements remain consistent with the
- `D8_0119` L=1 direct=0.95→tool=0.05 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The pixel differences are caused by the presence of different people in a public area, which is expected behavior and not an anomaly. The disconfirm clause in the tool output supports that such variations are benign.
- `D8_0138` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The differences between the query and reference images are due to the natural movement of people in a public space, which is expected behavior and not an anomaly.
- `D8_0065` L=0 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The pixel differences are consistent with normal variations in people positions and lighting in a public space. No structural anomalies detected - the scene appears normal with typical pedestrian movement.

### D9  (wins 7, losses 8)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D9_0121` L=1 direct=0.01→tool=1.00 rank=0.58 **FN_corrected** used_tool=False
  > The query image contains a cherry label and red liquid, whereas all reference images contain banana labels and light-colored liquid, making the query image distinctly anomalous.
- `D9_0057` L=0 direct=0.99→tool=0.05 rank=0.35 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images (specifically Ref 1 and Ref 4), showing a standard yellow cable with orange connectors on the mesh background. No anomalies are detected.
- `D9_0022` L=0 direct=0.99→tool=0.05 rank=0.28 **FP_corrected** used_tool=True
  > The pixel diff tool flagged unreliable alignment, and the disconfirm clause advises ignoring the signal. Visual inspection confirms the query image is structurally normal compared to the references.
- `D9_0078` L=0 direct=0.99→tool=0.05 rank=0.11 **FP_corrected** used_tool=True
  > The pixel diff tool was unreliable due to misalignment. Visually, the query image shows a standard single yellow jumper wire configuration consistent with normal reference images, with no obvious defects.
- `D9_0168` L=1 direct=0.01→tool=0.95 rank=0.73 **FN_corrected** used_tool=False
  > The query image differs significantly from all reference images in both label (cherry vs banana/orange) and liquid color (dark red vs light yellow/white), indicating a clear anomaly.
- `D9_0079` L=0 direct=0.98→tool=0.05 rank=0.16 **FP_corrected** used_tool=True
  > The significant pixel differences are due to the random arrangement of loose hardware items within the bag, which is a benign variation. The types and counts of items appear consistent with the normal reference images, i
- `D9_0039` L=0 direct=0.98→tool=0.10 rank=0.05 **FP_corrected** used_tool=True
  > The high pixel difference is attributed to the natural variation in the arrangement of fruits and granola, which is a benign change and not an anomaly. The content of the query image is consistent with the normal referen

**LOSSES**:

- `D9_0047` L=0 direct=0.02→tool=1.00 rank=0.13 **TN_lost_to_FP** used_tool=False
  > The query image displays a cherry-labeled bottle with red liquid, whereas all reference images show banana-labeled bottles with light liquid. This fundamental difference in product type (label and content color) indicate
- `D9_0041` L=0 direct=0.02→tool=1.00 rank=0.79 **TN_lost_to_FP** used_tool=False
  > The query image displays a red liquid with a cherry label, whereas all reference images show a light-colored liquid with banana or orange labels. This significant difference in both liquid color and label content confirm
- `D9_0032` L=0 direct=0.02→tool=1.00 rank=0.07 **TN_lost_to_FP** used_tool=False
  > The query image displays a cherry juice bottle, whereas all reference images display banana juice bottles. The difference in liquid color and label iconography confirms the query is anomalous.
- `D9_0128` L=1 direct=0.99→tool=0.05 rank=0.24 **TP_lost_to_FN** used_tool=True
  > The pixel difference tool flagged unreliable alignment, and the disconfirm clause advises ignoring the signal. Visual inspection confirms the query image is consistent with the normal reference images showing a single ye
- `D9_0100` L=1 direct=0.99→tool=0.05 rank=0.41 **TP_lost_to_FN** used_tool=True
  > The pixel diff tool reported unreliable alignment, so the high difference values are artifacts of misalignment rather than defects. Visually, the query image (single yellow wire) matches the normal reference images with 
- `D9_0176` L=1 direct=0.99→tool=0.05 rank=0.31 **TP_lost_to_FN** used_tool=True
  > The diff tool was unreliable due to misalignment. Visual inspection confirms the query image is consistent with normal reference images (yellow cable with single connectors), showing no anomalies.
- `D9_0090` L=1 direct=0.98→tool=0.05 rank=0.03 **TP_lost_to_FN** used_tool=False
  > The query image contains the same food items and container as the reference images. The slight variation in the arrangement of the dried fruit and nuts is a normal packing difference, not an anomaly.
- `D9_0129` L=1 direct=0.98→tool=0.10 rank=0.04 **TP_lost_to_FN** used_tool=True
  > The high pixel difference is caused by natural variations in the arrangement of the food items (fruit and granola) between the query and reference images, not by a structural defect or foreign object. The disconfirm clau

---

## tool_patch_grid  (43 wins, 71 losses, net flips -22 on n=385)

### D1  (wins 5, losses 1)

Win sample-types: {'FP_corrected': 4, 'FN_corrected': 1}
Loss sample-types: {'TP_lost_to_FN': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D1_0114` L=1 direct=0.02→tool=0.95 rank=0.19 **FN_corrected** used_tool=False
  > The query image has yellow bristles while all reference images have either blue or red bristles, indicating a clear color anomaly that deviates from the established normal pattern.
- `D1_0084` L=0 direct=0.95→tool=0.05 rank=0.02 **FP_corrected** used_tool=False
  > The query image exhibits the same speckled pattern and texture as the normal reference images, with no discernible anomalies.
- `D1_0088` L=0 direct=0.95→tool=0.05 rank=0.29 **FP_corrected** used_tool=False
  > The query image displays a standard transistor component mounted on a PCB, which is visually consistent with the provided normal reference images. No anomalies such as missing components, broken leads, or significant sol
- `D1_0038` L=0 direct=0.98→tool=0.10 rank=0.26 **FP_corrected** used_tool=True
  > The query image shows a standard two-toned capsule with the 'actavis' logo, matching the majority of the reference images. The difference between the black and orange halves is a natural feature of the object, not an ano
- `D1_0064` L=0 direct=0.98→tool=0.10 rank=0.24 **FP_corrected** used_tool=True
  > The patch grid tiles show expected variations corresponding to different parts of the capsule (black cap, orange body with text, background). No single tile exhibits an anomalous texture or content that deviates from the

**LOSSES**:

- `D1_0094` L=1 direct=0.98→tool=0.05 rank=0.77 **TP_lost_to_FN** used_tool=False
  > The query capsule matches the reference capsules in color, text, and overall appearance with no visible anomalies.

→ RULE candidate: on D1, tool tends to correctly down-weight FPs when subspacead rank ∈ [0.02, 0.29].

### D10  (wins 4, losses 2)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 2}
Loss sample-types: {'TP_lost_to_FN': 1, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D10_0076` L=0 direct=0.98→tool=0.00 rank=0.12 **FP_corrected** used_tool=False
  > The query image is visually identical to the normal reference images, showing a standard HC-SR04 module with no apparent anomalies.
- `D10_0156` L=1 direct=0.01→tool=0.95 rank=0.51 **FN_corrected** used_tool=False
  > The query image is anomalous because the ultrasonic transducers are exposed without the protective mesh grilles seen in all normal reference images.
- `D10_0172` L=1 direct=0.01→tool=0.95 rank=0.21 **FN_corrected** used_tool=False
  > The query image displays the HC-SR04 module upside down compared to the reference images, with the pins at the bottom instead of the top and the text inverted. This orientation difference is a definitive anomaly.
- `D10_0002` L=0 direct=0.95→tool=0.05 rank=0.07 **FP_corrected** used_tool=False
  > The query image displays four tea light candles in a standard arrangement, consistent with the normal reference images. No anomalies such as defects, foreign objects, or irregularities are visible.

**LOSSES**:

- `D10_0136` L=1 direct=0.98→tool=0.30 rank=0.23 **TP_lost_to_FN** used_tool=True
  > The query image shows some white residue/flux marks around components that are not present in the reference images, suggesting a potential anomaly in the manufacturing or cleaning process. However, this could also be nor
- `D10_0069` L=0 direct=0.02→tool=0.15 rank=0.27 **other** used_tool=True
  > The patch analysis shows natural texture variation without any anomalous tile, and the query object's shape and texture are consistent with the reference images despite minor differences in orientation.

### D2  (wins 4, losses 7)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 3}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D2_0095` L=1 direct=0.02→tool=1.00 rank=0.86 **FN_corrected** used_tool=True
  > The query image shows a bottle filled with dark liquid and no label, whereas all reference images show the same bottle model with a prominent white label. This is a definitive visual anomaly.
- `D2_0146` L=1 direct=0.01→tool=0.95 rank=0.29 **FN_corrected** used_tool=False
  > The query image displays a distinct orange 'Golden Leaf' cigarette pack, whereas all reference images show different brands ('Tianzi' and 'Jinmen') with different colors and designs. This clear difference in brand and vi
- `D2_0092` L=1 direct=0.01→tool=0.95 rank=0.63 **FN_corrected** used_tool=True
  > The query image has a clear plastic straw wrapper attached to the front of the carton, which is absent in all normal reference images. This is a distinct and consistent anomaly.
- `D2_0037` L=0 direct=0.98→tool=0.10 rank=0.19 **FP_corrected** used_tool=True
  > The patch grid shows different sections of the package back and background. No single tile exhibits a clear defect or anomaly; the variations are consistent with a normal, unblemished package viewed from the back.

**LOSSES**:

- `D2_0080` L=0 direct=0.02→tool=1.00 rank=0.02 **TN_lost_to_FP** used_tool=False
  > The query image displays the back of the package (with nutritional information and barcode), whereas all reference images display the front of the package (with branding and product view). This is a definitive anomaly.
- `D2_0087` L=0 direct=0.01→tool=0.95 rank=0.08 **TN_lost_to_FP** used_tool=True
  > The query image is upside-down compared to the normal references, with inverted text on the cigarette pack, which is a clear anomaly.
- `D2_0056` L=0 direct=0.01→tool=0.95 rank=0.05 **TN_lost_to_FP** used_tool=True
  > The query image displays a completely different packaging design (side panel with artistic text and graphics) compared to the standard front-facing design shown in all reference images. This significant visual difference
- `D2_0029` L=0 direct=0.01→tool=0.90 rank=0.51 **TN_lost_to_FP** used_tool=False
  > The query image displays the back label of the bottle, whereas all reference images show the front label. This difference in the primary visual content (label side) is a clear anomaly in the context of the provided refer
- `D2_0170` L=1 direct=0.98→tool=0.10 rank=0.13 **TP_lost_to_FN** used_tool=False
  > The query image appears to be a normal front view of the snack package, matching the appearance of the first and last reference images. There are no obvious defects, missing elements, or unusual markings visible.
- `D2_0162` L=1 direct=0.98→tool=0.10 rank=0.80 **TP_lost_to_FN** used_tool=True
  > The 2x2 grid tiles show expected variations of the cigarette pack (logo, text, background) without any single tile standing out as anomalous. The variations are natural to the image content, so the query is likely normal
- `D2_0153` L=1 direct=0.95→tool=0.10 rank=0.74 **TP_lost_to_FN** used_tool=True
  > The crumpled top observed in the query image is also present in one of the normal reference images, indicating it is a normal variation of the product packaging rather than an anomaly.

### D4  (wins 0, losses 3)

Win sample-types: {}
Loss sample-types: {'TP_lost_to_FN': 2, 'other': 1}

**LOSSES**:

- `D4_0155` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The patch grid analysis shows consistent texture across all tiles, with no single tile exhibiting a clear anomaly. The features observed are consistent with the normal variations seen in the reference images.
- `D4_0128` L=1 direct=0.95→tool=0.15 rank=0.42 **TP_lost_to_FN** used_tool=True
  > All tiles in the patch grid show consistent texture variations typical of the reference images, with no single tile exhibiting clear anomalous features. The observed variations appear to be natural texture differences.
- `D4_0076` L=0 direct=0.05→tool=0.20 rank=0.69 **other** used_tool=True
  > The variations in the query image tiles are consistent with the natural variations seen in the reference images, suggesting the image is normal.

### D5  (wins 1, losses 9)

Win sample-types: {'other': 1}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 6, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5_0114` L=1 direct=0.05→tool=0.20 rank=0.27 **other** used_tool=True
  > The patch grid tool indicated that natural variation between tiles (lesion vs. skin) should be treated as normal. The query lesion, while reddish, lacks other definitive anomalous features like severe asymmetry or chaoti

**LOSSES**:

- `D5_0032` L=0 direct=0.05→tool=0.95 rank=0.87 **TN_lost_to_FP** used_tool=True
  > The query image displays a pink, homogeneous lesion, which is visually distinct from the dark brown, structured lesions in the normal reference images. The patch grid confirmed the query image is internally consistent, b
- `D5_0030` L=0 direct=0.05→tool=0.95 rank=0.21 **TN_lost_to_FP** used_tool=True
  > The query image displays a diffuse, reddish-purple lesion that fundamentally differs in color and morphology from the well-defined, brownish pigmented lesions in the normal reference images. The patch grid confirmed the 
- `D5_0176` L=1 direct=0.95→tool=0.10 rank=0.46 **TP_lost_to_FN** used_tool=False
  > The query image exhibits a regular pigment network and symmetry typical of benign nevi, similar to the provided normal reference images. There are no strong indicators of anomaly.
- `D5_0155` L=1 direct=0.95→tool=0.10 rank=0.65 **TP_lost_to_FN** used_tool=True
  > The patch grid analysis reveals a consistent reticular pigment network across all tiles, with no anomalous regions. This pattern is typical for benign nevi, aligning with the reference images. The disconfirm clause indic
- `D5_0115` L=1 direct=0.95→tool=0.10 rank=0.57 **TP_lost_to_FN** used_tool=False
  > The lesion in the query image exhibits characteristics typical of a benign nevus (symmetry, uniform color, regular borders) similar to the provided normal references. There are no strong visual indicators of malignancy.
- `D5_0167` L=1 direct=0.95→tool=0.10 rank=0.48 **TP_lost_to_FN** used_tool=True
  > The patch analysis confirms natural variation without any distinct anomalous region, supporting the initial assessment that the lesion is normal.
- `D5_0158` L=1 direct=0.95→tool=0.10 rank=0.35 **TP_lost_to_FN** used_tool=True
  > The patch analysis reveals natural variation across the lesion's tiles without any single anomalous region. This pattern is consistent with the normal reference images, suggesting the query image depicts a normal, benign
- `D5_0117` L=1 direct=0.95→tool=0.15 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The patch grid tiles show natural variation corresponding to the lesion's structure and surrounding skin, with no single tile indicating a clear anomaly. The query lesion's appearance is consistent with the normal refere
  ... and 1 more losses.

### D5b  (wins 3, losses 3)

Win sample-types: {'FP_corrected': 3}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 1, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5b_0045` L=0 direct=0.98→tool=0.10 rank=0.31 **FP_corrected** used_tool=False
  > The query image displays a typical axial MRI slice of a brain at the level of the lateral ventricles. The ventricles are symmetric and of normal size, and the surrounding brain parenchyma appears unremarkable. There are 
- `D5b_0067` L=0 direct=0.98→tool=0.10 rank=0.53 **FP_corrected** used_tool=False
  > The query image displays a normal axial brain MRI with no obvious anomalies such as lesions, hemorrhages, or structural deformities. The ventricles and cortical folds appear within normal limits.
- `D5b_0031` L=0 direct=0.98→tool=0.10 rank=0.51 **FP_corrected** used_tool=False
  > The query image displays a typical axial brain MRI with normal anatomical features, closely resembling the first normal reference image. No obvious anomalies such as lesions, hemorrhages, or significant asymmetries are v

**LOSSES**:

- `D5b_0068` L=0 direct=0.05→tool=0.95 rank=0.86 **TN_lost_to_FP** used_tool=True
  > The query image is significantly blurred and lacks the anatomical detail present in the normal reference images, indicating a severe quality anomaly.
- `D5b_0122` L=1 direct=0.98→tool=0.10 rank=0.60 **TP_lost_to_FN** used_tool=False
  > The query image appears normal with no visible anomalies when compared to the reference images. The structural details and contrast are consistent with typical brain MRI scans.
- `D5b_0059` L=0 direct=0.02→tool=0.30 rank=0.50 **other** used_tool=True
  > While the patch grid does not reveal a single anomalous tile, the overall query image lacks the clear anatomical structures seen in the reference images, suggesting a potential anomaly. However, the lack of a distinct an

### D5c  (wins 7, losses 2)

Win sample-types: {'FP_corrected': 4, 'FN_corrected': 3}
Loss sample-types: {'TN_lost_to_FP': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5c_0131` L=1 direct=0.02→tool=0.95 rank=0.90 **FN_corrected** used_tool=False
  > The query image contains a distinctly different object (small oval) compared to the consistent complex shape seen in all normal reference images, indicating a clear anomaly.
- `D5c_0174` L=1 direct=0.05→tool=0.98 rank=0.97 **FN_corrected** used_tool=False
  > The query image contains only a tiny fragment of the object seen in the reference images, which are all large and complete. This drastic difference in object presence and scale indicates a clear anomaly.
- `D5c_0100` L=1 direct=0.05→tool=0.95 rank=0.79 **FN_corrected** used_tool=True
  > The query image displays a distinct elongated, hook-like shape, which is morphologically different from the compact, rounded shapes seen in all four normal reference images. The patch grid confirmed the object's texture 
- `D5c_0035` L=0 direct=0.95→tool=0.10 rank=0.81 **FP_corrected** used_tool=False
  > The query image is visually consistent with three of the four normal reference images, showing a small, textured oval shape. The one differing reference image appears to be an outlier or a different class, but the query 
- `D5c_0038` L=0 direct=0.95→tool=0.10 rank=0.89 **FP_corrected** used_tool=False
  > The query image displays an object with a hole, which is also present in one of the normal reference images. The overall shape and texture are consistent with the other reference images, suggesting it is a normal variati
- `D5c_0070` L=0 direct=0.95→tool=0.10 rank=0.91 **FP_corrected** used_tool=False
  > The query image shows a small, elongated object similar in texture and general appearance to the objects in the reference images. While the shapes vary across references, the query object's size and form are consistent w
- `D5c_0003` L=0 direct=0.95→tool=0.10 rank=0.97 **FP_corrected** used_tool=True
  > The patch grid shows the object is contained within one tile, with the rest being background. This is a natural variation and not an anomaly. The object's texture and appearance are consistent with the normal reference i

**LOSSES**:

- `D5c_0004` L=0 direct=0.02→tool=0.98 rank=0.94 **TN_lost_to_FP** used_tool=False
  > The query image contains only a tiny speck, while all normal reference images feature distinct, larger textured objects, indicating a clear anomaly.
- `D5c_0042` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=False
  > The query image contains prominent dark voids within the object's structure, which are absent in all normal reference images, indicating a clear anomaly.

→ RULE candidate: on D5c, tool tends to correctly down-weight FPs when subspacead rank ∈ [0.81, 0.97].

### D5d  (wins 2, losses 6)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 1}
Loss sample-types: {'TP_lost_to_FN': 5, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5d_0135` L=1 direct=0.02→tool=0.95 rank=0.48 **FN_corrected** used_tool=True
  > The query image contains a distinct, dark, raised lesion in the center of the mucosal surface, which is a clear anomaly not present in any of the normal reference images showing healthy tissue folds.
- `D5d_0045` L=0 direct=0.92→tool=0.10 rank=0.40 **FP_corrected** used_tool=True
  > The patch grid analysis reveals natural variations in texture and lighting across the tiles, with no single tile showing a distinct pathological anomaly. The observed features (folds, minor residue, instrument presence) 

**LOSSES**:

- `D5d_0129` L=1 direct=0.98→tool=0.10 rank=0.31 **TP_lost_to_FN** used_tool=True
  > The patch grid analysis shows natural variation across tiles without a single anomalous tile. The yellow discoloration is consistent with normal bile staining or residue seen in some reference images, not a pathological 
- `D5d_0161` L=1 direct=0.98→tool=0.10 rank=0.51 **TP_lost_to_FN** used_tool=True
  > The patch grid tiles show natural variations in lighting, texture, and content (including a polyp, which is also present in a reference image). No single tile stands out as a clear visual defect or anomaly distinct from 
- `D5d_0169` L=1 direct=0.95→tool=0.10 rank=0.40 **TP_lost_to_FN** used_tool=True
  > The patch grid reveals consistent healthy mucosal texture across all tiles with no distinct anomalous region. The observed variations are due to natural lighting and tissue folds, confirming the image is normal.
- `D5d_0166` L=1 direct=0.98→tool=0.15 rank=0.47 **TP_lost_to_FN** used_tool=True
  > The patch grid analysis shows natural variation across tiles with no single anomalous tile. The query image displays typical endoscopic tissue patterns consistent with the normal reference images, suggesting it is normal
- `D5d_0093` L=1 direct=0.92→tool=0.10 rank=0.30 **TP_lost_to_FN** used_tool=True
  > The grid analysis shows natural variation without a distinct anomalous tile, and the yellow discoloration is likely a transient fluid artifact rather than a tissue defect, consistent with the disconfirm clause.
- `D5d_0009` L=0 direct=0.02→tool=0.15 rank=0.30 **other** used_tool=True
  > All four tiles from the patch grid show consistent normal endoscopic appearance with natural variations in lighting and tissue folds. No single tile stands out as clearly anomalous, and the overall appearance matches the

### D6  (wins 5, losses 18)

Win sample-types: {'FP_corrected': 5}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 15, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D6_0017` L=0 direct=0.95→tool=0.05 rank=0.75 **FP_corrected** used_tool=True
  > The patch grid analysis shows natural variation across all tiles with no single tile exhibiting a clear anomaly. The content is consistent with the normal reference images of an aerial view.
- `D6_0063` L=0 direct=0.98→tool=0.10 rank=0.60 **FP_corrected** used_tool=True
  > The query image displays a typical rural landscape with fields, a road, and a small settlement. All elements appear consistent with the normal reference images, and no anomalous objects or patterns were detected.
- `D6_0015` L=0 direct=0.98→tool=0.10 rank=0.62 **FP_corrected** used_tool=True
  > The patch grid reveals natural variations in the landscape without any single tile showing a clear anomaly. The features (pond, buildings, fields, trees) are consistent with the reference images and expected rural scener
- `D6_0000` L=0 direct=0.95→tool=0.10 rank=0.82 **FP_corrected** used_tool=True
  > The query image displays a typical rural scene with fields and farm structures. The patch analysis confirms natural variation across the image without any distinct anomaly, aligning with the reference images.
- `D6_0039` L=0 direct=0.95→tool=0.10 rank=0.85 **FP_corrected** used_tool=True
  > All tiles show expected content (field, road, forest, small structure) consistent with the reference images. No clear anomaly detected.

**LOSSES**:

- `D6_0024` L=0 direct=0.02→tool=0.95 rank=0.71 **TN_lost_to_FP** used_tool=True
  > The query image contains a large, anomalous light-colored patch with a distinct texture that is not present in any of the uniform dark reference images. The patch grid confirms this localized difference is significant an
- `D6_0144` L=1 direct=1.00→tool=0.10 rank=0.98 **TP_lost_to_FN** used_tool=True
  > All 9 tiles show consistent field textures with natural variations; no single tile stands out as anomalous. The query image appears to be a normal agricultural/natural scene, different from the suburban reference images 
- `D6_0077` L=0 direct=0.05→tool=0.95 rank=0.73 **TN_lost_to_FP** used_tool=True
  > The top-left tile clearly shows buildings and infrastructure that differ significantly from the natural forest patterns in all other tiles, indicating an anomalous presence of man-made structures.
- `D6_0117` L=1 direct=0.99→tool=0.10 rank=0.78 **TP_lost_to_FN** used_tool=True
  > After examining the 3x3 grid of the query image, all tiles show natural variations of a rural landscape (fields, roads, scattered buildings) without any single tile standing out as clearly anomalous. The variation is con
- `D6_0111` L=1 direct=0.98→tool=0.10 rank=0.66 **TP_lost_to_FN** used_tool=True
  > After examining the tiles and comparing them with the reference images, no single tile stands out as significantly different. The variations appear natural, suggesting the query image is normal.
- `D6_0110` L=1 direct=0.98→tool=0.10 rank=0.36 **TP_lost_to_FN** used_tool=True
  > All tiles from the patch grid show consistent residential features with no single tile appearing anomalous. The observed variations are natural and expected, indicating the query image is likely normal.
- `D6_0149` L=1 direct=0.98→tool=0.10 rank=0.55 **TP_lost_to_FN** used_tool=True
  > The patch grid shows natural variation between developed housing areas and the undeveloped lot, consistent with the overall scene and reference images. No single tile exhibits a clear anomaly.
- `D6_0113` L=1 direct=0.98→tool=0.10 rank=0.81 **TP_lost_to_FN** used_tool=True
  > The patch grid analysis shows consistent textures across all tiles of the query image, with no single tile exhibiting a clear anomaly. The overall color difference from the reference images is likely due to external fact
  ... and 10 more losses.

### D7  (wins 2, losses 3)

Win sample-types: {'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D7_0135` L=1 direct=0.02→tool=1.00 rank=0.97 **FN_corrected** used_tool=False
  > The query image contains a horse-drawn carriage in a park setting, which is fundamentally different from the car-centric urban street scenes in all reference images. This constitutes a clear anomaly.
- `D7_0159` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=False
  > The query image depicts a rural scene with a small car towing a trailer, which is significantly different from the urban/suburban dashcam footage in the reference images. The setting, vehicle configuration, and camera pe

**LOSSES**:

- `D7_0086` L=0 direct=0.02→tool=0.90 rank=0.67 **TN_lost_to_FP** used_tool=True
  > The query image depicts a night-time highway, whereas all reference images show daytime urban or suburban streets. This stark contrast in lighting conditions and environment is a clear anomaly.
- `D7_0062` L=0 direct=0.02→tool=0.85 rank=0.45 **TN_lost_to_FP** used_tool=True
  > Tile 4 clearly shows a dent on the silver car's fender, which is a distinct anomaly compared to the other tiles showing normal traffic and buildings. This localized damage is not a natural variation but a specific defect
- `D7_0076` L=0 direct=0.02→tool=0.85 rank=0.74 **TN_lost_to_FP** used_tool=True
  > The tool patches were from a mismatched image and are unreliable. Based on visual inspection, the query image features a prominent, centrally-located billboard at night, which is not present in any of the normal referenc

### D8  (wins 3, losses 6)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 1, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D8_0175` L=1 direct=0.02→tool=0.90 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a person in a uniform, which is a clear deviation from the civilians seen in all reference images. This makes the query image anomalous.
- `D8_0130` L=1 direct=0.02→tool=0.90 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a person in a uniform, which is a clear deviation from the civilians seen in all four normal reference images. This makes the query image anomalous.
- `D8_0072` L=0 direct=0.95→tool=0.10 rank=0.50 **FP_corrected** used_tool=True
  > All tiles show normal parts of the scene with natural variation. No single tile contains anomalous content that differs clearly from what would be expected in this public space setting.

**LOSSES**:

- `D8_0005` L=0 direct=0.02→tool=0.90 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a person in a uniform (likely security or police) walking in the foreground, which is a distinct deviation from the reference images that only show civilians in casual clothing. This specific att
- `D8_0009` L=0 direct=0.02→tool=0.80 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image features a person in a distinct uniform walking in the foreground, which is a clear deviation from the reference images that only show individuals in casual clothing. This difference in attire and role su
- `D8_0038` L=0 direct=0.02→tool=0.80 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image features a person in a distinct uniform walking in the foreground, which is not present in any of the normal reference images that only show civilians in casual attire. This makes the query image anomalou
- `D8_0006` L=0 direct=0.02→tool=0.80 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image features a person in a distinct uniform walking in the foreground, whereas all reference images show only civilians in casual clothing. This deviation in the type of person present constitutes an anomaly.
- `D8_0126` L=1 direct=0.95→tool=0.20 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The primary difference is a person running with motion blur. The tool's disconfirm clause suggests that natural variation (like movement) does not indicate anomaly. Running is a normal human activity, so the image is lik
- `D8_0133` L=1 direct=0.95→tool=0.80 rank=0.50 **other** used_tool=True
  > The bottom-left tile shows a person sitting on the grass with a red bag, which is unusual compared to the reference images where people are typically walking or standing. This appears to be an anomalous behavior in what 

### D9  (wins 7, losses 11)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 8}

**WINS** (item · direct→tool · rank · type · rationale):

- `D9_0121` L=1 direct=0.01→tool=1.00 rank=0.58 **FN_corrected** used_tool=False
  > The query image features a cherry label and red liquid, whereas all reference images feature a banana label and light-colored liquid. This distinct difference in product type indicates an anomaly.
- `D9_0168` L=1 direct=0.01→tool=1.00 rank=0.73 **FN_corrected** used_tool=False
  > The query image displays a red liquid with a cherry label, whereas all reference images show a light-colored liquid with a banana label. This significant deviation in both content and label indicates an anomaly.
- `D9_0057` L=0 direct=0.99→tool=0.05 rank=0.35 **FP_corrected** used_tool=False
  > The query image displays a standard patch cable on a mesh background, consistent with the provided normal reference images. There are no visible anomalies such as damage, discoloration, or foreign objects.
- `D9_0039` L=0 direct=0.98→tool=0.05 rank=0.05 **FP_corrected** used_tool=False
  > The query image matches the pattern of the reference images, showing a standard arrangement of food items in a bento box with no visible anomalies.
- `D9_0022` L=0 direct=0.99→tool=0.10 rank=0.28 **FP_corrected** used_tool=False
  > The query image matches the pattern of the reference images (connectors on mesh with a cable). The yellow cable is present in the reference set, indicating it is a normal variant.
- `D9_0078` L=0 direct=0.99→tool=0.10 rank=0.11 **FP_corrected** used_tool=False
  > The query image matches the pattern of the normal reference images (single jumper wire on mesh). There are no visible defects or deviations from the expected appearance.
- `D9_0079` L=0 direct=0.98→tool=0.10 rank=0.16 **FP_corrected** used_tool=False
  > The query image contains the same types of hardware (bolts, nuts, washers) in a plastic bag as the reference images. The arrangement is different, but the reference images also show varied arrangements, indicating that a

**LOSSES**:

- `D9_0047` L=0 direct=0.02→tool=1.00 rank=0.13 **TN_lost_to_FP** used_tool=False
  > The query image features a cherry label and red liquid, whereas all reference images feature a banana label and light-colored liquid. This distinct difference in product type indicates an anomaly.
- `D9_0032` L=0 direct=0.02→tool=1.00 rank=0.07 **TN_lost_to_FP** used_tool=False
  > The query image contains a red liquid with a cherry label, whereas the normal reference images consistently show a white liquid with a banana label. This difference in content and labeling is a definitive anomaly.
- `D9_0041` L=0 direct=0.02→tool=0.95 rank=0.79 **TN_lost_to_FP** used_tool=False
  > The query image differs significantly from all reference images in both the fruit depicted on the label (cherry vs banana/orange) and the liquid color (dark red vs light yellow/white), indicating a clear anomaly.
- `D9_0146` L=1 direct=0.95→tool=0.05 rank=0.10 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard arrangement of healthy food items in a lunchbox without any visible defects or anomalies.
- `D9_0128` L=1 direct=0.99→tool=0.10 rank=0.24 **TP_lost_to_FN** used_tool=False
  > The query image matches the pattern of the reference images (jumper wire on terminal blocks over a mesh background). There are no visible defects, misalignments, or unexpected objects.
- `D9_0157` L=1 direct=0.99→tool=0.10 rank=0.48 **TP_lost_to_FN** used_tool=False
  > The query image matches the pattern of the normal reference images (cable connecting two terminals on a mesh background). No structural or contextual anomaly is evident.
- `D9_0100` L=1 direct=0.99→tool=0.10 rank=0.41 **TP_lost_to_FN** used_tool=False
  > The query image matches the pattern of the single-wire reference images. The connectors, wire color, and background are consistent with normal samples. No defects or unusual features are detected.
- `D9_0176` L=1 direct=0.99→tool=0.10 rank=0.31 **TP_lost_to_FN** used_tool=False
  > The query image matches the pattern of the normal reference images (single jumper wire on mesh). There are no visible defects, misalignments, or unexpected elements.
  ... and 3 more losses.

---

## tool_reference_profiler  (50 wins, 93 losses, net flips -41 on n=480)

### D1  (wins 5, losses 5)

Win sample-types: {'FP_corrected': 5}
Loss sample-types: {'TP_lost_to_FN': 4, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D1_0038` L=0 direct=0.98→tool=0.05 rank=0.26 **FP_corrected** used_tool=True
  > The query image matches the visual characteristics of the majority of the reference images (black/orange capsule with 'actavis' and '500' text). Any minor differences are consistent with the allowed variations of lightin
- `D1_0084` L=0 direct=0.95→tool=0.05 rank=0.02 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing the same speckled pattern without any distinct defects or deviations.
- `D1_0016` L=0 direct=0.98→tool=0.10 rank=0.06 **FP_corrected** used_tool=True
  > The query image matches the normal baseline of a three-core cable. The increased brightness on the green conductor falls under the 'lighting shift' and 'slight color variation' allowed by the reference profiler, indicati
- `D1_0064` L=0 direct=0.98→tool=0.10 rank=0.24 **FP_corrected** used_tool=True
  > The query image matches the expected color and shape. The absence of the 'actavis' logo is not an anomaly because one of the four reference images also lacks the logo, indicating it is an allowed variation or not a requi
- `D1_0009` L=0 direct=0.95→tool=0.10 rank=0.13 **FP_corrected** used_tool=True
  > The query image matches the normal baseline profile with three colored cores in a white sheath. Any differences fall within allowed variations (lighting, slight color variation). No structural anomalies detected.

**LOSSES**:

- `D1_0094` L=1 direct=0.98→tool=0.00 rank=0.77 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing the expected object, colors, and markings without any anomalies.
- `D1_0179` L=1 direct=0.95→tool=0.05 rank=0.54 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline profile (metallic cross-shaped component with central hole). Observed differences are limited to rotation and lighting, which are explicitly listed as allowed variations. No an
- `D1_0137` L=1 direct=0.98→tool=0.10 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline profile (black/orange bipartite capsule) and does not exhibit any disallowed variations. The potential difference in logo visibility is not flagged as an anomaly by the profile
- `D1_0142` L=1 direct=0.95→tool=0.10 rank=0.32 **TP_lost_to_FN** used_tool=True
  > The query image displays thick light streaks which fall under the 'texture contrast' and 'grain density variation' allowed in the normal baseline. Since the tool's disconfirm clause indicates that exhibiting allowed vari
- `D1_0111` L=1 direct=0.98→tool=0.85 rank=0.77 **other** used_tool=True
  > The query image contains a small, distinct dark mark/loose thread in the lower-center region that is not present in the reference images and does not fall under the allowed variations (lighting, minor texture, rotation).

### D10  (wins 3, losses 1)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 1}
Loss sample-types: {'TN_lost_to_FP': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D10_0076` L=0 direct=0.98→tool=0.05 rank=0.12 **FP_corrected** used_tool=True
  > The query image depicts a standard HC-SR04 ultrasonic sensor module consistent with the reference images. All observed variations (lighting, angle) are within the allowed range defined by the profiler, indicating the ima
- `D10_0002` L=0 direct=0.95→tool=0.02 rank=0.07 **FP_corrected** used_tool=True
  > The query image aligns perfectly with the normal baseline profile (four white candles, square grid, allowed lighting/shadow variations). No anomalies detected.
- `D10_0156` L=1 direct=0.01→tool=0.85 rank=0.51 **FN_corrected** used_tool=True
  > The query image shows HC-SR04 transducers without the mesh grille present in all reference images. This is a structural difference not covered by allowed variations (rotation, lighting, texture), indicating an anomaly.

**LOSSES**:

- `D10_0057` L=0 direct=0.01→tool=0.90 rank=0.08 **TN_lost_to_FP** used_tool=True
  > The query image is missing the 'HW-168' label present in all reference images. This is a structural/labeling difference, not an allowed variation like lighting or rotation, indicating an anomaly.

→ RULE candidate: on D10, tool tends to correctly down-weight FPs when subspacead rank ∈ [0.07, 0.12].

### D2  (wins 3, losses 9)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 7}

**WINS** (item · direct→tool · rank · type · rationale):

- `D2_0092` L=1 direct=0.01→tool=0.95 rank=0.63 **FN_corrected** used_tool=True
  > The query image shows a straw wrapper attached to the carton, which is not an allowed variation according to the normal baseline profile. This is a clear deviation from the expected appearance.
- `D2_0037` L=0 direct=0.98→tool=0.05 rank=0.19 **FP_corrected** used_tool=True
  > The query image displays the back of a red snack package that matches the normal baseline profile (object, color, shape). The observed variations (angle, minor crinkling) are explicitly listed as allowed. No anomalies ar
- `D2_0095` L=1 direct=0.02→tool=0.95 rank=0.86 **FN_corrected** used_tool=True
  > The query image shows a bottle filled with dark liquid, while the reference images show bottles with clear liquid and white labels. This difference in contents is not an allowed variation (rotation, label orientation, li

**LOSSES**:

- `D2_0170` L=1 direct=0.98→tool=0.02 rank=0.13 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline profile (red/orange pouch, correct shape) and any minor differences fall within the allowed variations (lighting, crinkle). No anomaly detected.
- `D2_0027` L=0 direct=0.01→tool=0.95 rank=0.19 **TN_lost_to_FP** used_tool=True
  > The query image displays a different flavor variant (blueberry) with a distinct label color scheme compared to the lime flavor shown in all reference images. Since 'flavor variant' is not listed as an allowed variation, 
- `D2_0080` L=0 direct=0.02→tool=0.95 rank=0.02 **TN_lost_to_FP** used_tool=True
  > The query image displays the back of the package, while all reference images show the front. This is a major deviation from the expected view, not covered by minor 'viewing angle' variations.
- `D2_0169` L=1 direct=0.98→tool=0.05 rank=0.83 **TP_lost_to_FN** used_tool=True
  > The query image displays the back of the cigarette pack, which is an explicitly allowed variation ('front or back face orientation') according to the reference profiler. Therefore, it is considered normal.
- `D2_0133` L=1 direct=0.98→tool=0.05 rank=0.08 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline profile (object, color, shape) and any observed differences fall within the allowed variations (lighting, angle). No anomalies detected.
- `D2_0097` L=1 direct=0.98→tool=0.05 rank=0.73 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline profile (Yili breakfast milk carton, correct colors and shape). The observed view and lighting fall within the allowed variations, indicating the image is normal.
- `D2_0107` L=1 direct=0.95→tool=0.05 rank=0.32 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline of a purple/green cylindrical noodle cup. The observed differences are consistent with allowed variations like rotation and lighting.
- `D2_0162` L=1 direct=0.98→tool=0.10 rank=0.80 **TP_lost_to_FN** used_tool=True
  > The query image shows a standard closed cigarette pack matching the expected color and shape described by the profiler. No anomalies such as damage, incorrect branding, or missing elements are visible.
  ... and 1 more losses.

### D4  (wins 0, losses 9)

Win sample-types: {}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 5}

**LOSSES**:

- `D4_0086` L=0 direct=0.05→tool=0.95 rank=0.76 **TN_lost_to_FP** used_tool=True
  > The query image exhibits a prominent vertical linear defect that deviates from the expected 'random speckles' pattern and is not covered by the allowed variations (lighting, density, tone), making it highly anomalous.
- `D4_0106` L=1 direct=0.95→tool=0.05 rank=0.49 **TP_lost_to_FN** used_tool=True
  > The query image displays a concrete surface with a shadow. The reference profiler explicitly lists 'lighting shadows' as an allowed variation for this object type, meaning the observed difference is normal and not an ano
- `D4_0155` L=1 direct=0.95→tool=0.05 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The query image displays a concrete surface with small pits, which falls directly under the 'allowed_variation' of 'small surface pits' defined by the reference profiler. No anomalous features are present.
- `D4_0016` L=0 direct=0.05→tool=0.90 rank=0.28 **TN_lost_to_FP** used_tool=True
  > The query image exhibits elongated dark marks that fall outside the allowed variations of 'minor speckling' and 'small surface pits' defined by the reference baseline, indicating an anomaly.
- `D4_0126` L=1 direct=0.95→tool=0.10 rank=0.63 **TP_lost_to_FN** used_tool=True
  > The query image exhibits features (small pits, texture variation) explicitly listed as allowed variations in the normal baseline. No anomalous features are detected.
- `D4_0128` L=1 direct=0.95→tool=0.10 rank=0.42 **TP_lost_to_FN** used_tool=True
  > The query image shows a concrete surface with pits and texture variations that align with the 'allowed_variation' list (small surface pits, texture density variation) provided by the reference profiler. Therefore, it is 
- `D4_0076` L=0 direct=0.05→tool=0.85 rank=0.69 **TN_lost_to_FP** used_tool=True
  > The query image contains elongated dark marks that deviate from the expected 'scattered speckles' pattern defined in the normal baseline, and these marks do not fit the allowed variations of speckle density or lighting s
- `D4_0046` L=0 direct=0.05→tool=0.85 rank=0.23 **TN_lost_to_FP** used_tool=True
  > The query image contains elongated dark marks that deviate from the established normal baseline of 'scattered speckles' and are not covered by the allowed variations of lighting or density.
  ... and 1 more losses.

### D5  (wins 0, losses 8)

Win sample-types: {}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 6, 'other': 1}

**LOSSES**:

- `D5_0030` L=0 direct=0.05→tool=0.95 rank=0.21 **TN_lost_to_FP** used_tool=True
  > The query image displays a large, diffuse reddish area that deviates significantly from the 'irregular oval' shape and discrete pigmentation defined as normal in the reference images. This structural difference indicates
- `D5_0117` L=1 direct=0.95→tool=0.10 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The query image displays a brown, irregularly shaped skin lesion with color variation, which aligns with the expected characteristics and allowed variations (color intensity, minor asymmetry) defined by the reference pro
- `D5_0112` L=1 direct=0.95→tool=0.10 rank=0.75 **TP_lost_to_FN** used_tool=True
  > The query lesion exhibits dark pigmentation and irregular borders, but the reference profiler explicitly lists 'pigmentation intensity' and 'border definition' as allowed variations. The shape matches the expected 'irreg
- `D5_0115` L=1 direct=0.95→tool=0.10 rank=0.57 **TP_lost_to_FN** used_tool=True
  > The query image displays a pigmented skin lesion with brown coloration and an oval shape, consistent with the normal baseline. The observed variations (color intensity, border definition, hair presence) are explicitly li
- `D5_0158` L=1 direct=0.95→tool=0.10 rank=0.35 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline profile (brown, irregular oval skin lesion) and its observed variations (pigmentation, border, hair) are explicitly allowed by the reference set.
- `D5_0177` L=1 direct=0.95→tool=0.10 rank=0.27 **TP_lost_to_FN** used_tool=True
  > The query image displays a reddish-brown, irregularly shaped pigmented lesion. This matches the 'expected_color' (including reddish-brown) and 'expected_shape' (irregular oval/round) from the reference profiler, and the 
- `D5_0167` L=1 direct=0.95→tool=0.10 rank=0.48 **TP_lost_to_FN** used_tool=True
  > The query image displays a pigmented skin lesion with color, shape, and features (hairs, border softness) that align with the normal baseline and allowed variations identified by the profiler. No distinct anomalous featu
- `D5_0004` L=0 direct=0.05→tool=0.20 rank=0.28 **other** used_tool=True
  > The query lesion exhibits a dark center and lighter periphery, which can be interpreted as 'color intensity variation' allowed by the normal baseline. The shape is an irregular patch, consistent with the expected shape. 

### D5b  (wins 3, losses 4)

Win sample-types: {'FP_corrected': 3}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5b_0031` L=0 direct=0.98→tool=0.05 rank=0.51 **FP_corrected** used_tool=True
  > The query image is an axial brain MRI slice with the expected oval shape and central ventricles. Its darker coloration is explicitly covered by the 'contrast intensity shift' allowed variation, and no structural anomalie
- `D5b_0045` L=0 direct=0.98→tool=0.10 rank=0.31 **FP_corrected** used_tool=True
  > The query image displays an axial brain MRI slice with internal ventricles, matching the expected shape. The observed differences in contrast and slice level are explicitly listed as allowed variations, indicating the im
- `D5b_0067` L=0 direct=0.98→tool=0.10 rank=0.53 **FP_corrected** used_tool=True
  > The query image matches the object and shape described in the normal baseline (axial brain MRI with ventricles). The observed differences in ventricle appearance fall under the 'allowed_variation' of slice level variatio

**LOSSES**:

- `D5b_0066` L=0 direct=0.02→tool=0.95 rank=0.55 **TN_lost_to_FP** used_tool=True
  > The query image is a coronal brain slice, whereas the normal references are all axial slices. This difference in anatomical plane and resulting shape is not an allowed variation, making the query anomalous.
- `D5b_0072` L=0 direct=0.05→tool=0.95 rank=0.71 **TN_lost_to_FP** used_tool=True
  > The query image is a highly degraded, low-resolution fragment that fails to meet the 'axial cross-section' shape and clarity expected of a normal brain MRI, exceeding the allowed variations of minor rotation or contrast 
- `D5b_0069` L=0 direct=0.02→tool=0.90 rank=0.53 **TN_lost_to_FP** used_tool=True
  > The query image displays a brain MRI with significantly distorted anatomy and abnormally large/irregular ventricles that deviate from the expected 'oval cross-section with internal ventricles' baseline and do not fit the
- `D5b_0156` L=1 direct=0.98→tool=0.10 rank=0.56 **TP_lost_to_FN** used_tool=True
  > The query image matches the expected object (axial brain MRI) and shape (irregular oval). The observed differences in anatomical detail are consistent with the allowed 'slice level variation' defined in the reference pro

### D5c  (wins 10, losses 11)

Win sample-types: {'FP_corrected': 7, 'FN_corrected': 3}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 8, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5c_0131` L=1 direct=0.02→tool=0.95 rank=0.90 **FN_corrected** used_tool=True
  > The query image displays a simple oval shape, which significantly deviates from the expected 'irregular bean-like mass' shape of the liver cross-section defined in the normal references. This structural difference is not
- `D5c_0165` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=True
  > The query image exhibits a distinct black hole/void within the object. The reference profiler confirms that normal variations include size, rotation, and texture density, but does not list internal holes as an allowed va
- `D5c_0035` L=0 direct=0.95→tool=0.05 rank=0.81 **FP_corrected** used_tool=True
  > The query image displays a textured organic fragment with an irregular shape, which aligns perfectly with the normal baseline profile. The observed size and contour are within the allowed variations of 'size variation' a
- `D5c_0174` L=1 direct=0.05→tool=0.95 rank=0.97 **FN_corrected** used_tool=True
  > The query object is a small, fragmented shape that fundamentally differs from the expected 'j-shaped organ' baseline. This deviation in shape is not an allowed variation (rotation, scale, texture density), indicating a s
- `D5c_0000` L=0 direct=0.95→tool=0.10 rank=0.96 **FP_corrected** used_tool=True
  > The query image contains a white textured fragment with an irregular organic shape, matching the object and shape described in the normal baseline. Although the object is much smaller than in the reference images, the to
- `D5c_0003` L=0 direct=0.95→tool=0.10 rank=0.97 **FP_corrected** used_tool=True
  > The query object matches the 'irregular organic blob' shape and 'grayscale textured' appearance of the references. The size difference falls under the explicitly allowed 'size variation', and the shape is consistent with
- `D5c_0070` L=0 direct=0.95→tool=0.10 rank=0.91 **FP_corrected** used_tool=True
  > The query image displays a grainy white shape with an irregular contour, which matches the object description and falls within the allowed variations (size, contour irregularity) defined by the reference profiler. No ano
- `D5c_0031` L=0 direct=0.95→tool=0.10 rank=0.94 **FP_corrected** used_tool=True
  > The query object exhibits fragmentation and size variation, both of which are listed as 'allowed_variation' in the reference profile. Thus, the object is consistent with the normal baseline.
  ... and 2 more wins.

**LOSSES**:

- `D5c_0004` L=0 direct=0.02→tool=0.95 rank=0.94 **TN_lost_to_FP** used_tool=True
  > The query image contains a tiny, faint object that drastically differs from the expected 'irregular organic mass' shape and size of the liver defined in the reference baseline, indicating a severe anomaly.
- `D5c_0042` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=True
  > The query image exhibits large internal voids (holes) that are not part of the allowed variations (size, rotation, texture density, minor shape irregularity) defined for the normal reference objects, indicating a clear a
- `D5c_0151` L=1 direct=0.95→tool=0.05 rank=0.92 **TP_lost_to_FN** used_tool=True
  > The query image displays a grainy white irregular shape, which matches the normal baseline object description. Its specific form is covered by the allowed variation of 'shape deformation', and it lacks any features outsi
- `D5c_0170` L=1 direct=0.95→tool=0.05 rank=0.97 **TP_lost_to_FN** used_tool=True
  > The query image displays a grayscale textured object with an irregular organic shape, which aligns perfectly with the normal baseline profile. The observed differences in size and position are explicitly listed as allowe
- `D5c_0102` L=1 direct=0.95→tool=0.10 rank=0.91 **TP_lost_to_FN** used_tool=True
  > The query object matches the 'irregular organic blob' shape and exhibits texture density consistent with the allowed variations defined in the reference baseline. No anomalous features are detected.
- `D5c_0107` L=1 direct=0.95→tool=0.10 rank=0.99 **TP_lost_to_FN** used_tool=True
  > The query image displays a grainy white shape consistent with the 'irregular organic blob' baseline. Its size and texture fall within the 'minor size variation' and 'texture density' allowed variations described by the p
- `D5c_0120` L=1 direct=0.95→tool=0.10 rank=0.96 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline of an irregular organic mass. Its shape and texture fall within the allowed variations of fragmentation, size, and density defined by the reference profiler.
- `D5c_0155` L=1 direct=0.95→tool=0.10 rank=0.96 **TP_lost_to_FN** used_tool=True
  > The query object is a grainy white shape that fits the 'irregular organic blob' description. Its smaller size and compact form are covered by the allowed variations of 'size variation' and 'shape deformation', making it 
  ... and 3 more losses.

### D5d  (wins 7, losses 9)

Win sample-types: {'FP_corrected': 3, 'FN_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 5, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5d_0173` L=1 direct=0.02→tool=0.95 rank=0.57 **FN_corrected** used_tool=True
  > The query image contains a dark, solid, oval object in the lumen that is not part of the normal mucosal folds or allowed variations (like the endoscope tip or lighting). This deviation from the expected 'pink/tan' color 
- `D5d_0135` L=1 direct=0.02→tool=0.95 rank=0.48 **FN_corrected** used_tool=True
  > The query image shows a dark, solid object within the lumen that is not present in the normal references and does not match any allowed variations (lighting, folds, texture) defined by the profiler. This indicates a clea
- `D5d_0128` L=1 direct=0.02→tool=0.95 rank=0.35 **FN_corrected** used_tool=True
  > The query image displays a large, distinct mass protruding into the lumen, which violates the expected 'tubular lumen with folds' shape and is not an allowed variation like lighting or minor texture. This indicates a sig
- `D5d_0071` L=0 direct=0.95→tool=0.05 rank=0.47 **FP_corrected** used_tool=True
  > The yellow patch in the query image corresponds to 'yellow bile residue', which is explicitly listed as an allowed variation in the normal baseline. Therefore, the image is considered normal.
- `D5d_0023` L=0 direct=0.98→tool=0.10 rank=0.39 **FP_corrected** used_tool=True
  > The reference profiler explicitly lists 'yellow' as an expected color for the normal baseline. The yellow discoloration in the query image matches this expected attribute, suggesting it is a normal variation rather than 
- `D5d_0045` L=0 direct=0.92→tool=0.05 rank=0.40 **FP_corrected** used_tool=True
  > The query image exhibits features (pink color, smooth folds, lighting reflections) that are explicitly defined as normal or allowed variations by the reference profiler. No anomalous features are detected.
- `D5d_0150` L=1 direct=0.02→tool=0.85 rank=0.59 **FN_corrected** used_tool=True
  > The query image displays a distinct, raised, oval-shaped lesion that is morphologically different from the 'circular folds' and 'focal fold prominence' described as normal variations. While 'focal fold prominence' is all

**LOSSES**:

- `D5d_0074` L=0 direct=0.02→tool=0.95 rank=0.57 **TN_lost_to_FP** used_tool=True
  > The query image contains a raised, lobulated mass (polyp) which is a structural anomaly not covered by the allowed variations of 'focal narrowing' or 'folds' defined in the normal baseline.
- `D5d_0069` L=0 direct=0.02→tool=0.95 rank=0.36 **TN_lost_to_FP** used_tool=True
  > The query image contains a raised, lobulated mass (polyp) which is a distinct structural abnormality not covered by the allowed variations (lighting, fold pattern, debris, viewing angle) defined for normal colonic mucosa
- `D5d_0161` L=1 direct=0.98→tool=0.05 rank=0.51 **TP_lost_to_FN** used_tool=True
  > The yellow discoloration in the query image matches the 'focal yellow discoloration' listed as an allowed variation in the normal baseline, indicating the image is normal.
- `D5d_0129` L=1 direct=0.98→tool=0.10 rank=0.31 **TP_lost_to_FN** used_tool=True
  > The yellow patch in the query image corresponds to the 'yellow' expected color and 'presence of fluid' allowed variation defined by the reference profiler, indicating a normal finding rather than an anomaly.
- `D5d_0146` L=1 direct=0.98→tool=0.10 rank=0.38 **TP_lost_to_FN** used_tool=True
  > The query image displays a colonic lumen with pink/orange mucosa, yellow residue, and specular highlights. These features align with the profiler's 'expected_color' and 'allowed_variation' (mucus presence, lighting refle
- `D5d_0009` L=0 direct=0.02→tool=0.85 rank=0.30 **TN_lost_to_FP** used_tool=True
  > The query image displays a distinct white spot on the mucosa near the endoscope tip. While the endoscope tip itself is an allowed variation, the white spot is not a mucus reflection, lighting variation, or fold prominenc
- `D5d_0166` L=1 direct=0.98→tool=0.15 rank=0.47 **TP_lost_to_FN** used_tool=True
  > The query image shows colonic mucosa with pink coloration and smooth folds, consistent with the normal baseline. The yellowish material appears to be mucus or residue, which is an allowed variation. No obvious pathologic
- `D5d_0093` L=1 direct=0.92→tool=0.10 rank=0.30 **TP_lost_to_FN** used_tool=True
  > The yellow discoloration in the query image matches the 'pale yellow' expected color and 'slight color variation' allowed by the reference profiler. Therefore, it is considered a normal variation, not an anomaly.
  ... and 1 more losses.

### D6  (wins 6, losses 19)

Win sample-types: {'FP_corrected': 5, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 17}

**WINS** (item · direct→tool · rank · type · rationale):

- `D6_0017` L=0 direct=0.95→tool=0.05 rank=0.75 **FP_corrected** used_tool=True
  > The query image matches the normal baseline profile of a residential grid. All observed differences are consistent with the allowed variations (lighting, vegetation, roof color) and do not constitute an anomaly.
- `D6_0050` L=0 direct=0.99→tool=0.10 rank=0.80 **FP_corrected** used_tool=True
  > The query image matches the normal baseline profile of an 'aerial view of rural landscape' with 'irregular patches and linear paths'. The observed variations are within the allowed range (e.g., vegetation density, soil t
- `D6_0015` L=0 direct=0.98→tool=0.10 rank=0.62 **FP_corrected** used_tool=True
  > The query image matches the normal baseline of a rural landscape. Observed differences are consistent with allowed variations such as vegetation density and crop patterns, indicating the image is normal.
- `D6_0039` L=0 direct=0.95→tool=0.10 rank=0.85 **FP_corrected** used_tool=True
  > The query image shows an aerial view of agricultural fields with a road, matching the normal baseline. All observed variations (color, texture) fall within the allowed variation categories, indicating this is a normal sa
- `D6_0000` L=0 direct=0.95→tool=0.10 rank=0.82 **FP_corrected** used_tool=True
  > The query image matches the normal baseline of an agricultural field with a rectangular pattern. The observed features, including the line of trees and field texture, fall within the allowed variations of crop density an
- `D6_0035` L=0 direct=0.98→tool=0.85 rank=0.64 **other** used_tool=True
  > The query image shows a significant structural difference in land cover (large bare ground area vs. vegetated/mounded areas in references) that exceeds the allowed 'vegetation density variation'. This suggests an anomaly

**LOSSES**:

- `D6_0144` L=1 direct=1.00→tool=0.05 rank=0.98 **TP_lost_to_FN** used_tool=True
  > The query image depicts a grassy field with tracks, which matches the normal baseline profile extracted from the references. The observed features fall within the allowed variations (texture, track density), confirming t
- `D6_0151` L=1 direct=0.99→tool=0.05 rank=0.92 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline profile (rural landscape, pond, irregular terrain) extracted from the references. No anomalous features are present.
- `D6_0149` L=1 direct=0.98→tool=0.05 rank=0.55 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline profile (suburban aerial view, grid layout, expected colors). Observed differences are minor rotation and lighting, which are explicitly allowed variations, so the image is nor
- `D6_0117` L=1 direct=0.99→tool=0.10 rank=0.78 **TP_lost_to_FN** used_tool=True
  > The query image aligns with the normal baseline of a rural landscape with fields and roads. All observed features (colors, shapes, variations) fall within the allowed variations defined by the reference profiler. No anom
- `D6_0116` L=1 direct=0.99→tool=0.10 rank=0.70 **TP_lost_to_FN** used_tool=True
  > The reference profiler identified the normal baseline as a 'construction site', which matches the query image. The tool's interpretation explicitly suggests the query is likely normal, indicating that the undeveloped sta
- `D6_0051` L=0 direct=0.02→tool=0.90 rank=0.72 **TN_lost_to_FP** used_tool=True
  > The query image is grayscale, whereas the reference images and the expected baseline are in color (brown, gray, green). This lack of color is not an allowed variation like lighting shift or texture variation, indicating 
- `D6_0133` L=1 direct=0.98→tool=0.10 rank=0.82 **TP_lost_to_FN** used_tool=True
  > The query image displays vertical striping in the field, which aligns with the 'texture variation' and 'crop density variation' listed as allowed variations in the normal baseline. The overall object, shape, and color pa
- `D6_0110` L=1 direct=0.98→tool=0.10 rank=0.36 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline profile with only allowed variations (lighting shift, vegetation density). No structural anomalies or unexpected objects are present.
  ... and 11 more losses.

### D7  (wins 2, losses 3)

Win sample-types: {'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D7_0135` L=1 direct=0.02→tool=1.00 rank=0.97 **FN_corrected** used_tool=True
  > The query image depicts a horse-drawn carriage in a public square, which fundamentally differs from the 'urban street view from vehicle' baseline established by the reference images. This deviation is not an allowed vari
- `D7_0159` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=True
  > The query image depicts a rural scene with a car towing a trailer, which deviates significantly from the established 'urban street view' baseline. This change in environment and vehicle activity is not an allowed variati

**LOSSES**:

- `D7_0055` L=0 direct=0.02→tool=0.95 rank=0.61 **TN_lost_to_FP** used_tool=True
  > The presence of a pedestrian standing in the active roadway is not covered by the allowed variations (lighting, weather, traffic density, time of day) and represents a significant deviation from the normal driving scene 
- `D7_0045` L=0 direct=0.02→tool=0.95 rank=0.47 **TN_lost_to_FP** used_tool=True
  > The query image contains a foreign object (a hubcap/wheel rim) on the road surface, which is not part of the normal traffic scene baseline and is not covered by the allowed variations (lighting, density, weather, angle).
- `D7_0172` L=1 direct=0.95→tool=0.05 rank=0.84 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline of a nighttime city street view. All elements (lighting, lane markings, vehicles, buildings) are consistent with the expected object and allowed variations defined by the refer

### D8  (wins 4, losses 5)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2, 'other': 1}
Loss sample-types: {'TP_lost_to_FN': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D8_0072` L=0 direct=0.95→tool=0.10 rank=0.50 **FP_corrected** used_tool=True
  > The query image shows a uniformed pedestrian walking in the plaza. The reference profiler lists 'pedestrian movement' as an allowed variation. Therefore, the presence of this person is consistent with the normal baseline
- `D8_0150` L=1 direct=0.02→tool=0.85 rank=0.50 **FN_corrected** used_tool=True
  > The query image features a person standing still, whereas the normal baseline established by the tool and references is 'pedestrians walking'. Since 'standing still' is not an allowed variation, this deviation in behavio
- `D8_0163` L=1 direct=0.05→tool=0.85 rank=0.50 **FN_corrected** used_tool=True
  > The query image features a person standing on the grass, whereas the normal baseline consists of pedestrians walking on the paved plaza. This deviation in both behavior (standing vs. walking) and location (grass vs. pave
- `D8_0102` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The query image depicts people in a station plaza, consistent with the normal baseline. Although there are uniformed individuals, their presence and interaction can be considered a form of 'pedestrian movement' or a norm

**LOSSES**:

- `D8_0138` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The query image shows a pedestrian walking in the station plaza, which is consistent with the normal baseline. The person's blue pants are within the expected color range, and the movement is an allowed variation. No ano
- `D8_0133` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The query image shows pedestrians walking in the same station plaza environment with similar architectural features. The scene appears consistent with the normal baseline - people are moving naturally, the structure matc
- `D8_0126` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The query image depicts a pedestrian (uniformed) walking in the station plaza, which aligns with the 'pedestrian movement' allowed variation identified by the reference profiler. The architectural structure also matches 
- `D8_0119` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The query image depicts a person jumping, which falls under the 'pedestrian movement' allowed variation defined by the reference profiler. The scene structure and colors are consistent with the normal baseline, so this i
- `D8_0179` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline profile with pedestrians in a station plaza and no deviations from allowed variations.

### D9  (wins 7, losses 10)

Win sample-types: {'FP_corrected': 6, 'FN_corrected': 1}
Loss sample-types: {'TP_lost_to_FN': 10}

**WINS** (item · direct→tool · rank · type · rationale):

- `D9_0089` L=0 direct=0.95→tool=0.00 rank=0.14 **FP_corrected** used_tool=True
  > The query image exhibits differences in liquid color and label icon, but the reference profiler explicitly lists both as allowed variations. Therefore, the query is classified as normal.
- `D9_0022` L=0 direct=0.99→tool=0.05 rank=0.28 **FP_corrected** used_tool=True
  > The query image matches the normal baseline profile: correct object type, allowed cable color (yellow), and permitted variations (minor curvature, single connector configuration). No anomalies detected.
- `D9_0078` L=0 direct=0.99→tool=0.05 rank=0.11 **FP_corrected** used_tool=True
  > The query image matches the normal baseline: it is a fiber optic patch cord with a horizontal linear connection. The single connector stack and slight cable curvature are explicitly listed as allowed variations in the re
- `D9_0039` L=0 direct=0.98→tool=0.05 rank=0.05 **FP_corrected** used_tool=True
  > The query image contains the expected objects and colors. The difference in fruit arrangement is explicitly listed as an allowed variation ('slight arrangement shift'), so it is not an anomaly.
- `D9_0079` L=0 direct=0.98→tool=0.05 rank=0.16 **FP_corrected** used_tool=True
  > The query image contains the expected hardware fasteners with allowed position variation, matching the normal baseline profile.
- `D9_0057` L=0 direct=0.99→tool=0.10 rank=0.35 **FP_corrected** used_tool=True
  > The query image matches the normal baseline: correct object type, expected colors, and allowed variations (minor curvature, connector orientation). No anomalous features detected.
- `D9_0174` L=1 direct=0.02→tool=0.85 rank=0.25 **FN_corrected** used_tool=True
  > The query image is missing one hexagonal nut compared to the consistent count of two nuts seen in all reference images. This missing component is a structural anomaly not explained by the allowed variations of position o

**LOSSES**:

- `D9_0154` L=1 direct=0.98→tool=0.00 rank=0.55 **TP_lost_to_FN** used_tool=True
  > The query image exhibits a different label icon (cherry vs. banana) and liquid color (dark vs. light) compared to the references. The reference profiler explicitly lists both 'label icon variation' and 'liquid color vari
- `D9_0127` L=1 direct=0.95→tool=0.00 rank=0.20 **TP_lost_to_FN** used_tool=True
  > The query image exhibits differences in liquid color and label icon, but the reference profiler explicitly lists both as allowed variations. Therefore, the query is considered normal.
- `D9_0128` L=1 direct=0.99→tool=0.05 rank=0.24 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline profile: it is a fiber optic patch cord with a horizontal connection, yellow color, and minor curvature, all of which are explicitly listed as allowed variations or expected at
- `D9_0100` L=1 direct=0.99→tool=0.05 rank=0.41 **TP_lost_to_FN** used_tool=True
  > The query image exhibits a yellow fiber optic patch cord with minor curvature, which falls within the allowed variations (color, shape, curvature) defined by the normal reference images. No anomalous features are detecte
- `D9_0176` L=1 direct=0.99→tool=0.05 rank=0.31 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline: a single fiber optic patch cord with a horizontal linear connection and minor curvature, all within allowed variations. No anomalies detected.
- `D9_0178` L=1 direct=0.98→tool=0.05 rank=0.66 **TP_lost_to_FN** used_tool=True
  > The query image shows a single fiber optic patch cord with yellow color and horizontal linear shape, matching the baseline. The difference in connector stack height (1 vs 2 or 4 in refs) is explicitly listed as an allowe
- `D9_0090` L=1 direct=0.98→tool=0.05 rank=0.03 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline defined by the references: a bento box with granola, dried fruit, and fresh fruit (2 oranges, 1 nectarine/peach). The specific arrangement of items falls within the 'allowed_va
- `D9_0129` L=1 direct=0.98→tool=0.05 rank=0.04 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal baseline of a bento box with fruit and granola. The slight difference in item arrangement is explicitly listed as an allowed variation, so it is not an anomaly.
  ... and 2 more losses.

---

## tool_reference_retriever  (41 wins, 91 losses, net flips -46 on n=400)

### D1  (wins 6, losses 7)

Win sample-types: {'FP_corrected': 6}
Loss sample-types: {'TP_lost_to_FN': 6, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D1_0016` L=0 direct=0.98→tool=0.05 rank=0.06 **FP_corrected** used_tool=False
  > The query image is visually consistent with the provided normal reference images, showing a standard three-core cable cross-section without any apparent anomalies.
- `D1_0064` L=0 direct=0.98→tool=0.05 rank=0.24 **FP_corrected** used_tool=True
  > The query image is highly similar to retrieved normal reference images, indicating it belongs to the normal class. No anomalies are detected.
- `D1_0084` L=0 direct=0.95→tool=0.05 rank=0.02 **FP_corrected** used_tool=False
  > The query image exhibits the same speckled pattern and texture as the normal reference images, with no detectable anomalies.
- `D1_0088` L=0 direct=0.95→tool=0.05 rank=0.29 **FP_corrected** used_tool=False
  > The query image is visually consistent with the provided normal reference images, showing a correctly mounted transistor with no apparent anomalies.
- `D1_0009` L=0 direct=0.95→tool=0.05 rank=0.13 **FP_corrected** used_tool=False
  > The query image is visually consistent with the provided normal reference images, showing a standard three-core cable cross-section with no detectable anomalies.
- `D1_0038` L=0 direct=0.98→tool=0.10 rank=0.26 **FP_corrected** used_tool=False
  > The query image is consistent with the majority of the normal reference images, showing the 'actavis' logo and '500' imprint clearly. The slight variation in one reference image does not indicate an anomaly in the query.

**LOSSES**:

- `D1_0094` L=1 direct=0.98→tool=0.00 rank=0.77 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the provided normal reference images, showing no signs of anomaly such as damage, incorrect labeling, or discoloration.
- `D1_0111` L=1 direct=0.98→tool=0.05 rank=0.77 **TP_lost_to_FN** used_tool=False
  > The query image is visually indistinguishable from the normal reference images, showing the same consistent woven texture without any apparent defects or anomalies.
- `D1_0137` L=1 direct=0.98→tool=0.05 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The query image is highly similar to the retrieved normal reference images, indicating it belongs to the normal class. No visual defects or deviations from the normal pattern are observed.
- `D1_0117` L=1 direct=0.98→tool=0.10 rank=0.68 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a typical hazelnut without any apparent defects or anomalies.
- `D1_0142` L=1 direct=0.95→tool=0.10 rank=0.32 **TP_lost_to_FN** used_tool=True
  > The high similarity scores from the reference retriever indicate that the query image's texture, including the light streaks, matches known normal samples well. Therefore, it is classified as normal.
- `D1_0179` L=1 direct=0.95→tool=0.10 rank=0.54 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing the same type of component with expected variations in orientation and lighting. No anomalies are detected.
- `D1_0167` L=1 direct=0.98→tool=0.80 rank=0.85 **other** used_tool=False
  > The query image contains a visible dark smudge/stain on the fabric in the bottom right corner that is not present in any of the normal reference images, indicating a potential anomaly.

### D10  (wins 3, losses 6)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 1}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D10_0002` L=0 direct=0.95→tool=0.01 rank=0.07 **FP_corrected** used_tool=False
  > The query image is visually consistent with the provided normal reference images, showing no signs of defects or anomalies.
- `D10_0156` L=1 direct=0.01→tool=0.95 rank=0.51 **FN_corrected** used_tool=False
  > The query image is anomalous because the ultrasonic transducers lack the mesh grille present in all normal reference images, appearing as solid metallic discs instead.
- `D10_0076` L=0 direct=0.98→tool=0.05 rank=0.12 **FP_corrected** used_tool=False
  > The query image is visually consistent with the provided normal reference images of the HC-SR04 module. No anomalies such as missing components, incorrect orientation, or physical damage are detected.

**LOSSES**:

- `D10_0136` L=1 direct=0.98→tool=0.00 rank=0.23 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard HC-SR04 module with all expected components intact and no visible anomalies.
- `D10_0027` L=0 direct=0.01→tool=0.95 rank=0.10 **TN_lost_to_FP** used_tool=False
  > The query image contains the text 'HW-168' near the 'IN+' label, which is absent in all four normal reference images. This missing/extra text is a definitive visual anomaly.
- `D10_0153` L=1 direct=0.98→tool=0.05 rank=0.62 **TP_lost_to_FN** used_tool=True
  > The reference retriever found highly similar normal images (similarity > 0.96), indicating the query belongs to the normal distribution despite minor visual differences from the initial set. The interpretation confirms t
- `D10_0140` L=1 direct=0.98→tool=0.05 rank=0.30 **TP_lost_to_FN** used_tool=True
  > The query image is highly similar to known normal reference images (similarity > 0.97), indicating it belongs to the normal class. The apparent rotation is a normal variation, not a defect.
- `D10_0158` L=1 direct=0.98→tool=0.05 rank=0.48 **TP_lost_to_FN** used_tool=True
  > The query image is highly similar to known normal cashews in the dataset, indicating the small spot is a natural variation and not an anomaly.
- `D10_0139` L=1 direct=0.98→tool=0.10 rank=0.20 **TP_lost_to_FN** used_tool=True
  > The tool retrieved highly similar normal reference images (top similarity 0.98), suggesting the query image, including the small dot, falls within the normal variation of the dataset. The high similarity score overrides 

### D2  (wins 4, losses 11)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 9}

**WINS** (item · direct→tool · rank · type · rationale):

- `D2_0095` L=1 direct=0.02→tool=1.00 rank=0.86 **FN_corrected** used_tool=False
  > The query image depicts a bottle filled with dark liquid, while all reference images show the same bottle type empty. This discrepancy in the bottle's state (filled vs. empty) constitutes a definitive anomaly.
- `D2_0092` L=1 direct=0.01→tool=0.95 rank=0.63 **FN_corrected** used_tool=True
  > The query image contains a plastic straw wrapper attached to the front of the carton, which is a clear visual deviation from the normal reference images that show the carton without any attached accessories. This confirm
- `D2_0037` L=0 direct=0.98→tool=0.10 rank=0.19 **FP_corrected** used_tool=False
  > The query image displays a standard back view of the snack package, consistent with the normal reference images. No anomalies such as damage, missing labels, or unusual markings are visible.
- `D2_0159` L=1 direct=0.01→tool=0.15 rank=0.99 **other** used_tool=True
  > High similarity to normal reference images (top 0.69) strongly suggests the query is normal. The bottle shows standard back label layout with no visible defects, damage, or anomalies.

**LOSSES**:

- `D2_0056` L=0 direct=0.01→tool=0.95 rank=0.05 **TN_lost_to_FP** used_tool=False
  > The query image features a completely different packaging design (blue background, comic style) compared to the consistent white packaging with realistic fruit imagery seen in all reference images, indicating a clear ano
- `D2_0087` L=0 direct=0.01→tool=0.95 rank=0.08 **TN_lost_to_FP** used_tool=False
  > The query image displays the cigarette pack upside down, with the text inverted relative to the normal reference images, indicating a clear anomaly in orientation.
- `D2_0133` L=1 direct=0.98→tool=0.05 rank=0.08 **TP_lost_to_FN** used_tool=False
  > The query image is visually indistinguishable from the normal reference images, showing the same product packaging without any apparent anomalies.
- `D2_0170` L=1 direct=0.98→tool=0.05 rank=0.13 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images showing the front of the same product package. No anomalies are detected.
- `D2_0169` L=1 direct=0.98→tool=0.05 rank=0.83 **TP_lost_to_FN** used_tool=True
  > The reference retriever found highly similar normal images (top similarity 0.94) matching the query's specific design (English text and tower graphic). This confirms the query belongs to a normal cluster, despite differi
- `D2_0097` L=1 direct=0.98→tool=0.05 rank=0.73 **TP_lost_to_FN** used_tool=False
  > The query image depicts a normal, intact product carton that is consistent with the provided reference images. No anomalies are detected.
- `D2_0167` L=1 direct=0.98→tool=0.05 rank=0.18 **TP_lost_to_FN** used_tool=True
  > The reference retriever found normal images with very high similarity (0.97) to the query. According to the tool's interpretation, this indicates the query belongs to a normal cluster, suggesting the perceived difference
- `D2_0153` L=1 direct=0.95→tool=0.05 rank=0.74 **TP_lost_to_FN** used_tool=False
  > The query image displays a standard Vitasoy carton that matches the appearance of the normal reference images, showing no signs of damage, tampering, or unusual features.
  ... and 3 more losses.

### D4  (wins 0, losses 8)

Win sample-types: {}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 7}

**LOSSES**:

- `D4_0086` L=0 direct=0.05→tool=0.95 rank=0.76 **TN_lost_to_FP** used_tool=False
  > The query image contains a prominent vertical linear defect (crack/seam) that is absent in the normal reference images, which only exhibit random surface speckling. This structural deviation is a strong indicator of an a
- `D4_0126` L=1 direct=0.95→tool=0.10 rank=0.63 **TP_lost_to_FN** used_tool=True
  > The high similarity scores (0.82 top) from the reference retriever strongly indicate the query image belongs to the normal distribution. The visual features match the normal reference patterns, with no clear anomalous ch
- `D4_0128` L=1 direct=0.95→tool=0.10 rank=0.42 **TP_lost_to_FN** used_tool=False
  > The query image displays typical concrete surface texture with minor imperfections that are consistent with the normal reference images. No distinct anomaly is observed.
- `D4_0152` L=1 direct=0.95→tool=0.10 rank=0.75 **TP_lost_to_FN** used_tool=True
  > The query image is highly similar to retrieved normal reference images (top similarity 0.80), indicating the observed crack and spots are consistent with normal variations in this domain.
- `D4_0155` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The query image displays surface features (pits, small dark spots) that are consistent with the variations observed in the provided normal reference images. There is no clear evidence of an anomaly.
- `D4_0174` L=1 direct=0.95→tool=0.15 rank=0.75 **TP_lost_to_FN** used_tool=True
  > The retrieved normal references have a high similarity (0.69) to the query, and the tool's interpretation indicates that a good match to a normal cluster suggests the image is normal. The dark spot in the query appears t
- `D4_0106` L=1 direct=0.95→tool=0.15 rank=0.49 **TP_lost_to_FN** used_tool=True
  > The query image displays a concrete surface with a shadow, which is a common normal variation. The reference retriever found similar normal samples, and the tool's interpretation warns that low similarity scores do not c
- `D4_0130` L=1 direct=0.95→tool=0.15 rank=0.57 **TP_lost_to_FN** used_tool=True
  > The reference retriever found normal samples with moderate-to-high similarity (0.678), suggesting the query's features (including the dark spot) are consistent with normal texture variations in this domain. The disconfir

### D5  (wins 0, losses 11)

Win sample-types: {}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 10}

**LOSSES**:

- `D5_0030` L=0 direct=0.05→tool=0.95 rank=0.21 **TN_lost_to_FP** used_tool=False
  > The query image shows a diffuse, reddish-purple lesion that lacks the defined borders and brown pigmentation characteristic of the normal nevi in the reference images, indicating a significant visual anomaly.
- `D5_0099` L=1 direct=0.95→tool=0.10 rank=0.65 **TP_lost_to_FN** used_tool=True
  > The query image shows a pigmented lesion that is highly similar to retrieved normal reference images (top similarity 0.78). This strong match to the normal class, combined with the lesion's relatively uniform color and s
- `D5_0176` L=1 direct=0.95→tool=0.10 rank=0.46 **TP_lost_to_FN** used_tool=False
  > The query image shows a pigmented lesion with features (uniform color, regular structure) that are consistent with the normal reference images provided. There are no clear indicators of anomaly such as irregular borders,
- `D5_0115` L=1 direct=0.95→tool=0.10 rank=0.57 **TP_lost_to_FN** used_tool=False
  > The query image exhibits features (symmetry, uniform color, regular borders) that align closely with the provided normal reference images, suggesting it is a benign lesion.
- `D5_0167` L=1 direct=0.95→tool=0.10 rank=0.48 **TP_lost_to_FN** used_tool=False
  > The query image displays features (symmetry, reticular pattern, uniform color) that are consistent with the provided normal reference images of pigmented skin lesions. There are no clear visual indicators of anomaly base
- `D5_0164` L=1 direct=0.95→tool=0.10 rank=0.54 **TP_lost_to_FN** used_tool=True
  > The tool found highly similar normal reference images (top similarity 0.775), and the interpretation indicates this strongly suggests the query is normal. The visual appearance of the query matches these normal examples.
- `D5_0155` L=1 direct=0.95→tool=0.15 rank=0.65 **TP_lost_to_FN** used_tool=False
  > The query image shows a pigmented lesion that is visually consistent with the provided normal reference images, exhibiting typical characteristics of a benign mole such as relatively uniform pigmentation and a defined, a
- `D5_0117` L=1 direct=0.95→tool=0.15 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The query image has high similarity to retrieved normal reference images, indicating it belongs to the normal class of pigmented skin lesions.
  ... and 3 more losses.

### D5b  (wins 5, losses 10)

Win sample-types: {'FP_corrected': 5}
Loss sample-types: {'TP_lost_to_FN': 9, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5b_0031` L=0 direct=0.98→tool=0.05 rank=0.51 **FP_corrected** used_tool=True
  > The query image has a very high similarity (0.93) to retrieved normal reference images, indicating it belongs to the normal distribution despite the initial color difference.
- `D5b_0067` L=0 direct=0.98→tool=0.05 rank=0.53 **FP_corrected** used_tool=True
  > The query image is highly similar to retrieved normal reference images (similarity > 0.90) and lacks the distinct hyperintense lesions or structural abnormalities seen in the anomalous reference. The high similarity to t
- `D5b_0045` L=0 direct=0.98→tool=0.10 rank=0.31 **FP_corrected** used_tool=False
  > The query image displays normal brain anatomy with no visible abnormalities compared to the reference images. The ventricular system and cortical structures appear typical.
- `D5b_0024` L=0 direct=0.98→tool=0.10 rank=0.44 **FP_corrected** used_tool=True
  > The high similarity (0.92) between the query and the retrieved normal reference images indicates that the query belongs to a normal cluster. The interpretation confirms that matching a normal cluster well suggests the im
- `D5b_0058` L=0 direct=0.95→tool=0.10 rank=0.52 **FP_corrected** used_tool=False
  > The query image displays a typical brain MRI structure with no visible abnormalities such as lesions, hemorrhages, or significant asymmetries when compared to the provided normal reference images.

**LOSSES**:

- `D5b_0152` L=1 direct=0.98→tool=0.05 rank=0.78 **TP_lost_to_FN** used_tool=False
  > The query image displays a normal brain MRI slice with no visible anomalies such as lesions, tumors, or structural deformities. The anatomy appears intact and symmetric.
- `D5b_0156` L=1 direct=0.98→tool=0.05 rank=0.56 **TP_lost_to_FN** used_tool=True
  > The query image has very high similarity (0.94) to known normal reference images, and the tool interpretation confirms this indicates the query likely belongs to the normal cluster. No visual anomalies were detected.
- `D5b_0094` L=1 direct=0.98→tool=0.05 rank=0.60 **TP_lost_to_FN** used_tool=True
  > The query image has high similarity (0.93) to retrieved normal reference images. The tool's interpretation indicates that matching a normal cluster strongly suggests the image is normal, overriding the initial visual sus
- `D5b_0122` L=1 direct=0.98→tool=0.05 rank=0.60 **TP_lost_to_FN** used_tool=False
  > The query image displays a standard brain MRI slice with normal anatomical structures and no visible anomalies such as lesions or abnormal signal intensities, matching the pattern of the provided normal reference images.
- `D5b_0160` L=1 direct=0.95→tool=0.05 rank=0.44 **TP_lost_to_FN** used_tool=True
  > The query image is highly similar to retrieved normal reference images, indicating the observed features are consistent with the normal distribution.
- `D5b_0170` L=1 direct=0.98→tool=0.10 rank=0.67 **TP_lost_to_FN** used_tool=True
  > The high similarity score (0.83) between the query and the retrieved normal references, combined with the tool's interpretation that this indicates a match to a normal cluster, suggests the observed features are not anom
- `D5b_0127` L=1 direct=0.98→tool=0.10 rank=0.58 **TP_lost_to_FN** used_tool=True
  > The high similarity scores (0.94+) to retrieved normal images indicate the query belongs to a normal cluster, overriding the initial visual discrepancy with the first set of references.
- `D5b_0137` L=1 direct=0.98→tool=0.10 rank=0.59 **TP_lost_to_FN** used_tool=True
  > The query image has high similarity to retrieved normal reference images, indicating it belongs to the normal distribution despite visual differences like blurriness. Therefore, it is classified as normal.
  ... and 2 more losses.

### D6  (wins 6, losses 17)

Win sample-types: {'FP_corrected': 5, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 5, 'TP_lost_to_FN': 7, 'other': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D6_0015` L=0 direct=0.98→tool=0.10 rank=0.62 **FP_corrected** used_tool=True
  > Visual comparison shows the query image is consistent with the normal reference images in terms of landscape features, building placement, and road networks. No anomalies were detected.
- `D6_0000` L=0 direct=0.95→tool=0.10 rank=0.82 **FP_corrected** used_tool=False
  > The query image appears visually consistent with the normal reference images, showing typical agricultural field patterns without any clear anomalous features.
- `D6_0017` L=0 direct=0.95→tool=0.10 rank=0.75 **FP_corrected** used_tool=False
  > The query image matches the normal reference images in terms of layout and features, with no visible anomalies.
- `D6_0064` L=0 direct=0.95→tool=0.10 rank=0.39 **FP_corrected** used_tool=True
  > Despite the tool failure, visual comparison shows the query image's residential layout and the presence of a commercial zone in the top right are consistent with the provided normal reference images. No significant anoma
- `D6_0039` L=0 direct=0.95→tool=0.20 rank=0.85 **FP_corrected** used_tool=True
  > The query image depicts a scene consistent with the normal references (rural road and fields). The small dark spot in the field is a minor feature that could be a small structure or natural variation, not a significant a
- `D6_0063` L=0 direct=0.98→tool=0.85 rank=0.60 **other** used_tool=True
  > The query image contains a prominent circular compound with buildings in the lower center that is absent in the normal reference images, which show a different layout in that area. This significant structural discrepancy

**LOSSES**:

- `D6_0024` L=0 direct=0.02→tool=0.95 rank=0.71 **TN_lost_to_FP** used_tool=False
  > The query image displays a large, distinct area of light-colored, textured ground that is absent in the normal reference images, which show uniform dark soil. This deviation in color and texture is a strong indicator of 
- `D6_0117` L=1 direct=0.99→tool=0.10 rank=0.78 **TP_lost_to_FN** used_tool=True
  > The query image depicts a standard rural landscape consistent with the rural areas seen in the reference images. The absence of the suburban development seen in one reference image is likely due to location variation rat
- `D6_0149` L=1 direct=0.98→tool=0.10 rank=0.55 **TP_lost_to_FN** used_tool=True
  > Based on visual comparison, the query image appears consistent with the normal reference images, showing a typical undeveloped lot with scattered structures and vegetation. No clear anomalies are detected.
- `D6_0111` L=1 direct=0.98→tool=0.10 rank=0.66 **TP_lost_to_FN** used_tool=True
  > The query image is visually consistent with the provided normal reference images in terms of landscape, road layout, and building types. No anomalous features are detected.
- `D6_0136` L=1 direct=0.98→tool=0.10 rank=0.70 **TP_lost_to_FN** used_tool=True
  > The query image displays a road and natural terrain similar to the reference images. The pond in the top right is a natural landscape feature and not an anomaly. No defects or foreign objects are visible.
- `D6_0148` L=1 direct=0.98→tool=0.10 rank=0.66 **TP_lost_to_FN** used_tool=True
  > The query image matches the layout of the second normal reference image, which also lacks the large white building seen in the first reference. This indicates the query is a normal view of the location, and the differenc
- `D6_0145` L=1 direct=0.95→tool=0.10 rank=0.65 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing typical rural features without any detectable anomalies.
- `D6_0137` L=1 direct=0.95→tool=0.10 rank=0.38 **TP_lost_to_FN** used_tool=False
  > The query image matches the normal reference images in terms of content and structure, showing no clear signs of anomaly.
  ... and 9 more losses.

### D7  (wins 3, losses 0)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2}
Loss sample-types: {}

**WINS** (item · direct→tool · rank · type · rationale):

- `D7_0159` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=True
  > The query image depicts a vintage car towing a trailer in a rural environment, which is fundamentally different from the modern urban/suburban driving scenes in the normal reference set. The extremely low similarity scor
- `D7_0135` L=1 direct=0.02→tool=0.95 rank=0.97 **FN_corrected** used_tool=False
  > The query image depicts a tourist scene with a horse-drawn carriage in a square, whereas all reference images are dashcam views of driving on roads. The scene content and context are fundamentally different.
- `D7_0022` L=0 direct=0.95→tool=0.05 rank=0.21 **FP_corrected** used_tool=True
  > The tool found a perfect match (similarity 1.0) in the normal reference pool, indicating the scene with the orange barrier is a standard normal variation. Therefore, the query image is classified as normal.

→ RULE candidate: on D7, tool tends to correctly down-weight FPs when subspacead rank ∈ [0.21, 0.21].

### D8  (wins 7, losses 8)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 4, 'other': 2}
Loss sample-types: {'TN_lost_to_FP': 5, 'TP_lost_to_FN': 2, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D8_0114` L=1 direct=0.02→tool=0.90 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a uniformed individual (security/police) walking in the foreground, a feature not present in any of the provided normal reference images which only show civilians. This distinct difference in sub
- `D8_0072` L=0 direct=0.95→tool=0.10 rank=0.50 **FP_corrected** used_tool=True
  > The presence of a uniformed individual in a public area is a common, normal occurrence (e.g., security patrol). The tool failure prevents further verification, but visual inspection suggests no anomaly.
- `D8_0175` L=1 direct=0.02→tool=0.85 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a uniformed individual, which is a distinct visual feature not present in any of the provided normal reference images that only show civilians. This deviation from the reference pattern indicates
- `D8_0115` L=1 direct=0.05→tool=0.80 rank=0.50 **FN_corrected** used_tool=True
  > The query image features a person in a distinct uniform, which is not present in any of the provided normal reference images that show only civilians. This visual discrepancy suggests an anomaly, although the possibility
- `D8_0102` L=1 direct=0.02→tool=0.60 rank=0.50 **FN_corrected** used_tool=True
  > The query image features a person in a distinct uniform, which is not present in any of the four provided normal reference images that only show civilians in casual attire. This deviation from the visual pattern of the r
- `D8_0150` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The query image depicts a person standing still, which differs from the motion in the reference images but is a normal human behavior in this context. No physical anomalies or defects are visible.
- `D8_0177` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The query image depicts a uniformed security officer in a public station, which is a plausible and common occurrence in such environments. The reference images show civilians, but the absence of other anomalies suggests 

**LOSSES**:

- `D8_0065` L=0 direct=0.02→tool=0.90 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed individual (security/police) which is a distinct visual deviation from the reference images that exclusively show civilians. Given the tool failure, this visual discrepancy is treated
- `D8_0008` L=0 direct=0.05→tool=0.90 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed individual (security/police) walking prominently in the foreground, which is a distinct deviation from the reference images that only show civilians in casual attire. This suggests th
- `D8_0138` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The query image depicts a typical scene in a public area with people walking, similar to the reference images. No anomalies are detected.
- `D8_0126` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The query image depicts a normal scene of a person walking in a public area, consistent with the reference images. No anomalies are detected.
- `D8_0009` L=0 direct=0.02→tool=0.85 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image features a uniformed individual, which is a significant deviation from the provided reference images that exclusively show civilians in casual attire. This suggests the presence of the uniformed person is
- `D8_0038` L=0 direct=0.02→tool=0.85 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image features a uniformed individual, which is a significant visual deviation from the provided reference images that exclusively show civilians in casual attire. This suggests the presence of the uniformed pe
- `D8_0050` L=0 direct=0.02→tool=0.85 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed individual, a feature not present in the provided normal reference images which only show civilians. This deviation in subject type suggests an anomaly.
- `D8_0010` L=0 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The presence of a uniformed individual in a public area is likely a normal security patrol. No other anomalous elements are visible in the scene compared to the reference images.

### D9  (wins 7, losses 13)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 10}

**WINS** (item · direct→tool · rank · type · rationale):

- `D9_0121` L=1 direct=0.01→tool=1.00 rank=0.58 **FN_corrected** used_tool=False
  > The query image differs significantly from all reference images in both the label illustration (cherry vs. banana) and the liquid color (dark red vs. light beige), indicating it is an anomaly.
- `D9_0057` L=0 direct=0.99→tool=0.05 rank=0.35 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard patch cable on the expected background. No anomalies are detected.
- `D9_0078` L=0 direct=0.99→tool=0.05 rank=0.11 **FP_corrected** used_tool=False
  > The query image matches the normal reference pattern of a single jumper wire between terminal blocks. No anomalies detected.
- `D9_0168` L=1 direct=0.01→tool=0.95 rank=0.73 **FN_corrected** used_tool=False
  > The query image differs significantly from all reference images in both the label icon (cherry vs. banana/orange) and the liquid color (dark red vs. light yellow/white), indicating a strong anomaly.
- `D9_0022` L=0 direct=0.99→tool=0.10 rank=0.28 **FP_corrected** used_tool=False
  > The query image matches the pattern of normal reference images: jumper wires connecting terminal blocks on a mesh background. No structural or contextual anomalies are detected.
- `D9_0039` L=0 direct=0.98→tool=0.10 rank=0.05 **FP_corrected** used_tool=False
  > The query image is visually consistent with the reference images, showing a standard arrangement of food items in a lunchbox. The slight variation in fruit placement is expected and does not indicate an anomaly.
- `D9_0079` L=0 direct=0.98→tool=0.10 rank=0.16 **FP_corrected** used_tool=False
  > The query image displays standard hardware components (bolts, nuts, washers) in a plastic bag, consistent with the content of the reference images. No visual defects or unexpected objects are present.

**LOSSES**:

- `D9_0047` L=0 direct=0.02→tool=1.00 rank=0.13 **TN_lost_to_FP** used_tool=False
  > The query image displays a cherry-labeled bottle with red liquid, whereas all reference images show banana-labeled bottles with light liquid. This significant difference in label and content color indicates an anomaly.
- `D9_0032` L=0 direct=0.02→tool=1.00 rank=0.07 **TN_lost_to_FP** used_tool=False
  > The query image is anomalous because the liquid color (red) and label (cherry) differ significantly from the normal reference images (white liquid, banana label).
- `D9_0100` L=1 direct=0.99→tool=0.05 rank=0.41 **TP_lost_to_FN** used_tool=False
  > The query image matches the pattern of the normal reference images showing a single yellow wire. There are no visible defects or deviations from the normal class.
- `D9_0128` L=1 direct=0.99→tool=0.05 rank=0.24 **TP_lost_to_FN** used_tool=False
  > The query image depicts a standard single yellow jumper wire setup, which matches the configuration seen in two of the provided normal reference images. No anomalies are detected.
- `D9_0157` L=1 direct=0.99→tool=0.05 rank=0.48 **TP_lost_to_FN** used_tool=False
  > The query image depicts a standard single yellow jumper wire connection, which matches the configuration seen in multiple normal reference images (1, 2, 4). There are no visible anomalies such as breaks, disconnections, 
- `D9_0173` L=1 direct=0.99→tool=0.05 rank=0.15 **TP_lost_to_FN** used_tool=True
  > The query image matches the configuration of multiple retrieved normal references with high similarity (0.86), indicating it is a standard normal sample. The presence of granola, dried bananas, and almonds is confirmed a
- `D9_0041` L=0 direct=0.02→tool=0.95 rank=0.79 **TN_lost_to_FP** used_tool=False
  > The query image contains a red liquid with a cherry label, whereas all reference images contain light-colored liquids with banana or orange labels. This significant difference in content indicates the query is anomalous.
- `D9_0165` L=1 direct=0.98→tool=0.05 rank=0.16 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the provided normal reference images, showing a standard arrangement of healthy food items in a compartmentalized container without any apparent defects or anomalies.
  ... and 5 more losses.

---

## tool_rotate_align  (56 wins, 107 losses, net flips -39 on n=480)

### D1  (wins 7, losses 8)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 1, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 3, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D1_0114` L=1 direct=0.02→tool=0.95 rank=0.19 **FN_corrected** used_tool=False
  > The query image has yellow bristles, whereas all reference images have either blue or red bristles. This color discrepancy strongly suggests the query is anomalous.
- `D1_0084` L=0 direct=0.95→tool=0.05 rank=0.02 **FP_corrected** used_tool=False
  > The query image exhibits the same speckled texture and pattern distribution as the reference images, with no detectable anomalies.
- `D1_0088` L=0 direct=0.95→tool=0.05 rank=0.29 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a correctly mounted transistor with no apparent anomalies.
- `D1_0038` L=0 direct=0.98→tool=0.10 rank=0.26 **FP_corrected** used_tool=True
  > The query image matches the reference images in content (logo and text). The small difference detected by the tool is likely due to minor lighting or color variations, as suggested by the tool's disconfirm clause, indica
- `D1_0064` L=0 direct=0.98→tool=0.10 rank=0.24 **FP_corrected** used_tool=True
  > The low mean difference and the tool's disconfirm clause indicating potential lighting variations suggest the query image is normal. Visual inspection confirms the capsule matches the reference.
- `D1_0009` L=0 direct=0.95→tool=0.10 rank=0.13 **FP_corrected** used_tool=True
  > Despite the tool's reported mean difference, the disconfirm clause indicates this is likely due to lighting or color variation. Visual inspection confirms the cable structure (three conductors with green, blue, and brown
- `D1_0156` L=1 direct=0.02→tool=0.15 rank=0.47 **other** used_tool=True
  > The observed differences are consistent with natural variation in speckle patterns seen across reference images. The tool's disconfirm clause indicates the residual difference is likely due to lighting/color variation ra

**LOSSES**:

- `D1_0008` L=0 direct=0.02→tool=0.95 rank=0.12 **TN_lost_to_FP** used_tool=False
  > The query image has yellow bristles, whereas all reference images have either blue or red bristles. This color difference is a definitive visual anomaly.
- `D1_0142` L=1 direct=0.95→tool=0.10 rank=0.32 **TP_lost_to_FN** used_tool=True
  > The visual difference is a variation in wood grain pattern (lighter streaks), which is a natural characteristic of wood textures. The tool's interpretation also suggests the signal is likely due to normal variation and t
- `D1_0019` L=0 direct=0.02→tool=0.85 rank=0.36 **TN_lost_to_FP** used_tool=True
  > The query image displays a hazelnut with a distinctly dark, jagged, and irregular scar at the base, which contrasts sharply with the smoother, lighter, and more uniform scars seen on the normal reference images. This str
- `D1_0111` L=1 direct=0.98→tool=0.15 rank=0.77 **TP_lost_to_FN** used_tool=True
  > The rotation alignment showed differences but the interpretation explicitly states these could be lighting/color variations and the query is likely normal. No clear structural anomalies are visible in the fabric pattern 
- `D1_0179` L=1 direct=0.95→tool=0.15 rank=0.54 **TP_lost_to_FN** used_tool=True
  > The alignment tool indicated a residual difference, but the interpretation explicitly stated this could be lighting variation and the query is likely normal. Visual inspection confirms the structure matches the reference
- `D1_0066` L=0 direct=0.02→tool=0.20 rank=0.25 **other** used_tool=True
  > The alignment difference is low and the tool's interpretation explicitly states that such residuals can be due to lighting/color variation, suggesting the image is likely normal despite the signal.
- `D1_0044` L=0 direct=0.01→tool=0.15 rank=0.37 **other** used_tool=True
  > Despite the high mean difference, the tool's interpretation explicitly states the query is likely NORMAL and attributes the difference to lighting/color variation. Without additional tools to verify specific regions, I f
- `D1_0015` L=0 direct=0.02→tool=0.15 rank=0.22 **other** used_tool=True
  > The low mean difference and the tool's warning about lighting variations suggest the observed differences are likely normal noise rather than a defect. The query image appears structurally identical to the reference.

### D10  (wins 2, losses 6)

Win sample-types: {'FP_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 2, 'other': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D10_0076` L=0 direct=0.98→tool=0.00 rank=0.12 **FP_corrected** used_tool=False
  > The query image matches the reference images in all visible aspects, including component placement, text labels, and overall structure. No anomalies are detected.
- `D10_0002` L=0 direct=0.95→tool=0.10 rank=0.07 **FP_corrected** used_tool=True
  > The tool's interpretation suggests the observed difference is likely due to lighting/color variation rather than a true anomaly, and the visual content of the query matches the reference images.

**LOSSES**:

- `D10_0027` L=0 direct=0.01→tool=0.95 rank=0.10 **TN_lost_to_FP** used_tool=False
  > The query image contains the text 'HW-168' next to 'IN+', which is not present in any of the normal reference images. This is a distinct visual difference indicating an anomaly.
- `D10_0057` L=0 direct=0.01→tool=0.95 rank=0.08 **TN_lost_to_FP** used_tool=False
  > The query image is missing the 'HW-168' text label that is clearly visible in all reference images, indicating a defect or anomaly in the PCB printing.
- `D10_0140` L=1 direct=0.98→tool=0.05 rank=0.30 **TP_lost_to_FN** used_tool=True
  > The alignment tool reported a low mean difference (25.7) and explicitly noted that such residuals often stem from lighting variations rather than defects. The disconfirm clause suggests the query is likely normal despite
- `D10_0097` L=1 direct=0.99→tool=0.10 rank=0.34 **TP_lost_to_FN** used_tool=True
  > The high difference score is likely due to lighting or color variation as indicated by the tool's disconfirm clause and the noisy nature of the diff image. No structural anomalies are evident.
- `D10_0069` L=0 direct=0.02→tool=0.20 rank=0.27 **other** used_tool=True
  > The post-alignment difference is likely due to lighting/color variation as indicated by the tool's disconfirm clause. The object shape and texture appear consistent with normal references.
- `D10_0158` L=1 direct=0.98→tool=0.85 rank=0.48 **other** used_tool=True
  > The query image contains a distinct dark spot on the cashew surface that is absent in all reference images. While the alignment tool suggested the difference could be lighting, the spot appears as a localized defect rath

### D2  (wins 4, losses 16)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 7, 'TP_lost_to_FN': 9}

**WINS** (item · direct→tool · rank · type · rationale):

- `D2_0092` L=1 direct=0.01→tool=1.00 rank=0.63 **FN_corrected** used_tool=False
  > The query image contains an extra object (a straw wrapper) on the product packaging that is absent in all normal reference images, indicating a clear anomaly.
- `D2_0095` L=1 direct=0.02→tool=1.00 rank=0.86 **FN_corrected** used_tool=False
  > The query image displays a bottle with dark liquid, which is fundamentally different from the white-labeled, clear-liquid bottles in the reference set.
- `D2_0037` L=0 direct=0.98→tool=0.10 rank=0.19 **FP_corrected** used_tool=True
  > The rotation alignment tool indicated a likely normal result despite a moderate difference score, attributing it to potential lighting or color variations. Visual inspection confirms the query image is the same product a
- `D2_0145` L=1 direct=0.02→tool=0.20 rank=0.71 **other** used_tool=True
  > Although the alignment tool showed a difference, the interpretation explicitly states that such residuals can be due to lighting/color and the query is likely normal. The overall structure and design elements (red top, d

**LOSSES**:

- `D2_0056` L=0 direct=0.01→tool=1.00 rank=0.05 **TN_lost_to_FP** used_tool=False
  > The query image displays a different product packaging design than the normal reference images, indicating an anomaly.
- `D2_0038` L=0 direct=0.01→tool=1.00 rank=0.62 **TN_lost_to_FP** used_tool=False
  > The query image displays the product box upside down, which is a significant deviation from the normal upright orientation seen in the reference images.
- `D2_0080` L=0 direct=0.02→tool=1.00 rank=0.02 **TN_lost_to_FP** used_tool=False
  > The query image shows the back of the product packaging, while the reference images consistently show the front, making it an anomaly.
- `D2_0087` L=0 direct=0.01→tool=0.95 rank=0.08 **TN_lost_to_FP** used_tool=True
  > The query image is clearly upside down relative to the reference images, with inverted text and logo. The rotation tool failed to detect this 180-degree flip, but the visual evidence of inversion is definitive for an ano
- `D2_0023` L=0 direct=0.01→tool=0.95 rank=0.06 **TN_lost_to_FP** used_tool=True
  > The query image displays the side of the noodle cup (with QR code), whereas the reference images display the front and back labels. This represents a different view of the product not covered by the normal references, ma
- `D2_0072` L=0 direct=0.02→tool=0.95 rank=0.06 **TN_lost_to_FP** used_tool=True
  > The query image shows the back of the chip bag, whereas the reference images show the front. This is a clear content anomaly, confirmed by the high alignment difference score which is not explained away by the tool's dis
- `D2_0044` L=0 direct=0.02→tool=0.95 rank=0.12 **TN_lost_to_FP** used_tool=False
  > The query image shows a different back panel design (marketing text vs. nutritional info) compared to the normal reference images, indicating an anomaly in the product packaging.
- `D2_0169` L=1 direct=0.98→tool=0.10 rank=0.83 **TP_lost_to_FN** used_tool=False
  > The query image shows the back of the cigarette pack while references show the front. This is a normal variation (different sides of the same object), not an anomaly.
  ... and 8 more losses.

### D4  (wins 6, losses 10)

Win sample-types: {'FN_corrected': 4, 'other': 2}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 4, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D4_0115` L=1 direct=0.05→tool=0.95 rank=0.12 **FN_corrected** used_tool=False
  > The query image contains a large, dark shadow or stain that is absent in all normal reference images, indicating a clear visual anomaly.
- `D4_0176` L=1 direct=0.05→tool=0.95 rank=0.82 **FN_corrected** used_tool=True
  > The query image displays large rocks and debris at the bottom, which is a significant structural deviation from the uniform, fine-grained texture seen in all reference images. The tool's failure to align confirms a funda
- `D4_0105` L=1 direct=0.05→tool=0.95 rank=0.06 **FN_corrected** used_tool=False
  > The query image contains a large dark region (shadow or stain) that is absent in all normal reference images, indicating a clear anomaly.
- `D4_0122` L=1 direct=0.05→tool=0.95 rank=0.79 **FN_corrected** used_tool=False
  > The query image contains a prominent dark shadow in the bottom-left corner that is absent in all normal reference images, indicating a clear anomaly.
- `D4_0110` L=1 direct=0.05→tool=0.20 rank=0.70 **other** used_tool=True
  > Although the alignment tool reported a difference, the interpretation clause warns this could be lighting/color variation on a textured surface. Visually, the query image's texture and features are consistent with the na
- `D4_0121` L=1 direct=0.05→tool=0.20 rank=0.47 **other** used_tool=True
  > The tool's interpretation explicitly states that the residual difference may be due to lighting/color variation and suggests the query is likely normal. The visual texture in the query matches the general pattern of the 

**LOSSES**:

- `D4_0026` L=0 direct=0.05→tool=0.95 rank=0.28 **TN_lost_to_FP** used_tool=False
  > The query image exhibits a significant blue color cast that is not present in any of the normal reference images, which are all gray. This color deviation is a clear anomaly.
- `D4_0086` L=0 direct=0.05→tool=0.95 rank=0.76 **TN_lost_to_FP** used_tool=False
  > The query image contains a prominent vertical crack/seam, whereas all reference images show a consistent, unbroken speckled surface. This is a clear structural anomaly.
- `D4_0126` L=1 direct=0.95→tool=0.10 rank=0.63 **TP_lost_to_FN** used_tool=True
  > The low mean difference (11.0) and the tool's interpretation indicating potential lighting/color variation suggest the query image is normal. The disconfirm clause supports not treating this as an anomaly.
- `D4_0106` L=1 direct=0.95→tool=0.10 rank=0.49 **TP_lost_to_FN** used_tool=True
  > The alignment tool was unreliable, but direct visual inspection shows the query image's texture and shadow pattern are consistent with the normal reference images, indicating no anomaly.
- `D4_0075` L=0 direct=0.02→tool=0.85 rank=0.01 **TN_lost_to_FP** used_tool=True
  > The query image is a uniform gray texture, fundamentally different from the granular, textured reference images. The high alignment difference is likely due to this texture/color mismatch, indicating the query is anomalo
- `D4_0155` L=1 direct=0.95→tool=0.15 rank=0.50 **TP_lost_to_FN** used_tool=True
  > Although the alignment shows a difference, the tool's interpretation explicitly states this may be due to lighting/color variation and suggests the image is likely normal. The visual texture and defect types (pits, spots
- `D4_0128` L=1 direct=0.95→tool=0.30 rank=0.42 **TP_lost_to_FN** used_tool=False
  > The query image shows a texture similar to the reference images with small dark spots. The larger dark patches appear to be within the natural variation of the concrete surface seen in the references, particularly simila
- `D4_0042` L=0 direct=0.02→tool=0.20 rank=0.14 **other** used_tool=True
  > Despite the mean difference of 37.7, the disconfirm clause indicates this could be lighting/color variation. The query appears to be a uniform gray texture while references are textured surfaces - this is a normal variat
  ... and 2 more losses.

### D5  (wins 3, losses 17)

Win sample-types: {'FN_corrected': 3}
Loss sample-types: {'TN_lost_to_FP': 6, 'TP_lost_to_FN': 5, 'other': 6}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5_0179` L=1 direct=0.05→tool=0.90 rank=0.27 **FN_corrected** used_tool=True
  > The tool was unreliable, but direct visual inspection reveals the query lesion has a prominent dark/black central area and irregular pigmentation not seen in the uniform, lighter brown reference lesions, indicating a lik
- `D5_0104` L=1 direct=0.05→tool=0.85 rank=0.42 **FN_corrected** used_tool=True
  > The query image displays a lesion with a distinct blue-gray coloration, which is significantly different from the brown pigmentation seen in all four normal reference images. Although the alignment tool suggested the dif
- `D5_0119` L=1 direct=0.05→tool=0.70 rank=0.32 **FN_corrected** used_tool=True
  > The rotation alignment tool was unreliable, so I relied on direct visual inspection. The query lesion exhibits irregular borders and color variegation, which are atypical compared to the more uniform and symmetric refere

**LOSSES**:

- `D5_0032` L=0 direct=0.05→tool=0.95 rank=0.87 **TN_lost_to_FP** used_tool=False
  > The query lesion is pink and lacks the brown pigmentation seen in all normal reference images, indicating a significant deviation from the normal class.
- `D5_0089` L=0 direct=0.05→tool=0.95 rank=0.42 **TN_lost_to_FP** used_tool=True
  > The tool was unreliable, but direct visual inspection reveals the query lesion is significantly darker and has a different structure (central black area) compared to the lighter, more uniform reference lesions, indicatin
- `D5_0030` L=0 direct=0.05→tool=0.95 rank=0.21 **TN_lost_to_FP** used_tool=False
  > The query image displays a diffuse, reddish-purple lesion that is visually distinct from the well-defined, brownish pigmented nevi shown in the reference images, indicating a high likelihood of anomaly.
- `D5_0063` L=0 direct=0.05→tool=0.90 rank=0.23 **TN_lost_to_FP** used_tool=True
  > The query image displays a small, dark, irregular lesion that is morphologically distinct from the larger, lighter, and more uniform nevi in the reference images. The high alignment difference confirms this structural di
- `D5_0117` L=1 direct=0.95→tool=0.10 rank=0.72 **TP_lost_to_FN** used_tool=False
  > The query image displays a pigmented lesion with features (color, border, symmetry) that are consistent with the normal reference images provided. There are no distinct visual anomalies suggesting pathology.
- `D5_0115` L=1 direct=0.95→tool=0.10 rank=0.57 **TP_lost_to_FN** used_tool=False
  > The query image exhibits characteristics typical of a benign nevus (symmetry, uniform color, smooth borders) similar to the provided normal references. No obvious signs of asymmetry, irregular borders, or color variegati
- `D5_0177` L=1 direct=0.95→tool=0.10 rank=0.27 **TP_lost_to_FN** used_tool=True
  > The alignment tool was unreliable for these non-rigid images. Direct visual inspection shows the query lesion is morphologically consistent with the normal nevi in the reference set, lacking definitive signs of anomaly.
- `D5_0067` L=0 direct=0.05→tool=0.85 rank=0.37 **TN_lost_to_FP** used_tool=True
  > The query image displays a lesion with a significantly different shape and color distribution compared to the normal reference images. The high mean difference scores from the alignment tool confirm that the query is not
  ... and 9 more losses.

### D5b  (wins 5, losses 6)

Win sample-types: {'FP_corrected': 5}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 1, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5b_0031` L=0 direct=0.98→tool=0.10 rank=0.51 **FP_corrected** used_tool=True
  > The high mean difference after alignment is likely due to intensity/contrast variations rather than structural anomalies, as suggested by the tool's disconfirm clause. The anatomical structures appear consistent with the
- `D5b_0067` L=0 direct=0.98→tool=0.10 rank=0.53 **FP_corrected** used_tool=True
  > The tool's interpretation explicitly suggests the query is likely normal despite the alignment difference, attributing it to lighting/color variation. No specific suspicious regions were identified that would override th
- `D5b_0058` L=0 direct=0.95→tool=0.10 rank=0.52 **FP_corrected** used_tool=False
  > The query image shows a brain MRI slice that is structurally similar to the reference images. There are no obvious anomalies such as lesions, tumors, or significant structural deformities. The slight differences in textu
- `D5b_0015` L=0 direct=0.98→tool=0.15 rank=0.56 **FP_corrected** used_tool=True
  > Despite the numerical difference, the tool's interpretation strongly suggests the variation is likely due to imaging parameters (lighting/color) rather than a structural anomaly. The anatomical structures appear consiste
- `D5b_0045` L=0 direct=0.98→tool=0.20 rank=0.31 **FP_corrected** used_tool=True
  > The alignment tool showed differences but explicitly noted they could be lighting/color variations and suggested the query is likely normal. Without additional tools to verify specific regions, the evidence points to a n

**LOSSES**:

- `D5b_0068` L=0 direct=0.05→tool=0.95 rank=0.86 **TN_lost_to_FP** used_tool=True
  > The query image is extremely low-resolution and blurred compared to the sharp reference images, indicating a significant deviation in image quality or modality that constitutes an anomaly, despite the structural similari
- `D5b_0020` L=0 direct=0.02→tool=0.85 rank=0.33 **TN_lost_to_FP** used_tool=True
  > Despite trying to align with the most similar reference image, a significant mean difference (10.2) and widespread residual changes in the diff mask remain. This suggests a structural anomaly rather than just a rotation 
- `D5b_0156` L=1 direct=0.98→tool=0.15 rank=0.56 **TP_lost_to_FN** used_tool=True
  > The tool's interpretation explicitly states that the residual difference may be due to lighting/color variation and suggests the image is likely normal. The visual structures in the query image match the reference images
- `D5b_0007` L=0 direct=0.02→tool=0.20 rank=0.53 **other** used_tool=True
  > The tool's disconfirm clause indicates the residual difference may be lighting/color variation rather than structural anomaly. Visual inspection shows the query image has normal brain anatomy consistent with reference im
- `D5b_0072` L=0 direct=0.05→tool=0.20 rank=0.71 **other** used_tool=True
  > The tool's interpretation indicates the residual difference may be due to lighting/color variation, and explicitly suggests the query is likely normal despite the signal. No further tools are available to confirm anomali
- `D5b_0028` L=0 direct=0.02→tool=0.15 rank=0.37 **other** used_tool=True
  > Both tool comparisons showed high mean differences but explicitly warned these could be lighting/color variations, not structural anomalies. The widespread nature of differences in diff masks supports this interpretation

### D5c  (wins 6, losses 8)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 5, 'TP_lost_to_FN': 2, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5c_0131` L=1 direct=0.02→tool=1.00 rank=0.90 **FN_corrected** used_tool=False
  > The query image contains a fundamentally different object shape and size compared to the consistent morphology seen in all reference images.
- `D5c_0174` L=1 direct=0.05→tool=1.00 rank=0.97 **FN_corrected** used_tool=False
  > The query image contains a tiny, fragmented object that is drastically different in size and morphology compared to the large, consistent J-shaped structures in all reference images, indicating a severe anomaly.
- `D5c_0165` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=True
  > The query image displays a large, complex structure with a distinct hole, which is structurally inconsistent with the small, solid, simple shapes in the reference images. The high alignment difference and residual mask c
- `D5c_0100` L=1 direct=0.05→tool=0.95 rank=0.79 **FN_corrected** used_tool=True
  > The query image exhibits a fundamentally different 'J' or hook shape compared to the rounded, blob-like shapes in all reference images. The high mean difference from the alignment tool confirms this structural discrepanc
- `D5c_0070` L=0 direct=0.95→tool=0.10 rank=0.91 **FP_corrected** used_tool=False
  > The query image displays a small, noisy blob that is morphologically consistent with the smaller blobs seen in reference images 1 and 4. While reference image 3 shows a larger, more complex shape, the query does not exhi
- `D5c_0035` L=0 direct=0.95→tool=0.15 rank=0.81 **FP_corrected** used_tool=True
  > The query image shows a small oval shape similar to references 0, 2, and 3. The rotation tool confirmed alignment with reference 0, and the interpretation suggests the small residual difference is likely due to non-anoma

**LOSSES**:

- `D5c_0004` L=0 direct=0.02→tool=0.98 rank=0.94 **TN_lost_to_FP** used_tool=False
  > The query image contains a tiny, barely visible object, whereas the reference images all feature large, clearly defined shapes. This significant deviation in object size and visibility indicates an anomaly.
- `D5c_0042` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=False
  > The query image contains a significantly larger object with internal voids (holes), which is structurally different from the solid, smaller objects seen in all reference images.
- `D5c_0015` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=False
  > The query image exhibits a fundamentally different morphology (elongated hook shape) compared to the compact, irregular shapes seen in all normal reference images, indicating a clear anomaly.
- `D5c_0061` L=0 direct=0.02→tool=0.95 rank=0.84 **TN_lost_to_FP** used_tool=False
  > The query image exhibits a significantly different morphology (multi-lobed with a large internal void) compared to the simpler, solid shapes in the reference images, indicating a clear anomaly.
- `D5c_0054` L=0 direct=0.02→tool=0.90 rank=0.93 **TN_lost_to_FP** used_tool=True
  > The query image has a distinct shape with a protrusion that does not match reference 0 even after optimal rotation, indicating a structural anomaly rather than just lighting variation.
- `D5c_0170` L=1 direct=0.95→tool=0.10 rank=0.97 **TP_lost_to_FN** used_tool=False
  > The query image displays a small, textured object similar in nature to the objects in the reference images, just smaller and without the fragmentation or holes seen in some references. This variation in size and integrit
- `D5c_0102` L=1 direct=0.95→tool=0.20 rank=0.91 **TP_lost_to_FN** used_tool=False
  > The query image appears similar to the reference images in terms of texture and general appearance. The variations in shape and size among the reference images suggest that the object is non-rigid, making rotation alignm
- `D5c_0055` L=0 direct=0.02→tool=0.15 rank=0.86 **other** used_tool=True
  > The query image is visually similar to normal references (Ref 0, Ref 3). The alignment tool showed a small residual difference, but the interpretation explicitly states this could be non-anomalous variation, suggesting t

### D5d  (wins 5, losses 5)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2, 'other': 2}
Loss sample-types: {'TP_lost_to_FN': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5d_0173` L=1 direct=0.02→tool=0.95 rank=0.57 **FN_corrected** used_tool=True
  > The query image contains a prominent dark foreign body in the lumen, which is not present in any of the normal reference images. The tool's failure to align confirms a significant structural difference, supporting the vi
- `D5d_0135` L=1 direct=0.02→tool=0.95 rank=0.48 **FN_corrected** used_tool=True
  > Direct visual inspection reveals a prominent dark, oval-shaped object in the center of the query image, which is absent in all normal reference images. The tool's unreliable alignment confirms the structural difference, 
- `D5d_0045` L=0 direct=0.92→tool=0.10 rank=0.40 **FP_corrected** used_tool=True
  > The alignment tool was unreliable due to significant content differences between the query and reference. Direct visual inspection of the query image reveals normal mucosal tissue with no obvious pathological features, l
- `D5d_0023` L=0 direct=0.98→tool=0.85 rank=0.39 **other** used_tool=True
  > Direct visual inspection reveals a yellow discoloration in the query image that is absent in the normal reference images, indicating a potential anomaly despite the unreliable tool output.
- `D5d_0128` L=1 direct=0.02→tool=0.15 rank=0.35 **other** used_tool=True
  > Direct visual inspection shows the query image displays normal colonic mucosa with typical vascular patterns and some residue, consistent with the normal reference images. No obvious pathological features are present.

**LOSSES**:

- `D5d_0129` L=1 direct=0.98→tool=0.10 rank=0.31 **TP_lost_to_FN** used_tool=False
  > The query image displays normal colonic mucosa with a small amount of bile staining, which is a common and non-pathological finding. There are no visible signs of disease such as polyps, ulcers, or inflammation that woul
- `D5d_0146` L=1 direct=0.98→tool=0.10 rank=0.38 **TP_lost_to_FN** used_tool=False
  > The query image displays normal mucosal tissue with a smooth texture and healthy pink coloration, consistent with a normal endoscopic view (likely the pylorus). The absence of text overlays or chromoendoscopy dye seen in
- `D5d_0161` L=1 direct=0.98→tool=0.10 rank=0.51 **TP_lost_to_FN** used_tool=True
  > Direct visual inspection reveals the query image shows normal mucosal tissue with a small amount of yellow fluid, consistent with normal endoscopic findings. The unreliable tool output is disregarded.
- `D5d_0166` L=1 direct=0.98→tool=0.10 rank=0.47 **TP_lost_to_FN** used_tool=True
  > The tool's interpretation explicitly states that the high difference score may be due to lighting/color variation and that the query is likely NORMAL. The visual content of the query image (smooth mucosa, instrument tip)
- `D5d_0169` L=1 direct=0.95→tool=0.10 rank=0.40 **TP_lost_to_FN** used_tool=True
  > The tool output was unreliable due to misalignment. Direct visual inspection confirms the query image displays normal colonic mucosa consistent with the reference images, showing no signs of pathology.

### D6  (wins 6, losses 13)

Win sample-types: {'FP_corrected': 6}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 10, 'other': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D6_0063` L=0 direct=0.98→tool=0.10 rank=0.60 **FP_corrected** used_tool=True
  > The high mean difference is likely due to color/lighting variation as warned by the tool's disconfirm clause. Structural content appears identical between query and reference images.
- `D6_0015` L=0 direct=0.98→tool=0.10 rank=0.62 **FP_corrected** used_tool=True
  > The tool's interpretation explicitly states that the residual difference may be due to lighting/color variation and that the query is likely normal. The noisy diff mask does not show a clear structural anomaly, supportin
- `D6_0000` L=0 direct=0.95→tool=0.10 rank=0.82 **FP_corrected** used_tool=True
  > The tool's interpretation explicitly states that the observed difference is likely due to lighting/color variation and that the query is likely normal, satisfying the disconfirm clause for anomaly.
- `D6_0039` L=0 direct=0.95→tool=0.10 rank=0.85 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing the same field patterns, road, and small features without any obvious deviations or anomalies.
- `D6_0017` L=0 direct=0.95→tool=0.10 rank=0.75 **FP_corrected** used_tool=True
  > Direct visual inspection shows no clear anomalies; the differences between the query and reference images are likely due to normal variations such as seasonal changes or minor updates, not structural or content anomalies
- `D6_0064` L=0 direct=0.95→tool=0.10 rank=0.39 **FP_corrected** used_tool=True
  > The tool indicated a high mean difference but the interpretation's disconfirm clause suggests this is likely due to lighting or color variation, not a structural anomaly. The visual layout of the neighborhood is consiste

**LOSSES**:

- `D6_0024` L=0 direct=0.02→tool=0.95 rank=0.71 **TN_lost_to_FP** used_tool=False
  > The query image contains a large, distinct area of light-colored ground that is completely absent in the normal reference images, which show a uniform dark field. This is a clear visual anomaly.
- `D6_0104` L=1 direct=0.98→tool=0.05 rank=0.69 **TP_lost_to_FN** used_tool=True
  > The rotation alignment confirmed the query and reference images are of the same location with identical structures. The significant pixel difference is solely due to the field color (brown vs. green), which the tool's in
- `D6_0145` L=1 direct=0.95→tool=0.05 rank=0.65 **TP_lost_to_FN** used_tool=True
  > The high mean difference is explained by seasonal color changes (vegetation, water) rather than structural anomalies. The underlying geometry of roads and buildings matches the reference perfectly, satisfying the tool's 
- `D6_0110` L=1 direct=0.98→tool=0.10 rank=0.36 **TP_lost_to_FN** used_tool=True
  > The alignment tool was unreliable, and direct visual inspection shows the query image is a similar aerial view of a residential area with consistent road patterns and vegetation as the references, indicating no significa
- `D6_0133` L=1 direct=0.98→tool=0.10 rank=0.82 **TP_lost_to_FN** used_tool=True
  > The structural layout aligns perfectly with the reference image. The observed differences in color and texture are consistent with seasonal vegetation changes, which the tool's interpretation flags as a potential disconf
- `D6_0111` L=1 direct=0.98→tool=0.10 rank=0.66 **TP_lost_to_FN** used_tool=True
  > The high difference score is attributed to seasonal lighting/color changes as per the tool's disconfirm clause, not structural anomalies. The underlying geometry appears consistent.
- `D6_0130` L=1 direct=0.98→tool=0.10 rank=0.54 **TP_lost_to_FN** used_tool=True
  > The alignment tool indicated that the observed differences are likely due to lighting or color variations rather than structural anomalies, as per its disconfirm clause. The scattered nature of the difference mask suppor
- `D6_0136` L=1 direct=0.98→tool=0.10 rank=0.70 **TP_lost_to_FN** used_tool=True
  > The alignment tool was unreliable, and the disconfirm clause indicates the high difference does not imply anomaly. Visual inspection shows the query image contains expected features (road, vegetation) consistent with the
  ... and 5 more losses.

### D7  (wins 2, losses 1)

Win sample-types: {'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D7_0159` L=1 direct=0.02→tool=1.00 rank=0.87 **FN_corrected** used_tool=False
  > The query image depicts a rural scene with a small car towing a trailer, whereas all reference images show urban or suburban street views from a vehicle's dashboard. The content, setting, and objects are fundamentally di
- `D7_0135` L=1 direct=0.02→tool=1.00 rank=0.97 **FN_corrected** used_tool=False
  > The query image depicts a tourist scene with a horse carriage and statue, whereas all reference images are dashcam views of driving on roads. This is a clear content anomaly.

**LOSSES**:

- `D7_0086` L=0 direct=0.02→tool=0.95 rank=0.67 **TN_lost_to_FP** used_tool=True
  > The query image depicts a night-time highway scene, whereas all reference images show daytime urban or suburban streets. This significant difference in lighting conditions and environment makes the query image anomalous 

### D8  (wins 5, losses 7)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 1, 'other': 3}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 3, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D8_0114` L=1 direct=0.02→tool=0.95 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a uniformed officer in the foreground, which is a distinct content difference from the reference images showing civilians. The tool's high mean difference supports this, and the visual evidence o
- `D8_0072` L=0 direct=0.95→tool=0.10 rank=0.50 **FP_corrected** used_tool=True
  > The difference detected is due to a person walking in the scene, which is normal activity. The tool's interpretation confirms that such residuals are likely lighting or transient object variations, not structural anomali
- `D8_0102` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The tool's interpretation explicitly suggests the query is likely normal, attributing differences to lighting/color. The visual difference (a uniformed person) is a plausible variation in this setting, not a structural a
- `D8_0165` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The tool's interpretation explicitly states the query is likely NORMAL despite the mean difference, attributing it to lighting/color variation. The scene structure is consistent with references, and the differences appea
- `D8_0177` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The tool's interpretation explicitly states that the residual difference may be due to lighting/color variation and that the query is likely NORMAL. The disconfirm clause confirms that post-alignment residuals don't nece

**LOSSES**:

- `D8_0005` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed individual walking in the foreground, which is a significant content difference compared to the reference images. The tool confirmed a high difference score, and the disconfirm clause
- `D8_0065` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a person in a uniform walking in the foreground, which is a distinct content difference from the reference images showing only civilians. The tool's high mean difference supports this observation
- `D8_0050` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a person in a uniform (likely security or police) walking in the foreground, whereas the reference images show only civilians. This is a significant content anomaly not explained by lighting or a
- `D8_0133` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The low mean difference and the tool's disconfirm clause indicating likely normality due to lighting variations, combined with visual inspection showing no structural anomalies, suggest the query image is normal.
- `D8_0126` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The difference detected is solely due to the presence of different people in the scene, which is expected behavior in a public area. The background remains consistent, and the tool's disconfirm clause suggests that such 
- `D8_0138` L=1 direct=0.95→tool=0.15 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The tool's interpretation explicitly suggests the query is likely normal despite the difference signal, attributing it to potential lighting/color variation or transient elements. The white stains on the ground are likel
- `D8_0119` L=1 direct=0.95→tool=0.80 rank=0.50 **other** used_tool=True
  > The query image contains a person in a white hoodie performing an unusual action (jumping/dancing) on the left side, which is not present in any of the reference images. The reference images show people walking or standi

### D9  (wins 5, losses 10)

Win sample-types: {'FP_corrected': 3, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 7}

**WINS** (item · direct→tool · rank · type · rationale):

- `D9_0121` L=1 direct=0.01→tool=1.00 rank=0.58 **FN_corrected** used_tool=False
  > The query image differs significantly from the reference images in both the label (cherry vs. banana) and the liquid color (red vs. light), which are definitive signs of an anomaly.
- `D9_0168` L=1 direct=0.01→tool=1.00 rank=0.73 **FN_corrected** used_tool=False
  > The query image differs significantly from the reference images in both the liquid color (red vs. light) and the label icon (cherry vs. banana), confirming it is anomalous.
- `D9_0022` L=0 direct=0.99→tool=0.10 rank=0.28 **FP_corrected** used_tool=True
  > The tool was unreliable, but direct visual inspection shows the query image is consistent with the normal reference images in terms of components, layout, and background. No anomaly is detected.
- `D9_0078` L=0 direct=0.99→tool=0.10 rank=0.11 **FP_corrected** used_tool=True
  > The alignment tool was unreliable. Direct visual inspection shows the query image is identical in structure to two of the four normal reference images (single yellow wire setup), indicating it is a normal sample.
- `D9_0079` L=0 direct=0.98→tool=0.10 rank=0.16 **FP_corrected** used_tool=False
  > The query image contains the same set of hardware components (2 bolts, 2 nuts, 2 washers) as the reference images, just arranged differently within the bag. The variation in position is expected for loose items and does 

**LOSSES**:

- `D9_0047` L=0 direct=0.02→tool=1.00 rank=0.13 **TN_lost_to_FP** used_tool=False
  > The query image contains a cherry label and red liquid, whereas all normal reference images contain banana labels and light-colored liquid. This is a definitive mismatch in product type.
- `D9_0041` L=0 direct=0.02→tool=1.00 rank=0.79 **TN_lost_to_FP** used_tool=False
  > The query image displays a red liquid with a cherry label, whereas all reference images show a light-colored liquid with banana or orange labels. This significant difference in content confirms the query is anomalous.
- `D9_0032` L=0 direct=0.02→tool=1.00 rank=0.07 **TN_lost_to_FP** used_tool=False
  > The query image is anomalous because the liquid color (red vs. white) and the label icon (cherry vs. banana) differ significantly from all normal reference images.
- `D9_0100` L=1 direct=0.99→tool=0.05 rank=0.41 **TP_lost_to_FN** used_tool=True
  > The alignment tool was unreliable. Direct visual inspection confirms the query image (single yellow wire) matches the configuration of normal reference images 1 and 3, indicating it is a normal sample.
- `D9_0176` L=1 direct=0.99→tool=0.05 rank=0.31 **TP_lost_to_FN** used_tool=True
  > Direct visual inspection confirms the query image (single yellow wire) matches the normal reference images (Ref 1 and Ref 3). The tool's unreliable output is disregarded.
- `D9_0128` L=1 direct=0.99→tool=0.10 rank=0.24 **TP_lost_to_FN** used_tool=False
  > The query image displays a standard single jumper wire setup that matches the pattern seen in the normal reference images. There are no visible defects, misalignments, or unexpected components.
- `D9_0157` L=1 direct=0.99→tool=0.10 rank=0.48 **TP_lost_to_FN** used_tool=True
  > The tool was unreliable. Direct visual inspection shows the query image matches the normal reference (image 2) with a yellow cable and two connectors, showing no visible anomalies.
- `D9_0129` L=1 direct=0.98→tool=0.10 rank=0.04 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing the same types of food items in a similar arrangement. No anomalies are detected.
  ... and 2 more losses.

---

## tool_segment_and_count  (56 wins, 106 losses, net flips -34 on n=480)

### D1  (wins 6, losses 3)

Win sample-types: {'FP_corrected': 4, 'other': 2}
Loss sample-types: {'TP_lost_to_FN': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D1_0084` L=0 direct=0.95→tool=0.05 rank=0.02 **FP_corrected** used_tool=False
  > The query image exhibits the same speckled texture and pattern distribution as the normal reference images. No structural anomalies or deviations are visible.
- `D1_0038` L=0 direct=0.98→tool=0.10 rank=0.26 **FP_corrected** used_tool=True
  > The tool confirms no structural anomalies, and the apparent difference in the 'actavis' logo is likely due to lighting or image quality, not a defect.
- `D1_0064` L=0 direct=0.98→tool=0.10 rank=0.24 **FP_corrected** used_tool=True
  > The segmentation tool found no coarse structural differences. The visual difference (presence of 'actavis' logo) appears to be a normal variation in printing or orientation rather than a defect, as the overall capsule st
- `D1_0088` L=0 direct=0.95→tool=0.10 rank=0.29 **FP_corrected** used_tool=True
  > The structural differences detected by the tool are likely due to lighting or exposure variations, as indicated by the disconfirm clause. Visual inspection confirms the component and PCB structure are consistent with the
- `D1_0016` L=0 direct=0.98→tool=0.85 rank=0.06 **other** used_tool=True
  > The query image shows a clear anomaly where the top conductor's strands are bright and shiny, contrasting with the dark, oxidized strands seen in all reference images. While the tool flagged a high change ratio, the spec
- `D1_0174` L=1 direct=0.02→tool=0.15 rank=0.15 **other** used_tool=True
  > The structural differences detected are likely due to lighting/exposure variations rather than actual defects. The component placement, pin configuration, and PCB pattern match the reference images, indicating this is a 

**LOSSES**:

- `D1_0094` L=1 direct=0.98→tool=0.05 rank=0.77 **TP_lost_to_FN** used_tool=False
  > The query image matches the reference images in shape, color, and text markings. No anomalies are detected.
- `D1_0111` L=1 direct=0.98→tool=0.05 rank=0.77 **TP_lost_to_FN** used_tool=True
  > The segmentation tool found no structural anomalies (0/64 cells changed). The weave pattern in the query image matches the reference images, with only minor pixel-level variations that are within normal range for this ty
- `D1_0179` L=1 direct=0.95→tool=0.05 rank=0.54 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing the same component type without any apparent anomalies.

### D10  (wins 3, losses 7)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 1}
Loss sample-types: {'TP_lost_to_FN': 4, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D10_0076` L=0 direct=0.98→tool=0.00 rank=0.12 **FP_corrected** used_tool=False
  > The query image matches the normal reference images in component layout, labeling, and overall appearance. No anomalies are detected.
- `D10_0156` L=1 direct=0.01→tool=0.95 rank=0.51 **FN_corrected** used_tool=True
  > The query image definitively lacks the protective mesh grilles present on the transducers in all reference images. This is a clear physical anomaly (missing component) rather than a lighting variation, as the underlying 
- `D10_0002` L=0 direct=0.95→tool=0.05 rank=0.07 **FP_corrected** used_tool=False
  > The query image matches the normal reference images in structure, content, and arrangement. No anomalies are detected.

**LOSSES**:

- `D10_0140` L=1 direct=0.98→tool=0.05 rank=0.30 **TP_lost_to_FN** used_tool=True
  > The minor structural differences detected by the tool are attributed to lighting or exposure variations as per the disconfirm clause, and visual inspection confirms the component appears normal.
- `D10_0097` L=1 direct=0.99→tool=0.10 rank=0.34 **TP_lost_to_FN** used_tool=True
  > Although the segmentation tool detected significant pixel differences, the interpretation clause indicates this is likely due to lighting/exposure changes. Visual inspection confirms the board structure and components ar
- `D10_0136` L=1 direct=0.98→tool=0.10 rank=0.23 **TP_lost_to_FN** used_tool=True
  > Despite the tool's high change ratio, the disconfirm clause indicates this is likely due to lighting/exposure differences. Visual inspection confirms the PCB structure and components are normal and match the reference im
- `D10_0139` L=1 direct=0.98→tool=0.10 rank=0.20 **TP_lost_to_FN** used_tool=True
  > Although the tool reported a high change ratio, the interpretation notes this can be caused by lighting or exposure shifts. Visual inspection confirms the objects and background are consistent with the reference images, 
- `D10_0071` L=0 direct=0.01→tool=0.15 rank=0.08 **other** used_tool=True
  > The structural differences detected are likely due to minor lighting variations rather than actual defects, as the pasta pieces appear visually consistent with the reference images.
- `D10_0153` L=1 direct=0.98→tool=0.85 rank=0.62 **other** used_tool=True
  > The query image shows a clear physical defect (a protrusion on a spoke) that is absent in all reference images. The tool's detection of structural change supports this, and the defect is not explainable by the disconfirm
- `D10_0016` L=0 direct=0.02→tool=0.15 rank=0.20 **other** used_tool=True
  > Despite the tool detecting some cell changes, the visual similarity between query and reference images suggests these differences are likely due to minor lighting variations rather than actual defects. The object's shape

### D2  (wins 5, losses 12)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 3}
Loss sample-types: {'TN_lost_to_FP': 5, 'TP_lost_to_FN': 7}

**WINS** (item · direct→tool · rank · type · rationale):

- `D2_0092` L=1 direct=0.01→tool=0.95 rank=0.63 **FN_corrected** used_tool=True
  > Despite the tool's negative result, the query image clearly shows a plastic straw wrapper attached to the carton, which is not present in any of the normal reference images. This is a clear structural anomaly.
- `D2_0095` L=1 direct=0.02→tool=0.95 rank=0.86 **FN_corrected** used_tool=True
  > The query image shows a bottle filled with dark liquid, whereas the reference images show the same bottle type with a white label and clear contents. This is a clear content anomaly, not a lighting artifact, confirming t
- `D2_0145` L=1 direct=0.02→tool=0.95 rank=0.71 **FN_corrected** used_tool=True
  > The query image displays different text content on the packaging compared to the reference images (e.g., 'Since 1973' vs 'Made by Hongta...'), confirming a genuine anomaly rather than a lighting artifact.
- `D2_0037` L=0 direct=0.98→tool=0.10 rank=0.19 **FP_corrected** used_tool=True
  > The query image shows a normal view of the product's back, consistent with reference images. The detected differences are likely due to lighting and angle variations, not actual defects.
- `D2_0068` L=0 direct=0.95→tool=0.10 rank=0.30 **FP_corrected** used_tool=True
  > The minimal structural difference detected (1/64 cells) is within normal variation and likely due to lighting/angle differences rather than an actual defect. The query image appears visually consistent with the reference

**LOSSES**:

- `D2_0056` L=0 direct=0.01→tool=1.00 rank=0.05 **TN_lost_to_FP** used_tool=False
  > The query image displays a fundamentally different product packaging design compared to the normal reference images, indicating a certain anomaly.
- `D2_0087` L=0 direct=0.01→tool=1.00 rank=0.08 **TN_lost_to_FP** used_tool=True
  > The query image is clearly upside down relative to the normal reference images, with inverted text and logo. This is a definitive anomaly, regardless of the tool's low change ratio which may be due to the coarse grid res
- `D2_0080` L=0 direct=0.02→tool=1.00 rank=0.02 **TN_lost_to_FP** used_tool=True
  > The query image shows the back of the package (nutrition facts, barcode) while all reference images show the front (branding, product view). This is a fundamental structural difference confirming the image is anomalous.
- `D2_0167` L=1 direct=0.98→tool=0.00 rank=0.18 **TP_lost_to_FN** used_tool=True
  > The tool detected no structural changes (0/64 cells), and the visual appearance of the query image matches the reference images perfectly. Therefore, the image is classified as normal.
- `D2_0029` L=0 direct=0.01→tool=0.95 rank=0.51 **TN_lost_to_FP** used_tool=False
  > The query image displays the back label of the bottle, whereas all reference images display the front label. This significant difference in the visible content (label side) indicates an anomaly.
- `D2_0063` L=0 direct=0.01→tool=0.95 rank=0.01 **TN_lost_to_FP** used_tool=True
  > The query image displays the back of the product packaging, whereas all reference images display the front or side. This represents a fundamental difference in the object's orientation/content relative to the 'normal' se
- `D2_0170` L=1 direct=0.98→tool=0.05 rank=0.13 **TP_lost_to_FN** used_tool=True
  > Despite the tool's high change ratio, the disconfirm clause indicates this is likely due to lighting/exposure. Visual inspection confirms the query image is a normal front view of the package, matching the other referenc
- `D2_0097` L=1 direct=0.98→tool=0.05 rank=0.73 **TP_lost_to_FN** used_tool=False
  > The query image displays a standard, undamaged product carton with no visible anomalies compared to the reference images.
  ... and 4 more losses.

### D4  (wins 1, losses 8)

Win sample-types: {'FN_corrected': 1}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 6}

**WINS** (item · direct→tool · rank · type · rationale):

- `D4_0176` L=1 direct=0.05→tool=0.95 rank=0.82 **FN_corrected** used_tool=True
  > The query image displays a coarse, rocky surface with large debris, which is structurally distinct from the fine-grained texture of the reference images. The high change ratio from the tool confirms this significant stru

**LOSSES**:

- `D4_0086` L=0 direct=0.05→tool=0.95 rank=0.76 **TN_lost_to_FP** used_tool=True
  > Despite the tool's low change ratio and warning about intensity shifts, the query image contains a clear vertical linear defect (crack) that is structurally different from the uniform texture of the normal reference imag
- `D4_0126` L=1 direct=0.95→tool=0.10 rank=0.63 **TP_lost_to_FN** used_tool=True
  > The structural change signal is minimal (1/64 cells) and the tool's interpretation notes this could be due to lighting/exposure rather than a defect. Visual inspection confirms the query matches the reference texture.
- `D4_0106` L=1 direct=0.95→tool=0.10 rank=0.49 **TP_lost_to_FN** used_tool=True
  > The high structural difference reported by the tool is attributed to the significant lighting/shadow variation visible in the query image, as noted in the tool's disconfirm clause. The underlying texture appears consiste
- `D4_0133` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > Although the segmentation tool detected significant differences, the interpretation notes this is likely due to global intensity shifts (lighting/shadow) rather than a structural defect. The texture itself appears consis
- `D4_0006` L=0 direct=0.05→tool=0.85 rank=0.10 **TN_lost_to_FP** used_tool=True
  > While the tool flags a high change ratio, the visual presence of distinct elongated dark marks in the query image, absent in the uniform speckled references, confirms an anomaly despite the potential for lighting variati
- `D4_0152` L=1 direct=0.95→tool=0.15 rank=0.75 **TP_lost_to_FN** used_tool=True
  > The segmentation tool reported a minimal change ratio (0.016), and the interpretation suggests this could be due to lighting or intensity shifts rather than a defect. Therefore, the image is classified as normal with a l
- `D4_0155` L=1 direct=0.95→tool=0.15 rank=0.50 **TP_lost_to_FN** used_tool=True
  > Despite the high change ratio from the tool, the visual features in the query image (pits, texture) are consistent with the normal reference images. The tool's signal is likely due to lighting/contrast variations, not a 
- `D4_0128` L=1 direct=0.95→tool=0.20 rank=0.42 **TP_lost_to_FN** used_tool=True
  > The coarse grid differences detected are likely due to normal texture variation or lighting differences rather than actual defects, as indicated by the disconfirm clause. The query image appears consistent with normal co

### D5  (wins 1, losses 13)

Win sample-types: {'FN_corrected': 1}
Loss sample-types: {'TN_lost_to_FP': 5, 'TP_lost_to_FN': 7, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5_0119` L=1 direct=0.05→tool=0.85 rank=0.32 **FN_corrected** used_tool=True
  > The high change ratio from the tool, combined with visual evidence of irregular borders, asymmetry, and color variegation in the query image compared to the uniform reference lesions, strongly suggests an anomaly. The di

**LOSSES**:

- `D5_0032` L=0 direct=0.05→tool=0.95 rank=0.87 **TN_lost_to_FP** used_tool=True
  > The query image displays a pinkish, homogeneous lesion, whereas all reference images show dark brown, pigmented lesions. The high change ratio from the tool reflects this fundamental difference in color and texture, indi
- `D5_0030` L=0 direct=0.05→tool=0.95 rank=0.21 **TN_lost_to_FP** used_tool=True
  > The query image displays a large, diffuse red area, which is structurally and chromatically distinct from the discrete, well-defined brown lesions in the reference images. The high change ratio from the tool confirms thi
- `D5_0099` L=1 direct=0.95→tool=0.10 rank=0.65 **TP_lost_to_FN** used_tool=False
  > The query image displays a pigmented lesion with regular borders and relatively uniform pigmentation, consistent with the benign characteristics seen in the normal reference images. No obvious anomalies are detected.
- `D5_0115` L=1 direct=0.95→tool=0.10 rank=0.57 **TP_lost_to_FN** used_tool=True
  > Although the tool detected a high change ratio, the interpretation notes this can be caused by lighting differences. Visually, the lesion is symmetric and uniform, consistent with the normal reference images, so the sign
- `D5_0158` L=1 direct=0.95→tool=0.10 rank=0.35 **TP_lost_to_FN** used_tool=True
  > Despite the high structural diff score, the interpretation notes this can be caused by lighting shifts. Visual inspection confirms the lesion has regular borders and uniform color, consistent with a normal benign nevus s
- `D5_0167` L=1 direct=0.95→tool=0.10 rank=0.48 **TP_lost_to_FN** used_tool=True
  > Although the tool detected a high structural difference, the interpretation notes this can be caused by lighting/exposure shifts. Visual inspection confirms the lesion is symmetric and uniform, consistent with the normal
- `D5_0085` L=0 direct=0.05→tool=0.85 rank=0.17 **TN_lost_to_FP** used_tool=True
  > The tool indicates a very high structural difference (93.8% of cells changed). While the disconfirm clause notes this could be due to lighting, the visual appearance of the lesion in the query image (color, pattern) is d
- `D5_0015` L=0 direct=0.05→tool=0.85 rank=0.13 **TN_lost_to_FP** used_tool=True
  > The query image exhibits significant color variegation (dark center, lighter rim) and structural asymmetry compared to the uniform reference lesions. The tool's high change ratio confirms this structural difference, and 
  ... and 5 more losses.

### D5b  (wins 5, losses 9)

Win sample-types: {'FP_corrected': 5}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 3, 'other': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5b_0015` L=0 direct=0.98→tool=0.10 rank=0.56 **FP_corrected** used_tool=False
  > The query image displays normal brain anatomy without visible lesions, masses, or structural deformities that would indicate an anomaly. The variations in the reference images are due to different slice levels and imagin
- `D5b_0031` L=0 direct=0.98→tool=0.10 rank=0.51 **FP_corrected** used_tool=True
  > The structural differences flagged by the tool are likely due to global intensity variations rather than anatomical anomalies, as the brain structures in the query image match the normal references.
- `D5b_0067` L=0 direct=0.98→tool=0.10 rank=0.53 **FP_corrected** used_tool=True
  > The query image displays normal brain anatomy for its slice level. The tool's positive signal is likely due to anatomical differences between slices or intensity variations, as warned by the disconfirm clause, rather tha
- `D5b_0045` L=0 direct=0.98→tool=0.15 rank=0.31 **FP_corrected** used_tool=True
  > The structural differences detected are likely due to different slice levels (ventricles present vs absent) and intensity variations, not actual pathological anomalies. The disconfirm clause applies here.
- `D5b_0058` L=0 direct=0.95→tool=0.15 rank=0.52 **FP_corrected** used_tool=True
  > The structural features of the brain in the query image match the reference images. The detected differences are likely due to intensity/contrast variations rather than actual anomalies, as cautioned by the tool's discon

**LOSSES**:

- `D5b_0068` L=0 direct=0.05→tool=0.95 rank=0.86 **TN_lost_to_FP** used_tool=True
  > The query image is significantly blurrier and lower resolution than the reference images. While the tool flagged a structural difference, the interpretation notes this can be caused by intensity/contrast shifts. However,
- `D5b_0150` L=1 direct=0.95→tool=0.10 rank=0.63 **TP_lost_to_FN** used_tool=True
  > Although the tool detected a 28% difference, the interpretation warns this may be due to intensity shifts rather than structural defects. Visual inspection confirms the query image has normal brain anatomy consistent wit
- `D5b_0156` L=1 direct=0.98→tool=0.15 rank=0.56 **TP_lost_to_FN** used_tool=True
  > The structural differences detected are likely due to imaging variations (intensity/contrast) rather than true anomalies, as the brain morphology appears normal when visually inspected against references.
- `D5b_0160` L=1 direct=0.95→tool=0.15 rank=0.44 **TP_lost_to_FN** used_tool=True
  > The high change ratio is likely due to intensity/contrast differences rather than structural anomaly, as the brain anatomy appears normal and symmetric in the query image.
- `D5b_0050` L=0 direct=0.02→tool=0.15 rank=0.49 **other** used_tool=True
  > The structural differences detected are likely due to different anatomical slice levels (query is more superior) rather than pathological anomalies. The disconfirm clause about intensity shifts and the visual evidence of
- `D5b_0007` L=0 direct=0.02→tool=0.15 rank=0.53 **other** used_tool=True
  > Despite the tool's signal, visual inspection confirms the query image shows normal brain anatomy consistent with the reference images. The detected differences are likely due to intensity variations rather than structura
- `D5b_0028` L=0 direct=0.02→tool=0.15 rank=0.37 **other** used_tool=True
  > The detected differences are likely due to intensity/contrast variations rather than structural anomalies. The brain anatomy appears normal with no visible lesions, masses, or deformities when comparing the query to refe
- `D5b_0069` L=0 direct=0.02→tool=0.15 rank=0.53 **other** used_tool=True
  > The observed differences are likely due to the query image being a different axial slice level (showing ventricles) rather than a pathological anomaly. The tool's disconfirm clause about intensity shifts supports this, a
  ... and 1 more losses.

### D5c  (wins 8, losses 9)

Win sample-types: {'FP_corrected': 3, 'FN_corrected': 4, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 5, 'TP_lost_to_FN': 3, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5c_0131` L=1 direct=0.02→tool=1.00 rank=0.90 **FN_corrected** used_tool=False
  > The query image contains a fundamentally different object shape and size compared to the consistent structure in the reference images, confirming it is anomalous.
- `D5c_0174` L=1 direct=0.05→tool=0.99 rank=0.97 **FN_corrected** used_tool=True
  > The query image shows only a tiny fragment of the object seen in the reference images, indicating a massive structural absence rather than a lighting variation. This confirms the image is anomalous.
- `D5c_0165` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=True
  > The query image displays a significantly larger and more complex structure with a distinct hole, which is fundamentally different from the small, solid shapes in the reference images. This structural discrepancy is not e
- `D5c_0100` L=1 direct=0.05→tool=0.95 rank=0.79 **FN_corrected** used_tool=True
  > The query image exhibits a fundamentally different shape (elongated hook) compared to the compact, blob-like shapes in the reference images. The tool's detection of structural change supports this visual observation, and
- `D5c_0035` L=0 direct=0.95→tool=0.10 rank=0.81 **FP_corrected** used_tool=True
  > The query image is visually consistent with the majority of the normal reference images. The minor structural difference detected by the tool is likely due to noise or slight intensity variations, as cautioned by the too
- `D5c_0070` L=0 direct=0.95→tool=0.10 rank=0.91 **FP_corrected** used_tool=True
  > Although the grid tool detected some cell changes, the interpretation notes this can be caused by non-defect factors like intensity shifts. Visually, the query image matches the morphology and texture of the normal refer
- `D5c_0038` L=0 direct=0.95→tool=0.15 rank=0.89 **FP_corrected** used_tool=True
  > The tool reports a low structural change ratio (0.141) against the primary reference, and the interpretation warns that such signals can be caused by non-defect factors like intensity shifts. Visually, the query shape is
- `D5c_0118` L=1 direct=0.02→tool=0.15 rank=0.96 **other** used_tool=True
  > The query image is visually consistent with most reference images (single object). The tool's detected difference is likely due to minor variations or intensity shifts, as cautioned by the tool's interpretation, rather t

**LOSSES**:

- `D5c_0004` L=0 direct=0.02→tool=0.95 rank=0.94 **TN_lost_to_FP** used_tool=True
  > The query image shows only a tiny speck, whereas all reference images display large, distinct textured shapes. This represents a fundamental structural absence of the object of interest, which is a clear anomaly despite 
- `D5c_0042` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=True
  > Despite the tool's caution about intensity shifts, the query image exhibits clear morphological differences (size, shape, internal voids) compared to the reference images, strongly indicating an anomaly.
- `D5c_0015` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=True
  > Despite the tool's warning about intensity shifts, the visual evidence shows a fundamentally different object shape and size in the query image compared to the reference images, indicating a structural anomaly.
- `D5c_0039` L=0 direct=0.02→tool=0.95 rank=0.90 **TN_lost_to_FP** used_tool=True
  > The query image contains a large object, whereas reference image 3 is almost entirely empty. This represents a fundamental structural anomaly that cannot be explained by simple intensity shifts, confirming the image is a
- `D5c_0061` L=0 direct=0.02→tool=0.95 rank=0.84 **TN_lost_to_FP** used_tool=True
  > The query image exhibits a fundamentally different shape and internal structure (multi-lobed with a void) compared to the simpler, solid shapes in the reference images. The tool's high change ratio confirms this structur
- `D5c_0170` L=1 direct=0.95→tool=0.10 rank=0.97 **TP_lost_to_FN** used_tool=True
  > The structural difference detected is likely due to the query object being a small, isolated instance (like refs 2 and 3) compared against a large, complex reference (ref 0), or a positional shift. The object's texture a
- `D5c_0102` L=1 direct=0.95→tool=0.15 rank=0.91 **TP_lost_to_FN** used_tool=True
  > The structural difference detected is minor (9.4%) and the tool's interpretation warns that such signals can be due to non-defect factors like intensity shifts. The visual appearance is consistent with the reference set,
- `D5c_0107` L=1 direct=0.95→tool=0.15 rank=0.99 **TP_lost_to_FN** used_tool=True
  > The query image's shape and size are consistent with the first three normal reference images. The tool's detected difference is likely due to minor positional or intensity variations, as cautioned by the disconfirm claus
  ... and 1 more losses.

### D5d  (wins 5, losses 10)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 3}
Loss sample-types: {'TP_lost_to_FN': 5, 'other': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5d_0173` L=1 direct=0.02→tool=0.95 rank=0.57 **FN_corrected** used_tool=True
  > The query image displays a prominent, dark, solid object in the lumen, which is a clear structural anomaly compared to the normal mucosal surfaces in the reference images. The high change ratio from the tool supports thi
- `D5d_0135` L=1 direct=0.02→tool=0.95 rank=0.48 **FN_corrected** used_tool=True
  > The query image contains a prominent dark, oval-shaped object in the lumen, which is absent in the normal reference images. The high structural change ratio from the tool corroborates this significant visual difference, 
- `D5d_0128` L=1 direct=0.02→tool=0.95 rank=0.35 **FN_corrected** used_tool=True
  > The query image contains a clear, raised polypoid lesion, which is a structural anomaly not present in the normal reference images. The high change ratio from the tool supports this visual finding, and the disconfirm cla
- `D5d_0023` L=0 direct=0.98→tool=0.15 rank=0.39 **FP_corrected** used_tool=True
  > The high change ratio from the tool is likely due to color/lighting differences (bile staining) rather than a structural defect, as warned in the disconfirm clause. The yellow patch appears to be normal bile residue, sim
- `D5d_0045` L=0 direct=0.92→tool=0.10 rank=0.40 **FP_corrected** used_tool=True
  > Although the tool detected significant pixel differences, the interpretation notes this is often caused by lighting/exposure changes. Visual inspection confirms the tissue structure is normal and healthy, with no visible

**LOSSES**:

- `D5d_0146` L=1 direct=0.98→tool=0.10 rank=0.38 **TP_lost_to_FN** used_tool=True
  > The high grid difference is likely due to anatomical differences (pylorus vs. colon) and lighting/contrast variations, not a defect. The query image shows a normal-appearing pylorus without obvious anomalies.
- `D5d_0161` L=1 direct=0.98→tool=0.10 rank=0.51 **TP_lost_to_FN** used_tool=True
  > The high change ratio from the tool is likely due to the yellow bile stain and lighting differences, which the tool's interpretation flags as a potential false positive for structural defects. The mucosal structure itsel
- `D5d_0166` L=1 direct=0.98→tool=0.10 rank=0.47 **TP_lost_to_FN** used_tool=True
  > The high change ratio is likely caused by the presence of the endoscopic instrument and lighting differences, as indicated by the tool's disconfirm clause. The visual features of the mucosa appear normal and consistent w
- `D5d_0169` L=1 direct=0.95→tool=0.10 rank=0.40 **TP_lost_to_FN** used_tool=True
  > The high change ratio detected by the tool is primarily due to the presence of a green UI overlay (scope position map) in the query image, which is absent in the reference images. This is a standard variation in endoscop
- `D5d_0093` L=1 direct=0.92→tool=0.10 rank=0.30 **TP_lost_to_FN** used_tool=True
  > The high change ratio from the tool is likely due to the presence of yellow fluid (bile/stool) on the mucosal surface, which is a common, non-pathological finding in endoscopy. The disconfirm clause in the tool output no
- `D5d_0129` L=1 direct=0.98→tool=0.85 rank=0.31 **other** used_tool=True
  > The query image shows a distinct yellowish discoloration (likely bile staining) that is not present in the reference images, and the high change ratio from the tool supports this structural difference. While lighting cou
- `D5d_0020` L=0 direct=0.02→tool=0.15 rank=0.26 **other** used_tool=True
  > Despite the high change ratio from the segmentation tool, the disconfirm clause indicates this could be due to lighting/exposure differences. Visual inspection confirms the query image shows normal endoscopic features co
- `D5d_0069` L=0 direct=0.02→tool=0.15 rank=0.36 **other** used_tool=True
  > Although the tool detected significant pixel differences, the interpretation notes this may be due to lighting/exposure variations rather than structural anomalies. Visual inspection confirms the tissue structure and vas
  ... and 2 more losses.

### D6  (wins 6, losses 14)

Win sample-types: {'FP_corrected': 6}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 10, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D6_0017` L=0 direct=0.95→tool=0.05 rank=0.75 **FP_corrected** used_tool=True
  > The high change ratio detected by the tool is explained by a global difference in brightness and contrast between the query and reference images, not by any structural anomaly. The scene content is consistent with the no
- `D6_0039` L=0 direct=0.95→tool=0.10 rank=0.85 **FP_corrected** used_tool=True
  > The high change ratio is likely due to global lighting/exposure differences rather than structural defects, as the scene content appears identical between query and reference images.
- `D6_0064` L=0 direct=0.95→tool=0.10 rank=0.39 **FP_corrected** used_tool=True
  > Although the segmentation tool detected a high change ratio, visual inspection confirms the structural layout is identical to the references. The difference is purely due to global lighting/exposure changes, which the to
- `D6_0063` L=0 direct=0.98→tool=0.15 rank=0.60 **FP_corrected** used_tool=True
  > The high change ratio is explained by the disconfirm clause as likely being due to global intensity/contrast differences rather than actual structural anomalies. The scene content appears consistent with reference images
- `D6_0015` L=0 direct=0.98→tool=0.20 rank=0.62 **FP_corrected** used_tool=True
  > While the tool detected some cell differences, these are likely due to minor variations in image capture (lighting, exposure) rather than actual structural anomalies. The scene content appears consistent with normal refe
- `D6_0000` L=0 direct=0.95→tool=0.30 rank=0.82 **FP_corrected** used_tool=True
  > While the tool detected structural differences, the disconfirm clause indicates this could be due to lighting/exposure changes. Visual inspection suggests the query image has different contrast/lighting than references, 

**LOSSES**:

- `D6_0024` L=0 direct=0.02→tool=0.98 rank=0.71 **TN_lost_to_FP** used_tool=True
  > The query image displays a large, irregular area of exposed light soil that is not present in the normal reference images. The tool's high change ratio confirms this major structural difference, which is not explained by
- `D6_0133` L=1 direct=0.98→tool=0.10 rank=0.82 **TP_lost_to_FN** used_tool=True
  > The high change ratio detected by the tool is likely due to seasonal differences (green vs. brown fields) and lighting variations, as indicated by the tool's disconfirm clause. The structural layout of the fields and bui
- `D6_0123` L=1 direct=0.98→tool=0.10 rank=0.74 **TP_lost_to_FN** used_tool=True
  > The high change ratio is due to the query and reference images showing completely different scenes/locations, not structural anomalies. The query image shows an undeveloped area with a single building complex, while refe
- `D6_0084` L=1 direct=0.98→tool=0.10 rank=0.41 **TP_lost_to_FN** used_tool=True
  > The tool indicates a high change ratio, but the interpretation warns this could be due to global intensity shifts. Visual inspection confirms the facility layout is consistent, with differences likely due to construction
- `D6_0104` L=1 direct=0.98→tool=0.10 rank=0.69 **TP_lost_to_FN** used_tool=True
  > The high change ratio detected by the tool is attributed to the significant color difference (brown vs. green fields) between the query and reference, which the tool's interpretation flags as a potential global intensity
- `D6_0145` L=1 direct=0.95→tool=0.10 rank=0.65 **TP_lost_to_FN** used_tool=True
  > The high change ratio detected by the tool is attributed to significant seasonal differences (vegetation color, water presence) rather than structural defects, as the underlying layout of roads and buildings remains cons
- `D6_0110` L=1 direct=0.98→tool=0.15 rank=0.36 **TP_lost_to_FN** used_tool=True
  > Despite the high change ratio from the segmentation tool, visual inspection shows the same structural layout between query and reference images. The differences appear to be due to lighting/contrast variations rather tha
- `D6_0111` L=1 direct=0.98→tool=0.15 rank=0.66 **TP_lost_to_FN** used_tool=True
  > The high change ratio is likely due to seasonal vegetation changes (drier vs greener) rather than structural anomalies. The road network and building positions appear consistent between images, indicating this is a norma
  ... and 6 more losses.

### D7  (wins 3, losses 1)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D7_0135` L=1 direct=0.02→tool=1.00 rank=0.97 **FN_corrected** used_tool=False
  > The query image depicts a tourist square with a horse carriage, while all reference images show typical urban driving scenes. The content and context are entirely different, indicating a certain anomaly.
- `D7_0159` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=True
  > The query image depicts a completely different scene (rural road with a car towing a trailer) compared to the urban/suburban driving scenes in the reference images. The high structural change ratio from the tool confirms
- `D7_0022` L=0 direct=0.95→tool=0.05 rank=0.21 **FP_corrected** used_tool=True
  > The high structural difference score is entirely explained by the drastic lighting change (daytime query vs. nighttime references), which the tool's disconfirm clause identifies as a non-anomalous cause. The scene itself

**LOSSES**:

- `D7_0045` L=0 direct=0.02→tool=0.95 rank=0.47 **TN_lost_to_FP** used_tool=True
  > The query image depicts a highway underpass scene, which is structurally and contextually different from all reference images showing open urban/suburban streets. The high change ratio from the tool confirms this fundame

→ RULE candidate: on D7, tool tends to correctly down-weight FPs when subspacead rank ∈ [0.21, 0.21].

### D8  (wins 6, losses 9)

Win sample-types: {'FP_corrected': 1, 'other': 5}
Loss sample-types: {'TP_lost_to_FN': 3, 'other': 6}

**WINS** (item · direct→tool · rank · type · rationale):

- `D8_0072` L=0 direct=0.95→tool=0.10 rank=0.50 **FP_corrected** used_tool=True
  > The detected changes are minimal and attributable to the presence of different people in the scene, which is normal variation. The structural background remains consistent with the reference images, and the tool's discon
- `D8_0114` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The segmentation tool shows minimal structural change (1/64 cells), and the interpretation warns this could be due to lighting/exposure rather than defects. The query image appears to show a normal scene of people in a s
- `D8_0159` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The detected differences are likely due to lighting variations and different people in the scene rather than structural anomalies. The disconfirm clause indicates that intensity shifts don't constitute defects, and the a
- `D8_0091` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The detected changes are likely due to normal pedestrian movement and potential lighting variations, not structural anomalies. The scene layout remains consistent with reference images.
- `D8_0150` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The structural layout is consistent with reference images. The detected differences are likely due to normal pedestrian movement and potential minor lighting variations, not an anomaly.
- `D8_0177` L=1 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The segmentation tool shows minimal structural changes (3.1% ratio) which the interpretation notes could be due to lighting variations rather than defects. The query image appears to show a normal scene consistent with t

**LOSSES**:

- `D8_0138` L=1 direct=0.95→tool=0.05 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The detected changes are consistent with normal pedestrian movement in a public space, and the tool's disconfirm clause indicates this is not a defect.
- `D8_0126` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The detected differences are attributed to a person walking in the scene, which is normal activity. The background structure remains consistent with the reference images, and the tool's disconfirm clause suggests the sig
- `D8_0133` L=1 direct=0.95→tool=0.15 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The very low change ratio (3.1%) and the tool's disconfirm clause about lighting/exposure shifts suggest this is a normal variation. The scene appears consistent with reference images showing people in a public space.
- `D8_0179` L=1 direct=0.95→tool=0.80 rank=0.50 **other** used_tool=True
  > The red bag in the foreground is a clear visual anomaly not present in the reference images, and the tool's localized difference signal supports this observation despite the low overall change ratio.
- `D8_0071` L=0 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The minimal structural difference (1/64 cells) detected by the tool is likely due to normal variations in people's positions or lighting conditions, not an actual anomaly. The scene composition appears consistent with th
- `D8_0038` L=0 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The minimal structural change (1/64 cells) combined with the tool's warning about lighting sensitivity indicates this is likely a normal scene with only minor variations in people positions or lighting conditions.
- `D8_0006` L=0 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The very low change ratio (3.1%) and the tool's disconfirm clause about lighting/exposure shifts suggest this is a normal image. The scene appears consistent with reference images showing people in a public space.
- `D8_0010` L=0 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The structural layout of the scene is consistent with the reference images. The detected differences are minor and attributed to the movement of people, which the tool's disconfirm clause suggests is not conclusive evide
  ... and 1 more losses.

### D9  (wins 7, losses 11)

Win sample-types: {'FP_corrected': 4, 'FN_corrected': 2, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 7, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D9_0078` L=0 direct=0.99→tool=0.05 rank=0.11 **FP_corrected** used_tool=True
  > The query image shows a single yellow jumper wire, which is structurally identical to the normal reference images (Ref 1 and Ref 3). The tool's detected difference is attributed to lighting or exposure variations as per 
- `D9_0121` L=1 direct=0.01→tool=0.95 rank=0.58 **FN_corrected** used_tool=False
  > The query image differs significantly from all reference images in both label (cherry vs banana) and liquid color (dark red vs light), indicating a clear anomaly.
- `D9_0168` L=1 direct=0.01→tool=0.95 rank=0.73 **FN_corrected** used_tool=False
  > The query image differs significantly from all reference images in both label icon (cherry vs banana/orange) and liquid color (dark red vs light yellow/white), indicating a clear anomaly.
- `D9_0057` L=0 direct=0.99→tool=0.10 rank=0.35 **FP_corrected** used_tool=True
  > The tool's signal is weak and explicitly flagged as potentially caused by lighting/exposure shifts. Visual inspection confirms the query image is structurally consistent with the normal reference images, showing no clear
- `D9_0022` L=0 direct=0.99→tool=0.10 rank=0.28 **FP_corrected** used_tool=True
  > The structural layout matches the reference images perfectly. The minor grid differences are attributed to lighting/exposure variations as warned in the tool's disconfirm clause, not actual anomalies.
- `D9_0079` L=0 direct=0.98→tool=0.10 rank=0.16 **FP_corrected** used_tool=True
  > The structural difference detected by the tool is attributed to the random arrangement of items and lighting variations, as confirmed by the tool's disconfirm clause. The query image contains the same components as the r
- `D9_0144` L=1 direct=0.02→tool=0.15 rank=0.11 **other** used_tool=True
  > The structural differences detected are likely due to minor variations in fruit positioning and lighting rather than an actual anomaly, as the overall composition matches the reference images.

**LOSSES**:

- `D9_0047` L=0 direct=0.02→tool=1.00 rank=0.13 **TN_lost_to_FP** used_tool=False
  > The query image differs significantly from all reference images in both the label graphic (cherry vs banana) and the liquid color (dark red vs light beige), indicating a certain anomaly.
- `D9_0032` L=0 direct=0.02→tool=1.00 rank=0.07 **TN_lost_to_FP** used_tool=False
  > The query image differs significantly from the reference images in both the label (cherry vs banana) and the liquid color (dark vs light), indicating a certain anomaly.
- `D9_0128` L=1 direct=0.99→tool=0.05 rank=0.24 **TP_lost_to_FN** used_tool=True
  > The query image depicts a standard single yellow jumper wire configuration identical to the normal references. The tool's signal is likely a false positive caused by lighting variations or reference set diversity, as exp
- `D9_0100` L=1 direct=0.99→tool=0.05 rank=0.41 **TP_lost_to_FN** used_tool=True
  > The query image depicts a single yellow jumper wire, which is a normal configuration seen in the reference images. The tool's detected difference is attributed to the disconfirm clause regarding lighting/exposure shifts,
- `D9_0176` L=1 direct=0.99→tool=0.05 rank=0.31 **TP_lost_to_FN** used_tool=True
  > Although the tool detected a coarse difference, the visual evidence shows the query image is structurally identical to the single-wire reference images. The difference is likely due to minor lighting or exposure variatio
- `D9_0041` L=0 direct=0.02→tool=0.95 rank=0.79 **TN_lost_to_FP** used_tool=False
  > The query image differs significantly from all reference images in both label (cherry vs banana/orange) and liquid color (dark red vs light yellow/white), indicating a clear anomaly.
- `D9_0090` L=1 direct=0.98→tool=0.05 rank=0.03 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing the same food items in a similar arrangement within the lunchbox. No anomalies are detected.
- `D9_0129` L=1 direct=0.98→tool=0.05 rank=0.04 **TP_lost_to_FN** used_tool=True
  > Although the tool flagged a structural difference, the interpretation's disconfirm clause notes that such signals can be caused by lighting changes. Visual inspection confirms the content and layout are normal, matching 
  ... and 3 more losses.

---

## tool_side_by_side  (72 wins, 121 losses, net flips -40 on n=480)

### D1  (wins 6, losses 5)

Win sample-types: {'FP_corrected': 4, 'FN_corrected': 2}
Loss sample-types: {'TP_lost_to_FN': 3, 'other': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D1_0038` L=0 direct=0.98→tool=0.05 rank=0.26 **FP_corrected** used_tool=True
  > The query image contains the 'actavis' logo, matching three of the four reference images. The fourth reference image lacks the logo, suggesting it is the anomaly, not the query. Therefore, the query is normal.
- `D1_0114` L=1 direct=0.02→tool=0.95 rank=0.19 **FN_corrected** used_tool=False
  > The query image has yellow bristles while all reference images have either blue or red bristles, indicating a clear color anomaly that deviates from the established pattern.
- `D1_0174` L=1 direct=0.02→tool=0.95 rank=0.15 **FN_corrected** used_tool=True
  > The query image shows a transistor with a cylindrical body, whereas all reference images show transistors with a rectangular body. This is a clear structural difference indicating an anomaly.
- `D1_0009` L=0 direct=0.95→tool=0.05 rank=0.13 **FP_corrected** used_tool=True
  > The query image displays a standard three-core cable cross-section. The side-by-side comparison confirms that any minor differences are within the range of natural variation observed in the reference images, indicating n
- `D1_0064` L=0 direct=0.98→tool=0.10 rank=0.24 **FP_corrected** used_tool=True
  > The query image displays the 'actavis' logo, which is also present in three of the four reference images. The single reference image lacking the logo appears to be the outlier in the reference set, not the query. Thus, t
- `D1_0084` L=0 direct=0.95→tool=0.10 rank=0.02 **FP_corrected** used_tool=True
  > The query image exhibits the same speckled texture as the reference images, with no unique structural or textural anomalies detected. The observed variations are consistent with natural texture variation.

**LOSSES**:

- `D1_0117` L=1 direct=0.98→tool=0.10 rank=0.68 **TP_lost_to_FN** used_tool=True
  > The query image shows a hazelnut with a cap on the side, which is a normal variation compared to the reference images where caps are on the bottom or top. No anomalous features like cracks or discoloration are present.
- `D1_0137` L=1 direct=0.98→tool=0.10 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The query image matches the majority of the reference images, showing a capsule with 'actavis' and '500' printed on it. The absence of the 'actavis' logo in one reference image is an anomaly, but the query image is norma
- `D1_0179` L=1 direct=0.95→tool=0.10 rank=0.54 **TP_lost_to_FN** used_tool=True
  > The query image shows a metallic component that is structurally and texturally consistent with the four reference images. No unique defects or anomalies were identified in the query image compared to the references.
- `D1_0044` L=0 direct=0.01→tool=0.20 rank=0.37 **other** used_tool=True
  > The query image shows the same mesh pattern as references but with a different orientation. Since the pattern structure is consistent and only the angle differs, this appears to be a normal variation rather than an anoma
- `D1_0111` L=1 direct=0.98→tool=0.85 rank=0.77 **other** used_tool=True
  > The query image contains a visible dark spot/defect in the fabric texture that is not present in any of the reference images, indicating an anomaly despite the tool's unreliable output.

### D10  (wins 3, losses 4)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D10_0156` L=1 direct=0.01→tool=0.95 rank=0.51 **FN_corrected** used_tool=False
  > The query image shows an HC-SR04 sensor without the protective mesh grilles that are clearly visible on all reference images. This missing component is a definitive anomaly.
- `D10_0094` L=1 direct=0.02→tool=0.95 rank=0.41 **FN_corrected** used_tool=False
  > The query image is upside down compared to the reference images, with the pins at the bottom and the text inverted, which is a clear anomaly.
- `D10_0002` L=0 direct=0.95→tool=0.10 rank=0.07 **FP_corrected** used_tool=True
  > The query image shows four tea light candles in a 2x2 grid arrangement, which matches the pattern seen in all reference images. No structural or textural anomalies are evident that would distinguish the query from normal

**LOSSES**:

- `D10_0153` L=1 direct=0.98→tool=0.05 rank=0.62 **TP_lost_to_FN** used_tool=True
  > Visual inspection shows the query image is consistent with the reference images. The object's shape, spokes, and central hole are normal, with no apparent anomalies.
- `D10_0139` L=1 direct=0.98→tool=0.05 rank=0.20 **TP_lost_to_FN** used_tool=True
  > The query image displays the same four yellow crescent-shaped objects on a green background as the reference images, with no visible anomalies in shape, color, or texture.
- `D10_0069` L=0 direct=0.02→tool=0.90 rank=0.27 **TN_lost_to_FP** used_tool=True
  > The query image shows a tilted rectangular object, while all reference images show horizontally aligned objects. This orientation difference is a clear anomaly.
- `D10_0136` L=1 direct=0.98→tool=0.15 rank=0.23 **TP_lost_to_FN** used_tool=True
  > After examining the side-by-side composite, the query image appears consistent with the reference images. All components (chips, resistors, capacitors, pins) are present and properly positioned. Any minor variations appe

### D2  (wins 5, losses 9)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D2_0146` L=1 direct=0.01→tool=1.00 rank=0.29 **FN_corrected** used_tool=True
  > The query image shows a distinct orange cigarette pack ('Huangjin Ye') that is visually and textually different from all four reference images (two 'Tianzi' and one 'Jinmen' packs). This mismatch in product identity conf
- `D2_0092` L=1 direct=0.01→tool=0.95 rank=0.63 **FN_corrected** used_tool=False
  > The query image contains a plastic straw wrapper attached to the carton, which is absent in all reference images, indicating a clear anomaly.
- `D2_0095` L=1 direct=0.02→tool=0.95 rank=0.86 **FN_corrected** used_tool=True
  > The query image displays a bottle filled with dark liquid, whereas the reference images show bottles with white labels that either obscure the liquid or indicate a different product state. This significant visual discrep
- `D2_0145` L=1 direct=0.02→tool=0.95 rank=0.71 **FN_corrected** used_tool=True
  > The query image has a different health warning label ('本公司提示...') compared to the reference images ('劝阻青少年吸烟...'), which is a significant and likely anomalous deviation for a standardized product.
- `D2_0037` L=0 direct=0.98→tool=0.10 rank=0.19 **FP_corrected** used_tool=True
  > The query image shows the back of the package, which matches the back views in the reference images. There are no visible defects or anomalies on the packaging itself. The difference in orientation (back vs. front with p

**LOSSES**:

- `D2_0072` L=0 direct=0.02→tool=1.00 rank=0.06 **TN_lost_to_FP** used_tool=False
  > The query image displays the back of the chip bag, whereas all four reference images display the front of the bag. This difference in orientation and visible content (nutritional info/barcode vs. logo/flavor) constitutes
- `D2_0080` L=0 direct=0.02→tool=1.00 rank=0.02 **TN_lost_to_FP** used_tool=False
  > The query image shows the back of the product packaging, while the reference images show the front. This difference in orientation makes the query image anomalous relative to the references.
- `D2_0029` L=0 direct=0.01→tool=0.95 rank=0.51 **TN_lost_to_FP** used_tool=False
  > The query image displays the back label of the bottle, whereas all reference images display the front label. This fundamental difference in the object's orientation and visible content makes the query image anomalous.
- `D2_0087` L=0 direct=0.01→tool=0.95 rank=0.08 **TN_lost_to_FP** used_tool=True
  > The query image is upside down relative to the normal reference images, as evidenced by the inverted text on the cigarette pack. This orientation difference is a definitive anomaly.
- `D2_0133` L=1 direct=0.98→tool=0.05 rank=0.08 **TP_lost_to_FN** used_tool=True
  > The query image is visually consistent with the reference images, showing the same product packaging and background. No unique anomalies were detected in the query image.
- `D2_0097` L=1 direct=0.98→tool=0.05 rank=0.73 **TP_lost_to_FN** used_tool=True
  > The query image is visually identical to the second normal reference image, showing a standard, undamaged carton of breakfast milk. No anomalies are detected.
- `D2_0170` L=1 direct=0.98→tool=0.10 rank=0.13 **TP_lost_to_FN** used_tool=True
  > The query image shows a normal snack package that matches the appearance of the reference images. No anomalous features detected - the packaging, text, and product are consistent with normal samples.
- `D2_0162` L=1 direct=0.98→tool=0.10 rank=0.80 **TP_lost_to_FN** used_tool=True
  > The query image matches the general appearance of the normal reference images, with no unique structural or textural anomalies detected. The tool's interpretation confirms that minor variations are normal.
  ... and 1 more losses.

### D4  (wins 7, losses 15)

Win sample-types: {'FN_corrected': 7}
Loss sample-types: {'TN_lost_to_FP': 6, 'TP_lost_to_FN': 7, 'other': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D4_0156` L=1 direct=0.05→tool=0.95 rank=0.20 **FN_corrected** used_tool=False
  > The query image contains a large, dark shadow or stain that is absent in all normal reference images, indicating a clear anomaly.
- `D4_0105` L=1 direct=0.05→tool=0.95 rank=0.06 **FN_corrected** used_tool=False
  > The query image contains a large dark region (likely a shadow or stain) that is absent in all normal reference images, indicating a clear anomaly.
- `D4_0115` L=1 direct=0.05→tool=0.95 rank=0.12 **FN_corrected** used_tool=True
  > The query image contains a large dark shadow/discoloration absent in all four normal reference images, which are uniformly light gray. This significant visual difference indicates an anomaly.
- `D4_0176` L=1 direct=0.05→tool=0.90 rank=0.82 **FN_corrected** used_tool=True
  > The tool output was unreliable (solid color bars), so I relied on raw image analysis. The query image exhibits a coarse, rocky texture with debris, which is structurally different from the fine, uniform granular textures
- `D4_0122` L=1 direct=0.05→tool=0.80 rank=0.79 **FN_corrected** used_tool=True
  > Based on visual inspection, the query image contains a distinct dark spot not present in the reference images, suggesting an anomaly.
- `D4_0121` L=1 direct=0.05→tool=0.75 rank=0.47 **FN_corrected** used_tool=True
  > The query image contains a distinct dark spot that is not present in any of the reference images, suggesting it is an anomaly in the otherwise consistent textured surface.
- `D4_0110` L=1 direct=0.05→tool=0.65 rank=0.70 **FN_corrected** used_tool=True
  > Based on visual inspection, the query image contains a distinct dark spot that is not consistently present in the same form across the reference images, suggesting it is likely an anomaly. However, the inability to use t

**LOSSES**:

- `D4_0037` L=0 direct=0.05→tool=0.95 rank=0.18 **TN_lost_to_FP** used_tool=True
  > The query image displays a uniform, smooth gray texture, while all reference images exhibit a distinct granular or pebbled surface structure. This fundamental difference in texture pattern indicates the query is anomalou
- `D4_0086` L=0 direct=0.05→tool=0.95 rank=0.76 **TN_lost_to_FP** used_tool=True
  > The query image contains a distinct vertical scratch/line defect that is not present in any of the normal reference images, indicating a clear anomaly.
- `D4_0006` L=0 direct=0.05→tool=0.90 rank=0.10 **TN_lost_to_FP** used_tool=True
  > The query image contains distinct elongated dark marks in the upper right quadrant that are not present in any of the normal reference images, which only exhibit small, scattered speckles. This indicates a structural ano
- `D4_0126` L=1 direct=0.95→tool=0.10 rank=0.63 **TP_lost_to_FN** used_tool=True
  > The query image shows a textured surface with small dark spots similar to the reference images. No unique structural or textural features are present only in the query that would indicate an anomaly. The observed variati
- `D4_0174` L=1 direct=0.95→tool=0.10 rank=0.75 **TP_lost_to_FN** used_tool=True
  > The query image displays a texture with small dark spots that is consistent with the natural variation observed across the reference images. No unique anomalous feature is present only in the query.
- `D4_0106` L=1 direct=0.95→tool=0.10 rank=0.49 **TP_lost_to_FN** used_tool=True
  > The primary difference is a shadow and lighting variation, not a structural or textural anomaly. The underlying surface texture matches the normal references.
- `D4_0128` L=1 direct=0.95→tool=0.10 rank=0.42 **TP_lost_to_FN** used_tool=True
  > The query image shows a texture and pattern of spots consistent with the natural variation seen in the reference images. No unique structural or textural feature is present only in the query.
- `D4_0133` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The query image displays a uniform texture consistent with the majority of the normal reference images. The shadow present is a lighting artifact, not a structural anomaly. The tool output was uninformative, but visual i
  ... and 7 more losses.

### D5  (wins 7, losses 19)

Win sample-types: {'FN_corrected': 5, 'other': 2}
Loss sample-types: {'TN_lost_to_FP': 9, 'TP_lost_to_FN': 8, 'other': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5_0179` L=1 direct=0.05→tool=0.95 rank=0.27 **FN_corrected** used_tool=True
  > The query lesion exhibits a distinct dark black center and high color variegation not present in the lighter, more uniform brown reference lesions, indicating a significant deviation from the normal class.
- `D5_0119` L=1 direct=0.05→tool=0.92 rank=0.32 **FN_corrected** used_tool=True
  > The query image displays a lesion with significant asymmetry, irregular borders, and color variegation, which are distinct from the smaller, more uniform, and symmetric lesions seen in the normal reference images.
- `D5_0166` L=1 direct=0.05→tool=0.90 rank=0.31 **FN_corrected** used_tool=True
  > The query lesion exhibits a distinct, very dark central pigmentation not present in any of the normal reference images, indicating a significant deviation from the normal class.
- `D5_0136` L=1 direct=0.08→tool=0.90 rank=0.65 **FN_corrected** used_tool=True
  > The query image displays a symmetric, uniformly pigmented lesion with regular borders, which contrasts sharply with the reference images that show asymmetric, variegated, and irregularly bordered lesions. Given that the 
- `D5_0114` L=1 direct=0.05→tool=0.85 rank=0.27 **FN_corrected** used_tool=True
  > The query image displays a lesion with a prominent reddish coloration and a specific reticular pattern that is visually distinct from the brown, more uniformly pigmented lesions shown in the reference images. This signif
- `D5_0125` L=1 direct=0.05→tool=0.20 rank=0.19 **other** used_tool=True
  > Based on visual inspection, the query lesion appears relatively uniform in color and shape, similar to the benign characteristics seen in some of the reference images. No strong indicators of anomaly are present.
- `D5_0156` L=1 direct=0.08→tool=0.20 rank=0.45 **other** used_tool=True
  > Based on visual inspection, the query lesion appears relatively symmetric and uniformly pigmented, lacking the pronounced irregularities seen in some reference images. However, the inability to use the comparison tool re

**LOSSES**:

- `D5_0030` L=0 direct=0.05→tool=0.98 rank=0.21 **TN_lost_to_FP** used_tool=True
  > The query image displays a uniform reddish area lacking the distinct brownish pigmented lesion structure seen in all normal reference images, indicating a clear anomaly.
- `D5_0032` L=0 direct=0.05→tool=0.95 rank=0.87 **TN_lost_to_FP** used_tool=False
  > The query lesion is pink and lacks the brown pigmentation seen in all reference images, indicating a significant deviation from the normal class.
- `D5_0063` L=0 direct=0.05→tool=0.95 rank=0.23 **TN_lost_to_FP** used_tool=True
  > The query lesion is significantly smaller, darker, and more irregular than the larger, lighter, and more uniform lesions in the reference images, indicating a clear anomaly.
- `D5_0066` L=0 direct=0.05→tool=0.90 rank=0.83 **TN_lost_to_FP** used_tool=True
  > The query lesion exhibits significant asymmetry, irregular borders, and darker, more variegated pigmentation compared to the more uniform, lighter, and symmetric reference lesions. These morphological differences are str
- `D5_0089` L=0 direct=0.05→tool=0.90 rank=0.42 **TN_lost_to_FP** used_tool=True
  > The query lesion exhibits a prominent dark black central blotch surrounded by a lighter brown rim, a feature absent in the uniformly lighter brown reference lesions. This significant difference in color distribution and 
- `D5_0117` L=1 direct=0.95→tool=0.10 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The query image displays a pinkish, structureless lesion similar to Reference 0. Although other references show brown pigmentation, the presence of a similar pink lesion in the normal set indicates that the query's featu
- `D5_0155` L=1 direct=0.95→tool=0.10 rank=0.65 **TP_lost_to_FN** used_tool=True
  > The query image displays a pigmented lesion with characteristics (uniform color, smooth borders) that are consistent with the majority of the provided normal reference images. No unique anomalous features are observed in
- `D5_0176` L=1 direct=0.95→tool=0.10 rank=0.46 **TP_lost_to_FN** used_tool=True
  > The query lesion shows a regular reticular pattern and uniform pigmentation, which are characteristic of benign nevi. These features are consistent with the normal variation seen in the reference images, and no specific 
  ... and 11 more losses.

### D5b  (wins 3, losses 6)

Win sample-types: {'FP_corrected': 3}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 4}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5b_0045` L=0 direct=0.98→tool=0.10 rank=0.31 **FP_corrected** used_tool=True
  > The query image shows normal brain anatomy with ventricles visible. The reference images demonstrate natural anatomical variation across different slice levels. According to the tool's interpretation, features that vary 
- `D5b_0031` L=0 direct=0.98→tool=0.10 rank=0.51 **FP_corrected** used_tool=True
  > The query image does not exhibit any unique structural or textural anomalies compared to the reference images, which show natural variation. Therefore, it is classified as normal.
- `D5b_0067` L=0 direct=0.98→tool=0.10 rank=0.53 **FP_corrected** used_tool=True
  > The query image displays typical brain anatomy consistent with the reference images, and the tool interpretation confirms that observed variations are within the normal range.

**LOSSES**:

- `D5b_0066` L=0 direct=0.02→tool=0.95 rank=0.55 **TN_lost_to_FP** used_tool=True
  > The query image displays a coronal brain slice, whereas all four reference images are axial slices. This fundamental difference in orientation means the query does not match the structural pattern of the normal reference
- `D5b_0059` L=0 direct=0.02→tool=0.90 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image exhibits significantly lower intensity and contrast compared to all four reference images, which display clear, bright anatomical structures. This stark difference suggests the query image is anomalous, e
- `D5b_0156` L=1 direct=0.98→tool=0.10 rank=0.56 **TP_lost_to_FN** used_tool=True
  > The query image appears to be a normal brain MRI slice at a different level/orientation than the references. No clear pathological anomalies are visible that would distinguish it as abnormal compared to normal anatomical
- `D5b_0149` L=1 direct=0.98→tool=0.10 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The query image displays a typical brain MRI slice without unique anomalies. The reference images show natural variation in slice level and appearance, and the query fits within this range of normal anatomical presentati
- `D5b_0160` L=1 direct=0.95→tool=0.10 rank=0.44 **TP_lost_to_FN** used_tool=True
  > The query image displays normal brain anatomy with ventricle structures consistent with the natural variation observed in the reference images. No definitive anomaly is detected.
- `D5b_0122` L=1 direct=0.98→tool=0.15 rank=0.60 **TP_lost_to_FN** used_tool=True
  > The query image shows a brain MRI with normal anatomical structures. The color difference appears to be a normalization/processing variation rather than a pathological anomaly. No structural abnormalities are evident tha

### D5c  (wins 10, losses 9)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 5}
Loss sample-types: {'TN_lost_to_FP': 5, 'TP_lost_to_FN': 3, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5c_0174` L=1 direct=0.05→tool=1.00 rank=0.97 **FN_corrected** used_tool=False
  > The query image contains a significantly smaller and differently shaped object compared to the large, consistent organ shapes in all reference images, indicating a severe anomaly.
- `D5c_0131` L=1 direct=0.02→tool=0.95 rank=0.90 **FN_corrected** used_tool=False
  > The query image contains a completely different object (small oval) compared to the consistent kidney-bean-shaped structures in all reference images, indicating a clear anomaly.
- `D5c_0118` L=1 direct=0.02→tool=0.95 rank=0.96 **FN_corrected** used_tool=True
  > The query image shows a single object, while one of the normal reference images (the second one) shows two separate objects. This discrepancy in the number of objects indicates the query is anomalous.
- `D5c_0165` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=True
  > The query image displays a distinct dark hole within the object, a feature completely absent in all normal reference images which show solid, simpler shapes. This structural discrepancy indicates an anomaly.
- `D5c_0100` L=1 direct=0.05→tool=0.95 rank=0.79 **FN_corrected** used_tool=True
  > The query object has a unique elongated, hook-like morphology that is fundamentally different from the compact, rounded shapes seen in all reference images, indicating a strong anomaly.
- `D5c_0035` L=0 direct=0.95→tool=0.10 rank=0.81 **FP_corrected** used_tool=True
  > The query image displays an object that is consistent in size, shape, and texture with three of the four reference images. The one differing reference image (with a hole and larger size) appears to be the anomaly in the 
- `D5c_0083` L=0 direct=0.95→tool=0.10 rank=1.00 **FP_corrected** used_tool=True
  > The query image displays a single, crescent-shaped object that falls within the range of shapes and sizes observed in the normal reference images. No distinct anomalies are visible.
- `D5c_0003` L=0 direct=0.95→tool=0.20 rank=0.97 **FP_corrected** used_tool=True
  > The query image displays a small, solid, textured object. The reference images show a wide range of normal variations, including objects of similar small size and solid texture (e.g., Ref 3, Ref 4). The presence of large
  ... and 2 more wins.

**LOSSES**:

- `D5c_0004` L=0 direct=0.02→tool=1.00 rank=0.94 **TN_lost_to_FP** used_tool=False
  > The query image lacks the prominent textured object seen in all four reference images, containing only a tiny speck instead. This absence of the expected object makes it certainly anomalous.
- `D5c_0042` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=True
  > The query image displays a significantly larger object with distinct internal holes compared to the smaller, solid objects in the reference images, indicating a clear anomaly.
- `D5c_0015` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=True
  > The query object has a unique hook-like morphology that is fundamentally different from the compact, irregular shapes seen in all reference images, confirming it as an anomaly.
- `D5c_0061` L=0 direct=0.02→tool=0.95 rank=0.84 **TN_lost_to_FP** used_tool=True
  > The query image exhibits a complex, multi-part structure with an internal void, which is fundamentally different from the simpler, solid shapes seen in all four reference images. This significant structural deviation ind
- `D5c_0039` L=0 direct=0.02→tool=0.90 rank=0.90 **TN_lost_to_FP** used_tool=True
  > The query image shows a large object, whereas one of the reference images shows a significantly smaller object, indicating a potential anomaly in size.
- `D5c_0159` L=1 direct=0.95→tool=0.10 rank=0.95 **TP_lost_to_FN** used_tool=True
  > Based on visual inspection, the query image appears consistent with the normal reference images in terms of shape and texture. No significant anomalies are detected.
- `D5c_0170` L=1 direct=0.95→tool=0.10 rank=0.97 **TP_lost_to_FN** used_tool=True
  > The query object's texture and general appearance match the smaller objects seen in the reference images. The variation in size and position across the reference set suggests these are normal variations, making the query
- `D5c_0107` L=1 direct=0.95→tool=0.30 rank=0.99 **TP_lost_to_FN** used_tool=True
  > The query image shows a small, elongated shape similar to some reference images, but the last reference image has a significantly larger and more irregular shape, suggesting potential anomaly. However, without clear doma
  ... and 1 more losses.

### D5d  (wins 6, losses 14)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 3, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 4, 'TP_lost_to_FN': 7, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5d_0173` L=1 direct=0.02→tool=0.95 rank=0.57 **FN_corrected** used_tool=True
  > The query image contains a distinct dark, oval-shaped object in the center of the lumen, which is not present in any of the normal reference images. This object appears to be a foreign body or a significant pathological 
- `D5d_0135` L=1 direct=0.02→tool=0.95 rank=0.48 **FN_corrected** used_tool=True
  > The query image contains a distinct dark, oval-shaped object in the lumen that is not present in any of the normal reference images, indicating a clear anomaly.
- `D5d_0150` L=1 direct=0.02→tool=0.95 rank=0.59 **FN_corrected** used_tool=True
  > The query image displays a distinct, raised, oval-shaped mass (likely a polyp) in the center of the lumen, which is not present in any of the normal reference images showing only smooth mucosal folds. This structural dif
- `D5d_0045` L=0 direct=0.92→tool=0.10 rank=0.40 **FP_corrected** used_tool=True
  > The query image displays normal gastrointestinal mucosa with smooth texture and natural folds, consistent with the reference images. No unique anomalous features are present that would indicate pathology.
- `D5d_0023` L=0 direct=0.98→tool=0.20 rank=0.39 **FP_corrected** used_tool=True
  > The yellow discoloration in the query image appears to be bile staining, which is a common and often normal finding in endoscopy. One of the reference images also shows a similar yellowish hue, suggesting this is not a u
- `D5d_0071` L=0 direct=0.95→tool=0.65 rank=0.47 **other** used_tool=True
  > The query image contains a prominent yellow discoloration not present in most reference images, suggesting an anomaly (likely bile or residue), although one reference shows similar staining, making it less certain.

**LOSSES**:

- `D5d_0069` L=0 direct=0.02→tool=0.95 rank=0.36 **TN_lost_to_FP** used_tool=False
  > The query image contains a prominent, abnormal submucosal mass (bluish lesion) which is not present in any of the normal reference images, indicating a significant anomaly.
- `D5d_0029` L=0 direct=0.02→tool=0.95 rank=0.35 **TN_lost_to_FP** used_tool=True
  > The query image displays a prominent raised lesion (polyp) which is absent in all normal reference images showing healthy mucosal folds. This structural abnormality indicates an anomaly.
- `D5d_0042` L=0 direct=0.02→tool=0.95 rank=0.36 **TN_lost_to_FP** used_tool=True
  > The query image contains a prominent dark vertical object (endoscope shaft) obstructing the view, which is not present in any of the normal reference images showing clear lumen views. This structural difference confirms 
- `D5d_0125` L=1 direct=0.98→tool=0.05 rank=0.40 **TP_lost_to_FN** used_tool=True
  > The query image shows normal colonic mucosa with typical vascular patterns and color, consistent with the provided normal reference images. No significant deviations or anomalies are observed.
- `D5d_0129` L=1 direct=0.98→tool=0.10 rank=0.31 **TP_lost_to_FN** used_tool=True
  > The yellowish stain in the query image appears to be bile or fluid, which is also visible in multiple reference images (e.g., Ref 2, 3, 4). Since this feature is present in the normal references, it is not considered an 
- `D5d_0170` L=1 direct=0.98→tool=0.10 rank=0.44 **TP_lost_to_FN** used_tool=True
  > The query image shows normal anatomical structures consistent with the reference images, with no unique anomalies detected.
- `D5d_0146` L=1 direct=0.98→tool=0.10 rank=0.38 **TP_lost_to_FN** used_tool=True
  > The query image displays normal anatomical features with common endoscopic artifacts like bile residue and small debris, which are also present in the normal reference images. No distinct pathological anomalies are visib
- `D5d_0166` L=1 direct=0.98→tool=0.10 rank=0.47 **TP_lost_to_FN** used_tool=True
  > The query image appears normal with no significant anomalies compared to the reference images. The slight variations observed are within the range of natural variation.
  ... and 6 more losses.

### D6  (wins 5, losses 16)

Win sample-types: {'FP_corrected': 4, 'FN_corrected': 1}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 10, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D6_0015` L=0 direct=0.98→tool=0.10 rank=0.62 **FP_corrected** used_tool=True
  > The tool output was unreliable (solid color block). Visual inspection of the raw images shows the query is consistent with the reference images, depicting the same rural landscape without any anomalous features.
- `D6_0000` L=0 direct=0.95→tool=0.10 rank=0.82 **FP_corrected** used_tool=True
  > The query image shows a relatively uniform field texture compared to the references which have more varied patterns. However, this difference is likely due to natural variation in field conditions (e.g., crop stage, soil
- `D6_0039` L=0 direct=0.95→tool=0.10 rank=0.85 **FP_corrected** used_tool=True
  > The query image depicts a standard rural scene with a field, road, and small structure. While it differs from the single visible reference image (which shows a paved area), these differences appear to be natural variatio
- `D6_0064` L=0 direct=0.95→tool=0.10 rank=0.39 **FP_corrected** used_tool=True
  > The side-by-side tool failed to produce a valid composite image. Based on direct visual inspection, the query image appears consistent with the normal reference images, showing no clear anomalies.
- `D6_0100` L=1 direct=0.02→tool=0.80 rank=0.68 **FN_corrected** used_tool=True
  > The query image shows a green field while all reference images show a brown/dry field in the same location. This stark color difference is not a slight degree variation but a fundamental change, indicating an anomaly. Th

**LOSSES**:

- `D6_0024` L=0 direct=0.02→tool=0.95 rank=0.71 **TN_lost_to_FP** used_tool=True
  > The query image contains a large, anomalous patch of light-colored soil that is not present in any of the normal reference images, which all show uniform dark tilled earth.
- `D6_0018` L=0 direct=0.02→tool=0.95 rank=0.55 **TN_lost_to_FP** used_tool=True
  > The query image shows a large, light brown/tan field in the center-right area, whereas the reference image shows a green field in the same location. This significant color difference in a large, distinct region indicates
- `D6_0032` L=0 direct=0.02→tool=0.95 rank=0.53 **TN_lost_to_FP** used_tool=True
  > The pond in the query image is dark and murky, whereas in all reference images it is clear and greenish-blue. This is a distinct visual anomaly not explained by natural variation.
- `D6_0117` L=1 direct=0.99→tool=0.10 rank=0.78 **TP_lost_to_FN** used_tool=True
  > The tool output was not useful due to corrupted image data. Based on the raw images, the query image appears to be a normal rural scene without obvious anomalies compared to the reference images.
- `D6_0111` L=1 direct=0.98→tool=0.10 rank=0.66 **TP_lost_to_FN** used_tool=True
  > The tool failed to provide a composite image. Based on raw image inspection, the query image shows natural variation in vegetation color compared to references, but structural elements (roads, buildings) are consistent. 
- `D6_0136` L=1 direct=0.98→tool=0.10 rank=0.70 **TP_lost_to_FN** used_tool=True
  > The tool failed to provide a usable composite, but visual inspection of the raw images shows the query is consistent with the reference images in terms of scene content (road, vegetation, buildings). Any minor difference
- `D6_0106` L=1 direct=0.98→tool=0.10 rank=0.64 **TP_lost_to_FN** used_tool=True
  > The query image shows a similar scene to the references but at a different stage of development (e.g., missing housing, different pond). These are natural variations over time, not structural anomalies. The key features 
- `D6_0104` L=1 direct=0.98→tool=0.10 rank=0.69 **TP_lost_to_FN** used_tool=True
  > The tool output was invalid (solid color block). Visual inspection of raw images shows the query and references depict the same location with identical infrastructure (roads, houses). The only difference is the field sta
  ... and 8 more losses.

### D7  (wins 2, losses 3)

Win sample-types: {'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 1, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D7_0159` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=False
  > The query image depicts a rural scene with a car towing a trailer, which is a significant deviation from the urban/suburban driving scenes present in all four reference images. The context and content are fundamentally d
- `D7_0135` L=1 direct=0.02→tool=0.95 rank=0.97 **FN_corrected** used_tool=True
  > The query image contains a large overhead structure and a bus, which are unique features not found in any of the reference images. The reference images depict different scenes (park, city street, night streets) without t

**LOSSES**:

- `D7_0086` L=0 direct=0.02→tool=0.95 rank=0.67 **TN_lost_to_FP** used_tool=False
  > The query image depicts a night-time highway, whereas all four reference images show daytime city streets. The significant difference in lighting conditions and scene type indicates the query is anomalous.
- `D7_0095` L=1 direct=0.99→tool=0.10 rank=0.95 **TP_lost_to_FN** used_tool=True
  > The query image displays typical night driving conditions with light glare, which is consistent with natural variations seen in the reference images. No structural or content anomalies are detected.
- `D7_0076` L=0 direct=0.02→tool=0.15 rank=0.74 **other** used_tool=True
  > The query image shows a typical night driving scene at an intersection with normal elements like streetlights, traffic signals, and a billboard. No anomalous features are present that distinguish it from normal driving s

### D8  (wins 11, losses 10)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 8, 'other': 2}
Loss sample-types: {'TN_lost_to_FP': 8, 'TP_lost_to_FN': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D8_0112` L=1 direct=0.02→tool=0.95 rank=0.50 **FN_corrected** used_tool=True
  > The query image features a uniformed individual (likely security or police) walking in the foreground, a feature completely absent in the reference images which show only civilians or empty space. This is a clear semanti
- `D8_0091` L=1 direct=0.02→tool=0.95 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a person standing still in the foreground, which is an anomaly compared to the reference images where the foreground is either empty or shows people in motion.
- `D8_0175` L=1 direct=0.02→tool=0.95 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a person in a uniform, which is a distinct deviation from the reference images that only show civilians in casual clothing. This suggests an anomalous event or presence.
- `D8_0130` L=1 direct=0.02→tool=0.95 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a person in a uniform, which is a significant deviation from the reference images that exclusively show civilians in casual clothing. This suggests an anomalous event or presence.
- `D8_0107` L=1 direct=0.02→tool=0.90 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a uniformed officer in the foreground, which is a distinct deviation from the reference images that only show civilians. This suggests the query is anomalous.
- `D8_0159` L=1 direct=0.02→tool=0.90 rank=0.50 **FN_corrected** used_tool=True
  > The query image features a uniformed security or police officer in the foreground, a specific type of person not present in any of the four reference images which show various civilians. While the scene structure is norm
- `D8_0072` L=0 direct=0.95→tool=0.10 rank=0.50 **FP_corrected** used_tool=True
  > The query image displays a scene consistent with the reference images, showing people in a public area with no unique structural or textural anomalies. The natural variation observed in the references supports the conclu
- `D8_0177` L=1 direct=0.02→tool=0.80 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a uniformed security/police officer walking prominently in the foreground, which is not present in any of the reference images showing only civilians. This suggests an anomalous event.
  ... and 3 more wins.

**LOSSES**:

- `D8_0014` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image features a uniformed person walking in the foreground, which is absent in all reference images that show only civilians. This distinct difference indicates an anomaly.
- `D8_0032` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image features a uniformed officer walking in the foreground, whereas all reference images show only civilians in similar positions. This distinct difference in the subject's attire and role indicates an anomal
- `D8_0050` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image features a uniformed person in the foreground, which is absent in all reference images that show only civilians. This constitutes a clear visual anomaly.
- `D8_0008` L=0 direct=0.05→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed security or police officer walking in the foreground, a feature not present in any of the normal reference images which show only civilians or empty space. This distinct difference in
- `D8_0005` L=0 direct=0.02→tool=0.90 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed individual walking in the foreground, a feature not present in any of the reference images which show only civilians or empty space in that area. This deviation from the normal patter
- `D8_0065` L=0 direct=0.02→tool=0.90 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image features a uniformed individual walking in the foreground, whereas all reference images show only civilians in casual attire. This distinct difference in subject type indicates an anomaly.
- `D8_0138` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The query image depicts a normal scene with people moving through a public area. The differences observed are due to natural temporal variation in pedestrian traffic, not structural or object anomalies. The disconfirm cl
- `D8_0126` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The uniformed person in the query image is likely a security officer or police, which is a normal presence in a public station area. The background and scene composition are consistent with the reference images, showing 
  ... and 2 more losses.

### D9  (wins 7, losses 11)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 8}

**WINS** (item · direct→tool · rank · type · rationale):

- `D9_0121` L=1 direct=0.01→tool=1.00 rank=0.58 **FN_corrected** used_tool=False
  > The query image contains a cherry label and red liquid, whereas all reference images contain banana labels and light-colored liquid, indicating a definitive anomaly.
- `D9_0168` L=1 direct=0.01→tool=1.00 rank=0.73 **FN_corrected** used_tool=False
  > The query image displays a red liquid with a cherry label, whereas all reference images consistently show a light-colored liquid with a banana label. This deviation in both content and label indicates an anomaly.
- `D9_0078` L=0 direct=0.99→tool=0.05 rank=0.11 **FP_corrected** used_tool=True
  > The tool output was unreliable (solid color bars), so I relied on direct visual comparison. The query image matches the single yellow wire reference images perfectly, and the red wire references represent normal dataset 
- `D9_0079` L=0 direct=0.98→tool=0.05 rank=0.16 **FP_corrected** used_tool=True
  > The query image contains the same number and type of hardware items (2 bolts, 2 nuts, 2 washers) as the reference images. The only difference is the arrangement within the bag, which is a natural variation and not an ano
- `D9_0057` L=0 direct=0.99→tool=0.10 rank=0.35 **FP_corrected** used_tool=True
  > The query image shows a yellow cable with orange connectors, similar to the reference images. The slight curvature of the cable is within the natural variation observed across the reference set. No unique structural or t
- `D9_0022` L=0 direct=0.99→tool=0.10 rank=0.28 **FP_corrected** used_tool=True
  > The query image's yellow cable and orange connectors match the normal variation seen in reference images 1 and 3. No anomalous features are present that aren't also found in the normal references.
- `D9_0039` L=0 direct=0.98→tool=0.10 rank=0.05 **FP_corrected** used_tool=False
  > The query image displays a standard arrangement of food items in a lunchbox, consistent with the provided normal reference images. No anomalies are detected.

**LOSSES**:

- `D9_0047` L=0 direct=0.02→tool=1.00 rank=0.13 **TN_lost_to_FP** used_tool=False
  > The query image displays a cherry-labeled bottle with red liquid, whereas all reference images show banana-labeled bottles with light liquid. This consistent difference in both label and content confirms the query is ano
- `D9_0041` L=0 direct=0.02→tool=1.00 rank=0.79 **TN_lost_to_FP** used_tool=False
  > The query image displays a red liquid with a cherry label, whereas all reference images show light-colored liquids with banana or orange labels. This significant difference in both liquid color and label content indicate
- `D9_0032` L=0 direct=0.02→tool=1.00 rank=0.07 **TN_lost_to_FP** used_tool=False
  > The query image contains a red liquid with a cherry label, whereas all reference images contain a white liquid with a banana label. This difference in content and labeling is a definitive anomaly.
- `D9_0128` L=1 direct=0.99→tool=0.05 rank=0.24 **TP_lost_to_FN** used_tool=True
  > The query image shows a single yellow jumper wire, which is structurally identical to two of the provided normal reference images. The tool's interpretation confirms that natural variation exists in the references, and t
- `D9_0178` L=1 direct=0.98→tool=0.05 rank=0.66 **TP_lost_to_FN** used_tool=True
  > The query image is visually identical to the second reference image (single yellow cable with single connectors), indicating it is a normal sample within the dataset's variations.
- `D9_0090` L=1 direct=0.98→tool=0.05 rank=0.03 **TP_lost_to_FN** used_tool=True
  > The query image matches the normal reference images in all observable aspects: fruit types, counts, and arrangement of granola and dried fruit. No anomalies detected.
- `D9_0100` L=1 direct=0.99→tool=0.10 rank=0.41 **TP_lost_to_FN** used_tool=False
  > The query image matches the pattern of the normal reference images showing single jumper wires on a mesh background. No visual anomalies are detected.
- `D9_0157` L=1 direct=0.99→tool=0.10 rank=0.48 **TP_lost_to_FN** used_tool=True
  > The query image displays an intact yellow cable with connectors, which is structurally consistent with the normal reference image showing an intact yellow cable. The presence of a different color (red) in other reference
  ... and 3 more losses.

---

## tool_texture_fft  (52 wins, 81 losses, net flips -29 on n=480)

### D1  (wins 6, losses 4)

Win sample-types: {'FP_corrected': 5, 'other': 1}
Loss sample-types: {'TP_lost_to_FN': 4}

**WINS** (item · direct→tool · rank · type · rationale):

- `D1_0009` L=0 direct=0.95→tool=0.05 rank=0.13 **FP_corrected** used_tool=True
  > The low periodicity score indicates an irregular texture, which the tool's disconfirm clause states is normal for this type of object. Visually, the query image matches the reference images in structure and appearance, c
- `D1_0038` L=0 direct=0.98→tool=0.10 rank=0.26 **FP_corrected** used_tool=False
  > The query image appears normal as it shows a standard capsule with expected markings. The absence of 'actavis' in some reference images might be due to different angles or lighting, but the query image itself does not sh
- `D1_0064` L=0 direct=0.98→tool=0.10 rank=0.24 **FP_corrected** used_tool=False
  > The query image appears normal as it matches the expected appearance of the capsule with both 'actavis' and '500' markings, similar to some of the reference images.
- `D1_0084` L=0 direct=0.95→tool=0.10 rank=0.02 **FP_corrected** used_tool=False
  > The query image exhibits the same random speckled texture as the reference images, with no obvious visual defects or deviations. The texture is non-periodic, so the FFT tool would not be discriminative. Based on visual s
- `D1_0088` L=0 direct=0.95→tool=0.10 rank=0.29 **FP_corrected** used_tool=False
  > The query image appears visually consistent with the normal reference images. The transistor is properly mounted, pins are intact, and the PCB traces and pads look standard. No obvious anomalies are detected.
- `D1_0016` L=0 direct=0.98→tool=0.85 rank=0.06 **other** used_tool=True
  > The query image shows a distinct color difference in the top conductor's copper strands (shiny/bright) compared to the darker, oxidized strands in the reference images. The texture tool's low periodicity score was explic

**LOSSES**:

- `D1_0094` L=1 direct=0.98→tool=0.05 rank=0.77 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard 'actavis 500' capsule with no apparent defects or anomalies.
- `D1_0111` L=1 direct=0.98→tool=0.05 rank=0.77 **TP_lost_to_FN** used_tool=True
  > The low periodicity score is expected for woven fabric textures and the interpretation explicitly warns against using this alone to flag anomalies. Visual inspection confirms the query image matches the reference images 
- `D1_0142` L=1 direct=0.95→tool=0.05 rank=0.32 **TP_lost_to_FN** used_tool=True
  > The low periodicity score indicates an irregular texture, but the tool's disconfirm clause states this is normal for natural scenes like wood. Visual inspection confirms the query image is a standard wood texture similar
- `D1_0179` L=1 direct=0.95→tool=0.05 rank=0.54 **TP_lost_to_FN** used_tool=True
  > The low periodicity score indicates irregular texture, but the tool's disconfirm clause states this is normal for such domains. Visual inspection confirms the query image is consistent with the normal reference images in

### D10  (wins 3, losses 4)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 1}
Loss sample-types: {'TP_lost_to_FN': 4}

**WINS** (item · direct→tool · rank · type · rationale):

- `D10_0076` L=0 direct=0.98→tool=0.05 rank=0.12 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard HC-SR04 module with no apparent defects or anomalies.
- `D10_0094` L=1 direct=0.02→tool=0.95 rank=0.41 **FN_corrected** used_tool=True
  > The query image shows smooth transducer surfaces, whereas all reference images show a distinct mesh grille. The low periodicity score confirms the absence of the mesh texture, which is a clear anomaly for this specific c
- `D10_0002` L=0 direct=0.95→tool=0.05 rank=0.07 **FP_corrected** used_tool=True
  > The low periodicity score indicates an irregular texture, which the tool's disconfirm clause states is normal for this type of scene (fabric background). Visual inspection confirms the query image matches the reference i

**LOSSES**:

- `D10_0097` L=1 direct=0.99→tool=0.05 rank=0.34 **TP_lost_to_FN** used_tool=True
  > The query image is visually identical to the normal reference images. The tool's low periodicity score is expected for a PCB image and the interpretation confirms that irregular texture does not imply anomaly in this con
- `D10_0139` L=1 direct=0.98→tool=0.05 rank=0.20 **TP_lost_to_FN** used_tool=True
  > The low periodicity score indicates irregular texture, but the tool's disconfirm clause clarifies that this is normal for such objects and does not indicate an anomaly. Visual inspection confirms the query matches the re
- `D10_0136` L=1 direct=0.98→tool=0.10 rank=0.23 **TP_lost_to_FN** used_tool=True
  > The low periodicity score is expected for a PCB and does not indicate an anomaly per the tool's disconfirm clause. Visual inspection confirms the query image matches the normal reference images in structure and component
- `D10_0158` L=1 direct=0.98→tool=0.15 rank=0.48 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicated irregular texture, but its interpretation explicitly disconfirms using this as an anomaly signal for natural objects. The small dark spot is a minor visual feature that may represent normal

### D2  (wins 3, losses 8)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 6}

**WINS** (item · direct→tool · rank · type · rationale):

- `D2_0092` L=1 direct=0.01→tool=1.00 rank=0.63 **FN_corrected** used_tool=False
  > The query image contains a plastic straw wrapper on the front of the carton, which is absent in all normal reference images, indicating a clear anomaly.
- `D2_0037` L=0 direct=0.98→tool=0.05 rank=0.19 **FP_corrected** used_tool=True
  > The low periodicity score is expected for a crumpled package with text and graphics. The tool's disconfirm clause explicitly warns that irregular texture is normal for such objects and should not be treated as an anomaly
- `D2_0095` L=1 direct=0.02→tool=0.95 rank=0.86 **FN_corrected** used_tool=True
  > The query image shows a bottle filled with dark liquid, while all reference images show bottles with white labels and clear liquid. This is a clear semantic anomaly (different product state/type). The texture tool's low 

**LOSSES**:

- `D2_0080` L=0 direct=0.02→tool=1.00 rank=0.02 **TN_lost_to_FP** used_tool=False
  > The query image displays the back of the product packaging, whereas all reference images display the front. This difference in view is a definitive anomaly.
- `D2_0167` L=1 direct=0.98→tool=0.02 rank=0.18 **TP_lost_to_FN** used_tool=True
  > The query image is visually consistent with the normal references. The tool's low periodicity score indicates an irregular texture, which the tool's disconfirm clause notes is normal for this type of image and should not
- `D2_0056` L=0 direct=0.01→tool=0.95 rank=0.05 **TN_lost_to_FP** used_tool=False
  > The query image displays a distinctly different packaging design with a blue grid pattern and different text arrangement compared to the consistent blueberry milk drink packaging in all reference images, indicating a cle
- `D2_0133` L=1 direct=0.98→tool=0.05 rank=0.08 **TP_lost_to_FN** used_tool=False
  > The query image is visually indistinguishable from the normal reference images, showing the same product packaging and background without any apparent defects.
- `D2_0162` L=1 direct=0.98→tool=0.05 rank=0.80 **TP_lost_to_FN** used_tool=True
  > The texture analysis indicated irregularity, but the tool's disconfirm clause states this is normal for such surfaces and should not trigger an anomaly flag. Visually, the query image is a standard closed cigarette pack,
- `D2_0170` L=1 direct=0.98→tool=0.10 rank=0.13 **TP_lost_to_FN** used_tool=False
  > The query image shows a normal product variant (red packaging) that matches one of the reference images. The pink packages in other references are simply a different product variant, not anomalies. No defects or irregula
- `D2_0130` L=1 direct=0.98→tool=0.10 rank=0.70 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicated low periodicity, but the disconfirm clause states this is normal for irregular textures and should not be used to flag an anomaly. The visual difference in the logo is likely a product vari
- `D2_0153` L=1 direct=0.95→tool=0.10 rank=0.74 **TP_lost_to_FN** used_tool=True
  > The low periodicity score is expected for a printed carton with text and graphics, and the disconfirm clause explicitly warns against flagging this as an anomaly. Additionally, one of the reference images shows a similar

### D4  (wins 0, losses 4)

Win sample-types: {}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 3}

**LOSSES**:

- `D4_0086` L=0 direct=0.05→tool=0.95 rank=0.76 **TN_lost_to_FP** used_tool=True
  > The query image displays a clear vertical linear defect (crack/seam) not present in the normal reference images. The FFT tool's low periodicity score is explicitly disconfirmed by its interpretation clause for irregular 
- `D4_0106` L=1 direct=0.95→tool=0.10 rank=0.49 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicates low periodicity, which the interpretation clarifies is normal for irregular surfaces like concrete. The visual differences in the query image are attributed to lighting (shadow) rather than
- `D4_0128` L=1 direct=0.95→tool=0.10 rank=0.42 **TP_lost_to_FN** used_tool=True
  > The low periodicity score indicates irregular texture, which is normal for concrete surfaces. The query image shows typical concrete characteristics consistent with the reference images, with no obvious anomalies detecte
- `D4_0155` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The low periodicity score indicates an irregular texture, which is explicitly noted as normal for domains like concrete. The visual appearance of the query image matches the normal reference images of concrete surfaces w

### D5  (wins 0, losses 11)

Win sample-types: {}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 9}

**LOSSES**:

- `D5_0099` L=1 direct=0.95→tool=0.10 rank=0.65 **TP_lost_to_FN** used_tool=True
  > The tool indicated low periodicity, but the interpretation clause explicitly states this is normal for tissue and should not be used to flag anomaly. Visually, the query lesion is consistent with the reference images of 
- `D5_0117` L=1 direct=0.95→tool=0.10 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicated low periodicity (irregular texture), but the interpretation explicitly warns that this is normal for tissue and should not be used to flag an anomaly. Visually, the lesion appears relativel
- `D5_0112` L=1 direct=0.95→tool=0.10 rank=0.75 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicated irregular texture, but the disconfirm clause clarifies that this is normal for tissue. The query image visually matches the normal reference images, showing no distinct anomalous features.
- `D5_0176` L=1 direct=0.95→tool=0.10 rank=0.46 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicated low periodicity, but the disconfirm clause noted that irregular texture is normal for tissue. Visually, the lesion exhibits a reticular pattern common in benign skin lesions, consistent wit
- `D5_0158` L=1 direct=0.95→tool=0.10 rank=0.35 **TP_lost_to_FN** used_tool=True
  > The tool indicates irregular texture, but the disconfirm clause clarifies that this is normal for skin tissue. Visually, the query lesion is consistent with the normal reference images, showing no obvious structural anom
- `D5_0172` L=1 direct=0.95→tool=0.10 rank=0.49 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicated irregularity, but the disconfirm clause states this is normal for tissue. The visual features (central white area) are consistent with benign skin lesions, so the image is classified as nor
- `D5_0167` L=1 direct=0.95→tool=0.10 rank=0.48 **TP_lost_to_FN** used_tool=False
  > The query image exhibits features consistent with the normal reference images (symmetry, uniform pigmentation, regular borders). The available tool measures texture periodicity, which is not a relevant feature for this t
- `D5_0115` L=1 direct=0.95→tool=0.10 rank=0.57 **TP_lost_to_FN** used_tool=True
  > The tool indicates irregular texture, but the disconfirm clause states this is normal for tissue. Visually, the lesion appears uniform and well-defined, suggesting it is normal.
  ... and 3 more losses.

### D5b  (wins 4, losses 2)

Win sample-types: {'FP_corrected': 4}
Loss sample-types: {'TP_lost_to_FN': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5b_0031` L=0 direct=0.98→tool=0.05 rank=0.51 **FP_corrected** used_tool=True
  > The texture analysis confirms irregular texture, which is expected for brain MRI scans. The visual appearance of the query image matches the normal reference images, showing no signs of anomaly.
- `D5b_0045` L=0 direct=0.98→tool=0.05 rank=0.31 **FP_corrected** used_tool=True
  > The tool indicated low periodicity, but the interpretation correctly notes that irregular texture is normal for brain tissue. The query image displays a standard anatomical structure (brain with ventricles) consistent wi
- `D5b_0058` L=0 direct=0.95→tool=0.05 rank=0.52 **FP_corrected** used_tool=True
  > The low periodicity score is expected for brain tissue and does not indicate an anomaly. Visual inspection confirms the query image matches the normal reference images in structure and appearance.
- `D5b_0067` L=0 direct=0.98→tool=0.10 rank=0.53 **FP_corrected** used_tool=False
  > The query image displays a typical brain MRI slice with no obvious structural anomalies compared to the general appearance of the reference images. The texture FFT tool is not suitable for detecting anatomical anomalies 

**LOSSES**:

- `D5b_0156` L=1 direct=0.98→tool=0.05 rank=0.56 **TP_lost_to_FN** used_tool=True
  > The low periodicity score is expected for brain tissue and does not indicate an anomaly. Visual inspection confirms the query image matches the normal reference images in structure and appearance.
- `D5b_0160` L=1 direct=0.95→tool=0.10 rank=0.44 **TP_lost_to_FN** used_tool=False
  > The query image displays a standard axial brain MRI slice with clear anatomical structures (ventricles, cortex) that appear consistent with normal variations seen in the reference images. There are no obvious signs of an

### D5c  (wins 12, losses 11)

Win sample-types: {'FP_corrected': 8, 'FN_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 9}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5c_0131` L=1 direct=0.02→tool=0.95 rank=0.90 **FN_corrected** used_tool=False
  > The query image contains a distinctly different object (small, oval) compared to the consistent kidney-shaped objects in the reference images, indicating a clear anomaly.
- `D5c_0165` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=True
  > While the texture periodicity is low (irregular), the tool's disconfirm clause notes this is common in normal tissue-like images. The decisive anomaly is the large, distinct dark void present in the query image but absen
- `D5c_0038` L=0 direct=0.95→tool=0.05 rank=0.89 **FP_corrected** used_tool=True
  > The texture FFT tool indicates low periodicity, which the tool's own interpretation notes is common in normal domains like tissue. The query image's visual appearance (irregular shape and texture) is consistent with the 
- `D5c_0070` L=0 direct=0.95→tool=0.05 rank=0.91 **FP_corrected** used_tool=True
  > The query image displays an irregular, speckled texture identical to the reference images. The tool's low periodicity score confirms this irregularity, and the tool's interpretation explicitly warns against flagging this
- `D5c_0032` L=0 direct=0.95→tool=0.05 rank=0.84 **FP_corrected** used_tool=True
  > The texture FFT tool indicated low periodicity, but the interpretation explicitly disconfirmed this as an anomaly signal for irregular textures common in such domains. Visually, the query image texture matches the refere
- `D5c_0100` L=1 direct=0.05→tool=0.95 rank=0.79 **FN_corrected** used_tool=False
  > The query image exhibits a significantly different global shape (elongated hook) compared to the compact, irregular blob shapes seen in all normal reference images. This structural deviation is a strong indicator of an a
- `D5c_0174` L=1 direct=0.05→tool=0.95 rank=0.97 **FN_corrected** used_tool=True
  > The query image shows a significantly smaller and differently shaped object compared to the reference images, which display larger, complete structures. The texture tool's low periodicity score is consistent with natural
- `D5c_0035` L=0 direct=0.95→tool=0.10 rank=0.81 **FP_corrected** used_tool=True
  > The query image exhibits an irregular texture (low periodicity), which the tool notes is common in normal samples for this type of data. Visually, it matches the majority of the reference images in shape and texture patt
  ... and 4 more wins.

**LOSSES**:

- `D5c_0004` L=0 direct=0.02→tool=1.00 rank=0.94 **TN_lost_to_FP** used_tool=False
  > The query image lacks the primary object present in all reference images, appearing as a blank frame with minimal noise, which is a definitive anomaly.
- `D5c_0042` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=True
  > The query image exhibits distinct dark holes or voids within the object's structure, a feature completely absent in the normal reference images. The texture FFT tool's low periodicity score is consistent with the irregul
- `D5c_0109` L=1 direct=0.95→tool=0.05 rank=0.90 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicated low periodicity, but the disconfirm clause noted that irregular textures are normal for this type of data. Visual inspection confirms the query image's texture and appearance are consistent
- `D5c_0151` L=1 direct=0.95→tool=0.05 rank=0.92 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicated low periodicity, but the interpretation explicitly disconfirmed this as an anomaly signal for natural textures. Visually, the query image matches the style and content of the reference imag
- `D5c_0120` L=1 direct=0.95→tool=0.05 rank=0.96 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicates low periodicity (irregular texture), which the tool's interpretation confirms is typical for normal samples in this domain (e.g., tissue). The visual appearance of the query image matches t
- `D5c_0102` L=1 direct=0.95→tool=0.10 rank=0.91 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicated low periodicity, but the disconfirm clause noted that irregular textures are common in normal samples (e.g., tissue). Visual inspection confirms the query's texture is similar to the refere
- `D5c_0107` L=1 direct=0.95→tool=0.10 rank=0.99 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicates low periodicity (irregular texture), which the tool's interpretation explicitly states is common in normal cases and should not be used to flag an anomaly. Visually, the texture matches the
- `D5c_0145` L=1 direct=0.95→tool=0.10 rank=0.91 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicated low periodicity, but the disconfirm clause noted that irregular textures are common in normal samples like tissue. Visual comparison confirms the query's texture matches the reference image
  ... and 3 more losses.

### D5d  (wins 6, losses 8)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 6}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5d_0173` L=1 direct=0.02→tool=0.95 rank=0.57 **FN_corrected** used_tool=False
  > The query image contains a clear, dark, solid foreign object in the center of the lumen, which is a significant deviation from the normal mucosal appearance seen in the reference images. This is a structural anomaly, not
- `D5d_0135` L=1 direct=0.02→tool=0.95 rank=0.48 **FN_corrected** used_tool=True
  > The query image contains a distinct dark, raised lesion not present in the normal reference images. Although the texture FFT tool indicated irregular texture, the tool's interpretation clarifies that this is normal for t
- `D5d_0150` L=1 direct=0.02→tool=0.95 rank=0.59 **FN_corrected** used_tool=True
  > The query image clearly shows a raised polypoid lesion, which is a significant anomaly compared to the smooth mucosal folds seen in the normal reference images. The texture FFT tool indicated irregular texture, but its i
- `D5d_0128` L=1 direct=0.02→tool=0.95 rank=0.35 **FN_corrected** used_tool=True
  > The query image displays a clear polypoid lesion, which is a structural anomaly compared to the smooth mucosa in the reference images. Although the texture FFT tool indicated irregular texture, its disconfirm clause stat
- `D5d_0023` L=0 direct=0.98→tool=0.10 rank=0.39 **FP_corrected** used_tool=True
  > The texture FFT tool indicated irregular texture, but the disconfirm clause states this is normal for tissue. The yellow discoloration appears to be bile staining, a common non-anomalous finding, so the image is classifi
- `D5d_0045` L=0 direct=0.92→tool=0.05 rank=0.40 **FP_corrected** used_tool=True
  > The tool's low periodicity score indicates irregular texture, which the disconfirm clause notes is normal for tissue. Visually, the query image matches the normal references, so it is classified as normal.

**LOSSES**:

- `D5d_0069` L=0 direct=0.02→tool=0.95 rank=0.36 **TN_lost_to_FP** used_tool=True
  > The query image displays a clear polypoid mass, a structural anomaly not present in the normal reference images. The texture tool's low periodicity score was correctly identified as non-diagnostic for tissue anomalies pe
- `D5d_0112` L=1 direct=0.95→tool=0.05 rank=0.33 **TP_lost_to_FN** used_tool=True
  > The low periodicity score is expected for normal tissue texture and does not indicate an anomaly. Visual inspection confirms the image is consistent with the normal reference images, showing no pathological features.
- `D5d_0065` L=0 direct=0.02→tool=0.90 rank=0.32 **TN_lost_to_FP** used_tool=False
  > The query image clearly displays a polypoid lesion, a distinct raised mass on the mucosal surface, which is absent in the normal reference images showing only folds and smooth mucosa. This structural difference is a stro
- `D5d_0129` L=1 direct=0.98→tool=0.10 rank=0.31 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicated low periodicity, but the disconfirm clause states this is normal for tissue. Visually, the yellow patch is consistent with bile staining, a common and often normal finding, and the mucosal 
- `D5d_0146` L=1 direct=0.98→tool=0.10 rank=0.38 **TP_lost_to_FN** used_tool=True
  > The texture analysis indicates irregularity, but the tool's interpretation clarifies that this is normal for tissue. Visually, the query image shows a normal pyloric sphincter with some residue, which is not an anomaly.
- `D5d_0166` L=1 direct=0.98→tool=0.10 rank=0.47 **TP_lost_to_FN** used_tool=True
  > The query image displays normal mucosal folds and texture consistent with the normal reference images. The low periodicity score from the tool is expected for biological tissue and does not indicate an anomaly, as per th
- `D5d_0161` L=1 direct=0.98→tool=0.10 rank=0.51 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicated irregular texture, but the disconfirm clause states this is normal for tissue. The yellow patch appears to be bile staining, a common and non-anomalous finding in endoscopy, and the surroun
- `D5d_0093` L=1 direct=0.92→tool=0.10 rank=0.30 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicated irregularity, but the disconfirm clause states this is normal for tissue. The yellow discoloration is visually consistent with bile or fluid residue, a common non-anomalous finding, rather 

### D6  (wins 7, losses 15)

Win sample-types: {'FP_corrected': 7}
Loss sample-types: {'TP_lost_to_FN': 15}

**WINS** (item · direct→tool · rank · type · rationale):

- `D6_0063` L=0 direct=0.98→tool=0.05 rank=0.60 **FP_corrected** used_tool=True
  > The low periodicity score reflects the natural, irregular texture of the rural landscape, which is consistent with the reference images. The tool's disconfirm clause clarifies that this signal does not indicate an anomal
- `D6_0015` L=0 direct=0.98→tool=0.05 rank=0.62 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing typical rural landscape features without any apparent defects or anomalies.
- `D6_0000` L=0 direct=0.95→tool=0.05 rank=0.82 **FP_corrected** used_tool=True
  > The texture FFT tool indicated low periodicity, but the disconfirm clause clarified that irregular textures are normal for natural scenes like these fields. Visually, the query image is consistent with the normal referen
- `D6_0039` L=0 direct=0.95→tool=0.05 rank=0.85 **FP_corrected** used_tool=True
  > The texture FFT tool indicates low periodicity, which the interpretation confirms is normal for natural scenes like agricultural fields. The visual content of the query image is consistent with the normal reference image
- `D6_0017` L=0 direct=0.95→tool=0.05 rank=0.75 **FP_corrected** used_tool=True
  > The texture FFT tool indicates low periodicity, which the disconfirm clause clarifies is expected for natural aerial scenes. The query image visually aligns with the normal reference images, showing no obvious anomalies.
- `D6_0064` L=0 direct=0.95→tool=0.05 rank=0.39 **FP_corrected** used_tool=True
  > The texture FFT tool indicates low periodicity, which the interpretation confirms is normal for this type of scene (aerial view of a neighborhood). The visual content of the query image is consistent with the reference i
- `D6_0035` L=0 direct=0.98→tool=0.10 rank=0.64 **FP_corrected** used_tool=True
  > The texture FFT tool indicated low periodicity, but the disconfirm clause states this is normal for natural/irregular scenes. The visual difference (empty lot) appears to be a semantic/temporal variation rather than a te

**LOSSES**:

- `D6_0130` L=1 direct=0.98→tool=0.02 rank=0.54 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool confirmed the texture is irregular (low periodicity), which the tool's disconfirm clause states is normal for natural scenes. The query image visually matches the reference images, showing no anomali
- `D6_0151` L=1 direct=0.99→tool=0.05 rank=0.92 **TP_lost_to_FN** used_tool=True
  > The query image shows a natural, irregular landscape which is consistent with the low periodicity score. The tool's disconfirm clause states that irregular textures are normal for natural scenes, so the difference from t
- `D6_0111` L=1 direct=0.98→tool=0.05 rank=0.66 **TP_lost_to_FN** used_tool=True
  > The texture analysis confirms an irregular pattern typical of natural landscapes, and the disconfirm clause explicitly warns against flagging this as anomalous. Visual comparison with reference images shows consistent co
- `D6_0149` L=1 direct=0.98→tool=0.05 rank=0.55 **TP_lost_to_FN** used_tool=True
  > The low periodicity score reflects the natural, irregular texture of the vacant lot, which is consistent with the reference images and explicitly noted as normal in the tool's disconfirm clause. No anomaly is detected.
- `D6_0133` L=1 direct=0.98→tool=0.05 rank=0.82 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicates low periodicity, which the interpretation clarifies is normal for natural scenes like fields. The visual content of the query image is consistent with the normal reference images, showing a
- `D6_0110` L=1 direct=0.98→tool=0.05 rank=0.36 **TP_lost_to_FN** used_tool=True
  > The low periodicity score is consistent with the irregular nature of natural residential scenes, as confirmed by the tool's disconfirm clause. The query image visually matches the normal reference images in structure and
- `D6_0148` L=1 direct=0.98→tool=0.05 rank=0.66 **TP_lost_to_FN** used_tool=True
  > The low periodicity score indicates irregular texture, which the tool interpretation confirms is normal for aerial/natural scenes. The query image shows typical buildings and fields with no obvious anomalies.
- `D6_0136` L=1 direct=0.98→tool=0.05 rank=0.70 **TP_lost_to_FN** used_tool=True
  > The texture FFT tool indicates low periodicity, which the interpretation confirms is expected for natural scenes and does not indicate an anomaly. Visual inspection also shows no obvious defects compared to the reference
  ... and 7 more losses.

### D7  (wins 2, losses 1)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 1}
Loss sample-types: {'TP_lost_to_FN': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D7_0135` L=1 direct=0.02→tool=1.00 rank=0.97 **FN_corrected** used_tool=False
  > The query image depicts a horse-drawn carriage in a park, while all reference images show driving scenes from a vehicle's perspective. This is a fundamental scene mismatch, indicating a certain anomaly.
- `D7_0022` L=0 direct=0.95→tool=0.10 rank=0.21 **FP_corrected** used_tool=True
  > The texture FFT tool indicated low periodicity, but the disconfirm clause clarifies that irregular textures are normal for street scenes. The orange barrier is a common object and not a texture anomaly. Thus, the image i

**LOSSES**:

- `D7_0097` L=1 direct=0.95→tool=0.05 rank=0.91 **TP_lost_to_FN** used_tool=True
  > The low periodicity score reflects the natural, irregular texture of the road and vehicles, which is consistent with the reference images. The disconfirm clause in the tool output confirms that this signal does not indic

### D8  (wins 2, losses 3)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 1}
Loss sample-types: {'TP_lost_to_FN': 2, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D8_0072` L=0 direct=0.95→tool=0.10 rank=0.50 **FP_corrected** used_tool=True
  > The low periodicity score is expected for natural scenes with people and architectural elements. The query image shows a normal scene consistent with the reference images, with no detectable anomalies.
- `D8_0163` L=1 direct=0.05→tool=0.80 rank=0.50 **FN_corrected** used_tool=False
  > The query image contains a person standing on the grass in the foreground, which is a significant deviation from the reference images where people are on the paved walkway or near the building. This suggests an anomalous

**LOSSES**:

- `D8_0126` L=1 direct=0.95→tool=0.05 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The low periodicity score is expected for a natural scene with people and architecture. The visual content of the query image is consistent with the normal reference images, showing typical pedestrian activity in a publi
- `D8_0179` L=1 direct=0.95→tool=0.30 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The query image contains a red bag and a person sitting on the grass, which are not present in the reference images. While this could be an anomaly, it's also possible that such occurrences are normal in this setting. Wi
- `D8_0119` L=1 direct=0.95→tool=0.80 rank=0.50 **other** used_tool=False
  > The query image contains a person in a white hoodie performing an unusual action (jumping/dancing) on the left, which is not present in the reference images showing typical pedestrian behavior in the same location. The t

### D9  (wins 7, losses 10)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 7}

**WINS** (item · direct→tool · rank · type · rationale):

- `D9_0121` L=1 direct=0.01→tool=1.00 rank=0.58 **FN_corrected** used_tool=False
  > The query image is anomalous because it features a cherry label and dark red liquid, whereas all reference images consistently show a banana label and light-colored liquid. This represents a clear deviation from the esta
- `D9_0168` L=1 direct=0.01→tool=0.95 rank=0.73 **FN_corrected** used_tool=False
  > The query image has a different label (cherry vs banana/orange) and liquid color compared to all reference images, indicating a clear anomaly in product type.
- `D9_0057` L=0 direct=0.99→tool=0.10 rank=0.35 **FP_corrected** used_tool=True
  > The low periodicity score is expected for an object scene and the tool's disconfirm clause advises against flagging it as anomalous. Visually, the cable and connectors are structurally consistent with the references, dif
- `D9_0022` L=0 direct=0.99→tool=0.10 rank=0.28 **FP_corrected** used_tool=True
  > The low periodicity score is likely due to the wire and connectors disrupting the mesh pattern, which is expected. The disconfirm clause advises not to flag this as anomalous. The image structure matches the references, 
- `D9_0078` L=0 direct=0.99→tool=0.10 rank=0.11 **FP_corrected** used_tool=True
  > The low periodicity score is expected for this type of image with objects on a mesh, and the disconfirm clause advises against flagging it as anomalous. The visual content (single yellow wire) is a plausible variation wi
- `D9_0039` L=0 direct=0.98→tool=0.10 rank=0.05 **FP_corrected** used_tool=False
  > The query image is visually consistent with the reference images, showing a standard arrangement of healthy food items in a lunchbox. No anomalies are detected.
- `D9_0079` L=0 direct=0.98→tool=0.10 rank=0.16 **FP_corrected** used_tool=False
  > The query image contains the same types of hardware components as the reference images, just arranged differently. There are no obvious defects, missing parts, or foreign objects visible. The variation in arrangement is 

**LOSSES**:

- `D9_0047` L=0 direct=0.02→tool=1.00 rank=0.13 **TN_lost_to_FP** used_tool=False
  > The query image displays a bottle with a cherry label and red liquid, whereas all reference images show bottles with banana labels and light-colored liquid. This represents a clear deviation from the normal class.
- `D9_0041` L=0 direct=0.02→tool=1.00 rank=0.79 **TN_lost_to_FP** used_tool=False
  > The query image displays a bottle with a cherry label and dark red liquid, whereas all reference images show bottles with banana or orange labels and light-colored liquids. This significant deviation in both label iconog
- `D9_0032` L=0 direct=0.02→tool=1.00 rank=0.07 **TN_lost_to_FP** used_tool=False
  > The query image displays a bottle with red liquid and a cherry label, whereas all reference images show bottles with white liquid and a banana label. This significant difference in product appearance and labeling indicat
- `D9_0100` L=1 direct=0.99→tool=0.05 rank=0.41 **TP_lost_to_FN** used_tool=True
  > The query image visually matches the normal reference images (single yellow wire on mesh). The tool's low periodicity score is explicitly disconfirmed by its own interpretation for this type of scene, indicating the text
- `D9_0090` L=1 direct=0.98→tool=0.05 rank=0.03 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard arrangement of food items in a lunchbox with no apparent defects or anomalies.
- `D9_0129` L=1 direct=0.98→tool=0.05 rank=0.04 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard arrangement of healthy food items in a lunchbox. No anomalies are detected.
- `D9_0146` L=1 direct=0.95→tool=0.05 rank=0.10 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard arrangement of healthy food items in a lunchbox without any apparent anomalies.
- `D9_0176` L=1 direct=0.99→tool=0.10 rank=0.31 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard single jumper wire setup. No obvious anomalies are present.
  ... and 2 more losses.

---

## tool_zoom_bbox  (58 wins, 110 losses, net flips -40 on n=467)

### D1  (wins 7, losses 3)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 1, 'TP_lost_to_FN': 1, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D1_0174` L=1 direct=0.02→tool=0.95 rank=0.15 **FN_corrected** used_tool=False
  > The query image displays a flat-packaged component on a PCB with different trace and pad geometry compared to the cylindrical components and PCB layout in the reference images, indicating a significant deviation from the
- `D1_0038` L=0 direct=0.98→tool=0.05 rank=0.26 **FP_corrected** used_tool=True
  > The query image displays the 'actavis' logo and '500' imprint clearly, matching three of the four normal reference images. The zoomed inspection revealed no printing defects or anomalies. The single reference image witho
- `D1_0064` L=0 direct=0.98→tool=0.05 rank=0.24 **FP_corrected** used_tool=True
  > The query image shows a capsule with 'actavis' and '500' imprints, matching the normal reference images. Close inspection of both halves revealed no defects, scratches, or other anomalies. The capsule appears to be in no
- `D1_0114` L=1 direct=0.02→tool=0.95 rank=0.19 **FN_corrected** used_tool=False
  > The query image has yellow bristles, which is a clear deviation from the blue and red bristles seen in the reference images, indicating an anomaly.
- `D1_0084` L=0 direct=0.95→tool=0.05 rank=0.02 **FP_corrected** used_tool=False
  > The query image exhibits the same speckled pattern and texture as the normal reference images, with no detectable anomalies.
- `D1_0088` L=0 direct=0.95→tool=0.10 rank=0.29 **FP_corrected** used_tool=False
  > The query image is visually consistent with the provided normal reference images, showing a standard transistor mounted on a PCB without any apparent anomalies.
- `D1_0009` L=0 direct=0.95→tool=0.10 rank=0.13 **FP_corrected** used_tool=True
  > The blue conductor's strand pattern and condition appear normal, consistent with the reference images. The observed variations are attributed to lighting and reflection rather than a defect.

**LOSSES**:

- `D1_0008` L=0 direct=0.02→tool=0.95 rank=0.12 **TN_lost_to_FP** used_tool=False
  > The query image displays a brush with yellow bristles, whereas all normal reference images show brushes with either blue or red bristles. This significant color difference indicates an anomaly.
- `D1_0179` L=1 direct=0.95→tool=0.10 rank=0.54 **TP_lost_to_FN** used_tool=True
  > Both zoomed regions show normal surface texture and clean edges consistent with reference images. No defects like cracks, chips, or irregularities were observed, suggesting the query image is normal.
- `D1_0019` L=0 direct=0.02→tool=0.15 rank=0.36 **other** used_tool=True
  > The dark, textured cap area is a normal anatomical feature of hazelnuts, consistent with variations seen in reference images. No clear defect or anomaly detected.

→ RULE candidate: on D1, tool tends to correctly down-weight FPs when subspacead rank ∈ [0.02, 0.29].

### D10  (wins 3, losses 5)

Win sample-types: {'FP_corrected': 2, 'FN_corrected': 1}
Loss sample-types: {'TP_lost_to_FN': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D10_0156` L=1 direct=0.01→tool=0.95 rank=0.51 **FN_corrected** used_tool=True
  > The query image shows an HC-SR04 sensor where the transducer elements have a smooth, solid surface, unlike the distinct mesh grille visible on the normal reference images. This structural difference indicates the query i
- `D10_0076` L=0 direct=0.98→tool=0.05 rank=0.12 **FP_corrected** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard HC-SR04 module with all expected components and layout. No anomalies are detected.
- `D10_0002` L=0 direct=0.95→tool=0.05 rank=0.07 **FP_corrected** used_tool=True
  > The detailed inspection of the top-left candle revealed no anomalies; the surface and wick appear consistent with the normal reference images. The overall arrangement and appearance of the candles in the query image matc

**LOSSES**:

- `D10_0140` L=1 direct=0.98→tool=0.05 rank=0.30 **TP_lost_to_FN** used_tool=True
  > The suspected anomaly is a reflection on the PCB surface, not a physical defect. The module appears structurally intact and consistent with the reference images.
- `D10_0106` L=1 direct=0.98→tool=0.05 rank=0.62 **TP_lost_to_FN** used_tool=True
  > After zooming into the suspected area and the edge, no defects were found. The surface texture and edges appear normal and consistent with the reference images. The initial 'spot' was likely an artifact.
- `D10_0153` L=1 direct=0.98→tool=0.10 rank=0.62 **TP_lost_to_FN** used_tool=True
  > The zoomed inspection of the suspected area revealed normal surface texture and no physical defects, indicating the initial observation was likely a lighting effect.
- `D10_0136` L=1 direct=0.98→tool=0.10 rank=0.23 **TP_lost_to_FN** used_tool=True
  > The white smudges observed are likely benign flux residue or lighting artifacts, consistent with the disconfirm clause. The component placement and board structure match the reference images, indicating the query is norm
- `D10_0158` L=1 direct=0.98→tool=0.10 rank=0.48 **TP_lost_to_FN** used_tool=True
  > The zoomed-in view of the suspected area reveals a normal, uniform surface texture, indicating the initial 'spot' was not a defect. Therefore, the query image is classified as normal.

### D2  (wins 6, losses 12)

Win sample-types: {'FP_corrected': 1, 'FN_corrected': 5}
Loss sample-types: {'TN_lost_to_FP': 5, 'TP_lost_to_FN': 6, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D2_0146` L=1 direct=0.01→tool=0.95 rank=0.29 **FN_corrected** used_tool=False
  > The query image displays a distinct orange 'Golden Leaf' cigarette pack, whereas all reference images show different brands ('Tianzi' and 'Jinmen') with different colors and designs. This clear mismatch in brand and visu
- `D2_0092` L=1 direct=0.01→tool=0.95 rank=0.63 **FN_corrected** used_tool=True
  > The query image displays a plastic straw wrapper attached to the front of the carton, a feature not present in any of the normal reference images. This constitutes a clear packaging anomaly.
- `D2_0163` L=1 direct=0.01→tool=0.95 rank=0.61 **FN_corrected** used_tool=True
  > The query image shows a visible tear/damage at the top-left corner of the box, which is a clear anomaly compared to the intact packaging in the reference images.
- `D2_0095` L=1 direct=0.02→tool=0.95 rank=0.86 **FN_corrected** used_tool=True
  > The query image shows a bottle filled with dark liquid without the white label seen in all reference images, which is a clear anomaly.
- `D2_0037` L=0 direct=0.98→tool=0.10 rank=0.19 **FP_corrected** used_tool=True
  > Despite failed zoom attempts, the query image shows a normal-looking package with no obvious defects. The low score reflects minor uncertainty due to tool issues, but the visual evidence suggests normality.
- `D2_0145` L=1 direct=0.02→tool=0.90 rank=0.71 **FN_corrected** used_tool=False
  > The query image's warning label text differs from at least one of the reference images, indicating an anomaly in the product packaging or labeling.

**LOSSES**:

- `D2_0056` L=0 direct=0.01→tool=1.00 rank=0.05 **TN_lost_to_FP** used_tool=False
  > The query image displays a significantly different packaging design (blue background, different text layout) compared to the consistent white-background design in all normal reference images, indicating a clear anomaly.
- `D2_0080` L=0 direct=0.02→tool=1.00 rank=0.02 **TN_lost_to_FP** used_tool=False
  > The query image displays the back of the product packaging, whereas all reference images display the front. This difference in the presented side of the object is a definitive anomaly.
- `D2_0087` L=0 direct=0.01→tool=0.95 rank=0.08 **TN_lost_to_FP** used_tool=True
  > Despite failed zoom attempts, the query image visibly shows the cigarette pack placed upside down relative to the normal reference images, which is a definitive anomaly in orientation.
- `D2_0083` L=0 direct=0.02→tool=0.95 rank=0.09 **TN_lost_to_FP** used_tool=False
  > The query image displays the back of the bottle with a barcode and text, while all reference images show the front with the main character logo. This represents a clear anomaly in the object's presentation relative to th
- `D2_0169` L=1 direct=0.98→tool=0.05 rank=0.83 **TP_lost_to_FN** used_tool=True
  > The query image shows the back of the cigarette pack, which is a normal variation from the front shown in references. The difference in logo and text is expected for different sides of the same product.
- `D2_0167` L=1 direct=0.98→tool=0.05 rank=0.18 **TP_lost_to_FN** used_tool=True
  > Despite failed zoom attempts, a direct visual comparison between the query and reference images shows no discernible differences or defects. The bottle's label, shape, and contents appear normal.
- `D2_0029` L=0 direct=0.01→tool=0.90 rank=0.51 **TN_lost_to_FP** used_tool=True
  > The query image displays the back of the bottle, whereas all reference images display the front. This consistent difference in the object's orientation/presentation across the dataset is treated as an anomaly, as the too
- `D2_0133` L=1 direct=0.98→tool=0.10 rank=0.08 **TP_lost_to_FN** used_tool=False
  > The query image matches the normal reference images in terms of packaging design, text, and product appearance. No defects or anomalies are detected.
  ... and 4 more losses.

### D4  (wins 2, losses 7)

Win sample-types: {'FN_corrected': 1, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 5}

**WINS** (item · direct→tool · rank · type · rationale):

- `D4_0105` L=1 direct=0.05→tool=0.95 rank=0.06 **FN_corrected** used_tool=False
  > The query image exhibits a significant shadow and a darker, potentially different texture compared to the uniformly lit and textured normal reference images, indicating a clear anomaly.
- `D4_0110` L=1 direct=0.05→tool=0.20 rank=0.70 **other** used_tool=True
  > The dark spot in the query image is consistent with the natural texture variations and minor imperfections seen in the normal reference images. It does not appear to be a significant anomaly.

**LOSSES**:

- `D4_0106` L=1 direct=0.95→tool=0.05 rank=0.49 **TP_lost_to_FN** used_tool=True
  > The zoomed inspection reveals a normal surface texture consistent with the reference images. The apparent anomaly in the full view was caused by lighting/shadow, which is a benign cue and not a defect.
- `D4_0126` L=1 direct=0.95→tool=0.10 rank=0.63 **TP_lost_to_FN** used_tool=False
  > The query image displays a surface texture with small dark spots that are consistent in appearance and distribution with the provided normal reference images. No obvious defects, unusual patterns, or significant deviatio
- `D4_0026` L=0 direct=0.05→tool=0.90 rank=0.28 **TN_lost_to_FP** used_tool=True
  > The query image contains a distinct dark spot that is not present in the normal reference images, indicating a localized defect or anomaly.
- `D4_0155` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The query image's texture and spot distribution closely match the first three normal reference images. The prominent spot in the query does not resemble the larger, distinct anomaly seen in the fourth reference image. Th
- `D4_0130` L=1 direct=0.95→tool=0.10 rank=0.57 **TP_lost_to_FN** used_tool=True
  > The zoomed region reveals a crack, which is also present in one of the normal reference images. Since the defect type (crack) is represented in the normal set, the query image is considered normal.
- `D4_0128` L=1 direct=0.95→tool=0.20 rank=0.42 **TP_lost_to_FN** used_tool=True
  > The query image shows a concrete surface with typical imperfections (small pits, speckles, minor irregularities) that are consistent with the normal reference images. The tool zoom was unsuccessful due to coordinate misa
- `D4_0065` L=0 direct=0.05→tool=0.70 rank=0.39 **TN_lost_to_FP** used_tool=True
  > The vertical line observed in the query image is likely a defect, as it is not present in the normal reference images and does not appear to be a benign visual cue.

### D5  (wins 2, losses 17)

Win sample-types: {'FN_corrected': 1, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 5, 'TP_lost_to_FN': 6, 'other': 6}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5_0179` L=1 direct=0.05→tool=0.85 rank=0.27 **FN_corrected** used_tool=True
  > Despite the tool misalignment, the query image displays a lesion with marked color variegation (black center, brown rim) and irregular borders, contrasting sharply with the uniform, symmetric lesions in the reference ima
- `D5_0104` L=1 direct=0.05→tool=0.20 rank=0.42 **other** used_tool=True
  > The query lesion is faint and relatively uniform, lacking the distinct irregularities or strong pigmentation seen in some reference images. The zoom was unhelpful. It appears consistent with a benign, less pigmented lesi

**LOSSES**:

- `D5_0032` L=0 direct=0.05→tool=0.95 rank=0.87 **TN_lost_to_FP** used_tool=False
  > The query lesion is pink and lacks the brown pigmentation seen in all reference images, indicating a significant deviation from the normal class.
- `D5_0030` L=0 direct=0.05→tool=0.95 rank=0.21 **TN_lost_to_FP** used_tool=True
  > The query image shows a diffuse, reddish-purple lesion that lacks the characteristic brown pigment network and well-defined borders of the normal nevi in the reference images, indicating a significant anomaly.
- `D5_0061` L=0 direct=0.05→tool=0.92 rank=0.22 **TN_lost_to_FP** used_tool=True
  > The lesion exhibits significant asymmetry, irregular borders, and color variegation with an atypical pigment network, distinguishing it clearly from the benign, uniform reference lesions.
- `D5_0155` L=1 direct=0.95→tool=0.10 rank=0.65 **TP_lost_to_FN** used_tool=False
  > The query image shows a pigmented lesion that appears consistent with the normal reference images in terms of color uniformity and border characteristics. There are no strong indicators of anomaly such as significant asy
- `D5_0117` L=1 direct=0.95→tool=0.10 rank=0.72 **TP_lost_to_FN** used_tool=True
  > The zoomed view shows a regular reticular pigment network, which is a characteristic feature of benign melanocytic nevi. This pattern is consistent with the 'normal' reference images, particularly the last one, indicatin
- `D5_0115` L=1 direct=0.95→tool=0.10 rank=0.57 **TP_lost_to_FN** used_tool=True
  > The query lesion exhibits a regular pigment network and well-defined borders, characteristic of a benign nevus, contrasting with the irregular features seen in the reference images. The zoomed view confirms the absence o
- `D5_0089` L=0 direct=0.05→tool=0.85 rank=0.42 **TN_lost_to_FP** used_tool=True
  > The query image displays a lesion with marked color variegation (dark black center, lighter brown periphery) which is distinct from the more uniform pigmentation seen in the normal reference images. This asymmetry in col
- `D5_0017` L=0 direct=0.05→tool=0.85 rank=0.00 **TN_lost_to_FP** used_tool=True
  > The query image displays a distinctly brown, pigmented lesion with a more defined, albeit slightly irregular, border. In contrast, the normal reference images show pinkish, less pigmented, and more diffuse lesions. This 
  ... and 9 more losses.

### D5b  (wins 5, losses 8)

Win sample-types: {'FP_corrected': 5}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 4, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5b_0045` L=0 direct=0.98→tool=0.10 rank=0.31 **FP_corrected** used_tool=False
  > The query image appears to be a normal brain MRI slice showing typical anatomical structures (lateral ventricles, cortical gyri) without obvious pathological features. The appearance is consistent with normal brain anato
- `D5b_0031` L=0 direct=0.98→tool=0.10 rank=0.51 **FP_corrected** used_tool=False
  > The query image displays normal brain anatomy consistent with the reference images, with no visible anomalies such as lesions, masses, or structural deformities.
- `D5b_0024` L=0 direct=0.98→tool=0.10 rank=0.44 **FP_corrected** used_tool=True
  > The high-resolution crop reveals normal tissue texture, suggesting the dark region in the overview is a benign anatomical feature or artifact rather than a defect.
- `D5b_0067` L=0 direct=0.98→tool=0.10 rank=0.53 **FP_corrected** used_tool=False
  > The query image displays normal brain anatomy with no visible anomalies such as tumors, lesions, or hemorrhages when compared to the general structure of the reference images.
- `D5b_0058` L=0 direct=0.95→tool=0.10 rank=0.52 **FP_corrected** used_tool=False
  > The query image displays typical brain anatomy consistent with the normal reference images, showing no apparent anomalies such as tumors, strokes, or structural deformities.

**LOSSES**:

- `D5b_0072` L=0 direct=0.05→tool=0.95 rank=0.71 **TN_lost_to_FP** used_tool=True
  > The query image is an anomalous, severely cropped, and low-quality fragment compared to the complete, high-quality reference scans, indicating a data processing error.
- `D5b_0002` L=0 direct=0.02→tool=0.90 rank=0.34 **TN_lost_to_FP** used_tool=True
  > The query image displays significantly enlarged ventricles (ventriculomegaly) compared to the reference images, which is a clear anatomical anomaly indicative of conditions like hydrocephalus or atrophy. The surrounding 
- `D5b_0066` L=0 direct=0.02→tool=0.90 rank=0.55 **TN_lost_to_FP** used_tool=True
  > The query image displays a sagittal brain slice, whereas all reference images are axial slices. This fundamental difference in anatomical orientation makes the query image inconsistent with the normal reference set, indi
- `D5b_0156` L=1 direct=0.98→tool=0.10 rank=0.56 **TP_lost_to_FN** used_tool=False
  > The query image displays a brain MRI with typical gyral patterns and symmetry comparable to the provided normal reference images. No distinct hyperintensities, masses, or structural deformities are immediately apparent t
- `D5b_0117` L=1 direct=0.98→tool=0.10 rank=0.53 **TP_lost_to_FN** used_tool=True
  > The zoomed-in region displays normal brain surface texture with no evidence of a localized defect. The initial anomaly signal was likely a visual artifact, and the high-resolution inspection confirms normalcy.
- `D5b_0149` L=1 direct=0.98→tool=0.10 rank=0.72 **TP_lost_to_FN** used_tool=False
  > The query image displays normal brain anatomy consistent with the first reference image, showing no visible signs of anomalies such as tumors, hemorrhages, or structural deformities.
- `D5b_0122` L=1 direct=0.98→tool=0.10 rank=0.60 **TP_lost_to_FN** used_tool=False
  > The query image displays normal brain anatomy without any visible anomalies such as lesions, hemorrhages, or abnormal signal intensities that would indicate pathology.
- `D5b_0059` L=0 direct=0.02→tool=0.15 rank=0.50 **other** used_tool=True
  > The query image appears to be a different anatomical slice level (lower brain/cerebellum region) compared to the reference images (higher cortical slices). No clear pathological anomalies are visible in the zoomed region

### D5c  (wins 9, losses 9)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 4}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 5, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5c_0131` L=1 direct=0.02→tool=0.95 rank=0.90 **FN_corrected** used_tool=False
  > The query image contains a fundamentally different object (small oval) compared to the consistent complex shape seen in all reference images, indicating a clear anomaly.
- `D5c_0165` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=True
  > The query image contains a prominent dark hole/void within the object, which is not present in any of the normal reference images, indicating a clear anomaly.
- `D5c_0100` L=1 direct=0.05→tool=0.95 rank=0.79 **FN_corrected** used_tool=False
  > The query image exhibits a fundamentally different shape (elongated and hook-like) compared to the compact, rounded shapes seen in all normal reference images, indicating a clear anomaly.
- `D5c_0174` L=1 direct=0.05→tool=0.95 rank=0.97 **FN_corrected** used_tool=False
  > The query image contains a tiny, isolated object that is drastically different in size and morphology compared to the larger, organ-like structures in all reference images, indicating a clear anomaly.
- `D5c_0035` L=0 direct=0.95→tool=0.10 rank=0.81 **FP_corrected** used_tool=False
  > The query image displays a small, oval-shaped object similar to three of the four normal reference images. The one differing reference image (image 2) appears to be an outlier or a different class, but the query matches 
- `D5c_0038` L=0 direct=0.95→tool=0.10 rank=0.89 **FP_corrected** used_tool=True
  > The query image's texture and the presence of a hole are consistent with the variations seen in the normal reference images, particularly image 2. No distinct localized defects were found upon zooming.
- `D5c_0003` L=0 direct=0.95→tool=0.10 rank=0.97 **FP_corrected** used_tool=True
  > The zoomed region shows a consistent texture matching the normal references with no localized defects or anomalies detected.
- `D5c_0070` L=0 direct=0.95→tool=0.10 rank=0.91 **FP_corrected** used_tool=True
  > The zoomed-in view reveals a consistent, grainy texture without any localized defects. This matches the appearance of the normal reference images, indicating the query is likely normal.
  ... and 1 more wins.

**LOSSES**:

- `D5c_0004` L=0 direct=0.02→tool=0.95 rank=0.94 **TN_lost_to_FP** used_tool=False
  > The query image contains a tiny, barely visible object, which is drastically different from the large, clear objects seen in all normal reference images, indicating a severe anomaly.
- `D5c_0042` L=0 direct=0.02→tool=0.95 rank=0.88 **TN_lost_to_FP** used_tool=True
  > The query image contains large internal voids not present in the reference images, indicating a significant structural anomaly.
- `D5c_0061` L=0 direct=0.02→tool=0.95 rank=0.84 **TN_lost_to_FP** used_tool=False
  > The query image exhibits a complex, fragmented structure with internal voids that is morphologically inconsistent with the solid, continuous shapes seen in all normal reference images.
- `D5c_0120` L=1 direct=0.95→tool=0.10 rank=0.96 **TP_lost_to_FN** used_tool=True
  > The query image shows an object with a texture and dark patches that are also present in one of the normal reference images (the last one). The differences in shape and fragmentation seen in other references are likely v
- `D5c_0107` L=1 direct=0.95→tool=0.10 rank=0.99 **TP_lost_to_FN** used_tool=True
  > The zoomed view reveals a consistent granular texture without any distinct defects, holes, or irregular boundaries. This texture matches the appearance of the normal reference images, suggesting the query image is also n
- `D5c_0151` L=1 direct=0.95→tool=0.10 rank=0.92 **TP_lost_to_FN** used_tool=True
  > The query object exhibits a consistent texture and solid structure similar to the reference images, lacking the significant fragmentation or holes seen in some references. The small detached speck is likely minor noise o
- `D5c_0170` L=1 direct=0.95→tool=0.10 rank=0.97 **TP_lost_to_FN** used_tool=True
  > Despite failed zoom attempts, the query object's shape and texture appear consistent with the smaller, intact objects in the normal reference set. It lacks the fragmentation or internal voids seen in the more complex ref
- `D5c_0145` L=1 direct=0.95→tool=0.15 rank=0.91 **TP_lost_to_FN** used_tool=True
  > The query object's texture and general appearance are consistent with the normal reference images. No distinct anomalies like unexpected voids, breaks, or foreign textures are visible. The zoom tool was unreliable, but t
  ... and 1 more losses.

### D5d  (wins 6, losses 10)

Win sample-types: {'FP_corrected': 4, 'FN_corrected': 2}
Loss sample-types: {'TP_lost_to_FN': 7, 'other': 3}

**WINS** (item · direct→tool · rank · type · rationale):

- `D5d_0135` L=1 direct=0.02→tool=0.95 rank=0.48 **FN_corrected** used_tool=True
  > The query image displays a prominent dark, raised lesion (likely a polyp) in the center, which is a clear deviation from the healthy, smooth mucosal folds seen in the normal reference images. Despite the failed zoom atte
- `D5d_0128` L=1 direct=0.02→tool=0.95 rank=0.35 **FN_corrected** used_tool=True
  > The query image displays a prominent, raised, lobulated mass (likely a polyp) that is not present in any of the normal reference images. This is a clear visual anomaly.
- `D5d_0023` L=0 direct=0.98→tool=0.10 rank=0.39 **FP_corrected** used_tool=True
  > The close-up inspection reveals normal mucosal texture without pathological defects; the initial yellow patch is likely benign staining or an artifact.
- `D5d_0045` L=0 direct=0.92→tool=0.05 rank=0.40 **FP_corrected** used_tool=False
  > The query image shows healthy, smooth mucosa with normal anatomical folds and no visible lesions, inflammation, or foreign bodies, consistent with the normal reference images.
- `D5d_0044` L=0 direct=0.95→tool=0.10 rank=0.34 **FP_corrected** used_tool=True
  > The apparent anomaly is an artifact caused by the endoscope tip pressing against the mucosa, not a pathological defect. The tissue itself appears normal.
- `D5d_0071` L=0 direct=0.95→tool=0.15 rank=0.47 **FP_corrected** used_tool=True
  > The zoomed regions reveal normal mucosal texture without localized defects. The yellow discoloration in the overview is likely a benign superficial artifact (e.g., bile staining) rather than a pathological anomaly, consi

**LOSSES**:

- `D5d_0146` L=1 direct=0.98→tool=0.05 rank=0.38 **TP_lost_to_FN** used_tool=True
  > The zoomed region confirms the presence of standard endoscopy system overlays (text, diagram) which are also present in the normal reference images. The underlying tissue texture appears normal with no signs of lesions, 
- `D5d_0129` L=1 direct=0.98→tool=0.10 rank=0.31 **TP_lost_to_FN** used_tool=True
  > The apparent anomaly in the query image is identified as specular reflection (lighting artifact) on normal mucosal tissue, confirmed by the zoomed view showing smooth texture without defects.
- `D5d_0154` L=1 direct=0.98→tool=0.10 rank=0.38 **TP_lost_to_FN** used_tool=False
  > The query image shows normal mucosal tissue with typical endoscopic artifacts (text, reflections) and residue, similar to the provided normal reference images. No distinct pathological features are observed.
- `D5d_0161` L=1 direct=0.98→tool=0.10 rank=0.51 **TP_lost_to_FN** used_tool=True
  > The zoomed region reveals a healthy mucosal surface with normal specular reflections. The yellow discoloration is consistent with benign bile staining seen in reference images, not a tissue defect.
- `D5d_0112` L=1 direct=0.95→tool=0.10 rank=0.33 **TP_lost_to_FN** used_tool=False
  > The query image shows normal colonic mucosa with typical features including smooth pink tissue, visible vascular patterns, and some yellowish residue which is common in endoscopic images. No obvious polyps, ulcers, bleed
- `D5d_0132` L=1 direct=0.95→tool=0.10 rank=0.43 **TP_lost_to_FN** used_tool=True
  > The observed 'anomaly' is identified as chromoendoscopy dye (blue staining) and air bubbles, which are procedural artifacts rather than pathological defects. The underlying tissue texture appears normal.
- `D5d_0166` L=1 direct=0.98→tool=0.15 rank=0.47 **TP_lost_to_FN** used_tool=True
  > The zoomed region shows normal mucosal texture with minor reflections/debris, not a distinct pathological defect. The yellowish area in the full view is likely benign residue (bile/stool). No clear anomaly is detected co
- `D5d_0111` L=1 direct=0.98→tool=0.65 rank=0.43 **other** used_tool=True
  > The query image displays scattered dark specks around the central opening, a feature not present in the provided normal reference images, indicating a potential anomaly despite the tool's misalignment.
  ... and 2 more losses.

### D6  (wins 5, losses 17)

Win sample-types: {'FP_corrected': 5}
Loss sample-types: {'TN_lost_to_FP': 2, 'TP_lost_to_FN': 14, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D6_0063` L=0 direct=0.98→tool=0.10 rank=0.60 **FP_corrected** used_tool=True
  > The zoomed-in view reveals a standard rural property with buildings and vehicles. No anomalous defects or foreign objects are present; the scene is consistent with normal variations in such imagery.
- `D6_0015` L=0 direct=0.98→tool=0.10 rank=0.62 **FP_corrected** used_tool=True
  > Both zoomed regions show normal rural features (fields, pond, paths) with no detectable anomalies. The query image appears consistent with the normal reference images.
- `D6_0000` L=0 direct=0.95→tool=0.10 rank=0.82 **FP_corrected** used_tool=True
  > Inspection of multiple high-resolution crops revealed only normal agricultural textures and field boundaries. No defects or anomalies were detected.
- `D6_0017` L=0 direct=0.95→tool=0.10 rank=0.75 **FP_corrected** used_tool=False
  > The query image shows a typical suburban landscape with houses, roads, and commercial buildings that aligns well with the normal reference images. No obvious defects, intrusions, or structural anomalies are visible at th
- `D6_0039` L=0 direct=0.95→tool=0.10 rank=0.85 **FP_corrected** used_tool=True
  > The structure in the bottom right corner appears to be a normal small building/shed surrounded by trees, which is typical for rural areas. No obvious defects or anomalies detected.

**LOSSES**:

- `D6_0144` L=1 direct=1.00→tool=0.05 rank=0.98 **TP_lost_to_FN** used_tool=True
  > The zoomed region displays a standard residential neighborhood consistent with the normal reference images. No defects or anomalies are visible in the detailed view.
- `D6_0016` L=0 direct=0.02→tool=0.95 rank=0.69 **TN_lost_to_FP** used_tool=True
  > The query image contains a distinct cluster of buildings and trees in the bottom-left corner, which is absent in the normal reference images showing only the field. This structural difference constitutes a clear anomaly.
- `D6_0110` L=1 direct=0.98→tool=0.05 rank=0.36 **TP_lost_to_FN** used_tool=True
  > Both zoomed regions show normal suburban features with no defects or anomalies. The image appears consistent with the reference images.
- `D6_0116` L=1 direct=0.99→tool=0.10 rank=0.70 **TP_lost_to_FN** used_tool=True
  > The zoomed region reveals a normal residential area consistent with the reference images. The apparent anomaly in the full view is likely a different type of land use (e.g., undeveloped land or construction) rather than 
- `D6_0032` L=0 direct=0.02→tool=0.90 rank=0.53 **TN_lost_to_FP** used_tool=True
  > The pond in the query image is markedly darker and appears to have a different water level or composition compared to the reference images, which show a greener, healthier-looking pond. This significant visual difference
- `D6_0133` L=1 direct=0.98→tool=0.10 rank=0.82 **TP_lost_to_FN** used_tool=True
  > The zoomed region shows normal agricultural field texture without any localized defects. The apparent striping is consistent with normal field patterns, not an anomaly.
- `D6_0113` L=1 direct=0.98→tool=0.10 rank=0.81 **TP_lost_to_FN** used_tool=True
  > The zoomed inspection reveals normal forest texture without localized anomalies. The overall color difference is likely a benign environmental factor (season/lighting) rather than a defect.
- `D6_0123` L=1 direct=0.98→tool=0.10 rank=0.74 **TP_lost_to_FN** used_tool=True
  > The zoomed region shows a typical building complex with no visible anomalies; all features align with normal infrastructure and natural surroundings.
  ... and 9 more losses.

### D7  (wins 2, losses 2)

Win sample-types: {'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 2}

**WINS** (item · direct→tool · rank · type · rationale):

- `D7_0135` L=1 direct=0.02→tool=1.00 rank=0.97 **FN_corrected** used_tool=False
  > The query image contains a horse-drawn carriage and a large statue in a park setting, which is fundamentally different from the car-centric urban street scenes in the reference images.
- `D7_0159` L=1 direct=0.02→tool=0.95 rank=0.87 **FN_corrected** used_tool=False
  > The query image depicts a car towing a trailer in a scenic, non-urban setting, which is fundamentally different from the dashcam-style urban/suburban driving scenes in the reference images. This significant difference in

**LOSSES**:

- `D7_0086` L=0 direct=0.02→tool=0.95 rank=0.67 **TN_lost_to_FP** used_tool=False
  > The query image depicts a night-time highway, whereas all reference images show daytime city streets. This fundamental difference in time of day and road type makes the query image anomalous relative to the provided norm
- `D7_0061` L=0 direct=0.02→tool=0.90 rank=0.67 **TN_lost_to_FP** used_tool=True
  > The query image contains a bright green taxi, which is an anomalous color compared to the standard yellow taxi seen in the reference images and typical taxi colors. This color deviation is a clear visual anomaly.

### D8  (wins 4, losses 10)

Win sample-types: {'FN_corrected': 3, 'other': 1}
Loss sample-types: {'TN_lost_to_FP': 5, 'TP_lost_to_FN': 4, 'other': 1}

**WINS** (item · direct→tool · rank · type · rationale):

- `D8_0107` L=1 direct=0.02→tool=0.95 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a uniformed security or police officer walking in the foreground, which is a distinct anomaly compared to the reference images that exclusively show civilians. The tool failures do not negate thi
- `D8_0175` L=1 direct=0.02→tool=0.95 rank=0.50 **FN_corrected** used_tool=True
  > The query image is anomalous because it features a uniformed officer, whereas the normal reference images exclusively show civilians. This is a distinct and significant difference in the scene's content.
- `D8_0112` L=1 direct=0.02→tool=0.85 rank=0.50 **FN_corrected** used_tool=True
  > The query image contains a group of people in matching uniforms, which is a significant deviation from the casual, varied attire of individuals seen in the normal reference images. This suggests an anomalous event or pre
- `D8_0177` L=1 direct=0.02→tool=0.20 rank=0.50 **other** used_tool=True
  > The uniformed person appears to be a security officer or police, which is a normal presence in public transit areas. The scene composition and lighting are consistent with the reference images, suggesting no significant 

**LOSSES**:

- `D8_0014` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=False
  > The query image contains a person in a distinct uniform walking in the center, whereas the reference images only show civilians in casual wear. This presence of a uniformed individual is a clear deviation from the normal
- `D8_0009` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed officer in the central foreground, which is a distinct deviation from the reference images showing only civilians. This content difference constitutes an anomaly.
- `D8_0050` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed security or police officer walking in the foreground, which is a distinct anomaly compared to the reference images that exclusively show civilians in casual attire.
- `D8_0065` L=0 direct=0.02→tool=0.95 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image is anomalous because it features a uniformed officer in the foreground, a distinct element not present in any of the normal reference images which only contain civilians.
- `D8_0020` L=0 direct=0.02→tool=0.90 rank=0.50 **TN_lost_to_FP** used_tool=True
  > The query image contains a uniformed individual (likely security or police) walking in the foreground, which is a distinct deviation from the reference images that only show civilians. This presence of an authority figur
- `D8_0133` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=False
  > The query image appears consistent with the reference images, showing a normal scene of people walking in a public area. No obvious anomalies such as missing objects, unusual structures, or unexpected elements are visibl
- `D8_0126` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > Despite the tool zooms failing to target the person correctly, a visual inspection of the full images shows a normal public scene. The presence of a uniformed individual is plausible in this setting and does not constitu
- `D8_0119` L=1 direct=0.95→tool=0.10 rank=0.50 **TP_lost_to_FN** used_tool=True
  > The zoomed-in view confirms the presence of a person's legs and feet, which is a normal occurrence in a public space. There are no signs of defects or anomalies in the environment or the person's appearance that would in
  ... and 2 more losses.

### D9  (wins 7, losses 10)

Win sample-types: {'FP_corrected': 5, 'FN_corrected': 2}
Loss sample-types: {'TN_lost_to_FP': 3, 'TP_lost_to_FN': 7}

**WINS** (item · direct→tool · rank · type · rationale):

- `D9_0121` L=1 direct=0.01→tool=1.00 rank=0.58 **FN_corrected** used_tool=False
  > The query image contains a cherry label and red liquid, whereas all reference images contain banana labels and light-colored liquid. This fundamental difference in product type (flavor/label) and content color makes the 
- `D9_0168` L=1 direct=0.01→tool=1.00 rank=0.73 **FN_corrected** used_tool=False
  > The query image contains a red liquid and a cherry label, which is inconsistent with the normal reference images that all feature a light-colored liquid and a banana label.
- `D9_0022` L=0 direct=0.99→tool=0.05 rank=0.28 **FP_corrected** used_tool=True
  > The query image shows a jumper wire with connectors that appear structurally sound and identical to the normal reference images, aside from the wire color which varies in the normal set. No defects or anomalies were dete
- `D9_0057` L=0 direct=0.99→tool=0.10 rank=0.35 **FP_corrected** used_tool=True
  > The query image shows a standard patch cable with no visible defects or anomalies compared to the reference images. The connectors and cable surface appear normal.
- `D9_0078` L=0 direct=0.99→tool=0.10 rank=0.11 **FP_corrected** used_tool=False
  > The query image matches the normal reference patterns (single jumper wire on mesh). No anomalies detected.
- `D9_0039` L=0 direct=0.98→tool=0.10 rank=0.05 **FP_corrected** used_tool=True
  > The query image shows a normal lunchbox with fruit and granola. No anomalies were detected in the detailed inspection of both compartments.
- `D9_0079` L=0 direct=0.98→tool=0.10 rank=0.16 **FP_corrected** used_tool=False
  > The query image shows a bag with two bolts, two nuts, and two washers. The reference images also show bags with similar hardware components (two bolts, two nuts, two washers). The arrangement varies slightly due to rando

**LOSSES**:

- `D9_0047` L=0 direct=0.02→tool=1.00 rank=0.13 **TN_lost_to_FP** used_tool=False
  > The query image displays a cherry-labeled bottle with red liquid, whereas all reference images show banana-labeled bottles with light liquid. This fundamental difference in product type (label and content color) confirms
- `D9_0032` L=0 direct=0.02→tool=1.00 rank=0.07 **TN_lost_to_FP** used_tool=False
  > The query image is anomalous because it features a red liquid and a cherry label, whereas all normal reference images consistently show a white liquid and a banana label.
- `D9_0041` L=0 direct=0.02→tool=0.95 rank=0.79 **TN_lost_to_FP** used_tool=False
  > The query image contains a red liquid with a cherry label, whereas all reference images show light-colored liquids with banana or orange labels. This clear deviation in both liquid color and label content indicates an an
- `D9_0090` L=1 direct=0.98→tool=0.05 rank=0.03 **TP_lost_to_FN** used_tool=False
  > The query image matches the pattern of the normal reference images, containing the expected food items in a standard arrangement without visible anomalies.
- `D9_0129` L=1 direct=0.98→tool=0.05 rank=0.04 **TP_lost_to_FN** used_tool=False
  > The query image is visually consistent with the normal reference images, showing a standard arrangement of healthy food items in a lunchbox without any apparent anomalies.
- `D9_0157` L=1 direct=0.99→tool=0.10 rank=0.48 **TP_lost_to_FN** used_tool=False
  > The query image displays an intact jumper wire, which is consistent with the normal reference images. The anomaly in the reference set is a broken wire, which is not present in the query image.
- `D9_0100` L=1 direct=0.99→tool=0.10 rank=0.41 **TP_lost_to_FN** used_tool=False
  > The query image matches the pattern of the normal reference images (specifically the one with a single yellow wire). There are no visible signs of damage, misalignment, or foreign objects that would indicate an anomaly.
- `D9_0176` L=1 direct=0.99→tool=0.10 rank=0.31 **TP_lost_to_FN** used_tool=False
  > The query image matches the configuration of the second and fourth reference images (single connector stack, yellow wire), indicating it is a normal sample.
  ... and 2 more losses.

---
