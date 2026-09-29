#include "xar_bridge/actor_army_role_private_v1.hpp"

#include "xar_bridge/prewar_scope_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <atomic>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <string>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kCharacterStorageSlotRva = 0x570C130;
constexpr std::uintptr_t kRegimentStorageSlotRva = 0x57BF4C8;
constexpr std::uintptr_t kGetArmyCommanderRva = 0x2278F70;
constexpr std::size_t kMaximumRegiments = 4096;

template <typename T>
bool ReadAt(const void *base, std::size_t offset, T &out) noexcept {
  if (base == nullptr ||
      reinterpret_cast<std::uintptr_t>(base) >
          std::numeric_limits<std::uintptr_t>::max() - offset) {
    return false;
  }
  SIZE_T read = 0;
  const auto *const address = reinterpret_cast<const void *>(
      reinterpret_cast<std::uintptr_t>(base) + offset);
  return ReadProcessMemory(GetCurrentProcess(), address, &out, sizeof(T),
                           &read) != FALSE &&
         read == sizeof(T);
}

bool ReadStored(void *const *storage_slot, std::int32_t id,
                std::size_t id_offset, void *&out) noexcept {
  out = nullptr;
  if (storage_slot == nullptr || id <= 0) return false;
  void *storage = nullptr;
  if (!ReadAt(storage_slot, 0, storage) || storage == nullptr) return false;
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadAt(storage, 0x20, slots) || !ReadAt(storage, 0x2C, capacity) ||
      slots == nullptr || capacity <= 0 ||
      capacity > static_cast<std::int32_t>(
                     kPrewarScopeV1MaximumComponentCapacity)) {
    return false;
  }
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return false;
  void *component = nullptr;
  if (!ReadAt(slots, static_cast<std::size_t>(index) * 0x10 + 0x08,
              component) ||
      component == nullptr) {
    return false;
  }
  std::int32_t observed_id = -1;
  if (!ReadAt(component, id_offset, observed_id) || observed_id != id) {
    return false;
  }
  out = component;
  return true;
}

bool CanonicalPositive(std::string_view token, std::int32_t &out) noexcept {
  out = -1;
  if (token.empty() || token.front() == '0' || token.size() > 10) {
    return false;
  }
  for (const char ch : token) {
    if (ch < '0' || ch > '9') return false;
  }
  const auto [end, error] =
      std::from_chars(token.data(), token.data() + token.size(), out);
  return error == std::errc{} && end == token.data() + token.size() &&
         out > 0;
}

bool OwnsPausedSlot(const ActorArmyRolePrivateQueryV1 &query,
                    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      stamp.game_state == 0 || stamp.jomini_state == 0 ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *query.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             query.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor == &ExecuteActorArmyRolePrivateQueryV1 &&
         mailbox.executor_context == &query;
}

bool SameFrame(const ActorArmyRolePrivateQueryV1 &query,
               const MainThreadExecutionStampV1 &stamp) {
  game::Snapshot snapshot{};
  return OwnsPausedSlot(query, stamp) && query.game != nullptr &&
         game::ReadSnapshot(*query.game, snapshot) &&
         snapshot == query.expected_snapshot && snapshot.paused &&
         snapshot.map_ready && snapshot.has_played_character &&
         snapshot.played_character_alive &&
         snapshot.played_character_id == query.actor_character_id &&
         snapshot.date_raw == stamp.date_raw;
}

const game::ArmySnapshot *FindOnePublicArmy(
    const game::Snapshot &snapshot, std::int32_t army_id) noexcept {
  const game::ArmySnapshot *found = nullptr;
  for (const auto &row : snapshot.player_armies) {
    if (row.army_id == army_id) {
      if (found != nullptr) return nullptr;
      found = &row;
    }
  }
  return found;
}

void ReadRole(const ActorArmyRolePrivateQueryV1 &query,
              ActorArmyRoleResultV1 &result) {
  result.native_revision = query.expected_revision;
  result.date_raw = query.expected_snapshot.date_raw;
  result.actor_character_id = query.actor_character_id;
  result.public_army_id = query.public_army_id;
  const auto *const public_army =
      FindOnePublicArmy(query.expected_snapshot, query.public_army_id);
  if (public_army == nullptr ||
      public_army->owner_character_id != query.actor_character_id) {
    result.unavailable_stage = "public_actor_army_missing_or_ambiguous";
    return;
  }
  if (query.module_base == 0) {
    result.unavailable_stage = "module_unavailable";
    return;
  }
  auto *const unit_slot = reinterpret_cast<void *const *>(
      query.module_base + kPrewarScopeV1UnitStorageSlotRva);
  auto *const army_slot = reinterpret_cast<void *const *>(
      query.module_base + kPrewarScopeV1ArmyStorageSlotRva);
  auto *const character_slot = reinterpret_cast<void *const *>(
      query.module_base + kCharacterStorageSlotRva);
  auto *const regiment_slot = reinterpret_cast<void *const *>(
      query.module_base + kRegimentStorageSlotRva);
  void *actor = nullptr;
  void *unit = nullptr;
  if (!ReadStored(character_slot, query.actor_character_id, 0x18, actor) ||
      !ReadStored(unit_slot, query.public_army_id, 0x10, unit)) {
    result.unavailable_stage = "actor_or_public_unit_identity";
    return;
  }
  std::int32_t owner_id = -1;
  std::int32_t native_carmy_id = -1;
  if (!ReadAt(unit, 0x174, owner_id) ||
      !ReadAt(unit, 0x178, native_carmy_id) ||
      owner_id != query.actor_character_id || native_carmy_id <= 0) {
    result.unavailable_stage = "unit_owner_or_carmy_identity";
    return;
  }
  void *army = nullptr;
  std::int32_t reverse_unit_id = -1;
  if (!ReadStored(army_slot, native_carmy_id, 0x10, army) ||
      !ReadAt(army, 0x124, reverse_unit_id) ||
      reverse_unit_id != query.public_army_id) {
    result.unavailable_stage = "carmy_identity_or_unit_backlink";
    return;
  }
  if (public_army->has_current_province) {
    void *province = nullptr;
    std::int32_t province_id = -1;
    if (!ReadAt(unit, 0x20, province) || province == nullptr ||
        !ReadAt(province, 0x10, province_id) ||
        province_id != public_army->current_province_id) {
      result.unavailable_stage = "current_province_public_native_drift";
      return;
    }
    result.current_province_id = province_id;
  }
  result.native_carmy_id = native_carmy_id;
  result.owner_character_id = owner_id;
  result.army_state = public_army->army_state;
  result.in_combat = public_army->in_combat;
  result.retreating = public_army->retreating;

  std::int32_t commander_id = -1;
  if (ReadAt(army, 0x120, commander_id)) {
    if (commander_id == -1) {
      result.commander_status = "absent";
      result.is_commander_of_requested_army = false;
    } else if (commander_id > 0) {
      void *commander = nullptr;
      using GetArmyCommander = void *(*)(void *);
      auto *const get_commander = reinterpret_cast<GetArmyCommander>(
          query.module_base + kGetArmyCommanderRva);
      if (ReadStored(character_slot, commander_id, 0x18, commander) &&
          get_commander(army) == commander) {
        result.commander_status = "available";
        result.commander_character_id = commander_id;
        result.is_commander_of_requested_army =
            commander_id == query.actor_character_id;
      }
    }
  }

  void *regiment_ids = nullptr;
  std::int32_t count = -1;
  std::int32_t capacity = -1;
  if (!ReadAt(army, 0x38, regiment_ids) ||
      !ReadAt(army, 0x40, capacity) || !ReadAt(army, 0x44, count) ||
      count < 0 || capacity < 0 || count > capacity ||
      count > static_cast<std::int32_t>(kMaximumRegiments) ||
      (count > 0 && regiment_ids == nullptr)) {
    result.unavailable_stage = "regiment_array_shape";
    result.status = "partial";
    result.knight_regiment_id.reset();
    return;
  }
  bool actor_is_knight = false;
  for (std::int32_t index = 0; index < count; ++index) {
    std::int32_t regiment_id = -1;
    if (!ReadAt(regiment_ids, static_cast<std::size_t>(index) * 4,
                regiment_id) ||
        regiment_id <= 0) {
      result.unavailable_stage = "regiment_id_unavailable";
      result.status = "partial";
      result.knight_regiment_id.reset();
      return;
    }
    void *regiment = nullptr;
    std::int32_t regiment_army_id = -1;
    std::int32_t knight_id = -1;
    if (!ReadStored(regiment_slot, regiment_id, 0x10, regiment) ||
        !ReadAt(regiment, 0x140, regiment_army_id) ||
        !ReadAt(regiment, 0x148, knight_id) ||
        regiment_army_id != native_carmy_id || knight_id < -1) {
      result.unavailable_stage = "regiment_army_or_knight_identity";
      result.status = "partial";
      result.knight_regiment_id.reset();
      return;
    }
    if (knight_id == -1) continue;
    void *knight = nullptr;
    void *knight_link = nullptr;
    std::int32_t reverse_regiment_id = -1;
    if (!ReadStored(character_slot, knight_id, 0x18, knight) ||
        !ReadAt(knight, 0x1B0, knight_link) || knight_link == nullptr ||
        !ReadAt(knight_link, 0xF8, reverse_regiment_id) ||
        reverse_regiment_id != regiment_id) {
      result.unavailable_stage = "knight_reverse_membership";
      result.status = "partial";
      result.knight_regiment_id.reset();
      return;
    }
    if (knight_id == query.actor_character_id) {
      if (actor_is_knight) {
        result.unavailable_stage = "actor_duplicate_knight_regiments";
        result.status = "partial";
        result.knight_regiment_id.reset();
        return;
      }
      actor_is_knight = true;
      result.knight_regiment_id = regiment_id;
    }
  }
  result.knight_status = actor_is_knight ? "available" : "absent";
  result.is_knight_in_requested_army = actor_is_knight;
  result.status = result.is_commander_of_requested_army.has_value()
                      ? "available"
                      : "partial";
  result.unavailable_stage =
      result.status == "available" ? "" : "commander_unavailable";
}

void AppendString(std::string &out, std::string_view value) {
  out.push_back('"');
  constexpr char hex[] = "0123456789abcdef";
  for (unsigned char ch : value) {
    if (ch == '"' || ch == '\\') {
      out.push_back('\\');
      out.push_back(static_cast<char>(ch));
    } else if (ch < 0x20) {
      out += "\\u00";
      out.push_back(hex[ch >> 4]);
      out.push_back(hex[ch & 0x0F]);
    } else {
      out.push_back(static_cast<char>(ch));
    }
  }
  out.push_back('"');
}

template <typename T>
void AppendOptionalNumber(std::string &out, const std::optional<T> &value) {
  out += value ? std::to_string(*value) : "null";
}

void AppendOptionalBool(std::string &out, const std::optional<bool> &value) {
  out += value ? (*value ? "true" : "false") : "null";
}

} // namespace

bool ParseActorArmyRolePrivateStepV1(std::string_view step,
                                    std::int32_t &actor_character_id,
                                    std::int32_t &public_army_id) noexcept {
  actor_character_id = -1;
  public_army_id = -1;
  if (!step.starts_with(kActorArmyRolePrivateStepPrefixV1)) return false;
  const auto suffix = step.substr(kActorArmyRolePrivateStepPrefixV1.size());
  const auto separator = suffix.find('-');
  return separator != std::string_view::npos &&
         suffix.find('-', separator + 1) == std::string_view::npos &&
         CanonicalPositive(suffix.substr(0, separator), actor_character_id) &&
         CanonicalPositive(suffix.substr(separator + 1), public_army_id);
}

bool ExecuteActorArmyRolePrivateQueryV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query = static_cast<ActorArmyRolePrivateQueryV1 *>(opaque);
  if (query == nullptr) return false;
  if (!OwnsPausedSlot(*query, stamp) || query->executor_invocations != 0 ||
      query->expected_revision == 0 || query->actor_character_id <= 0 ||
      query->public_army_id <= 0 || query->module_base == 0) {
    query->failure_stage = "application_main_admission";
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    if (!SameFrame(*query, stamp)) {
      query->failure_stage = "public_frame_drift";
      return true;
    }
    ReadRole(*query, query->result);
    if (!SameFrame(*query, stamp)) {
      query->result = {};
      query->failure_stage = "postread_public_frame_drift";
      return true;
    }
    query->completed = true;
    return true;
  } catch (...) {
    query->result = {};
    query->failure_stage = "private_query_exception";
    return true;
  }
}

std::string SerializeActorArmyRolePrivateResultV1(
    const ActorArmyRoleResultV1 &row) {
  if (row.native_revision == 0 || row.actor_character_id <= 0 ||
      row.public_army_id <= 0) return {};
  std::string out = "{\"schema\":\"xar.war.actor-army-role-private.v1\",";
  out += "\"private_build\":true,\"read_only\":true,";
  out += "\"status\":";
  AppendString(out, row.status);
  out += ",\"unavailable_stage\":";
  if (row.unavailable_stage.empty()) out += "null";
  else AppendString(out, row.unavailable_stage);
  out += ",\"native_revision\":" + std::to_string(row.native_revision);
  out += ",\"date_raw\":" + std::to_string(row.date_raw);
  out += ",\"actor_character_id\":" +
         std::to_string(row.actor_character_id);
  out += ",\"public_army_id\":" + std::to_string(row.public_army_id);
  out += ",\"native_carmy_id\":";
  AppendOptionalNumber(out, row.native_carmy_id);
  out += ",\"owner_character_id\":";
  AppendOptionalNumber(out, row.owner_character_id);
  out += ",\"current_province_id\":";
  AppendOptionalNumber(out, row.current_province_id);
  out += ",\"army_state\":";
  AppendString(out, row.army_state);
  out += ",\"in_combat\":";
  AppendOptionalBool(out, row.in_combat);
  out += ",\"retreating\":";
  AppendOptionalBool(out, row.retreating);
  out += ",\"commander_status\":";
  AppendString(out, row.commander_status);
  out += ",\"commander_character_id\":";
  AppendOptionalNumber(out, row.commander_character_id);
  out += ",\"is_commander_of_requested_army\":";
  AppendOptionalBool(out, row.is_commander_of_requested_army);
  out += ",\"knight_status\":";
  AppendString(out, row.knight_status);
  out += ",\"knight_regiment_id\":";
  AppendOptionalNumber(out, row.knight_regiment_id);
  out += ",\"is_knight_in_requested_army\":";
  AppendOptionalBool(out, row.is_knight_in_requested_army);
  out += ",\"global_commander_or_knight_status\":\"unknown\",";
  out += "\"safe_role_release\":null,\"date_credit\":false}";
  return out;
}

} // namespace xar::ck3_11906
