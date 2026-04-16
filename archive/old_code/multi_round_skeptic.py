
import os
from agents import Agent, Runner
from prompts import external_skeptic_cold_start, external_skeptic_iterative, \
        verifier_internal_trigger, verifier_internal_cold_start, verifier_internal_iterative
from tools import initial_skeptical_logic, external_skeptic, verify_anomaly, check_anomaly_in_query
from utils import no_epoche_check


external_skeptic_interface = Agent(
    name="External_Skeptic",
    instructions="You are a coordinator among multiple reasoning modules.",
    tools=[initial_skeptical_logic, external_skeptic],
)

# 融合后的 verifier 和 internal skeptic
verifier_internal_interface = Agent(
    name="Verifier_Internal",
    instructions=verifier_internal_trigger,
    tools=[verify_anomaly, check_anomaly_in_query],
)


class Skeptic_agent():

    def __init__(self, session, run_config, depth_quota=3):
        self.session = session
        self.run_config = run_config
        self.depth_quota = depth_quota
        self.count = 0

    def run(self, visual_ctx):

        while self.count < self.depth_quota:

            if self.count == 0:
                # 第一轮：冷启动
                # 1. External Skeptic 提出异常
                ext_ske_prompt = external_skeptic_cold_start
                Runner.run_sync(external_skeptic_interface, input=ext_ske_prompt, session=self.session, \
                            run_config=self.run_config, context=visual_ctx)
                
                # 2. Verifier_Internal 验证异常并综合评估
                verifier_prompt = verifier_internal_cold_start
                result = Runner.run_sync(verifier_internal_interface, input=verifier_prompt, session=self.session, \
                            run_config=self.run_config, context=visual_ctx)
                result = result.to_input_list()
                
            else:
                # 后续轮次：迭代
                # 1. External Skeptic 针对TBD提出更详细的异常
                ext_ske_prompt = external_skeptic_iterative
                Runner.run_sync(external_skeptic_interface, input=ext_ske_prompt, session=self.session, \
                                run_config=self.run_config, context=visual_ctx)

                # 2. Verifier_Internal 验证新的异常并综合评估更新JSON
                verifier_prompt = verifier_internal_iterative
                result = Runner.run_sync(verifier_internal_interface, input=verifier_prompt, session=self.session, \
                                run_config=self.run_config, context=visual_ctx)
                result = result.to_input_list()
                
            #? check skeptic ending criteria
            if no_epoche_check(result):
                break

            self.count += 1

        return result, self.count

    
