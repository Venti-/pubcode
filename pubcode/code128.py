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

    # List of bar and space weights, indexed by symbol character values (0-105), and the STOP character (106).
    # The first weights is a bar and then it alternates.
    _val2bars = [
        '212222', '222122', '222221', '121223', '121322', '131222', '122213', '122312', '132212', '221213',
        '221312', '231212', '112232', '122132', '122231', '113222', '123122', '123221', '223211', '221132',
        '221231', '213212', '223112', '312131', '311222', '321122', '321221', '312212', '322112', '322211',
        '212123', '212321', '232121', '111323', '131123', '131321', '112313', '132113', '132311', '211313',
        '231113', '231311', '112133', '112331', '132131', '113123', '113321', '133121', '313121', '211331',
        '231131', '213113', '213311', '213131', '311123', '311321', '331121', '312113', '312311', '332111',
        '314111', '221411', '431111', '111224', '111422', '121124', '121421', '141122', '141221', '112214',
        '112412', '122114', '122411', '142112', '142211', '241211', '221114', '413111', '241112', '134111',
        '111242', '121142', '121241', '114212', '124112', '124211', '411212', '421112', '421211', '212141',
        '214121', '412121', '111143', '111341', '131141', '114113', '114311', '411113', '411311', '113141',
        '114131', '311141', '411131', '211412', '211214', '211232', '2331112'
    ]

    class Special(object):
        """These are special characters used by the Code128 encoding."""
        START_A = '[Start Code A]'
        START_B = '[Start Code B]'
        START_C = '[Start Code C]'
        CODE_A = '[Code A]'
        CODE_B = '[Code B]'
        CODE_C = '[Code C]'
        SHIFT_A = '[Shift A]'
        SHIFT_B = '[Shift B]'
        FNC_1 = '[FNC 1]'
        FNC_2 = '[FNC 2]'
        FNC_3 = '[FNC 3]'
        FNC_4 = '[FNC 4]'
        STOP = '[Stop]'

    _start_codes = {'A': Special.START_A, 'B': Special.START_B, 'C': Special.START_C}
    _char_codes = {'A': Special.CODE_A, 'B': Special.CODE_B, 'C': Special.CODE_C}

    # Lists mapping symbol values to characters in each character set. This defines the alphabet and Code128._sym2val
    # is derived from this structure.
    _val2sym = {
        # Code Set A includes ordinals 0 through 95 and 7 special characters. The ordinals include digits,
        # upper case characters, punctuation and control characters.
        'A':
            list(map(chr, range(32, 95 + 1))) +
            list(map(chr, range(0, 31 + 1))) +
            [
                Special.FNC_3, Special.FNC_2, Special.SHIFT_B, Special.CODE_C,
                Special.CODE_B, Special.FNC_4, Special.FNC_1,
                Special.START_A, Special.START_B, Special.START_C, Special.STOP
            ],
        # Code Set B includes ordinals 32 through 127 and 7 special characters. The ordinals include digits,
        # upper and lover case characters and punctuation.
        'B':
            list(map(chr, range(32, 127 + 1))) +
            [
                Special.FNC_3, Special.FNC_2, Special.SHIFT_A, Special.CODE_C,
                Special.FNC_4, Special.CODE_A, Special.FNC_1,
                Special.START_A, Special.START_B, Special.START_C, Special.STOP
            ],
        # Code Set C includes all pairs of 2 digits and 3 special characters.
        'C':
            list(map(lambda x: '%02d' % (x,), range(0, 99 + 1))) +
            [
                Special.CODE_B, Special.CODE_A, Special.FNC_1,
                Special.START_A, Special.START_B, Special.START_C, Special.STOP
            ],
    }

    # Dicts mapping characters to symbol values in each character set.
    _sym2val = {
        'A': {char: val for val, char in enumerate(_val2sym['A'])},
        'B': {char: val for val, char in enumerate(_val2sym['B'])},
        'C': {char: val for val, char in enumerate(_val2sym['C'])},
    }

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

        if charset in ('A', 'B'):
            charset *= len(data)
        elif charset in ('C',):
            charset *= (len(data) / 2)
            if len(data) % 2 == 1:
                # If there are an odd number of characters for charset C, encode the last character with charset B.
                charset += 'B'

        self.data = data
        self.symbol_values = self._encode(data, charset)

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

    @classmethod
    def _encode(cls, data, charsets):
        """Encode the data using the character sets in charsets.

        :param data: Data to be encoded.
        :param charsets: Sequence of charsets that are used to encode the barcode.
                         Must be the exact amount of symbols needed to encode the data.
        :return: List of the symbol values representing the barcode.
        """
        result = []

        charset = charsets[0]
        start_symbol = cls._start_codes[charset]
        result.append(cls._sym2val[charset][start_symbol])

        cur = 0
        prev_charset = charsets[0]
        for symbol_num in range(len(charsets)):
            charset = charsets[symbol_num]

            if charset is not prev_charset:
                charset_symbol = cls._char_codes[charset]
                result.append(cls._sym2val[prev_charset][charset_symbol])
                prev_charset = charset

            nxt = cur + (2 if charset is 'C' else 1)
            symbol = data[cur:nxt]
            cur = nxt
            result.append(cls._sym2val[charset][symbol])

        result.append(cls._calc_checksum(result))
        result.append(cls._sym2val[charset][cls.Special.STOP])

        return result

    @property
    def symbols(self):
        """List of the coded symbols as strings, with special characters included."""
        def _iter_symbols(symbol_values):
            # The initial charset doesn't matter, as the start codes have the same symbol values in all charsets.
            charset = 'A'

            for symbol_value in symbol_values:
                symbol = self._val2sym[charset][symbol_value]

                if symbol in (self.Special.START_A, self.Special.CODE_A):
                    charset = 'A'
                elif symbol in (self.Special.START_B, self.Special.CODE_B):
                    charset = 'B'
                elif symbol in (self.Special.START_C, self.Special.CODE_C):
                    charset = 'C'

                yield symbol

        return list(_iter_symbols(self.symbol_values))

    @staticmethod
    def _calc_checksum(values):
        """Calculate the symbol check character."""
        checksum = values[0]
        for index, value in enumerate(values):
            checksum += index * value
        return checksum % 103
