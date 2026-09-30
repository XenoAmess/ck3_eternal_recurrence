#include "xar_bridge/ck3_12002_settlement.hpp"

#include <array>
#include <cstddef>
#include <cstring>

namespace xar::ck3_12002 {
namespace {

template <typename T>
T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

struct NameView {
  const char *data = nullptr;
  std::int32_t length = 0;
  std::uint8_t indirect = 0;
  std::array<std::byte, 3> padding{};
};
static_assert(sizeof(NameView) == 0x10);

constexpr std::int64_t kScale = 100'000;
constexpr std::int32_t kMaximumGlobalEntries = 1'000'000;

const void *Find(const SettlementBindings &bindings, void *table,
                 void *container, std::string_view name) noexcept {
  const NameView view{name.data(), static_cast<std::int32_t>(name.size())};
  std::int32_t key = -1;
  if (bindings.lookup_identifier(table, &key, &view) == nullptr || key < 0) {
    return nullptr;
  }
  const auto entries = Load<void *>(container, 0x10);
  const auto count = Load<std::int32_t>(container, 0x1C);
  if (count < 0 || count > kMaximumGlobalEntries ||
      (entries == nullptr && count != 0)) {
    return nullptr;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    const auto entry = static_cast<const std::byte *>(entries) + index * 0x20ULL;
    if (Load<std::int32_t>(entry, 0x08) == key) {
      return entry + 0x10;
    }
  }
  return nullptr;
}

bool Fixed(const void *target, game::FixedPointValue &output) noexcept {
  if (target == nullptr || Load<std::uint16_t>(target, 0) != 1) {
    return false;
  }
  output.raw = Load<std::int64_t>(target, 0x08);
  output.scale = kScale;
  return true;
}

bool Integer(const void *target, std::int64_t &output) noexcept {
  game::FixedPointValue value;
  if (!Fixed(target, value) || value.raw % kScale != 0) {
    return false;
  }
  output = value.raw / kScale;
  return true;
}

bool Boolean(const void *target, bool &output) noexcept {
  std::int64_t value = 0;
  if (!Integer(target, value) || (value != 0 && value != 1)) {
    return false;
  }
  output = value == 1;
  return true;
}

bool SourceCharacter(const CoreBindings &core, const void *target,
                     std::int32_t &output) noexcept {
  if (target == nullptr || Load<std::uint16_t>(target, 0) != 4) {
    return false;
  }
  const auto id = Load<std::int32_t>(target, 0x08);
  const auto storage = *core.character_storage_slot;
  if (storage == nullptr || id == -1) {
    return false;
  }
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto slots = Load<void *>(storage, 0x20);
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return false;
  }
  const auto character = Load<void *>(slots, index * 0x10ULL + 0x08);
  if (character == nullptr || Load<std::int32_t>(character, 0x18) != id) {
    return false;
  }
  // Identity of the retained dead character is sufficient. No gameplay
  // liveness/family/death component is required by the settlement contract.
  output = id;
  return true;
}

} // namespace

SettlementBindings BindSettlementImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  if (image_base == 0 || executable_sha256 != kExecutableSha256) {
    return {};
  }
  return {true,
          reinterpret_cast<SettlementGlobalAccessor *>(
              image_base + kSettlementGlobalAccessorSlotRva),
          reinterpret_cast<SettlementIdentifierTableGetter>(
              image_base + kSettlementIdentifierTableGetterRva),
          reinterpret_cast<SettlementIdentifierLookup>(
              image_base + kSettlementIdentifierLookupRva)};
}

SettlementReadResult ReadSettlement(const SettlementBindings &bindings,
                                    const CoreBindings &core,
                                    game::Snapshot &output) noexcept {
  output.has_one_life_settlement = false;
  output.one_life_settlement = {};
  if (!bindings.enabled || !core.enabled ||
      bindings.global_accessor_slot == nullptr ||
      *bindings.global_accessor_slot == nullptr ||
      bindings.identifier_table == nullptr ||
      bindings.lookup_identifier == nullptr ||
      core.character_storage_slot == nullptr) {
    return SettlementReadResult::unavailable;
  }
  const auto container = (*bindings.global_accessor_slot)();
  const auto table = bindings.identifier_table();
  if (container == nullptr || table == nullptr) {
    return SettlementReadResult::unavailable;
  }
  const auto find = [&](std::string_view name) {
    return Find(bindings, table, container, name);
  };
  bool ready = false;
  const auto ready_target = find("xa_settlement_ready");
  if (ready_target == nullptr) {
    return SettlementReadResult::not_published;
  }
  if (!Boolean(ready_target, ready)) {
    // Names are registered before first use; their value may still be none.
    return Load<std::uint16_t>(ready_target, 0) == 0
               ? SettlementReadResult::not_published
               : SettlementReadResult::invalid_payload;
  }
  if (!ready) {
    return SettlementReadResult::not_published;
  }

  game::OneLifeSettlementSnapshot settlement;
  if (!Integer(find("xa_settlement_commit_serial"), settlement.commit_serial) ||
      !SourceCharacter(core, find("xa_settlement_source_character"),
                       settlement.source_character_id) ||
      !Fixed(find("xa_settlement_final_score"), settlement.final_score) ||
      !Fixed(find("xa_settlement_score_before_reject"),
             settlement.score_before_reject) ||
      !Integer(find("xa_settlement_record_candidate"),
               settlement.record_candidate) ||
      !Integer(find("xa_settlement_old_record"), settlement.old_record) ||
      !Integer(find("xa_settlement_record_delta"), settlement.record_delta) ||
      !Integer(find("xa_settlement_blessing_count"), settlement.blessing_count) ||
      !Integer(find("xa_settlement_refusal_count"), settlement.refusal_count) ||
      !Integer(find("xa_settlement_contract_progress"),
               settlement.contract_progress) ||
      !Boolean(find("xa_settlement_record_written"), settlement.record_written)) {
    return SettlementReadResult::invalid_payload;
  }
  ready = false;
  if (!Boolean(find("xa_settlement_ready"), ready) || !ready) {
    return SettlementReadResult::not_published;
  }
  output.one_life_settlement = settlement;
  output.has_one_life_settlement = true;
  return SettlementReadResult::published;
}

} // namespace xar::ck3_12002
