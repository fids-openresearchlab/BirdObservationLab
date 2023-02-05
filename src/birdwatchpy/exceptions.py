
class BirdwatchpyError(Exception):
    """Base class for Sphinx errors."""
    category = 'Birdwatchpy error'

class PathnameFormatException(Exception):
    pass


class SequenceIDFormatException(Exception):
    pass

class ProductionNotPlausibleException(Exception):
    pass