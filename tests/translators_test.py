""" TODO - Module DOC """

from modules import tei, utilities
from modules.translators import TEIFileCanonicalTranslator, GoogleSTTCanonicalTranslator, \
    AWSTranscribeCanonicalTranslator

if __name__ == '__main__':
    file_names = ['FCINI002a', 'FCINI002b', 'FCINI003a', 'FCINI003b', 'FCINI004a', 'FCINI004b', 'FCINI005a', 'FCINI005b']
    paths = utilities.get_paths_for_file_names(file_names)
    for tei_reference_file_path, google_transcription_files_path, aws_transcription_files_path in zip(
            paths['tei_reference_file_paths'], paths['google_transcription_files_paths'],
            paths['aws_transcription_files_paths']):
        print('------------------------------------------------------------------------------------------------------')
        print('Building {} TEI reference file...'.format(tei_reference_file_path))
        tei_file = tei.TEIFile(tei_reference_file_path)
        print('Translating {} TEI reference file to canonical format...'.format(tei_reference_file_path))
        TEIFileCanonicalTranslator(tei_reference_file_path, tei_file).translate()
        print('------------------------------------------------------------------------------------------------------')
        print('Translating {} Google transcription file to canonical format...'.format(google_transcription_files_path))
        GoogleSTTCanonicalTranslator(google_transcription_files_path, tei_file).translate()
        print('------------------------------------------------------------------------------------------------------')
        print('Translating {} AWS transcription file to canonical format...'.format(aws_transcription_files_path))
        AWSTranscribeCanonicalTranslator(aws_transcription_files_path, tei_file).translate()
