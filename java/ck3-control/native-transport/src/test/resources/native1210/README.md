# CK3 1.21 Core producer fixtures

These are unchanged outputs of the C++ `ck3_1210_core_frame_v1.cpp` software fixture, not handwritten expected packets. The serializer source SHA-256 was `724cb6fb0ae91412b6fe6937d1a7be62a7b8e169c9c1b36b71d259d3ca6f167a`; the original production/fixture qualification is recorded in `CORE-PRODUCER-PACKETS02.json` under the migration evidence root. No game code executed to produce these files.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| core-producer-partial.json | 599 | 1d7df534e64680a88b4a40665b175c15b1928c47f0cdd0c5058ef381063d9ec6 |
| core-producer-unavailable.json | 620 | 4a1c50df66540be46f59d210ae53eaf318ae0f7089b3663a6eed0cd4bdf2c38d |
| application-exit-producer-ack01.json | 533 | 3fe5153d80540f848ec18b4c37fefccbcd4664216aefcfddc550c8c2be3ad6a6 |

Both Java receiver tests check the entire payload hash before use. An explicit absolute `xar.native.core1210.fixtures` directory can replace the classpath source for producer-to-consumer qualification, with the same exact checks. Partial Core data and submission ACKs grant no full snapshot, domain readiness, engine-effect, or confirmed SAVE status.

The application-exit fixture is a full command-result emitted by the Native application-exit serializer through its software callback fixture (`APPLICATION-EXIT-PRODUCER01.json`). The Java test retains its exact result token while supplying the actual software request ID in the enclosing replay. Deliberately changed negative results are marked as test DATA and are not additional observed Native outputs.
