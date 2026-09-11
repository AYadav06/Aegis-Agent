import time


class UsageTracker:
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.llm_calls = 0
        self.start_time = None

    def start(self):
        self.start_time = time.time()
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.llm_calls = 0

    def record(self, response):
        u = getattr(response, "usage", None)
        if u:
            self.prompt_tokens += getattr(u, "prompt_tokens", 0) or 0
            self.completion_tokens += getattr(u, "completion_tokens", 0) or 0
        self.llm_calls += 1

    @property
    def total_tokens(self):
        return self.prompt_tokens + self.completion_tokens

    @property
    def elapsed(self):
        if self.start_time is None:
            return 0.0
        return round(time.time() - self.start_time, 2)

    def report(self, agent_name: str = "Agent") -> str:
        return (
            f"\n[{agent_name}] "
            f"time={self.elapsed}s | "
            f"llm_calls={self.llm_calls} | "
            f"tokens: prompt={self.prompt_tokens}, "
            f"completion={self.completion_tokens}, total={self.total_tokens}"
        )
