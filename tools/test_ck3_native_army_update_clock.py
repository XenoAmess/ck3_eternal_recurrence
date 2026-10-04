"""Exactly two focused clock checks, after native source closure."""
import unittest

from ck3_native_army_update_clock import EPOCH_RAW, preview


class NativeClockCases(unittest.TestCase):
    def test_calendar_february_month_first_precedes_selected_bucket(self):
        # Native February ends at year-day 58; this month has 28 days, not 30.
        rows = preview(EPOCH_RAW + 57 * 24, 2, observed_army_bucket=29)['rows']
        self.assertEqual((rows[0]['month_index'], rows[0]['day_of_month_index']), (1, 27))
        self.assertFalse(rows[0]['calendar_month_first'])
        march_first = rows[1]
        self.assertEqual((march_first['native_day'], march_first['month_index'], march_first['day_of_month_index']), (59, 2, 0))
        self.assertTrue(march_first['calendar_month_first'])
        self.assertTrue(march_first['army_selected_by_bucket'])
        self.assertEqual(march_first['ordered_clock_stages'], [
            'pre: prepare persistent monthly fraction cache',
            'admit: date+24 and GameState+9C',
            'post: regular persistent integer fill',
            'post: refresh raised/army strengths',
            'post: select actual ArmyManager day bucket',
        ])

    def test_native_signed_calendar_and_unsigned_phase_have_distinct_domains(self):
        # One day before epoch is the last table day, with unsigned +9C%30.
        before = preview(EPOCH_RAW - 48, 1)['rows'][0]
        self.assertEqual((before['native_day'], before['year_day_index']), (-1, 364))
        self.assertEqual((before['month_index'], before['day_of_month_index']), (11, 30))
        self.assertEqual(before['actual_manager_bucket_phase'], 15)
        self.assertIsNone(before['army_selected_by_bucket'])
        # Native signed division truncates toward zero for a partial-day input.
        zero = preview(EPOCH_RAW - 25, 1, observed_army_bucket=0)['rows'][0]
        self.assertEqual(zero['native_day'], 0)
        self.assertTrue(zero['calendar_month_first'])
        self.assertEqual(zero['actual_manager_bucket_phase'], 0)
        self.assertTrue(zero['army_selected_by_bucket'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
