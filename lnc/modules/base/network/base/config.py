from lnc.modules.base.config import Config as ConfigBase

MAX_CONNECTION_TO_HOST = 3
RETRY_COUNT = 3
DELAY_BEFORE_RETRY = 0.01
TIMEOUT = 5
PORT = None
class Config(ConfigBase):
    max_connection_to_host:int = None
    retry_count:int = None
    delay_before_retry:float = None
    timeout:int = None
    port:int = None

    def __init__(self):
        super().__init__()
        self.max_connection_to_host = MAX_CONNECTION_TO_HOST
        self.retry_count = RETRY_COUNT
        self.delay_before_retry = DELAY_BEFORE_RETRY
        self.timeout = TIMEOUT
        self.port = PORT

    @classmethod
    def from_dict(cls, config_dict: dict):
        config = super().from_dict(config_dict)
        config.max_connection_to_host = config_dict.get("max_connection_to_host", MAX_CONNECTION_TO_HOST)
        config.retry_count = config_dict.get("retry_count", RETRY_COUNT)
        config.delay_before_retry = config_dict.get("delay_before_retry", DELAY_BEFORE_RETRY)
        config.timeout = config_dict.get("timeout", TIMEOUT)
        config.port = PORT
        return config