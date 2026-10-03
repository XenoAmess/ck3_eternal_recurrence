#include "xar_bridge/ck3_12003_county_conversion.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <sstream>
#include <utility>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::ck3_12003::religion::county_conversion {
namespace {
using Seat = ck3_12002::religion::clergy::CurrentClergySeat;
using Frame = ck3_12002::CoreSnapshotPrefix;

struct TaskScopes {
  std::int32_t incumbent = -1;
  std::int32_t owner = -1;
  std::uint16_t target_tag = 0;
  std::array<std::byte, 6> reserved{};
  std::int32_t target = 0;
  std::array<std::byte, 12> trailing{};
};
static_assert(sizeof(TaskScopes) == 0x20);
static_assert(offsetof(TaskScopes, target) == 0x10);

// Read-only input layout used by the exact native command validator. It does
// not inspect the prefix/vptr, invoke a virtual method or submit this packet.
struct ChangeTaskValidationPacket {
  std::array<std::byte, 0x20> unused_prefix{};
  std::int32_t active_task_id = -1;
  std::uint32_t padding = 0;
  const void *task_type = nullptr;
  TaskScopes scopes{};
};
static_assert(sizeof(ChangeTaskValidationPacket) == 0x50);
static_assert(offsetof(ChangeTaskValidationPacket, active_task_id) == 0x20);
static_assert(offsetof(ChangeTaskValidationPacket, task_type) == 0x28);
static_assert(offsetof(ChangeTaskValidationPacket, scopes) == 0x30);

bool Bytes(const Environment &e, const void *address, void *out,
           std::size_t size) noexcept {
  if (!address || !out) return false;
  if (e.clergy.read_memory)
    return e.clergy.read_memory(e.clergy.read_context, address, out, size);
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(out, address, size);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
  return true;
}

template <typename T>
bool At(const Environment &e, const void *object, std::size_t offset,
        T &out) noexcept {
  return object && Bytes(e, static_cast<const std::byte *>(object) + offset,
                        &out, sizeof(out));
}

template <typename Function, typename Return, typename... Args>
bool Invoke(Function function, Return &out, Args... args) noexcept {
  if (!function) return false;
#if defined(_MSC_VER)
  __try { out = function(args...); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  out = function(args...);
#endif
  return true;
}

bool Snapshot(const Environment &e, Frame &out) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return ck3_12002::ReadCoreSnapshot(e.clergy.core, out);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

void *Character(const Environment &e, std::int32_t id) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return ck3_12002::ResolveCoreCharacter(e.clergy.core, id);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
#endif
}

bool Exact(const Environment &e) noexcept {
  if (!e.exact_build_admitted || e.executable_sha256 != ck3_12003::kExecutableSha256 ||
      !e.clergy.enabled || !e.clergy.core.enabled ||
      !e.allocator.exact_build_admitted || !e.game_state_slot ||
      !e.title_storage_slot || !e.title_fallback_slot ||
      !e.task_type_database_slot || !e.task_type_fallback_slot ||
      !e.hash_key || !e.lookup_type || !e.shown || !e.valid || !e.target_valid ||
      !e.produce_targets || !e.monthly_rate || !e.county_rite ||
      !e.allocator.initialize_vector || !e.allocator.release_allocation) return false;
  if (e.offline_fixture)
    return e.module_base == 0 && e.clergy.offline_fixture &&
        e.allocator.offline_fixture_function_overrides;
  const auto base = e.module_base;
  return base != 0 && !e.clergy.offline_fixture &&
      !e.allocator.offline_fixture_function_overrides &&
      e.clergy.module_base == base && e.allocator.module_base == base &&
      reinterpret_cast<std::uintptr_t>(e.game_state_slot) == base + 0x5C68C50 &&
      reinterpret_cast<std::uintptr_t>(e.title_storage_slot) == base + 0x5D1DAF8 &&
      reinterpret_cast<std::uintptr_t>(e.title_fallback_slot) == base + 0x5D1DAE0 &&
      reinterpret_cast<std::uintptr_t>(e.task_type_database_slot) == base + 0x5C671D8 &&
      reinterpret_cast<std::uintptr_t>(e.task_type_fallback_slot) == base + 0x5D1F900 &&
      reinterpret_cast<std::uintptr_t>(e.hash_key) == base + 0x3F7E240 &&
      reinterpret_cast<std::uintptr_t>(e.lookup_type) == base + 0xCF1E80 &&
      reinterpret_cast<std::uintptr_t>(e.shown) == base + 0x31AC7B0 &&
      reinterpret_cast<std::uintptr_t>(e.valid) == base + 0x31AC680 &&
      reinterpret_cast<std::uintptr_t>(e.target_valid) == base + 0x2C48970 &&
      reinterpret_cast<std::uintptr_t>(e.produce_targets) == base + 0x2C48E80 &&
      reinterpret_cast<std::uintptr_t>(e.monthly_rate) == base + kMonthlyRateRva &&
      reinterpret_cast<std::uintptr_t>(e.county_rite) == base + kCountyRiteRva &&
      (!e.value_inputs_enabled || (
      reinterpret_cast<std::uintptr_t>(e.character_rite) == base + 0x28D2F90 &&
      reinterpret_cast<std::uintptr_t>(e.rite_faith) == base + 0x24FC560 &&
      reinterpret_cast<std::uintptr_t>(e.government) == base + 0x28C2E10 &&
      reinterpret_cast<std::uintptr_t>(e.title_by_key) == base + 0xA847A0 &&
      reinterpret_cast<std::uintptr_t>(e.identifier_name) == base + 0x3F4F900 &&
      reinterpret_cast<std::uintptr_t>(e.county_opinion) == base + 0x24D4CB0 &&
      reinterpret_cast<std::uintptr_t>(e.government_fallback_slot) == base + 0x5D1E2A8));
}

bool Key(const Environment &e, const void *object, std::string &out) {
  if (!object) return false;
  const auto *key = static_cast<const std::byte *>(object) + 0x18;
  std::uint64_t size = 0, capacity = 0;
  if (!At(e, key, 0x10, size) || !At(e, key, 0x18, capacity) ||
      size == 0 || size > 1024 || size > capacity) return false;
  const void *text = key;
  if (capacity > 15 && (!At(e, key, 0, text) || !text)) return false;
  out.resize(static_cast<std::size_t>(size));
  return Bytes(e, text, out.data(), out.size()) &&
      std::none_of(out.begin(), out.end(), [](unsigned char ch) {
        return ch == 0 || ch < 0x20U;
      });
}

bool NativeString(const Environment &e, const void *key, std::string &out) {
  if (!key) return false;
  std::uint64_t size = 0, capacity = 0;
  if (!At(e, key, 0x10, size) || !At(e, key, 0x18, capacity) ||
      size == 0 || size > 1024 || size > capacity) return false;
  const void *text = key;
  if (capacity > 15 && (!At(e, key, 0, text) || !text)) return false;
  out.resize(static_cast<std::size_t>(size));
  return Bytes(e, text, out.data(), out.size());
}

bool Province(const Environment &e, const void *province, std::int32_t &id) noexcept {
  void *state = nullptr, *map = nullptr, *array = nullptr, *indexed = nullptr;
  std::int32_t count = 0;
  std::uint32_t tag = 0;
  return province && At(e, province, 0x10, id) && id > 0 &&
      At(e, province, 0x85C, tag) && tag == 0x50726F76U &&
      At(e, e.game_state_slot, 0, state) && At(e, state, 0xA0, map) &&
      At(e, map, 0x140, array) && array && At(e, map, 0x14C, count) &&
      count > 0 && count <= 65'536 && id < count &&
      At(e, array, static_cast<std::size_t>(id) * sizeof(void *), indexed) &&
      indexed == province;
}

bool ProvinceById(const Environment &e, std::int32_t id, const void *&out) noexcept {
  out = nullptr;
  void *state = nullptr, *map = nullptr, *array = nullptr, *province = nullptr;
  std::int32_t count = 0, observed = -1;
  if (id <= 0 || !At(e, e.game_state_slot, 0, state) || !At(e, state, 0xA0, map) ||
      !At(e, map, 0x140, array) || !array || !At(e, map, 0x14C, count) ||
      count <= 0 || count > 65'536 || id >= count ||
      !At(e, array, static_cast<std::size_t>(id) * sizeof(void *), province) ||
      !Province(e, province, observed) || observed != id) return false;
  out = province;
  return true;
}

bool Title(const Environment &e, std::int32_t id, const void *&out) noexcept {
  out = nullptr;
  void *storage = nullptr, *fallback = nullptr, *entries = nullptr, *title = nullptr;
  std::int32_t capacity = 0, observed = -1;
  if (id <= 0 || !At(e, e.title_storage_slot, 0, storage) || !storage ||
      !At(e, e.title_fallback_slot, 0, fallback) ||
      !At(e, storage, 0x20, entries) || !entries ||
      !At(e, storage, 0x2C, capacity) || capacity <= 0 || capacity > 4'194'304)
    return false;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity) ||
      !At(e, entries, static_cast<std::size_t>(index) * 0x10 + 8, title) ||
      !title || title == fallback || !At(e, title, 0x10, observed) || observed != id)
    return false;
  out = title;
  return true;
}

bool CountyIdentity(const Environment &e, const void *province, const void *&county,
                    Candidate &row) noexcept {
  const void *title = nullptr;
  county = nullptr;
  return Province(e, province, row.province_id) && At(e, province, 0x848, county) &&
      county && At(e, county, 0x18, row.county_title_id) &&
      Title(e, row.county_title_id, title) &&
      At(e, title, 0x128, row.holder_character_id) &&
      Character(e, row.holder_character_id) != nullptr;
}

bool CountyRite(const Environment &e, const void *county,
                std::optional<std::uint32_t> &out) noexcept {
  out.reset();
  std::uint32_t id = 0xFFFFFFFFU, observed = 0xFFFFFFFFU, last = 0xFFFFFFFFU;
  if (!At(e, county, 0x384, id)) return false;
  if (id == 0xFFFFFFFFU) return true;
  const void *rite = nullptr;
  if (!Invoke(e.county_rite, rite, county) || !rite ||
      !At(e, rite, 8, observed) || observed != id ||
      !At(e, county, 0x384, last) || last != id) return false;
  out = id;
  return true;
}

bool CharacterRite(const Environment &e, const void *character,
                   std::optional<std::uint32_t> &out) noexcept {
  out.reset();
  std::uint32_t id = 0xFFFFFFFFU;
  if (!At(e, character, 0xB4, id)) return false;
  if (id != 0xFFFFFFFFU) out = id;
  return true;
}

bool RiteFaith(const Environment &e, const void *rite, std::uint32_t rite_id,
               std::uint32_t &faith_id) noexcept {
  const void *faith = nullptr;
  std::uint32_t observed_rite = 0, observed_faith = 0;
  return rite && At(e, rite, 8, observed_rite) && observed_rite == rite_id &&
      At(e, rite, 0x4B8, faith_id) && faith_id != 0xFFFFFFFFU &&
      Invoke(e.rite_faith, faith, rite) && faith &&
      At(e, faith, 8, observed_faith) && observed_faith == faith_id;
}

bool CharacterFaith(const Environment &e, const void *character,
                    std::optional<std::uint32_t> rite_id,
                    std::uint32_t &faith_id) noexcept {
  const void *rite = nullptr;
  return rite_id && Invoke(e.character_rite, rite, character) &&
      RiteFaith(e, rite, *rite_id, faith_id);
}

bool MinistryAccess(const Environment &e, const void *owner,
                    std::int32_t owner_id, bool &out) {
  out = false;
  const void *government = nullptr, *fallback = nullptr, *flags = nullptr;
  std::int32_t count = 0;
  if (!At(e, e.government_fallback_slot, 0, fallback) ||
      !Invoke(e.government, government, owner)) return false;
  if (!government || government == fallback) return true;
  if (!At(e, government, 0x50, flags) || !At(e, government, 0x5C, count) ||
      count < 0 || count > 4096 || (count > 0 && !flags)) return false;
  bool celestial = false, budget = false;
  for (std::int32_t i = 0; i < count; ++i) {
    std::int32_t identifier = 0;
    const std::string *native = nullptr;
    std::string key;
    if (!At(e, flags, static_cast<std::size_t>(i) * sizeof(identifier), identifier) ||
        !Invoke(e.identifier_name, native, identifier) || !NativeString(e, native, key))
      return false;
    celestial = celestial || key == "government_is_celestial";
    budget = budget || key == "government_uses_ministry_budget";
  }
  if (!celestial || !budget) return true;
  // Mirror only the seven-byte fixed stock key. Engine resolver retains all
  // lookup ownership; this stack string transfers no allocation or title.
  struct NativeSmallString {
    std::array<char, 16> bytes{'h','_','c','h','i','n','a','\0'};
    std::uint64_t size = 7;
    std::uint64_t capacity = 15;
  } key;
  static_assert(sizeof(NativeSmallString) == 32);
  const void *title = nullptr, *title_fallback = nullptr, *resolved = nullptr;
  std::int32_t full_id = -1, holder = -1;
  if (!At(e, e.title_fallback_slot, 0, title_fallback) ||
      !Invoke(e.title_by_key, title, static_cast<const void *>(&key))) return false;
  if (!title || title == title_fallback) return true;
  if (!At(e, title, 0x10, full_id) || !Title(e, full_id, resolved) || resolved != title ||
      !At(e, title, 0x128, holder)) return false;
  out = holder == owner_id;
  return true;
}

bool CountyValues(const Environment &e, const Candidate &identity,
                  std::uint32_t owner_faith, std::uint32_t incumbent_faith,
                  std::uint32_t owner_rite, std::uint32_t incumbent_rite,
                  bool ministry, CountyValueInputs &out) noexcept {
  const void *province = nullptr, *county = nullptr, *rite = nullptr;
  Candidate checked{};
  if (!identity.county_rite_id || !ProvinceById(e, identity.province_id, province) ||
      !CountyIdentity(e, province, county, checked) ||
      checked.county_title_id != identity.county_title_id ||
      checked.holder_character_id != identity.holder_character_id ||
      !Invoke(e.county_rite, rite, county) ||
      !RiteFaith(e, rite, *identity.county_rite_id, out.county_faith_id) ||
      !Invoke(e.county_opinion, out.current_popular_opinion, county)) return false;
  out.province_id = identity.province_id;
  out.county_title_id = identity.county_title_id;
  out.holder_character_id = identity.holder_character_id;
  const bool use_owner = ministry || out.county_faith_id == owner_faith ||
      incumbent_faith == owner_faith;
  out.destination_rite_id = use_owner ? owner_rite : incumbent_rite;
  out.destination_faith_id = use_owner ? owner_faith : incumbent_faith;
  out.faith_changes = out.county_faith_id != out.destination_faith_id;
  out.rite_changes = *identity.county_rite_id != out.destination_rite_id;
  return true;
}

struct CurrentState {
  Seat seat{};
  std::optional<std::uint32_t> owner_rite;
  std::optional<std::uint32_t> incumbent_rite;
  std::string key;
  std::optional<std::int32_t> kind;
  std::optional<std::int32_t> progress_kind;
  std::optional<bool> frozen;
  std::optional<std::int64_t> percentage;
  std::optional<std::int32_t> province;
  std::optional<std::int32_t> county_title;
  std::optional<std::uint32_t> county_rite;
  bool operator==(const CurrentState &) const = default;
};

Failure ReadCurrent(const Environment &e, std::int32_t owner_id,
                    CurrentState &out) {
  out = {};
  if (!ck3_12002::religion::clergy::ResolveCurrentClergySeat12002(e.clergy, owner_id,
          out.seat) || !CharacterRite(e, out.seat.owner, out.owner_rite))
    return Failure::clergy_seat_unavailable;
  if (!out.seat.task) return Failure::none;
  std::int32_t kind = -1, progress_kind = -1;
  std::uint8_t frozen = 0;
  if (!Key(e, out.seat.type, out.key) || !At(e, out.seat.type, 0x48, kind) ||
      kind < 0 || kind > 2 || !At(e, out.seat.type, 0x54, progress_kind) ||
      progress_kind < 0 || progress_kind > 2 ||
      !At(e, out.seat.task, 0x39, frozen) || frozen > 1)
    return Failure::current_task_unavailable;
  out.kind = kind; out.progress_kind = progress_kind; out.frozen = frozen != 0;
  if (out.seat.incumbent &&
      !CharacterRite(e, out.seat.incumbent, out.incumbent_rite))
    return Failure::clergy_seat_unavailable;
  if (progress_kind == 1) {
    std::int64_t progress = 0;
    if (!At(e, out.seat.task, 0x20, progress) || progress < 0 || progress > 10'000'000)
      return Failure::current_task_unavailable;
    out.percentage = progress;
  }
  if (kind == 1) {
    std::uint16_t tag = 0;
    std::int32_t id = -1;
    const void *province = nullptr, *county = nullptr;
    Candidate identity{};
    if (!At(e, out.seat.task, 0x48, tag) || tag != 8 ||
        !At(e, out.seat.task, 0x50, id) || !ProvinceById(e, id, province) ||
        !CountyIdentity(e, province, county, identity))
      return Failure::county_identity_unavailable;
    if (!CountyRite(e, county, out.county_rite)) return Failure::county_rite_unavailable;
    out.province = id; out.county_title = identity.county_title_id;
  }
  return Failure::none;
}

void PublishCurrent(const CurrentState &c, Observation &out) {
  out.owner_rite_id = c.owner_rite;
  out.position_present = c.seat.task != nullptr;
  if (c.seat.task) out.active_task_id = c.seat.task_id;
  if (c.seat.incumbent) out.incumbent_character_id = c.seat.incumbent_character_id;
  out.incumbent_rite_id = c.incumbent_rite;
  out.current_task_key = c.key; out.current_task_type = c.kind;
  out.current_progress_kind = c.progress_kind; out.current_task_frozen = c.frozen;
  out.current_percentage_progress_raw = c.percentage;
  out.current_target_province_id = c.province;
  out.current_target_county_title_id = c.county_title;
  out.current_target_county_rite_id = c.county_rite;
}

bool TaskType(const Environment &e, const Seat &seat, const void *&type) {
  void *database = nullptr, *fallback = nullptr;
  const void *position = nullptr;
  std::int32_t hash = 0, kind = -1, progress_kind = -1;
  std::string key;
  return At(e, e.task_type_database_slot, 0, database) && database &&
      At(e, e.task_type_fallback_slot, 0, fallback) &&
      Invoke(e.hash_key, hash, nullptr, kTaskKey.data(),
          static_cast<std::uint32_t>(kTaskKey.size())) &&
      Invoke(e.lookup_type, type, static_cast<const void *>(database), hash) &&
      type && type != fallback && Key(e, type, key) && key == kTaskKey &&
      At(e, type, 0x40, position) && position == seat.position &&
      At(e, type, 0x48, kind) && kind == 1 &&
      At(e, type, 0x54, progress_kind) && progress_kind == 1;
}

bool Initialize(const Environment &e, void *allocator, NativeVector &vector) noexcept {
  std::memset(allocator, 0, ck3_12002::kCouncilCandidatesAllocatorSize12002);
  std::memcpy(allocator, &e.allocator.allocator_vtable, sizeof(std::uintptr_t));
  std::memcpy(static_cast<std::byte *>(allocator) +
      ck3_12002::kCouncilCandidatesAllocatorFallbackOffset12002,
      &e.allocator.fallback_allocator, sizeof(std::uintptr_t));
  vector = {}; vector.allocator = allocator;
#if defined(_MSC_VER)
  __try { e.allocator.initialize_vector(allocator, &vector.data_address, &vector.capacity); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  e.allocator.initialize_vector(allocator, &vector.data_address, &vector.capacity);
#endif
  return vector.data_address == reinterpret_cast<std::uintptr_t>(allocator) + 8 &&
      vector.capacity == 64 && vector.count == 0;
}

bool Produce(const Environment &e, const void *incumbent, const void *type,
             NativeVector &vector) noexcept {
#if defined(_MSC_VER)
  __try { e.produce_targets(incumbent, type, false, &vector, false); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  e.produce_targets(incumbent, type, false, &vector, false);
#endif
  return true;
}

bool Release(const Environment &e, NativeVector &vector) noexcept {
  if (!vector.data_address) return true;
#if defined(_MSC_VER)
  __try { e.allocator.release_allocation(vector.allocator,
      reinterpret_cast<void *>(vector.data_address), sizeof(std::uintptr_t)); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  e.allocator.release_allocation(vector.allocator,
      reinterpret_cast<void *>(vector.data_address), sizeof(std::uintptr_t));
#endif
  return true;
}

struct OwnedVector {
  const Environment &environment;
  NativeVector vector{};
  bool release_attempted = false;
  bool Finish() noexcept { release_attempted = true; return Release(environment, vector); }
  ~OwnedVector() { if (!release_attempted) Release(environment, vector); }
};

bool MonthlyRate(const Environment &e, const void *type, const void *scopes,
                 bool frozen, std::int64_t &out) noexcept {
  std::int64_t *returned = nullptr;
  return Invoke(e.monthly_rate, returned, type, &out, scopes, nullptr, frozen) &&
      returned == &out;
}

Failure Candidates(const Environment &e, const CurrentState &current,
                   const void *type, Observation &out) {
  TaskScopes scopes{};
  scopes.incumbent = current.seat.incumbent_character_id;
  scopes.owner = out.owner_character_id;
  auto *dispatch = out.task_dispatch ? &*out.task_dispatch : nullptr;
  bool dispatch_evaluating = dispatch && e.final_task_validator &&
      (e.offline_fixture || reinterpret_cast<std::uintptr_t>(e.final_task_validator) ==
          e.module_base + kTaskDispatchValidatorRva);
  if (dispatch) dispatch->failure = dispatch_evaluating ? "none" : "bindings_unavailable";
  bool shown = false, valid = false;
  if (!Invoke(e.shown, shown, type, static_cast<const void *>(&scopes)) ||
      !Invoke(e.valid, valid, type, static_cast<const void *>(&scopes), nullptr))
    return Failure::native_evaluation_unavailable;
  out.native_task_shown = shown; out.native_task_valid = valid;
  if (!shown || !valid) {
    if (dispatch_evaluating) dispatch->available = true;
    return Failure::none;
  }
  alignas(16) std::array<std::byte, ck3_12002::kCouncilCandidatesAllocatorSize12002> allocator{};
  OwnedVector owned{e};
  auto &vector = owned.vector;
  Failure failure = Failure::none;
  if (!Initialize(e, allocator.data(), vector) ||
      !Produce(e, current.seat.incumbent, type, vector) ||
      vector.count < 0 || vector.capacity < 0 || vector.capacity > 65'536 ||
      vector.count > vector.capacity || (vector.count > 0 && !vector.data_address))
    failure = Failure::candidate_collection_unavailable;
  if (failure == Failure::none) {
    out.candidates.reserve(static_cast<std::size_t>(vector.count));
    for (std::int32_t ordinal = 0; ordinal < vector.count; ++ordinal) {
      const void *province = nullptr, *county = nullptr;
      Candidate row{};
      if (!At(e, reinterpret_cast<const void *>(vector.data_address),
          static_cast<std::size_t>(ordinal) * sizeof(void *), province) ||
          !CountyIdentity(e, province, county, row)) {
        failure = Failure::county_identity_unavailable; break;
      }
      if (std::any_of(out.candidates.begin(), out.candidates.end(),
          [&](const auto &other) { return other.province_id == row.province_id ||
              other.county_title_id == row.county_title_id; })) {
        failure = Failure::county_identity_unavailable; break;
      }
      if (!CountyRite(e, county, row.county_rite_id)) {
        failure = Failure::county_rite_unavailable; break;
      }
      row.native_collection_ordinal = static_cast<std::uint32_t>(ordinal);
      row.directly_held_by_player = row.holder_character_id == out.owner_character_id;
      if (!Invoke(e.target_valid, row.native_target_valid, type,
          static_cast<const void *>(current.seat.incumbent), province, nullptr)) {
        failure = Failure::native_evaluation_unavailable; break;
      }
      if (row.native_target_valid) {
        scopes.target_tag = 8; scopes.target = row.province_id;
        std::int64_t rate = 0;
        if (!MonthlyRate(e, type, &scopes, false, rate)) {
          failure = Failure::native_evaluation_unavailable; break;
        }
        row.native_monthly_rate_raw = rate;
      }
      if (dispatch_evaluating) {
        ChangeTaskValidationPacket packet{};
        packet.active_task_id = current.seat.task_id;
        packet.task_type = type;
        packet.scopes = scopes;
        packet.scopes.target_tag = 8;
        packet.scopes.target = row.province_id;
        TaskDispatchCandidate input{};
        input.province_id = row.province_id;
        input.county_title_id = row.county_title_id;
        input.already_active_at_target = current.key == kTaskKey &&
            current.province == row.province_id;
        input.replacement_required = !input.already_active_at_target;
        if (!Invoke(e.final_task_validator, input.native_final_can_dispatch,
            static_cast<const void *>(&packet), nullptr)) {
          dispatch->failure = "native_final_validator_unavailable";
          dispatch->candidates.clear();
          dispatch_evaluating = false;
        } else {
          dispatch->candidates.push_back(input);
        }
      }
      out.candidates.push_back(row);
    }
  }
  if (!owned.Finish()) return Failure::candidate_collection_unavailable;
  if (failure != Failure::none) return failure;
  std::sort(out.candidates.begin(), out.candidates.end(), [](const auto &a, const auto &b) {
    return static_cast<std::uint32_t>(a.county_title_id) <
           static_cast<std::uint32_t>(b.county_title_id);
  });
  out.candidate_collection_evaluated = true;
  out.candidate_collection_complete = true;
  if (dispatch_evaluating) {
    std::sort(dispatch->candidates.begin(), dispatch->candidates.end(),
        [](const auto &a, const auto &b) {
          return static_cast<std::uint32_t>(a.county_title_id) <
              static_cast<std::uint32_t>(b.county_title_id);
        });
    dispatch->available = true;
  }
  return Failure::none;
}

bool SameFrame(const Frame &a, const Frame &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}

void ReadValueInputs(const Environment &e, const CurrentState &current,
                     Observation &out) {
  if (!e.value_inputs_enabled) return;
  auto &values = out.value_inputs.emplace();
  if (!e.character_rite || !e.rite_faith || !e.government || !e.identifier_name ||
      !e.title_by_key || !e.county_opinion || !e.government_fallback_slot) return;
  if (!current.seat.incumbent || !current.owner_rite || !current.incumbent_rite) {
    values.failure = "owner_or_incumbent_rite_absent"; return;
  }
  std::uint32_t owner_faith = 0, incumbent_faith = 0;
  bool ministry = false;
  if (!CharacterFaith(e, current.seat.owner, current.owner_rite, owner_faith) ||
      !CharacterFaith(e, current.seat.incumbent, current.incumbent_rite, incumbent_faith)) {
    values.failure = "character_faith_unavailable"; return;
  }
  if (!MinistryAccess(e, current.seat.owner, out.owner_character_id, ministry)) {
    values.failure = "ministry_access_unavailable"; return;
  }
  values.owner_faith_id = owner_faith; values.incumbent_faith_id = incumbent_faith;
  values.owner_has_access_to_ministry = ministry;
  if (current.province) {
    const void *province = nullptr, *county = nullptr;
    Candidate identity{};
    CountyValueInputs target{};
    if (!ProvinceById(e, *current.province, province) ||
        !CountyIdentity(e, province, county, identity)) {
      values.failure = "current_target_identity_unavailable"; return;
    }
    identity.county_rite_id = current.county_rite;
    if (!CountyValues(e, identity, owner_faith, incumbent_faith,
        *current.owner_rite, *current.incumbent_rite, ministry, target)) {
      values.failure = "current_target_values_unavailable"; return;
    }
    values.current_target = target;
  }
  for (const auto &identity : out.candidates) {
    CountyValueInputs row{};
    if (!CountyValues(e, identity, owner_faith, incumbent_faith,
        *current.owner_rite, *current.incumbent_rite, ministry, row)) {
      values.failure = "candidate_values_unavailable";
      values.candidates.clear(); return;
    }
    values.candidates.push_back(row);
  }
  values.available = true; values.failure = "none";
}

bool Failed(Observation &out, Failure failure) {
  const auto epoch = out.capture_epoch;
  const auto date = out.date_raw;
  const auto owner = out.owner_character_id;
  out = {}; out.capture_epoch = epoch; out.date_raw = date;
  out.owner_character_id = owner; out.failure = failure;
  return false;
}

template <typename T>
void Optional(std::ostringstream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}

void JsonString(std::ostringstream &out, std::string_view text) {
  out << '"';
  for (const auto ch : text) {
    if (ch == '"' || ch == '\\') out << '\\';
    out << ch;
  }
  out << '"';
}
} // namespace

Environment BindCountyConversionImage12003(std::uintptr_t base,
    std::string_view sha) noexcept {
  Environment e{};
  if (!base || sha != ck3_12003::kExecutableSha256) return e;
  e.exact_build_admitted = true; e.module_base = base;
  e.executable_sha256 = ck3_12003::kExecutableSha256;
  // The .3 frozen ABI reuses the .2 core/chaplain/allocator layouts. Admission
  // remains the exact .3 identity above; the legacy bindings are internal only.
  e.clergy = ck3_12002::religion::clergy::BindClergyAppointmentImage12002(
      base, ck3_12002::kExecutableSha256);
  e.allocator = ck3_12002::BindCouncilCandidates12002(base, ck3_12002::kExecutableSha256);
  e.game_state_slot = reinterpret_cast<void **>(base + 0x5C68C50);
  e.title_storage_slot = reinterpret_cast<void **>(base + 0x5D1DAF8);
  e.title_fallback_slot = reinterpret_cast<void **>(base + 0x5D1DAE0);
  e.task_type_database_slot = reinterpret_cast<void **>(base + 0x5C671D8);
  e.task_type_fallback_slot = reinterpret_cast<void **>(base + 0x5D1F900);
  e.hash_key = reinterpret_cast<HashKey>(base + 0x3F7E240);
  e.lookup_type = reinterpret_cast<LookupType>(base + 0xCF1E80);
  e.shown = reinterpret_cast<Shown>(base + 0x31AC7B0);
  e.valid = reinterpret_cast<Valid>(base + 0x31AC680);
  e.target_valid = reinterpret_cast<TargetValid>(base + 0x2C48970);
  e.produce_targets = reinterpret_cast<ProduceTargets>(base + 0x2C48E80);
  e.monthly_rate = reinterpret_cast<EvaluatedTaskMonthlyRate>(base + kMonthlyRateRva);
  e.county_rite = reinterpret_cast<CountyRiteGetter>(base + kCountyRiteRva);
  e.value_inputs_enabled = true;
  e.character_rite = reinterpret_cast<ObjectGetter>(base + 0x28D2F90);
  e.rite_faith = reinterpret_cast<ObjectGetter>(base + 0x24FC560);
  e.government = reinterpret_cast<ObjectGetter>(base + 0x28C2E10);
  e.title_by_key = reinterpret_cast<ObjectGetter>(base + 0xA847A0);
  e.identifier_name = reinterpret_cast<IdentifierName>(base + 0x3F4F900);
  e.county_opinion = reinterpret_cast<CountyOpinionGetter>(base + 0x24D4CB0);
  e.government_fallback_slot = reinterpret_cast<void **>(base + 0x5D1E2A8);
  e.task_dispatch_enabled = true;
  e.final_task_validator = reinterpret_cast<ChangeCouncilTaskFinalValidator>(
      base + kTaskDispatchValidatorRva);
  return e;
}

bool ReadCountyConversion12003(const Environment &e, std::uint64_t epoch,
                             Observation &out) noexcept {
  try {
    out = {}; out.capture_epoch = epoch;
    if (!Exact(e)) return Failed(out, Failure::bindings_unavailable);
    if (!e.offline_fixture) {
#if defined(_WIN32)
      if (!e.application_main_thread_id ||
          GetCurrentThreadId() != e.application_main_thread_id)
#endif
        return Failed(out, Failure::owner_thread_required);
    }
    Frame before{}, after{};
    if (!Snapshot(e, before)) return Failed(out, Failure::frame_unavailable);
    out.date_raw = before.clock.date_raw;
    if (!before.clock.paused) return Failed(out, Failure::not_paused);
    if (!before.map_ready || !before.has_played_character || !before.played_character_alive)
      return Failed(out, Failure::player_unavailable);
    out.owner_character_id = before.played_character_id;
    CurrentState current{}, last{};
    auto failure = ReadCurrent(e, out.owner_character_id, current);
    if (failure != Failure::none) return Failed(out, failure);
    PublishCurrent(current, out);
    if (e.task_dispatch_enabled) out.task_dispatch.emplace();
    if (current.seat.task && current.seat.incumbent) {
      const void *type = nullptr;
      if (!TaskType(e, current.seat, type)) return Failed(out, Failure::task_type_unavailable);
      if (current.key == kTaskKey) {
        if (current.seat.type != type || current.kind != 1 || current.progress_kind != 1)
          return Failed(out, Failure::current_task_unavailable);
        std::int64_t rate = 0;
        if (!MonthlyRate(e, current.seat.type,
            static_cast<const std::byte *>(current.seat.task) + 0x40,
            current.frozen.value(), rate))
          return Failed(out, Failure::native_evaluation_unavailable);
        out.current_conversion_monthly_rate_raw = rate;
      }
      failure = Candidates(e, current, type, out);
      if (failure != Failure::none) return Failed(out, failure);
    }
    ReadValueInputs(e, current, out);
    if (!Snapshot(e, after) || !SameFrame(before, after) ||
        ReadCurrent(e, out.owner_character_id, last) != Failure::none || current != last)
      return Failed(out, Failure::state_changed);
    out.available = true; out.failure = Failure::none;
    return true;
  } catch (...) {
    try { return Failed(out, Failure::reader_exception); }
    catch (...) { return false; }
  }
}

const char *CountyConversionFailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::owner_thread_required: return "owner_thread_required";
  case Failure::frame_unavailable: return "frame_unavailable";
  case Failure::not_paused: return "not_paused";
  case Failure::player_unavailable: return "player_unavailable";
  case Failure::clergy_seat_unavailable: return "clergy_seat_unavailable";
  case Failure::task_type_unavailable: return "task_type_unavailable";
  case Failure::current_task_unavailable: return "current_task_unavailable";
  case Failure::candidate_collection_unavailable: return "candidate_collection_unavailable";
  case Failure::county_identity_unavailable: return "county_identity_unavailable";
  case Failure::county_rite_unavailable: return "county_rite_unavailable";
  case Failure::native_evaluation_unavailable: return "native_evaluation_unavailable";
  case Failure::state_changed: return "state_changed";
  case Failure::reader_exception: return "reader_exception";
  }
  return "unknown";
}

std::string SerializeCountyConversion12003(const Observation &v) {
  std::ostringstream o; o << std::boolalpha;
  o << "{\"schema\":\"xar.ck3.county-conversion/v1\",\"schema_version\":1,"
    << "\"exact_build\":{\"game_version\":\"1.20.0.3\",\"steam_build\":25652598,"
    << "\"executable_sha256\":\"" << ck3_12003::kExecutableSha256 << "\"},"
    << "\"status\":\"" << (v.available ? "available" : "unavailable")
    << "\",\"failure\":\"" << CountyConversionFailureKey(v.failure)
    << "\",\"capture_epoch\":" << v.capture_epoch << ",\"date_raw\":" << v.date_raw
    << ",\"owner_character_id\":" << v.owner_character_id << ",\"owner_rite_id\":";
  Optional(o, v.owner_rite_id);
  o << ",\"position_present\":" << v.position_present << ",\"incumbent_character_id\":";
  Optional(o, v.incumbent_character_id);
  o << ",\"incumbent_rite_id\":"; Optional(o, v.incumbent_rite_id);
  o << ",\"active_task_id\":"; Optional(o, v.active_task_id);
  o << ",\"current_task_key\":"; JsonString(o, v.current_task_key);
  o << ",\"current_task_type\":"; Optional(o, v.current_task_type);
  o << ",\"current_progress_kind\":"; Optional(o, v.current_progress_kind);
  o << ",\"current_task_frozen\":"; Optional(o, v.current_task_frozen);
  o << ",\"current_percentage_progress_raw\":"; Optional(o, v.current_percentage_progress_raw);
  o << ",\"percentage_progress_maximum_raw\":10000000,\"fixed_point_scale\":" << kFixedPointScale;
  o << ",\"current_conversion_monthly_rate_raw\":";
  Optional(o, v.current_conversion_monthly_rate_raw);
  o << ",\"current_target_province_id\":"; Optional(o, v.current_target_province_id);
  o << ",\"current_target_county_title_id\":"; Optional(o, v.current_target_county_title_id);
  o << ",\"current_target_county_rite_id\":"; Optional(o, v.current_target_county_rite_id);
  o << ",\"task_key\":\"" << kTaskKey << "\",\"native_task_shown\":";
  Optional(o, v.native_task_shown);
  o << ",\"native_task_valid\":"; Optional(o, v.native_task_valid);
  o << ",\"candidate_collection_evaluated\":" << v.candidate_collection_evaluated
    << ",\"candidate_collection_complete\":" << v.candidate_collection_complete
    << ",\"candidate_count\":" << v.candidates.size() << ",\"candidates\":[";
  bool comma = false;
  for (const auto &row : v.candidates) {
    if (comma) o << ',';
    comma = true;
    o << "{\"native_collection_ordinal\":" << row.native_collection_ordinal
      << ",\"province_id\":" << row.province_id
      << ",\"county_title_id\":" << row.county_title_id
      << ",\"holder_character_id\":" << row.holder_character_id << ",\"county_rite_id\":";
    Optional(o, row.county_rite_id);
    o << ",\"directly_held_by_player\":" << row.directly_held_by_player
      << ",\"native_target_valid\":" << row.native_target_valid
      << ",\"native_monthly_rate_raw\":"; Optional(o, row.native_monthly_rate_raw);
    o << ",\"native_monthly_rate_scale\":" << kFixedPointScale << '}';
  }
  o << ']';
  if (v.value_inputs) {
    const auto &values = *v.value_inputs;
    const auto county_value = [&](const CountyValueInputs &row) {
      o << "{\"province_id\":" << row.province_id
        << ",\"county_title_id\":" << row.county_title_id
        << ",\"holder_character_id\":" << row.holder_character_id
        << ",\"county_faith_id\":" << row.county_faith_id
        << ",\"destination_rite_id\":" << row.destination_rite_id
        << ",\"destination_faith_id\":" << row.destination_faith_id
        << ",\"current_popular_opinion\":" << row.current_popular_opinion
        << ",\"popular_opinion_scale\":1,\"faith_changes\":" << row.faith_changes
        << ",\"rite_changes\":" << row.rite_changes << '}';
    };
    o << ",\"value_inputs\":{\"status\":\""
      << (values.available ? "available" : "unavailable") << "\",\"failure\":";
    JsonString(o, values.failure);
    o << ",\"owner_faith_id\":"; Optional(o, values.owner_faith_id);
    o << ",\"incumbent_faith_id\":"; Optional(o, values.incumbent_faith_id);
    o << ",\"owner_has_access_to_ministry\":";
    Optional(o, values.owner_has_access_to_ministry);
    o << ",\"current_target\":";
    if (values.current_target) county_value(*values.current_target); else o << "null";
    o << ",\"candidates\":[";
    bool value_comma = false;
    for (const auto &row : values.candidates) {
      if (value_comma) o << ',';
      value_comma = true; county_value(row);
    }
    o << "],\"decision_inputs_complete\":" << values.available << '}';
  }
  if (v.task_dispatch) {
    const auto &dispatch = *v.task_dispatch;
    o << ",\"task_dispatch\":{\"status\":\""
      << (dispatch.available ? "available" : "unavailable") << "\",\"failure\":";
    JsonString(o, dispatch.failure);
    o << ",\"candidates\":[";
    bool dispatch_comma = false;
    for (const auto &row : dispatch.candidates) {
      if (dispatch_comma) o << ',';
      dispatch_comma = true;
      o << "{\"province_id\":" << row.province_id
        << ",\"county_title_id\":" << row.county_title_id
        << ",\"native_final_can_dispatch\":" << row.native_final_can_dispatch
        << ",\"already_active_at_target\":" << row.already_active_at_target
        << ",\"replacement_required\":" << row.replacement_required << '}';
    }
    o << "],\"eligibility_inputs_complete\":" << dispatch.available << '}';
  }
  o << ",\"action_eligibility_complete\":"
    << (v.task_dispatch && v.task_dispatch->available) << '}';
  return o.str();
}

} // namespace xar::ck3_12003::religion::county_conversion
