# Episode04 Review01 actual machine audit, completion a02

The 1,199,061,934-byte Review01 movie with SHA-256
`a1abb0f2abaa06f3fd38839123e9f4ddd4c4218f8dd15e0965732d3596c69346`
completed a new whole-file frames+packets probe and strict whole video/AAC
decode on 2026-10-06. Both observed process return codes were 0.

Video has 52,074 decoded frames and packets on a 1/48000 time base with
1,600 ticks per frame. AAC presents 83,318,400 samples per channel over
1,735.8 seconds. All 81,366 decoded audio frames have original integer
PTS equal to cumulative prior samples; every adjacent gap is zero. The
first priming packet has PTS -1024 and skip_samples 1024. The actual final
packet starts at 83,317,760, has duration 640 and discard_padding 384;
the decoded final frame has 640 samples. Packet duration is already
trimmed, so its discard metadata is not subtracted a second time.

Full decoded float NaN and Inf counters are zero. Overall mixed peak is
-3.286156 dBFS and RMS -22.351325 dBFS. Source narration separately
contains 41,658,624 mono 24 kHz signed 16-bit PCM samples, 1,735.776 s,
peak -0.4390011973 dBFS and RMS -19.5606524704 dBFS, with zero samples at
integer limits. There is no separately produced whole mixed PCM file.
The 0.024 s difference is the final video-grid tail. Source narration
PCM is not claimed identical to lossy, music-mixed AAC.

`python -B portable_consumer_a02.py PACKAGE_DIRECTORY` verifies the
relative text catalog and preserved decoded clock CSV in another folder
or machine using the standard library. It performs no movie decode,
render, file transfer, listening, or independent source-media hash.
The full original stdout/stderr and PCM/WAV boundary artifacts remain
in the original external attempt; their exact identities are in the
results and reports. These binary artifacts are not part of this text
package. `audit_closed_review01_a02.py` is the actual executor source,
with explicit RuntimeError acceptance checks that survive Python -O.
Its original machine paths describe its input provenance; reproduce an
audit only with explicit paths to the corresponding media and tools.

The interrupted a01 attempt is preserved with unknown return codes and
termination cause. Its assertion-based source is historical text, not
the reusable acceptance verifier. Existing old A-only exact-PTS RED
evidence is also preserved and is not interpreted as a pass by a02.

Machine PASS does not approve subjective sound, continuous source
cleanliness, actual native-event exact frames, or human 1x complete
viewing. Human signoff remains pending. This package has no Git push,
OneDrive transfer, or remote readback claim.
