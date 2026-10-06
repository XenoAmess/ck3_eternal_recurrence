#include "xar_bridge/ck3_12003_confucian_assembly_predicates.hpp"

#include "xar_bridge/ck3_12002_family_query_abi.hpp"
#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/ck3_12003.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::confucian_assembly {
namespace {
namespace p = ck3_12002::phase_character;
namespace r = ck3_12002::religion;
namespace c = r::organization::members;
namespace a = ck3_12002::family_query_abi;
constexpr std::uint32_t absent = 0xFFFFFFFFU;
constexpr std::int32_t max_source_items = 1000000;

template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}

bool ReferenceMatches(const void *object, std::uint32_t id,
                      std::size_t offset) noexcept {
  return object != nullptr && id != absent && Load<std::uint32_t>(object, offset) == id;
}

void *Resolve(void **slot, std::uint32_t id, std::size_t identity) noexcept {
  if (slot == nullptr || *slot == nullptr || id == absent) return nullptr;
  const auto *storage = *slot;
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto *rows = Load<const void *>(storage, 0x20);
  const auto index = id & 0x00FFFFFFU;
  if (capacity <= 0 || rows == nullptr || index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  auto *object = Load<void *>(rows, static_cast<std::size_t>(index) * 16 + 8);
  return ReferenceMatches(object, id, identity) ? object : nullptr;
}

void *Character(const Bindings &b, std::uint32_t id) noexcept {
  if (id == absent) return nullptr;
  auto *object = ck3_12002::ResolveCoreCharacter(b.core, static_cast<std::int32_t>(id));
  return object != nullptr && Load<std::uint32_t>(object, p::kCharacterKindOffset) == 0x43686172U
      ? object : nullptr;
}

template <typename F> bool Leaf(const Bindings &b, std::uint32_t id,
                               void *expected, F read) noexcept {
  if (Character(b, id) != expected) return false;
  read();
  return Character(b, id) == expected;
}

bool Collect(Collector collector, std::uint16_t kind, std::uint32_t id,
             std::int32_t capacity, std::vector<c::ScopeValue> &out) {
  if (collector == nullptr || capacity < 0 || capacity > max_source_items) return false;
  // +1 makes capacity exhaustion observable even when every source item is a
  // member. The current exact native collector emits <= one row per source.
  out.resize(static_cast<std::size_t>(capacity) + 1);
  const auto actual_capacity = capacity + 1;
  c::ScopeArray native{out.data(), actual_capacity, 0, nullptr};
  const c::ScopeValue root{kind, 0, 0, id};
  const c::ScopeRoot context{&root};
  collector(nullptr, &native, &context);
  if (native.data != out.data() || native.capacity != actual_capacity ||
      native.allocator != nullptr || native.size < 0 || native.size > capacity) return false;
  out.resize(static_cast<std::size_t>(native.size));
  return true;
}

bool FaithRites(const Bindings &b, void *faith, std::uint32_t faith_id,
               std::vector<std::uint32_t> &out) {
  out.clear();
  const auto *container = b.faith_rites(faith);
  if (container == nullptr) return false;
  const auto count = Load<std::int32_t>(container, 0xC);
  const auto capacity = Load<std::int32_t>(container, 8);
  const auto *ids = Load<const std::uint32_t *>(container, 0);
  if (count < 0 || count > capacity || count > max_source_items || (count > 0 && ids == nullptr)) return false;
  for (std::int32_t i = 0; i < count; ++i) {
    auto *rite = Resolve(b.rite_storage_slot, ids[i], r::kReferenceIdentityOffset);
    if (rite == nullptr || Load<std::uint32_t>(rite, r::kRiteFaithIdOffset) != faith_id ||
        !ReferenceMatches(b.rite_faith(rite), faith_id, r::kReferenceIdentityOffset)) return false;
    out.push_back(ids[i]);
  }
  std::sort(out.begin(), out.end());
  return std::adjacent_find(out.begin(), out.end()) == out.end();
}

CharacterPredicate ReadMember(const Bindings &b, std::uint32_t id,
                             std::uint32_t faith_id,
                             const std::vector<std::uint32_t> &rite_ids,
                             void *incapable) noexcept {
  CharacterPredicate out;
  out.character_id = id;
  auto *character = Character(b, id);
  if (character == nullptr) { out.unavailable_reason = "full_generation_character_unavailable"; return out; }
  std::uint32_t rite_id = absent;
  if (!Leaf(b, id, character, [&] { rite_id = Load<std::uint32_t>(character, r::kCharacterRiteIdOffset); })) {
    out.unavailable_reason = "character_changed_during_membership_leaf"; return out;
  }
  auto *rite = Resolve(b.rite_storage_slot, rite_id, r::kReferenceIdentityOffset);
  if (rite == nullptr || !std::binary_search(rite_ids.begin(), rite_ids.end(), rite_id) ||
      Load<std::uint32_t>(rite, r::kRiteFaithIdOffset) != faith_id ||
      b.character_rite(character) != rite ||
      !ReferenceMatches(b.rite_faith(rite), faith_id, r::kReferenceIdentityOffset)) {
    out.unavailable_reason = "native_faith_membership_unavailable"; return out;
  }
  out.rite_id = rite_id;
  out.faith_id = faith_id;
  if (!Leaf(b, id, character, [&] { out.alive = Load<void *>(character, p::kCharacterDeathDataOffset) == nullptr; })) {
    out.unavailable_reason = "character_changed_during_alive_leaf"; return out;
  }
  if (out.alive != true) { out.unavailable_reason = "alive_collector_member_not_alive"; return out; }
  bool adult_valid = false;
  if (!Leaf(b, id, character, [&] {
        const auto selector = Load<std::uint8_t>(character, a::kAdultSelectorOffset);
        if (selector > 1) return;
        const auto measure = Load<std::int16_t>(character, a::kAdultMeasureOffset);
        const auto threshold = selector == 0 ? *b.adult_threshold_zero : *b.adult_threshold_one;
        out.adult_selector_raw = selector;
        out.adult_measure_raw = measure;
        out.adult_threshold_raw = threshold;
        out.adult = a::IsAdult(measure, threshold);
        adult_valid = true;
      }) || !adult_valid) { out.unavailable_reason = "native_adult_leaf_unavailable"; return out; }
  if (!Leaf(b, id, character, [&] { out.is_ai = !b.traits.is_human_player_character(static_cast<std::int32_t>(id)); })) {
    out.unavailable_reason = "character_changed_during_human_player_leaf"; return out;
  }
  if (!Leaf(b, id, character, [&] { out.effective_learning = b.effective_skill(character, 4); })) {
    out.unavailable_reason = "character_changed_during_learning_leaf"; return out;
  }
  bool trait_valid = false;
  if (incapable != nullptr && Leaf(b, id, character, [&] {
        const std::array<void *, 1> definitions{incapable};
        bool present = false;
        trait_valid = p::ReadTraitPresence(b.traits, character, definitions, present);
        if (trait_valid) out.incapable = present;
      }) && trait_valid) {
    // Concrete trait key lookup, rather than an assumed saved trait index.
  } else { out.unavailable_reason = "native_incapable_trait_leaf_unavailable"; return out; }
  if (b.is_imprisoned != nullptr) {
    if (!Leaf(b, id, character, [&] { out.imprisoned = b.is_imprisoned(character); })) {
      out.unavailable_reason = "character_changed_during_imprisoned_leaf"; return out;
    }
  } else { out.unavailable_reason = "native_imprisoned_binding_unknown"; return out; }
  if (Character(b, id) != character || Load<std::uint32_t>(character, r::kCharacterRiteIdOffset) != rite_id ||
      Resolve(b.rite_storage_slot, rite_id, r::kReferenceIdentityOffset) != rite ||
      Load<std::uint32_t>(rite, r::kRiteFaithIdOffset) != faith_id) {
    out.unavailable_reason = "native_membership_changed"; return out;
  }
  out.complete = true;
  return out;
}

bool Read(const Bindings &b, std::uint64_t epoch, Snapshot &out) {
  ck3_12002::CoreSnapshotPrefix frame;
  if (!ck3_12002::ReadCoreSnapshot(b.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive) { out.unavailable_reason = "paused_frame_unavailable"; return false; }
  if (!frame.clock.paused) { out.unavailable_reason = "frame_not_paused"; return false; }
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = frame.played_character_id;
  auto *actor = Character(b, static_cast<std::uint32_t>(frame.played_character_id));
  if (actor == nullptr) { out.unavailable_reason = "actor_unavailable"; return false; }
  const auto rite_id = Load<std::uint32_t>(actor, r::kCharacterRiteIdOffset);
  auto *rite = Resolve(b.rite_storage_slot, rite_id, r::kReferenceIdentityOffset);
  if (rite == nullptr || b.character_rite(actor) != rite) { out.unavailable_reason = "actor_rite_unavailable"; return false; }
  const auto faith_id = Load<std::uint32_t>(rite, r::kRiteFaithIdOffset);
  auto *faith = b.rite_faith(rite);
  if (!ReferenceMatches(faith, faith_id, r::kReferenceIdentityOffset)) { out.unavailable_reason = "actor_faith_unavailable"; return false; }
  auto *religion = b.faith_religion(faith);
  const auto religion_id = Load<std::uint32_t>(faith, r::kFaithReligionIdOffset);
  if (!ReferenceMatches(religion, religion_id, r::kReferenceIdentityOffset)) { out.unavailable_reason = "religion_unavailable"; return false; }
  out.faith_id = faith_id;
  out.played_rite_id = rite_id;
  out.religion_id = religion_id;
  if (!FaithRites(b, faith, faith_id, out.complete_native_faith_rite_ids) ||
      !std::binary_search(out.complete_native_faith_rite_ids.begin(), out.complete_native_faith_rite_ids.end(), rite_id)) {
    out.unavailable_reason = "full_native_faith_rite_list_unavailable"; return false;
  }
  auto *state = *b.core.game_state_slot;
  auto *data = state == nullptr ? nullptr : Load<void *>(state, 0xA0);
  if (data == nullptr) { out.unavailable_reason = "alive_source_pool_unavailable"; return false; }
  const auto alive_count = Load<std::int32_t>(data, c::kAlivePoolSizeOffset);
  const auto county_count = Load<std::int32_t>(religion, c::kReligionCountyPoolSizeOffset);
  const auto *alive_pool = Load<const void *>(data, c::kAlivePoolOffset);
  const auto *county_pool = Load<const void *>(religion, c::kReligionCountyPoolOffset);
  if (alive_count < 0 || alive_count > max_source_items || county_count < 0 || county_count > max_source_items ||
      (alive_count > 0 && alive_pool == nullptr) || (county_count > 0 && county_pool == nullptr)) {
    out.unavailable_reason = "source_pool_extent_unavailable"; return false;
  }
  out.alive_source_pool_count = alive_count;
  out.religion_county_source_pool_count = county_count;
  std::vector<c::ScopeValue> native_members;
  if (!Collect(b.faith_characters, c::kFaithScope, faith_id, alive_count, native_members)) {
    out.unavailable_reason = "full_native_faith_collector_unavailable"; return false;
  }
  for (const auto &row : native_members) {
    if (row.kind != c::kCharacterScope || row.flags != 0 || row.identity > UINT32_MAX) {
      out.unavailable_reason = "native_faith_collector_row_unavailable"; return false;
    }
    out.complete_native_faith_member_ids.push_back(static_cast<std::uint32_t>(row.identity));
  }
  std::sort(out.complete_native_faith_member_ids.begin(), out.complete_native_faith_member_ids.end());
  if (std::adjacent_find(out.complete_native_faith_member_ids.begin(), out.complete_native_faith_member_ids.end()) != out.complete_native_faith_member_ids.end()) {
    out.unavailable_reason = "native_faith_collector_duplicate_identity"; return false;
  }
  if (!std::binary_search(out.complete_native_faith_member_ids.begin(),
                          out.complete_native_faith_member_ids.end(),
                          static_cast<std::uint32_t>(frame.played_character_id))) {
    out.unavailable_reason = "alive_played_actor_missing_from_native_faith_collector"; return false;
  }
  auto *database = b.traits.get_trait_database();
  auto *incapable = p::FindUniqueTraitDefinition(database, "incapable");
  for (const auto id : out.complete_native_faith_member_ids) {
    out.members.push_back(ReadMember(b, id, faith_id, out.complete_native_faith_rite_ids, incapable));
  }
  for (const auto id : out.complete_native_faith_rite_ids) {
    RiteCounties counties;
    counties.rite_id = id;
    auto *candidate = Resolve(b.rite_storage_slot, id, r::kReferenceIdentityOffset);
    std::vector<c::ScopeValue> rows;
    if (candidate == nullptr || Load<std::uint32_t>(candidate, r::kRiteFaithIdOffset) != faith_id ||
        !Collect(b.rite_counties, c::kRiteScope, id, county_count, rows)) {
      counties.unavailable_reason = "complete_native_rite_counties_unavailable";
    } else {
      counties.complete = true;
      for (const auto &row : rows) {
        if (row.kind != c::kTitleScope || row.flags != 0 || row.identity > UINT32_MAX) { counties.complete = false; break; }
        const auto title_id = static_cast<std::uint32_t>(row.identity);
        auto *title = Resolve(b.title_storage_slot, title_id, c::kTitleIdentityOffset);
        auto *definition = title == nullptr ? nullptr : Load<void *>(title, c::kTitleTemplateOffset);
        if (title == nullptr || Load<std::uint32_t>(title, 0x14) != 0x4C616E64U ||
            definition == nullptr || Load<std::int32_t>(definition, c::kTitleTemplateRankOffset) != 2 ||
            Resolve(b.title_storage_slot, title_id, c::kTitleIdentityOffset) != title) { counties.complete = false; break; }
        counties.county_title_ids.push_back(title_id);
      }
      std::sort(counties.county_title_ids.begin(), counties.county_title_ids.end());
      if (std::adjacent_find(counties.county_title_ids.begin(), counties.county_title_ids.end()) != counties.county_title_ids.end()) counties.complete = false;
      if (!counties.complete) counties.unavailable_reason = "native_county_title_identity_unavailable";
    }
    out.rites.push_back(std::move(counties));
  }
  // A second complete native enumeration proves closure; every predicate is
  // independently read again with full-generation identity checks.
  std::vector<c::ScopeValue> native_after;
  std::vector<std::uint32_t> ids_after;
  std::vector<std::uint32_t> rites_after;
  bool stable = FaithRites(b, faith, faith_id, rites_after) &&
      rites_after == out.complete_native_faith_rite_ids &&
      Collect(b.faith_characters, c::kFaithScope, faith_id, alive_count, native_after);
  for (const auto &row : native_after) {
    if (row.kind != c::kCharacterScope || row.flags != 0 || row.identity > UINT32_MAX) stable = false;
    else ids_after.push_back(static_cast<std::uint32_t>(row.identity));
  }
  std::sort(ids_after.begin(), ids_after.end());
  stable = stable && ids_after == out.complete_native_faith_member_ids;
  for (const auto &member : out.members) {
    stable = stable && ReadMember(b, member.character_id, faith_id, rites_after, incapable) == member;
  }
  for (const auto &counties : out.rites) {
    if (!counties.complete) continue;
    std::vector<c::ScopeValue> rows;
    std::vector<std::uint32_t> ids;
    stable = stable && Collect(b.rite_counties, c::kRiteScope, counties.rite_id, county_count, rows);
    for (const auto &row : rows) {
      if (row.kind != c::kTitleScope || row.flags != 0 || row.identity > UINT32_MAX) stable = false;
      else {
       const auto title_id = static_cast<std::uint32_t>(row.identity);
       auto *title = Resolve(b.title_storage_slot, title_id, c::kTitleIdentityOffset);
       auto *definition = title == nullptr ? nullptr : Load<void *>(title, c::kTitleTemplateOffset);
       if (title == nullptr || Load<std::uint32_t>(title, 0x14) != 0x4C616E64U ||
           definition == nullptr || Load<std::int32_t>(definition, c::kTitleTemplateRankOffset) != 2 ||
           Resolve(b.title_storage_slot, title_id, c::kTitleIdentityOffset) != title) stable = false;
       ids.push_back(title_id);
      }
    }
    std::sort(ids.begin(), ids.end());
    stable = stable && ids == counties.county_title_ids;
  }
  ck3_12002::CoreSnapshotPrefix after;
  stable = stable && ck3_12002::ReadCoreSnapshot(b.core, after) && after.clock.paused &&
      after.map_ready && after.has_played_character && after.played_character_alive &&
      after.clock.date_raw == frame.clock.date_raw && after.played_character_id == frame.played_character_id &&
      Character(b, static_cast<std::uint32_t>(frame.played_character_id)) == actor &&
      Load<std::uint32_t>(actor, r::kCharacterRiteIdOffset) == rite_id &&
      Resolve(b.rite_storage_slot, rite_id, r::kReferenceIdentityOffset) == rite &&
      Load<std::uint32_t>(rite, r::kRiteFaithIdOffset) == faith_id &&
      b.rite_faith(rite) == faith && ReferenceMatches(faith, faith_id, r::kReferenceIdentityOffset) &&
      Load<std::uint32_t>(faith, r::kFaithReligionIdOffset) == religion_id &&
      b.faith_religion(faith) == religion && ReferenceMatches(religion, religion_id, r::kReferenceIdentityOffset) &&
      *b.core.game_state_slot == state && Load<void *>(state, 0xA0) == data &&
      Load<std::int32_t>(data, c::kAlivePoolSizeOffset) == alive_count &&
      Load<const void *>(data, c::kAlivePoolOffset) == alive_pool &&
      Load<std::int32_t>(religion, c::kReligionCountyPoolSizeOffset) == county_count &&
      Load<const void *>(religion, c::kReligionCountyPoolOffset) == county_pool;
  if (!stable) { out.unavailable_reason = "native_frame_or_membership_changed"; return false; }
  out.available = true;
  out.predicates_complete = std::all_of(out.members.begin(), out.members.end(), [](const auto &row) { return row.complete; }) &&
      std::all_of(out.rites.begin(), out.rites.end(), [](const auto &row) { return row.complete; });
  out.unavailable_reason = out.predicates_complete ? "" : "one_or_more_native_predicates_unknown";
  return true;
}

// The application owning-thread caller never treats an inaccessible native
// pointer as a false predicate or an empty enumeration. This boundary has no
// native-owned object mutation and contains no local C++ objects needing SEH
// unwinding. Normal C++ allocation exceptions continue to the outer catch.
bool GuardedRead(const Bindings &b, std::uint64_t epoch, Snapshot &out,
                 bool &native_access_fault) {
  native_access_fault = false;
#if defined(_MSC_VER)
  __try {
#endif
    return Read(b, epoch, out);
#if defined(_MSC_VER)
  } __except (GetExceptionCode() == EXCEPTION_ACCESS_VIOLATION ||
              GetExceptionCode() == EXCEPTION_IN_PAGE_ERROR ||
              GetExceptionCode() == EXCEPTION_DATATYPE_MISALIGNMENT
                  ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH) {
    native_access_fault = true;
    return false;
  }
#endif
}

std::string Quote(std::string_view text) {
  std::string out = "\"";
  for (const auto ch : text) { if (ch == '\\' || ch == '"') out += '\\'; out += ch; }
  return out + '"';
}
template <typename T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
std::string Bool(const std::optional<bool> &value) { return value ? (*value ? "true" : "false") : "null"; }
std::string Ids(const std::vector<std::uint32_t> &ids) {
  std::string out = "[";
  for (const auto id : ids) { if (out.size() > 1) out += ','; out += std::to_string(id); }
  return out + ']';
}
} // namespace

Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b;
  if (base == 0 || sha != ck3_12003::kExecutableSha256) return b;
  b.enabled = true;
  b.core = {true, reinterpret_cast<void **>(base + ck3_12003::kGameStateSlotRva),
      reinterpret_cast<void **>(base + ck3_12003::kJominiStateSlotRva),
      reinterpret_cast<void **>(base + ck3_12003::kCharacterStorageSlotRva),
      reinterpret_cast<ck3_12002::GetLocalPlayer>(base + ck3_12003::kGetLocalPlayerRva)};
  b.traits.enabled = true;
  b.traits.get_trait_database = reinterpret_cast<p::GetTraitDatabase>(base + p::kTraitDatabaseRva);
  b.traits.character_has_trait = reinterpret_cast<p::CharacterHasTrait>(base + p::kCharacterHasTraitRva);
  b.traits.is_human_player_character = reinterpret_cast<p::IsHumanPlayerCharacter>(base + p::kIsHumanPlayerCharacterRva);
  b.rite_storage_slot = reinterpret_cast<void **>(base + 0x5D1E2F8);
  b.title_storage_slot = reinterpret_cast<void **>(base + c::kTitleStorageSlotRva);
  b.character_rite = reinterpret_cast<ObjectGetter>(base + r::kCharacterRiteRva);
  b.rite_faith = reinterpret_cast<ObjectGetter>(base + r::kRiteFaithRva);
  b.faith_religion = reinterpret_cast<ObjectGetter>(base + r::kFaithReligionRva);
  b.faith_rites = reinterpret_cast<ContainerGetter>(base + 0xB801B0);
  b.faith_characters = reinterpret_cast<Collector>(base + c::kFaithCharacterCollectorRva);
  b.rite_counties = reinterpret_cast<Collector>(base + c::kRiteCountyCollectorRva);
  b.effective_skill = reinterpret_cast<EffectiveSkillGetter>(base + 0x28B16B0);
  b.adult_threshold_zero = reinterpret_cast<const std::int32_t *>(base + a::kAdultThresholdZeroSlotRva);
  b.adult_threshold_one = reinterpret_cast<const std::int32_t *>(base + a::kAdultThresholdOneSlotRva);
  // CCharacter::IsImprisoned, independently named by the current GUI callback
  // and matched to the actual CIsImprisonedTrigger evaluator. It tests the
  // extension/custody pointers and deliberately does not resolve jailer ID.
  b.is_imprisoned = reinterpret_cast<BoolGetter>(base + 0x28C20A0);
  return b;
}

bool ReadCurrentFaithPredicates(const Bindings &b, std::uint64_t epoch,
                               Snapshot &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  if (!b.enabled || !b.core.enabled || !b.traits.enabled ||
      !b.core.game_state_slot || !b.core.jomini_state_slot || !b.core.character_storage_slot || !b.core.get_local_player ||
      !b.rite_storage_slot || !b.title_storage_slot || !b.character_rite || !b.rite_faith || !b.faith_religion ||
      !b.faith_rites || !b.faith_characters || !b.rite_counties || !b.effective_skill ||
      !b.adult_threshold_zero || !b.adult_threshold_one || !b.traits.get_trait_database ||
      !b.traits.character_has_trait || !b.traits.is_human_player_character) return false;
  try {
    Snapshot current;
    current.capture_epoch = epoch;
    bool access_fault = false;
    const bool ok = GuardedRead(b, epoch, current, access_fault);
    if (!ok) {
      out.unavailable_reason = access_fault ? "native_memory_read_unavailable" : current.unavailable_reason;
      out.date_raw = current.date_raw;
      out.played_character_id = current.played_character_id;
      return false;
    }
    out = std::move(current);
    return true;
  } catch (...) { out = {}; out.capture_epoch = epoch; out.unavailable_reason = "native_read_exception"; return false; }
}

std::string Serialize(const Snapshot &s) {
  std::string out = "{\"schema\":\"ck3_12003_confucian_assembly_predicates_v1\",\"read_only\":true,\"game_version\":\"1.20.0.3\",\"executable_sha256\":" + Quote(ck3_12003::kExecutableSha256) +
      ",\"available\":" + (s.available ? "true" : "false") + ",\"predicates_complete\":" + (s.predicates_complete ? "true" : "false") +
      ",\"unavailable_reason\":" + (s.unavailable_reason.empty() ? "null" : Quote(s.unavailable_reason)) +
      ",\"capture_epoch\":" + std::to_string(s.capture_epoch) + ",\"date_raw\":" + std::to_string(s.date_raw) +
      ",\"played_character_id\":" + std::to_string(s.played_character_id) + ",\"faith_id\":" + Number(s.faith_id) +
      ",\"played_rite_id\":" + Number(s.played_rite_id) + ",\"religion_id\":" + Number(s.religion_id) +
      ",\"alive_source_pool_count\":" + Number(s.alive_source_pool_count) +
      ",\"religion_county_source_pool_count\":" + Number(s.religion_county_source_pool_count) +
      ",\"complete_native_faith_member_ids\":" + (s.available ? Ids(s.complete_native_faith_member_ids) : "null") +
      ",\"complete_native_faith_rite_ids\":" + (s.available ? Ids(s.complete_native_faith_rite_ids) : "null") + ",\"members\":";
  if (!s.available) out += "null";
  else {
    out += '[';
    for (const auto &row : s.members) {
      if (out.back() != '[') out += ',';
      out += "{\"character_id\":" + std::to_string(row.character_id) + ",\"rite_id\":" + Number(row.rite_id) +
          ",\"faith_id\":" + Number(row.faith_id) + ",\"alive\":" + Bool(row.alive) + ",\"adult\":" + Bool(row.adult) +
          ",\"imprisoned\":" + Bool(row.imprisoned) + ",\"incapable\":" + Bool(row.incapable) +
          ",\"is_ai\":" + Bool(row.is_ai) + ",\"effective_learning\":" + Number(row.effective_learning) +
          ",\"adult_measure_raw\":" + Number(row.adult_measure_raw) + ",\"adult_selector_raw\":" + Number(row.adult_selector_raw) +
          ",\"adult_threshold_raw\":" + Number(row.adult_threshold_raw) + ",\"complete\":" + (row.complete ? "true" : "false") +
          ",\"unavailable_reason\":" + (row.unavailable_reason.empty() ? "null" : Quote(row.unavailable_reason)) + '}';
    }
    out += ']';
  }
  out += ",\"rites\":";
  if (!s.available) out += "null";
  else {
    out += '[';
    for (const auto &row : s.rites) {
      if (out.back() != '[') out += ',';
      out += "{\"rite_id\":" + std::to_string(row.rite_id) + ",\"county_title_ids\":" +
          (row.complete ? Ids(row.county_title_ids) : "null") + ",\"native_county_count\":" +
          (row.complete ? std::to_string(row.county_title_ids.size()) : "null") + ",\"complete\":" + (row.complete ? "true" : "false") +
          ",\"unavailable_reason\":" + (row.unavailable_reason.empty() ? "null" : Quote(row.unavailable_reason)) + '}';
    }
    out += ']';
  }
  return out + '}';
}

} // namespace xar::ck3_12003::confucian_assembly
