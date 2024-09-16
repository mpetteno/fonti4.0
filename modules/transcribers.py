""" TODO - Module DOC """

import proto
import boto3
import time
from abc import ABC, abstractmethod
from google.cloud import speech_v1p1beta1 as speech, storage
from modules import utilities
from modules.constants import ConfigSections, Google, Amazon, Paths


class TranscribeService(ABC):
    """ TODO - Class DOC """

    def __init__(self, speech_file_location: str):
        self._speech_file_location = speech_file_location

    def transcribe(self) -> None:
        """ TODO - Function DOC """

        json_response = self._transcribe_internal()
        self._save_transcription_file(json_response)

    def _get_output_file_name(self):
        """ TODO - Function DOC """

        language_code = self._get_language_code()
        speech_file_name = utilities.get_file_name(self._speech_file_location)
        return speech_file_name + ('_' + language_code if language_code else '') + '.json'

    def _save_transcription_file(self, json_response: str) -> None:
        """Saves the transcript in JSON format to the path specified in the main configuration file, if set, otherwise
        in the current working directory. Transcript file's name is automatically extracted from given location.

        Args:
            json_response (str):
                The response to the transcription request in JSON format.

        """

        print('Saving transcription response...')
        output_file_path = self._get_output_file_path() + '/' + self._get_output_file_name()
        utilities.write_local_file(output_file_path, json_response)
        print(f'Transcription response saved to {output_file_path}.')

    @abstractmethod
    def _get_language_code(self) -> str:
        """ TODO - Function DOC """

        pass

    @abstractmethod
    def _get_output_file_path(self) -> str:
        """ TODO - Function DOC """

        pass

    @abstractmethod
    def _transcribe_internal(self) -> str:
        """ TODO - Function DOC """

        pass


class GoogleSTTTranscribeService(TranscribeService):
    """ TODO - Module dedicated to Google Cloud Speech-To-Text (STT) service

    The module contains all the methods useful for transcribing an audio file with Google Cloud STT service.
    Google STT service configuration is loaded from the main configuration file; the description of each available
    option can be found here: https://cloud.google.com/speech-to-text/docs/reference/rest/v1/RecognitionConfig

        Typical usage example:

        from modules import google_stt
        google_stt.transcribe_speech('../tests/speeches/FCINI002b_cut_48_16_small.wav')
        google_stt.transcribe_speech('gs://fonti40_cini/speeches/FCINI002b_cut_48_16_small.wav')

    """

    def __init__(self, speech_file_location: str):
        super().__init__(speech_file_location)

        # Load configuration file
        config_file = utilities.load_configuration_section(ConfigSections.GOOGLE_STT)
        self._config_file = config_file

        # Instantiates clients
        project_id = config_file.get(Google.PROJECT_ID)
        service_account_json_file = config_file.get(Google.SERVICE_ACCOUNT_JSON_FILE_PATH)
        if service_account_json_file:
            self._speech_client = speech.SpeechClient.from_service_account_json(service_account_json_file)
            self._storage_client = storage.Client.from_service_account_json(service_account_json_file)
        else:
            self._speech_client = speech.SpeechClient()
            self._storage_client = storage.Client(project=project_id)

        # Set up recognition configuration
        self._recognition_config = self._init_recognize_config()

    def _transcribe_internal(self) -> str:
        """TODO - Transcribe a file with Google STT service.
        The method automatically decides between synchronous and asynchronous transcription of the file: the former is
        only supported if the audio file lasts less than a minute.
        If the speech file location is a path to a local file, if the file is larger than 10MB, it will be automatically
        uploaded to the GCS bucket specified in the main configuration file.
        The transcript is saved to the path specified in the main configuration file, if set, otherwise in the current
        working directory..
        """

        if utilities.is_gcs_uri(self._speech_file_location):
            audio = speech.RecognitionAudio(uri=self._speech_file_location)
        else:
            local_speech_file_size = utilities.get_local_file_size(self._speech_file_location)
            if local_speech_file_size < Google.LOCAL_RECOGNIZE_REQUEST_MB_LIMIT:
                local_speech_file_content = utilities.read_local_file(self._speech_file_location, mode='rb')
                audio = speech.RecognitionAudio(content=local_speech_file_content)
            else:
                print(f'Local file {self._speech_file_location} too large.')
                speech_file_uri = self._upload_local_speech_file_to_gcs_bucket()
                audio = speech.RecognitionAudio(uri=speech_file_uri)

        # TODO - Check local audio file length.
        #  If it is less then 1 minute we should perform synchronous recognition.
        long_recognize_response = self._asynchronous_recognition(audio)
        return proto.Message.to_json(long_recognize_response)

    def _get_language_code(self) -> str:
        """ TODO - Function DOC """

        return self._recognition_config.language_code

    def _get_output_file_path(self) -> str:
        """ TODO - Function DOC """

        return self._config_file.get(Paths.TRANSCRIPTION_OUTPUT_PATH)

    def _init_recognize_config(self) -> speech.RecognitionConfig:
        """ TODO - Function DOC """

        # Set up metadata
        recognition_metadata = speech.RecognitionMetadata(
            interaction_type=speech.RecognitionMetadata.InteractionType.DISCUSSION
        )

        # Set up speech contexts
        speech_contexts = [speech.SpeechContext()]

        # Set up speech adaptation
        speech_adaptation = speech.SpeechAdaptation()

        # Set up diarization configuration
        diarization_config = speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=self._config_file.getboolean(Google.ENABLE_SPEAKER_DIARIZATION),
            min_speaker_count=int(self._config_file.get(Google.MIN_SPEAKER_COUNT) or 2),
            max_speaker_count=int(self._config_file.get(Google.MAX_SPEAKER_COUNT) or 6)
        )

        # Set up recognition configuration
        language_code = self._config_file.get(Google.LANGUAGE_CODE)
        alternative_language_codes = self._config_file.get(Google.ALTERNATIVE_LANGUAGE_CODES)
        return speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding[self._config_file.get(Google.ENCODING)],
            sample_rate_hertz=int(self._config_file.get(Google.SAMPLE_RATE_HERTZ) or 0),
            audio_channel_count=int(self._config_file.get(Google.AUDIO_CHANNEL_COUNT) or 0),
            enable_separate_recognition_per_channel=self._config_file.getboolean(
                Google.ENABLE_SEPARATE_RECOGNITION_PER_CHANNEL),
            language_code=language_code,
            alternative_language_codes=alternative_language_codes.split(',') if alternative_language_codes else [],
            max_alternatives=int(self._config_file.get(Google.MAX_ALTERNATIVES) or 0),
            profanity_filter=self._config_file.getboolean(Google.PROFANITY_FILTER),
            adaptation=speech_adaptation,
            speech_contexts=speech_contexts,
            enable_word_time_offsets=self._config_file.getboolean(Google.ENABLE_WORD_TIME_OFFSETS),
            enable_word_confidence=self._config_file.getboolean(Google.ENABLE_WORD_CONFIDENCE),
            enable_automatic_punctuation=self._config_file.getboolean(Google.ENABLE_AUTOMATIC_PUNCTUATION),
            diarization_config=diarization_config,
            metadata=recognition_metadata,
            model=self._config_file.get(Google.MODEL),
            use_enhanced=self._config_file.getboolean(Google.USE_ENHANCED)
        )

    def _asynchronous_recognition(self, audio: speech.RecognitionAudio) -> speech.LongRunningRecognizeResponse:
        """Asynchronously transcribes the given audio file and waits for the long recognize operation to finish with
        a configurable timeout.

        Args:
            audio (speech.RecognitionAudio):
                The audio to transcribe.

        Returns:
            speech.LongRunningRecognizeResponse:
                The response to the recognition request.

        """

        print('Starting asynchronous recognition job for given audio file...')
        operation = self._speech_client.long_running_recognize(config=self._recognition_config, audio=audio)

        print("Waiting for operation to complete...")
        long_running_recognize_response = operation.result(timeout=int(self._config_file.get(
            Google.LONG_RECOGNIZE_TIMEOUT)))
        print('Asynchronous recognition job completed.')

        return long_running_recognize_response

    def _synchronous_recognition(self, audio: speech.RecognitionAudio) -> speech.RecognizeResponse:
        """Synchronously transcribes the given audio file.

        Args:
            audio (speech.RecognitionAudio):
                The audio to transcribe.

        Returns:
            speech.RecognizeResponse:
                The response to the recognition request.

        """

        print('Starting synchronous recognition job for given audio file...')
        recognize_response = self._speech_client.recognize(config=self._recognition_config, audio=audio)
        print('Synchronous recognition job completed.')

        return recognize_response

    def _upload_local_speech_file_to_gcs_bucket(self) -> str:
        """Uploads a local speech file to the GCS bucket specified in the main configuration file.

        Returns:
            str:
                The GCS URI for the uploaded file

        """

        input_bucket_name = self._config_file.get(Google.INPUT_BUCKET_NAME)
        speech_file_name = utilities.get_file_name_with_extension(self._speech_file_location)
        input_file_blob = self._config_file.get(Google.INPUT_BLOB_PREFIX) + speech_file_name
        input_file_uri = Google.GS_URI_PREFIX + input_bucket_name + '/' + input_file_blob

        print(f'Uploading local file {self._speech_file_location} to {input_file_uri}...')
        bucket = self._storage_client.bucket(input_bucket_name)
        blob = bucket.blob(input_file_blob)
        blob.upload_from_filename(self._speech_file_location)

        return input_file_uri


class AWSTranscribeService(TranscribeService):
    """ TODO - Module dedicated to Amazon Web Services (AWS) transcribe service

    The module contains all the methods useful for transcribing an audio file with AWS Transcribe service.
    AWS Transcribe service configuration is loaded from the main configuration file; the description of each available
    option can be found here: https://docs.aws.amazon.com/transcribe/latest/dg/API_StartTranscriptionJob.html

        Typical usage example:

        from modules import aws_transcribe
        aws_transcribe.transcribe_speech('../tests/speeches/FCINI002b_cut_48_16_small.wav')
        aws_transcribe.transcribe_speech('s3://fonti4.0/speeches/FCINI002b_cut_48_16_small.wav')

    """

    def __init__(self, speech_file_location: str):
        super().__init__(speech_file_location)

        # Load configuration file
        config_file = utilities.load_configuration_section(ConfigSections.AWS_TRANSCRIBE)
        self._config_file = config_file

        # Instantiates clients
        aws_access_key_id = str(config_file.get(Amazon.AWS_ACCESS_KEY_ID)) or None
        aws_secret_access_key = str(config_file.get(Amazon.AWS_SECRET_ACCESS_KEY)) or None
        self._transcribe_client = boto3.client(Amazon.TRANSCRIBE_SERVICE,
                                               aws_access_key_id=aws_access_key_id,
                                               aws_secret_access_key=aws_secret_access_key)
        self._s3_client = boto3.client(Amazon.S3_SERVICE,
                                       aws_access_key_id=aws_access_key_id,
                                       aws_secret_access_key=aws_secret_access_key)

        # Setup transcribe configuration
        transcribe_config = {
            'Settings': {
                'ChannelIdentification': config_file.getboolean(Amazon.CHANNEL_IDENTIFICATION)
            }
        }
        self._transcribe_config = transcribe_config

        # Setup ContentRedaction object if configuration requires it
        redaction_output = config_file.get(Amazon.REDACTION_OUTPUT)
        if redaction_output:
            transcribe_config['ContentRedaction'] = {
                'RedactionOutput': redaction_output,
                'RedactionType': config_file.get(Amazon.REDACTION_TYPE)
            }

        # Setup language identification
        identify_language = config_file.getboolean(Amazon.IDENTIFY_LANGUAGE)
        language_code = config_file.get(Amazon.LANGUAGE_CODE)
        if identify_language:
            transcribe_config['IdentifyLanguage'] = identify_language
            transcribe_config['LanguageOptions'] = config_file.get(Amazon.LANGUAGE_OPTIONS).split(',')
        else:
            transcribe_config['LanguageCode'] = language_code

        # Setup JobExecutionSettings object if configuration requires it
        is_allow_deferred_execution = config_file.get(Amazon.ALLOW_DEFERRED_EXECUTION)
        if is_allow_deferred_execution:
            transcribe_config['JobExecutionSettings'] = {
                'AllowDeferredExecution': is_allow_deferred_execution,
                'DataAccessRoleArn': config_file.get(Amazon.DATA_ACCESS_ROLE_ARN)
            }

        # Setup media format
        transcribe_config['MediaFormat'] = utilities.get_file_format(speech_file_location)

        # Setup media sample rate
        media_sample_rate = int(config_file.get(Amazon.MEDIA_SAMPLE_RATE_HERTZ) or 0)
        if media_sample_rate > 0:
            transcribe_config['MediaSampleRateHertz'] = media_sample_rate

        # Setup ModelSettings object if configuration requires it
        language_model_name = config_file.get(Amazon.LANGUAGE_MODEL_NAME)
        if language_model_name:
            transcribe_config['ModelSettings'] = {
                'LanguageModelName': language_model_name
            }

        # Setup OutputBucketName and OutputKey
        transcribe_config['OutputBucketName'] = config_file.get(Amazon.OUTPUT_BUCKET_NAME)
        transcribe_config['OutputKey'] = config_file.get(Amazon.OUTPUT_KEY_PREFIX) + super()._get_output_file_name()

        # Setup OutputEncryptionKMSKeyId key if configuration requires it
        output_encryption_kms_key_id = config_file.get(Amazon.OUTPUT_ENCRYPTION_KMS_KEY_ID)
        if output_encryption_kms_key_id:
            transcribe_config['OutputEncryptionKMSKeyId'] = output_encryption_kms_key_id

        # Update Settings object if configuration requires to show alternatives on transcription results
        is_show_alternatives = config_file.getboolean(Amazon.SHOW_ALTERNATIVES)
        if is_show_alternatives:
            transcribe_config['Settings'].update(
                {
                    'ShowAlternatives': is_show_alternatives,
                    'MaxAlternatives': int(config_file.get(Amazon.MAX_ALTERNATIVES) or 0)
                }
            )

        # Update Settings object if configuration requires diarization
        is_show_speaker_labels = config_file.getboolean(Amazon.SHOW_SPEAKER_LABELS)
        if is_show_speaker_labels:
            transcribe_config['Settings'].update(
                {
                    'ShowSpeakerLabels': is_show_speaker_labels,
                    'MaxSpeakerLabels': int(config_file.get(Amazon.MAX_SPEAKER_LABELS) or 0)
                }
            )

        # Update Settings object if configuration requires vocabulary filter
        vocabulary_filter_name = config_file.get(Amazon.VOCABULARY_FILTER_NAME)
        if vocabulary_filter_name:
            transcribe_config['Settings'].update(
                {
                    'VocabularyFilterMethod': config_file.get(Amazon.VOCABULARY_FILTER_METHOD),
                    'VocabularyFilterName': vocabulary_filter_name
                }
            )

        # Update Settings object if configuration requires custom vocabulary
        vocabulary_name = config_file.get(Amazon.VOCABULARY_NAME)
        if vocabulary_name:
            transcribe_config['Settings'].update(
                {
                    'VocabularyName': vocabulary_name
                }
            )

        # Setup TranscriptionJobName
        transcribe_config['TranscriptionJobName'] = config_file.get(
            Amazon.TRANSCRIPTION_JOB_NAME_PREFIX) + '_' + utilities.get_file_name(speech_file_location)

    def _transcribe_internal(self) -> None:
        """TODO - Transcribe a file with AWS Transcribe service.
        If the speech file location is a path to a local file, the file will be automatically uploaded to the AWS S3
        bucket specified in the main configuration file.
        The transcript is saved to the path specified in the main configuration file, if set, otherwise in the current
        working directory.
        """

        # Update file to bucket if speech_file_location is a local path
        if utilities.is_s3_uri(self._speech_file_location):
            media_file_uri = self._speech_file_location
        else:
            media_file_uri = self._upload_local_speech_file_to_s3_bucket()

        # Update transcribe configuration
        self._transcribe_config['Media'] = {
            'MediaFileUri': media_file_uri
        }

        self._start_transcription_job()

        self._wait_for_transcription_long_job()

        transcription_result = self._s3_client.get_object(Bucket=self._transcribe_config['OutputBucketName'],
                                                          Key=self._transcribe_config['OutputKey'])
        return transcription_result["Body"].read().decode()

    def _get_language_code(self) -> str:
        """ TODO - Function DOC """

        return self._transcribe_config['LanguageCode']

    def _get_output_file_path(self) -> str:
        """ TODO - Function DOC """

        return self._config_file.get(Paths.TRANSCRIPTION_OUTPUT_PATH)

    def _start_transcription_job(self) -> None:
        """Starts an AWS transcription job.
        The method checks if a job with the given name already exists in AWS Transcribe. If so it will be deleted.
        """

        job_name = self._transcribe_config['TranscriptionJobName']
        print(f'Check if a transcription job with name {job_name} already exists...')
        existing_transcriptions_jobs = self._transcribe_client.list_transcription_jobs()
        is_existing_job = False
        for job in existing_transcriptions_jobs['TranscriptionJobSummaries']:
            if job_name == job['TranscriptionJobName']:
                is_existing_job = True
                self._transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
                break

        if is_existing_job:
            print(f'Existing job with name {job_name} found. Deleting it...')
        else:
            print(f'No existing job with name {job_name} found.')

        print(f'Starting new transcription job {job_name}...')
        self._transcribe_client.start_transcription_job(**self._transcribe_config)

    def _wait_for_transcription_long_job(self) -> None:
        """ Waits for the transcription job to finish with configurable timeout given by: TRANSCRIBE_JOB_MAX_TRIES*10s.
        """

        job_name = self._transcribe_config['TranscriptionJobName']
        max_tries = int(self._config_file.get(Amazon.TRANSCRIBE_JOB_MAX_TRIES) or 60)
        while max_tries > 0:
            max_tries -= 1
            transcription_long_job = self._transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            job_status = transcription_long_job['TranscriptionJob']['TranscriptionJobStatus']
            if job_status in ['COMPLETED', 'FAILED']:
                print(f'Job {job_name} is {job_status}.')
                return
            else:
                print(f'Waiting for {job_name}. Current status is {job_status}.')
            time.sleep(10)

    def _upload_local_speech_file_to_s3_bucket(self) -> str:
        """Uploads a local speech file to the AWS S3 bucket specified in the main configuration file.

        Returns:
            str:
                The AWS S3 URI for the uploaded file

        """

        speech_file_name = utilities.get_file_name_with_extension(self._speech_file_location)
        input_bucket_name = self._config_file.get(Amazon.INPUT_BUCKET_NAME)
        input_file_key = self._config_file.get(Amazon.INPUT_KEY_PREFIX) + speech_file_name
        media_file_uri = Amazon.S3_URI_PREFIX + input_bucket_name + '/' + input_file_key

        print(f'Uploading local file {self._speech_file_location} to {media_file_uri}...')
        self._s3_client.upload_file(self._speech_file_location, input_bucket_name, input_file_key)

        return media_file_uri
