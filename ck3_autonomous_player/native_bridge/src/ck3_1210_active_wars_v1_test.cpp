#include "xar_bridge/ck3_1210_active_wars_v1.hpp"

#include <array>
#include <bit>
#include <cstring>
#include <iostream>
#include <limits>
#include <span>
#include <string_view>
#include <vector>

namespace {
using namespace xar::ck3_1210;
void *local_player = nullptr;
const void *war_a_address = nullptr, *war_b_address = nullptr;
std::byte *date_address = nullptr, *actor_id_address = nullptr, *native_mutation_address = nullptr;
std::int32_t native_mutation_value = 0;
std::int32_t score_a = 17, score_b = -33;
std::size_t core_calls = 0, native_calls = 0;
bool change_date = false, change_actor = false, score_drifts = false, wrong_native_abi = false;

void *LocalPlayer(void *) {
  ++core_calls;
  if (core_calls == 2 && change_date) {
    const std::int32_t changed = 777777;
    std::memcpy(date_address, &changed, sizeof changed);
  }
  if (core_calls == 2 && change_actor) {
    const auto changed = std::bit_cast<std::int32_t>(0x82000001U);
    std::memcpy(actor_id_address, &changed, sizeof changed);
  }
  return local_player;
}
std::int32_t FakeScore(const void *war, void *tooltip) {
  ++native_calls;
  wrong_native_abi = wrong_native_abi || tooltip != nullptr ||
      (war != war_a_address && war != war_b_address);
  if (native_calls == 1 && native_mutation_address != nullptr)
    std::memcpy(native_mutation_address, &native_mutation_value, sizeof native_mutation_value);
  if (war == war_a_address) return score_drifts && native_calls == 2 ? score_a + 1 : score_a;
  if (war == war_b_address) return score_b;
  return 0;
}
struct Memory {
  explicit Memory(std::size_t size) : bytes(size) {}
  std::vector<std::byte> bytes;
  void *data() { return bytes.data(); }
  template <class T> void Put(std::size_t offset, T value) {
    if (offset > bytes.size() || sizeof(T) > bytes.size() - offset)
      throw std::string_view("fixture write outside bounded memory");
    std::memcpy(bytes.data() + offset, &value, sizeof value);
  }
};
struct Fixture {
  static constexpr auto player = std::bit_cast<std::int32_t>(0x81000001U);
  static constexpr std::int32_t peer_a = 0x02000002, peer_b = 0x03000003;
  static constexpr auto id_a = std::bit_cast<std::int32_t>(0x84000000U);
  static constexpr std::int32_t id_b = 0x05000001, id_ended = 0x06000002;
  Memory game{0xB0}, jomini{0x28}, players{0x200}, local{0x80};
  Memory data{0x3F400}, entry{0xE0}, entries{8};
  Memory char_store{0x40}, char_slots{4 * 0x10};
  Memory actor{0x1E0}, other_a{0x1E0}, other_b{0x1E0}, zero_character{0x1E0};
  Memory war_store{0x58}, other_war_store{0x58}, war_slots{3 * 0x10};
  Memory war_a{0x370}, war_b{0x370}, ended{0x370};
  Memory attack_array_a{3 * 8}, defend_array_a{8}, attack_a{0x10}, defend_a{0x10}, zero_record{0x10};
  Memory attack_array_b{8}, defend_array_b{8}, attack_b{0x10}, defend_b{0x10};
  // An unrelated scope really may contain an actor-owned Unit. War-only
  // identity must not call the military-empty/Unit gate at all.
  Memory unit_store{0x58}, unit_slots{0x10}, unit{0x180};
  void *game_slot = nullptr, *jomini_slot = nullptr, *char_slot = nullptr, *war_slot = nullptr;
  ActiveWarsBindingsV1 bindings{};
  std::vector<std::span<const std::byte>> readable;
  const void *deny = nullptr;
  bool guard_valid = true, side_changes = false, ended_changes = false, roots_change = false;
  std::size_t attack_reads = 0, ended_reads = 0, root_reads = 0;

  Fixture() {
    core_calls = native_calls = 0;
    change_date = change_actor = score_drifts = wrong_native_abi = false;
    native_mutation_address = nullptr; score_a = 17; score_b = -33;
    local_player = local.data(); war_a_address = war_a.data(); war_b_address = war_b.data();
    date_address = game.bytes.data() + kGameStateDateOffset;
    actor_id_address = actor.bytes.data() + kCharacterFullIdOffset;
    game_slot = game.data(); jomini_slot = jomini.data();
    char_slot = char_store.data(); war_slot = war_store.data();
    bindings.exact_build_admitted = true;
    bindings.core = {true, &game_slot, &jomini_slot, &char_slot, LocalPlayer};
    bindings.war_registry_slot = &war_slot;
    bindings.war_registry_vtable = 0x104E9C188ULL;
    bindings.war_manager_vtable = 0x104E9C2C0ULL;
    bindings.war_vtable = 0x104E51D80ULL;
    bindings.get_attacker_war_score = FakeScore;
    game.Put(kGameStateDateOffset, std::int32_t{123456});
    game.Put(kGameStateSpeedOffset, std::int32_t{2}); game.Put(kGameStateDataOffset, data.data());
    jomini.Put(kJominiPlayersOffset, players.data()); jomini.Put(kJominiPausedOffset, std::uint8_t{1});
    players.Put(kPlayersLocalPlayerIdOffset, std::int32_t{0}); local.Put(kPlayerIdOffset, std::int32_t{0});
    entry.Put(kPlayerEntryLocalPlayerIdOffset, std::int32_t{0}); entry.Put(kPlayerEntryCharacterIdOffset, player);
    entries.Put(0, entry.data());
    data.Put(kPlayerCharacterManagerOffset + kPlayerManagerEntriesOffset, entries.data());
    data.Put(kPlayerCharacterManagerOffset + kPlayerManagerCountOffset, std::int32_t{1});
    char_store.Put(0x20, char_slots.data()); char_store.Put(0x2C, std::int32_t{4});
    InitCharacter(actor, player); InitCharacter(other_a, peer_a); InitCharacter(other_b, peer_b);
    InitCharacter(zero_character, 0);
    char_slots.Put(8, zero_character.data()); char_slots.Put(0x18, actor.data());
    char_slots.Put(0x28, other_a.data()); char_slots.Put(0x38, other_b.data());
    data.Put(kActiveWarsManagerOffsetV1, bindings.war_manager_vtable);
    data.Put(kActiveWarsManagerOffsetV1 + 0x20, war_slot);
    war_store.Put(0, bindings.war_registry_vtable); other_war_store.Put(0, bindings.war_registry_vtable);
    InitWar(war_a, id_a); InitWar(war_b, id_b); InitWar(ended, id_ended);
    ended.Put(0x360, std::uint8_t{1});
    attack_a.Put(8, player); defend_a.Put(8, peer_a); zero_record.Put(8, std::int32_t{0});
    attack_b.Put(8, peer_a); defend_b.Put(8, peer_b);
    attack_array_a.Put(0, attack_a.data()); attack_array_a.Put(8, zero_record.data());
    attack_array_a.Put(16, attack_a.data()); defend_array_a.Put(0, defend_a.data());
    attack_array_b.Put(0, attack_b.data()); defend_array_b.Put(0, defend_b.data());
    SetSide(war_a, 0x20, attack_array_a); SetSide(war_a, 0x80, defend_array_a);
    SetSide(war_b, 0x20, attack_array_b); SetSide(war_b, 0x80, defend_array_b);
    war_a.Put(0x290, player); war_a.Put(0x294, peer_a);
    war_b.Put(0x290, peer_a); war_b.Put(0x294, peer_b);
    unit_store.Put(0x20, unit_slots.data()); unit_store.Put(0x2C, std::int32_t{1});
    unit_slots.Put(8, unit.data()); unit.Put(0x10, std::int32_t{0});
    unit.Put(0x14, std::uint32_t{0x556E6974U}); unit.Put(0x174, player);
    data.Put(0x3ABF8 + 0x20, unit_store.data());
    for (Memory *m : std::array{&game,&jomini,&players,&local,&data,&entry,&entries,
             &char_store,&char_slots,&actor,&other_a,&other_b,&zero_character,&war_store,
             &other_war_store,&war_slots,&war_a,&war_b,&ended,&attack_array_a,&defend_array_a,
             &attack_a,&defend_a,&zero_record,&attack_array_b,&defend_array_b,&attack_b,&defend_b,
             &unit_store,&unit_slots,&unit})
      readable.emplace_back(m->bytes.data(), m->bytes.size());
    for (void **slot : std::array{&game_slot,&jomini_slot,&char_slot,&war_slot})
      readable.emplace_back(reinterpret_cast<const std::byte *>(slot), sizeof(void *));
  }
  static void InitCharacter(Memory &m, std::int32_t id) {
    m.Put(0x18, id); m.Put(0x1C, std::uint32_t{0x43686172U});
  }
  static void InitWar(Memory &m, std::int32_t id) {
    m.Put(0, std::uintptr_t{0x104E51D80ULL});
    m.Put(8, id); m.Put(0xC, std::uint32_t{0x5761725FU});
  }
  static void SetSide(Memory &war, std::size_t offset, Memory &records) {
    war.Put(offset + 8, records.data()); war.Put(offset + 0x10, std::int32_t{1});
    war.Put(offset + 0x14, std::int32_t{1});
  }
  void Populate() {
    for (Memory *store : std::array{&war_store,&other_war_store}) {
      store->Put(0x20, war_slots.data()); store->Put(0x2C, std::int32_t{3});
    }
    war_slots.Put(8, war_a.data()); war_slots.Put(24, war_b.data()); war_slots.Put(40, ended.data());
  }
  void Defender() {
    attack_a.Put(8, peer_a); defend_a.Put(8, player);
    war_a.Put(0x290, peer_a); war_a.Put(0x294, player);
  }
  CoreSnapshotPrefix Expected() {
    CoreSnapshotPrefix out{};
    if (!ReadCoreSnapshot(bindings.core, out)) throw std::string_view("fixture Core read failed");
    core_calls = 0; return out;
  }
  static bool Copy(void *context, const void *source, void *destination, std::size_t size) noexcept {
    auto &f = *static_cast<Fixture *>(context);
    if (source == f.deny) return false;
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    const auto code = reinterpret_cast<std::uintptr_t>(FakeScore);
    if (address >= code && address - code < kActiveWarsScoreEntry32V1.size() &&
        size <= kActiveWarsScoreEntry32V1.size() - (address - code)) {
      // Bounded fake code view verifies entry guarding without patching code.
      std::memcpy(destination, kActiveWarsScoreEntry32V1.data() + (address - code), size);
      if (!f.guard_valid && address == code) *static_cast<std::uint8_t *>(destination) ^= 1;
      return true;
    }
    if (source == f.attack_a.bytes.data() + 8 && ++f.attack_reads == 2 && f.side_changes) {
      f.attack_a.Put(8, peer_a); f.defend_a.Put(8, player);
      f.war_a.Put(0x290, peer_a); f.war_a.Put(0x294, player);
    }
    if (source == f.ended.bytes.data() + 0x360 && ++f.ended_reads == 2 && f.ended_changes)
      f.ended.Put(0x360, std::uint8_t{0});
    if (source == &f.war_slot && ++f.root_reads == 2 && f.roots_change) {
      f.war_slot = f.other_war_store.data();
      f.data.Put(kActiveWarsManagerOffsetV1 + 0x20, f.war_slot);
    }
    for (auto range : f.readable) {
      const auto begin = reinterpret_cast<std::uintptr_t>(range.data());
      if (address >= begin && address - begin <= range.size() &&
          size <= range.size() - (address - begin)) {
        std::memcpy(destination, source, size); return true;
      }
    }
    return false;
  }
  bool Read(const CoreSnapshotPrefix &expected, ActiveWarsObservationV1 &out) {
    return ReadActiveWarsV1(bindings, expected, out, {this, Copy});
  }
};
int failures = 0;
void Check(bool condition, std::string_view name) {
  if (!condition) { ++failures; std::cerr << "FAILED " << name << '\n'; }
}
void NotFull(const ActiveWarsObservationV1 &out) {
  Check(out.partial && !out.full_snapshot_available && !out.complete_active_wars_qualified,
      "scoped identity never grants complete ActiveWar or Full Snapshot");
}
void Reject(Fixture &f, std::string_view reason) {
  ActiveWarsObservationV1 out{}; out.available = out.identity_complete = true;
  out.active_wars.emplace();
  Check(!f.Read(f.Expected(), out), reason);
  Check(out.unavailable_reason == reason, "specific unavailable reason");
  Check(!out.available && !out.same_frame_ready && !out.identity_complete &&
      !out.active_wars.has_value(), "failed identity never retains stale/empty collection");
  NotFull(out);
}
void Binder() {
  const auto no = BindActiveWarsImageV1(0x140000000ULL, "bad");
  Check(!no.exact_build_admitted && !no.core.enabled && no.war_registry_slot == nullptr &&
      no.get_attacker_war_score == nullptr, "exact SHA gate");
  Check(!BindActiveWarsImageV1((std::numeric_limits<std::uintptr_t>::max)(),
      kExecutableSha256).exact_build_admitted, "binder overflow");
  const auto yes = BindActiveWarsImageV1(0x140000000ULL, kExecutableSha256);
  Check(yes.exact_build_admitted && !yes.integration_native_calls_permitted &&
      reinterpret_cast<std::uintptr_t>(yes.war_registry_slot) == 0x146A666D0ULL &&
      reinterpret_cast<std::uintptr_t>(yes.get_attacker_war_score) == 0x1429E8DE0ULL,
      "exact new addresses, native calls disabled by default");
}
void IdentitySuccess() {
  Fixture empty; ActiveWarsObservationV1 out{};
  Check(empty.Read(empty.Expected(), out) && out.identity_complete && out.active_wars &&
      out.active_wars->empty() && out.war_slots_scanned == 0 && native_calls == 0,
      "actual cap0/null slots is known empty"); NotFull(out);
  Fixture attack; attack.Populate();
  Check(attack.Read(attack.Expected(), out) && out.active_wars && out.active_wars->size() == 1 &&
      out.active_war_rows == 2 && out.ended_war_rows == 1 && out.participant_records == 4 &&
      out.war_slots_scanned == 3 && core_calls == 3 && native_calls == 0,
      "full scan with player attack, unrelated active and ended War, owned Unit irrelevant");
  if (out.active_wars && out.active_wars->size() == 1) {
    const auto &row = out.active_wars->front();
    Check(row.war_id == Fixture::id_a && row.actual_player_character_id == Fixture::player &&
        out.frame.local_player_id == 0 && row.actual_player_character_id != out.frame.local_player_id &&
        row.player_side == ActiveWarPlayerSideV1::attacker &&
        row.primary_attacker_character_id == Fixture::player &&
        row.primary_opponent_character_id == Fixture::peer_a && row.player_is_primary_war_leader &&
        row.attacker_participant_ids == std::vector<std::int32_t>{Fixture::player} &&
        !row.player_relative_war_score && row.score_unavailable_reason == "active_wars_native_calls_not_permitted" &&
        !row.targeted_titles_observed && !row.objectives_observed &&
        !row.allied_armies_observed && !row.enemy_armies_observed,
        "signed32 player/War identities and unobserved collections kept distinct");
  }
  Check(!out.score_complete, "gate OFF identity success is score partial");
  Fixture defend; defend.Populate(); defend.Defender();
  Check(defend.Read(defend.Expected(), out) && out.active_wars->front().player_side == ActiveWarPlayerSideV1::defender &&
      out.active_wars->front().primary_opponent_character_id == Fixture::peer_a,
      "positive player defender identity");
  Fixture zero; zero.Populate(); zero.war_a.Put(8, std::int32_t{0});
  zero.war_a.Put(0x30, std::int32_t{3}); zero.war_a.Put(0x34, std::int32_t{3});
  Check(zero.Read(zero.Expected(), out) && out.active_wars->front().war_id == 0 &&
      out.active_wars->front().attacker_participant_ids ==
          std::vector<std::int32_t>{Fixture::player,0,Fixture::player},
      "WarID zero and ordered participant zero/duplicates preserved without low24 coercion");
}
void ScoreSuccessAndPartial() {
  ActiveWarsObservationV1 out{};
  Fixture attack; attack.Populate(); attack.bindings.integration_native_calls_permitted = true;
  Check(attack.Read(attack.Expected(), out) && out.score_complete &&
      out.active_wars->front().player_relative_war_score == 17 && native_calls == 2 &&
      out.native_score_calls_attempted == 2 && !wrong_native_abi,
      "native ABI War receiver/null tooltip, attacker sign and repeated observation"); NotFull(out);
  Fixture defend; defend.Populate(); defend.Defender(); defend.bindings.integration_native_calls_permitted = true;
  Check(defend.Read(defend.Expected(), out) && out.active_wars->front().player_relative_war_score == -17,
      "defender checked sign conversion, no GUI times1000");
  Fixture zero; zero.Populate(); zero.bindings.integration_native_calls_permitted = true; score_a = 0;
  Check(zero.Read(zero.Expected(), out) && out.score_complete &&
      out.active_wars->front().player_relative_war_score.has_value() &&
      *out.active_wars->front().player_relative_war_score == 0, "native zero is a legitimate observed score");
  Fixture raw; raw.Populate(); raw.bindings.integration_native_calls_permitted = true; score_a = 1234567;
  Check(raw.Read(raw.Expected(), out) && out.active_wars->front().player_relative_war_score == score_a,
      "no invented global score clamp");
  Fixture overflow; overflow.Populate(); overflow.Defender();
  overflow.bindings.integration_native_calls_permitted = true;
  score_a = (std::numeric_limits<std::int32_t>::min)();
  Check(overflow.Read(overflow.Expected(), out) && !out.score_complete &&
      out.active_wars->front().native_attacker_score_raw == score_a &&
      !out.active_wars->front().player_relative_war_score &&
      out.active_wars->front().score_unavailable_reason == "active_wars_relative_score_overflow",
      "INT_MIN defender overflow is identity partial, never wrapped/zero");
  Fixture guard; guard.Populate(); guard.bindings.integration_native_calls_permitted = true; guard.guard_valid = false;
  Check(guard.Read(guard.Expected(), out) && !out.score_complete && native_calls == 0 &&
      out.active_wars->front().score_unavailable_reason == "active_wars_score_guard_unavailable",
      "bad guard means zero native calls and score unavailable");
  Fixture missing; missing.Populate(); missing.bindings.integration_native_calls_permitted = true;
  missing.bindings.get_attacker_war_score = nullptr;
  Check(missing.Read(missing.Expected(), out) && !out.score_complete && native_calls == 0 &&
      out.active_wars->front().score_unavailable_reason == "active_wars_score_getter_unavailable",
      "missing getter does not erase positive identity");
  Fixture drift; drift.Populate(); drift.bindings.integration_native_calls_permitted = true; score_drifts = true;
  Check(drift.Read(drift.Expected(), out) && !out.score_complete &&
      !out.active_wars->front().player_relative_war_score &&
      out.active_wars->front().score_unavailable_reason == "active_wars_score_changed",
      "score-only drift leaves honest partial identity");
}
void InvalidIdentity() {
  { Fixture f; f.Populate(); f.defend_a.Put(8, Fixture::player); Reject(f, "active_wars_player_on_both_sides"); }
  { Fixture f; f.Populate(); f.attack_a.Put(8, Fixture::peer_a);
    ActiveWarsObservationV1 out{};
    Check(f.Read(f.Expected(), out) && out.active_wars->empty(), "both sides false means unrelated, not defender"); }
  { Fixture f; f.Populate(); f.war_a.Put(8, Fixture::id_b); Reject(f, "active_wars_war_identity_invalid"); }
  { Fixture f; f.Populate(); f.war_a.Put(0xC, std::uint32_t{0}); Reject(f, "active_wars_war_identity_invalid"); }
  { Fixture f; f.Populate(); f.war_a.Put(0, std::uintptr_t{1}); Reject(f, "active_wars_war_identity_invalid"); }
  { Fixture f; f.Populate(); f.ended.Put(0x360, std::uint8_t{2}); Reject(f, "active_wars_war_identity_invalid"); }
  { Fixture f; f.Populate(); f.other_a.Put(0x18, std::int32_t{0x07000002});
    Reject(f, "active_wars_character_generation_unresolved"); }
  { Fixture f; f.Populate(); f.war_a.Put(0x294, std::int32_t{0x07000002});
    Reject(f, "active_wars_character_generation_unresolved"); }
  { Fixture f; f.war_store.Put(0x2C, kActiveWarsStorageLimitV1 + 1); Reject(f, "active_wars_storage_header_invalid"); }
  { Fixture f; f.war_store.Put(0x2C, std::int32_t{1}); Reject(f, "active_wars_storage_header_invalid"); }
  { Fixture f; f.Populate(); f.war_a.Put(0x34, std::int32_t{2}); Reject(f, "active_wars_participant_header_invalid"); }
  { Fixture f; f.Populate(); f.war_a.Put(0x28, static_cast<void *>(nullptr));
    Reject(f, "active_wars_participant_header_invalid"); }
  { Fixture f; f.Populate(); f.attack_array_a.Put(0, static_cast<void *>(nullptr));
    Reject(f, "active_wars_participant_record_invalid"); }
  { Fixture f; f.war_store.Put(0, std::uintptr_t{1}); Reject(f, "active_wars_registry_type_mismatch"); }
  { Fixture f; f.data.Put(kActiveWarsManagerOffsetV1, std::uintptr_t{1});
    Reject(f, "active_wars_registry_type_mismatch"); }
  { Fixture f; f.data.Put(kActiveWarsManagerOffsetV1 + 0x20, f.other_war_store.data());
    Reject(f, "active_wars_registry_owner_mismatch"); }
  { Fixture f; f.Populate(); f.deny = f.attack_a.bytes.data() + 8; Reject(f, "active_wars_read_failed"); }
  { Fixture f; f.Populate();
    f.war_slots.Put(8, reinterpret_cast<void *>((std::numeric_limits<std::uintptr_t>::max)() - 3));
    Reject(f, "active_wars_address_invalid"); }
}
void Changes() {
  { Fixture f; f.Populate(); f.side_changes = true; Reject(f, "active_wars_identity_changed"); }
  { Fixture f; f.Populate(); f.ended_changes = true; Reject(f, "active_wars_identity_changed"); }
  { Fixture f; f.Populate(); f.roots_change = true; Reject(f, "active_wars_identity_changed"); }
  { Fixture f; f.Populate(); auto expected = f.Expected(); change_date = true;
    ActiveWarsObservationV1 out{};
    Check(!f.Read(expected, out) && out.unavailable_reason == "core_frame_changed", "Core date drift"); }
  { Fixture f; f.Populate(); auto expected = f.Expected(); change_actor = true;
    ActiveWarsObservationV1 out{};
    Check(!f.Read(expected, out) && out.unavailable_reason == "core_frame_changed", "actual actor generation drift"); }
  { Fixture f; f.Populate(); f.bindings.integration_native_calls_permitted = true;
    native_mutation_address = f.war_a.bytes.data() + 0x294; native_mutation_value = Fixture::peer_b;
    ActiveWarsObservationV1 out{};
    Check(!f.Read(f.Expected(), out) && out.unavailable_reason == "active_wars_score_identity_changed" &&
        !out.active_wars && out.native_score_calls_attempted == 1,
        "per-score primary identity recheck and truthful attempted-call counter"); }
  { Fixture f; f.Populate(); f.bindings.integration_native_calls_permitted = true;
    native_mutation_address = f.attack_a.bytes.data() + 8; native_mutation_value = Fixture::peer_b;
    ActiveWarsObservationV1 out{};
    Check(!f.Read(f.Expected(), out) && out.unavailable_reason == "active_wars_score_identity_changed",
        "per-score complete participant membership recheck"); }
  { Fixture f; auto expected = f.Expected(); expected.clock.paused = false;
    ActiveWarsObservationV1 out{};
    Check(!f.Read(expected, out) && out.unavailable_reason == "requires_paused" && native_calls == 0,
        "running frame cannot invoke score"); }
}
} // namespace
int main() {
  try { Binder(); IdentitySuccess(); ScoreSuccessAndPartial(); InvalidIdentity(); Changes(); }
  catch (std::string_view why) { ++failures; std::cerr << why << '\n'; }
  catch (...) { ++failures; std::cerr << "unexpected fixture exception\n"; }
  if (failures == 0) std::cout << "ck3_1210 active wars NoGame fixture passed\n";
  return failures == 0 ? 0 : 1;
}
