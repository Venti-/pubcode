# -*- coding: utf-8 -*-
from unittest import TestCase
from pubcode import Code128


class TestCode128(TestCase):
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
        data = ''.join(map(chr, range(0, 95+1)))
        code = Code128(data, charset='A')

        correct_symbols = (
            [Code128.Special.START_A] +
            map(chr, range(0, 95+1)) +
            ['T', Code128.Special.STOP]
        )

        self.assertSequenceEqual(code.symbols, correct_symbols)

    def test_codeset_b(self):
        """Test code set B."""
        data = ''.join(map(chr, range(32, 127+1)))
        code = Code128(data, charset='B')

        # The characters that can be encoded are ordinals 32 through 127.
        correct_symbols = (
            [Code128.Special.START_B] +
            map(chr, range(32, 127+1)) +
            ['\x7f', Code128.Special.STOP]
        )

        self.assertSequenceEqual(code.symbols, correct_symbols)

    def test_codeset_c(self):
        """Test every pair of numbers in code set C."""
        data = ("%02d" * 100) % tuple(range(100))
        code = Code128(data, charset='C')

        correct_symbols = (
            [Code128.Special.START_C] +
            map(lambda x: '%02d' % (x), range(100)) +
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
