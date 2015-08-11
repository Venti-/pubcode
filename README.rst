PubCode
=======
PubCode is a library that encodes barcodes and allows easy access to the data
required to render the barcode. It can optionally use PIL to render the
barcode or to provide a data URL containing a single pixel high PNG barcode
which can be resized by a browser to a more usefull size.

.. image:: https://travis-ci.org/Venti-/pubcode.svg?branch=master
    :target: https://travis-ci.org/Venti-/pubcode


Supported barcodes
------------------
    - Code128


Usage
-------

    >>> from pubcode import Code128
    >>> barcode = Code128('Hello!', charset='B')

You can access the data required to render the barcode easily and intuitively.

    >>> barcode.bars
    '2112142311131122142211142211141341112221221212412331112'
    >>> barcode.modules  # doctest: +ELLIPSIS
    [0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, ...]

You can generate PIL.Image objects from barcodes.

    >>> barcode.image()  # doctest: +ELLIPSIS
    <PIL.Image.Image image mode=1 size=121x1 at ...>
    >>> barcode.image(height=10, module_width=2)  # doctest: +ELLIPSIS
    <PIL.Image.Image image mode=1 size=242x10 at ...>

You can also generate data URLs.

    >>> barcode.data_url()  # doctest: +ELLIPSIS
    'data:image/png;base64,...'

You can also control the exact way in which the barcode is encoded, which
allows you to control the size of the resulting barcode.

    >>> barcode = Code128('12\x00x\x01', charset='CABA')
    >>> barcode.symbols
    ['[Start Code C]', '12', '[Code A]', '\x00', '[Shift B]', 'x', '\x01', '\x15', '[Stop]']
