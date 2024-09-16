""" TODO - Module DOC """

import time
import boto3
import proto
from google.cloud import language_v1
from modules import utilities
from modules.constants import ConfigSections, Google, Amazon


def google_analyze_entities(text_content):
    """
    Analyzing Syntax in a String

    Args:
      text_content The text content to analyze
    """

    # Instantiates clients
    # Load configuration file
    config_file = utilities.load_configuration_section(ConfigSections.GOOGLE_STT)
    service_account_json_file = config_file.get(Google.SERVICE_ACCOUNT_JSON_FILE_PATH)
    if service_account_json_file:
        client = language_v1.LanguageServiceClient.from_service_account_json(service_account_json_file)
    else:
        client = language_v1.LanguageServiceClient()

    # Available types: PLAIN_TEXT, HTML
    type_ = language_v1.Document.Type.PLAIN_TEXT

    # Optional. If not specified, the language is automatically detected.
    # For list of supported languages:
    # https://cloud.google.com/natural-language/docs/languages
    language = 'it'
    document = {'content': text_content, 'type_': type_, 'language': language}

    # Available values: NONE, UTF8, UTF16, UTF32
    encoding_type = language_v1.EncodingType.UTF8

    response = client.analyze_entities(request={'document': document, 'encoding_type': encoding_type})

    response_to_json = proto.Message.to_json(response)

    utilities.write_local_file('./test_entities_google.json', response_to_json)


def aws_analyze_entities(aws_txt_file):

    def upload_local_txt_file_to_s3_bucket(txt_file_path) -> str:
        """Uploads a local txt to the AWS S3 bucket specified in the main configuration file.

        Returns:
            str:
                The AWS S3 URI for the uploaded file

        """

        speech_file_name = utilities.get_file_name_with_extension(txt_file_path)
        input_bucket_name = config_file.get(Amazon.INPUT_BUCKET_NAME)
        input_file_key = config_file.get(Amazon.INPUT_KEY_PREFIX) + speech_file_name
        media_file_uri = Amazon.S3_URI_PREFIX + input_bucket_name + '/' + input_file_key

        print(f'Uploading local file {txt_file_path} to {media_file_uri}...')

        s3_client.upload_file(txt_file_path, input_bucket_name, input_file_key)

        return media_file_uri

    def wait_for_entities_detection_job(entities_detection_job_id) -> None:
        """ Waits for the transcription job to finish with configurable timeout given by: TRANSCRIBE_JOB_MAX_TRIES*10s.
        """

        max_tries = 60
        while max_tries > 0:
            max_tries -= 1
            transcription_long_job = comprehend_client.describe_entities_detection_job(JobId=entities_detection_job_id)
            job_status = transcription_long_job['EntitiesDetectionJobProperties']['JobStatus']
            if job_status in ['COMPLETED', 'FAILED']:
                print(f'Job {job_name} is {job_status}.')
                return
            else:
                print(f'Waiting for {entities_detection_job_id}. Current status is {job_status}.')
            time.sleep(10)

    # Load configuration file
    config_file = utilities.load_configuration_section(ConfigSections.AWS_COMPEHEND)
    config_file = config_file

    # Instantiates clients
    aws_access_key_id = str(config_file.get(Amazon.AWS_ACCESS_KEY_ID)) or None
    aws_secret_access_key = str(config_file.get(Amazon.AWS_SECRET_ACCESS_KEY)) or None
    comprehend_client = boto3.client('comprehend', aws_access_key_id=aws_access_key_id,
                                     aws_secret_access_key=aws_secret_access_key)
    s3_client = boto3.client(Amazon.S3_SERVICE, aws_access_key_id=aws_access_key_id,
                             aws_secret_access_key=aws_secret_access_key)

    # TODO - Check for aws_text_file length, if it exceed 5000 byte upload the file to S3 bucket
    if True:
        s3_uri = upload_local_txt_file_to_s3_bucket(aws_txt_file)
        job_name = config_file.get(Amazon.TRANSCRIPTION_JOB_NAME_PREFIX) + '_' + utilities.get_file_name(
            aws_txt_file_path)
        response = comprehend_client.start_entities_detection_job(
            InputDataConfig={
                'S3Uri': s3_uri,
                'InputFormat': 'ONE_DOC_PER_FILE'
            },
            OutputDataConfig={
                'S3Uri': config_file.get(Amazon.OUTPUT_BUCKET_NAME)
            },
            JobName=job_name,
            LanguageCode='it'
        )
        job_id = response['JobId']
        wait_for_entities_detection_job(job_id)
    else:
        text_content = utilities.read_local_file(aws_txt_file)
        response = comprehend_client.detect_entities(Text=text_content, LanguageCode='it')

    utilities.write_local_file('./test_entities_aws.json', response)
    print(f'Transcription response saved.')


if __name__ == '__main__':
    file_names = ['FCINI005b']
    paths = utilities.get_paths_for_file_names(file_names)
    for google_txt_file_path in paths['google_txt_file_paths']:
        google_txt_file = utilities.read_local_file(google_txt_file_path)
        google_analyze_entities(google_txt_file)
    for aws_txt_file_path in paths['aws_txt_file_paths']:
        aws_analyze_entities(aws_txt_file_path)
