class ExampleFaceDetector:
    """It doesn't really work!"""
    def __init__(self, example_parameter):
        self.example_parameter = example_parameter

    @staticmethod
    def detect_faces(_binary_data):
        return [((110, 120), (130, 140)),
                ((220, 240), (230, 250)),
                ((300, 300), (310, 310))
        ]
