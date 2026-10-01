#include "xar_bridge/activity_feast_guest_rule_toggle_v1.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"

#if defined(_WIN32)
#include <windows.h>
#endif

#include <array>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

constexpr std::uintptr_t kPlayedIdRva = 0x4FE7EE0;
constexpr std::uintptr_t kDatabaseSlotRva = 0x57D35F8;
constexpr std::uintptr_t kMissingRuleSlotRva = 0x57D3618;
constexpr std::uintptr_t kDatabaseVtableRva = 0x4400678;
constexpr std::uintptr_t kDatabaseSubVtableRva = 0x4400660;
constexpr std::uintptr_t kFeastTypeVtableRva = 0x440E308;
constexpr std::uintptr_t kWindowVtableRva = 0x41676E8;
constexpr std::size_t kMaxRules = 64;
constexpr std::size_t kMaxGroups = 64;
constexpr std::size_t kMaxCharacters = 4096;

// 1.20 addresses are recovered independently from RTTI, the string-key
// resolver, its DB lookup, and the native window toggle/getter callers.
std::uintptr_t RuleRva(const ActivityPlannerDiagEnvironmentV1 &env,
                       std::uintptr_t legacy) noexcept {
  if (!IsActivityPlanner12002V1(env)) return legacy;
  switch (legacy) {
  case 0x4FE7EE0: return 0x54DBC00;
  case 0x57D35F8: return 0x5D33EE8;
  case 0x57D3618: return 0x5D33F48;
  case 0x4400678: return 0x48B2F20;
  case 0x4400660: return 0x48B2EC0;
  case 0x440E308: return 0x48BFE50;
  case 0x41676E8: return 0x457B1A0;
  case 0x3B8B000: return 0x3F7E240;
  case 0x2C19210: return 0x3057BC0;
  case 0x2C1B800: return 0x305A280;
  case 0x151C110: return 0x165A9D0;
  case 0x151C2B0: return 0x165AB90;
  default: return legacy;
  }
}
std::size_t RulePlannerOffset(const ActivityPlannerDiagEnvironmentV1 &env,
                             std::size_t legacy) noexcept {
  if (!IsActivityPlanner12002V1(env)) return legacy;
  switch (legacy) {
  case 0xD0: return 0xA0;
  case 0x1538: return 0x1508;
  case 0x1A18: return 0x1A50;
  case 0x1A24: return 0x1A5C;
  case 0x1590: return 0x15C8;
  case 0x159C: return 0x15D4;
  default: return legacy;
  }
}
std::size_t RuleWindowOffset(const ActivityPlannerDiagEnvironmentV1 &env,
                            std::size_t legacy) noexcept {
  return IsActivityPlanner12002V1(env) ?
      (legacy == 0x100 ? 0xD0 : legacy == 0xF8 ? 0xC8 : legacy) : legacy;
}
std::size_t RuleTypeOffset(const ActivityPlannerDiagEnvironmentV1 &env,
                          std::size_t legacy) noexcept {
  return IsActivityPlanner12002V1(env) ?
      (legacy == 0xD20 ? 0xBC8 : legacy == 0xD2C ? 0xBD4 : legacy) : legacy;
}

template <typename T>
bool Read(const ActivityPlannerDiagEnvironmentV1 &source,
          std::uintptr_t address, T &value) noexcept {
  return source.read_memory != nullptr && address != 0 &&
         source.read_memory(source.context, address, &value, sizeof(value));
}

template <typename T>
bool ReadAt(const ActivityPlannerDiagEnvironmentV1 &source,
            std::uintptr_t base, std::size_t offset, T &value) noexcept {
  return base != 0 &&
         offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
         Read(source, base + offset, value);
}

template <std::size_t N>
bool BytesAt(const ActivityPlannerDiagEnvironmentV1 &source,
             std::uintptr_t rva,
             const std::array<std::uint8_t, N> &expected) noexcept {
  std::array<std::uint8_t, N> actual{};
  return source.module_base != 0 &&
         rva <= (std::numeric_limits<std::uintptr_t>::max)() -
                    source.module_base &&
         source.read_memory != nullptr &&
         source.read_memory(source.context, source.module_base + RuleRva(source, rva),
                            actual.data(), actual.size()) &&
         actual == expected;
}

bool Abi(const ActivityFeastGuestRuleEnvironmentV1 &env) noexcept {
  const auto &source = env.diagnostic;
  const bool modern = IsActivityPlanner12002V1(source);
  if (!env.enabled || !source.enabled || source.module_base == 0 ||
      !IsActivityPlannerSupportedBuildV1(source) ||
      source.read_memory == nullptr ||
      (env.capture == nullptr &&
       (env.passive_cost == nullptr ||
        env.passive_cost->environment.module_base != source.module_base ||
        env.passive_cost->environment.executable_sha256 !=
            source.admitted_executable_sha256))) return false;
  return BytesAt(source, 0x3B8B000,
      std::array<std::uint8_t, 8>{0x89,0x4C,0x24,0x08,0x53,0x48,0x83,0xEC}) &&
      BytesAt(source, 0x2C19210,
      std::array<std::uint8_t, 8>{0x48,0x83,0xEC,0x38,0x48,0x8B,0x05,
          static_cast<std::uint8_t>(modern ? 0x1D : 0xDD)}) &&
      BytesAt(source, 0x2C1B800,
      std::array<std::uint8_t, 8>{0x48,0x89,0x5C,0x24,0x08,0x45,0x33,0xC0}) &&
      BytesAt(source, 0x151C110,
      std::array<std::uint8_t, 8>{0x40,0x57,0x41,
          static_cast<std::uint8_t>(modern ? 0x55 : 0x57),0x48,0x83,0xEC,
          static_cast<std::uint8_t>(modern ? 0x38 : 0x28)}) &&
      BytesAt(source, 0x151C2B0,
      std::array<std::uint8_t, 8>{0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x74});
}

bool AuthoredKey(std::string_view key) noexcept {
  constexpr std::string_view prefix = "activity_invite_rule_";
  if (!key.starts_with(prefix) || key.size() <= prefix.size() ||
      key.size() > 95)
    return false;
  for (const char c : key)
    if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_'))
      return false;
  return true;
}

bool FeastType(const ActivityPlannerDiagEnvironmentV1 &source,
               std::uintptr_t type) noexcept {
  constexpr char key[] = "activity_feast";
  std::uintptr_t vtable = 0, data = type + 0x18;
  std::uint64_t size = 0, capacity = 0;
  if (!ReadAt(source, type, 0, vtable) ||
      vtable != source.module_base + RuleRva(source, kFeastTypeVtableRva) ||
      !ReadAt(source, type, 0x28, size) ||
      !ReadAt(source, type, 0x30, capacity) ||
      size != sizeof(key) - 1 || size > capacity ||
      (capacity > 15 && !ReadAt(source, type, 0x18, data)))
    return false;
  std::array<char, sizeof(key) - 1> actual{};
  return source.read_memory(source.context, data, actual.data(),
                            actual.size()) &&
         std::memcmp(actual.data(), key, actual.size()) == 0;
}

ActivityPlannerDiagResultV1 Diag(
    const ActivityFeastGuestRuleEnvironmentV1 &env,
    const ActivityPlannerDiagFrameV1 &expected) noexcept {
  return env.read_diagnostic != nullptr
             ? env.read_diagnostic(env.context, expected)
             : ReadActivityPlannerDiagV1(env.diagnostic, expected);
}

bool Capture(const ActivityFeastGuestRuleEnvironmentV1 &env,
             const ActivityPlannerDiagFrameV1 &expected,
             ActivityCostSlot12CaptureV1 &capture) noexcept {
  if (env.capture != nullptr)
    return env.capture(env.context, expected, capture);
#if defined(_WIN32)
  if (env.passive_cost == nullptr ||
      expected.date_raw < (std::numeric_limits<std::int32_t>::min)() ||
      expected.date_raw > (std::numeric_limits<std::int32_t>::max)())
    return false;
  return ReadActivityCostSlot12PassiveV1(
             *env.passive_cost,
             {static_cast<std::int32_t>(expected.date_raw),
              expected.actor_character_id, GetCurrentThreadId(), true},
             capture) == ActivityCostSlot12ReadStatusV1::observed;
#else
  (void)expected;
  (void)capture;
  return false;
#endif
}

std::uint32_t NativeHash(void *, std::uintptr_t base,
                         std::string_view key) noexcept {
#if defined(_WIN32)
  using Hash = std::uint32_t(__fastcall *)(void *, const char *, std::uint32_t);
  return reinterpret_cast<Hash>(base + 0x3B8B000)(
      nullptr, key.data(), static_cast<std::uint32_t>(key.size()));
#else
  (void)base;
  (void)key;
  return 0;
#endif
}

std::uint32_t NativeHash12002(void *, std::uintptr_t base,
                         std::string_view key) noexcept {
#if defined(_WIN32)
  using Hash = std::uint32_t(__fastcall *)(void *, const char *, std::uint32_t);
  return reinterpret_cast<Hash>(base + 0x3F7E240)(
      nullptr, key.data(), static_cast<std::uint32_t>(key.size()));
#else
  (void)base;
  (void)key;
  return 0;
#endif
}

std::uintptr_t NativeLookup(void *, std::uintptr_t base,
                            std::uint32_t hash) noexcept {
#if defined(_WIN32)
  using GetDatabase = void *(__fastcall *)();
  using Lookup = void *(__fastcall *)(void *, std::uint32_t);
  auto *database = reinterpret_cast<GetDatabase>(base + 0x2C19210)();
  return database == nullptr
             ? 0
             : reinterpret_cast<std::uintptr_t>(
                   reinterpret_cast<Lookup>(base + 0x2C1B800)(database, hash));
#else
  (void)base;
  (void)hash;
  return 0;
#endif
}

std::uintptr_t NativeLookup12002(void *, std::uintptr_t base,
                            std::uint32_t hash) noexcept {
#if defined(_WIN32)
  using GetDatabase = void *(__fastcall *)();
  using Lookup = void *(__fastcall *)(void *, std::uint32_t);
  auto *database = reinterpret_cast<GetDatabase>(base + 0x3057BC0)();
  return database == nullptr
             ? 0
             : reinterpret_cast<std::uintptr_t>(
                   reinterpret_cast<Lookup>(base + 0x305A280)(database, hash));
#else
  (void)base;
  (void)hash;
  return 0;
#endif
}

bool NativeActive(void *, std::uintptr_t base, std::uintptr_t window,
                  std::uintptr_t row, bool &active) noexcept {
#if defined(_WIN32)
  using Getter = bool(__fastcall *)(void *, void *);
  active = reinterpret_cast<Getter>(base + 0x151C2B0)(
      reinterpret_cast<void *>(window), reinterpret_cast<void *>(row));
  return true;
#else
  (void)base;
  (void)window;
  (void)row;
  (void)active;
  return false;
#endif
}

bool NativeActive12002(void *, std::uintptr_t base, std::uintptr_t window,
                  std::uintptr_t row, bool &active) noexcept {
#if defined(_WIN32)
  using Getter = bool(__fastcall *)(void *, void *);
  active = reinterpret_cast<Getter>(base + 0x165AB90)(
      reinterpret_cast<void *>(window), reinterpret_cast<void *>(row));
  return true;
#else
  (void)base;
  (void)window;
  (void)row;
  (void)active;
  return false;
#endif
}

bool NativeToggle(void *, std::uintptr_t base, std::uintptr_t window,
                  std::uintptr_t row) noexcept {
#if defined(_WIN32)
  using Toggle = void(__fastcall *)(void *, void *);
  reinterpret_cast<Toggle>(base + 0x151C110)(
      reinterpret_cast<void *>(window), reinterpret_cast<void *>(row));
  return true;
#else
  (void)base;
  (void)window;
  (void)row;
  return false;
#endif
}

bool NativeToggle12002(void *, std::uintptr_t base, std::uintptr_t window,
                  std::uintptr_t row) noexcept {
#if defined(_WIN32)
  using Toggle = void(__fastcall *)(void *, void *);
  reinterpret_cast<Toggle>(base + 0x165A9D0)(
      reinterpret_cast<void *>(window), reinterpret_cast<void *>(row));
  return true;
#else
  (void)base;
  (void)window;
  (void)row;
  return false;
#endif
}

struct Binding {
  ActivityCostSlot12CaptureV1 capture{};
  std::uintptr_t window = 0;
  std::uintptr_t row = 0;
  std::uintptr_t definition = 0;
  std::uint32_t hash = 0;
  std::int32_t ordered_count = 0;
};

ActivityFeastGuestRuleStatusV1 Bind(
    const ActivityFeastGuestRuleEnvironmentV1 &env,
    const ActivityPlannerDiagFrameV1 &expected, std::string_view key,
    bool require_window, Binding &binding) noexcept {
  const auto &source = env.diagnostic;
  const auto diag = Diag(env, expected);
  if (diag.status != ActivityPlannerDiagStatusV1::observed ||
      !diag.value.planner_present || diag.value.stage != 5 ||
      !diag.value.widget_attached ||
      (diag.value.host_view_activity_key_known &&
       std::string_view(diag.value.host_view_activity_key.data(),
                        diag.value.host_view_activity_key_size) !=
           "activity_feast"))
    return ActivityFeastGuestRuleStatusV1::planner_unavailable;
  if (!Capture(env, expected, binding.capture) ||
      binding.capture.frame.date_raw != expected.date_raw ||
      binding.capture.frame.actor_character_id != expected.actor_character_id ||
      binding.capture.planning_stage != 5 || binding.capture.planner == 0 ||
      binding.capture.owner == 0 ||
      !FeastType(source, binding.capture.activity_type))
    return ActivityFeastGuestRuleStatusV1::planner_unavailable;
  std::uintptr_t planner = 0, owner = 0;
  std::int32_t host_id = 0;
  std::uint32_t played_id = 0;
  if (!ReadAt(source, binding.capture.owner, 0x3C0, planner) ||
      !ReadAt(source, binding.capture.planner, RulePlannerOffset(source, 0xD0), owner) ||
      !ReadAt(source, binding.capture.planner, RulePlannerOffset(source, 0x1538), host_id) ||
      !ReadAt(source, source.module_base, RuleRva(source, kPlayedIdRva), played_id) ||
      planner != binding.capture.planner || owner != binding.capture.owner ||
      host_id != expected.actor_character_id ||
      played_id != static_cast<std::uint32_t>(expected.actor_character_id))
    return ActivityFeastGuestRuleStatusV1::planner_unavailable;
  // The planner's active-rule vector drives guest filtering even before the
  // separate guest-list view binds. Only the native toggle needs that view.
  if (require_window) {
    std::uintptr_t window = 0, vtable = 0, bound = 0;
    std::int32_t mode = 0;
    if (!ReadAt(source, binding.capture.owner, 0x3F0, window) ||
        window == 0 || !ReadAt(source, window, 0, vtable) ||
        !ReadAt(source, window, RuleWindowOffset(source, 0x100), bound) ||
        !ReadAt(source, window, RuleWindowOffset(source, 0xF8), mode) ||
        vtable != source.module_base + RuleRva(source, kWindowVtableRva) ||
        bound != binding.capture.planner || mode != -1)
      return ActivityFeastGuestRuleStatusV1::window_unbound;
    binding.window = window;
  }
  std::uintptr_t database = 0, database_vtable = 0, sub_vtable = 0;
  std::uintptr_t missing = 0;
  if (!ReadAt(source, source.module_base, RuleRva(source, kDatabaseSlotRva), database) ||
      database == 0 || !ReadAt(source, database, 0, database_vtable) ||
      !ReadAt(source, database, 0x38, sub_vtable) ||
      !ReadAt(source, source.module_base, RuleRva(source, kMissingRuleSlotRva), missing) ||
      database_vtable != source.module_base + RuleRva(source, kDatabaseVtableRva) ||
      sub_vtable != source.module_base + RuleRva(source, kDatabaseSubVtableRva) || missing == 0)
    return ActivityFeastGuestRuleStatusV1::rule_unavailable;
  const auto hash = env.hash_key != nullptr ? env.hash_key : (IsActivityPlanner12002V1(env.diagnostic) ? &NativeHash12002 : &NativeHash);
  const auto lookup = env.lookup_rule != nullptr ? env.lookup_rule : (IsActivityPlanner12002V1(env.diagnostic) ? &NativeLookup12002 : &NativeLookup);
  binding.hash = hash(env.context, source.module_base, key);
  binding.definition = lookup(env.context, source.module_base, binding.hash);
  if (binding.definition == 0 || binding.definition == missing)
    return ActivityFeastGuestRuleStatusV1::rule_unavailable;
  std::uintptr_t rows = 0;
  if (!ReadAt(source, binding.capture.activity_type, RuleTypeOffset(source, 0xD20), rows) ||
      !ReadAt(source, binding.capture.activity_type, RuleTypeOffset(source, 0xD2C),
              binding.ordered_count) ||
      binding.ordered_count < 0 ||
      binding.ordered_count > static_cast<std::int32_t>(kMaxRules) ||
      (binding.ordered_count != 0 && rows == 0))
    return ActivityFeastGuestRuleStatusV1::native_read_failed;
  for (std::int32_t i = 0; i < binding.ordered_count; ++i) {
    std::uintptr_t definition = 0;
    const auto row = rows + static_cast<std::size_t>(i) * 16;
    if (!ReadAt(source, row, 0, definition))
      return ActivityFeastGuestRuleStatusV1::native_read_failed;
    if (definition != binding.definition) continue;
    if (binding.row != 0)
      return ActivityFeastGuestRuleStatusV1::ambiguous_rule;
    binding.row = row;
  }
  return binding.row != 0 ? ActivityFeastGuestRuleStatusV1::observed_inactive
                          : ActivityFeastGuestRuleStatusV1::rule_unavailable;
}

ActivityFeastGuestRuleStatusV1 Observe(
    const ActivityFeastGuestRuleEnvironmentV1 &env,
    const ActivityPlannerDiagFrameV1 &expected, const Binding &binding,
    ActivityFeastGuestRuleResultV1 &result) noexcept {
  const auto &source = env.diagnostic;
  std::uintptr_t bound = 0, planner = 0, active_rows = 0, groups = 0;
  std::int32_t mode = 0, active_count = 0, group_count = 0;
  if (!ReadAt(source, binding.capture.owner, 0x3C0, planner) ||
      planner != binding.capture.planner ||
      !ReadAt(source, binding.capture.planner, RulePlannerOffset(source, 0x1A18), active_rows) ||
      !ReadAt(source, binding.capture.planner, RulePlannerOffset(source, 0x1A24), active_count) ||
      !ReadAt(source, binding.capture.planner, RulePlannerOffset(source, 0x1590), groups) ||
      !ReadAt(source, binding.capture.planner, RulePlannerOffset(source, 0x159C), group_count) ||
      active_count < 0 || active_count > static_cast<std::int32_t>(kMaxRules) ||
      group_count < 0 || group_count > static_cast<std::int32_t>(kMaxGroups) ||
      (active_count != 0 && active_rows == 0) ||
      (group_count != 0 && groups == 0))
    return ActivityFeastGuestRuleStatusV1::native_read_failed;
  bool vector_active = false;
  for (std::int32_t i = 0; i < active_count; ++i) {
    std::uintptr_t definition = 0;
    if (!ReadAt(source, active_rows, static_cast<std::size_t>(i) * 16,
                definition))
      return ActivityFeastGuestRuleStatusV1::native_read_failed;
    if (definition == binding.definition) vector_active = true;
  }
  if (binding.window != 0) {
    if (!ReadAt(source, binding.window, RuleWindowOffset(source, 0x100), bound) ||
        !ReadAt(source, binding.window, RuleWindowOffset(source, 0xF8), mode) ||
        bound != binding.capture.planner || mode != -1)
      return ActivityFeastGuestRuleStatusV1::window_unbound;
    const auto active =
        env.read_active != nullptr ? env.read_active : (IsActivityPlanner12002V1(env.diagnostic) ? &NativeActive12002 : &NativeActive);
    bool getter_active = false;
    if (!active(env.context, source.module_base, binding.window, binding.row,
                getter_active))
      return ActivityFeastGuestRuleStatusV1::native_read_failed;
    // A bound window supplies a second source, particularly after a toggle.
    if (getter_active != vector_active)
      return ActivityFeastGuestRuleStatusV1::postcondition_failed;
  }
  std::size_t character_count = 0;
  for (std::int32_t i = 0; i < group_count; ++i) {
    std::uintptr_t ids = 0;
    std::int32_t count = 0;
    const auto group = groups + static_cast<std::size_t>(i) * 0x18;
    if (!ReadAt(source, group, 0, ids) || !ReadAt(source, group, 0x0C, count) ||
        count < 0 || (count != 0 && ids == 0) ||
        character_count + static_cast<std::size_t>(count) > kMaxCharacters)
      return ActivityFeastGuestRuleStatusV1::native_read_failed;
    character_count += static_cast<std::size_t>(count);
  }
  ActivityPlannerDiagFrameV1 current{};
  if (source.read_frame == nullptr ||
      !source.read_frame(source.context, current) || current != expected)
    return ActivityFeastGuestRuleStatusV1::frame_changed;
  result.active = vector_active;
  result.active_rule_count = active_count;
  result.filtered_group_count = group_count;
  result.filtered_character_count = static_cast<std::int32_t>(character_count);
  return vector_active ? ActivityFeastGuestRuleStatusV1::observed_active
                       : ActivityFeastGuestRuleStatusV1::observed_inactive;
}

ActivityFeastGuestRuleResultV1 Run(
    const ActivityFeastGuestRuleEnvironmentV1 &env,
    const ActivityPlannerDiagFrameV1 &expected, std::string_view key,
    bool activate, bool policy_approved) noexcept {
  ActivityFeastGuestRuleResultV1 result{};
  result.frame = expected;
  if (!Abi(env)) return result;
  if (expected.revision == 0 || expected.actor_character_id <= 0 ||
      !expected.application_main_thread || !expected.paused ||
      !expected.map_ready || !expected.actor_alive) {
    result.status = ActivityFeastGuestRuleStatusV1::frame_changed;
    return result;
  }
  if (!AuthoredKey(key)) {
    result.status = ActivityFeastGuestRuleStatusV1::rule_unavailable;
    return result;
  }
  Binding binding{};
  result.status = Bind(env, expected, key, activate, binding);
  if (result.status != ActivityFeastGuestRuleStatusV1::observed_inactive)
    return result;
  result.native_key_hash = binding.hash;
  result.ordered_rule_count = binding.ordered_count;
  result.status = Observe(env, expected, binding, result);
  if (!activate || !policy_approved ||
      result.status != ActivityFeastGuestRuleStatusV1::observed_inactive)
    return result;
  const auto invoke = env.toggle != nullptr ? env.toggle : (IsActivityPlanner12002V1(env.diagnostic) ? &NativeToggle12002 : &NativeToggle);
  result.invoked = true;
  if (!invoke(env.context, env.diagnostic.module_base, binding.window,
              binding.row)) {
    result.status = ActivityFeastGuestRuleStatusV1::native_action_failed;
    return result;
  }
  // The native callback has returned. Read the independent active getter,
  // copied planner rules and filtered groups again on the paused frame.
  result.status = Observe(env, expected, binding, result);
  if (result.status == ActivityFeastGuestRuleStatusV1::observed_active)
    result.status = ActivityFeastGuestRuleStatusV1::activated;
  else if (result.status == ActivityFeastGuestRuleStatusV1::observed_inactive)
    result.status = ActivityFeastGuestRuleStatusV1::postcondition_failed;
  return result;
}

} // namespace

ActivityFeastGuestRuleResultV1 ReadActivityFeastGuestRuleV1(
    const ActivityFeastGuestRuleEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    std::string_view authored_rule_key) noexcept {
  return Run(environment, expected, authored_rule_key, false, false);
}

ActivityFeastGuestRuleResultV1 ActivateActivityFeastGuestRuleV1(
    const ActivityFeastGuestRuleEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    std::string_view authored_rule_key, bool policy_approved) noexcept {
  return Run(environment, expected, authored_rule_key, true, policy_approved);
}

std::string_view ActivityFeastGuestRuleStatusKeyV1(
    ActivityFeastGuestRuleStatusV1 status) noexcept {
  switch (status) {
  case ActivityFeastGuestRuleStatusV1::observed_inactive: return "observed_inactive";
  case ActivityFeastGuestRuleStatusV1::observed_active: return "observed_active";
  case ActivityFeastGuestRuleStatusV1::activated: return "activated";
  case ActivityFeastGuestRuleStatusV1::exact_build_rejected: return "exact_build_rejected";
  case ActivityFeastGuestRuleStatusV1::frame_changed: return "frame_changed";
  case ActivityFeastGuestRuleStatusV1::planner_unavailable: return "planner_unavailable";
  case ActivityFeastGuestRuleStatusV1::window_unbound: return "window_unbound";
  case ActivityFeastGuestRuleStatusV1::rule_unavailable: return "rule_unavailable";
  case ActivityFeastGuestRuleStatusV1::ambiguous_rule: return "ambiguous_rule";
  case ActivityFeastGuestRuleStatusV1::native_read_failed: return "native_read_failed";
  case ActivityFeastGuestRuleStatusV1::native_action_failed: return "native_action_failed";
  case ActivityFeastGuestRuleStatusV1::postcondition_failed: return "postcondition_failed";
  }
  return "unknown";
}

} // namespace xar::bridge
