
import os
from agents import Agent, Runner
from prompts import external_skeptic_cold_start, external_skeptic_iterative, \
        internal_trigger, internal_skeptic_cold_start, internal_skeptic_iterative
from tools import initial_skeptical_logic, external_skeptic
from utils import no_epoche_check


external_skeptic_interface = Agent(
    name="External_Skeptic",
    instructions="You are a coordinator among multiple reasoning modules.",
    tools=[initial_skeptical_logic, external_skeptic],
)

internal_skeptic = Agent(
    name="Internal_Skeptic",
    instructions=internal_trigger,
    tools=[],
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
                ext_ske_prompt = external_skeptic_cold_start
                Runner.run_sync(external_skeptic_interface, input=ext_ske_prompt, session=self.session, \
                            run_config=self.run_config, context=visual_ctx)
                
                int_ske_prompt = internal_skeptic_cold_start
                result = Runner.run_sync(internal_skeptic, input=int_ske_prompt, session=self.session, \
                                        run_config=self.run_config, context=visual_ctx)
                result = result.to_input_list()
                
            else:
                ext_ske_prompt = external_skeptic_iterative
                Runner.run_sync(external_skeptic_interface, input=ext_ske_prompt, session=self.session, \
                                run_config=self.run_config, context=visual_ctx)

                int_ske_prompt = internal_skeptic_iterative
                result = Runner.run_sync(internal_skeptic, input=int_ske_prompt, session=self.session, \
                                        run_config=self.run_config, context=visual_ctx)
                result = result.to_input_list()
                
            #? check skeptic ending criteria
            if no_epoche_check(result):
                break

            self.count += 1

        return result, self.count

    
