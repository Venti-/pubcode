# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *  # Use Python3-like builtins for Python2.
import base64
import io
try:
    from PIL import Image
except ImportError:
    # PIL is needed only for creating images of the barcode. Set Image to None to signify that PIL is missing.
    Image = None


class Code128(object):
    class Error(Exception):
        pass

    class CharsetError(Error):
        pass

    class CharsetLengthError(Error):
        pass

    class IncompatibleCharsetError(Error):
        pass

    class MissingDependencyError(Error):
        pass

    class UnknownFormatError(Error):
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
            [chr(x) for x in range(32, 95 + 1)] +
            [chr(x) for x in range(0, 31 + 1)] +
            [
                Special.FNC_3, Special.FNC_2, Special.SHIFT_B, Special.CODE_C,
                Special.CODE_B, Special.FNC_4, Special.FNC_1,
                Special.START_A, Special.START_B, Special.START_C, Special.STOP
            ],
        # Code Set B includes ordinals 32 through 127 and 7 special characters. The ordinals include digits,
        # upper and lover case characters and punctuation.
        'B':
            [chr(x) for x in range(32, 127 + 1)] +
            [
                Special.FNC_3, Special.FNC_2, Special.SHIFT_A, Special.CODE_C,
                Special.FNC_4, Special.CODE_A, Special.FNC_1,
                Special.START_A, Special.START_B, Special.START_C, Special.STOP
            ],
        # Code Set C includes all pairs of 2 digits and 3 special characters.
        'C':
            ['%02d' % (x,) for x in range(0, 99 + 1)] +
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

    # How large the quiet zone is on either side of the barcode, when quiet zone is used.
    quiet_zone = 10

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
            charset *= (len(data) // 2)
            if len(data) % 2 == 1:
                # If there are an odd number of characters for charset C, encode the last character with charset B.
                charset += 'B'

        self.data = data
        self.symbol_values = self._encode(data, charset)

    def width(self, add_quiet_zone=False):
        """Return the barcodes width in modules for a given data and character set combination.

        :param add_quiet_zone: Whether quiet zone should be included in the width.

        :return: Width of barcode in modules, which for images translates to pixels.
        """
        quiet_zone = self.quiet_zone if add_quiet_zone else 0
        return len(self.modules) + 2 * quiet_zone

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
                # Handle a special case of there being a single A in middle of two B's or the other way around, where
                # using a single shift character is more efficient than using two character set switches.
                next_charset = charsets[symbol_num + 1] if symbol_num + 1 < len(charsets) else None
                if charset == 'A' and prev_charset == next_charset == 'B':
                    result.append(cls._sym2val[prev_charset][cls.Special.SHIFT_A])
                elif charset == 'B' and prev_charset == next_charset == 'A':
                    result.append(cls._sym2val[prev_charset][cls.Special.SHIFT_B])
                else:
                    # This is the normal case.
                    charset_symbol = cls._char_codes[charset]
                    result.append(cls._sym2val[prev_charset][charset_symbol])
                    prev_charset = charset

            nxt = cur + (2 if charset == 'C' else 1)
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

            shift_charset = None
            for symbol_value in symbol_values:
                if shift_charset:
                    symbol = self._val2sym[shift_charset][symbol_value]
                    shift_charset = None
                else:
                    symbol = self._val2sym[charset][symbol_value]

                if symbol in (self.Special.START_A, self.Special.CODE_A):
                    charset = 'A'
                elif symbol in (self.Special.START_B, self.Special.CODE_B):
                    charset = 'B'
                elif symbol in (self.Special.START_C, self.Special.CODE_C):
                    charset = 'C'
                elif symbol in (self.Special.SHIFT_A,):
                    shift_charset = 'A'
                elif symbol in (self.Special.SHIFT_B,):
                    shift_charset = 'B'

                yield symbol

        return list(_iter_symbols(self.symbol_values))

    @property
    def bars(self):
        """A string of the bar and space weights of the barcode. Starting with a bar and alternating.

        >>> barcode = Code128("Hello!", charset='B')
        >>> barcode.bars
        '2112142311131122142211142211141341112221221212412331112'

        :rtype: string
        """
        return ''.join(map((lambda val: self._val2bars[val]), self.symbol_values))

    @property
    def modules(self):
        """A list of the modules, with 0 representing a bar and 1 representing a space.

        >>> barcode = Code128("Hello!", charset='B')
        >>> barcode.modules  # doctest: +ELLIPSIS
        [0, 0, 1, 0, 1, 1, 0, 1, ..., 0, 0, 0, 1, 0, 1, 0, 0]

        :rtype: list[int]
        """
        def _iterate_modules(bars):
            is_bar = True
            for char in map(int, bars):
                while char > 0:
                    char -= 1
                    yield 0 if is_bar else 1
                is_bar = not is_bar

        return list(_iterate_modules(self.bars))

    @staticmethod
    def _calc_checksum(values):
        """Calculate the symbol check character."""
        checksum = values[0]
        for index, value in enumerate(values):
            checksum += index * value
        return checksum % 103

    def image(self, height=1, module_width=1, add_quiet_zone=True):
        """Get the barcode as PIL.Image.

        By default the image is one pixel high and the number of modules pixels wide, with 10 empty modules added to
        each side to act as the quiet zone. The size can be modified by setting height and module_width, but if used in
        a web page it might be a good idea to do the scaling on client side.

        :param height: Height of the image in number of pixels.
        :param module_width: A multiplier for the width.
        :param add_quiet_zone: Whether to add 10 empty modules to each side of the barcode.

        :rtype: PIL.Image
        :return: A monochromatic image containing the barcode as black bars on white background.
        """
        if Image is None:
            raise Code128.MissingDependencyError("PIL module is required to use image method.")

        modules = list(self.modules)
        if add_quiet_zone:
            # Add ten space modules to each side of the barcode.
            modules = [1] * self.quiet_zone + modules + [1] * self.quiet_zone
        width = len(modules)

        img = Image.new(mode='1', size=(width, 1))
        img.putdata(modules)

        if height == 1 and module_width == 1:
            return img
        else:
            new_size = (width * module_width, height)
            return img.resize(new_size, resample=Image.NEAREST)

    def data_url(self, image_format='png', add_quiet_zone=False):
        """Get a data URL representing the barcode.

        >>> barcode = Code128('Hello!', charset='B')
        >>> barcode.data_url()  # doctest: +ELLIPSIS
        'data:image/png;base64,...'

        :param image_format: Either 'png' or 'bmp'.
        :param add_quiet_zone: Add a 10 white pixels on either side of the barcode.

        :raises: Code128.UnknownFormatError
        :raises: Code128.MissingDependencyError

        :rtype: str
        :returns: A data URL with the barcode as an image.
        """
        memory_file = io.BytesIO()
        pil_image = self.image(add_quiet_zone=add_quiet_zone)

        # Using BMP can often result in smaller data URLs than PNG, but it isn't as widely supported by browsers as PNG.
        # GIFs result in data URLs 10 times bigger than PNG or BMP, possibly due to lack of support for monochrome GIFs
        # in Pillow, so they shouldn't be used.
        if image_format == 'png':
            # Unfortunately there is no way to avoid adding the zlib headers.
            # Using compress_level=0 sometimes results in a slightly bigger data size (by a few bytes), but there
            # doesn't appear to be a difference between levels 9 and 1, so let's just use 1.
            pil_image.save(memory_file, format='png', compress_level=1)
        elif image_format == 'bmp':
            pil_image.save(memory_file, format='bmp')
        else:
            raise Code128.UnknownFormatError('Only png and bmp are supported.')

        # Encode the data in the BytesIO object and convert the result into unicode.
        base64_image = base64.b64encode(memory_file.getvalue()).decode('ascii')

        data_url = 'data:image/{format};base64,{base64_data}'.format(
            format=image_format,
            base64_data=base64_image
        )

        return data_url
