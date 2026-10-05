#include "xar_bridge/ck3_12003_maa_recruitment.hpp"

#include <cstddef>
#include <cstring>
#include <utility>

namespace xar::ck3_12003 {
namespace {

constexpr std::string_view kExactImageSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
constexpr std::array<std::string_view, 9> kSiegeTypeKeys{
    "onager", "mangonel", "trebuchet", "bombard", "torch_bearers",
    "ballista", "cloud_ladder", "siege_tower", "cannon"};

template <typename T> T Load(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

const void *ResolveStored(void **slot, std::int32_t full_id,
                          std::size_t identity_offset) {
  if (full_id == -1 || !slot || !*slot) return nullptr;
  const auto *storage = *slot;
  const auto index = static_cast<std::uint32_t>(full_id) & 0xFFFFFFu;
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  if (capacity < 0 || index >= static_cast<std::uint32_t>(capacity))
    return nullptr;
  const auto *rows = Load<const void *>(storage, 0x20);
  if (!rows) return nullptr;
  const auto *object = Load<const void *>(
      rows, static_cast<std::size_t>(index) * 16 + 8);
  if (!object || Load<std::int32_t>(object, identity_offset) != full_id)
    return nullptr;
  return object;
}

bool ReadSiegeTypeKey(const void *type, std::optional<std::size_t> &key_index) {
  key_index.reset();
  const auto length = Load<std::uint32_t>(type, 0x28);
  bool wanted_length = false;
  for (const auto key : kSiegeTypeKeys)
    wanted_length = wanted_length || key.size() == length;
  if (!wanted_length) return true;
  const auto capacity = Load<std::uint64_t>(type, 0x30);
  const char *bytes = capacity < 16
                          ? static_cast<const char *>(type) + 0x18
                          : Load<const char *>(type, 0x18);
  if (!bytes) return false;
  for (std::size_t i = 0; i < kSiegeTypeKeys.size(); ++i) {
    const auto key = kSiegeTypeKeys[i];
    if (key.size() == length && std::memcmp(bytes, key.data(), length) == 0) {
      key_index = i;
      break;
    }
  }
  return true;
}

// Same80B producer as the true regular personal GUI and charge consumer.
// Its fifth argument is title scope; personal creation passes false.
bool ReadRegularRawQuote(const NativeMaaRecruitmentBindings &bindings,
                         const void *type, const void *owner,
                         std::int32_t effective_quantity,
                         NativeMaaCost80 &output) noexcept {
  if (!bindings.regular_final_raw_quote) return false;
  NativeMaaCost80 value;
  NativeMaaCost80 *returned = nullptr;
  const auto quantity_fixed =
      static_cast<std::int64_t>(effective_quantity) * 100'000;
#if defined(_MSC_VER) && defined(_WIN32)
  __try {
    returned = bindings.regular_final_raw_quote(
        type, &value, owner, quantity_fixed, false);
  } __except (1) {
    return false;
  }
#else
  try {
    returned = bindings.regular_final_raw_quote(
        type, &value, owner, quantity_fixed, false);
  } catch (...) {
    return false;
  }
#endif
  if (returned != &value) return false;
  output = value;
  return true;
}

} // namespace

// Integration owner: C. Insert inside namespace xar::ck3_12003.
// Exact 1.20.0.3: CCreateMAARegimentCommand, primary validator 296F9F0.
// Formal 1338F90 personal defaults: kind1/title-1/quantity-1/pay1.
// This caller-owned buffer is only a direct validator input. It is never
// cloned, submitted, or passed to a virtual command operation.

bool ReadNativeMaaRegularPersonalCanCreate(
    const NativeMaaRecruitmentBindings& bindings,
    std::int32_t owner_full_id,
    std::int32_t type_index,
    bool& output) noexcept {
    if (!bindings.regular_personal_can_create) {
        return false;
    }
    alignas(8) std::uint8_t local_command[0x38]{};
    const std::int32_t creation_kind_raw = 1;
    const std::int32_t title_full_id = -1;
    const std::int32_t requested_quantity = -1;
    const std::uint8_t pay_cost = 1;
    std::memcpy(local_command + 0x20, &creation_kind_raw, sizeof(creation_kind_raw));
    std::memcpy(local_command + 0x24, &title_full_id, sizeof(title_full_id));
    std::memcpy(local_command + 0x28, &owner_full_id, sizeof(owner_full_id));
    std::memcpy(local_command + 0x2c, &type_index, sizeof(type_index));
    std::memcpy(local_command + 0x30, &requested_quantity, sizeof(requested_quantity));
    std::memcpy(local_command + 0x34, &pay_cost, sizeof(pay_cost));
    bool admitted = false;
#if defined(_MSC_VER) && defined(_WIN32)
    __try {
        admitted = bindings.regular_personal_can_create(local_command, nullptr);
    } __except (1) {
        return false;
    }
#else
    try {
        admitted = bindings.regular_personal_can_create(local_command, nullptr);
    } catch (...) {
        return false;
    }
#endif
    output = admitted;
    return true;
}

NativeMaaRecruitmentBindings BindNativeMaaRecruitmentImage(
    std::uintptr_t base, std::string_view executable_sha256) noexcept {
  NativeMaaRecruitmentBindings bindings;
  if (!base || executable_sha256 != kExactImageSha256) return bindings;
  bindings.character_storage_slot = reinterpret_cast<void **>(base + 0x5C67568);
  bindings.public_unit_storage_slot = reinterpret_cast<void **>(base + 0x5D1E380);
  bindings.type_registry_slot = reinterpret_cast<void **>(base + 0x5C67558);
  bindings.regular_personal_can_create =
      reinterpret_cast<NativeMaaRegularPersonalCanCreate>(base + 0x296F9F0);
  bindings.regular_final_raw_quote =
      reinterpret_cast<NativeMaaRegularFinalRawQuote>(base + 0x30BCE20);
  bindings.enabled = true;
  return bindings;
}

game::NativeMaaRecruitmentInputsV1 ReadNativeMaaRecruitmentInputsV1(
    const NativeMaaRecruitmentBindings &bindings,
    std::int32_t owner_full_id) noexcept {
  game::NativeMaaRecruitmentInputsV1 output;
  try {
    if (!bindings.enabled) {
      output.unavailable_reason = "exact_build_binding_unavailable";
      return output;
    }
    const auto *owner = ResolveStored(bindings.character_storage_slot,
                                      owner_full_id, 0x18);
    if (!owner || Load<std::uint32_t>(owner, 0x1C) != 0x43686172u) {
      output.unavailable_reason = "owner_character_unresolved";
      return output;
    }
    output.owner_character_id = owner_full_id;
    if (!bindings.type_registry_slot || !*bindings.type_registry_slot) {
      output.unavailable_reason = "type_registry_unavailable";
      return output;
    }
    const auto *registry = *bindings.type_registry_slot;
    const auto *types = Load<const void *>(registry, 0x50);
    const auto count = Load<std::int32_t>(registry, 0x5C);
    if (count < 0 || (count != 0 && !types)) {
      output.unavailable_reason = "type_registry_header_unavailable";
      return output;
    }
    std::array<bool, kSiegeTypeKeys.size()> found{};
    bool catalog_complete = true;
    bool rows_complete = true;
    for (std::int32_t i = 0; i < count; ++i) {
      const auto *type = Load<const void *>(
          types, static_cast<std::size_t>(i) * sizeof(void *));
      if (!type || Load<std::uint32_t>(type, 0x38) != 0x4744624Fu) {
        catalog_complete = false;
        continue;
      }
      std::optional<std::size_t> key_index;
      if (!ReadSiegeTypeKey(type, key_index)) {
        catalog_complete = false;
        continue;
      }
      if (!key_index) continue;
      found[*key_index] = true;
      game::NativeMaaRecruitmentTypeInputsV1 row;
      row.type_key = kSiegeTypeKeys[*key_index];
      row.type_index = Load<std::int32_t>(type, 0x10);
      row.effective_quantity = Load<std::int32_t>(type, 0x70);
      bool can_create = false;
      if (ReadNativeMaaRegularPersonalCanCreate(
              bindings, owner_full_id, row.type_index, can_create)) {
        row.can_create = can_create;
      }
      NativeMaaCost80 quote;
      if (ReadRegularRawQuote(bindings, type, owner,
                              *row.effective_quantity, quote)) {
        row.regular_personal_quote.resources_raw = quote.resources_raw;
        row.regular_personal_quote.status = "available";
      } else {
        row.regular_personal_quote.unavailable_reason =
            "native_regular_final_quote_unavailable";
      }
      row.inputs_ready = row.can_create.has_value() &&
                         row.regular_personal_quote.resources_raw.has_value();
      if (!row.inputs_ready) {
        row.unavailable_reason = "native_regular_creation_inputs_unavailable";
        rows_complete = false;
      }
      output.types_in_native_order.push_back(std::move(row));
    }
    output.catalog_observed = catalog_complete;
    if (catalog_complete) {
      for (std::size_t i = 0; i < found.size(); ++i)
        if (!found[i]) output.missing_type_keys.emplace_back(kSiegeTypeKeys[i]);
    }
    output.status = catalog_complete && rows_complete ? "available" : "partial";
    if (output.status == "partial")
      output.unavailable_reason = "native_regular_inputs_partially_observed";
    return output;
  } catch (...) {
    output.status = "unavailable";
    output.unavailable_reason = "native_maa_recruitment_read_failed";
    return output;
  }
}

game::NativeMaaRecruitmentInputsV1 ReadNativeMaaRecruitmentInputsForUnitV1(
    const NativeMaaRecruitmentBindings &bindings,
    std::int32_t public_unit_id) noexcept {
  game::NativeMaaRecruitmentInputsV1 output;
  try {
    if (!bindings.enabled) {
      output.unavailable_reason = "exact_build_binding_unavailable";
      return output;
    }
    const auto *unit = ResolveStored(bindings.public_unit_storage_slot,
                                     public_unit_id, 0x10);
    if (!unit) {
      output.unavailable_reason = "public_unit_unresolved";
      return output;
    }
    return ReadNativeMaaRecruitmentInputsV1(
        bindings, Load<std::int32_t>(unit, 0x174));
  } catch (...) {
    output.unavailable_reason = "public_unit_owner_unavailable";
    return output;
  }
}

} // namespace xar::ck3_12003
