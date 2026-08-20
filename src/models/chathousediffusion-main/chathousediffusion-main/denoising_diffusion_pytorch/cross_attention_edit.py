import random
class AttentionEdit:
    __instance = None
    __hasInit = False

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
            return cls.__instance
        return cls.__instance

    def __init__(self, total_steps=50, inject_step=25, mask_threshold=0.3):
        if not self.__hasInit:
            self.total_steps = total_steps
            self.inject_step = inject_step
            self.seed = 0
            self.mask_threshold = mask_threshold
            self.old_attn_dict = {
                k: {} for k in range(total_steps)
            }  # timestep, attn_index, attn_value
            self.new_attn_dict = {
                k: {} for k in range(total_steps)
            }  # timestep, attn_index, attn_value
            self.timestep = total_steps
            self.attn_index = 0
            self.__hasInit = True

    @classmethod
    def is_instance_created(cls):
        return cls.__instance is not None

    def save_attn(self, attn):
        self.old_attn_dict[self.timestep][self.attn_index] = attn

    def has_attn(self):
        if self.timestep in self.old_attn_dict:
            return self.attn_index in self.old_attn_dict[self.timestep]
        return False

    def replace_attn(self, new_attn):
        self.new_attn_dict[self.timestep][self.attn_index] = new_attn
        if self.timestep < self.inject_step:
            return new_attn
        else:
            return self.old_attn_dict[self.timestep][self.attn_index]

    def next_index(self):
        self.attn_index += 1

    def next_timestep(self):
        self.timestep -= 1
        self.attn_index = 0

    def reset(self):
        self.timestep = self.total_steps
        self.attn_index = 0

    def end_of_generate(self):
        if 0 in self.new_attn_dict[0]:
            self.old_attn_dict = self.new_attn_dict
            self.new_attn_dict = {k: {} for k in range(self.total_steps)}
        else:
            pass

    def clear_all(self):
        self.old_attn_dict = {k: {} for k in range(self.total_steps)}
        self.new_attn_dict = {k: {} for k in range(self.total_steps)}
        self.timestep = self.total_steps
        self.attn_index = 0
        self.seed=random.randint(0,1000000)
