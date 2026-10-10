# Guardian factory creation input observation (1.20.0.4)

The existing private Guardian capture uses the same NativeDriver family query
and native paused job. Each fixed factory row may now carry
`factory_create_inputs_v1` with independently available raw DWORD `+0x10` and
QWORD `+0x18`. The DWORD reuses `record_name_id`; the QWORD is a new guarded
eight-byte read. The existing opaque descriptor comes from `+0x08` and remains
separate.

The Python capture wrapper validates the sibling against its retained original
command request, native revision, date, played character, exact executable and
heir binding. The original ordered keys, stored names, name/map/record IDs,
factory addresses, vtables and virtual-slot address/RVA bindings remain in an
owned native copy under `native_factory_discovery_v1`. The input fields keep
their native per-row shape. An observed zero remains available; a failed read
remains false/null. A legacy packet without either sibling keeps its original
capture result. Malformed new siblings fail the private capture decoder after
the ordinary family result has already been saved independently.

These observations assign no role to the QWORD or virtual slots and do not
invoke Create, Evaluate, allocation or initialization. They do not establish
Guardian membership, pair readiness or gameplay outcomes. The retained R92
capture predates the QWORD observer and supplies no historical `+0x18` value.

Qualification is a single joined software check using five newly emitted 52f
production serializer wires. One fake response traverses the existing driver
method and private transport; four additional native failure wires exercise
independent decoder availability. This uses owned synthetic native inputs and
does not establish CK3 runtime values. The external 59f/52f delivery receipts
record the actual execution result; source authoring alone is not a GREEN run.
