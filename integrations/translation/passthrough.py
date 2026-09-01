"""Development translator that preserves canonical English text."""


class PassthroughTranslator:
    def translate(self, text: str, target_language: str) -> str:
        return text

