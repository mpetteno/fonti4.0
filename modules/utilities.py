""" Utility methods for other modules.

The module contains all methods that are not related to any specific function or service such as methods to handle
services configuration and file system access.

"""

import ast
import configparser
import csv
from collections import defaultdict
from pathlib import Path
from typing import AnyStr, Iterable, Mapping, Any
from google.protobuf import json_format
from modules.constants import Paths, Google, Amazon, ConfigSections
from modules.compiled.canonical_transcription_pb2 import CanonicalTranscription


def get_local_file_size(local_file_path: str) -> float:
    """Calculates the size a local file in Megabytes (MB).

    Args:
        local_file_path (str):
            The path to the local file.

    Returns:
        float:
            The local file size in Megabytes.

    """

    local_file = Path(local_file_path)
    local_file_size_bytes = local_file.stat().st_size
    return local_file_size_bytes / (1024 * 1024)


def get_file_format(file_location: str) -> str:
    """Retrieves the file format from a file location.
    A file location can be either a local path or a URI that points to remote bucket.

    Args:
        file_location (str):
            The file location.

    Returns:
        str:
            The file format.

    """

    return Path(file_location).suffix[1:]


def get_file_name(file_location: str) -> str:
    """Retrieves the file name (excluding the extension) from a file location.
    A file location can be either a local path or a URI that points to remote bucket.

    Args:
        file_location (str):
            The file location.

    Returns:
        str:
            The file name (excluding the extension).

    """

    return Path(file_location).stem


def get_file_name_with_extension(file_location: str) -> str:
    """Retrieves the file name (including the extension) from a file location.
    A file location can be either a local path or a URI that points to remote bucket.

    Args:
        file_location (str):
            The file location.

    Returns:
        str:
            The file name (including the extension).

    """

    return Path(file_location).name


def get_file_extension(file_location: str) -> str:
    """Retrieves the file extension from a file location.
    A file location can be either a local path or a URI that points to remote bucket.

    Args:
        file_location (str):
            The file location.

    Returns:
        str:
            The file extension.

    """

    return Path(file_location).suffix


def get_parent_path(file_location: str) -> str:
    """Retrieves the parent path from a file location.
    A file location can be either a local path or a URI that points to remote bucket.

    Args:
        file_location (str):
            The file location.

    Returns:
        str:
            The parent path.

    """

    return Path(file_location).parent


def get_paths_for_file_names(file_names: Iterable[str]) -> Mapping[str, str]:
    """ TODO - Function DOC """

    def match_first_file(dir_path: str, match_name: str, file_extension: str) -> str:
        """ TODO - Function DOC """

        try:
            return str(next(Path(dir_path).glob('{}*.{}'.format(match_name, file_extension))))
        except StopIteration:
            return ''

    speeches_conf = load_configuration_section(ConfigSections.SPEECHES)
    tei_conf = load_configuration_section(ConfigSections.TEI)
    google_conf = load_configuration_section(ConfigSections.GOOGLE_STT)
    aws_conf = load_configuration_section(ConfigSections.AWS_TRANSCRIBE)

    paths = defaultdict(list)

    for file_name in file_names:
        local_speech_file_path = match_first_file(speeches_conf[Paths.SPEECH_FILES_PATH], file_name, 'wav')
        tei_reference_file_path = match_first_file(tei_conf[Paths.TEI_FILES_PATH], file_name, 'xml')
        google_transcription_files_path = '{}/{}/{}'.format(google_conf[Paths.TRANSCRIPTION_OUTPUT_PATH],
                                                            file_name[-2:], file_name)
        aws_transcription_files_path = '{}/{}/{}'.format(aws_conf[Paths.TRANSCRIPTION_OUTPUT_PATH], file_name[-2:],
                                                         file_name)
        tei_canonical_file_path = match_first_file(tei_conf[Paths.CANONICAL_TRANSCRIPTION_OUTPUT_PATH], file_name,
                                                   'json')
        google_canonical_file_path = match_first_file(google_conf[Paths.CANONICAL_TRANSCRIPTION_OUTPUT_PATH],
                                                      file_name, 'json')
        aws_canonical_file_path = match_first_file(aws_conf[Paths.CANONICAL_TRANSCRIPTION_OUTPUT_PATH], file_name,
                                                   'json')
        google_txt_file_path = match_first_file(google_conf[Paths.TXT_OUTPUT_PATH], file_name, 'txt')
        aws_txt_file_path = match_first_file(aws_conf[Paths.TXT_OUTPUT_PATH], file_name, 'txt')
        paths['local_speech_file_paths'].append(local_speech_file_path)
        paths['tei_reference_file_paths'].append(tei_reference_file_path)
        paths['google_transcription_files_paths'].append(google_transcription_files_path)
        paths['aws_transcription_files_paths'].append(aws_transcription_files_path)
        paths['tei_canonical_file_paths'].append(tei_canonical_file_path)
        paths['google_canonical_file_paths'].append(google_canonical_file_path)
        paths['aws_canonical_file_paths'].append(aws_canonical_file_path)
        paths['google_txt_file_paths'].append(google_txt_file_path)
        paths['aws_txt_file_paths'].append(aws_txt_file_path)

    return paths


def is_gcs_uri(speech_file_location: str) -> bool:
    """Uploads a local speech file to the AWS S3 bucket specified in the main configuration file.

    Args:
        speech_file_location (str):
            A path to a local speech file.

    Returns:
        str:
            The AWS S3 URI for the uploaded file

    """

    return speech_file_location.startswith(Google.GS_URI_PREFIX)


def is_s3_uri(speech_file_location: str) -> bool:
    """ Decides if a speech file location is a local path or a URI that points to an AWS S3 bucket

    Args:
        speech_file_location (str):
            The file location.

    Returns:
        bool:
            True if speech_file_location is an AWS S3 URI, False otherwise

    """

    return speech_file_location.startswith(Amazon.S3_URI_PREFIX)


def load_canonical_transcription(canonical_transcription_path: str):
    """ TODO - Function DOC """

    canonical_transcription_file = read_local_file(canonical_transcription_path)
    return json_format.Parse(canonical_transcription_file, CanonicalTranscription())


def load_configuration_file() -> configparser.ConfigParser:
    """Loads the configuration file specified in modules.constants.Paths.MAIN_CONFIG_FILE.
    Files that cannot be opened are silently ignored.

    Returns:
        configparser.ConfigParser:
            An object representing the configuration file.

    """

    config_file = configparser.ConfigParser()
    config_file.read(Paths.MAIN_CONFIG_FILE)
    return config_file


def load_configuration_section(section_name: str) -> Mapping[str, Any]:
    """Loads a section of the configuration file specified in modules.constants.Paths.MAIN_CONFIG_FILE.

    Args:
        section_name (str):
            The name of the section to load.

    Returns:
        TODO - Function DOC

    """

    config_file = load_configuration_file()
    file_section = dict()
    for option in config_file.options(section_name):
        option_value = config_file.get(section_name, option)
        try:
            file_section[option] = ast.literal_eval(option_value)
        except (SyntaxError, ValueError):
            file_section[option] = option_value
    return file_section


def read_local_file(local_file_path: str, mode: str = 'r') -> AnyStr:
    """Reads the content of a local file as bytes sequence.

    Args:
        local_file_path (str):
            The path to the local file.
        mode (str):
            How to read the file.

    Returns:
        Depending on the value of mode argument, a sequence of bytes or a string representing the content of the local
        file.

    """

    with Path(local_file_path).open(mode=mode) as local_file:
        return local_file.read()


def write_local_file(local_file_path: str, file_content: AnyStr, mode: str = 'w') -> None:
    """ TODO - Class DOC """

    print('Writing file to {}'.format(local_file_path))

    with Path(local_file_path).open(mode=mode) as local_file:
        local_file.writelines(file_content)


def write_local_csv_file(local_csv_file_path: str, csv_header: Iterable, csv_rows: Iterable[Iterable]) -> None:
    """ TODO - Class DOC """

    print('Writing file to {}'.format(local_csv_file_path))

    with Path(local_csv_file_path).open(mode='w') as output_csv_file:
        writer = csv.writer(output_csv_file)
        writer.writerow(csv_header)
        writer.writerows(csv_rows)
