""" TODO - Module DOC """

from __future__ import annotations
import collections
import json
import numpy as np
from abc import ABC, abstractmethod
from enum import Enum
from typing import Mapping, Any, Iterable
from modules import utilities
from modules.compiled.canonical_transcription_pb2 import CanonicalToken, CanonicalUtterance, CanonicalTokenEvent
from modules.constants import Paths, ConfigSections
from modules.evaluator import DefaultMetricsCanonicalEvaluator
from modules.tei import TEIFile


class LevenshteinOperation:
    """ TODO - Class DOC """

    class Type(Enum):
        """ TODO - Class DOC """

        CORRECT = 0
        INSERTION = 1
        DELETION = 2
        SUBSTITUTION = 3

    class Penalty(Enum):
        """ TODO - Class DOC """

        # According to SCTK weights
        CORRECT = 0
        INSERTION = 1
        DELETION = 1
        SUBSTITUTION = 2

    def __init__(self, reference_word: CanonicalToken = CanonicalToken(word=None),
                 hypothesis_word: CanonicalToken = CanonicalToken(word=None),
                 operation_type: Type = Type.CORRECT, operation_cost: int = Penalty.CORRECT.value):
        if operation_type not in LevenshteinOperation.Type:
            raise ValueError('Operation type {} not valid.'.format(operation_type))
        self._reference_word = reference_word
        self._hypothesis_word = hypothesis_word
        self._type = operation_type
        self._cost = operation_cost

    def __hash__(self):
        return hash((self._reference_word.word, self._hypothesis_word.word))

    def __eq__(self, other):
        return (self._reference_word.word, self._hypothesis_word.word) == (other.reference_word.word,
                                                                           other.hypothesis_word.word)

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return repr('{} ==> {}'.format(self._reference_word.word, self._hypothesis_word.word))

    @property
    def cost(self):
        """ TODO - Function DOC """

        return self._cost

    @property
    def hypothesis_word(self):
        """ TODO - Function DOC """

        return self._hypothesis_word

    @property
    def reference_word(self):
        """ TODO - Function DOC """

        return self._reference_word

    @property
    def type(self):
        """ TODO - Function DOC """

        return self._type


class LevenshteinOperationGroup:
    """ TODO - Class DOC """

    def __init__(self, operations_type: LevenshteinOperation.Type):
        self._operations_type = operations_type
        self._operations = list()

    @property
    def operations_type(self):
        """ TODO - Function DOC """

        return self._operations_type.name

    def add(self, operation: LevenshteinOperation) -> None:
        """ TODO - Function DOC """

        if operation.type != self._operations_type:
            raise ValueError('Operation type {} does not match with group operation type {}'.format(
                operation.type, self._operations_type))

        self._operations.append(operation)

    def collect_operations(self) -> [LevenshteinOperation, int]:
        """ TODO - Function DOC """

        transformations = collections.defaultdict(int)
        for operation in reversed(self._operations):
            transformations[operation] += 1
        return list((k, transformations[k]) for k in sorted(transformations, key=transformations.get, reverse=True))

    @staticmethod
    def operations_groups_to_dict(operations_groups: [LevenshteinOperationGroup]):
        """ TODO - Function DOC """

        operations_group_dict = collections.defaultdict()
        for operation_group in operations_groups:
            operations_group_dict[operation_group.operations_type] = collections.defaultdict()
            collected_operations = operation_group.collect_operations()
            for operation, count in collected_operations:
                operations_group_dict[operation_group.operations_type].update({
                    repr(operation): count
                })
        return operations_group_dict


class MetricsCalculator:
    """ TODO - Class DOC """

    @staticmethod
    def compute_corpus_metrics(files_metrics: Mapping[str, Any]) -> Mapping[str, Any]:
        """ TODO - Function DOC """

        corpus_metrics = collections.defaultdict()
        # Compute global metrics
        corpus_metrics.update(MetricsCalculator.compute_global_metrics(files_metrics.values()))
        # Compute per language metrics
        languages_metrics_group = MetricsCalculator._group_metrics_by_id(files_metrics.values(), 'languages')
        corpus_metrics['languages'] = MetricsCalculator._compute_global_metrics_for_group(languages_metrics_group)
        for language_code, language_metrics in languages_metrics_group.items():
            current_language_metrics = corpus_metrics['languages'][language_code]
            language_audio_note_group = MetricsCalculator._group_metrics_by_id(language_metrics, 'audio_notes')
            current_language_metrics['audio_notes'] = MetricsCalculator._compute_global_metrics_for_group(
                language_audio_note_group)
        # Compute per audio notes language metrics
        audio_notes_metrics_group = MetricsCalculator._group_metrics_by_id(files_metrics.values(), 'audio_notes')
        corpus_metrics['audio_notes'] = MetricsCalculator._compute_global_metrics_for_group(audio_notes_metrics_group)
        return corpus_metrics

    @staticmethod
    def compute_file_metrics(utterances_metrics: Mapping[str, Any]) -> Mapping[str, Any]:
        """ TODO - Function DOC """

        file_metrics = collections.defaultdict()
        # Compute global metrics
        file_metrics.update(MetricsCalculator.compute_global_metrics(utterances_metrics.values()))
        # Compute per language metrics
        language_metrics_group = MetricsCalculator._group_metrics_by_field(utterances_metrics.values(), 'language')
        file_metrics['languages'] = MetricsCalculator._compute_global_metrics_for_group(language_metrics_group)
        for language_code, language_metrics in language_metrics_group.items():
            current_language_metrics = file_metrics['languages'][language_code]
            language_audio_note_group = MetricsCalculator._group_metrics_by_field(language_metrics, 'audio_note')
            current_language_metrics['audio_notes'] = MetricsCalculator._compute_global_metrics_for_group(
                language_audio_note_group)
        # Compute per audio note tag metrics
        audio_note_metrics_group = MetricsCalculator._group_metrics_by_field(utterances_metrics.values(), 'audio_note')
        file_metrics['audio_notes'] = MetricsCalculator._compute_global_metrics_for_group(audio_note_metrics_group)
        return file_metrics

    @staticmethod
    def compute_utterance_metrics(backtrace: Mapping[str, Any]) -> Mapping[str, Any]:
        """ TODO - Function DOC """

        backtrace_totals = backtrace['totals']
        return {
            'totals': MetricsCalculator.compute_words_metrics(backtrace_totals['num_cor'],
                                                              backtrace_totals['num_sub'],
                                                              backtrace_totals['num_del'],
                                                              backtrace_totals['num_ins'],
                                                              backtrace_totals['ref_len'],
                                                              backtrace_totals['hyp_len']),
            'operations_groups': LevenshteinOperationGroup.operations_groups_to_dict(
                backtrace['operations_groups'].values())
        }

    @staticmethod
    def compute_global_metrics(metrics: Iterable[Mapping[str, Any]]):
        """ TODO - Function DOC """

        global_metrics = collections.defaultdict()

        # Compute overall text metrics
        overall_text_inputs = list(metric['overall_text'] for metric in metrics)
        global_metrics['overall_text'] = MetricsCalculator.compute_totals_metrics(overall_text_inputs)
        global_metrics['overall_text'].update(MetricsCalculator.compute_operations_groups(overall_text_inputs))

        # Compute without event tags text metrics
        without_tags_inputs = list(metric['without_tags_text'] for metric in metrics)
        global_metrics['without_tags_text'] = MetricsCalculator.compute_totals_metrics(without_tags_inputs)
        global_metrics['without_tags_text'].update(MetricsCalculator.compute_operations_groups(without_tags_inputs))

        # Compute event tags metrics
        global_metrics.update(MetricsCalculator.compute_event_tags_metrics(metrics))

        return global_metrics

    @staticmethod
    def compute_totals_metrics(metrics: Iterable[Mapping[str, Any]]) -> Mapping[str, Any]:
        """ TODO - Function DOC """

        totals_metrics = collections.defaultdict()
        input_totals = list(metric['totals'] for metric in metrics)
        total_ref_len = sum(metric['ref_len'] for metric in input_totals)
        total_hyp_len = sum(metric['hyp_len'] for metric in input_totals)
        total_num_cor = sum(metric['cor'] for metric in input_totals)
        total_num_sub = sum(metric['sub'] for metric in input_totals)
        total_num_del = sum(metric['del'] for metric in input_totals)
        total_num_ins = sum(metric['ins'] for metric in input_totals)
        totals_metrics.update(MetricsCalculator.compute_words_metrics(total_num_cor, total_num_sub, total_num_del,
                                                                      total_num_ins, total_ref_len, total_hyp_len))
        return {'totals': totals_metrics}

    @staticmethod
    def compute_event_tags_metrics(metrics: Iterable[Mapping[str, Any]]) -> Mapping[str, Mapping[str, Any]]:
        """ TODO - Function DOC """

        event_tags_group = MetricsCalculator._group_metrics_by_id(metrics, 'event_tags')
        event_tags_metrics = collections.defaultdict()
        for event_name, event_tag_metrics in event_tags_group.items():
            event_key = event_name.lower()
            event_tags_metrics[event_key] = MetricsCalculator.compute_totals_metrics(event_tag_metrics)
            event_tags_metrics[event_key].update(MetricsCalculator.compute_operations_groups(event_tag_metrics))
        return {'event_tags': event_tags_metrics}

    @staticmethod
    def compute_operations_groups(metrics: Iterable[Mapping[str, Any]]) -> Mapping[str, Any]:
        """ TODO - Function DOC """

        operations_groups_group = MetricsCalculator._group_metrics_by_id(metrics, 'operations_groups')
        operations_groups = collections.defaultdict()
        for operation_type, per_type_operation_groups in operations_groups_group.items():
            operations_groups[operation_type] = collections.defaultdict(int)
            for per_type_operation_group in per_type_operation_groups:
                for operation, count in per_type_operation_group.items():
                    operations_groups[operation_type][operation] += count
            operations_groups[operation_type] = dict(sorted(operations_groups[operation_type].items(),
                                                            key=lambda item: item[1], reverse=True))
        return {'operations_groups': operations_groups}

    @staticmethod
    def compute_words_metrics(num_cor: int, num_sub: int, num_del: int, num_ins: int, num_reference_words: int,
                              num_hypothesis_words: int) -> Mapping[str, float]:
        """ TODO - Function DOC """

        return {'ref_len': num_reference_words,
                'hyp_len': num_hypothesis_words,
                'cor': num_cor,
                'sub': num_sub,
                'del': num_del,
                'ins': num_ins,
                'errors': num_sub + num_del + num_ins,
                'aligned': num_cor + num_sub + num_del + num_ins,
                'wer': MetricsCalculator.compute_wer(num_sub, num_del, num_ins, num_reference_words),
                'mer': MetricsCalculator.compute_mer(num_cor, num_sub, num_del, num_ins),
                'wip': MetricsCalculator.compute_wip(num_cor, num_reference_words, num_hypothesis_words),
                'wil': MetricsCalculator.compute_wil(num_cor, num_reference_words, num_hypothesis_words)}

    @staticmethod
    def compute_wer(num_sub: int, num_del: int, num_ins: int, num_reference_words: int) -> float:
        """ TODO - Function DOC """

        wer_divider = num_reference_words if num_reference_words != 0 else 1
        word_error_rate = (num_sub + num_del + num_ins) / wer_divider
        return word_error_rate

    @staticmethod
    def compute_mer(num_cor: int, num_sub: int, num_del: int, num_ins) -> float:
        """ TODO - Function DOC """

        mer_divider = num_cor + num_sub + num_del + num_ins
        matching_error_rate = (num_sub + num_del + num_ins) / mer_divider if mer_divider != 0 else 0
        return matching_error_rate

    @staticmethod
    def compute_wip(num_cor: int, num_reference_words: int, num_hypothesis_words: int) -> float:
        """ TODO - Function DOC """

        if num_reference_words == 0 or num_hypothesis_words == 0:
            return 1
        word_information_preserved = (num_cor / num_hypothesis_words) * (num_cor / num_reference_words)
        return word_information_preserved

    @staticmethod
    def compute_wil(num_cor: int, num_reference_words: int, num_hypothesis_words: int) -> float:
        """ TODO - Function DOC """

        word_information_lost = 1 - MetricsCalculator.compute_wip(num_cor, num_reference_words, num_hypothesis_words)
        return word_information_lost

    @staticmethod
    def _compute_global_metrics_for_group(metrics_group: Mapping[str, Iterable[Mapping[str, Any]]]):
        """ TODO - Function DOC """

        global_metrics = collections.defaultdict(lambda: collections.defaultdict())
        for metrics_id, metrics in metrics_group.items():
            global_metrics[metrics_id].update(MetricsCalculator.compute_global_metrics(metrics))
        return global_metrics

    @staticmethod
    def _group_metrics_by_field(metrics: Iterable[Mapping[str, Any]], field: str) -> \
            Mapping[str, Iterable[Mapping[str, Any]]]:
        """ TODO - Function DOC """

        metrics_group = collections.defaultdict(list)
        for metric in metrics:
            metrics_group[metric[field]].append(metric)
        return metrics_group

    @staticmethod
    def _group_metrics_by_id(metrics: Iterable[Mapping[str, Any]], metric_id: str) -> \
            Mapping[str, Iterable[Mapping[str, Any]]]:
        """ TODO - Function DOC """

        filtered_metrics = list(metric[metric_id] for metric in metrics)
        metrics_group = collections.defaultdict(list)
        for filtered_metric in filtered_metrics:
            for metric_id, metric in filtered_metric.items():
                metrics_group[metric_id].append(metric)
        return metrics_group


class Metrics(ABC):
    """ TODO - Class DOC """

    def __init__(self, canonical_references: Iterable[str], canonical_hypotheses: Iterable[str]):
        self._corpus = zip(canonical_references, canonical_hypotheses)
        self._corpus_metrics = collections.defaultdict()

    def metrics(self) -> Mapping[str, Any]:
        """ TODO - Function DOC """

        files_metrics = collections.defaultdict()
        for canonical_reference, canonical_hypothesis in self._corpus:
            file_name = utilities.get_file_name(canonical_hypothesis)
            print('Compute metrics for file {}...'.format(file_name))
            ground_truth = self._get_ground_truth(canonical_reference)
            hypotheses = self._get_hypotheses(canonical_hypothesis)
            # Compute metrics per utterance
            utterances_metrics = collections.defaultdict()
            for reference, hypothesis in zip(ground_truth, hypotheses):
                utterances_metrics[reference.id] = self._get_utterance_metrics(reference, hypothesis)
            # Compute file metrics and update class dictionary
            file_metrics = collections.defaultdict()
            file_metrics.update(self._get_file_metrics(utterances_metrics))
            file_metrics['utterances'] = utterances_metrics
            files_metrics[file_name] = file_metrics
        # Compute file metrics and update class dictionary
        self._corpus_metrics.update(self._get_corpus_metrics(files_metrics))
        self._corpus_metrics['files'] = files_metrics
        # Allow subclasses to inject code before return
        self._process_metrics()
        return self._corpus_metrics

    def _get_ground_truth(self, canonical_reference: str) -> [CanonicalUtterance]:
        """ TODO - Function DOC """

        canonical_transcription = utilities.load_canonical_transcription(canonical_reference)
        transcription_evaluator = self._get_transcription_evaluator()
        return transcription_evaluator.evaluate(canonical_transcription).utterances if transcription_evaluator else \
            canonical_transcription.utterances

    def _get_hypotheses(self, canonical_hypothesis: str) -> [CanonicalUtterance]:
        """ TODO - Function DOC """

        canonical_transcription = utilities.load_canonical_transcription(canonical_hypothesis)
        transcription_evaluator = self._get_transcription_evaluator()
        return transcription_evaluator.evaluate(canonical_transcription).utterances if transcription_evaluator else \
            canonical_transcription.utterances

    @abstractmethod
    def _get_corpus_metrics(self, files_metrics: Mapping[str, Any]) -> Mapping[str, Any]:
        """ TODO - Function DOC """

        pass

    @abstractmethod
    def _get_file_metrics(self, utterances_metrics: Mapping[str, Any]) -> Mapping[str, Any]:
        """ TODO - Function DOC """

        pass

    @abstractmethod
    def _get_transcription_evaluator(self):
        """ TODO - Function DOC """

        pass

    @abstractmethod
    def _get_utterance_metrics(self, reference: CanonicalUtterance, hypothesis: CanonicalUtterance) -> \
            Mapping[str, Any]:
        """ TODO - Function DOC """

        pass

    @abstractmethod
    def _process_metrics(self) -> None:
        """ TODO - Function DOC """

        pass


class DefaultMetrics(Metrics):
    """ TODO - Class DOC """

    CANONICAL_TYPEB_EVENTS = (CanonicalToken.CanonicalTokenType.VOCAL_EVENT,
                              CanonicalToken.CanonicalTokenType.INCIDENT_EVENT,
                              CanonicalToken.CanonicalTokenType.GAP_EVENT)
    CSV_HEADER_FIELDS = ['operation', 'reference_word', 'hypothesis_word', 'events']

    def __init__(self, canonical_references: Iterable[str], canonical_hypotheses: Iterable[str],
                 evaluator_configuration: Mapping[str, Any] = None):
        super().__init__(canonical_references, canonical_hypotheses)
        self._config = utilities.load_configuration_section(self._get_configuration_section())
        self._evaluator_configuration = evaluator_configuration

    def _get_corpus_metrics(self, files_metrics: Mapping[str, Any]) -> Mapping[str, Any]:
        """ TODO - Function DOC """

        return MetricsCalculator.compute_corpus_metrics(files_metrics)

    def _get_file_metrics(self, utterances_metrics: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any]:
        """ TODO - Function DOC """

        return MetricsCalculator.compute_file_metrics(utterances_metrics)

    def _get_utterance_metrics(self, reference: CanonicalUtterance, hypothesis: CanonicalUtterance) \
            -> Mapping[str, Any]:
        """ TODO - Function DOC """

        # Reference and hypothesis words initialization
        original_reference_words = reference.words if reference.words else list()
        filtered_reference_words = list(reference_word for reference_word in original_reference_words
                                        if reference_word.type not in TEIFile.TYPE_B_EVENTS)
        hypothesis_words = hypothesis.words if hypothesis else list()

        utterance_metrics = collections.defaultdict()
        utterance_metrics['language'] = reference.language
        utterance_metrics['audio_note'] = reference.note

        # Operation matrix compilation
        operation_matrix = self._compile_operation_matrix(original_reference_words, filtered_reference_words,
                                                          hypothesis_words)

        # Backtrace though the best route and get CSV entries
        backtraces, csv_lines = self._backtrace_operation_matrix(operation_matrix)
        utterance_metrics['csv_lines'] = csv_lines

        # Compute overall metrics from backtrace
        utterance_metrics['overall_text'] = MetricsCalculator.compute_utterance_metrics(backtraces['overall_backtrace'])

        # Compute no event tags metrics from backtrace
        utterance_metrics['without_tags_text'] = MetricsCalculator.compute_utterance_metrics(
            backtraces['no_event_tags_backtrace'])

        # Compute event tags metrics from backtrace
        event_tags_backtrace = backtraces['event_tags_backtrace']
        events_metrics = collections.defaultdict()
        for event_name, event_backtrace in event_tags_backtrace.items():
            events_metrics[event_name] = MetricsCalculator.compute_utterance_metrics(event_backtrace)
        utterance_metrics['event_tags'] = events_metrics

        return utterance_metrics

    def _get_transcription_evaluator(self):
        """ TODO - Function DOC """

        return DefaultMetricsCanonicalEvaluator(self._evaluator_configuration)

    def _process_metrics(self) -> None:
        """ TODO - Function DOC """

        for file_name, file_metric in self._corpus_metrics['files'].items():
            # Write CSV backtrace file
            all_csv_lines = list()
            for utterance_metric in file_metric['utterances'].values():
                all_csv_lines.extend(utterance_metric['csv_lines'])
                del utterance_metric['csv_lines']
            utilities.write_local_csv_file(self._get_backtrace_output_file_path(file_name), self.CSV_HEADER_FIELDS,
                                           all_csv_lines)
        # Write JSON corpus metrics report file
        utilities.write_local_file(self._get_metrics_output_file_path(), json.dumps(self._corpus_metrics, indent=4))

    def _backtrace_operation_matrix(self, operation_matrix: [[LevenshteinOperation]]) -> (Mapping[str, Any], [[str]]):
        """ TODO - Function DOC """

        # Initialize backtraces
        overall_backtrace = {
            'totals': collections.defaultdict(int),
            'operations_groups': {operation_type.value: LevenshteinOperationGroup(operation_type) for operation_type
                                  in LevenshteinOperation.Type}
        }
        event_tags_backtrace = collections.defaultdict(
            lambda: {
                'totals': collections.defaultdict(int),
                'operations_groups': {operation_type.value: LevenshteinOperationGroup(operation_type) for operation_type
                                      in LevenshteinOperation.Type}
            }
        )
        no_event_tags_backtrace = {
            'totals': collections.defaultdict(int),
            'operations_groups': {operation_type.value: LevenshteinOperationGroup(operation_type) for operation_type
                                  in LevenshteinOperation.Type}
        }

        # Populate backtraces
        i = len(operation_matrix) - 1
        j = len(operation_matrix[0]) - 1
        csv_lines = list()
        while i > 0 or j > 0:
            operation = operation_matrix[i][j]
            if operation.type == LevenshteinOperation.Type.CORRECT:
                backtrack_key = 'num_cor'
                i -= 1
                j -= 1
            elif operation.type == LevenshteinOperation.Type.SUBSTITUTION:
                backtrack_key = 'num_sub'
                i -= 1
                j -= 1
            elif operation.type == LevenshteinOperation.Type.INSERTION:
                backtrack_key = 'num_ins'
                j -= 1
            elif operation.type == LevenshteinOperation.Type.DELETION:
                backtrack_key = 'num_del'
                i -= 1
            else:
                raise ValueError('Operation type {} not valid'.format(operation.type))

            # Populate overall backtrace
            overall_backtrace['totals'][backtrack_key] += 1
            if operation.type != LevenshteinOperation.Type.INSERTION:
                overall_backtrace['totals']['ref_len'] += 1
                overall_backtrace['totals']['hyp_len'] += 1
            overall_backtrace['operations_groups'][operation.type.value].add(operation)
            operation_events = operation.reference_word.events
            if not operation_events:
                # Populate no event tags backtrace
                no_event_tags_backtrace['totals'][backtrack_key] += 1
                if operation.type != LevenshteinOperation.Type.INSERTION:
                    no_event_tags_backtrace['totals']['ref_len'] += 1
                    no_event_tags_backtrace['totals']['hyp_len'] += 1
                no_event_tags_backtrace['operations_groups'][operation.type.value].add(operation)
            else:
                # Populate event tags backtrace: increment 'all' key once then iterate over all events
                event_tags_backtrace['all']['totals'][backtrack_key] += 1
                if operation.type != LevenshteinOperation.Type.INSERTION:
                    event_tags_backtrace['all']['totals']['ref_len'] += 1
                    event_tags_backtrace['all']['totals']['hyp_len'] += 1
                event_tags_backtrace['all']['operations_groups'][operation.type.value].add(operation)
                for operation_event in operation_events:
                    event_tags_backtrace[operation_event.type]['totals'][backtrack_key] += 1
                    if operation.type != LevenshteinOperation.Type.INSERTION:
                        event_tags_backtrace[operation_event.type]['totals']['ref_len'] += 1
                        event_tags_backtrace[operation_event.type]['totals']['hyp_len'] += 1
                    event_tags_backtrace[operation_event.type]['operations_groups'][operation.type.value].add(operation)
            # Populate CSV lines
            csv_lines.append(self._get_operation_csv_row(operation))

        # Build backtraces dictionary
        backtraces_dictionary = {
            'overall_backtrace': overall_backtrace,
            'event_tags_backtrace': event_tags_backtrace,
            'no_event_tags_backtrace': no_event_tags_backtrace
        }

        return backtraces_dictionary, list(reversed(csv_lines))

    def _compile_operation_matrix(self, original_reference_words: [CanonicalToken],
                                  filtered_reference_words: [CanonicalToken],
                                  hypothesis_words: [CanonicalToken]) -> [[LevenshteinOperation]]:
        """ TODO - Function DOC """

        # Operation matrix initialization
        op_matrix_rows_num = len(filtered_reference_words) + 1
        op_matrix_cols_num = len(hypothesis_words) + 1
        op_matrix = np.array([[LevenshteinOperation() for _ in range(op_matrix_cols_num)]
                              for _ in range(op_matrix_rows_num)])

        # Compilation
        # First column represents the case where we achieve zero hypothesis words by deleting all reference words.
        for i in range(1, op_matrix_rows_num):
            reference_word = self._get_reference_word(original_reference_words[i - 1], filtered_reference_words[i - 1],
                                                      LevenshteinOperation.Type.DELETION)
            op_matrix[i][0] = LevenshteinOperation(reference_word=reference_word,
                                                   hypothesis_word=CanonicalToken(word=None),
                                                   operation_type=LevenshteinOperation.Type.DELETION,
                                                   operation_cost=LevenshteinOperation.Penalty.DELETION.value * i)
        # First row represents the case where we achieve the hypothesis by inserting all hypothesis words into a
        # zero-length reference.
        for j in range(1, op_matrix_cols_num):
            reference_word = CanonicalToken(word=None) if not original_reference_words else original_reference_words[0]
            op_matrix[0][j] = LevenshteinOperation(reference_word=reference_word,
                                                   hypothesis_word=hypothesis_words[j - 1],
                                                   operation_type=LevenshteinOperation.Type.INSERTION,
                                                   operation_cost=LevenshteinOperation.Penalty.INSERTION.value * j)
        # Levenshtein distance minimization
        for i in range(1, op_matrix_rows_num):
            for j in range(1, op_matrix_cols_num):
                if filtered_reference_words[i - 1].word == hypothesis_words[j - 1].word:
                    operation_type = LevenshteinOperation.Type.CORRECT
                    operation_cost = op_matrix[i - 1][j - 1].cost
                    reference_word = filtered_reference_words[i - 1]
                    hypothesis_word = hypothesis_words[j - 1]
                else:
                    substitution_cost = op_matrix[i - 1][j - 1].cost + LevenshteinOperation.Penalty.SUBSTITUTION.value
                    insertion_cost = op_matrix[i][j - 1].cost + LevenshteinOperation.Penalty.INSERTION.value
                    deletion_cost = op_matrix[i - 1][j].cost + LevenshteinOperation.Penalty.DELETION.value
                    operation_cost = min(substitution_cost, insertion_cost, deletion_cost)
                    # Order of case is important here: if there's an equal cost we always prefer insertions/deletions
                    # to substitutions
                    if operation_cost == insertion_cost:
                        operation_type = LevenshteinOperation.Type.INSERTION
                        hypothesis_word = hypothesis_words[j - 1]
                    elif operation_cost == deletion_cost:
                        operation_type = LevenshteinOperation.Type.DELETION
                        hypothesis_word = CanonicalToken(word=None)
                    else:
                        operation_type = LevenshteinOperation.Type.SUBSTITUTION
                        hypothesis_word = hypothesis_words[j - 1]
                    reference_word = self._get_reference_word(original_reference_words[i - 1],
                                                              filtered_reference_words[i - 1], operation_type)
                op_matrix[i][j] = LevenshteinOperation(reference_word, hypothesis_word, operation_type, operation_cost)

        return op_matrix

    def _get_backtrace_output_file_path(self, file_name: str) -> str:
        """ TODO - Function DOC """

        return '{}/{}_Backtrace.csv'.format(self._config[Paths.REPORT_OUTPUT_PATH], file_name)

    def _get_metrics_output_file_path(self) -> str:
        """ TODO - Function DOC """

        return '{}/Corpus_Metrics.json'.format(self._config[Paths.REPORT_OUTPUT_PATH])

    @classmethod
    def _get_operation_csv_row(cls, operation: LevenshteinOperation) -> [str]:
        """ TODO - Function DOC """

        csv_word_event_entry = cls._get_word_events_csv_entry(operation.reference_word.events)
        return [operation.type.name[:3], operation.reference_word.word, operation.hypothesis_word.word,
                csv_word_event_entry]

    @classmethod
    def _get_reference_word(cls, original_reference_word: CanonicalToken, filtered_reference_word: CanonicalToken,
                            operation_type: LevenshteinOperation.Type) -> CanonicalToken:
        """ TODO - Function DOC """

        word = None if operation_type == LevenshteinOperation.Type.INSERTION else filtered_reference_word.word
        if original_reference_word.type in cls.CANONICAL_TYPEB_EVENTS:
            events = list(original_reference_word.events) + list(filtered_reference_word.events)
        else:
            events = list(filtered_reference_word.events)
        return CanonicalToken(word=word, events=events)

    @staticmethod
    def _get_word_events_csv_entry(word_events: [CanonicalTokenEvent]) -> str:
        """ TODO - Function DOC """

        csv_word_events = list()
        for word_event in word_events:
            csv_word_event = word_event.type
            csv_word_event_properties = list()
            for word_event_property in word_event.properties:
                csv_word_event_property = '{}={}'.format(word_event_property.key, word_event_property.value)
                csv_word_event_properties.append(csv_word_event_property)
            csv_word_event += '[{}]'.format(';'.join(csv_word_event_properties))
            csv_word_events.append(csv_word_event)
        return ';'.join(csv_word_events)

    @abstractmethod
    def _get_configuration_section(self) -> str:
        """ TODO - Function DOC """

        pass


class GoogleSTTMetrics(DefaultMetrics):

    def _get_configuration_section(self) -> str:
        """ TODO - Function DOC """

        return ConfigSections.GOOGLE_STT


class AWSTranscribeMetrics(DefaultMetrics):

    def _get_configuration_section(self) -> str:
        """ TODO - Function DOC """

        return ConfigSections.AWS_TRANSCRIBE
