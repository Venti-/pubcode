# -*- coding: utf-8 -*-
from unittest import TestCase
from pubcode import Code128


class TestCode128(TestCase):
    def test___init__(self):
        data = "Hello!"
        barcode = Code128(data)
        self.assertEqual(barcode.data, data)
