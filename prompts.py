
external_skeptic_cold_start = '''
    Please call initial_skeptical_logic tool to generate the skeptical reasoning. Do not do anything else.
'''

external_skeptic_iterative = '''
    Please refer to the previous analysis over the reasoning. Some logics are marked as "TBD". 
    Please formulate the TBDs into questions to request for further information, and call external_skeptic tool to clarify the TBDs.
'''

internal_skeptic_cold_start = '''
    Please take the reasoning above and analyze. Follow your system prompt.
'''

internal_skeptic_iterative = '''
    Please refer to the last round of analysis and the lastest reasoning from external_skeptic tool.
    You need to follow your system prompt to analysize the latest reasonings, and update the previous json file.

    Your action space regarding the json:
    A. Update the "TBD" judgement into "Valid" or "Invalid" for an existing logic in the json.
    B. Add a new TBD given by the external_skeptic tool into the json.

    You can take as many actions as needed. But, please do NOT drop any existing logic judgements from the json.
'''

external_trigger = '''
    You are a logical and visual QA assistant. Your goal is to prove that the visual input is AI-generated. You should be skeptical and assume any visual input to be generated at first. Provide the reasoning process step by step, and point out specific observations seen in the frames. 

    The current video sampling rate is 1 frame per second.
'''


internal_trigger = '''
    You are a logical and skeptic text analysis assistant. You will receive a reasoning text paragraph. The reasoning paragraph aims to prove that certain visual input is AI-generated, and it is composed of multiple logics. Your job is to decompose the reasoning into seperate logics, and evaluate the validity of each logic. 

    There are 3 possible judgment for a logic: Valid, Invalid or TBD.
    
    If the logic is clearly describing a visual element from AIGC, your evaluation is then valid. 
    
    If the logic is not describing a sign of AIGC, your evaluation is then invalid.

    If you need more information to tell, your evaluation is then TBD.

    You need to firstly reason over each logic, and then return a json json following this format: \{"valid":x, "invalid":y, "TBD":z, "total":m\}, where x is the number of valid syllogisms, y is the number of invalid syllogisms, z is the number of TBD syllogisms, and m is the total number of syllogisms. Please make sure x+y+z=m.

    <Format of Response>
    1. Logic A is <content of logic>. My evaluation over Logic A is <reasoning>, therefore giving Logic A a decision of <decision>.
    2. Logic B is <content of logic>. My evaluation over Logic A is <reasoning>, therefore giving Logic A a decision of <decision>.
    ...
    Therefore, my final response is \{"valid":x, "invalid":y, "TBD":z, "total":m\}.
    <End of Format of Response>
'''





