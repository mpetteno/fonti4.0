""" TODO - Module DOC """

from abc import ABC, abstractmethod
from typing import Mapping, Any
from modules.compiled.canonical_transcription_pb2 import CanonicalTranscription, CanonicalToken
from modules import tei, utilities
from modules.constants import ConfigSections, Evaluator


class CanonicalEvaluator(ABC):
    """ TODO - Class DOC """

    @abstractmethod
    def evaluate(self, canonical_transcription: CanonicalTranscription) -> CanonicalTranscription:
        """ TODO - Function DOC """

        pass


class DefaultMetricsCanonicalEvaluator(CanonicalEvaluator):
    """ TODO - Class DOC """

    def __init__(self, evaluator_configuration: Mapping[str, Any] = None):
        self._evaluator_config = evaluator_configuration if evaluator_configuration else \
            utilities.load_configuration_section(ConfigSections.EVALUATOR)

    def evaluate(self, canonical_transcription: CanonicalTranscription) -> CanonicalTranscription:
        """ TODO - Function DOC """

        evaluated_transcription = canonical_transcription

        if not self._is_evaluator_config_enabled(Evaluator.PUNCTUATION):
            for canonical_utterance in evaluated_transcription.utterances:
                evaluated_words = list(canonical_word for canonical_word in canonical_utterance.words if
                                       canonical_word.type != CanonicalToken.CanonicalTokenType.PUNCTUATION)
                del canonical_utterance.words[:]
                canonical_utterance.words.extend(evaluated_words)

        if not self._is_evaluator_config_enabled(Evaluator.STOP_WORDS):
            for canonical_utterance in evaluated_transcription.utterances:
                # TODO - Filter stop words
                evaluated_words = canonical_utterance.words
                del canonical_utterance.words[:]
                canonical_utterance.words.extend(evaluated_words)

        if not self._is_evaluator_config_enabled(Evaluator.ELISIONS):
            for canonical_utterance in evaluated_transcription.utterances:
                # TODO - Filter elisions
                evaluated_words = canonical_utterance.words
                del canonical_utterance.words[:]
                canonical_utterance.words.extend(evaluated_words)

        if not self._is_evaluator_config_enabled(Evaluator.DIACRITICS):
            for canonical_utterance in evaluated_transcription.utterances:
                # TODO - Filter diacritics
                evaluated_words = canonical_utterance.words
                del canonical_utterance.words[:]
                canonical_utterance.words.extend(evaluated_words)

        if not self._is_evaluator_config_enabled(Evaluator.APOCOPES):
            for canonical_utterance in evaluated_transcription.utterances:
                # TODO - Filter apocopes
                evaluated_words = canonical_utterance.words
                del canonical_utterance.words[:]
                canonical_utterance.words.extend(evaluated_words)

        return evaluated_transcription

    def _is_evaluator_config_enabled(self, config_key: str) -> bool:
        """ TODO - Function DOC """

        return self._evaluator_config[config_key]


class ExternalToolMetricsCanonicalEvaluator(DefaultMetricsCanonicalEvaluator):
    """ TODO - Class DOC """

    def evaluate(self, canonical_transcription: CanonicalTranscription) -> CanonicalTranscription:
        """ TODO - Function DOC """

        evaluated_transcription = canonical_transcription

        for canonical_utterance in evaluated_transcription.utterances:
            normalized_words = list(reference_word for reference_word in canonical_utterance.words
                                    if reference_word.type not in tei.TEIFile.TYPE_B_EVENTS)
            del canonical_utterance.words[:]
            canonical_utterance.words.extend(normalized_words)

        return super().evaluate(evaluated_transcription)
