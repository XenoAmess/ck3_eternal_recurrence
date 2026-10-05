#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

struct NativeMaaRecruitmentQuoteV1 {
  std::string context = "regular_personal_create";
  std::string status = "unavailable";
  std::string unavailable_reason;
  std::int64_t resource_scale = 100'000;
  // Ten signed native resource slots, including conditional gold/treasury.
  std::optional<std::array<std::int64_t, 10>> resources_raw;
  friend bool operator==(const NativeMaaRecruitmentQuoteV1 &,
                         const NativeMaaRecruitmentQuoteV1 &) = default;
};

struct NativeMaaRecruitmentTypeInputsV1 {
  std::string type_key;
  std::int32_t type_index = -1;
  bool inputs_ready = false;
  std::string unavailable_reason;
  std::optional<std::int32_t> effective_quantity;
  std::optional<bool> can_create;
  NativeMaaRecruitmentQuoteV1 regular_personal_quote;
  friend bool operator==(const NativeMaaRecruitmentTypeInputsV1 &,
                         const NativeMaaRecruitmentTypeInputsV1 &) = default;
};

struct NativeMaaRecruitmentInputsV1 {
  std::int32_t schema_version = 1;
  std::string status = "unavailable";
  std::string unavailable_reason;
  std::optional<std::int32_t> owner_character_id;
  std::int32_t creation_kind = 1;
  std::string creation_scope = "regular_personal";
  std::string command_class = "CCreateMAARegimentCommand";
  std::int32_t title_id = -1;
  std::int32_t requested_quantity = -1;
  bool pay_cost = true;
  bool catalog_observed = false;
  std::vector<NativeMaaRecruitmentTypeInputsV1> types_in_native_order;
  std::vector<std::string> missing_type_keys;
  friend bool operator==(const NativeMaaRecruitmentInputsV1 &,
                         const NativeMaaRecruitmentInputsV1 &) = default;
};

} // namespace xar::game

namespace xar::ck3_12003 {

struct alignas(8) NativeMaaCost80 {
  std::array<std::int64_t, 10> resources_raw{};
};
static_assert(sizeof(NativeMaaCost80) == 80);

using NativeMaaRegularPersonalCanCreate = bool (*)(const void *, void *);
using NativeMaaRegularFinalRawQuote = NativeMaaCost80 *(*)(
    const void *, NativeMaaCost80 *, const void *, std::int64_t, bool);

struct NativeMaaRecruitmentBindings {
  bool enabled = false;
  void **character_storage_slot = nullptr;
  void **public_unit_storage_slot = nullptr;
  void **type_registry_slot = nullptr;
  NativeMaaRegularPersonalCanCreate regular_personal_can_create = nullptr;
  NativeMaaRegularFinalRawQuote regular_final_raw_quote = nullptr;
};

NativeMaaRecruitmentBindings BindNativeMaaRecruitmentImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

bool ReadNativeMaaRegularPersonalCanCreate(
    const NativeMaaRecruitmentBindings &, std::int32_t owner_full_id,
    std::int32_t type_index, bool &output) noexcept;

game::NativeMaaRecruitmentInputsV1 ReadNativeMaaRecruitmentInputsV1(
    const NativeMaaRecruitmentBindings &, std::int32_t owner_full_id) noexcept;
game::NativeMaaRecruitmentInputsV1 ReadNativeMaaRecruitmentInputsForUnitV1(
    const NativeMaaRecruitmentBindings &, std::int32_t public_unit_id) noexcept;

} // namespace xar::ck3_12003
