class KatalanError(Exception):
    pass

class ConfigurationError(KatalanError):
    pass

class PendingBusInteraction(KatalanError):
    pass
