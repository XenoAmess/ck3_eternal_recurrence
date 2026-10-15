"""Exact historical methods, executed only with offline paths in tests."""
import os

class BeforeQueueFixture:
    def artifact_bytes(self):
            # Four bounded attempt directories only; no world/state/config traversal.
            return sum(path.stat().st_size for root in (INBOX, OUTBOX, N / "p11-display-responses", Q)
                       if root.is_dir() for path in root.iterdir() if path.is_file())

class P12QueueFixture:
    def artifact_bytes(self):
            # Same four flat attempt roots; fresh enumeration, no retained byte cache.
            total = 0
            for root in (INBOX, OUTBOX, N / 'p12-display-responses', Q):
                if root.is_dir():
                    with os.scandir(root) as entries:
                        for entry in entries:
                            if entry.is_file(follow_symlinks=False):
                                total += entry.stat(follow_symlinks=False).st_size
            return total
