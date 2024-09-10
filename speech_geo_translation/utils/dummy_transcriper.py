class DummyTranscriper:
    def __init__(
        self,
    ):
        pass

    def __call__(self, audio_path):
        return "شارع محمد فريد مع حسن رضوان طنطا الغربية"

    def transcribe(self, audio_path):
        return self.__call__(audio_path=audio_path)
