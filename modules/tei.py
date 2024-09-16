""" TODO - Module DOC """

import re
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from lxml import etree
from modules import utilities
from modules.compiled.canonical_transcription_pb2 import CanonicalToken
from modules.constants import TEI, ConfigSections

tei_config = utilities.load_configuration_section(ConfigSections.TEI)


class UtteranceEventType(Enum):
    """ TODO - Class DOC """

    UNKNOWN = 0
    FOREIGN = 1
    UNCLEAR = 2
    VOCAL = 3
    SHIFT = 4
    INCIDENT = 5
    GAP = 6
    DEL = 7
    OVERLAP = 8
    NOTE = 9
    DISTINCT = 10


@dataclass()
class Language:
    """ TODO - Class DOC """

    code: str = ''
    usage: float = 0.0
    words_count: int = 0


@dataclass()
class LanguageKnown:
    """ TODO - Class DOC """

    code: str = ''
    level: str = ''


@dataclass()
class Person:
    """ TODO - Class DOC """

    id: str = ''
    name: str = ''
    sex: str = ''
    language_knowledge: [LanguageKnown] = field(default_factory=list)


@dataclass()
class TimeInterval:
    """ TODO - Class DOC """

    id: str = ''
    interval: float = 0.0
    reference: str = ''


@dataclass()
class Timeline:
    """ TODO - Class DOC """

    unit: str = 's'
    intervals: [TimeInterval] = field(default_factory=list)


@dataclass()
class UtteranceEvent:
    """ TODO - Class DOC """

    type: UtteranceEventType = UtteranceEventType.UNKNOWN
    properties: [(str, str)] = field(default_factory=list)


@dataclass()
class UtteranceWord:
    """ TODO - Class DOC """

    word: str
    events: [UtteranceEvent] = field(default_factory=list)


@dataclass()
class Utterance:
    """ TODO - Class DOC """

    id: str = ''
    speaker: Person = None
    language: str = ''
    start_time: float = 0.0
    end_time: float = 0.0
    note: str = ''
    text: str = ''
    words: [UtteranceWord] = field(default_factory=list)


class TEIFile(object):
    """ TODO - Class DOC """

    DEFAULT_LANGUAGE = 'it-IT'

    TYPE_B_EVENTS = [CanonicalToken.CanonicalTokenType.VOCAL_EVENT, CanonicalToken.CanonicalTokenType.INCIDENT_EVENT,
                     CanonicalToken.CanonicalTokenType.GAP_EVENT]

    def __init__(self, file_path: str):
        self._file_path = file_path
        self._words_counter = 0
        self._parser = TEIParser(self)
        self._languages = self._parser.parse_lang_usage()
        self._speakers = self._parser.parse_partic_desc()
        self._timeline = self._parser.parse_timeline()
        self._utterances = self._parser.parse_body()

    @property
    def file_path(self) -> str:
        """ TODO - Function DOC """

        return self._file_path

    @property
    def total_words(self) -> int:
        """ TODO - Function DOC """

        return self._words_counter

    @property
    def parser(self) -> object:
        """ TODO - Function DOC """

        return self._parser

    @property
    def languages(self) -> [Language]:
        """ TODO - Function DOC """

        return self._languages

    @property
    def speakers(self) -> [Person]:
        """ TODO - Function DOC """

        return self._speakers

    @property
    def timeline(self) -> Timeline:
        """ TODO - Function DOC """

        return self._timeline

    @property
    def utterances(self) -> [Utterance]:
        """ TODO - Function DOC """

        return self._utterances

    def get_language_by_code(self, language_code: str) -> Language:
        """ TODO - Function DOC """

        return next((language for language in self._languages if language.code == language_code), self.DEFAULT_LANGUAGE)

    def get_speaker_by_id(self, speaker_id: str) -> Person:
        """ TODO - Function DOC """

        return next((speaker for speaker in self._speakers if speaker.id == speaker_id), None)

    def get_time_interval_by_id(self, time_interval_id: str) -> TimeInterval:
        """ TODO - Function DOC """

        return next((time_interval for time_interval in self._timeline.intervals if time_interval.id ==
                     time_interval_id), None)

    def increment_language_words_counter(self, language_code: str, increment: int) -> None:
        """ TODO - Function DOC """

        language = self.get_language_by_code(language_code)
        language.words_count += increment

    def increment_words_counter(self, increment: int) -> None:
        """ TODO - Function DOC """

        self._words_counter += increment

    def validate(self) -> (bool, property):
        """ TODO - Function DOC """

        validator = etree.XMLSchema(file=tei_config[TEI.XSD_SCHEMA_PATH])
        validation_result = validator.validate(etree.parse(self._file_path))

        return validation_result, validator.error_log


class TEIParser(object):
    """ TODO - Class DOC """

    class EventParser(ABC):
        """ TODO - Class DOC """

        @dataclass()
        class ParsedEvent:
            """ TODO - Class DOC """

            utterance_event: UtteranceEvent
            event_words: [str]
            non_event_words: [str]
            sub_events: ['TEIParser.EventParser.ParsedEvent']

        def __init__(self, event_tag: str, event_element: etree.Element, annotation_block_element: etree.Element):
            self._event_tag = event_tag
            self._event_element = event_element
            self._annotation_block_element = annotation_block_element

        def parse_event(self) -> ParsedEvent:
            """ TODO - Function DOC """

            utterance_event = UtteranceEvent(self._get_event_type(), self._get_event_properties())
            event_words = self._get_event_words()
            non_event_words = self._get_non_event_words()
            sub_events = self._parse_sub_events()

            return self.ParsedEvent(utterance_event, event_words, non_event_words, sub_events)

        def _get_event_attributes(self) -> [(str, str)]:
            """ TODO - Function DOC """

            return list((TEIParser._remove_prefix_from_tag(key), value) for key, value in
                        self._event_element.attrib.items())

        def _get_event_type_from_tag(self) -> UtteranceEventType:
            """ TODO - Function DOC """

            return UtteranceEventType[self._event_tag.upper()]

        def _parse_sub_events(self) -> [ParsedEvent]:
            """ TODO - Function DOC """

            return list(TEIParser._parse_event(sub_event_element, self._annotation_block_element) for sub_event_element
                        in self._event_element)

        def _get_words_from_element_text(self) -> [str]:
            """ TODO - Function DOC """

            return self._get_stripped_words_from_text(self._event_element.text)

        def _get_words_from_element_tail(self) -> [str]:
            """ TODO - Function DOC """

            return self._get_stripped_words_from_text(self._event_element.tail)

        @staticmethod
        def _get_stripped_words_from_text(text: str) -> [str]:
            """ TODO - Function DOC """

            return list(word.strip() for word in text.split() if word.strip()) if text else list()

        @abstractmethod
        def _get_event_type(self) -> UtteranceEventType:
            """ TODO - Function DOC """

            pass

        @abstractmethod
        def _get_event_properties(self) -> [(str, str)]:
            """ TODO - Function DOC """

            pass

        @abstractmethod
        def _get_event_words(self) -> [str]:
            """ TODO - Function DOC """

            pass

        @abstractmethod
        def _get_non_event_words(self) -> [str]:
            """ TODO - Function DOC """

            pass

    class TypeAEventParser(EventParser):
        """ TODO - Class DOC """

        def _get_event_type(self) -> UtteranceEventType:
            """ TODO - Function DOC """

            return super()._get_event_type_from_tag()

        def _get_event_properties(self) -> [(str, str)]:
            """ TODO - Function DOC """

            return super()._get_event_attributes()

        def _get_event_words(self) -> [str]:
            """ TODO - Function DOC """

            return super()._get_words_from_element_text()

        def _get_non_event_words(self) -> [str]:
            """ TODO - Function DOC """

            return super()._get_words_from_element_tail()

    class TypeBEventParser(EventParser):
        """ TODO - Class DOC """

        def _get_event_type(self) -> UtteranceEventType:
            """ TODO - Function DOC """

            return super()._get_event_type_from_tag()

        def _get_event_properties(self) -> [(str, str)]:
            """ TODO - Function DOC """

            property_key = TEIParser._remove_prefix_from_tag(self._event_element[0].tag)
            property_value = self._event_element[0].text
            return [(property_key, property_value)]

        def _get_event_words(self) -> [str]:
            """ TODO - Function DOC """

            return ['[{}_event]'.format(self._event_tag)]

        def _get_non_event_words(self) -> [str]:
            """ TODO - Function DOC """

            return super()._get_words_from_element_tail()

    class GapEventParser(TypeBEventParser):
        """ TODO - Class DOC """

        def _get_event_properties(self) -> [(str, str)]:
            """ TODO - Function DOC """

            return super()._get_event_attributes()

    class ShiftEventParser(EventParser):
        """ TODO - Class DOC """

        def _get_event_type(self) -> UtteranceEventType:
            """ TODO - Function DOC """

            return super()._get_event_type_from_tag()

        def _get_event_properties(self) -> [(str, str)]:
            """ TODO - Function DOC """

            return super()._get_event_attributes()

        def _get_event_words(self) -> [str]:
            """ TODO - Function DOC """

            return list() if self._event_element.get('new', 'normal') == 'normal' \
                else super()._get_words_from_element_tail()

        def _get_non_event_words(self) -> [str]:
            """ TODO - Function DOC """

            return super()._get_words_from_element_tail() if self._event_element.get('new', 'normal') == 'normal' \
                else list()

    class AnchorEventParser(EventParser):
        """ TODO - Class DOC """

        def _get_event_type(self) -> UtteranceEventType:
            """ TODO - Function DOC """

            return UtteranceEventType.OVERLAP

        def _get_event_properties(self) -> [(str, str)]:
            """ TODO - Function DOC """

            anchor_synch_attribute = self._event_element.get('synch')
            if re.fullmatch(r'ovrl\d+', anchor_synch_attribute):
                utterance_elements = TEIParser._get_elements_by_relative_xpath('tei:u', self._annotation_block_element)
                overlap_utterance_elements = utterance_elements[1:]
                for overlap_utterance_element in overlap_utterance_elements:
                    anchor_element = overlap_utterance_element[0]
                    overlap_utterance_anchor_id = anchor_element.get(TEIParser.XML_NAMESPACE_ATTRIBUTE_PREFIX + 'id')
                    if overlap_utterance_anchor_id == anchor_synch_attribute:
                        event_properties = list()
                        event_properties.append(('speaker_id', overlap_utterance_element.get('who')))
                        event_properties.append(('text', self._get_overlap_utterance_text(overlap_utterance_element)))
                        return event_properties
                raise etree.ParserError('Anchor tag\'s synch attribute {} in main utterance does not match any anchor '
                                        'tag IDs in overlap utterances.'.format(anchor_synch_attribute))
            elif re.fullmatch(r'ovrl\d+e', anchor_synch_attribute):
                return list()
            else:
                raise etree.ParserError('Anchor tag synch attribute {} not valid.'.format(anchor_synch_attribute))

        def _get_event_words(self) -> [str]:
            """ TODO - Function DOC """

            anchor_synch_attribute = self._event_element.get('synch')
            if re.fullmatch(r'ovrl\d+', anchor_synch_attribute):
                return super()._get_words_from_element_tail()
            elif re.fullmatch(r'ovrl\d+e', anchor_synch_attribute):
                return list()
            else:
                raise etree.ParserError('Anchor tag synch attribute {} not valid.'.format(anchor_synch_attribute))

        def _get_non_event_words(self) -> [str]:
            """ TODO - Function DOC """

            anchor_synch_attribute = self._event_element.get('synch')
            if re.fullmatch(r'ovrl\d+', anchor_synch_attribute):
                return list()
            elif re.fullmatch(r'ovrl\d+e', anchor_synch_attribute):
                return super()._get_words_from_element_tail()
            else:
                raise etree.ParserError('Anchor tag synch attribute {} not valid.'.format(anchor_synch_attribute))

        def _get_overlap_utterance_text(self, overlap_utterance_element: etree.Element) -> str:
            """ TODO - Function DOC """

            overlap_utterance_text = list()
            first_anchor_element_tail = overlap_utterance_element[0].tail
            overlap_utterance_text.extend(super()._get_stripped_words_from_text(first_anchor_element_tail))
            for event_element in overlap_utterance_element[1:-1]:
                parsed_event = TEIParser._parse_event(event_element, self._annotation_block_element)
                overlap_utterance_text.extend(parsed_event.event_words)
                overlap_utterance_text.extend(parsed_event.non_event_words)
            return ' '.join(overlap_utterance_text)

    class DefaultEventParser(EventParser):
        """ TODO - Class DOC """

        def _get_event_type(self) -> UtteranceEventType:
            """ TODO - Function DOC """

            return UtteranceEventType.UNKNOWN

        def _get_event_properties(self) -> [(str, str)]:
            """ TODO - Function DOC """

            return list()

        def _get_event_words(self) -> [str]:
            """ TODO - Function DOC """

            return list()

        def _get_non_event_words(self) -> [str]:
            """ TODO - Function DOC """

            return super()._get_words_from_element_tail()

    XML_NAMESPACE_ATTRIBUTE_PREFIX = '{%s}' % TEI.TEI_NAMESPACES.get('xml')
    TEI_NAMESPACE_ATTRIBUTE_PREFIX = '{%s}' % TEI.TEI_NAMESPACES.get('tei')

    EVENT_PARSE_HANDLER_MAPPING = {
        'unclear': TypeAEventParser,
        'del': TypeAEventParser,
        'foreign': TypeAEventParser,
        'vocal': TypeBEventParser,
        'incident': TypeBEventParser,
        'gap': GapEventParser,
        'shift': ShiftEventParser,
        'anchor': AnchorEventParser,
        'distinct': TypeAEventParser
    }

    def __init__(self, tei_file: TEIFile):
        self._tei_file = tei_file
        self._tei_file_tree = etree.parse(tei_file.file_path)
        self._root_tree = self._tei_file_tree.getroot()

    @property
    def tei_file(self) -> TEIFile:
        """ TODO - Function DOC """

        return self._tei_file

    def parse_lang_usage(self) -> [Language]:
        """ TODO - Function DOC """

        language_elements = self._get_elements_by_root_xpath('tei:teiHeader/tei:profileDesc/tei:langUsage/tei:language')
        languages = list()
        for language_element in language_elements:
            language = Language()
            language.code = language_element.get('ident')
            language.usage = language_element.get('usage')
            languages.append(language)
        return languages

    def parse_partic_desc(self) -> [Person]:
        """ TODO - Function DOC """

        persons_elements = self._get_elements_by_root_xpath('tei:teiHeader/tei:profileDesc/tei:particDesc/tei:person')
        participants = list()
        for person_element in persons_elements:
            participant_id = person_element.get('{}id'.format(TEIParser.XML_NAMESPACE_ATTRIBUTE_PREFIX))
            participant_name = person_element.get('n')
            participant_sex = person_element.get('sex')
            participant = Person(participant_id, participant_name, participant_sex)
            participant.language_knowledge = self._parse_language_knowledge(person_element)
            participants.append(participant)
        return participants

    def parse_timeline(self) -> Timeline:
        """ TODO - Function DOC """

        when_elements = self._get_elements_by_root_xpath('tei:text/tei:timeline/tei:when')
        timeline = Timeline()
        for when_element in when_elements:
            time_interval = TimeInterval()
            time_interval.id = when_element.get('{}id'.format(TEIParser.XML_NAMESPACE_ATTRIBUTE_PREFIX))
            time_interval.interval = float(when_element.get('interval', default=0.0))
            time_interval.reference = str(when_element.get('since', default=''))
            timeline.intervals.append(time_interval)
        return timeline

    def parse_body(self) -> [Utterance]:
        """ TODO - Function DOC """

        annotation_block_elements = self._get_elements_by_root_xpath('tei:text/tei:body/tei:annotationBlock')
        utterances = list()
        for annotation_block_element in annotation_block_elements:
            utterance = Utterance()
            # Populate utterance with data from annotation block attributes
            speaker_id = annotation_block_element.get('who')
            utterance.speaker = self._tei_file.get_speaker_by_id(speaker_id)
            start_time_id = annotation_block_element.get('start')
            utterance.start_time = self._tei_file.get_time_interval_by_id(start_time_id).interval
            end_time_id = annotation_block_element.get('end')
            utterance.end_time = self._tei_file.get_time_interval_by_id(end_time_id).interval
            # Populate utterance with data from main utterance element (the first utterance in the block)
            utterance_elements = self._get_elements_by_relative_xpath('tei:u', annotation_block_element)
            main_utterance_element = utterance_elements[0]
            utterance.id = main_utterance_element.get('{}id'.format(TEIParser.XML_NAMESPACE_ATTRIBUTE_PREFIX))
            # Determine utterance language: if main utterance's second element is a <foreign> tag use its 'lang'
            # attribute as language code otherwise language code it-IT is used
            first_main_utterance_element = main_utterance_element[0]
            if self._remove_prefix_from_tag(first_main_utterance_element.tag) == 'foreign':
                event_elements_container = first_main_utterance_element
                utterance.language = event_elements_container.get('{}lang'.format(
                    TEIParser.XML_NAMESPACE_ATTRIBUTE_PREFIX))
            else:
                utterance.language = self.tei_file.DEFAULT_LANGUAGE
                event_elements_container = main_utterance_element
            # First events container element is always a <note> tag
            utterance_note_element = event_elements_container[0]
            utterance.note = utterance_note_element.text.strip()
            # Populate utterance words
            for event_element in event_elements_container:
                parsed_event = TEIParser._parse_event(event_element, annotation_block_element)
                utterance.words.extend(self._get_utterance_word_for_parsed_event(parsed_event,
                                                                                 [parsed_event.utterance_event]))
            # Increment total and language's words counts
            utterance_words_count = len(utterance.words)
            self._tei_file.increment_words_counter(utterance_words_count)
            self._tei_file.increment_language_words_counter(utterance.language, utterance_words_count)
            # Populate text
            utterance.text = ' '.join(list(utterance_word.word for utterance_word in utterance.words))
            utterances.append(utterance)
        return utterances

    def _parse_language_knowledge(self, person_element: etree.Element) -> [LanguageKnown]:
        """ TODO - Function DOC """

        lang_known_elements = self._get_elements_by_relative_xpath('tei:langKnowledge/tei:langKnown', person_element)
        language_knowledge = list()
        for lang_known_element in lang_known_elements:
            language_known = LanguageKnown()
            language_known.code = lang_known_element.get('tag')
            language_known.level = lang_known_element.get('level')
            language_knowledge.append(language_known)
        return language_knowledge

    def _get_elements_by_root_xpath(self, root_xpath: str) -> [etree.Element]:
        """ TODO - Function DOC """

        return self._root_tree.xpath(root_xpath, namespaces=TEI.TEI_NAMESPACES)

    @staticmethod
    def _get_elements_by_relative_xpath(relative_xpath: str, element: etree.Element) -> [etree.Element]:
        """ TODO - Function DOC """

        return element.xpath(relative_xpath, namespaces=TEI.TEI_NAMESPACES)

    @staticmethod
    def _get_utterance_word_for_parsed_event(parsed_event: EventParser.ParsedEvent, word_events: [UtteranceEvent]) -> \
            [UtteranceWord]:
        """ TODO - Function DOC """

        utterance_words = list(UtteranceWord(event_word, word_events) for event_word in parsed_event.event_words)

        for sub_event in parsed_event.sub_events:
            extended_word_events = word_events + [sub_event.utterance_event]
            utterance_words.extend(TEIParser._get_utterance_word_for_parsed_event(sub_event, extended_word_events))

        utterance_words.extend(list(UtteranceWord(non_event_word) for non_event_word in parsed_event.non_event_words))

        return utterance_words

    @staticmethod
    def _parse_event(event_element: etree.Element, annotation_block_element: etree.Element) -> EventParser.ParsedEvent:
        """ TODO - Function DOC """

        event_tag = TEIParser._remove_prefix_from_tag(event_element.tag)
        event_parser_class = TEIParser.EVENT_PARSE_HANDLER_MAPPING.get(event_tag, TEIParser.DefaultEventParser)
        event_parser = event_parser_class(event_tag, event_element, annotation_block_element)
        return event_parser.parse_event()

    @staticmethod
    def _remove_prefix_from_tag(tag: str) -> str:
        """ TODO - Function DOC """

        if tag.startswith(TEIParser.TEI_NAMESPACE_ATTRIBUTE_PREFIX):
            return tag[len(TEIParser.TEI_NAMESPACE_ATTRIBUTE_PREFIX):]

        if tag.startswith(TEIParser.XML_NAMESPACE_ATTRIBUTE_PREFIX):
            return tag[len(TEIParser.XML_NAMESPACE_ATTRIBUTE_PREFIX):]

        return tag
