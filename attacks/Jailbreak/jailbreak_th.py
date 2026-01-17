# from data.jailbreak_th_data import Jailbreak_th_data
# class Jailbreak:
#     def __init__(self, levels=["ceremonial", "formal", "semi_formal", "informal", "casual"]):
#         self.obfuscation_prompts = [
#             Jailbreak_th_data.get_obfuscation_th()["compressor"][levels], 
#             Jailbreak_th_data.get_obfuscation_th()["dr_al"][levels]
#         ]
#         self.rule_prompts = [
#             Jailbreak_th_data.get_rule_th()["force_start"][levels], 
#             Jailbreak_th_data.get_rule_th()["negative_constraints"][levels]
#         ]
#         self.role_prompts = [
#             Jailbreak_th_data.get_role_play_th()["dan"][levels], 
#             Jailbreak_th_data.get_role_play_th()["stan"][levels], 
#             Jailbreak_th_data.get_role_play_th()["dev_mode"][levels]
#         ]
        
#         self.jailbreachat_prompts = [
#             Jailbreak_th_data.get_ja_prompts_1()["character_perspective"][levels] , 
#             Jailbreak_th_data.get_ja_prompts_1()["tom_jerry"][levels],
#             Jailbreak_th_data.get_ja_prompts_1()["niccolo_aim"][levels],
#             Jailbreak_th_data.get_ja_prompts_1()["condition_red"][levels]
#         ]
        
#         self.jailbreachat_prompts2 = [
#             Jailbreak_th_data.get_ja_prompts_2()["person_gpt"][levels],
#             Jailbreak_th_data.get_ja_prompts_2()["hgttg"][levels],
#             Jailbreak_th_data.get_ja_prompts_2()["alignment_benchmark"][levels],
#             Jailbreak_th_data.get_ja_prompts_2()["jb_jailbreak"][levels],
#             Jailbreak_th_data.get_ja_prompts_2()["switch_flipper"][levels]
#         ]
        
#         self.prompts = self.obfuscation_prompts + self.rule_prompts + self.role_prompts + self.jailbreachat_prompts + self.jailbreachat_prompts2
        
#     def get_random_prompt(self):
#         import random
#         return random.choice(self.prompts)
    
#     def get_combined_prompts(self, query_prompt, jailbreak_prompt, model):
#         if "[your query]" in jailbreak_prompt:
#             prompt = jailbreak_prompt.replace("[your query]", query_prompt)
#             if model is not None and "[your model]" in prompt:
#                 prompt = prompt.replace("[your model]", model)
#             return prompt
#         else:
#             return -1
            
#     def execute_attack(self, data, model):
#         # Todo: define the prompt evaluation scope
#         jailbreak_prompts = self.prompts
#         results = []
#         prompts = []
#         print("Model: ", model.model)
#         for prompt in data.generate_queries():
#             for jailbreak_prompt in jailbreak_prompts:
#                 query_prompt = self.get_combined_prompts(prompt, jailbreak_prompt, model.model)
#                 if query_prompt != -1:
#                     prompts.append(query_prompt)
#                     results.append(model.query(query_prompt))
#         return results, prompts
    
    
    
from data.jailbreak_th_data import Jailbreak_th_data

class Jailbreak:
    def __init__(self, level="ceremonial"):
        self.level = level

        self.obfuscation_prompts = [
            Jailbreak_th_data.get_obfuscation_th()["compressor"][level], 
            Jailbreak_th_data.get_obfuscation_th()["dr_al"][level]
        ]

        self.rule_prompts = [
            Jailbreak_th_data.get_rule_th()["force_start"][level], 
            Jailbreak_th_data.get_rule_th()["negative_constraints"][level]
        ]

        self.role_prompts = [
            Jailbreak_th_data.get_role_play_th()["dan"][level], 
            Jailbreak_th_data.get_role_play_th()["stan"][level], 
            Jailbreak_th_data.get_role_play_th()["dev_mode"][level]
        ]
        
        self.jailbreachat_prompts = [
            Jailbreak_th_data.get_ja_prompts_1()["character_perspective"][level], 
            Jailbreak_th_data.get_ja_prompts_1()["niccolo_aim"][level],
            Jailbreak_th_data.get_ja_prompts_1()["condition_red"][level]
        ]
        
        self.jailbreachat_prompts2 = [
            Jailbreak_th_data.get_ja_prompts_2()["person_gpt"][level],
            Jailbreak_th_data.get_ja_prompts_2()["hgttg"][level],
            Jailbreak_th_data.get_ja_prompts_2()["alignment_benchmark"][level],
            Jailbreak_th_data.get_ja_prompts_2()["jb_jailbreak"][level],
            Jailbreak_th_data.get_ja_prompts_2()["switch_flipper"][level]
        ]
        
        self.prompts = (
            self.obfuscation_prompts
            + self.rule_prompts
            + self.role_prompts
            + self.jailbreachat_prompts
            + self.jailbreachat_prompts2
        )

    def get_combined_prompts(self, query_prompt, jailbreak_prompt, model):
        if "[your query]" not in jailbreak_prompt:
            return None

        prompt = jailbreak_prompt.replace("[your query]", query_prompt)
        if model is not None and "[your model]" in prompt:
            prompt = prompt.replace("[your model]", model)
        return prompt
            
    def execute_attack(self, data, model):
        results = []
        prompts = []

        for query in data.generate_queries():
            for jailbreak_prompt in self.prompts:
                full_prompt = self.get_combined_prompts(
                    query, jailbreak_prompt, model.model
                )
                if full_prompt:
                    prompts.append(full_prompt)
                    results.append(model.query(full_prompt))

        return results, prompts
