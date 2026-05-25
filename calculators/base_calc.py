class BaseCalculator:
    category = "deepsky"

    def __init__(self):
        self.inputs = {}
        self.results = {}

    def set_inputs(self, **kwargs):
        self.inputs.update(kwargs)

    def calculate(self):
        raise NotImplementedError
