#!/usr/bin/python3
#
# Tests mfmv.py
#
# usage
#   * python mfmv_test.py
#       * need to have mfmv.py in $PYTHONPATH or place mfmv.py in parent directory
#
# version 0.8
# notes
#   * tested on 'Windows 10 2004' # TODO: testing with OSX and linux
#
# todos
#   * cases with more multifiles and files not part of multifiles
#   * refactor creation of params
#   * input prompts related to dir such as 'd ..'

# type: ignore # TODO

import copy
import os
import sys
import unittest
import unittest.mock

import parameterized  # python3 -m pip install parameterized

from typing import List  # declaration of parameter and return types

try:
    import mfmv
    from utils.wrapped_indexable_callable import WrappedIndexableCallable
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    import mfmv
    from utils.wrapped_indexable_callable import WrappedIndexableCallable
####################################################################################################
####################################################################################################
# fmt: off
gen_indexable_part_0_99_indices = [
    ["000000000", "000000001", "000000002", "000000003", "000000004", "000000005", "000000006", "000000007", "000000008", "000000009", "000000010", "000000011", "000000012", "000000013", "000000014", "000000015", "000000016", "000000017", "000000018", "000000019", "000000020", "000000021", "000000022", "000000023", "000000024", "000000025", "000000026", "000000027", "000000028", "000000029", "000000030", "000000031", "000000032", "000000033", "000000034", "000000035", "000000036", "000000037", "000000038", "000000039", "000000040", "000000041", "000000042", "000000043", "000000044", "000000045", "000000046", "000000047", "000000048", "000000049", "000000050", "000000051", "000000052", "000000053", "000000054", "000000055", "000000056", "000000057", "000000058", "000000059", "000000060", "000000061", "000000062", "000000063", "000000064", "000000065", "000000066", "000000067", "000000068", "000000069", "000000070", "000000071", "000000072", "000000073", "000000074", "000000075", "000000076", "000000077", "000000078", "000000079", "000000080", "000000081", "000000082", "000000083", "000000084", "000000085", "000000086", "000000087", "000000088", "000000089", "000000090", "000000091", "000000092", "000000093", "000000094", "000000095", "000000096", "000000097", "000000098", "000000099",],
    ["00000000", "00000001", "00000002", "00000003", "00000004", "00000005", "00000006", "00000007", "00000008", "00000009", "00000010", "00000011", "00000012", "00000013", "00000014", "00000015", "00000016", "00000017", "00000018", "00000019", "00000020", "00000021", "00000022", "00000023", "00000024", "00000025", "00000026", "00000027", "00000028", "00000029", "00000030", "00000031", "00000032", "00000033", "00000034", "00000035", "00000036", "00000037", "00000038", "00000039", "00000040", "00000041", "00000042", "00000043", "00000044", "00000045", "00000046", "00000047", "00000048", "00000049", "00000050", "00000051", "00000052", "00000053", "00000054", "00000055", "00000056", "00000057", "00000058", "00000059", "00000060", "00000061", "00000062", "00000063", "00000064", "00000065", "00000066", "00000067", "00000068", "00000069", "00000070", "00000071", "00000072", "00000073", "00000074", "00000075", "00000076", "00000077", "00000078", "00000079", "00000080", "00000081", "00000082", "00000083", "00000084", "00000085", "00000086", "00000087", "00000088", "00000089", "00000090", "00000091", "00000092", "00000093", "00000094", "00000095", "00000096", "00000097", "00000098", "00000099",],
    ["0000000", "0000001", "0000002", "0000003", "0000004", "0000005", "0000006", "0000007", "0000008", "0000009", "0000010", "0000011", "0000012", "0000013", "0000014", "0000015", "0000016", "0000017", "0000018", "0000019", "0000020", "0000021", "0000022", "0000023", "0000024", "0000025", "0000026", "0000027", "0000028", "0000029", "0000030", "0000031", "0000032", "0000033", "0000034", "0000035", "0000036", "0000037", "0000038", "0000039", "0000040", "0000041", "0000042", "0000043", "0000044", "0000045", "0000046", "0000047", "0000048", "0000049", "0000050", "0000051", "0000052", "0000053", "0000054", "0000055", "0000056", "0000057", "0000058", "0000059", "0000060", "0000061", "0000062", "0000063", "0000064", "0000065", "0000066", "0000067", "0000068", "0000069", "0000070", "0000071", "0000072", "0000073", "0000074", "0000075", "0000076", "0000077", "0000078", "0000079", "0000080", "0000081", "0000082", "0000083", "0000084", "0000085", "0000086", "0000087", "0000088", "0000089", "0000090", "0000091", "0000092", "0000093", "0000094", "0000095", "0000096", "0000097", "0000098", "0000099",],
    ["000000", "000001", "000002", "000003", "000004", "000005", "000006", "000007", "000008", "000009", "000010", "000011", "000012", "000013", "000014", "000015", "000016", "000017", "000018", "000019", "000020", "000021", "000022", "000023", "000024", "000025", "000026", "000027", "000028", "000029", "000030", "000031", "000032", "000033", "000034", "000035", "000036", "000037", "000038", "000039", "000040", "000041", "000042", "000043", "000044", "000045", "000046", "000047", "000048", "000049", "000050", "000051", "000052", "000053", "000054", "000055", "000056", "000057", "000058", "000059", "000060", "000061", "000062", "000063", "000064", "000065", "000066", "000067", "000068", "000069", "000070", "000071", "000072", "000073", "000074", "000075", "000076", "000077", "000078", "000079", "000080", "000081", "000082", "000083", "000084", "000085", "000086", "000087", "000088", "000089", "000090", "000091", "000092", "000093", "000094", "000095", "000096", "000097", "000098", "000099",],
    ["00000", "00001", "00002", "00003", "00004", "00005", "00006", "00007", "00008", "00009", "00010", "00011", "00012", "00013", "00014", "00015", "00016", "00017", "00018", "00019", "00020", "00021", "00022", "00023", "00024", "00025", "00026", "00027", "00028", "00029", "00030", "00031", "00032", "00033", "00034", "00035", "00036", "00037", "00038", "00039", "00040", "00041", "00042", "00043", "00044", "00045", "00046", "00047", "00048", "00049", "00050", "00051", "00052", "00053", "00054", "00055", "00056", "00057", "00058", "00059", "00060", "00061", "00062", "00063", "00064", "00065", "00066", "00067", "00068", "00069", "00070", "00071", "00072", "00073", "00074", "00075", "00076", "00077", "00078", "00079", "00080", "00081", "00082", "00083", "00084", "00085", "00086", "00087", "00088", "00089", "00090", "00091", "00092", "00093", "00094", "00095", "00096", "00097", "00098", "00099",],
    ["0000", "0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008", "0009", "0010", "0011", "0012", "0013", "0014", "0015", "0016", "0017", "0018", "0019", "0020", "0021", "0022", "0023", "0024", "0025", "0026", "0027", "0028", "0029", "0030", "0031", "0032", "0033", "0034", "0035", "0036", "0037", "0038", "0039", "0040", "0041", "0042", "0043", "0044", "0045", "0046", "0047", "0048", "0049", "0050", "0051", "0052", "0053", "0054", "0055", "0056", "0057", "0058", "0059", "0060", "0061", "0062", "0063", "0064", "0065", "0066", "0067", "0068", "0069", "0070", "0071", "0072", "0073", "0074", "0075", "0076", "0077", "0078", "0079", "0080", "0081", "0082", "0083", "0084", "0085", "0086", "0087", "0088", "0089", "0090", "0091", "0092", "0093", "0094", "0095", "0096", "0097", "0098", "0099",],
    ["000", "001", "002", "003", "004", "005", "006", "007", "008", "009", "010", "011", "012", "013", "014", "015", "016", "017", "018", "019", "020", "021", "022", "023", "024", "025", "026", "027", "028", "029", "030", "031", "032", "033", "034", "035", "036", "037", "038", "039", "040", "041", "042", "043", "044", "045", "046", "047", "048", "049", "050", "051", "052", "053", "054", "055", "056", "057", "058", "059", "060", "061", "062", "063", "064", "065", "066", "067", "068", "069", "070", "071", "072", "073", "074", "075", "076", "077", "078", "079", "080", "081", "082", "083", "084", "085", "086", "087", "088", "089", "090", "091", "092", "093", "094", "095", "096", "097", "098", "099",],
    ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "70", "71", "72", "73", "74", "75", "76", "77", "78", "79", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99",],
    ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
    ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "70", "71", "72", "73", "74", "75", "76", "77", "78", "79", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99",],
    ["000000001", "000000002", "000000003", "000000004", "000000005", "000000006", "000000007", "000000008", "000000009", "000000010", "000000011", "000000012", "000000013", "000000014", "000000015", "000000016", "000000017", "000000018", "000000019", "000000020", "000000021", "000000022", "000000023", "000000024", "000000025", "000000026", "000000027", "000000028", "000000029", "000000030", "000000031", "000000032", "000000033", "000000034", "000000035", "000000036", "000000037", "000000038", "000000039", "000000040", "000000041", "000000042", "000000043", "000000044", "000000045", "000000046", "000000047", "000000048", "000000049", "000000050", "000000051", "000000052", "000000053", "000000054", "000000055", "000000056", "000000057", "000000058", "000000059", "000000060", "000000061", "000000062", "000000063", "000000064", "000000065", "000000066", "000000067", "000000068", "000000069", "000000070", "000000071", "000000072", "000000073", "000000074", "000000075", "000000076", "000000077", "000000078", "000000079", "000000080", "000000081", "000000082", "000000083", "000000084", "000000085", "000000086", "000000087", "000000088", "000000089", "000000090", "000000091", "000000092", "000000093", "000000094", "000000095", "000000096", "000000097", "000000098", "000000099", "000000100",],
    ["00000001", "00000002", "00000003", "00000004", "00000005", "00000006", "00000007", "00000008", "00000009", "00000010", "00000011", "00000012", "00000013", "00000014", "00000015", "00000016", "00000017", "00000018", "00000019", "00000020", "00000021", "00000022", "00000023", "00000024", "00000025", "00000026", "00000027", "00000028", "00000029", "00000030", "00000031", "00000032", "00000033", "00000034", "00000035", "00000036", "00000037", "00000038", "00000039", "00000040", "00000041", "00000042", "00000043", "00000044", "00000045", "00000046", "00000047", "00000048", "00000049", "00000050", "00000051", "00000052", "00000053", "00000054", "00000055", "00000056", "00000057", "00000058", "00000059", "00000060", "00000061", "00000062", "00000063", "00000064", "00000065", "00000066", "00000067", "00000068", "00000069", "00000070", "00000071", "00000072", "00000073", "00000074", "00000075", "00000076", "00000077", "00000078", "00000079", "00000080", "00000081", "00000082", "00000083", "00000084", "00000085", "00000086", "00000087", "00000088", "00000089", "00000090", "00000091", "00000092", "00000093", "00000094", "00000095", "00000096", "00000097", "00000098", "00000099", "00000100",],
    ["0000001", "0000002", "0000003", "0000004", "0000005", "0000006", "0000007", "0000008", "0000009", "0000010", "0000011", "0000012", "0000013", "0000014", "0000015", "0000016", "0000017", "0000018", "0000019", "0000020", "0000021", "0000022", "0000023", "0000024", "0000025", "0000026", "0000027", "0000028", "0000029", "0000030", "0000031", "0000032", "0000033", "0000034", "0000035", "0000036", "0000037", "0000038", "0000039", "0000040", "0000041", "0000042", "0000043", "0000044", "0000045", "0000046", "0000047", "0000048", "0000049", "0000050", "0000051", "0000052", "0000053", "0000054", "0000055", "0000056", "0000057", "0000058", "0000059", "0000060", "0000061", "0000062", "0000063", "0000064", "0000065", "0000066", "0000067", "0000068", "0000069", "0000070", "0000071", "0000072", "0000073", "0000074", "0000075", "0000076", "0000077", "0000078", "0000079", "0000080", "0000081", "0000082", "0000083", "0000084", "0000085", "0000086", "0000087", "0000088", "0000089", "0000090", "0000091", "0000092", "0000093", "0000094", "0000095", "0000096", "0000097", "0000098", "0000099", "0000100",],
    ["000001", "000002", "000003", "000004", "000005", "000006", "000007", "000008", "000009", "000010", "000011", "000012", "000013", "000014", "000015", "000016", "000017", "000018", "000019", "000020", "000021", "000022", "000023", "000024", "000025", "000026", "000027", "000028", "000029", "000030", "000031", "000032", "000033", "000034", "000035", "000036", "000037", "000038", "000039", "000040", "000041", "000042", "000043", "000044", "000045", "000046", "000047", "000048", "000049", "000050", "000051", "000052", "000053", "000054", "000055", "000056", "000057", "000058", "000059", "000060", "000061", "000062", "000063", "000064", "000065", "000066", "000067", "000068", "000069", "000070", "000071", "000072", "000073", "000074", "000075", "000076", "000077", "000078", "000079", "000080", "000081", "000082", "000083", "000084", "000085", "000086", "000087", "000088", "000089", "000090", "000091", "000092", "000093", "000094", "000095", "000096", "000097", "000098", "000099", "000100",],
    ["00001", "00002", "00003", "00004", "00005", "00006", "00007", "00008", "00009", "00010", "00011", "00012", "00013", "00014", "00015", "00016", "00017", "00018", "00019", "00020", "00021", "00022", "00023", "00024", "00025", "00026", "00027", "00028", "00029", "00030", "00031", "00032", "00033", "00034", "00035", "00036", "00037", "00038", "00039", "00040", "00041", "00042", "00043", "00044", "00045", "00046", "00047", "00048", "00049", "00050", "00051", "00052", "00053", "00054", "00055", "00056", "00057", "00058", "00059", "00060", "00061", "00062", "00063", "00064", "00065", "00066", "00067", "00068", "00069", "00070", "00071", "00072", "00073", "00074", "00075", "00076", "00077", "00078", "00079", "00080", "00081", "00082", "00083", "00084", "00085", "00086", "00087", "00088", "00089", "00090", "00091", "00092", "00093", "00094", "00095", "00096", "00097", "00098", "00099", "00100",],
    ["0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008", "0009", "0010", "0011", "0012", "0013", "0014", "0015", "0016", "0017", "0018", "0019", "0020", "0021", "0022", "0023", "0024", "0025", "0026", "0027", "0028", "0029", "0030", "0031", "0032", "0033", "0034", "0035", "0036", "0037", "0038", "0039", "0040", "0041", "0042", "0043", "0044", "0045", "0046", "0047", "0048", "0049", "0050", "0051", "0052", "0053", "0054", "0055", "0056", "0057", "0058", "0059", "0060", "0061", "0062", "0063", "0064", "0065", "0066", "0067", "0068", "0069", "0070", "0071", "0072", "0073", "0074", "0075", "0076", "0077", "0078", "0079", "0080", "0081", "0082", "0083", "0084", "0085", "0086", "0087", "0088", "0089", "0090", "0091", "0092", "0093", "0094", "0095", "0096", "0097", "0098", "0099", "0100",],
    ["001", "002", "003", "004", "005", "006", "007", "008", "009", "010", "011", "012", "013", "014", "015", "016", "017", "018", "019", "020", "021", "022", "023", "024", "025", "026", "027", "028", "029", "030", "031", "032", "033", "034", "035", "036", "037", "038", "039", "040", "041", "042", "043", "044", "045", "046", "047", "048", "049", "050", "051", "052", "053", "054", "055", "056", "057", "058", "059", "060", "061", "062", "063", "064", "065", "066", "067", "068", "069", "070", "071", "072", "073", "074", "075", "076", "077", "078", "079", "080", "081", "082", "083", "084", "085", "086", "087", "088", "089", "090", "091", "092", "093", "094", "095", "096", "097", "098", "099", "100",],
    ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "70", "71", "72", "73", "74", "75", "76", "77", "78", "79", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99",],
    ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "70", "71", "72", "73", "74", "75", "76", "77", "78", "79", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "100",],
    ["aaaaaaaaa", "aaaaaaaab", "aaaaaaaac", "aaaaaaaad", "aaaaaaaae", "aaaaaaaaf", "aaaaaaaag", "aaaaaaaah", "aaaaaaaai", "aaaaaaaaj", "aaaaaaaak", "aaaaaaaal", "aaaaaaaam", "aaaaaaaan", "aaaaaaaao", "aaaaaaaap", "aaaaaaaaq", "aaaaaaaar", "aaaaaaaas", "aaaaaaaat", "aaaaaaaau", "aaaaaaaav", "aaaaaaaaw", "aaaaaaaax", "aaaaaaaay", "aaaaaaaaz", "aaaaaaaba", "aaaaaaabb", "aaaaaaabc", "aaaaaaabd", "aaaaaaabe", "aaaaaaabf", "aaaaaaabg", "aaaaaaabh", "aaaaaaabi", "aaaaaaabj", "aaaaaaabk", "aaaaaaabl", "aaaaaaabm", "aaaaaaabn", "aaaaaaabo", "aaaaaaabp", "aaaaaaabq", "aaaaaaabr", "aaaaaaabs", "aaaaaaabt", "aaaaaaabu", "aaaaaaabv", "aaaaaaabw", "aaaaaaabx", "aaaaaaaby", "aaaaaaabz", "aaaaaaaca", "aaaaaaacb", "aaaaaaacc", "aaaaaaacd", "aaaaaaace", "aaaaaaacf", "aaaaaaacg", "aaaaaaach", "aaaaaaaci", "aaaaaaacj", "aaaaaaack", "aaaaaaacl", "aaaaaaacm", "aaaaaaacn", "aaaaaaaco", "aaaaaaacp", "aaaaaaacq", "aaaaaaacr", "aaaaaaacs", "aaaaaaact", "aaaaaaacu", "aaaaaaacv", "aaaaaaacw", "aaaaaaacx", "aaaaaaacy", "aaaaaaacz", "aaaaaaada", "aaaaaaadb", "aaaaaaadc", "aaaaaaadd", "aaaaaaade", "aaaaaaadf", "aaaaaaadg", "aaaaaaadh", "aaaaaaadi", "aaaaaaadj", "aaaaaaadk", "aaaaaaadl", "aaaaaaadm", "aaaaaaadn", "aaaaaaado", "aaaaaaadp", "aaaaaaadq", "aaaaaaadr", "aaaaaaads", "aaaaaaadt", "aaaaaaadu", "aaaaaaadv",],
    ["aaaaaaaa", "aaaaaaab", "aaaaaaac", "aaaaaaad", "aaaaaaae", "aaaaaaaf", "aaaaaaag", "aaaaaaah", "aaaaaaai", "aaaaaaaj", "aaaaaaak", "aaaaaaal", "aaaaaaam", "aaaaaaan", "aaaaaaao", "aaaaaaap", "aaaaaaaq", "aaaaaaar", "aaaaaaas", "aaaaaaat", "aaaaaaau", "aaaaaaav", "aaaaaaaw", "aaaaaaax", "aaaaaaay", "aaaaaaaz", "aaaaaaba", "aaaaaabb", "aaaaaabc", "aaaaaabd", "aaaaaabe", "aaaaaabf", "aaaaaabg", "aaaaaabh", "aaaaaabi", "aaaaaabj", "aaaaaabk", "aaaaaabl", "aaaaaabm", "aaaaaabn", "aaaaaabo", "aaaaaabp", "aaaaaabq", "aaaaaabr", "aaaaaabs", "aaaaaabt", "aaaaaabu", "aaaaaabv", "aaaaaabw", "aaaaaabx", "aaaaaaby", "aaaaaabz", "aaaaaaca", "aaaaaacb", "aaaaaacc", "aaaaaacd", "aaaaaace", "aaaaaacf", "aaaaaacg", "aaaaaach", "aaaaaaci", "aaaaaacj", "aaaaaack", "aaaaaacl", "aaaaaacm", "aaaaaacn", "aaaaaaco", "aaaaaacp", "aaaaaacq", "aaaaaacr", "aaaaaacs", "aaaaaact", "aaaaaacu", "aaaaaacv", "aaaaaacw", "aaaaaacx", "aaaaaacy", "aaaaaacz", "aaaaaada", "aaaaaadb", "aaaaaadc", "aaaaaadd", "aaaaaade", "aaaaaadf", "aaaaaadg", "aaaaaadh", "aaaaaadi", "aaaaaadj", "aaaaaadk", "aaaaaadl", "aaaaaadm", "aaaaaadn", "aaaaaado", "aaaaaadp", "aaaaaadq", "aaaaaadr", "aaaaaads", "aaaaaadt", "aaaaaadu", "aaaaaadv",],
    ["aaaaaaa", "aaaaaab", "aaaaaac", "aaaaaad", "aaaaaae", "aaaaaaf", "aaaaaag", "aaaaaah", "aaaaaai", "aaaaaaj", "aaaaaak", "aaaaaal", "aaaaaam", "aaaaaan", "aaaaaao", "aaaaaap", "aaaaaaq", "aaaaaar", "aaaaaas", "aaaaaat", "aaaaaau", "aaaaaav", "aaaaaaw", "aaaaaax", "aaaaaay", "aaaaaaz", "aaaaaba", "aaaaabb", "aaaaabc", "aaaaabd", "aaaaabe", "aaaaabf", "aaaaabg", "aaaaabh", "aaaaabi", "aaaaabj", "aaaaabk", "aaaaabl", "aaaaabm", "aaaaabn", "aaaaabo", "aaaaabp", "aaaaabq", "aaaaabr", "aaaaabs", "aaaaabt", "aaaaabu", "aaaaabv", "aaaaabw", "aaaaabx", "aaaaaby", "aaaaabz", "aaaaaca", "aaaaacb", "aaaaacc", "aaaaacd", "aaaaace", "aaaaacf", "aaaaacg", "aaaaach", "aaaaaci", "aaaaacj", "aaaaack", "aaaaacl", "aaaaacm", "aaaaacn", "aaaaaco", "aaaaacp", "aaaaacq", "aaaaacr", "aaaaacs", "aaaaact", "aaaaacu", "aaaaacv", "aaaaacw", "aaaaacx", "aaaaacy", "aaaaacz", "aaaaada", "aaaaadb", "aaaaadc", "aaaaadd", "aaaaade", "aaaaadf", "aaaaadg", "aaaaadh", "aaaaadi", "aaaaadj", "aaaaadk", "aaaaadl", "aaaaadm", "aaaaadn", "aaaaado", "aaaaadp", "aaaaadq", "aaaaadr", "aaaaads", "aaaaadt", "aaaaadu", "aaaaadv",],
    ["aaaaaa", "aaaaab", "aaaaac", "aaaaad", "aaaaae", "aaaaaf", "aaaaag", "aaaaah", "aaaaai", "aaaaaj", "aaaaak", "aaaaal", "aaaaam", "aaaaan", "aaaaao", "aaaaap", "aaaaaq", "aaaaar", "aaaaas", "aaaaat", "aaaaau", "aaaaav", "aaaaaw", "aaaaax", "aaaaay", "aaaaaz", "aaaaba", "aaaabb", "aaaabc", "aaaabd", "aaaabe", "aaaabf", "aaaabg", "aaaabh", "aaaabi", "aaaabj", "aaaabk", "aaaabl", "aaaabm", "aaaabn", "aaaabo", "aaaabp", "aaaabq", "aaaabr", "aaaabs", "aaaabt", "aaaabu", "aaaabv", "aaaabw", "aaaabx", "aaaaby", "aaaabz", "aaaaca", "aaaacb", "aaaacc", "aaaacd", "aaaace", "aaaacf", "aaaacg", "aaaach", "aaaaci", "aaaacj", "aaaack", "aaaacl", "aaaacm", "aaaacn", "aaaaco", "aaaacp", "aaaacq", "aaaacr", "aaaacs", "aaaact", "aaaacu", "aaaacv", "aaaacw", "aaaacx", "aaaacy", "aaaacz", "aaaada", "aaaadb", "aaaadc", "aaaadd", "aaaade", "aaaadf", "aaaadg", "aaaadh", "aaaadi", "aaaadj", "aaaadk", "aaaadl", "aaaadm", "aaaadn", "aaaado", "aaaadp", "aaaadq", "aaaadr", "aaaads", "aaaadt", "aaaadu", "aaaadv",],
    ["aaaaa", "aaaab", "aaaac", "aaaad", "aaaae", "aaaaf", "aaaag", "aaaah", "aaaai", "aaaaj", "aaaak", "aaaal", "aaaam", "aaaan", "aaaao", "aaaap", "aaaaq", "aaaar", "aaaas", "aaaat", "aaaau", "aaaav", "aaaaw", "aaaax", "aaaay", "aaaaz", "aaaba", "aaabb", "aaabc", "aaabd", "aaabe", "aaabf", "aaabg", "aaabh", "aaabi", "aaabj", "aaabk", "aaabl", "aaabm", "aaabn", "aaabo", "aaabp", "aaabq", "aaabr", "aaabs", "aaabt", "aaabu", "aaabv", "aaabw", "aaabx", "aaaby", "aaabz", "aaaca", "aaacb", "aaacc", "aaacd", "aaace", "aaacf", "aaacg", "aaach", "aaaci", "aaacj", "aaack", "aaacl", "aaacm", "aaacn", "aaaco", "aaacp", "aaacq", "aaacr", "aaacs", "aaact", "aaacu", "aaacv", "aaacw", "aaacx", "aaacy", "aaacz", "aaada", "aaadb", "aaadc", "aaadd", "aaade", "aaadf", "aaadg", "aaadh", "aaadi", "aaadj", "aaadk", "aaadl", "aaadm", "aaadn", "aaado", "aaadp", "aaadq", "aaadr", "aaads", "aaadt", "aaadu", "aaadv",],
    ["aaaa", "aaab", "aaac", "aaad", "aaae", "aaaf", "aaag", "aaah", "aaai", "aaaj", "aaak", "aaal", "aaam", "aaan", "aaao", "aaap", "aaaq", "aaar", "aaas", "aaat", "aaau", "aaav", "aaaw", "aaax", "aaay", "aaaz", "aaba", "aabb", "aabc", "aabd", "aabe", "aabf", "aabg", "aabh", "aabi", "aabj", "aabk", "aabl", "aabm", "aabn", "aabo", "aabp", "aabq", "aabr", "aabs", "aabt", "aabu", "aabv", "aabw", "aabx", "aaby", "aabz", "aaca", "aacb", "aacc", "aacd", "aace", "aacf", "aacg", "aach", "aaci", "aacj", "aack", "aacl", "aacm", "aacn", "aaco", "aacp", "aacq", "aacr", "aacs", "aact", "aacu", "aacv", "aacw", "aacx", "aacy", "aacz", "aada", "aadb", "aadc", "aadd", "aade", "aadf", "aadg", "aadh", "aadi", "aadj", "aadk", "aadl", "aadm", "aadn", "aado", "aadp", "aadq", "aadr", "aads", "aadt", "aadu", "aadv",],
    ["aaa", "aab", "aac", "aad", "aae", "aaf", "aag", "aah", "aai", "aaj", "aak", "aal", "aam", "aan", "aao", "aap", "aaq", "aar", "aas", "aat", "aau", "aav", "aaw", "aax", "aay", "aaz", "aba", "abb", "abc", "abd", "abe", "abf", "abg", "abh", "abi", "abj", "abk", "abl", "abm", "abn", "abo", "abp", "abq", "abr", "abs", "abt", "abu", "abv", "abw", "abx", "aby", "abz", "aca", "acb", "acc", "acd", "ace", "acf", "acg", "ach", "aci", "acj", "ack", "acl", "acm", "acn", "aco", "acp", "acq", "acr", "acs", "act", "acu", "acv", "acw", "acx", "acy", "acz", "ada", "adb", "adc", "add", "ade", "adf", "adg", "adh", "adi", "adj", "adk", "adl", "adm", "adn", "ado", "adp", "adq", "adr", "ads", "adt", "adu", "adv",],
    ["aa", "ab", "ac", "ad", "ae", "af", "ag", "ah", "ai", "aj", "ak", "al", "am", "an", "ao", "ap", "aq", "ar", "as", "at", "au", "av", "aw", "ax", "ay", "az", "ba", "bb", "bc", "bd", "be", "bf", "bg", "bh", "bi", "bj", "bk", "bl", "bm", "bn", "bo", "bp", "bq", "br", "bs", "bt", "bu", "bv", "bw", "bx", "by", "bz", "ca", "cb", "cc", "cd", "ce", "cf", "cg", "ch", "ci", "cj", "ck", "cl", "cm", "cn", "co", "cp", "cq", "cr", "cs", "ct", "cu", "cv", "cw", "cx", "cy", "cz", "da", "db", "dc", "dd", "de", "df", "dg", "dh", "di", "dj", "dk", "dl", "dm", "dn", "do", "dp", "dq", "dr", "ds", "dt", "du", "dv",],
    ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",],
    ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "ba", "bb", "bc", "bd", "be", "bf", "bg", "bh", "bi", "bj", "bk", "bl", "bm", "bn", "bo", "bp", "bq", "br", "bs", "bt", "bu", "bv", "bw", "bx", "by", "bz", "ca", "cb", "cc", "cd", "ce", "cf", "cg", "ch", "ci", "cj", "ck", "cl", "cm", "cn", "co", "cp", "cq", "cr", "cs", "ct", "cu", "cv", "cw", "cx", "cy", "cz", "da", "db", "dc", "dd", "de", "df", "dg", "dh", "di", "dj", "dk", "dl", "dm", "dn", "do", "dp", "dq", "dr", "ds", "dt", "du", "dv",],
]
# fmt: on
####################################################################################################
####################################################################################################
coverage = "low"
print("INFO: testing with coverage set to: " + coverage)
if coverage == "low":
    part_symbols = ["-"]
    part_word = ["pt"]
    dirs_out = ["."]
    part_out = mfmv.gen_wrapped_indexable_callable()
elif coverage == "mid":
    part_symbols = ["_"]
    part_word = ["pt", ""]
    dirs_out = [None, "test"]
    part_out = ["1", "part_a", "cd0"]
elif coverage == "high":
    part_symbols = ["_", "-", " ", ""]
    part_word = ["pt", "part", ""]
    dirs_out = [None, ".", "..", "test", "test" + os.sep + "level1"]
    part_out = ["a", "1", "part_a", " pt0", "cd 6"]
else:
    raise
params = [w for w in dirs_out]
params = [[p, x + y + z] for p in params for x in part_symbols for y in part_word for z in part_symbols]
params = [p + [o] for p in params for o in part_out]
# print(params)


class MultifileMvTestCase(unittest.TestCase):
    def setUp(self):
        default_parser_args = {
            "dir_in": ".",
            "dir_out": None,
            "excludes": [],
            "regex": None,
            "inplace": False,
            "maxdepth": 5,
            "mindepth": 1,
            "part_final": "1000",
            "exts": ["mp4", "txt"],
            "exts_json": None,
            "exts_env": None,
            "range_search": [0, 1],
            "range_mv": None,
        }
        self.args = lambda: None  # hack to 'forward declare' variable
        self.set_cmd_args(default_parser_args)
        self.base = "base"
        self.ext = ".mp4"
        self.input_side_effect = ["c"] * 200
        self.generate_parts(11)
        self.mvd = []
        self.files_in = []
        self.files_out = []

    def set_cmd_args(self, dict_args):
        [setattr(self.args, k, v) for k, v in dict_args.items()]

    def generate_parts(self, length: int) -> List[str]:
        digits = len(str(length))
        self.nums = [str(i) for i in range(0, length + 1)]
        self.nums_padded = [n.zfill(digits) for i, n in enumerate(self.nums) if i < 10 ** digits - 1]

    def gen_parts(self, part_out: str, length: int) -> List[str]:
        if part_out.isdigit():
            return [str(i) for i in range(int(part_out), int(part_out) + length)]
        else:
            return gen_indexable_part_0_99_indices[-2][: length + 1]

    def listdir_side_effect(self, *args, **kwargs):
        return self.files_in if args[0] == self.args.dir_in else []

    def listdir_dirs_side_effect(self, *args, **kwargs):
        return [self.args.dir_in]

    def isfile_side_effect(self, *args, **kwargs):
        for (lhs, rhs) in self.mvd:
            if args[0] == rhs:
                assert args[0] in [
                    os.path.join(self.dir_mv, f) for f in self.files_out
                ], f"{args[0]} not in {[os.path.join(self.dir_mv, f) for f in self.files_out]}"
                return True
        for (lhs, rhs) in self.mvd:
            if args[0] == lhs:
                assert args[0] in [os.path.join(self.args.dir_in, f) for f in self.files_in]
                return False
        return args[0] in [os.path.join(self.args.dir_in, f) for f in self.files_in]

    def isdir_side_effect(self, *args, **kwargs):
        if args[0] == self.args.dir_in:
            return True
        if args[0] == self.args.dir_out:
            return True
        return False

    def multifile_mv_side_effect(self, *args, **kwargs):
        self.mvd.append((args[0], args[1]))

    def part_func_selection_terminal_side_effect(self, *args, **kwargs):
        mfmv.gen_wrapped_indexable_callable()

    def runTest(self, args, files_in, files_out, prepart, part_out):
        self.set_cmd_args(args)
        self.files_in = copy.deepcopy(files_in)
        self.files_out = copy.deepcopy(files_out)
        self.dir_mv = self.args.dir_out if self.args.dir_out != None else self.args.dir_in
        mv_pairs = [
            (os.path.join(self.args.dir_in, i), os.path.join(self.dir_mv, o))
            for i, o in zip(self.files_in, self.files_out)
        ]
        # with unittest.mock.patch('builtins.input', side_effect=self.input_side_effect): # hardcode user input
        with unittest.mock.patch(
            "argparse.ArgumentParser.parse_args", return_value=copy.deepcopy(self.args)
        ):  # hardcode user cmd line args
            with unittest.mock.patch("mfmv.listdir_dirs", side_effect=self.listdir_dirs_side_effect):
                with unittest.mock.patch("os.path.isfile", side_effect=self.isfile_side_effect):
                    with unittest.mock.patch("os.path.isdir", side_effect=self.isdir_side_effect):
                        with unittest.mock.patch("os.listdir", side_effect=self.listdir_side_effect):
                            with unittest.mock.patch("mfmv.mv_atomic", side_effect=self.multifile_mv_side_effect) as mv:
                                with unittest.mock.patch("mfmv.prepart_selection_terminal", return_value=prepart):
                                    with unittest.mock.patch("mfmv.postpart_selection_terminal", return_value=""):
                                        # with unittest.mock.patch('mfmv.part_func_selection_terminal', return_value=part_out):
                                        # with unittest.mock.patch('builtins.print'): # silence output and speed up test
                                        mfmv.main()
                                        assert len(mv.call_args_list) == len(
                                            mv_pairs
                                        ), f"{len(mv.call_args_list)} != {len(mv_pairs)}"
                                        for (args, kwargs), mv_pair in zip(mv.call_args_list, mv_pairs):
                                            assert args == mv_pair, f"{args} != {mv_pair}"

    @parameterized.parameterized.expand(params)
    def testNo1(self, dir_out, prepart, part_out):
        args = {"dir_out": dir_out, "part_out": part_out}
        files_in = [self.base + prepart + p + self.ext for p in self.nums]
        if len(part_out) < len(files_in):  # TODO:
            return
        files_out = [self.base + prepart + p + self.ext for p in part_out[0 : len(files_in)]]
        if files_in[0] == files_out[0]:
            return
        self.runTest(args, files_in, files_out, prepart, part_out)

    # @parameterized.parameterized.expand(params)
    # def testNo2(self, dir_out, prepart, part_out):
    #     args = {'dir_out':dir_out, 'part_out':part_out}
    #     self.input_side_effect = ['20', 'i', 'b mid', 'i', 'b final', 'e .ext', 'c']
    #     files_in = [self.base + prepart + str(p) + 'fluff' + self.ext for p in self.nums[1:]]
    #     files_out = ['final' + part_out[:-1]  + str(p) + '.ext' for i, p in enumerate(self.gen_parts(part_out[-1], len(files_in))) if i < len(files_in)]
    #     self.runTest(args, files_in, files_out)

    # @parameterized.parameterized.expand(params)
    # def testNo3(self, dir_out, prepart, part_out):
    #     args = {'dir_out':dir_out, 'part_out':part_out, 'range_search':[0,2]}
    #     files_in = [self.base + prepart + str(p) + self.ext for p in self.nums[2:] if prepart + str(self.nums[2]) != part_out]
    #     files_out = [self.base + part_out[:-1] + str(p) + self.ext for i, p in enumerate(self.gen_parts(part_out[-1], len(files_in))) if i < len(files_in)]
    #     self.runTest(args, files_in, files_out)

    def gen_indexable_part_funcs_fixture(self):
        funcs, lengths = zip(*mfmv.gen_indexable_part_funcs())
        wrapped_funcs = [WrappedIndexableCallable(*args) for args in zip(funcs, lengths)]
        return {"funcs": funcs, "lengths": lengths, "wrapped_funcs": wrapped_funcs}

    @unittest.mock.patch("builtins.print")
    def test_gen_indexable_part_funcs(self, print):
        dic = self.gen_indexable_part_funcs_fixture()
        for wf, length, expected in zip(dic["wrapped_funcs"], dic["lengths"], gen_indexable_part_0_99_indices):
            assert len(expected) > 0
            for actual, expected in zip(wf, expected):
                assert actual == expected, str(actual) + " != " + str(expected)
            with self.assertRaises(IndexError):
                wf[length]

    @unittest.mock.patch("builtins.print")
    def test_part_func_selection_terminal(self, print):
        dic = self.gen_indexable_part_funcs_fixture()
        with unittest.mock.patch(
            "builtins.input", side_effect=[str(i) for i in reversed(range(1, len(dic["wrapped_funcs"]) + 1))]
        ):
            for wf in reversed(dic["wrapped_funcs"]):
                actual = mfmv.part_func_selection_terminal(dic["wrapped_funcs"])
                assert wf[0] == actual[0], str(wf[0]) + " != " + str(actual[0])
                assert wf[-1] == actual[-1], str(wf[-1]) + " != " + str(actual[-1])
                assert len(wf) == len(actual), str(len(wf)) + " != " + str(len(actual))

    @unittest.mock.patch("builtins.print")
    def test_prepart_selection_terminal(self, print):
        input_side_effect = [
            "1",
            "custom_input1",
            "y",
            "1",
            "custom_input2",
            "y",
            "1",
            "custom_input3",
            "y",
            "1",
            "custom_input4",
            "n",
            "q",
        ]
        expecteds = input_side_effect[slice(1, -3, 3)] + [None]
        with unittest.mock.patch("builtins.input", side_effect=input_side_effect):
            for expected in expecteds:
                assert mfmv.prepart_selection_terminal() == expected, (
                    str(mfmv.prepart_selection_terminal()) + " != " + str(expected)
                )

    @unittest.mock.patch("builtins.print")
    def test_postpart_selection_terminal(self, print):
        input_side_effect = [
            "1",
            "custom_input1",
            "y",
            "1",
            "custom_input2",
            "y",
            "1",
            "custom_input3",
            "y",
            "1",
            "custom_input4",
            "n",
            "q",
        ]
        expecteds = input_side_effect[slice(1, -3, 3)] + [None]
        with unittest.mock.patch("builtins.input", side_effect=input_side_effect):
            for expected in expecteds:
                assert mfmv.postpart_selection_terminal() == expected, (
                    str(mfmv.postpart_selection_terminal()) + " != " + str(expected)
                )


if __name__ == "__main__":
    unittest.main()
