""" TODO - Module DOC """

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, cast, Mapping
from pathlib import Path
from google.cloud.speech_v1p1beta1 import RecognizeResponse
from google.protobuf import json_format
from modules import utilities, tei
from modules.compiled.canonical_transcription_pb2 import *
from modules.constants import Paths, ConfigSections
from modules.tokenizer import DefaultCanonicalTokenizer, TEICanonicalTokenizer


class CanonicalTranslator(ABC):
    """ TODO - Class DOC """

    def __init__(self, transcription_path: str, reference_tei_file: tei.TEIFile):
        self._transcription_path = transcription_path
        self._reference_tei_file = reference_tei_file
        self._config = utilities.load_configuration_section(self._get_configuration_section())
        self._canonical_transcription = None
        self._current_reference_utterance_index = -1

    def translate(self) -> None:
        """ TODO - Function DOC """

        self._canonical_transcription = CanonicalTranscription()
        for reference_utterance_index in range(len(self._reference_tei_file.utterances)):
            self._current_reference_utterance_index = reference_utterance_index
            canonical_utterance = CanonicalUtterance()
            canonical_utterance.id = self._get_current_reference_utterance().id
            canonical_utterance.language = self._get_current_reference_utterance().language
            self._pre_canonical_utterance_populate()
            self._populate_canonical_utterance(canonical_utterance)
            self._post_canonical_utterance_populate()
            self._canonical_transcription.utterances.append(canonical_utterance)
        self._save_canonical_transcription_to_json()

    def _get_canonical_transcription_output_path(self) -> str:
        """ TODO - Function DOC """

        return self._config[Paths.CANONICAL_TRANSCRIPTION_OUTPUT_PATH]

    def _get_current_reference_utterance(self) -> tei.Utterance:
        """ TODO - Function DOC """

        return self._get_reference_utterance(self._current_reference_utterance_index)

    def _get_next_reference_utterance(self) -> tei.Utterance:
        """ TODO - Function DOC """

        return self._get_reference_utterance(self._current_reference_utterance_index + 1)

    def _get_previous_reference_utterance(self) -> tei.Utterance:
        """ TODO - Function DOC """

        return self._get_reference_utterance(self._current_reference_utterance_index - 1)

    def _get_reference_utterance(self, reference_utterance_index) -> tei.Utterance:
        """ TODO - Function DOC """

        return self._reference_tei_file.utterances[reference_utterance_index]

    def _is_first_reference_utterance(self) -> bool:
        """ TODO - Function DOC """

        return self._current_reference_utterance_index == 0

    def _is_last_reference_utterance(self) -> bool:
        """ TODO - Function DOC """

        return self._current_reference_utterance_index == len(self._reference_tei_file.utterances) - 1

    def _save_canonical_transcription_to_json(self) -> None:
        """ TODO - Function DOC """

        output_file_name = '{}.json'.format(utilities.get_file_name(self._transcription_path))
        output_file_path = '{}/{}'.format(self._get_canonical_transcription_output_path(), output_file_name)
        json_canonical_transcription = json_format.MessageToJson(self._canonical_transcription)
        utilities.write_local_file(output_file_path, json_canonical_transcription)

    @abstractmethod
    def _get_configuration_section(self) -> str:
        """ TODO - Function DOC """

        pass

    @abstractmethod
    def _pre_canonical_utterance_populate(self) -> None:
        """ TODO - Function DOC """

        pass

    @abstractmethod
    def _populate_canonical_utterance(self, canonical_utterance: CanonicalUtterance) -> None:
        """ TODO - Function DOC """

        pass

    @abstractmethod
    def _post_canonical_utterance_populate(self) -> None:
        """ TODO - Function DOC """

        pass


class CloudServiceCanonicalTranslator(CanonicalTranslator):
    """ TODO - Class DOC """

    class TranscriptionFileStatus(ABC):
        """ TODO - Class DOC """

        def __init__(self, response: Any, word_index: int = 0):
            self._response = response
            self._word_index = word_index

        @abstractmethod
        def get_current_word_content(self) -> str:
            """ TODO - Function DOC """

            pass

        @abstractmethod
        def get_current_word_evaluation_time(self) -> float:
            """ TODO - Function DOC """

            pass

        @abstractmethod
        def get_current_word_start_time(self) -> float:
            """ TODO - Function DOC """

            pass

        @abstractmethod
        def get_current_word_end_time(self) -> float:
            """ TODO - Function DOC """

            pass

        @abstractmethod
        def move_forward(self) -> bool:
            """ TODO - Function DOC """

            pass

    def __init__(self, transcription_path: str, reference_tei_file: tei.TEIFile,
                 tokenizer_configuration: Mapping[str, Any] = None):
        super().__init__(transcription_path, reference_tei_file)
        self._tokenizer_configuration = tokenizer_configuration
        self._transcription_file_status_register = self._init_transcription_file_status_register()

    def _populate_canonical_utterance(self, canonical_utterance: CanonicalUtterance) -> None:
        """ TODO - Function DOC """

        self._populate_canonical_utterance_words_before_start(canonical_utterance)
        self._populate_canonical_utterance_words(canonical_utterance)
        self._populate_canonical_utterance_words_after_end(canonical_utterance)

    def _pre_canonical_utterance_populate(self) -> None:
        """ TODO - Function DOC """

        pass

    def _post_canonical_utterance_populate(self) -> None:
        """ TODO - Function DOC """

        self._update_transcription_file_registers()

    def _init_transcription_file_status_register(self) -> Dict[str, TranscriptionFileStatus]:
        """ TODO - Function DOC """

        transcription_file_status_register = dict()
        base_transcription_file_name = utilities.get_file_name(self._transcription_path)
        base_transcription_file_extension = utilities.get_file_extension(self._transcription_path)
        base_transcription_file_root_path = utilities.get_parent_path(self._transcription_path)
        glob_expression = '{}*{}'.format(base_transcription_file_name, base_transcription_file_extension)
        for transcription_file_path in Path(base_transcription_file_root_path).glob(glob_expression):
            transcription_file_language = utilities.get_file_name(transcription_file_path)[-5:]
            transcription_file_content = utilities.read_local_file(transcription_file_path)
            transcription_file_status = self._get_transcription_file_status(transcription_file_content)
            transcription_file_status_register[transcription_file_language] = transcription_file_status
        return transcription_file_status_register

    def _populate_canonical_utterance_words_before_start(self, canonical_utterance: CanonicalUtterance) -> None:
        """ TODO - Function DOC """

        current_transcription_file_status = self._get_current_transcription_file_status()
        while self._is_current_word_before_reference_utterance_start():
            canonical_word = self._tokenize_current_word()
            if canonical_word:
                canonical_utterance.words_before_start.extend(canonical_word)
            if not current_transcription_file_status.move_forward():
                break

    def _populate_canonical_utterance_words(self, canonical_utterance: CanonicalUtterance) -> None:
        """ TODO - Function DOC """

        current_transcription_file_status = self._get_current_transcription_file_status()
        canonical_utterance.start_time = current_transcription_file_status.get_current_word_start_time()
        last_word_end_time = current_transcription_file_status.get_current_word_end_time()
        while self._is_current_word_in_reference_utterance():
            last_word_end_time = current_transcription_file_status.get_current_word_end_time()
            canonical_word = self._tokenize_current_word()
            if canonical_word:
                canonical_utterance.words.extend(canonical_word)
            if not current_transcription_file_status.move_forward():
                break
        canonical_utterance.end_time = last_word_end_time

    def _populate_canonical_utterance_words_after_end(self, canonical_utterance: CanonicalUtterance) -> None:
        """ TODO - Function DOC """

        current_transcription_file_status = self._get_current_transcription_file_status()
        while self._is_current_word_after_reference_utterance_end():
            canonical_word = self._tokenize_current_word()
            if canonical_word:
                canonical_utterance.words_after_end.extend(canonical_word)
            if not current_transcription_file_status.move_forward():
                break

    def _update_transcription_file_registers(self):
        """ TODO - Function DOC """

        current_reference_utterance = self._get_current_reference_utterance()
        for language, transcription_file_status in self._transcription_file_status_register.items():
            if language != current_reference_utterance.language:
                if not self._is_last_reference_utterance():
                    next_reference_utterance = self._get_next_reference_utterance()
                    if next_reference_utterance.language != current_reference_utterance.language:
                        upper_limit = current_reference_utterance.end_time
                    else:
                        upper_limit = self._get_words_after_end_time_limit()
                else:
                    upper_limit = self._get_words_after_end_time_limit()
                lower_limit = self._get_words_before_start_time_limit()
                while lower_limit <= transcription_file_status.get_current_word_evaluation_time() < upper_limit:
                    if not transcription_file_status.move_forward():
                        break

    def _get_current_transcription_file_status(self) -> TranscriptionFileStatus:
        """ TODO - Function DOC """

        current_reference_utterance = self._get_current_reference_utterance()
        return self._transcription_file_status_register[current_reference_utterance.language]

    def _is_current_word_after_reference_utterance_end(self) -> bool:
        """ TODO - Function DOC """

        current_word_evaluation_time = self._get_current_transcription_file_status().get_current_word_evaluation_time()
        words_after_end_time_limit = self._get_words_after_end_time_limit()
        current_reference_utterance = self._get_current_reference_utterance()
        return current_reference_utterance.end_time < current_word_evaluation_time < words_after_end_time_limit

    def _is_current_word_before_reference_utterance_start(self) -> bool:
        """ TODO - Function DOC """

        current_word_evaluation_time = self._get_current_transcription_file_status().get_current_word_evaluation_time()
        words_before_start_time_limit = self._get_words_before_start_time_limit()
        current_reference_utterance = self._get_current_reference_utterance()
        return words_before_start_time_limit <= current_word_evaluation_time < current_reference_utterance.start_time

    def _is_current_word_in_reference_utterance(self) -> bool:
        """ TODO - Function DOC """

        current_word_evaluation_time = self._get_current_transcription_file_status().get_current_word_evaluation_time()
        current_reference_utterance = self._get_current_reference_utterance()
        return current_reference_utterance.start_time <= current_word_evaluation_time <= \
            current_reference_utterance.end_time

    def _get_words_after_end_time_limit(self) -> float:
        """ TODO - Function DOC """

        current_reference_utterance = self._get_current_reference_utterance()
        if not self._is_last_reference_utterance():
            next_reference_utterance = self._get_next_reference_utterance()
            if next_reference_utterance.language != current_reference_utterance.language:
                return next_reference_utterance.start_time
            else:
                reference_end_time = current_reference_utterance.end_time
                return reference_end_time + (next_reference_utterance.start_time - reference_end_time) / 2
        else:
            return float('inf')

    def _get_words_before_start_time_limit(self) -> float:
        """ TODO - Function DOC """

        current_reference_utterance = self._get_current_reference_utterance()
        if not self._is_first_reference_utterance():
            previous_reference_utterance = self._get_previous_reference_utterance()
            if previous_reference_utterance.language != current_reference_utterance.language:
                return previous_reference_utterance.end_time
            else:
                reference_start_time = current_reference_utterance.start_time
                return reference_start_time - (reference_start_time - previous_reference_utterance.end_time) / 2
        else:
            return 0.0

    def _tokenize_current_word(self) -> [CanonicalWord]:
        """ TODO - Function DOC """

        current_transcription_file_status = self._get_current_transcription_file_status()
        default_tokenizer = DefaultCanonicalTokenizer(self._get_current_reference_utterance().language,
                                                      self._tokenizer_configuration)
        return default_tokenizer.tokenize(word=current_transcription_file_status.get_current_word_content(),
                                          start_time=current_transcription_file_status.get_current_word_start_time(),
                                          end_time=current_transcription_file_status.get_current_word_end_time())

    @abstractmethod
    def _get_transcription_file_status(self, transcription_file_content: str) -> TranscriptionFileStatus:
        """ TODO - Function DOC """

        pass


class TEIFileCanonicalTranslator(CanonicalTranslator):
    """ TODO - Class DOC """

    def __init__(self, transcription_path: str, reference_tei_file: tei.TEIFile,
                 tokenizer_configuration: Mapping[str, Any] = None):
        super().__init__(transcription_path, reference_tei_file)
        self._tokenizer_configuration = tokenizer_configuration

    def _get_configuration_section(self) -> str:
        """ TODO - Function DOC """

        return ConfigSections.TEI

    def _pre_canonical_utterance_populate(self) -> None:
        """ TODO - Function DOC """

        pass

    def _populate_canonical_utterance(self, canonical_utterance: CanonicalUtterance) -> None:
        """ TODO - Function DOC """

        current_reference_utterance = self._get_current_reference_utterance()
        canonical_utterance.start_time = current_reference_utterance.start_time
        canonical_utterance.end_time = current_reference_utterance.end_time
        canonical_utterance.note = current_reference_utterance.note
        canonical_utterance.speaker_id = current_reference_utterance.speaker.id
        # Populate words
        for tei_utterance_word in current_reference_utterance.words:
            tei_tokenizer = TEICanonicalTokenizer(current_reference_utterance.language, self._tokenizer_configuration)
            canonical_utterance_word = tei_tokenizer.tokenize(word=tei_utterance_word.word)
            if canonical_utterance_word:
                # Populate events
                for tei_utterance_word_event in tei_utterance_word.events:
                    canonical_utterance_word_event = CanonicalWordEvent(type=tei_utterance_word_event.type.name)
                    # Populate properties
                    for key, value in tei_utterance_word_event.properties:
                        canonical_utterance_word_event_property = CanonicalWordEventProperty(key=key, value=value)
                        canonical_utterance_word_event.properties.append(canonical_utterance_word_event_property)
                    for words in canonical_utterance_word:
                        words.events.append(canonical_utterance_word_event)
                canonical_utterance.words.extend(canonical_utterance_word)

    def _post_canonical_utterance_populate(self) -> None:
        """ TODO - Function DOC """

        pass


class GoogleSTTCanonicalTranslator(CloudServiceCanonicalTranslator):
    """ TODO - Class DOC """

    class GoogleTranscriptionFileStatus(CloudServiceCanonicalTranslator.TranscriptionFileStatus):
        """ TODO - Class DOC """

        def __init__(self, recognize_response: RecognizeResponse, word_index: int = 0, result_index: int = 0):
            super().__init__(recognize_response, word_index)
            self._result_index = result_index

        def get_current_word_content(self) -> str:
            """ TODO - Function DOC """

            return self._get_current_word().word

        def get_current_word_evaluation_time(self) -> float:
            """ TODO - Function DOC """

            return (self.get_current_word_start_time() + self.get_current_word_end_time()) / 2

        def get_current_word_start_time(self) -> float:
            """ TODO - Function DOC """

            return self._get_current_word().start_time.total_seconds()

        def get_current_word_end_time(self) -> float:
            """ TODO - Function DOC """

            return self._get_current_word().end_time.total_seconds()

        def move_forward(self) -> bool:
            """ TODO - Function DOC """

            result_index = self._result_index
            word_index = self._word_index
            transcription_results = self._response.results
            result_alternative = transcription_results[result_index].alternatives[0]
            if len(result_alternative.words) == word_index + 1:
                if len(transcription_results) == result_index + 1:
                    return False
                self._word_index = 0
                self._result_index += 1
            else:
                self._word_index += 1
            return True

        def _get_current_word(self):
            """ TODO - Function DOC """

            current_result_index = self._result_index
            current_word_index = self._word_index
            current_transcription_results = self._response.results
            current_result_alternative = current_transcription_results[current_result_index].alternatives[0]
            return current_result_alternative.words[current_word_index]

    def _get_configuration_section(self) -> str:
        """ TODO - Function DOC """

        return ConfigSections.GOOGLE_STT

    def _get_transcription_file_status(self, transcription_file_content: str):
        """ TODO - Function DOC """

        recognize_response = RecognizeResponse.from_json(transcription_file_content)
        return GoogleSTTCanonicalTranslator.GoogleTranscriptionFileStatus(recognize_response)


class AWSTranscribeCanonicalTranslator(CloudServiceCanonicalTranslator):
    """ TODO - Class DOC """

    class AmazonTranscriptionFileStatus(CloudServiceCanonicalTranslator.TranscriptionFileStatus):
        """ TODO - Class DOC """

        def __init__(self, response: Any, word_index: int = 0):
            super().__init__(response, word_index)

        def get_current_word_content(self) -> str:
            """ TODO - Function DOC """

            return self._get_current_word()['alternatives'][0]['content']

        def get_current_word_evaluation_time(self) -> float:
            """ TODO - Function DOC """

            return (self.get_current_word_start_time() + self.get_current_word_end_time()) / 2

        def get_current_word_start_time(self) -> float:
            """ TODO - Function DOC """

            if self.is_current_word_punctuation():
                current_word_index = self._word_index
                current_transcription_items = self._response['results']['items']
                if current_word_index == 0:
                    return 0.0
                else:
                    previous_word = current_transcription_items[current_word_index - 1]
                    return float(previous_word['start_time'])
            else:
                return float(self._get_current_word()['start_time'])

        def get_current_word_end_time(self) -> float:
            """ TODO - Function DOC """

            if self.is_current_word_punctuation():
                current_word_index = self._word_index
                current_transcription_items = self._response['results']['items']
                if current_word_index == 0:
                    return 0.0
                else:
                    previous_word = current_transcription_items[current_word_index - 1]
                    return float(previous_word['end_time'])
            else:
                return float(self._get_current_word()['end_time'])

        def is_current_word_punctuation(self) -> bool:
            """ TODO - Function DOC """

            return (self._get_current_word())['type'] == 'punctuation'

        def move_forward(self) -> bool:
            """ TODO - Function DOC """

            current_word_index = self._word_index
            current_transcription_items = self._response['results']['items']
            if len(current_transcription_items) == current_word_index + 1:
                return False
            else:
                self._word_index += 1
            return True

        def _get_current_word(self):
            """ TODO - Function DOC """

            return self._response['results']['items'][self._word_index]

    def _get_configuration_section(self) -> str:
        """ TODO - Function DOC """

        return ConfigSections.AWS_TRANSCRIBE

    def _get_transcription_file_status(self, transcription_file_content: str):
        """ TODO - Function DOC """

        transcribe_response = json.loads(transcription_file_content)
        return AWSTranscribeCanonicalTranslator.AmazonTranscriptionFileStatus(transcribe_response)

    def _is_current_word_after_reference_utterance_end(self) -> bool:
        """ TODO - Function DOC """

        current_transcription_file_status = cast(AWSTranscribeCanonicalTranslator.AmazonTranscriptionFileStatus,
                                                 super()._get_current_transcription_file_status())
        return current_transcription_file_status.is_current_word_punctuation() \
            or super()._is_current_word_after_reference_utterance_end()

    def _is_current_word_before_reference_utterance_start(self) -> bool:
        """ TODO - Function DOC """

        current_transcription_file_status = cast(AWSTranscribeCanonicalTranslator.AmazonTranscriptionFileStatus,
                                                 super()._get_current_transcription_file_status())
        return current_transcription_file_status.is_current_word_punctuation() \
            or super()._is_current_word_before_reference_utterance_start()

    def _is_current_word_in_reference_utterance(self) -> bool:
        """ TODO - Function DOC """

        current_transcription_file_status = cast(AWSTranscribeCanonicalTranslator.AmazonTranscriptionFileStatus,
                                                 super()._get_current_transcription_file_status())
        return current_transcription_file_status.is_current_word_punctuation() \
            or super()._is_current_word_in_reference_utterance()
