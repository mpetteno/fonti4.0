""" TODO - Module DOC """

from abc import ABC, abstractmethod
from modules import utilities
from modules.compiled.canonical_transcription_pb2 import CanonicalUtterance
from modules.constants import Paths
from modules.evaluator import ExternalToolMetricsCanonicalEvaluator


class CanonicalConverter(ABC):
    """ TODO - Class DOC """

    def __init__(self, canonical_transcription_path: str, config_section: str):
        self._canonical_transcription_path = canonical_transcription_path
        self._config = utilities.load_configuration_section(config_section)

    def convert(self):
        """ TODO - Function DOC """

        canonical_transcription = utilities.load_canonical_transcription(self._canonical_transcription_path)
        normalized_transcription = self._get_transcription_evaluator().evaluate(canonical_transcription)
        converted_lines = list()
        for canonical_utterance in normalized_transcription.utterances:
            converted_lines.extend(self._convert_canonical_utterance(canonical_utterance))

        self._save_converted_file(converted_lines)

    @staticmethod
    def get_utterance_text(canonical_utterance: CanonicalUtterance) -> str:
        """ TODO - Function DOC """

        return ' '.join(list(utterance_word.word for utterance_word in canonical_utterance.words))

    def _get_converted_file_output_path(self) -> str:
        """ TODO - Function DOC """

        converted_file_output_path = self._config[self._get_output_path_config_label()]
        converted_file_name = utilities.get_file_name(self._canonical_transcription_path)
        converted_file_extension = self._get_converted_file_extension()
        return '{}/{}.{}'.format(converted_file_output_path, converted_file_name, converted_file_extension)

    def _save_converted_file(self, file_lines: [str]) -> None:
        """ TODO - Function DOC """

        converted_file_content = ('{}\n'.format(line) for line in file_lines)
        converted_file_output_path = self._get_converted_file_output_path()
        utilities.write_local_file(converted_file_output_path, converted_file_content)

    @abstractmethod
    def _convert_canonical_utterance(self, canonical_utterance: CanonicalUtterance) -> [str]:
        """ TODO - Function DOC """

        pass

    @abstractmethod
    def _get_converted_file_extension(self) -> str:
        """ TODO - Function DOC """

        pass

    @abstractmethod
    def _get_output_path_config_label(self):
        """ TODO - Function DOC """

        pass

    @abstractmethod
    def _get_transcription_evaluator(self):
        """ TODO - Function DOC """

        pass


class TRNConverter(CanonicalConverter):
    """ TODO - Class DOC """

    def __init__(self, canonical_transcription_path: str, converted_file_output_path: str):
        super().__init__(canonical_transcription_path, converted_file_output_path)

    def _convert_canonical_utterance(self, canonical_utterance: CanonicalUtterance) -> [str]:
        """ TODO - Function DOC """

        return ['{} ({})'.format(super().get_utterance_text(canonical_utterance), canonical_utterance.id)]

    def _get_converted_file_extension(self) -> str:
        """ TODO - Function DOC """

        return 'trn'

    def _get_output_path_config_label(self):
        """ TODO - Function DOC """

        return Paths.TRN_OUTPUT_PATH

    def _get_transcription_evaluator(self):
        """ TODO - Function DOC """

        return ExternalToolMetricsCanonicalEvaluator()


class CTMConverter(CanonicalConverter):
    """ TODO - Class DOC """

    def _convert_canonical_utterance(self, canonical_utterance: CanonicalUtterance) -> [str]:
        """ TODO - Function DOC """

        waveform_file_name = utilities.get_file_name(self._canonical_transcription_path).replace(' ', '_')
        waveform_channel = 'A'
        ctm_lines = list()
        for canonical_utterance_word in canonical_utterance.words:
            begin_time = canonical_utterance_word.start_time
            duration = canonical_utterance_word.end_time - canonical_utterance_word.start_time
            word = canonical_utterance_word.word
            ctm_line = '<{}> <{}> <{}> <{}> {}'.format(waveform_file_name, waveform_channel, begin_time, duration, word)
            ctm_lines.append(ctm_line)
        return ctm_lines

    def _get_converted_file_extension(self) -> str:
        """ TODO - Function DOC """

        return 'ctm'

    def _get_output_path_config_label(self):
        """ TODO - Function DOC """

        return Paths.CTM_OUTPUT_PATH

    def _get_transcription_evaluator(self):
        """ TODO - Function DOC """

        return ExternalToolMetricsCanonicalEvaluator()


class STMConverter(CanonicalConverter):
    """ TODO - Class DOC """

    def _convert_canonical_utterance(self, canonical_utterance: CanonicalUtterance) -> [str]:
        """ TODO - Function DOC """

        waveform_file_name = utilities.get_file_name(self._canonical_transcription_path).replace(' ', '_')
        waveform_channel = 'A'
        speaker_id = canonical_utterance.speaker_id
        begin_time = canonical_utterance.start_time
        end_time = canonical_utterance.end_time
        transcript = super().get_utterance_text(canonical_utterance)

        return ['<{}> <{}> <{}> <{}> <{}> {}'.format(waveform_file_name, waveform_channel, speaker_id, begin_time,
                                                     end_time, transcript)]

    def _get_converted_file_extension(self) -> str:
        """ TODO - Function DOC """

        return 'stm'

    def _get_output_path_config_label(self):
        """ TODO - Function DOC """

        return Paths.STM_OUTPUT_PATH

    def _get_transcription_evaluator(self):
        """ TODO - Function DOC """

        return ExternalToolMetricsCanonicalEvaluator()


class TXTConverter(CanonicalConverter):
    """ TODO - Class DOC """

    def _convert_canonical_utterance(self, canonical_utterance: CanonicalUtterance) -> [str]:
        """ TODO - Function DOC """

        return [super().get_utterance_text(canonical_utterance)]

    def _get_converted_file_extension(self) -> str:
        """ TODO - Function DOC """

        return 'txt'

    def _get_output_path_config_label(self):
        """ TODO - Function DOC """

        return Paths.TXT_OUTPUT_PATH

    def _get_transcription_evaluator(self):
        """ TODO - Function DOC """

        return ExternalToolMetricsCanonicalEvaluator()
