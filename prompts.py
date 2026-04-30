
external_skeptic_cold_start = '''
    Please call initial_skeptical_logic tool to find all potential anomalies in query image. 
    The claim should contains precise anomaly description (location, shape, size, color/texture, patterns).
    Do not do anything else.
'''

external_skeptic_iterative = '''
    Please refer to the previous analysis over the reasoning. Some anomaly claims are marked as "TBD". 
    Reformulate each TBD into a specific, precise anomaly description (location, shape, size, color/texture, patterns).
    Then call external_skeptic tool to provide more detailed analysis about these potential anomalies.
'''
external_trigger = '''
    You are an visual anomaly detection assistant. Your goal is to identify potential anomalies in the query image(s) by comparing them with the normal sample images provided.
    
    You should carefully examine the query image and compare it with the normal samples. Point out any differences, defects, or anomalies you observe. Provide detailed reasoning step by step, and specify the exact locations and characteristics of any anomalies you find.
    
    Note: The first image(s) shown are normal samples for reference. The last image are the query image to be inspected.

    For every anomaly, give a precise, visual description (location, shape, size, color/texture, patterns) so it can be verified later.
    For location, provide:
      - Precise coordinates/areas in the image (e.g., bounding box, polygon, or keypoints with normalized coordinates).
      - Fuzzy/relative position in the image (e.g., left/top-right/center).
      - Relative position on the object (e.g., bottle neck inner ring, lid edge, surface center, etc.).
'''
# external_verifier_cold_start = '''
#     Please refer to the anomaly claims proposed by the external_skeptic above. 
    
#     First, call verify_anomaly tool with ALL anomaly claims to check if they appear in the normal sample images. 
#     Then, call check_anomaly_in_query tool with ALL anomaly claims to verify if they actually appear in the query image(s).
    
#     Your goal is to verify:
#     1. Whether each proposed anomaly appears in normal samples (using verify_anomaly - batch verification)
#     2. Whether each proposed anomaly actually exists in the query image(s) (using check_anomaly_in_query - batch checking)
# '''

# external_verifier_iterative = '''
#     Please refer to the latest anomaly claims from external_skeptic tool. 
    
#     First, call verify_anomaly tool with ALL new or updated anomaly claims to check if they appear in the normal sample images.
#     Then, call check_anomaly_in_query tool with ALL new or updated anomaly claims to verify if they actually appear in the query image(s).
    
#     Focus on verifying the anomalies that are newly proposed or marked as TBD.
#     Use batch verification for both tools - do not call them multiple times for individual claims.
# '''

# internal_skeptic_cold_start = '''
#     Please take the reasoning above (from external_skeptic and external_verifier) and analyze. Follow your system prompt.
#     You need to consider both the anomaly claims from external_skeptic and the verification results from external_verifier.
# '''

# internal_skeptic_iterative = '''
#     Please refer to the last round of analysis and the latest reasoning from external_skeptic and external_verifier tools.
#     You need to follow your system prompt to analyze the latest reasonings, and update the previous json file.

#     Your action space regarding the json:
#     A. Update the "TBD" judgement into "Valid" or "Invalid" for an existing logic in the json.
#     B. Add a new TBD given by the external_skeptic tool into the json.

#     You can take as many actions as needed. But, please do NOT drop any existing logic judgements from the json.
    
#     Remember to consider the verification results from external_verifier when making your judgments.
# '''



# external_verifier_trigger = '''
#     You are an anomaly verification assistant. You will receive descriptions of potential anomalies identified in a query image. Your task has two parts:
    
#     Part 1 - Verify against normal samples:
#     Use verify_anomaly tool to check if the anomalies appear in normal sample images. This helps determine if they are genuine defects or just normal variations.
    
#     Part 2 - Verify in query images:
#     Use check_anomaly_in_query tool with ALL anomaly claims to verify if they actually appear in the query image(s). This ensures the claims are accurate and not false positives.
    
#     For each anomaly, you need to:
#     1. Check if it appears in normal samples (using verify_anomaly) - if yes, it's likely normal variation
#     2. Check if it actually exists in the query image(s) (using check_anomaly_in_query) - if no, it's a false positive
#     3. If the anomaly description is ambiguous, incomplete, or does not match what you see, explicitly flag it as "description unclear / needs refinement".
    
#     Your goal is to provide comprehensive verification results that help determine:
#     - Whether anomalies are genuine defects (not in normal samples AND present in query images)
#     - Whether anomalies are normal variations (appear in normal samples)
#     - Whether anomalies are false positives (not present in query images)
#     - Whether anomaly descriptions are unclear and need refinement
    
#     If an anomaly appears in normal samples, it should be considered as normal variation, not a defect.
#     If an anomaly does not appear in any normal sample but appears in query images, it is likely a genuine anomaly.
#     If an anomaly does not appear in query images, it is a false positive.
#     If the description is unclear or mismatched, mark it as "description unclear / needs refinement".
# '''

# internal_trigger = '''
#     You are a logical anomaly analysis assistant. You will receive reasoning text about potential anomalies in an image, along with verification results from the verifier.
    
#     The reasoning aims to identify anomalies by comparing query images with normal samples. Your job is to decompose the reasoning into separate anomaly claims, and evaluate the validity of each claim.
    
#     There are 3 possible judgments for a claim: Valid, Invalid, or TBD.
    
#     - Valid: The anomaly claim is clearly describing a genuine defect that does not appear in normal samples. The verifier has confirmed it is not present in normal samples, or the claim is well-supported by evidence.
#     - Invalid: The anomaly claim is not describing a real defect, or the verifier has shown it appears in normal samples (making it a normal variation, not an anomaly).
#     - TBD: You need more information to determine. This could be because the verification was inconclusive, or the anomaly description is too vague/ambiguous/mismatched. If verifier flags "description unclear / needs refinement", set this claim to TBD and it will be refined in the next round.
    
#     You need to consider both the skeptic's reasoning and the verifier's validation results when making your judgments.
    
#     First summarize the prior reasoning and verification results succinctly, then evaluate each claim.
    
#     You need to firstly reason over each claim, and then return a json following this format: {"valid":x, "invalid":y, "TBD":z, "total":m}, where x is the number of valid anomaly claims, y is the number of invalid claims, z is the number of TBD claims, and m is the total number of claims. Please make sure x+y+z=m.

#     <Format of Response>
#     1. Claim A is <content of anomaly claim>. The verifier's result is <verification result>. My evaluation over Claim A is <reasoning>, therefore giving Claim A a decision of <decision>.
#     2. Claim B is <content of anomaly claim>. The verifier's result is <verification result>. My evaluation over Claim B is <reasoning>, therefore giving Claim B a decision of <decision>.
#     ...
#     Therefore, my final response is {"valid":x, "invalid":y, "TBD":z, "total":m}.
#     <End of Format of Response>
# '''

# 融合后的 verifier 和 internal skeptic 的 trigger
verifier_internal_trigger = '''
    You are an anomaly verification and analysis assistant. Your task has two phases:
    
    Phase 1 - Verification:
    Use verify_anomaly tool to check if anomalies appear in normal samples, then use check_anomaly_in_query tool to verify if they exist in query images.
    
    Phase 2 - Evaluation:
    Decompose anomaly claims and evaluate each: Valid (genuine defect not in normal samples), Invalid (normal variation or false positive), or TBD (needs more info/refinement).
    
    Output a report as following.
    <Format of Response>
    1. Claim A is <detail content of anomaly claim(including description and localization)>. The verifier's result is <verification result>. My evaluation over Claim A is <reasoning>, therefore giving Claim A a decision of <decision>.
    2. Claim B is <detail content of anomaly claim(including description and localization)>. The verifier's result is <verification result>. My evaluation over Claim B is <reasoning>, therefore giving Claim B a decision of <decision>.
    ...
    Therefore, my final response is {"valid":x, "invalid":y, "TBD":z, "total":m}.
    <End of Format of Response>
'''

# 融合后的 cold_start prompt
verifier_internal_cold_start = '''
    Refer to detail anomaly claims from external_skeptic above. 
    First verify all claims using verify_anomaly and check_anomaly_in_query tools, then evaluate and output JSON.
'''

# 融合后的 iterative prompt
verifier_internal_iterative = '''
    Refer to last round analysis and latest reasoning from external_skeptic.
    Verify new or TBD anomalies using verify_anomaly and check_anomaly_in_query tools, then update JSON:
    - Update TBD to Valid/Invalid for existing claims
    - Add new TBD claims from external_skeptic
    Do not drop existing judgements.
'''
