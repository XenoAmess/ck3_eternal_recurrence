#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from zg361_localization_style import (
    normalize_localization_rows,
    normalize_player_chinese,
)


class LocalizationStyleTest(unittest.TestCase):
    def test_translates_player_facing_jargon(self) -> None:
        self.assertEqual(
            normalize_player_chinese("HC owner 发出 Offer，进入 PIP"),
            "编制名额责任人发出录用邀约，进入绩效改进计划",
        )

    def test_preserves_ck3_command_payloads(self) -> None:
        source = "责任人 [scope:zg361_owner.GetShortUIName] 查看 KPI"
        self.assertEqual(
            normalize_player_chinese(source),
            "责任人 [scope:zg361_owner.GetShortUIName] 查看绩效指标",
        )

    def test_never_rewrites_localization_keys(self) -> None:
        rows = [' zg361.offer.owner:0 "Offer owner"']
        self.assertEqual(
            normalize_localization_rows(rows),
            [' zg361.offer.owner:0 "录用邀约责任人"'],
        )


if __name__ == "__main__":
    unittest.main()
