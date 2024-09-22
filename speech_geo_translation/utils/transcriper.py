import nemo.collections.asr as nemo_asr

from enum import Enum


class Language(Enum):
    AR = 1
    EN = 2


class Transcriper:
    def __init__(
        self,
    ):
        self.ar_model = nemo_asr.models.EncDecCTCModelBPE.restore_from(
            "/home/mohamed/Mohamed/Vodafone_project/conformer_ar.nemo"
        )
        self.en_model = nemo_asr.models.EncDecCTCModelBPE.restore_from(
            "/home/mohamed/Mohamed/Vodafone_project/conformer_en.nemo"
        )

    def __call__(self, audio_path: str, language: Language = Language.AR):
        if language == Language.AR:
            return self.ar_model.transcribe([audio_path])[0]
        elif language == Language.EN:
            return self.en_model.transcribe([audio_path])[0]

    def transcribe(self, audio_path: str, language: Language = Language.AR):
        return self.__call__(audio_path=audio_path, language=language)
