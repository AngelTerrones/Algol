#!/usr/bin/env python
# Copyright (c) 2015 Angel Terrones (<angelterrones@gmail.com>)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from myhdl import always_comb


def Mux2(sel,
         in1,
         in2,
         out):
    """
    Defines a multiplexor 2 to 1.

    :param sel:  Data selector
    :param int1: Data input
    :param int2: Data input
    :param out:  Data output
    """
    @always_comb
    def rtl():
        if sel == 0:
            out.next = in1
        else:
            out.next = in2

    return rtl


def Mux4(sel,
         in1,
         in2,
         in3,
         in4,
         out):
    """
    Defines a multiplexor 4 to 1.

    :param sel:  Data selector
    :param int1: Data input
    :param int2: Data input
    :param int3: Data input
    :param int4: Data input
    :param out:  Data output
    """
    @always_comb
    def rtl():
        if sel == 0:
            out.next = in1
        elif sel == 1:
            out.next = in2
        elif sel == 2:
            out.next = in3
        else:
            out.next = in4

    return rtl

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
