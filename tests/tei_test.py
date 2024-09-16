""" TODO - Module DOC """

from modules import utilities
from modules.tei import TEIFile

if __name__ == '__main__':
    file_names = ['FCINI002a', 'FCINI002b', 'FCINI003a', 'FCINI003b', 'FCINI004a', 'FCINI004b', 'FCINI005a', 'FCINI005b']
    paths = utilities.get_paths_for_file_names(file_names)
    for tei_reference_file_path in paths['tei_reference_file_paths']:
        print('------------------------------------------------------------------------------------------------------')
        print('Building {} TEI file...'.format(tei_reference_file_path))
        test_tei_file = TEIFile(tei_reference_file_path)
        print('Performing TEI file validation...')
        is_valid, error_logs = test_tei_file.validate()
        if is_valid:
            print('Valid TEI file.')
        else:
            print('Invalid TEI file. Found ' + str(len(error_logs)) + ' errors:')
            for error_log in error_logs:
                print('\033[93m' + str(error_log))
            print('\033[0m')
        print('Computing statistic for TEI file...')
        print('Total words: %s' % test_tei_file.total_words)
        print('Languages:')
        for test_language in test_tei_file.languages:
            language_usage = round((test_language.words_count / test_tei_file.total_words) * 100, 2)
            print('\t%s - Words count: %s - Usage: %s' % (test_language.code, test_language.words_count, language_usage)
                  + '%')
