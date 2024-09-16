""" TODO - Module DOC """

import re
from abc import ABC, abstractmethod
from typing import Mapping, Any
from num2words import num2words
from modules import utilities
from modules.compiled.canonical_transcription_pb2 import CanonicalToken
from modules.constants import ConfigSections, Tokenizer


class CanonicalTokenizer(ABC):
    """ TODO - Class DOC """

    def __init__(self, language_code: str):
        self._language_code = language_code

    @staticmethod
    def _get_canonical_pronunciation_word(word: str, start_time: float = 0.0, end_time: float = 0.0) -> CanonicalToken:
        """ TODO - Function DOC """

        return CanonicalToken(word=word, start_time=start_time, end_time=end_time,
                              type=CanonicalToken.CanonicalTokenType.PRONUNCIATION)

    @staticmethod
    def _get_canonical_punctuation_word(word: str, start_time: float = 0.0, end_time: float = 0.0) -> CanonicalToken:
        """ TODO - Function DOC """

        return CanonicalToken(word=word, start_time=start_time, end_time=end_time,
                              type=CanonicalToken.CanonicalTokenType.PUNCTUATION)

    @abstractmethod
    def tokenize(self, word: str, start_time: float = 0.0, end_time: float = 0.0) -> [CanonicalToken]:
        """ TODO - Function DOC """

        pass


class DefaultCanonicalTokenizer(CanonicalTokenizer):
    """ TODO - Class DOC """

    SPECIAL_CHARACTERS = '"#$%()/<=>@[\\]^_`{|}~'
    ALLOWED_PUNCTUATION = '!,-.:;?'

    def __init__(self, language_code: str, tokenizer_configuration: Mapping[str, Any] = None):
        super().__init__(language_code)
        self._tokenizer_config = tokenizer_configuration if tokenizer_configuration else \
            utilities.load_configuration_section(ConfigSections.TOKENIZER)

    def tokenize(self, word: str, start_time: float = 0.0, end_time: float = 0.0) -> [CanonicalToken]:
        """ TODO - Function DOC """

        # Empty word check
        if not word:
            return None

        # Clean special characters
        cleaned_word = re.sub('[' + self.SPECIAL_CHARACTERS + ']', '', word)

        # Separate punctuation and pronunciation
        last_character = cleaned_word[-1]
        if cleaned_word in self.ALLOWED_PUNCTUATION:
            return [super()._get_canonical_punctuation_word(cleaned_word, start_time, end_time)]
        elif last_character in self.ALLOWED_PUNCTUATION:
            pronunciation_word = super()._get_canonical_pronunciation_word(cleaned_word[:-1], start_time, end_time)
            punctuation_word = super()._get_canonical_punctuation_word(last_character, start_time, end_time)
            return self._tokenize_pronunciation_word(pronunciation_word) + [punctuation_word]
        else:
            pronunciation_word = super()._get_canonical_pronunciation_word(cleaned_word, start_time, end_time)
            return self._tokenize_pronunciation_word(pronunciation_word)

    def _is_tokenizer_config_enabled(self, config_key: str) -> bool:
        """ TODO - Function DOC """

        return self._tokenizer_config[config_key]

    def _tokenize_pronunciation_word(self, pronunciation_word: CanonicalToken) -> [CanonicalToken]:
        """ TODO - Function DOC """

        tokens = [pronunciation_word]

        if self._is_tokenizer_config_enabled(Tokenizer.LOWERCASE):
            processed_tokens = list()
            for token in tokens:
                processed_word = token.word.lower()
                processed_token = CanonicalToken(word=processed_word, start_time=token.start_time,
                                                 end_time=token.end_time, type=token.type)
                processed_tokens.append(processed_token)
            tokens = processed_tokens

        if self._is_tokenizer_config_enabled(Tokenizer.NUMBERS_TO_WORD):
            processed_tokens = list()
            for token in tokens:
                if token.word.isdigit():
                    processed_words = num2words(int(token.word), lang=self._language_code).split()
                    for processed_word in processed_words:
                        processed_token = CanonicalToken(word=processed_word, start_time=token.start_time,
                                                         end_time=token.end_time, type=token.type)
                        processed_tokens.append(processed_token)
                else:
                    processed_tokens.append(token)
            tokens = processed_tokens

        if self._is_tokenizer_config_enabled(Tokenizer.SPLIT_APOSTROPHES):
            processed_tokens = list()
            for token in tokens:
                regex_search_result = re.search(r'([\w]+[\'])([\w]+)', token.word)
                if regex_search_result:
                    processed_words = regex_search_result.groups()
                    for processed_word in processed_words:
                        processed_token = CanonicalToken(word=processed_word, start_time=token.start_time,
                                                         end_time=token.end_time, type=token.type)
                        processed_tokens.append(processed_token)
                else:
                    processed_tokens.append(token)
            tokens = processed_tokens

        if self._is_tokenizer_config_enabled(Tokenizer.EXPAND_CONTRACTED_WORDS):
            processed_tokens = list()
            for token in tokens:
                # TODO: Expand contracted words
                processed_tokens.append(token)
            tokens = processed_tokens

        if self._is_tokenizer_config_enabled(Tokenizer.EXPAND_COMPOUND_WORDS):
            processed_tokens = list()
            for token in tokens:
                # TODO: Expand compound words
                processed_tokens.append(token)
            tokens = processed_tokens

        if self._is_tokenizer_config_enabled(Tokenizer.MULTI_SPELLED_WORDS):
            processed_tokens = list()
            for token in tokens:
                # TODO: Expand multi spelled words
                processed_tokens.append(token)
            tokens = processed_tokens

        return tokens


class TEICanonicalTokenizer(DefaultCanonicalTokenizer):
    TYPE_B_EVENT_MARKERS = ['[vocal_event]', '[incident_event]', '[gap_event]']

    def tokenize(self, word: str, start_time: float = 0.0, end_time: float = 0.0) -> [CanonicalToken]:
        """ TODO - Function DOC """

        if word in TEICanonicalTokenizer.TYPE_B_EVENT_MARKERS:
            canonical_word_type_name = re.sub(r'[\[\]]', '', word).upper()
            canonical_word_type = CanonicalToken.CanonicalTokenType.DESCRIPTOR.values_by_name[canonical_word_type_name]
            return [CanonicalToken(start_time=start_time, end_time=end_time, type=canonical_word_type.index)]
        else:
            return super().tokenize(word, start_time, end_time)
