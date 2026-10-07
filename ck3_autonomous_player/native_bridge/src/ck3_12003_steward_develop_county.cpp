#include "xar_bridge/ck3_12003_steward_develop_county.hpp"
#include "xar_bridge/ck3_12004_steward_develop_county.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <utility>

#if defined(_MSC_VER)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::ck3_12003 {
namespace {
using Environment = StewardDevelopCountyEnvironment12003;
using Access = StewardDevelopCountyAccess12003;
using Failure = game::StewardDevelopCountyFailureReasonV1;
using Result = game::ReadStewardDevelopCountyCandidatesResultV1;
using CouncilAccess = ck3_12002::CouncilCandidatesAccessV1;
using CouncilFrame = ck3_12002::CouncilCandidatesFrameV1;
constexpr std::int64_t kScale = 100'000;
constexpr std::string_view kTask = "task_develop_county";

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

struct Proxy {
  const Environment *environment = nullptr;
  const Access *access = nullptr;
};

bool Memory(void *opaque, const void *address, void *out, std::size_t size) noexcept {
  const auto &proxy = *static_cast<Proxy *>(opaque);
  if (proxy.access->read_memory != nullptr)
    return proxy.access->read_memory(proxy.access->context, address, out, size);
  CouncilAccess direct{};
  return ck3_12002::ReadCouncilMemory12002(direct, address, out, size);
}

bool MainThread(void *opaque) noexcept {
  const auto &proxy = *static_cast<Proxy *>(opaque);
  return proxy.access->is_main_thread != nullptr &&
         proxy.access->is_main_thread(proxy.access->context);
}

ck3_12004::CouncilCandidatesAccessV1 Actual4Access(const CouncilAccess &access) noexcept {
  ck3_12004::CouncilCandidatesAccessV1 out{};
  out.context = access.context;
  out.capture_frame = access.capture_frame;
  out.is_main_thread = access.is_main_thread;
  out.read_memory = access.read_memory;
  return out;
}

bool ResolveSourceCharacter(const Environment &env, const CouncilAccess &access,
                            std::int32_t id, const void *&pointer) noexcept {
  if (env.admitted_executable_sha256 == ck3_12004::kExecutableSha256)
    return ck3_12004::ResolveCouncilCharacter12004(
        env.council12004, Actual4Access(access), id, pointer);
  return ck3_12002::ResolveCouncilCharacter12002(env.council, access, id, pointer);
}

bool CaptureSourceFrame(const Environment &env, const CouncilAccess &access,
                        CouncilFrame &frame) noexcept {
  if (env.admitted_executable_sha256 == ck3_12004::kExecutableSha256)
    return ck3_12004::CaptureCouncilCandidatesFrame12004(
        env.council12004, Actual4Access(access), frame);
  return ck3_12002::CaptureCouncilCandidatesFrame12002(env.council, access, frame);
}

bool Capture(void *opaque, CouncilFrame &out) noexcept {
  auto &proxy = *static_cast<Proxy *>(opaque);
  game::StewardDevelopCountyCandidatesFrameV1 frame{};
  if (proxy.access->capture_frame == nullptr ||
      !proxy.access->capture_frame(proxy.access->context, frame)) return false;
  out = {};
  out.native_revision = frame.snapshot_revision;
  out.public_revision = frame.snapshot_revision;
  out.date_raw = frame.date_raw;
  out.paused = frame.paused;
  out.map_ready = frame.map_ready;
  out.has_played_character = frame.has_played_character;
  out.played_character_alive = frame.played_character_alive;
  out.played_character_id = frame.played_character_id;
  CouncilAccess access{};
  access.context = &proxy;
  access.read_memory = &Memory;
  const void *player = nullptr;
  if (frame.has_played_character &&
      ResolveSourceCharacter(*proxy.environment,
          access, frame.played_character_id, player))
    out.played_character = reinterpret_cast<std::uintptr_t>(player);
  return true;
}

CouncilAccess SourceAccess(Proxy &proxy) noexcept {
  CouncilAccess out{};
  out.context = &proxy;
  out.capture_frame = &Capture;
  out.is_main_thread = &MainThread;
  out.read_memory = &Memory;
  return out;
}

template <typename T>
bool Read(const CouncilAccess &access, const void *base, std::size_t offset,
          T &out) noexcept {
  const auto start = reinterpret_cast<std::uintptr_t>(base);
  return base != nullptr && offset <= (std::numeric_limits<std::uintptr_t>::max)() - start &&
      ck3_12002::ReadCouncilMemory12002(access,
          reinterpret_cast<const void *>(start + offset), &out, sizeof(out));
}

bool Key(const CouncilAccess &access, const void *object, std::string &out) {
  std::size_t length = 0, capacity = 0;
  const auto *key = static_cast<const std::byte *>(object) + 0x18;
  if (!Read(access, key, 0x10, length) || !Read(access, key, 0x18, capacity) ||
      length == 0 || length > capacity || length > 1'024) return false;
  const void *bytes = key;
  if (capacity > 15 && (!Read(access, key, 0, bytes) || bytes == nullptr)) return false;
  out.resize(length);
  return ck3_12002::ReadCouncilMemory12002(access, bytes, out.data(), length) &&
      std::none_of(out.begin(), out.end(), [](unsigned char value) {
        return value == 0 || value < 0x20U;
      });
}

template <typename Function, typename Return, typename... Args>
bool Invoke(Function function, Return &out, Args... args) noexcept {
  if (function == nullptr) return false;
#if defined(_MSC_VER)
  __try { out = function(args...); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  out = function(args...);
#endif
  return true;
}

bool Produce(const Environment &env, const void *steward, const void *type,
             DevelopVector &vector) noexcept {
#if defined(_MSC_VER)
  __try { env.produce_targets(steward, type, false, &vector, true); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  env.produce_targets(steward, type, false, &vector, true);
#endif
  return true;
}

bool Initialize(const Environment &env, void *allocator, DevelopVector &vector) noexcept {
  std::memset(allocator, 0, ck3_12002::kCouncilCandidatesAllocatorSize12002);
  std::memcpy(allocator, &env.council.allocator_vtable, sizeof(std::uintptr_t));
  std::memcpy(static_cast<std::byte *>(allocator) +
      ck3_12002::kCouncilCandidatesAllocatorFallbackOffset12002,
      &env.council.fallback_allocator, sizeof(std::uintptr_t));
  vector = {};
  vector.allocator = allocator;
#if defined(_MSC_VER)
  __try { env.council.initialize_vector(allocator, &vector.data_address, &vector.capacity); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  env.council.initialize_vector(allocator, &vector.data_address, &vector.capacity);
#endif
  return vector.data_address == reinterpret_cast<std::uintptr_t>(allocator) + 8 &&
         vector.capacity == 64 && vector.count == 0;
}

bool Release(const Environment &env, DevelopVector &vector) noexcept {
  if (vector.data_address == 0) return true;
#if defined(_MSC_VER)
  __try { env.council.release_allocation(vector.allocator,
      reinterpret_cast<void *>(vector.data_address), sizeof(std::uintptr_t)); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  env.council.release_allocation(vector.allocator,
      reinterpret_cast<void *>(vector.data_address), sizeof(std::uintptr_t));
#endif
  return true;
}

struct OwnedVector {
  const Environment &environment;
  DevelopVector vector{};
  bool release_attempted = false;
  bool Finish() noexcept {
    release_attempted = true;
    return Release(environment, vector);
  }
  ~OwnedVector() {
    if (!release_attempted) Release(environment, vector);
  }
};

bool Exact(const Environment &env) noexcept {
  if (env.admitted_executable_sha256 == ck3_12004::kExecutableSha256)
    return ck3_12004::IsStewardDevelopCountyEnvironment12004(env);
  if (!env.exact_build_admitted || env.module_base == 0 ||
      env.admitted_executable_sha256 != kExecutableSha256 ||
      env.game_state_slot == nullptr || env.title_storage_slot == nullptr ||
      env.title_fallback_slot == nullptr || env.task_type_database_slot == nullptr ||
      env.task_type_fallback_slot == nullptr || env.hash_key == nullptr ||
      env.lookup_type == nullptr || env.immediate_liege == nullptr ||
      env.capital_province == nullptr || env.is_human == nullptr ||
      env.shown == nullptr || env.valid == nullptr || env.target_valid == nullptr ||
      env.growth == nullptr || env.decay == nullptr ||
      env.current_progress == nullptr || env.maximum_progress == nullptr ||
      env.produce_targets == nullptr) return false;
  if (env.offline_fixture_function_overrides)
    return env.council.offline_fixture_function_overrides;
  const auto base = env.module_base;
  return !env.council.offline_fixture_function_overrides &&
      env.council.module_base == base &&
      reinterpret_cast<std::uintptr_t>(env.game_state_slot) == base + 0x5C68C50 &&
      reinterpret_cast<std::uintptr_t>(env.title_storage_slot) == base + 0x5D1DAF8 &&
      reinterpret_cast<std::uintptr_t>(env.title_fallback_slot) == base + 0x5D1DAE0 &&
      reinterpret_cast<std::uintptr_t>(env.task_type_database_slot) == base + 0x5C671D8 &&
      reinterpret_cast<std::uintptr_t>(env.task_type_fallback_slot) == base + 0x5D1F900 &&
      reinterpret_cast<std::uintptr_t>(env.hash_key) == base + 0x3F7E240 &&
      reinterpret_cast<std::uintptr_t>(env.lookup_type) == base + 0xCF1E80 &&
      reinterpret_cast<std::uintptr_t>(env.immediate_liege) == base + 0x28BFC70 &&
      reinterpret_cast<std::uintptr_t>(env.capital_province) == base + 0x28B1CD0 &&
      reinterpret_cast<std::uintptr_t>(env.is_human) == base + 0x2BAA710 &&
      reinterpret_cast<std::uintptr_t>(env.shown) == base + 0x31AC7B0 &&
      reinterpret_cast<std::uintptr_t>(env.valid) == base + 0x31AC680 &&
      reinterpret_cast<std::uintptr_t>(env.target_valid) == base + 0x2C48970 &&
      reinterpret_cast<std::uintptr_t>(env.growth) == base + 0x24CF900 &&
      reinterpret_cast<std::uintptr_t>(env.decay) == base + 0x24CFB50 &&
      reinterpret_cast<std::uintptr_t>(env.current_progress) == base + 0x31AB520 &&
      reinterpret_cast<std::uintptr_t>(env.maximum_progress) == base + 0x31AB840 &&
      reinterpret_cast<std::uintptr_t>(env.produce_targets) == base + 0x2C48E80;
}

bool Province(const Environment &env, const CouncilAccess &access,
              const void *province, std::int32_t &id) noexcept {
  void *state = nullptr, *data = nullptr, *array = nullptr, *indexed = nullptr;
  std::int32_t count = 0;
  std::uint32_t tag = 0;
  return province != nullptr && Read(access, province, 0x10, id) && id > 0 &&
      Read(access, province, 0x85C, tag) && tag == 0x50726F76U &&
      Read(access, env.game_state_slot, 0, state) && Read(access, state, 0xA0, data) &&
      Read(access, data, 0x140, array) && array != nullptr &&
      Read(access, data, 0x14C, count) && count > 0 && count <= 65'536 && id < count &&
      Read(access, array, static_cast<std::size_t>(id) * 8, indexed) && indexed == province;
}

bool Title(const Environment &env, const CouncilAccess &access,
           std::int32_t id, const void *&out) noexcept {
  void *storage = nullptr, *fallback = nullptr, *entries = nullptr, *title = nullptr;
  std::int32_t capacity = 0, observed = -1;
  if (id <= 0 || !Read(access, env.title_storage_slot, 0, storage) || storage == nullptr ||
      !Read(access, env.title_fallback_slot, 0, fallback) ||
      !Read(access, storage, 0x20, entries) || entries == nullptr ||
      !Read(access, storage, 0x2C, capacity) || capacity <= 0 || capacity > 4'194'304)
    return false;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity) ||
      !Read(access, entries, static_cast<std::size_t>(index) * 0x10 + 8, title) ||
      title == nullptr || title == fallback || !Read(access, title, 0x10, observed) ||
      observed != id) return false;
  out = title;
  return true;
}

bool Progress(const Environment &env, const void *type, const void *scopes,
              game::FixedPointValue &current, game::FixedPointValue &maximum) noexcept {
  std::int64_t *returned = nullptr;
  if (!Invoke(env.current_progress, returned, type, &current.raw, scopes) ||
      returned != &current.raw ||
      !Invoke(env.maximum_progress, returned, type, &maximum.raw, scopes) ||
      returned != &maximum.raw) return false;
  current.scale = maximum.scale = kScale;
  return current.raw >= 0 && maximum.raw > 0 && current.raw <= maximum.raw;
}

bool Binding(const Environment &env, const CouncilAccess &access,
             const CouncilFrame &frame, game::CampaignRootCouncilPositionV1 &out,
             const void *&steward) {
  const auto *task = reinterpret_cast<const void *>(frame.active_task);
  const void *type = nullptr;
  std::int32_t incumbent = -1, owner = -1, kind = -1, progress_kind = -1;
  std::uint8_t frozen = 0;
  std::string key;
  if (!Read(access, task, 0x18, type) || type == nullptr || !Key(access, type, key) ||
      !Read(access, task, 0x40, incumbent) || incumbent <= 0 ||
      !Read(access, task, 0x44, owner) || owner != frame.played_character_id ||
      !ResolveSourceCharacter(env, access, incumbent, steward) ||
      !Read(access, type, 0x48, kind) || kind < 0 || kind > 2 ||
      !Read(access, type, 0x54, progress_kind) || progress_kind < 0 || progress_kind > 2 ||
      !Read(access, task, 0x39, frozen) || frozen > 1) return false;
  out.position_key = "councillor_steward";
  out.incumbent_character_id = incumbent;
  out.task_key = key;
  out.task_type = static_cast<game::CampaignRootCouncilTaskTypeV1>(kind);
  out.frozen = frozen != 0;
  if (kind != 0) {
    std::uint16_t tag = 0;
    std::int32_t target = -1;
    if (!Read(access, task, 0x48, tag) || !Read(access, task, 0x50, target)) return false;
    if (kind == 1) {
      void *state = nullptr, *data = nullptr, *array = nullptr, *province = nullptr;
      std::int32_t count = 0, observed = -1;
      if (tag != 8 || target <= 0 || !Read(access, env.game_state_slot, 0, state) ||
          !Read(access, state, 0xA0, data) || !Read(access, data, 0x140, array) ||
          !Read(access, data, 0x14C, count) || target >= count || count > 65'536 ||
          !Read(access, array, static_cast<std::size_t>(target) * 8, province) ||
          !Province(env, access, province, observed) || observed != target) return false;
      out.target = game::CampaignRootCouncilTargetV1{target, std::nullopt};
    } else {
      const void *character = nullptr;
      if (tag != 4 || !ResolveSourceCharacter(env, access,
          target, character)) return false;
      out.target = game::CampaignRootCouncilTargetV1{std::nullopt, target};
    }
  }
  game::CampaignRootCouncilProgressV1 progress{};
  progress.kind = static_cast<game::CampaignRootCouncilProgressKindV1>(progress_kind);
  if (progress_kind != 0) {
    game::FixedPointValue current{0, kScale}, maximum{10'000'000, kScale};
    if (progress_kind == 1) {
      if (!Read(access, task, 0x20, current.raw) || current.raw < 0 ||
          current.raw > maximum.raw) return false;
    } else if (!Progress(env, type, static_cast<const std::byte *>(task) + 0x40,
                         current, maximum)) return false;
    progress.current = current;
    progress.maximum = maximum;
  }
  out.progress = progress;
  return true;
}

struct Sample {
  bool shown = false;
  bool valid = false;
  game::StewardDevelopCountyMaterialV1 material{};
  friend bool operator==(const Sample &, const Sample &) = default;
};

Failure ReadSample(const Environment &env, const CouncilAccess &access,
                   const CouncilFrame &frame, Sample &out) {
  const void *steward = nullptr, *owner = nullptr, *liege = nullptr, *type = nullptr;
  game::CampaignRootCouncilPositionV1 binding{};
  if (!Binding(env, access, frame, binding, steward) ||
      !ResolveSourceCharacter(env, access,
          frame.played_character_id, owner)) return Failure::identity_round_trip_failed;
  bool human = false;
  if (!Invoke(env.immediate_liege, liege, steward) || liege != owner ||
      !Invoke(env.is_human, human, frame.played_character_id) || !human)
    return Failure::candidate_invalid;
  void *database = nullptr, *fallback = nullptr;
  std::int32_t hash = 0, kind = -1, player_scope = -1, progress_kind = -1;
  std::string key;
  if (!Read(access, env.task_type_database_slot, 0, database) || database == nullptr ||
      !Read(access, env.task_type_fallback_slot, 0, fallback) ||
      !Invoke(env.hash_key, hash, nullptr, kTask.data(), static_cast<std::uint32_t>(kTask.size())) ||
      !Invoke(env.lookup_type, type, static_cast<const void *>(database), hash) ||
      type == nullptr || type == fallback || !Key(access, type, key) || key != kTask ||
      !Read(access, type, 0x48, kind) || kind != 1 ||
      !Read(access, type, 0x4C, player_scope) || player_scope != 2 ||
      !Read(access, type, 0x54, progress_kind) || progress_kind != 2)
    return Failure::native_reader_not_frozen;
  TaskScopes scopes{};
  scopes.incumbent = binding.incumbent_character_id.value();
  scopes.owner = frame.played_character_id;
  if (!Invoke(env.shown, out.shown, type, static_cast<const void *>(&scopes)) ||
      !Invoke(env.valid, out.valid, type, static_cast<const void *>(&scopes), nullptr))
    return Failure::fixture_source_failed;
  out.material.current_active_task_binding = binding;
  if (!out.shown || !out.valid) {
    out.material.candidate_collection_complete = true;
    return Failure::none;
  }
  const void *capital = nullptr;
  std::int32_t capital_id = -1;
  if (!Invoke(env.capital_province, capital, owner) ||
      (capital != nullptr && !Province(env, access, capital, capital_id)))
    return Failure::identity_round_trip_failed;
  alignas(16) std::array<std::byte, ck3_12002::kCouncilCandidatesAllocatorSize12002> allocator{};
  OwnedVector owned{env};
  auto &vector = owned.vector;
  Failure failure = Failure::none;
  if (!Initialize(env, allocator.data(), vector) ||
      !Produce(env, steward, type, vector)) failure = Failure::fixture_source_failed;
  if (failure == Failure::none &&
      (vector.count < 0 || vector.capacity < 0 || vector.capacity > 65'536 ||
       vector.count > vector.capacity || (vector.count > 0 && vector.data_address == 0)))
    failure = Failure::candidate_invalid;
  if (failure == Failure::none) {
    out.material.candidates.reserve(static_cast<std::size_t>(vector.count));
    for (std::int32_t ordinal = 0; ordinal < vector.count; ++ordinal) {
      const void *province = nullptr, *county = nullptr, *title = nullptr, *holder = nullptr;
      game::StewardDevelopCountyMaterialCandidateV1 row{};
      if (!Read(access, reinterpret_cast<const void *>(vector.data_address),
          static_cast<std::size_t>(ordinal) * sizeof(std::uintptr_t), province) ||
          !Province(env, access, province, row.capital_province_id) ||
          !Read(access, province, 0x848, county) || county == nullptr ||
          !Read(access, county, 0x18, row.county_title_id) ||
          !Title(env, access, row.county_title_id, title) ||
          !Read(access, title, 0x128, row.holder_character_id) ||
          !ResolveSourceCharacter(env, access,
              row.holder_character_id, holder)) {
        failure = Failure::identity_round_trip_failed; break;
      }
      if (std::any_of(out.material.candidates.begin(), out.material.candidates.end(),
          [&](const auto &other) { return other.county_title_id == row.county_title_id ||
              other.capital_province_id == row.capital_province_id; })) {
        failure = Failure::candidate_invalid; break;
      }
      row.native_collection_ordinal = static_cast<std::uint32_t>(ordinal);
      row.is_player_capital = province == capital;
      row.directly_held_by_player = row.holder_character_id == frame.played_character_id;
      scopes.target_tag = 8;
      scopes.target = row.capital_province_id;
      std::int64_t growth = 0, decay = 0;
      std::int64_t *returned = nullptr;
      if (!Invoke(env.target_valid, row.native_target_valid, type, steward, province, nullptr) ||
          !Invoke(env.growth, returned, &growth, county, nullptr) || returned != &growth ||
          !Invoke(env.decay, returned, &decay, county, nullptr) || returned != &decay ||
          (decay > 0 && growth > (std::numeric_limits<std::int64_t>::max)() - decay) ||
          (decay < 0 && growth < (std::numeric_limits<std::int64_t>::min)() - decay) ||
          !Progress(env, type, &scopes, row.development_progress_current,
              row.development_progress_maximum)) {
        failure = Failure::fixture_source_failed; break;
      }
      row.monthly_development_rate = {growth + decay, kScale};
      out.material.candidates.push_back(row);
    }
  }
  if (!owned.Finish()) return Failure::fixture_source_failed;
  if (failure != Failure::none) return failure;
  std::sort(out.material.candidates.begin(), out.material.candidates.end(),
      [](const auto &a, const auto &b) {
        return static_cast<std::uint32_t>(a.county_title_id) <
               static_cast<std::uint32_t>(b.county_title_id);
      });
  out.material.candidate_collection_complete = true;
  return Failure::none;
}

Result Unavailable(game::StewardDevelopCountyCandidatesV1 &out,
                   std::uint64_t revision, Failure failure,
                   std::optional<std::int32_t> date = std::nullopt) {
  out = {};
  out.material.emplace();
  out.snapshot_revision = revision;
  out.observed_date_raw = date;
  out.unavailable_reason = failure;
  return Result::unavailable;
}
} // namespace

StewardDevelopCountyEnvironment12003 BindStewardDevelopCounty12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  Environment out{};
  if (module_base == 0 || executable_sha256 != kExecutableSha256) return out;
  out.exact_build_admitted = true;
  out.module_base = module_base;
  out.admitted_executable_sha256 = kExecutableSha256;
  // Existing .3 reviewed reuse proves these .2 core/role/allocator seams.
  out.council = ck3_12002::BindCouncilCandidates12002(module_base, ck3_12002::kExecutableSha256);
  out.game_state_slot = reinterpret_cast<void **>(module_base + 0x5C68C50);
  out.title_storage_slot = reinterpret_cast<void **>(module_base + 0x5D1DAF8);
  out.title_fallback_slot = reinterpret_cast<void **>(module_base + 0x5D1DAE0);
  out.task_type_database_slot = reinterpret_cast<void **>(module_base + 0x5C671D8);
  out.task_type_fallback_slot = reinterpret_cast<void **>(module_base + 0x5D1F900);
  out.hash_key = reinterpret_cast<DevelopHash>(module_base + 0x3F7E240);
  out.lookup_type = reinterpret_cast<DevelopLookup>(module_base + 0xCF1E80);
  out.immediate_liege = reinterpret_cast<DevelopResolver>(module_base + 0x28BFC70);
  out.capital_province = reinterpret_cast<DevelopResolver>(module_base + 0x28B1CD0);
  out.is_human = reinterpret_cast<DevelopHumanCheck>(module_base + 0x2BAA710);
  out.shown = reinterpret_cast<DevelopShown>(module_base + 0x31AC7B0);
  out.valid = reinterpret_cast<DevelopValid>(module_base + 0x31AC680);
  out.target_valid = reinterpret_cast<DevelopTargetValid>(module_base + 0x2C48970);
  out.growth = reinterpret_cast<DevelopGrowth>(module_base + 0x24CF900);
  out.decay = reinterpret_cast<DevelopGrowth>(module_base + 0x24CFB50);
  out.current_progress = reinterpret_cast<DevelopProgress>(module_base + 0x31AB520);
  out.maximum_progress = reinterpret_cast<DevelopProgress>(module_base + 0x31AB840);
  out.produce_targets = reinterpret_cast<DevelopProducer>(module_base + 0x2C48E80);
  return out;
}

game::ReadStewardDevelopCountyCandidatesResultV1 ReadStewardDevelopCounty12003(
    const Environment &env, const Access &access,
    const ck3_11906::StewardDevelopCountyCandidatesRequestV1 &request,
    game::StewardDevelopCountyCandidatesV1 &output) noexcept {
  try {
    if (request.expected_snapshot_revision == 0)
      return Unavailable(output, request.expected_snapshot_revision, Failure::invalid_request);
    if (!Exact(env))
      return Unavailable(output, request.expected_snapshot_revision, Failure::exact_build_not_admitted);
    if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context))
      return Unavailable(output, request.expected_snapshot_revision, Failure::application_main_thread_required);
    Proxy proxy{&env, &access};
    const auto source = SourceAccess(proxy);
    CouncilFrame before{}, after{};
    if (!CaptureSourceFrame(env, source, before))
      return Unavailable(output, request.expected_snapshot_revision, Failure::frame_capture_failed);
    if (before.native_revision != request.expected_snapshot_revision)
      return Unavailable(output, request.expected_snapshot_revision, Failure::snapshot_revision_mismatch);
    if (!before.paused || !before.map_ready || !before.has_played_character ||
        !before.played_character_alive || !before.played_character_identity_round_trip ||
        !before.active_task_identity_round_trip || before.active_task == 0)
      return Unavailable(output, request.expected_snapshot_revision, Failure::paused_player_unavailable, before.date_raw);
    Sample first{}, second{};
    auto failure = ReadSample(env, source, before, first);
    if (failure == Failure::none) failure = ReadSample(env, source, before, second);
    if (!CaptureSourceFrame(env, source, after) ||
        before != after)
      return Unavailable(output, request.expected_snapshot_revision, Failure::same_frame_drift, before.date_raw);
    if (failure != Failure::none)
      return Unavailable(output, request.expected_snapshot_revision, failure, before.date_raw);
    if (first != second)
      return Unavailable(output, request.expected_snapshot_revision, Failure::native_sample_drift, before.date_raw);
    output = {};
    output.status = game::StewardDevelopCountyCandidatesStatusV1::available;
    output.snapshot_revision = request.expected_snapshot_revision;
    output.observed_date_raw = before.date_raw;
    output.player_character_id = before.played_character_id;
    output.steward_character_id = first.material.current_active_task_binding->incumbent_character_id;
    output.shown = first.shown;
    output.valid = first.valid;
    if (!first.shown) output.task_failure_reason = "task_not_shown";
    else if (!first.valid) output.task_failure_reason = "task_invalid";
    output.material = std::move(first.material);
    output.same_frame_stable = true;
    output.readiness.ready = true;
    return Result::available;
  } catch (...) {
    try { return Unavailable(output, request.expected_snapshot_revision, Failure::reader_exception); }
    catch (...) { return Result::unavailable; }
  }
}
} // namespace xar::ck3_12003
