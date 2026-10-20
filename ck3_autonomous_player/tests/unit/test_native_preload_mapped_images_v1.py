"""Finite stage-specific mapping boundaries; no WinDLL or process is opened."""
from dataclasses import replace
from unittest import TestCase, mock
from xar_autoplayer.bridge import native_preload_mapped_images_v1 as m
from xar_autoplayer.bridge import native_loaded_provider_custody_v1 as c
from xar_autoplayer.bridge import native_loaded_provider_windows_v1 as w


class Reader:
    def __init__(self):
        self.calls = self.names = 0
        self.change = False
        self.edit = lambda row: row

    def bounds(self):
        return 0x10000, 0x1ffff, 0x1000, 64

    def query(self, pos):
        self.calls += 1
        if pos == 0x10000:
            row = m.RegionV1(48, pos, 0x2000, 0x10000, None, None)
        elif pos in (0x12000, 0x13000):
            row = m.RegionV1(48, pos, 0x1000, 0x1000, 0x12000, 0x1000000)
        else:
            row = m.RegionV1(48, pos, 0xc000, 0x10000, None, None)
        return self.edit(row)

    def mapped_name(self, base):
        self.names += 1
        return "\\Device\\HarddiskVolume1\\" + ("changed.exe" if self.change and self.names > 1 else "owned.exe")


class PreloadMappingTests(TestCase):
    def test_complete_two_walks_deduplicate_all_image_regions(self):
        reader = Reader()
        rows = m.stable_preload_images_v1(reader)
        self.assertEqual(rows, (m.PreloadImageV1(0x12000, r"\Device\HarddiskVolume1\owned.exe"),))
        self.assertEqual((reader.calls, reader.names), (8, 2))
        self.assertFalse(hasattr(rows[0], "image_size"))

    def test_partial_error_and_changed_roster_are_unknown(self):
        variants = [lambda r: replace(r, returned_bytes=47),
                    lambda r: replace(r, base=True), lambda r: replace(r, size=0),
                    lambda r: replace(r, size=2**64), lambda r: replace(r, kind=0) if r.state != 0x10000 else r,
                    lambda r: replace(r, allocation_base=0) if r.kind == 0x1000000 else r]
        for edit in variants:
            with self.subTest(edit=edit):
                reader = Reader(); reader.edit = edit
                with self.assertRaises(ValueError): m.stable_preload_images_v1(reader)
        reader = Reader(); reader.change = True
        with self.assertRaisesRegex(ValueError, "roster changed"): m.stable_preload_images_v1(reader)
        reader = Reader()
        def error87(pos): raise OSError(87, "invalid parameter inside system bounds")
        reader.query = error87
        with self.assertRaises(OSError): m.stable_preload_images_v1(reader)

    def test_free_undefined_fields_reserved_images_and_complete_empty(self):
        reader = Reader()
        reader.edit = lambda r: replace(r, state=0x2000) if r.kind == 0x1000000 else r
        self.assertEqual(len(m.stable_preload_images_v1(reader)), 1)
        reader.edit = lambda r: replace(r, state=0x10000, allocation_base=None, kind=None)
        with self.assertRaisesRegex(ValueError, "nonempty"): m.stable_preload_images_v1(reader)

    def test_native_names_bounds_and_caps_fail_closed(self):
        for name in ("", r"C:\owned.exe", "\\Device\\x\\..\\owned.exe", "\\Device\\x/owned.exe", "\\Device\\" + "x"*32768):
            with self.subTest(name=name[:50]), self.assertRaises(ValueError):
                m.validate_image_v1(m.PreloadImageV1(0x12000, name))
        reader = Reader(); reader.bounds = lambda: (True, 0x1ffff, 4096, 64)
        with self.assertRaises(ValueError): m.stable_preload_images_v1(reader)
        reader = Reader(); reader.bounds = lambda: (0x10000, 0x10000 + 65537*4096-1, 4096, 64)
        reader.query = lambda pos: m.RegionV1(48, pos, 4096, 0x10000, None, None)
        with self.assertRaisesRegex(ValueError, "region cap"): m.stable_preload_images_v1(reader)

    def test_facade_process_bookends_and_default_missing(self):
        process = c._ProcessReadbackV1(17, 134368602545256920, "20261019051054.525692+000", r"C:\owned.exe", True)
        facade = w.WindowsNativeCustodyFacadeV1(enabled=True, _api=object())
        with mock.patch.object(facade, "observe_process", side_effect=[process, replace(process, pid=18)]), \
             mock.patch.object(m, "Win32PreloadMapReaderV1", return_value=Reader()):
            with self.assertRaisesRegex(ValueError, "held process changed"):
                facade.observe_preload_mapped_images(1)
        self.assertEqual(facade._preload_mapping_phase_v1["status"], "unavailable")
        with self.assertRaises(NotImplementedError): c._CustodyOSFacadeV1().observe_preload_mapped_images(1)
        facade = w.WindowsNativeCustodyFacadeV1()
        with self.assertRaises(NotImplementedError): facade.observe_preload_mapped_images(1)
        self.assertIsNone(facade._api)
