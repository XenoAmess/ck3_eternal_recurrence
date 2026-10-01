#include "xar_bridge/ck3_12002_prewar_participants.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <cstring>
#include <limits>
#include <sstream>

#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_12002 {
namespace {
constexpr std::int32_t kMaximumContracts = 4096;
constexpr std::int32_t kMaximumTerms = 4096;

bool DirectRead(const void *source, void *output, std::size_t size) noexcept {
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, source, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(output, source, size);
  return true;
#endif
}

template <typename T>
bool Read(const PrewarParticipantsAccess12002 &access, const void *base,
          std::size_t offset, T &output) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(base);
  if (base == nullptr ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - address)
    return false;
  const auto *source = reinterpret_cast<const void *>(address + offset);
  if (access.read_memory != nullptr)
    return access.read_memory(access.context, source, &output, sizeof(output));
  return DirectRead(source, &output, sizeof(output));
}

void *Resolve(const PrewarParticipantsAccess12002 &access, void **slot,
              std::int32_t id, std::size_t identity_offset) noexcept {
  if (id == -1) return nullptr;
  void *storage = nullptr;
  void *entries = nullptr;
  std::int32_t capacity = 0;
  void *object = nullptr;
  std::int32_t observed_id = -1;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (!Read(access, slot, 0, storage) ||
      !Read(access, storage, 0x2C, capacity) || capacity < 0 ||
      index >= static_cast<std::uint32_t>(capacity) ||
      !Read(access, storage, 0x20, entries) ||
      !Read(access, entries, static_cast<std::size_t>(index) * 0x10 + 0x08,
            object) ||
      !Read(access, object, identity_offset, observed_id) || observed_id != id)
    return nullptr;
  return object;
}

bool ReadRound(const PrewarParticipantsBindings12002 &bindings,
               const PrewarParticipantsAccess12002 &access, void *primary,
               void *opposing_primary, void *term, bool attacker_side,
               ForcedPrewarParticipantsSnapshot12002 &output,
               std::string_view &failure) {
  void *land = nullptr;
  void *contract_ids = nullptr;
  std::int32_t count = 0;
  if (!Read(access, primary, kPrewarCharacterLandOffset12002, land)) {
    failure = "primary_subject_contract_collection_unreadable";
    return false;
  }
  // The native getter projects an absent land extension to an empty array.
  if (land != nullptr &&
      (!Read(access, land, 0x248, contract_ids) ||
       !Read(access, land, 0x254, count) || count < 0 ||
       count > kMaximumContracts || (count != 0 && contract_ids == nullptr))) {
    failure = "primary_subject_contract_collection_unreadable";
    return false;
  }
  auto &source_count = attacker_side ? output.attacker_source_contract_count
                                    : output.defender_source_contract_count;
  source_count = static_cast<std::uint32_t>(count);
  std::uint8_t default_level = 0;
  if (!Read(access, term, kPrewarObligationDefaultLevelOffset12002,
            default_level)) {
    failure = "obligation_default_level_unreadable";
    return false;
  }
  void *fallback = nullptr;
  if (!Read(access, bindings.subject_contract_fallback_slot, 0, fallback)) {
    failure = "subject_contract_fallback_unreadable";
    return false;
  }
  for (std::int32_t order = 0; order < count; ++order) {
    std::int32_t contract_id = -1;
    if (!Read(access, contract_ids, static_cast<std::size_t>(order) * 4,
              contract_id)) {
      failure = "subject_contract_id_unreadable";
      return false;
    }
    auto *contract = Resolve(access, bindings.subject_contract_storage_slot,
                             contract_id, 0x08);
    void *source_endpoint = nullptr;
    if (contract == nullptr || contract == fallback ||
        !Read(access, contract, 0x28, source_endpoint) ||
        source_endpoint != primary) {
      failure = "subject_contract_identity_unavailable";
      return false;
    }
    void *terms = nullptr;
    std::int32_t term_count = 0;
    if (!Read(access, contract, 0x38, terms) ||
        !Read(access, contract, 0x44, term_count) || term_count < 0 ||
        term_count > kMaximumTerms || (term_count != 0 && terms == nullptr)) {
      failure = "subject_contract_terms_unreadable";
      return false;
    }
    std::int32_t obligation_index = -1;
    for (std::int32_t index = 0; index < term_count; ++index) {
      void *candidate = nullptr;
      if (!Read(access, terms, static_cast<std::size_t>(index) * 8, candidate)) {
        failure = "subject_contract_term_unreadable";
        return false;
      }
      if (candidate == term) {
        obligation_index = index;
        break; // Native pointer search selects the first occurrence.
      }
    }
    if (obligation_index == -1) continue;
    void *levels = nullptr;
    std::uint8_t active_level = 0;
    if (!Read(access, contract, 0x68, levels) ||
        !Read(access, levels, static_cast<std::size_t>(obligation_index),
              active_level)) {
      failure = "subject_contract_obligation_level_unreadable";
      return false;
    }
    if (active_level == default_level) continue;
    void *subject = nullptr;
    std::int32_t subject_id = -1;
    if (!Read(access, contract, 0x20, subject) ||
        !Read(access, subject, 0x18, subject_id) ||
        Resolve(access, bindings.character_storage_slot, subject_id, 0x18) !=
            subject) {
      failure = "subject_character_identity_unavailable";
      return false;
    }
    ForcedPrewarParticipant12002 row{
        subject_id, attacker_side,
        attacker_side ? output.primary_attacker_character_id
                      : output.primary_defender_character_id,
        contract_id, static_cast<std::uint32_t>(order), active_level,
        default_level};
    // Only the attacker round has this native collision branch. Do not
    // introduce a symmetric defender exclusion or deduplicate repeated rows.
    if (attacker_side && subject == opposing_primary)
      output.excluded_primary_defender_collisions.push_back(row);
    else
      output.forced_participants.push_back(row);
  }
  return true;
}

bool ReadSample(const PrewarParticipantsBindings12002 &bindings,
                const PrewarParticipantsAccess12002 &access,
                std::int32_t attacker_id, std::int32_t defender_id,
                ForcedPrewarParticipantsSnapshot12002 &output,
                std::string_view &failure) {
  output = {};
  output.primary_attacker_character_id = attacker_id;
  output.primary_defender_character_id = defender_id;
  auto *attacker = Resolve(access, bindings.character_storage_slot, attacker_id,
                           0x18);
  auto *defender = Resolve(access, bindings.character_storage_slot, defender_id,
                           0x18);
  if (attacker == nullptr || defender == nullptr) {
    failure = "prewar_primary_character_identity_unavailable";
    return false;
  }
  void *database = nullptr;
  void *term = nullptr;
  if (!Read(access, bindings.subject_contract_database_slot, 0, database) ||
      !Read(access, database, kPrewarObligationDatabaseOffset12002, term) ||
      term == nullptr) {
    failure = "subject_contract_obligation_database_unavailable";
    return false;
  }
  if (!ReadRound(bindings, access, attacker, defender, term, true, output,
                 failure) ||
      !ReadRound(bindings, access, defender, attacker, term, false, output,
                 failure))
    return false;
  output.available = true;
  return true;
}

void SerializeRows(std::ostringstream &wire,
                   const std::vector<ForcedPrewarParticipant12002> &rows) {
  wire << '[';
  bool first = true;
  for (const auto &row : rows) {
    if (!first) wire << ',';
    first = false;
    wire << "{\"character_id\":" << row.character_id
         << ",\"side\":\"" << (row.attacker_side ? "attacker" : "defender")
         << "\",\"source_primary_character_id\":"
         << row.source_primary_character_id
         << ",\"subject_contract_id\":" << row.subject_contract_id
         << ",\"source_contract_native_order\":"
         << row.source_contract_native_order
         << ",\"obligation_type_key\":\"tributary_war_participation_obligation\""
         << ",\"active_level_index_raw\":"
         << static_cast<unsigned>(row.active_level_index_raw)
         << ",\"default_level_index_raw\":"
         << static_cast<unsigned>(row.default_level_index_raw)
         << ",\"inclusion_reason\":\"nondefault_tributary_war_participation_obligation\""
         << ",\"source\":\"native_forced_tributary_contract\""
         << ",\"join_certainty\":\"native_builder_contract_forced_current_snapshot\"}";
  }
  wire << ']';
}
} // namespace

PrewarParticipantsBindings12002 BindPrewarParticipantsImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  if (module_base == 0 || executable_sha256 != kExecutableSha256) return {};
  return {true,
          reinterpret_cast<void **>(module_base + kCharacterStorageSlotRva),
          reinterpret_cast<void **>(module_base + kPrewarSubjectContractStorageSlotRva12002),
          reinterpret_cast<void **>(module_base + kPrewarSubjectContractFallbackSlotRva12002),
          reinterpret_cast<void **>(module_base + kPrewarSubjectContractDatabaseSlotRva12002)};
}

bool ReadForcedPrewarParticipants12002(
    const PrewarParticipantsBindings12002 &bindings,
    const PrewarParticipantsAccess12002 &access, std::int32_t attacker_id,
    std::int32_t defender_id, ForcedPrewarParticipantsSnapshot12002 &output,
    std::string_view &failure) {
  output = {};
  failure = {};
  if (!bindings.enabled || bindings.character_storage_slot == nullptr ||
      bindings.subject_contract_storage_slot == nullptr ||
      bindings.subject_contract_fallback_slot == nullptr ||
      bindings.subject_contract_database_slot == nullptr) {
    failure = "prewar_participants_environment_unavailable";
    return false;
  }
  ForcedPrewarParticipantsSnapshot12002 first, second;
  if (!ReadSample(bindings, access, attacker_id, defender_id, first, failure) ||
      !ReadSample(bindings, access, attacker_id, defender_id, second, failure))
    return false;
  if (first != second) {
    failure = "prewar_subject_contract_samples_changed";
    return false;
  }
  output = std::move(second);
  return true;
}

std::string SerializeForcedPrewarParticipants12002(
    const ForcedPrewarParticipantsSnapshot12002 &snapshot) {
  std::ostringstream wire;
  wire << "{\"schema\":\"ck3.forced-prewar-participants.v1\",\"game_version\":\"1.20.0.2\","
       << "\"exe_sha256\":\"" << kExecutableSha256 << "\",\"available\":"
       << (snapshot.available ? "true" : "false")
       << ",\"complete_initial_participants_ready\":false"
       << ",\"voluntary_allies_available\":false"
       << ",\"primary_attacker_character_id\":"
       << snapshot.primary_attacker_character_id
       << ",\"primary_defender_character_id\":"
       << snapshot.primary_defender_character_id
       << ",\"attacker_source_contract_count\":"
       << snapshot.attacker_source_contract_count
       << ",\"defender_source_contract_count\":"
       << snapshot.defender_source_contract_count
       << ",\"forced_participants\":";
  SerializeRows(wire, snapshot.forced_participants);
  wire << ",\"excluded_primary_defender_collisions\":";
  SerializeRows(wire, snapshot.excluded_primary_defender_collisions);
  wire << '}';
  return wire.str();
}

} // namespace xar::ck3_12002
