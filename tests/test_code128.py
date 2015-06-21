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
