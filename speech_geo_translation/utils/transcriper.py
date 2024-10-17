import nemo.collections.asr as nemo_asr
from nemo.collections.asr.parts.submodules.ctc_decoding import CTCDecodingConfig

from enum import Enum


class Language(Enum):
    AR = 1
    EN = 2


class Transcriper:
    def __init__(
        self,
    ):
        self.ar_model = nemo_asr.models.EncDecCTCModelBPE.restore_from(
            "/home/mohamed/Mohamed/Vodafone_project/projects/app/files/asr_model_files/ar_model/ar_conformer_with_adapter.nemo"
        )
        decoding_cfg = CTCDecodingConfig()

        decoding_cfg.strategy = "flashlight"
        decoding_cfg.beam.search_type = "flashlight"
        decoding_cfg.beam.kenlm_path = f"/home/mohamed/Mohamed/Vodafone_project/projects/app/files/asr_model_files/base_lm.bin"
        decoding_cfg.beam.flashlight_cfg.lexicon_path = f"/home/mohamed/Mohamed/Vodafone_project/projects/app/files/asr_model_files/base_lm.lexicon"
        decoding_cfg.beam.flashlight_cfg.boost_path = f"/home/mohamed/Mohamed/Vodafone_project/projects/app/files/asr_model_files/boost.txt"

        decoding_cfg.beam.beam_size = 32
        decoding_cfg.beam.beam_alpha = 0.1
        decoding_cfg.beam.beam_beta = 0.1
        decoding_cfg.beam.flashlight_cfg.beam_size_token = 32
        decoding_cfg.beam.flashlight_cfg.beam_threshold = 15.0

        self.ar_model.change_decoding_strategy(decoding_cfg)

        self.en_model = nemo_asr.models.EncDecCTCModelBPE.restore_from(
            "/home/mohamed/Mohamed/Vodafone_project/projects/app/files/asr_model_files/en_model/canary-1b.nemo",
            map_location="cpu",
        )

    def __call__(self, audio_path: str, language: str):
        if language == "Arabic":
            return self.ar_model.transcribe([audio_path])[0]
        elif language == "English":
            return self.en_model.transcribe([audio_path])[0]

    def transcribe(self, audio_path: str, language: str):
        return self.__call__(audio_path=audio_path, language=language)
