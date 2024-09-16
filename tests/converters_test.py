""" TODO - Module DOC """

from modules import utilities
from modules.constants import ConfigSections
from modules.converters import TRNConverter, STMConverter, TXTConverter, CTMConverter

if __name__ == '__main__':
    file_names = ['FCINI002a', 'FCINI002b', 'FCINI003a', 'FCINI003b', 'FCINI004a', 'FCINI004b', 'FCINI005a',
                  'FCINI005b']
    paths = utilities.get_paths_for_file_names(file_names)
    for tei_canonical_file_paths in paths['tei_canonical_file_paths']:
        print('------------------------------------------------------------------------------------------------------')
        print('Converting {} to TRN, STM and TXT formats...'.format(tei_canonical_file_paths))
        TRNConverter(tei_canonical_file_paths, ConfigSections.TEI).convert()
        STMConverter(tei_canonical_file_paths, ConfigSections.TEI).convert()
        TXTConverter(tei_canonical_file_paths, ConfigSections.TEI).convert()
    for google_canonical_file_path in paths['google_canonical_file_paths']:
        print('------------------------------------------------------------------------------------------------------')
        print('Converting {} to TRN, CTM and TXT formats...'.format(google_canonical_file_path))
        TRNConverter(google_canonical_file_path, ConfigSections.GOOGLE_STT).convert()
        CTMConverter(google_canonical_file_path, ConfigSections.GOOGLE_STT).convert()
        TXTConverter(google_canonical_file_path, ConfigSections.GOOGLE_STT).convert()
    for aws_canonical_file_path in paths['aws_canonical_file_paths']:
        print('------------------------------------------------------------------------------------------------------')
        print('Converting {} to TRN, CTM and TXT formats...'.format(aws_canonical_file_path))
        TRNConverter(aws_canonical_file_path, ConfigSections.AWS_TRANSCRIBE).convert()
        CTMConverter(aws_canonical_file_path, ConfigSections.AWS_TRANSCRIBE).convert()
        TXTConverter(aws_canonical_file_path, ConfigSections.AWS_TRANSCRIBE).convert()
