from src.media.tts_generator import NarrationGenerator


def test_kokoro_voice_mapping_english_voices():
    assert NarrationGenerator._resolve_voice("en-US-ChristopherNeural") == "af_heart"
    assert NarrationGenerator._resolve_voice("en-US-AriaNeural") == "af_heart"
    assert NarrationGenerator._resolve_voice("en-GB-RyanNeural") == "bf_emma"
    assert NarrationGenerator._resolve_voice("unknown-voice") == "af_heart"
