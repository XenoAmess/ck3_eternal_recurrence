# Native software NormalExit UNKNOWN samples

machine_id: `xenoamess-full-tower-eb9d2c1186`. Native owner: `/root/rea64/m7`; Java consumer owner: `/root/java_native_exitclaim66`.

`native-software-autosave-unknown.jsonl` retains, in order, the exact software Native producer/serializer envelopes for failed toggle, missing post-read, and final frame drift. The source is M7 `resume65-m7-normal-exit-protocol-samples01/PACKETS02.jsonl`, produced on 2026-10-30. The Java consumer does not reserialize those retained payloads before NativeWire decoding.

The autosave bodies come from the actual Native owned-memory policy producer. Completion/frame loss and observation proof flags are fixture conditions applied before the real serializer; these samples do not prove a mailbox, pipe, Game, save, or OS-exit outcome. In the final sample, a successful prior post-read remains true while the enclosing frame is false and its signature is empty. Consumers must retain that UNKNOWN without granting phase completion or retry.

FILETIME `133000000000000043` is the original exact integer token, preserved through the Java public decimal-string wire conversion.
