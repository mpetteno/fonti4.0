""" Module that contains all necessary constants.

Constants are separated into classes in order to make the module more readable and maintainable.

"""

from pathlib import Path


class ConfigSections:
    """ Constants that indicate the sections present in the main configuration file. """
    
    AWS_TRANSCRIBE = 'AWS_Transcribe'
    AWS_COMPEHEND = 'AWS_Comprehend'
    EVALUATOR = 'Evaluator'
    GOOGLE_STT = 'Google_STT'
    SPEECHES = 'Speeches'
    TEI = 'TEI'
    TOKENIZER = 'Tokenizer'


class Amazon:
    """ Constants related to the AWS Transcribe service. """

    S3_URI_PREFIX = 's3://'
    S3_SERVICE = 's3'
    TRANSCRIBE_SERVICE = 'transcribe'
    TRANSCRIBE_JOB_MAX_TRIES = 'transcribe_job_max_tries'
    REDACTION_OUTPUT = 'redaction_output'
    REDACTION_TYPE = 'redaction_type'
    ALLOW_DEFERRED_EXECUTION = 'allow_deferred_execution'
    DATA_ACCESS_ROLE_ARN = 'data_access_role_arn'
    IDENTIFY_LANGUAGE = 'identify_language'
    LANGUAGE_CODE = 'language_code'
    LANGUAGE_OPTIONS = 'language_options'
    MEDIA_SAMPLE_RATE_HERTZ = 'media_sample_rate_hertz'
    LANGUAGE_MODEL_NAME = 'language_model_name'
    OUTPUT_BUCKET_NAME = 'output_bucket_name'
    OUTPUT_ENCRYPTION_KMS_KEY_ID = 'output_encryption_kms_key_id'
    OUTPUT_KEY_PREFIX = 'output_key_prefix'
    CHANNEL_IDENTIFICATION = 'channel_identification'
    MAX_ALTERNATIVES = 'max_alternatives'
    MAX_SPEAKER_LABELS = 'max_speaker_labels'
    SHOW_ALTERNATIVES = 'show_alternatives'
    SHOW_SPEAKER_LABELS = 'show_speaker_labels'
    VOCABULARY_FILTER_METHOD = 'vocabulary_filter_method'
    VOCABULARY_FILTER_NAME = 'vocabulary_filter_name'
    VOCABULARY_NAME = 'vocabulary_name'
    TRANSCRIPTION_JOB_NAME_PREFIX = 'transcription_job_name_prefix'
    AWS_ACCESS_KEY_ID = 'aws_access_key_id'
    AWS_SECRET_ACCESS_KEY = 'aws_secret_access_key'
    INPUT_BUCKET_NAME = 'input_bucket_name'
    INPUT_KEY_PREFIX = 'input_key_prefix'


class Evaluator:
    """ Constants related to evaluation operations. """

    PUNCTUATION = 'punctuation'
    APOCOPES = 'apocopes'
    DIACRITICS = 'diacritics'
    STOP_WORDS = 'stop_words'
    ELISIONS = 'elisions'


class Google:
    """ Constants related to the Google Speech-to-Text service. """

    GS_URI_PREFIX = 'gs://'
    LOCAL_RECOGNIZE_REQUEST_MB_LIMIT = 10
    ENCODING = 'encoding'
    SAMPLE_RATE_HERTZ = 'sample_rate_hertz'
    AUDIO_CHANNEL_COUNT = 'audio_channel_count'
    ENABLE_SEPARATE_RECOGNITION_PER_CHANNEL = 'enable_separate_recognition_per_channel'
    LANGUAGE_CODE = 'language_code'
    ALTERNATIVE_LANGUAGE_CODES = 'alternative_language_codes'
    MAX_ALTERNATIVES = 'max_alternatives'
    PROFANITY_FILTER = 'profanity_filter'
    ENABLE_WORD_TIME_OFFSETS = 'enable_word_time_offsets'
    ENABLE_WORD_CONFIDENCE = 'enable_word_confidence'
    ENABLE_AUTOMATIC_PUNCTUATION = 'enable_automatic_punctuation'
    ENABLE_SPEAKER_DIARIZATION = 'enable_speaker_diarization'
    MIN_SPEAKER_COUNT = 'min_speaker_count'
    MAX_SPEAKER_COUNT = 'max_speaker_count'
    MODEL = 'model'
    USE_ENHANCED = 'use_enhanced'
    LONG_RECOGNIZE_TIMEOUT = 'long_recognize_timeout'
    INPUT_BUCKET_NAME = 'input_bucket_name'
    INPUT_BLOB_PREFIX = 'input_blob_prefix'
    PROJECT_ID = 'project_id'
    SERVICE_ACCOUNT_JSON_FILE_PATH = 'service_account_json_file_path'


class Paths:
    """ Constants that represent useful file system paths.

     This class use pathlib library to declare the paths.

     """

    ROOT_CONFIG_PATH = Path('../config')
    MAIN_CONFIG_FILE = ROOT_CONFIG_PATH / 'config.ini'
    TRANSCRIPTION_OUTPUT_PATH = 'transcription_output_path'
    CANONICAL_TRANSCRIPTION_OUTPUT_PATH = 'canonical_transcription_output_path'
    TRN_OUTPUT_PATH = 'trn_output_path'
    CTM_OUTPUT_PATH = 'ctm_output_path'
    TXT_OUTPUT_PATH = 'txt_output_path'
    STM_OUTPUT_PATH = 'stm_output_path'
    REPORT_OUTPUT_PATH = 'report_output_path'
    SPEECH_FILES_PATH = 'speech_files_path'
    TEI_FILES_PATH = 'tei_files_path'


class TEI:
    """ Constants related to TEI (Text Encoding Initiative) files. """

    XSD_SCHEMA_PATH = 'xsd_schema_path'
    TEI_NAMESPACES = {
        'tei': 'http://www.tei-c.org/ns/1.0',
        'xml': 'http://www.w3.org/XML/1998/namespace'
    }


class Tokenizer:
    """ Constants related to tokenize operations. """

    LOWERCASE = 'lowercase'
    EXPAND_CONTRACTED_WORDS = 'expand_contracted_words'
    EXPAND_COMPOUND_WORDS = 'expand_compound_words'
    MULTI_SPELLED_WORDS = 'multi_spelled_words'
    NUMBERS_TO_WORD = 'numbers_to_word'
    SPLIT_APOSTROPHES = 'split_apostrophes'


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

