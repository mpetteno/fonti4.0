""" TODO - Module DOC """

from modules.tokenizer import DefaultCanonicalTokenizer
from modules.compiled.canonical_transcription_pb2 import CanonicalWord

if __name__ == '__main__':
    default_tokenizer = DefaultCanonicalTokenizer('it')
    tokenized_word = default_tokenizer.tokenize('dell\'arte')
    if not tokenized_word:
        print('Empty')
    elif len(tokenized_word) > 1:
        test_word = tokenized_word[0]
        punctuation = tokenized_word[1]
        print('Normalized - ' + CanonicalWord.CanonicalWordType.Name(test_word.type) + ': ' + test_word.word + ', '
              + CanonicalWord.CanonicalWordType.Name(punctuation.type) + ': ' + punctuation.word)
    else:
        test_word = tokenized_word[0]
        print('Normalized - ' + CanonicalWord.CanonicalWordType.Name(test_word.type) + ': ' + test_word.word)
