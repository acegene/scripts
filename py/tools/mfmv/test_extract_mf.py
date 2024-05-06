import unittest

# from typing import List, Sequence  # declaration of parameter and return types

import parameterized  # type: ignore [import-untyped] # python3 -m pip install parameterized

from tools import mfmv

# fmt: off
PARAMS = (
    (
        ("text1.mp4", "text2.mp4", "text3.mp4"),
        ([("base", "text"), ("prepart", ""), ("parts", ("1", "2", "3")), ("postpart", ""), ("ext", ".mp4")],),
    ),
    (
        ("texta.mp4", "textb.mp4", "textc.mp4"),
        ([("base", "text"), ("prepart", ""), ("parts", ("a", "b", "c")), ("postpart", ""), ("ext", ".mp4")],),
    ),
    (
        ("text1.mp4", "text2.mp4", "text3.mp4", "text4.mp4", "text5.mp4", "text6.mp4", "text7.mp4", "text8.mp4", "text9.mp4", "text10.mp4", "text11.mp4"),
        ([("base", "text"), ("prepart", ""), ("parts", ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11")), ("postpart", ""), ("ext", ".mp4")],),
    ),
    (
        ("text0.mp4", "text1.mp4", "text2.mp4", "text3.mp4"),
        ([("base", "text"), ("prepart", ""), ("parts", ("0", "1", "2", "3")), ("postpart", ""), ("ext", ".mp4")],),
    ),
    (
        ("text1.mp4", "text2.mp4", "text11.mp4", "text12.mp4"),
        (
            [("base", "text"), ("prepart", ""), ("parts", ("1", "2")), ("postpart", ""), ("ext", ".mp4")],
            [("base", "text1"), ("prepart", ""), ("parts", ("1", "2")), ("postpart", ""), ("ext", ".mp4")],
        ),
    ),
    (
        ("text.mp4", "text1.mp4", "text2.mp4", "text3.mp4"),
        ([("base", "text"), ("prepart", ""), ("parts", ("", "1", "2", "3")), ("postpart", ""), ("ext", ".mp4")],),
    ),
)
# fmt: on


class ExtractMF(unittest.TestCase):
    def setUp(self):
        pass

    @parameterized.parameterized.expand(PARAMS)
    def test_no_1(self, files_in, expected_mf_details):
        mf_details = mfmv.Multifile.extract_mfs(files_in)
        self.assertEqual(len(expected_mf_details), len(mf_details), (expected_mf_details, mf_details))
        for expected_mf_detail, mf_detail in zip(expected_mf_details, mf_details):
            self.assertTrue(all(k in mf_detail for k, _v in expected_mf_detail))
            for k, v in expected_mf_detail:
                if isinstance(v, tuple):
                    self.assertEqual(len(v), len(mf_detail[k]), (v, mf_detail[k]))
                    for ee, e in zip(v, mf_detail[k]):
                        self.assertEqual(ee, e, (ee, e))
                else:
                    self.assertEqual(v, mf_detail[k], type(mf_detail[k]))


if __name__ == "__main__":
    unittest.main()
