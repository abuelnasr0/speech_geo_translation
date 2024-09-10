import nemo.collections.asr as nemo_asr

class Transcriper:
    def __init__(self, ):
        self.model = nemo_asr.models.EncDecCTCModelBPE.restore_from("/home/mohamed/Mohamed/Vodafone project/Conformer-CTC-L_spe128_ar-AR_3.0.nemo")

    def __call__(self, audio_path):
        return self.model.transcribe([audio_path])[0]
    
    def transcribe(self, audio_path):
        return self.__call__(audio_path=audio_path)
