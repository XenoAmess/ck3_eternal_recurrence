# Current pair child-list relation bonus, CK3 1.20.0.4

The actual pair provider adds its loaded relation scalar only when either
partner's current primary-spouse full ID matches the other, and its child-list
checks find no child-parent witness for the other partner. Either empty list
goes directly to the additive branch. This is a current numerical input branch;
it does not establish a conception probability or a pregnancy/birth outcome.

Exact build: Steam 25734779 / 1.20.0.4, held executable SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The parent provider source and this helper source are bound in
[SOURCE-CLOSURE.json](SOURCE-CLOSURE.json). No full EXE hash or section scan was
performed for this packet. The helper spans three reached PDATA fragments:
`2B955C0..2B955E3` (35 B), `2B955E3..2B95653` (112 B), and
`2B95653..2B95664` (17 B), a total of 164 newly read bytes using shared range
claims. The 35 B first PDATA interval alone is not the complete predicate.

The list receiver is Family+38, its DWORD pointer is receiver+0 and its signed
count receiver+C (Family+44). Character+1A8 supplies Family; null Family selects
the caller's static default list at RVA5D59588. Existing actual4 descendant
source names this receiver and parent slots0/4. This is independent of the
other offspring-count provider and the close-relation provider.

For each stored DWORD, the helper uses low24 bits as the Character storage
index, checks storage capacity+2C, follows slots+20 with stride16/pointer+8,
and requires object+18 to equal the complete stored DWORD. A native miss
selects the default Character from slot5C67570. It then checks the entry's
Family+1A8 parent slot+4 or+0 against the queried other's complete ID+18.
The other must have type `0x43686172` at+1C and ID other than FFFFFFFF. No
liveness gate excludes a dead child. The predicate is a parent witness in a
child list, not direct membership of the other partner's ID.

Provider2B95670 first/second receivers are R14/R13. At2B960C1 the first list is
queried against the second Character; a true AL jumps to2B960FB and skips the
relation add. Only false calls2B960D0 with second list and first Character.
Both false reaches2B960D9 and adds the signed QWORD from5C69DB8. Either
Character+1C0 nonnull additionally adds5C69DC0 at2B960F4. Their loaded numeric
values and the remainder of pair arithmetic remain the owning numeric/provider
packets' scope.

The standalone candidate leaf captures only these household inputs and
publishes the bonus conditions. `BindConceptionPairListBonus12004` binds the
exact build, image base and Root's memory-copy callback;
`ReadConceptionPairListBonusForCharacters12004` accepts Root's two resolved
household pointers and complete IDs. It preserves the native short-circuit
order, so counts/witnesses not evaluated remain absent. Failed required reads
remain unavailable. Its pure `ConceptionPairRelationBonusCondition12004`
retains this distinction without loading game objects or loaded scalar values.

The single new [focus result](focus01/RESULT.json) is GREEN: two candidate
translation units compiled with MSVC `/W4 /WX`, ten owned-memory scenes and
three pure-condition checks passed. Cases include first empty/null-Family
default list, both parent slots, second-list short-circuit, dead child, stale
generation selecting the native default Character, unread parent, negative
nonempty count and wrong build. Existing FIRST was not replayed. The numerical
composition, shared query/core wiring and live qualification remain Root's
integration; the candidate is qualified offline only. The source tree was
frozen before leaf code; no Game, SDK or gameplay operation occurred.

The project EXE exclusion hook returned `settings_failed` with
`admin_required_for_verified_readback`; no setting addition was attempted.
The actual receipt is retained under `focus01/defender-exe-exclusions/`.
The fixture completed successfully, and this packet does not claim the
exclusion is active.
