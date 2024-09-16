""" TODO - Module DOC """

from modules.transcribers import GoogleSTTTranscribeService, AWSTranscribeService

if __name__ == '__main__':
    print('---------------------------------------------------------------------------------------------------------')
    print('Transcribing file with Google Speech-to-Text service...')
    GoogleSTTTranscribeService('../files/speeches/FCINI002b_cut_48_16_small.wav').transcribe()
    print('---------------------------------------------------------------------------------------------------------')
    print('Transcribing file with AWS Transcribe service...')
    AWSTranscribeService('../files/speeches/FCINI002b_cut_48_16_small.wav').transcribe()
