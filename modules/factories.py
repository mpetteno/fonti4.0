""" TODO - Module DOC """

import ast
import collections
import ipywidgets as widgets
from typing import Mapping, Any
from IPython.core.display import display
from modules import tei, utilities
from modules.constants import Colors
from modules.metrics import GoogleSTTMetrics, AWSTranscribeMetrics, MetricsCalculator
from modules.canonicalizers import TEIFileCanonicalizer, GoogleSTTCanonicalizer, \
    AWSTranscribeCanonicalizer


class WidgetFactory:
    """ TODO - Class DOC """

    computation_configuration = {
        'corpus': {
            'all': {
                'value': True,
                'disabled': False
            },
            'FCINI002a': {
                'value': True,
                'disabled': False
            },
            'FCINI002b': {
                'value': True,
                'disabled': False
            },
            'FCINI003a': {
                'value': True,
                'disabled': False
            },
            'FCINI003b': {
                'value': True,
                'disabled': False
            },
            'FCINI004a': {
                'value': True,
                'disabled': False
            },
            'FCINI004b': {
                'value': True,
                'disabled': False
            },
            'FCINI005a': {
                'value': True,
                'disabled': False
            },
            'FCINI005b': {
                'value': True,
                'disabled': False
            }
        },
        'tokenizer': {
            'all': {
                'value': False,
                'disabled': False
            },
            'lowercase': {
                'value': True,
                'disabled': False
            },
            'split_apostrophes': {
                'value': True,
                'disabled': False
            },
            'numbers_to_word': {
                'value': False,
                'disabled': False
            },
            'expand_contracted_words': {
                'value': False,
                'disabled': True
            },
            'expand_compound_words': {
                'value': False,
                'disabled': True
            },
            'multi_spelled_words': {
                'value': False,
                'disabled': True
            }
        },
        'evaluation_rules': {
            'all': {
                'value': False,
                'disabled': False
            },
            'punctuation': {
                'value': False,
                'disabled': False
            },
            'apocopes': {
                'value': True,
                'disabled': True
            },
            'diacritics': {
                'value': True,
                'disabled': True
            },
            'stop_words': {
                'value': True,
                'disabled': True
            },
            'elisions': {
                'value': True,
                'disabled': True
            }
        }
    }
    results_configuration = {
        'files': collections.defaultdict(),
        'languages': collections.defaultdict(),
        'audio_notes': collections.defaultdict(),
        'event_tags': collections.defaultdict()
    }
    results_scope = None
    google_stt_metrics = None
    aws_transcribe_metrics = None
    result_widget = None
    event_tags_conf_widget = None
    results_conf_widget = None

    @staticmethod
    def computation_widget() -> widgets.Accordion:
        """ TODO - Function DOC """

        def compute_metrics(change):
            """ TODO - Function DOC """

            # Delete previous result widget and clear previous output
            if WidgetFactory.result_widget:
                WidgetFactory.result_widget.close()
                del WidgetFactory.result_widget
            compute_metrics_output.clear_output()
            # Get configurations
            corpus_configuration = WidgetFactory.computation_configuration['corpus']
            corpus_files = list(file_name for file_name, file_name_properties in corpus_configuration.items()
                                if file_name_properties['value'] and file_name != 'all')
            tokenizer_configuration = dict({key: properties['value'] for key, properties in
                                            WidgetFactory.computation_configuration['tokenizer'].items()})
            evaluator_configuration = dict({key: properties['value'] for key, properties in
                                            WidgetFactory.computation_configuration['evaluation_rules'].items()})
            paths = utilities.get_paths_for_file_names(corpus_files)
            # Convert transcription files to canonical format
            with compute_metrics_output:
                print('{}Converting transcription files to canonical format...{}'.format(Colors.OKGREEN, Colors.ENDC))
                for tei_reference_file_path, google_transcription_files_path, aws_transcription_files_path in zip(
                        paths['tei_reference_file_paths'], paths['google_transcription_files_paths'],
                        paths['aws_transcription_files_paths']):
                    tei_file = tei.TEIFile(tei_reference_file_path)
                    TEIFileCanonicalizer(tei_reference_file_path, tei_file, tokenizer_configuration).canonicalize()
                    GoogleSTTCanonicalizer(google_transcription_files_path, tei_file,
                                           tokenizer_configuration).canonicalize()
                    AWSTranscribeCanonicalizer(aws_transcription_files_path, tei_file,
                                               tokenizer_configuration).canonicalize()
            # Compute metrics
            with compute_metrics_output:
                print('{}Computing Google Speech-to-Text metrics...{}'.format(Colors.OKGREEN, Colors.ENDC))
                WidgetFactory.google_stt_metrics = GoogleSTTMetrics(paths['tei_canonical_file_paths'],
                                                                    paths['google_canonical_file_paths'],
                                                                    evaluator_configuration).metrics()
            with compute_metrics_output:
                print('{}Computing AWS Transcribe metrics...{}'.format(Colors.OKGREEN, Colors.ENDC))
                WidgetFactory.aws_transcribe_metrics = AWSTranscribeMetrics(paths['tei_canonical_file_paths'],
                                                                            paths['aws_canonical_file_paths'],
                                                                            evaluator_configuration).metrics()
            # Initialize results configuration
            for key in WidgetFactory.results_configuration.keys():
                if key != 'event_tags':
                    WidgetFactory.results_configuration[key]['all'] = {
                        'value': True,
                        'disabled': False
                    }
                for name in WidgetFactory.google_stt_metrics[key].keys():
                    WidgetFactory.results_configuration[key][name] = {
                        'value': True,
                        'disabled': False
                    }
                for name in WidgetFactory.aws_transcribe_metrics[key].keys():
                    WidgetFactory.results_configuration[key][name] = {
                        'value': True,
                        'disabled': False
                    }
            # Update widgets
            computation_accordion.selected_index = None
            with compute_metrics_output:
                print('{}Done.{}'.format(Colors.OKGREEN, Colors.ENDC))
            WidgetFactory.result_widget = WidgetFactory.results_widget()
            display(WidgetFactory.result_widget)

        corpus_conf = WidgetFactory._checkbox_computation_widget('Corpus', format_labels=False)
        tokenizer_conf = WidgetFactory._checkbox_computation_widget('Tokenizer')
        evaluator_conf = WidgetFactory._checkbox_computation_widget('Evaluation Rules')
        configuration_grid = widgets.VBox([corpus_conf, tokenizer_conf, evaluator_conf])
        compute_metrics_button = widgets.Button(description="Compute Metrics", layout=widgets.Layout(margin='10px'))
        compute_metrics_button.on_click(compute_metrics)
        compute_metrics_output = widgets.Output(layout=widgets.Layout(margin='10px'))
        compute_metrics_box = widgets.HBox([compute_metrics_button, compute_metrics_output])
        computation_accordion = widgets.Accordion(children=[widgets.VBox([configuration_grid, compute_metrics_box])])
        computation_accordion.set_title(0, 'Computation')
        return computation_accordion

    @staticmethod
    def results_widget() -> widgets.Accordion:
        """ TODO - Function DOC """

        def update_results(change):
            """ TODO - Function DOC """

            def get_selected_items(result_configuration_key: str) -> [str]:
                """ TODO - Function DOC """

                result_configuration = WidgetFactory.results_configuration[result_configuration_key]
                return list(key for key, properties in result_configuration.items() if properties['value']
                            and key != 'all')

            # Clear previous output
            update_results_output.clear_output()

            # Get selected results configurations
            selected_files = get_selected_items('files')
            selected_languages = get_selected_items('languages')
            selected_audio_notes = get_selected_items('audio_notes')
            selected_scope = WidgetFactory.results_scope
            if WidgetFactory.results_configuration['event_tags']['all']['value']:
                selected_event_tags = ['all']
            else:
                selected_event_tags = get_selected_items('event_tags')

            # Files, Languages and Audio Notes and Scope configurations can't be empty
            if not selected_files or not selected_languages or not selected_audio_notes or not selected_scope:
                with update_results_output:
                    print('{}Update results failed. Files, Languages, Audio Notes and Scope can\'t be empty.{}'.
                          format(Colors.FAIL, Colors.ENDC))
                return

            # If selected scope is 'event_tags' Event Tags configuration can't be empty
            if selected_scope == 'event_tags' and not selected_event_tags:
                with update_results_output:
                    print('{}Update results failed. Event Tags can\'t be empty.{}'.
                          format(Colors.FAIL, Colors.ENDC))
                return

            # Get result from computed metrics
            google_results = list()
            aws_results = list()
            for file in selected_files:
                current_google_file = WidgetFactory.google_stt_metrics['files'][file]
                current_aws_file = WidgetFactory.aws_transcribe_metrics['files'][file]
                for language in selected_languages:
                    current_google_file_language = current_google_file['languages'][language]
                    current_aws_file_language = current_aws_file['languages'][language]
                    for audio_note in selected_audio_notes:
                        google_audio_note = current_google_file_language['audio_notes'][audio_note] \
                            if current_google_file_language else None
                        aws_audio_note = current_aws_file_language['audio_notes'][audio_note] \
                            if current_aws_file_language else None
                        if selected_scope == 'event_tags':
                            for event_tags in selected_event_tags:
                                try:
                                    google_results.append(google_audio_note['event_tags'][event_tags]
                                                          if google_audio_note else None)
                                    aws_results.append(aws_audio_note['event_tags'][event_tags]
                                                       if aws_audio_note else None)
                                except KeyError:
                                    continue
                        else:
                            try:
                                google_results.append(google_audio_note[selected_scope] if google_audio_note else None)
                                aws_results.append(aws_audio_note[selected_scope] if aws_audio_note else None)
                            except KeyError:
                                with update_results_output:
                                    print('{}{} {} {}{}'.format(file, language, audio_note, Colors.FAIL, Colors.ENDC))
            google_metrics = collections.defaultdict()
            google_results = list(filter(None, google_results))
            if google_results:
                google_metrics.update(MetricsCalculator.compute_totals_metrics(google_results))
                google_metrics.update(MetricsCalculator.compute_operations_groups(google_results))
            aws_metrics = collections.defaultdict()
            aws_results = list(filter(None, aws_results))
            if aws_results:
                aws_metrics.update(MetricsCalculator.compute_totals_metrics(aws_results))
                aws_metrics.update(MetricsCalculator.compute_operations_groups(aws_results))

            # Update widgets
            google_stt_grid.top_left = WidgetFactory._metrics_widget(google_metrics)
            aws_transcribe_grid.top_left = WidgetFactory._metrics_widget(aws_metrics)

            with update_results_output:
                print('{}Results updated.{}'.format(Colors.OKGREEN, Colors.ENDC))

        # Google STT accordion
        google_stt_grid = widgets.TwoByTwoLayout()
        google_accordion_layout = widgets.Layout(margin='5px 0 5px 0')
        google_stt_metrics_accordion = widgets.Accordion(children=[google_stt_grid], layout=google_accordion_layout)
        google_stt_metrics_accordion.set_title(0, 'Google Speech-to-Text')
        google_stt_metrics_accordion.selected_index = 0
        # AWS accordion
        aws_transcribe_grid = widgets.TwoByTwoLayout()
        aws_accordion_layout = widgets.Layout(margin='5px 0 5px 0')
        aws_transcribe_metrics_accordion = widgets.Accordion(children=[aws_transcribe_grid],
                                                             layout=aws_accordion_layout)
        aws_transcribe_metrics_accordion.set_title(0, 'AWS Transcribe')
        aws_transcribe_metrics_accordion.selected_index = 0
        # Visualization Grid
        files_conf = WidgetFactory._checkbox_results_widget('Files', format_labels=False)
        languages_conf = WidgetFactory._checkbox_results_widget('Languages', format_labels=False)
        audio_notes_conf = WidgetFactory._checkbox_results_widget('Audio Notes')
        scope_conf = WidgetFactory._checkbox_scope_widget('Scope')
        update_results_button = widgets.Button(description="Update Results", layout=widgets.Layout(margin='10px'))
        update_results_button.on_click(update_results)
        update_results_output = widgets.Output(layout=widgets.Layout(margin='10px'))
        update_results_box = widgets.HBox([update_results_button, update_results_output])
        update_results_button.click()
        WidgetFactory.event_tags_conf_widget = WidgetFactory._checkbox_results_widget('Event Tags')
        WidgetFactory.results_conf_widget = widgets.VBox([files_conf, languages_conf, audio_notes_conf, scope_conf,
                                                          update_results_box],
                                                         layout=widgets.Layout(margin='0 0 35px 0'))
        # Metrics accordion
        metrics_accordion = widgets.Accordion(children=[widgets.VBox([WidgetFactory.results_conf_widget,
                                                                      google_stt_metrics_accordion,
                                                                      aws_transcribe_metrics_accordion])])
        metrics_accordion.set_title(0, 'Results')
        return metrics_accordion

    @staticmethod
    def style_widget() -> widgets.HTML:
        """ TODO - Function DOC """

        return widgets.HTML("<style>.bold_label { font-weight:bold }</style>")

    @staticmethod
    def _checkbox_computation_widget(widget_label: str, format_labels=True) -> widgets.Box:
        """ TODO - Function DOC """

        return WidgetFactory._checkbox_configuration_widget(widget_label, WidgetFactory.computation_configuration,
                                                            format_labels)

    @staticmethod
    def _checkbox_results_widget(widget_label: str, format_labels=True) -> widgets.Box:
        """ TODO - Function DOC """

        return WidgetFactory._checkbox_configuration_widget(widget_label, WidgetFactory.results_configuration,
                                                            format_labels)

    @staticmethod
    def _checkbox_scope_widget(widget_label: str) -> widgets.Box:
        """ TODO - Function DOC """

        def checkbox_changed(change):
            """ TODO - Function DOC """

            new_value = change['new']
            event_owner = change['owner']

            # Update selected scope
            if not new_value:
                WidgetFactory.results_scope = None
            elif event_owner.description == 'Overall text':
                WidgetFactory.results_scope = 'overall_text'
            elif event_owner.description == 'Without event tags text':
                WidgetFactory.results_scope = 'without_tags_text'
            else:
                WidgetFactory.results_scope = 'event_tags'

            # Checkboxes are mutually exclusive
            for current_checkbox in checkboxes:
                if event_owner.description != current_checkbox.description:
                    current_checkbox.unobserve(checkbox_changed, names='value')
                    current_checkbox.value = False
                    current_checkbox.observe(checkbox_changed, names='value')

            # If event tags checkbox is selected show event tags filters widget, hide it otherwise
            new_children = list(WidgetFactory.results_conf_widget.children)
            if event_owner.description == 'Only event tags text':
                if new_value:
                    new_children.insert(len(new_children) - 1, WidgetFactory.event_tags_conf_widget)
                else:
                    new_children.remove(WidgetFactory.event_tags_conf_widget)
            else:
                try:
                    new_children.remove(WidgetFactory.event_tags_conf_widget)
                except ValueError:
                    pass
            WidgetFactory.results_conf_widget.children = new_children

        # Widget label container
        widget_label_box = widgets.HBox([widgets.Label(widget_label).add_class('bold_label')],
                                        layout=widgets.Layout(flex='0 0 15%', margin='0 0 0 10px', align_self='center'))

        # Widget checkboxes container
        overall_text_checkbox = widgets.Checkbox(True, description='Overall text', indent=False, disabled=False)
        WidgetFactory.results_scope = 'overall_text'
        without_event_tags_text_checkbox = widgets.Checkbox(False, description='Without event tags text', indent=False,
                                                            disabled=False)
        only_event_tags_text_checkbox = widgets.Checkbox(False, description='Only event tags text', indent=False,
                                                         disabled=False)
        checkboxes = [overall_text_checkbox, without_event_tags_text_checkbox, only_event_tags_text_checkbox]
        for checkbox in checkboxes:
            checkbox.observe(checkbox_changed, names='value')
        widget_checkboxes_box_layout = widgets.Layout(grid_template_columns="repeat(3, 250px)", flex='auto',
                                                      overflow='hidden', margin='10px 0px 5px 0px')
        widget_checkboxes_box = widgets.GridBox(checkboxes, layout=widget_checkboxes_box_layout)

        # Widget container
        widget_box_layout = widgets.Layout(border='1px solid', margin='10px')
        widget_box = widgets.HBox([widget_label_box, widget_checkboxes_box], layout=widget_box_layout)
        return widget_box

    @staticmethod
    def _checkbox_configuration_widget(widget_label: str, configuration: Mapping[str, Any], format_labels=True) \
            -> widgets.Box:
        """ TODO - Function DOC """

        def checkbox_changed(change):
            """ TODO - Function DOC """

            new_value = change['new']
            event_owner = change['owner']

            if event_owner.description == 'All':
                # Handle all-checkbox value changed
                for index in range(1, len(checkboxes)):
                    current_checkbox = checkboxes[index]
                    if not current_checkbox.disabled:
                        current_checkbox_conf_key = current_checkbox.description.replace(' ', '_').lower() \
                            if format_labels else current_checkbox.description
                        configuration[component_key][current_checkbox_conf_key]['value'] = new_value
                        current_checkbox.value = new_value
            else:
                configuration_key = event_owner.description.replace(' ', '_').lower() if format_labels \
                    else event_owner.description
                configuration[component_key][configuration_key]['value'] = new_value
                # Change all-checkbox value if necessary
                if checkboxes[0].description == 'All':
                    select_all_checkbox = checkboxes[0]
                    new_all_value = True
                    for index in range(1, len(checkboxes)):
                        current_checkbox = checkboxes[index]
                        if not current_checkbox.disabled and not current_checkbox.value:
                            new_all_value = False
                            break
                    # Workaround to not trigger this callback again on all-checkbox value change.
                    # See https://github.com/jupyter-widgets/ipywidgets/issues/2230
                    select_all_checkbox.unobserve(checkbox_changed, names='value')
                    configuration[component_key]['all']['value'] = new_all_value
                    select_all_checkbox.value = new_all_value
                    select_all_checkbox.observe(checkbox_changed, names='value')

        # Widget label container
        component_key = widget_label.replace(' ', '_').lower()
        widget_configuration_dictionary = configuration[component_key]
        widget_label_box = widgets.HBox([widgets.Label(widget_label).add_class('bold_label')],
                                        layout=widgets.Layout(flex='0 0 15%', margin='0 0 0 10px', align_self='center'))

        # Widget checkboxes container
        checkboxes = list()
        for widget_configuration_key, widget_configuration_properties in widget_configuration_dictionary.items():
            if widget_configuration_key == 'all':
                checkbox_label = 'All'
            else:
                checkbox_label = widget_configuration_key.replace('_', ' ').title() if format_labels \
                    else widget_configuration_key
            checkbox = widgets.Checkbox(widget_configuration_properties['value'], description=checkbox_label,
                                        indent=False, disabled=widget_configuration_properties['disabled'])
            checkbox.observe(checkbox_changed, names='value')
            checkboxes.append(checkbox)
        widget_checkboxes_box_layout = widgets.Layout(grid_template_columns="repeat(3, 250px)", flex='auto',
                                                      overflow='hidden')
        widget_checkboxes_box = widgets.GridBox(checkboxes, layout=widget_checkboxes_box_layout)

        # Widget container
        widget_box_layout = widgets.Layout(border='1px solid', margin='10px')
        widget_box = widgets.HBox([widget_label_box, widget_checkboxes_box], layout=widget_box_layout)
        return widget_box

    @staticmethod
    def _metrics_widget(metrics: Mapping[str, Any]) -> widgets.Box:
        """ TODO - Function DOC """

        def metric_box(label: str, value: str):
            """ TODO - Function DOC """

            labels_layout = widgets.Layout(margin='5px')
            metric_label = widgets.Label(label, layout=labels_layout)
            value_label = widgets.Label(value, layout=labels_layout)
            box_layout = widgets.Layout(border='1px solid', margin='10px', justify_content='center')
            return widgets.HBox([metric_label, value_label], layout=box_layout)

        def update_operations_groups_output(change):
            """ TODO - Function DOC """

            operations_groups_output.clear_output()
            selected_operation_type = operation_type_dropdown.value
            if operation_count_dropdown.value == 'All':
                count_greater_than_dropdown.disabled = False
                count_greater_than = count_greater_than_dropdown.value
                selected_operations = list((key, value) for key, value in operations_groups[selected_operation_type]
                                           .items() if value > count_greater_than)[:50]
            else:
                count_greater_than_dropdown.disabled = True
                selected_operation_type = operation_type_dropdown.value
                selected_count = operation_count_dropdown.value
                selected_operations = list(operations_groups[selected_operation_type].items())[:selected_count]
            for index in range(0, len(selected_operations)):
                operation, count = selected_operations[index]
                with operations_groups_output:
                    print('{: >5}: {: >5} -> {}'.format(index + 1, count, ast.literal_eval(operation)))

        # Handle empty metrics
        if not any(metrics):
            empty_metrics_output = widgets.Output(layout=widgets.Layout(margin='10px'))
            with empty_metrics_output:
                print('{}Empty results for selected configuration.{}'.format(Colors.WARNING, Colors.ENDC))
            return widgets.VBox([empty_metrics_output])

        # Totals
        totals_metrics = metrics['totals']
        totals_label = widgets.Label('Totals', layout=widgets.Layout(margin='10px 0px 0px 10px')) \
            .add_class('bold_label')
        totals_metrics_box = widgets.Box([metric_box('COR', '{}'.format(str(totals_metrics['cor']))),
                                          metric_box('SUB', '{}'.format(str(totals_metrics['sub']))),
                                          metric_box('INS', '{}'.format(str(totals_metrics['ins']))),
                                          metric_box('DEL', '{}'.format(str(totals_metrics['del']))),
                                          metric_box('WER', '{}%'.format(str(round(totals_metrics['wer'] * 100, 2)))),
                                          metric_box('MER', '{}%'.format(str(round(totals_metrics['mer'] * 100, 2)))),
                                          metric_box('WIL', '{}%'.format(str(round(totals_metrics['wil'] * 100, 2)))),
                                          metric_box('WIP', '{}%'.format(str(round(totals_metrics['wip'] * 100, 2))))],
                                         layout=widgets.Layout(justify_content='space-between'))
        totals_box = widgets.VBox([totals_label, totals_metrics_box], layout=widgets.Layout(margin='10px 0px'))

        # Operations groups
        operations_groups = metrics['operations_groups']
        operations_groups_label = widgets.Label('Operations Groups', layout=widgets.Layout(margin='10px 0px 0px 10px')) \
            .add_class('bold_label')
        operation_type_dropdown_options = list(key for key, value in operations_groups.items() if value)
        operation_type_dropdown = widgets.Dropdown(
            options=operation_type_dropdown_options,
            value=operation_type_dropdown_options[0],
            description='Type:',
            disabled=False,
            layout=widgets.Layout(width='max-content', margin='10px 60px 10px 10px')
        )
        operation_type_dropdown.observe(update_operations_groups_output, names='value')
        operation_count_dropdown = widgets.Dropdown(
            options=[('All', 'All'), ('10', 10), ('20', 20), ('30', 30)],
            description='Top:',
            disabled=False,
            layout=widgets.Layout(width='max-content', margin='10px 60px 10px 10px')
        )
        operation_count_dropdown.observe(update_operations_groups_output, names='value')
        count_greater_than_dropdown = widgets.Dropdown(
            options=[('> 1', 1), ('> 2', 2), ('> 3', 3), ('> 4', 4)],
            value=2,
            description='Count:',
            disabled=True,
            layout=widgets.Layout(width='max-content', margin='10px 60px 10px 10px')
        )
        count_greater_than_dropdown.observe(update_operations_groups_output, names='value')
        operations_groups_dropdown_box = widgets.HBox([operation_type_dropdown, operation_count_dropdown,
                                                       count_greater_than_dropdown])
        operations_groups_output = widgets.Output(layout=widgets.Layout(margin='10px', padding='0px 25px'))
        operation_count_dropdown.value = 10
        operations_groups_box = widgets.VBox([operations_groups_label, operations_groups_dropdown_box,
                                              operations_groups_output], layout=widgets.Layout(margin='10px 0px'))

        return widgets.VBox([totals_box, operations_groups_box])
