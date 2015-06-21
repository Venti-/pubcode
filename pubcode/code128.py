# -*- coding: utf-8 -*-


class Code128(object):
    class Error(Exception):
        pass

    class CharsetError(Error):
        pass

    class CharsetLengthError(Error):
        pass

    class IncompatibleCharsetError(Error):
        pass

    def __init__(self, data, charset=None):
        """Initialize a barcode with data as described by the character sets in charset.

        :param data: The data to be encoded.
        :param charset: A single character set (A, B or C), an iterable with a character set for each symbol or None.
                        - If a single character set is chosen, all characters will be encoded with that set, except for
                          incompatible characters which will be coded with one of the other character sets.
                        - If a sequence of character sets are given, incompatible characters will result in
                          Code128.IncompatibleCharsetError. Wrong size of the charset sequence in relation to data,
                          will result in Code128.CharsetLengthError.
                        - If None is given, the character set will be chosen as to minimize the length of the barcode.
        """
        self._validate_charset(data, charset)

        self.data = data

    @staticmethod
    def _validate_charset(data, charset):
        """"Validate that the charset is correct and throw an error if it isn't."""
        if len(charset) > 1:
            charset_data_length = 0
            for symbol_charset in charset:
                if symbol_charset not in ('A', 'B', 'C'):
                    raise Code128.CharsetError
                charset_data_length += 2 if symbol_charset is 'C' else 1
            if charset_data_length != len(data):
                raise Code128.CharsetLengthError
        elif len(charset) == 1:
            if charset not in ('A', 'B', 'C'):
                raise Code128.CharsetError
        elif charset is not None:
            raise Code128.CharsetError
