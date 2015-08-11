# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *  # Use Python3-like builtins for Python2.
from unittest import TestCase
from pubcode import Code128
import base64
from PIL import Image
import io


class TestCode128(TestCase):
    # Test data used by multiple tests.
    _hello_b_modules = [
        0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1,  # Start B
        0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1,  # H
        0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1,  # e
        0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1,  # l
        0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1,  # l
        0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1,  # o
        0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1,  # !
        0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1,  # check symbol (r)
        0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0  # Stop
    ]

    def test__init__wrong_charset(self):
        with self.assertRaises(Code128.CharsetError):
            Code128('Hello!', 'D')

    def test__init__wrong_length_charset(self):
        with self.assertRaises(Code128.CharsetLengthError):
            Code128('Hello!', 'BB')
        with self.assertRaises(Code128.CharsetLengthError):
            Code128('Hello!', 'BBBBBBB')

    def test_codeset_a(self):
        """Test every character in code set A."""
        data = ''.join(chr(x) for x in range(0, 95 + 1))
        code = Code128(data, charset='A')

        correct_symbols = (
            [Code128.Special.START_A] +
            [chr(x) for x in range(0, 95 + 1)] +
            ['T', Code128.Special.STOP]
        )

        self.assertSequenceEqual(code.symbols, correct_symbols)

    def test_codeset_b(self):
        """Test code set B."""
        data = ''.join(chr(x) for x in range(32, 127 + 1))
        code = Code128(data, charset='B')

        # The characters that can be encoded are ordinals 32 through 127.
        correct_symbols = (
            [Code128.Special.START_B] +
            [chr(x) for x in range(32, 127 + 1)] +
            ['\x7f', Code128.Special.STOP]
        )

        self.assertSequenceEqual(code.symbols, correct_symbols)

    def test_codeset_c(self):
        """Test every pair of numbers in code set C."""
        data = ("%02d" * 100) % tuple(range(100))
        code = Code128(data, charset='C')

        correct_symbols = (
            [Code128.Special.START_C] +
            ['%02d' % (x,) for x in range(100)] +
            ['97', Code128.Special.STOP]
        )

        self.assertSequenceEqual(code.symbols, correct_symbols)

    def test_codeset_c_odd(self):
        """Test switching to another code set to code the leftover number in code set C."""
        data = "123"
        code = Code128(data, charset='C')

        correct_symbols = [
            Code128.Special.START_C,
            '12', Code128.Special.CODE_B, '3',
            'a', Code128.Special.STOP
        ]

        self.assertSequenceEqual(code.symbols, correct_symbols)

    def test_shift_a(self):
        data = 'a\x00a\x00a'
        code = Code128(data, charset='BABAB')

        correct_symbols = [
            Code128.Special.START_B,
            'a', Code128.Special.SHIFT_A, '\x00', 'a', Code128.Special.SHIFT_A, '\x00', 'a',
            'v', Code128.Special.STOP
        ]

        self.assertSequenceEqual(code.symbols, correct_symbols)

    def test_shift_b(self):
        data = '\x00b\x00b\x00'
        code = Code128(data, charset='ABABA')

        correct_symbols = [
            Code128.Special.START_A,
            '\x00', Code128.Special.SHIFT_B, 'b', '\x00', Code128.Special.SHIFT_B, 'b', '\x00',
            '\x1b', Code128.Special.STOP
        ]

        self.assertSequenceEqual(code.symbols, correct_symbols)

    def test_image(self):
        """Test that the generated image is of the correct format and contains the correct data."""
        data = "Hello!"
        code = Code128(data, charset='B')
        image = code.image(add_quiet_zone=False)

        # Check that the image is monochrome.
        self.assertEqual(image.mode, '1')

        # Check that the image is exactly one pixel in height.
        self.assertEqual(image.size[1], 1)

        # Check that the image is of the correct width and has the correct pixels in it.
        pixels = [image.getpixel((x, 0)) for x in range(image.size[0])]
        self.assertListEqual(pixels, self._hello_b_modules)

    def test_data_url(self):
        code = Code128("Hello!", charset='B')

        # Get the second part of the data url, which contains the base64 encoded image.
        base64_image = code.data_url().split(',')[1]

        # Remove the base64 encoding and create a PIL.Image out of it.
        image_data = base64.b64decode(base64_image)
        memory_file = io.BytesIO(image_data)
        image = Image.open(memory_file)

        # Check that the image is monochrome.
        self.assertEqual(image.mode, '1')

        # Check that the image is exactly one pixel in height.
        self.assertEqual(image.size[1], 1)

        # Check that the image is of the correct width and has the correct pixels in it.
        pixels = [1 if image.getpixel((x, 0)) else 0 for x in range(image.size[0])]
        self.assertListEqual(pixels, self._hello_b_modules)
