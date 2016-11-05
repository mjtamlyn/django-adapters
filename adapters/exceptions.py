class ValidationError(Exception):
    def __init__(self, msg, field=None):
        super().__init__(msg, field)
        self.msg = msg
        self.field = field

    def __hash__(self):
        return hash((self.msg, self.field))

    def __eq__(self, other):
        if not isinstance(other, ValidationError):
            return NotImplemented
        return self.field == other.field and self.msg == other.msg


class CycleError(ValueError):
    pass
