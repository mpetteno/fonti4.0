""" TODO - Module DOC """

from modules import utilities
from modules.metrics import GoogleSTTMetrics, AWSTranscribeMetrics

if __name__ == '__main__':
    file_names = ['FCINI002a', 'FCINI002b', 'FCINI003a', 'FCINI003b', 'FCINI004a', 'FCINI004b', 'FCINI005a', 'FCINI005b']
    paths = utilities.get_paths_for_file_names(file_names)
    print('---------------------------------------------------------------------------------------------------------')
    print('Custom metrics for Google STT')
    print('Computing...')
    GoogleSTTMetrics(paths['tei_canonical_file_paths'], paths['google_canonical_file_paths']).metrics()
    print('---------------------------------------------------------------------------------------------------------')
    print('Computing...')
    print('Custom metrics for AWS Transcribe')
    AWSTranscribeMetrics(paths['tei_canonical_file_paths'], paths['aws_canonical_file_paths']).metrics()
