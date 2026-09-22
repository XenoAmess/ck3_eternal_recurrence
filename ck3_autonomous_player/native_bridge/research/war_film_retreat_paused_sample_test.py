"""Synthetic memory-reader checks, never a game/process acceptance test."""
import struct
import unittest

from war_film_retreat_paused_sample import stable_sample


class Memory:
    base = 0x140000000
    unit = 0x810000
    coordinator = 0x820000
    subunit = 0x830000
    parent = 0x840000
    war = 0x850000
    character = 0x860000
    army = 0x870000
    game = 0x880000
    jomini = 0x890000
    subject_id = 0x1000001

    def __init__(self):
        self.data = {}
        self.next_address = 0x100000
        self.put(self.base + 0x570E068, "Q", self.game)
        self.put(self.base + 0x570F7B8, "Q", self.jomini)
        self.put(self.game + 8, "i", 10660915)
        self.put(self.jomini + 0x20, "B", 1)
        for slot, obj, offset in ((0x570CC80, self.unit, 0x10), (0x57C07A8, self.coordinator, 0x10),
                                  (0x570C740, self.war, 8), (0x570C130, self.character, 0x18),
                                  (0x570C730, self.army, 0x10)):
            self.store(slot, obj, offset)
        self.put(self.base + 0x57C0798, "Q", 0)
        self.put(self.unit + 0x1C4, "i", self.subject_id)
        self.put(self.unit + 0x1D0, "Q", self.subunit)
        self.put(self.unit + 0x178, "i", self.subject_id)
        self.put(self.unit + 0x174, "i", self.subject_id)
        for obj, vtable in ((self.coordinator, 0x41923B0), (self.subunit, 0x4192778), (self.parent, 0x4191870)):
            self.put(obj, "Q", self.base + vtable)
        self.put(self.subunit + 0x40, "Q", self.parent)
        self.put(self.parent + 0x58, "Q", self.coordinator)
        self.array(self.coordinator + 0x50, "Q", [self.parent])
        self.array(self.parent + 0x40, "Q", [self.subunit])
        self.array(self.subunit + 0x10, "i", [self.subject_id])
        self.array(self.coordinator + 0x20, "i", [self.subject_id])
        self.put(self.coordinator + 0x1B50, "Q", self.coordinator)
        self.put(self.coordinator + 0x1C, "i", self.subject_id)
        self.put(self.coordinator + 0x68, "H", 16)
        self.put(self.coordinator + 0x88, "q", 40000)
        self.put(self.coordinator + 0x94, "i", 6)
        self.put(self.coordinator + 0x1B38, "i", 25)
        self.put(self.coordinator + 0x1B58, "q", 300000)
        self.put(self.coordinator + 0x1B60, "q", 600000)
        self.put(self.war + 0x288, "i", self.subject_id)
        self.put(self.war + 0x28C, "i", self.subject_id)
        self.put(self.character + 0x1B8, "Q", 0x900000)
        self.put(0x900000 + 0x1D0, "i", 5)
        self.put(self.army + 0x128, "i", 123)
        self.put(self.army + 0x1D4, "B", 0)
        self.put(self.army + 0x1EC, "B", 0)
        self.put(self.war + 0x100, "Q", 0x910000)
        self.put(0x910000 + 0x1718, "I", 0)
        for offset, value in ((0x570DF68, 50000), (0x570DF18, 40000), (0x570DF88, 75000), (0x570DF80, 50000)):
            self.put(self.base + offset, "q", value)
        self.array(self.base + 0x4F56778, "i", [5, 10, 15])
        self.array(self.base + 0x4F56760, "i", [25, 50, 75])

    def put(self, address, fmt, value):
        for i, byte in enumerate(struct.pack("<" + fmt, value)):
            self.data[address + i] = byte

    def allocate(self):
        self.next_address += 0x1000
        return self.next_address

    def array(self, address, fmt, values):
        data = self.allocate()
        self.put(address, "Q", data)
        self.put(address + 8, "i", len(values))
        self.put(address + 12, "i", len(values))
        for i, value in enumerate(values):
            self.put(data + i * struct.calcsize(fmt), fmt, value)

    def store(self, slot, obj, offset):
        storage, entries = self.allocate(), self.allocate()
        self.put(self.base + slot, "Q", storage)
        self.put(storage + 0x2C, "I", 2)
        self.put(storage + 0x20, "Q", entries)
        self.put(entries + 24, "Q", obj)
        self.put(obj + offset, "i", self.subject_id)

    def read(self, address, size):
        return bytes(self.data[address + i] for i in range(size))


class PausedResearchTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory()

    def sample(self, reader=None):
        return stable_sample(reader or self.memory.read, self.memory.base, self.memory.subject_id)

    def test_stable_sample_keeps_raw_and_does_not_claim_choice(self):
        result = self.sample()
        self.assertEqual(result["proof_layer"], "stable-paused-raw-memory-only")
        self.assertFalse(result["producer_observed"])
        self.assertFalse(result["native_choice_proven"])
        self.assertEqual(result["samples"][0]["values"]["score_1b38_raw"], 25)
        self.assertEqual(result["samples"][0], result["samples"][1])
        self.assertTrue(result["samples"][0]["raw_reads"])

    def test_unpaused_rejected(self):
        self.memory.put(self.memory.jomini + 0x20, "B", 0)
        with self.assertRaisesRegex(ValueError, "requires paused"):
            self.sample()

    def test_stale_full_id_rejected(self):
        self.memory.put(self.memory.unit + 0x10, "i", 0x2000001)
        with self.assertRaisesRegex(ValueError, "generation mismatch"):
            self.sample()

    def test_stale_war_rejected(self):
        self.memory.put(self.memory.war + 8, "i", 0x2000001)
        with self.assertRaisesRegex(ValueError, "generation mismatch"):
            self.sample()

    def test_wrong_cache_backlink_rejected(self):
        self.memory.put(self.memory.coordinator + 0x1B50, "Q", self.memory.parent)
        with self.assertRaisesRegex(ValueError, "cache backlink mismatch"):
            self.sample()

    def test_wrong_membership_rejected(self):
        self.memory.array(self.memory.subunit + 0x10, "i", [0x1000002])
        with self.assertRaisesRegex(ValueError, "subject membership mismatch"):
            self.sample()

    def test_changed_sample_rejected(self):
        reads = 0
        def changed(address, size):
            nonlocal reads
            if address == self.memory.coordinator + 0x1B38:
                reads += 1
                self.memory.put(address, "i", 24 + reads)
            return self.memory.read(address, size)
        with self.assertRaisesRegex(ValueError, "sample changed"):
            self.sample(changed)

    def test_frame_change_rejected(self):
        reads = 0
        def changed(address, size):
            nonlocal reads
            if address == self.memory.game + 8:
                reads += 1
                self.memory.put(address, "i", 10660915 + reads)
            return self.memory.read(address, size)
        with self.assertRaisesRegex(ValueError, "frame changed"):
            self.sample(changed)

    def test_unbounded_array_rejected(self):
        self.memory.put(self.memory.coordinator + 0x58, "i", 1000000)
        with self.assertRaisesRegex(ValueError, "invalid bounded array"):
            self.sample()


if __name__ == "__main__":
    unittest.main(verbosity=2)
