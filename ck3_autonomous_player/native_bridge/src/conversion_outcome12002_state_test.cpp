#include "xar_bridge/conversion_outcome12002_state.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace c = xar::ck3_12002;
namespace r = c::religion;
namespace g = r::conversion_gates;
namespace o = c::religion_conversion::outcome::state;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &b, std::size_t at, T value) {
  std::memcpy(b.data() + at, &value, sizeof(value));
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{}; Bytes<0x1F8> players{}; Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{}; std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{}, rite_storage{}; Bytes<0x100> slots{}, rite_slots{};
  Bytes<0x1D8> actor{}; Bytes<0x500> rite{};
  Bytes<0x308> resources{}; Bytes<0x30> flags{}, atom_pool{}; Bytes<0x60> rows{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *rite_storage_ptr = rite_storage.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t target_id = 0x85000007U;
  static constexpr std::array<std::uint32_t, 3> atoms{0x01000051U, 0x02000062U, 0x03000073U};
  std::array<bool, 3> registered{true, true, true};
  std::int64_t knowledge = 25'000, current = 70'000;
  bool lookup_fails = false, flags_missing = false, knowledge_fails = false, fulfillment_fails = false;
  bool knowledge_changes = false, flags_change = false, date_changes = false;
  int knowledge_calls = 0, fulfillment_calls = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, actor.data()); Put(actor, 0x18, actor_id);
    Put(rite_storage, 0x20, rite_slots.data()); Put(rite_storage, 0x2C, std::int32_t{8});
    Put(rite_slots, 7 * 0x10 + 8, rite.data()); Put(rite, r::kReferenceIdentityOffset, target_id);
    Put(actor, g::kCharacterScriptDataOffset, resources.data()); Put(resources, 0, std::int32_t{4});
    Put(resources, o::kBaselineFulfillmentOffset, std::int64_t{-10'000});
    Put(flags, g::kFlagRowsOffset, rows.data()); Put(flags, g::kFlagCountOffset, std::int32_t{3});
    Put(flags, o::kFlagCurrentCounterOffset, std::int32_t{110});
    const std::int32_t expiry[]{173, 112, -1};
    for (std::size_t i = 0; i < 3; ++i) {
      Put(rows, i * g::kFlagRowStride + g::kFlagKeyOffset, atoms[i]);
      Put(rows, i * g::kFlagRowStride + o::kFlagExpiryCounterOffset, expiry[i]);
    }
    Put(atom_pool, 0x10, rows.data()); Put(atom_pool, 0x1C, std::int32_t{15});
  }
};
Fixture *q = nullptr;
void *Player(void *) { return q->player.data(); }
void *Flags(void *resources) {
  if (resources != q->resources.data() || q->flags_missing) return nullptr;
  return q->flags.data();
}
std::uint32_t *Lookup(void *pool, std::uint32_t *out, const o::NativeStringView *key) {
  if (pool != q->atom_pool.data() || key->range_comparison != 1 || q->lookup_fails) return nullptr;
  const std::string_view name(key->data, static_cast<std::size_t>(key->length));
  const char *keys[]{o::kRecentConversionFlag, o::kConversionMemoryFlag, o::kNarrativeRecentConvertFlag};
  for (std::size_t i = 0; i < 3; ++i) {
    if (name == keys[i]) { *out = q->registered[i] ? Fixture::atoms[i] : r::kAbsentReference; return out; }
  }
  return nullptr;
}
std::int64_t *Knowledge(std::int64_t *out, void *actor, void *rite) {
  if (actor != q->actor.data() || rite != q->rite.data() || q->knowledge_fails) return nullptr;
  *out = q->knowledge + (q->knowledge_changes ? q->knowledge_calls : 0);
  ++q->knowledge_calls;
  return out;
}
std::int64_t *Fulfillment(void *actor, std::int64_t *out) {
  if (actor != q->actor.data() || q->fulfillment_fails) return nullptr;
  *out = q->current;
  if (q->flags_change) Put(q->rows, o::kFlagExpiryCounterOffset, std::int32_t{173 + q->fulfillment_calls});
  if (q->date_changes) Put(q->state, 8, std::int32_t{53175817});
  ++q->fulfillment_calls;
  return out;
}
o::Bindings Bind(Fixture &fixture) {
  q = &fixture;
  o::Bindings b{}; b.enabled = true;
  b.core = {true, &q->state_ptr, &q->jomini_ptr, &q->storage_ptr, &Player};
  b.rite_storage_slot = &q->rite_storage_ptr;
  b.rite_knowledge = &Knowledge; b.existing_atom = &Lookup; b.atom_pool = q->atom_pool.data();
  b.character_flag_collection = &Flags; b.character_spiritual_fulfillment = &Fulfillment;
  return b;
}
int checks = 0;
bool Check(bool value, const char *name) {
  ++checks; if (!value) std::cerr << "FAIL " << name << '\n'; return value;
}
void Wire(const std::filesystem::path &dir, const char *name, const o::Context &out) {
  if (!dir.empty()) std::ofstream(dir/name) << o::SerializePlayedConversionOutcomeState12002(out) << '\n';
}
} // namespace
int main(int argc, char **argv) {
  const auto dir = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture f; const auto b = Bind(f); o::Context out{};
  if (!Check(o::ReadPlayedConversionOutcomeState12002(b, Fixture::target_id, 901, out), "actual provider before snapshot") ||
      !Check(out.capture_epoch == 901 && out.date_raw == 53175816 &&
             out.played_character_id == static_cast<std::uint32_t>(Fixture::actor_id) &&
             out.target_rite_id == Fixture::target_id, "played frame and full target") ||
      !Check(out.knowledge_level_raw == 25'000 && out.spiritual_fulfillment_raw == 70'000 &&
             out.baseline_spiritual_fulfillment_raw == -10'000, "independent actual knowledge current and baseline") ||
      !Check(out.faith_conversion_recently_converted.present == true &&
             out.faith_conversion_recently_converted.expiry_counter_raw == 173 &&
             out.faith_conversion_recently_converted.current_counter_raw == 110 &&
             out.faith_conversion_recently_converted.remaining_updates == 63, "actual expiry not fixed five years") ||
      !Check(out.conversion_memory_recently_created.present == true &&
             out.conversion_memory_recently_created.remaining_updates == 2, "independent memory flag") ||
      !Check(out.recent_convert.present == true && out.recent_convert.timed == false &&
             out.recent_convert.expiry_counter_raw == -1 && !out.recent_convert.remaining_updates,
             "actual permanent sentinel not fixed twenty years")) return 1;
  Wire(dir, "before-actual-state.json", out);
  f.knowledge = 60'001; f.current = -5'000; Put(f.resources, o::kBaselineFulfillmentOffset, std::int64_t{8'000});
  Put(f.flags, o::kFlagCurrentCounterOffset, std::int32_t{111});
  Put(f.rows, g::kFlagRowStride + g::kFlagKeyOffset, std::uint32_t{0x04000084U});
  if (!Check(o::ReadPlayedConversionOutcomeState12002(b, Fixture::target_id, 902, out) &&
             out.knowledge_level_raw == 60'001 && out.spiritual_fulfillment_raw == -5'000 &&
             out.baseline_spiritual_fulfillment_raw == 8'000, "after fixture separately calls same full target") ||
      !Check(out.conversion_memory_recently_created.present == false &&
             !out.conversion_memory_recently_created.expiry_counter_raw &&
             out.faith_conversion_recently_converted.remaining_updates == 62, "actual absent memory and current counter")) return 2;
  Wire(dir, "after-actual-state.json", out);
  f.knowledge = 0; f.current = 0; Put(f.resources, o::kBaselineFulfillmentOffset, std::int64_t{0});
  Put(f.flags, g::kFlagCountOffset, std::int32_t{0});
  if (!Check(o::ReadPlayedConversionOutcomeState12002(b, Fixture::target_id, 903, out) &&
             out.knowledge_level_raw == 0 && out.spiritual_fulfillment_raw == 0 &&
             out.baseline_spiritual_fulfillment_raw == 0 && out.recent_convert.present == false,
             "legitimate zeros and flag absence remain known")) return 3;
  Wire(dir, "zero-empty-flags.json", out);
  f.registered = {false, true, false};
  if (!Check(o::ReadPlayedConversionOutcomeState12002(b, Fixture::target_id, 904, out) &&
             out.faith_conversion_recently_converted.key_registered == false &&
             out.faith_conversion_recently_converted.present == false &&
             out.conversion_memory_recently_created.key_registered == true &&
             out.recent_convert.key_registered == false, "three independent atom keys and registered absence")) return 4;
  f.registered = {true, true, true}; f.flags_missing = true;
  if (!Check(!o::ReadPlayedConversionOutcomeState12002(b, Fixture::target_id, 905, out) &&
             out.failure == o::Failure::flag_collection_unavailable &&
             !out.faith_conversion_recently_converted.present && !out.conversion_memory_recently_created.present &&
             !out.recent_convert.present && !out.knowledge_level_raw, "failed collection is unknown not absent")) return 5;
  Wire(dir, "flags-unavailable.json", out); f.flags_missing = false;
  f.knowledge_fails = true;
  if (!Check(!o::ReadPlayedConversionOutcomeState12002(b, Fixture::target_id, 906, out) &&
             out.failure == o::Failure::knowledge_unavailable && !out.knowledge_level_raw,
             "native knowledge failure stays unknown")) return 6;
  f.knowledge_fails = false; f.fulfillment_fails = true;
  if (!Check(!o::ReadPlayedConversionOutcomeState12002(b, Fixture::target_id, 907, out) &&
             out.failure == o::Failure::fulfillment_unavailable && !out.spiritual_fulfillment_raw,
             "actual fulfillment failure stays unknown")) return 7;
  Wire(dir, "fulfillment-unavailable.json", out); f.fulfillment_fails = false;
  Put(f.actor, g::kCharacterScriptDataOffset, static_cast<void *>(nullptr));
  if (!Check(o::ReadPlayedConversionOutcomeState12002(b, Fixture::target_id, 908, out) &&
             out.recent_convert.present == false && !out.baseline_spiritual_fulfillment_raw,
             "no resources legal empty flags and absent baseline")) return 8;
  Put(f.actor, g::kCharacterScriptDataOffset, f.resources.data()); Put(f.resources, 0, std::int32_t{-1});
  f.flags_missing = true;
  if (!Check(o::ReadPlayedConversionOutcomeState12002(b, Fixture::target_id, 909, out) &&
             out.recent_convert.present == false, "empty native index skips lazy getter")) return 9;
  Put(f.resources, 0, std::int32_t{4}); f.flags_missing = false;
  f.knowledge_changes = true;
  if (!Check(!o::ReadPlayedConversionOutcomeState12002(b, Fixture::target_id, 910, out) &&
             out.failure == o::Failure::state_changed, "actual target knowledge changes between samples")) return 10;
  f.knowledge_changes = false; f.flags_change = true; f.fulfillment_calls = 0;
  Put(f.flags, g::kFlagCountOffset, std::int32_t{1});
  if (!Check(!o::ReadPlayedConversionOutcomeState12002(b, Fixture::target_id, 911, out) &&
             out.failure == o::Failure::state_changed, "expiry changes between samples")) return 11;
  f.flags_change = false; f.date_changes = true;
  if (!Check(!o::ReadPlayedConversionOutcomeState12002(b, Fixture::target_id, 912, out) &&
             out.failure == o::Failure::state_changed, "core date changes during getter")) return 12;
  f.date_changes = false; Put(f.state, 8, std::int32_t{53175816});
  if (!Check(!o::ReadPlayedConversionOutcomeState12002(b, 0x05000007U, 913, out) &&
             out.failure == o::Failure::target_rite_unavailable, "stale target generation") ||
      !Check(!o::ReadPlayedConversionOutcomeState12002(b, r::kAbsentReference, 914, out) &&
             out.failure == o::Failure::target_rite_unavailable, "absent target rejected")) return 13;
  Put(f.rite, r::kReferenceIdentityOffset, std::uint32_t{0}); Put(f.rite_slots, 8, f.rite.data());
  if (!Check(o::ReadPlayedConversionOutcomeState12002(b, 0, 915, out) && out.target_rite_id == 0U,
             "target full ref zero valid")) return 14;
  Wire(dir, "target-zero.json", out);
  f.jomini[0x20] = std::byte{0};
  if (!Check(!o::ReadPlayedConversionOutcomeState12002(b, 0, 916, out) &&
             out.failure == o::Failure::frame_not_paused, "actual paused owner required")) return 15;
  f.jomini[0x20] = std::byte{1}; f.lookup_fails = true;
  if (!Check(!o::ReadPlayedConversionOutcomeState12002(b, 0, 917, out) &&
             out.failure == o::Failure::flag_pool_unavailable, "actual atom lookup checked")) return 16;
  const auto bound = o::BindConversionOutcomeStateImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(bound.enabled && bound.core.enabled &&
             reinterpret_cast<std::uintptr_t>(bound.rite_knowledge) == 0x142BDBDE0 &&
             reinterpret_cast<std::uintptr_t>(bound.character_spiritual_fulfillment) == 0x1428BCE40 &&
             reinterpret_cast<std::uintptr_t>(bound.existing_atom) == 0x143F8A3A0, "exact native addresses bound") ||
      !Check(!o::BindConversionOutcomeStateImage12002(0, c::kExecutableSha256).enabled &&
             !o::BindConversionOutcomeStateImage12002(0x140000000, "old-build").enabled, "exact hash binding")) return 17;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true native_callbacks=fixture live=false\n";
  return 0;
}
