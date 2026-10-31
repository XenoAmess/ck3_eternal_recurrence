#include "xar_bridge/family_ruler_default_materializer_12004.hpp"

#include <limits>
#include <utility>

namespace xar::bridge {
namespace {

struct ContextHeader {
  std::uintptr_t definition = 0;
  std::uint32_t definition_hash = 0;
  std::array<std::uint32_t, 6> raw_roles{};
  std::uintptr_t rows = 0;
  std::int32_t count = 0;
  std::uintptr_t bank = 0;
  std::int32_t capacity = 0;
  std::int32_t bank_count = 0;
  std::uint32_t matrilineal_id = 0;
  std::uint32_t grand_wedding_id = 0;
  friend bool operator==(const ContextHeader &, const ContextHeader &) = default;
};

template <typename T>
bool ReadAt(const FamilyOutgoingStorageAccess12004 &access,
            std::uintptr_t base, std::size_t offset, T &out) noexcept {
  constexpr auto top = (std::numeric_limits<std::uintptr_t>::max)();
  if (access.read_memory == nullptr || base == 0 || offset > top - base)
    return false;
  const auto address = base + offset;
  if (sizeof(T) - 1 > top - address) return false;
  return access.read_memory(access.context, address, &out, sizeof(T));
}

bool ReadHeader(const FamilyRulerContextAccess12004 &access,
                std::uintptr_t context, std::uintptr_t definition,
                ContextHeader &header) noexcept {
  const auto &memory = access.memory;
  return ReadAt(memory, context, 0, header.definition) &&
      ReadAt(memory, definition, 0x14, header.definition_hash) &&
      ReadAt(memory, context, 0x2D8, header.raw_roles) &&
      ReadAt(memory, definition, 0x2258, header.rows) &&
      ReadAt(memory, definition, 0x2264, header.count) &&
      ReadAt(memory, context, 0x300, header.bank) &&
      ReadAt(memory, context, 0x308, header.capacity) &&
      ReadAt(memory, context, 0x30C, header.bank_count) &&
      ReadAt(memory, access.matrilineal_option_id_slot, 0,
             header.matrilineal_id) &&
      ReadAt(memory, access.grand_wedding_option_id_slot, 0,
             header.grand_wedding_id);
}

bool ValidHeader(const ContextHeader &header,
                 std::uintptr_t expected_definition) noexcept {
  if (header.definition != expected_definition || header.raw_roles[0] == 0 ||
      header.raw_roles[0] == UINT32_MAX ||
      header.raw_roles[5] != header.raw_roles[0] || header.count < 0 ||
      header.count > 4096 || header.capacity < header.count ||
      header.bank_count != header.count)
    return false;
  for (std::size_t index = 1; index < 5; ++index)
    if (header.raw_roles[index] == 0) return false;
  return header.count == 0 || (header.rows != 0 && header.bank != 0);
}

FamilyRulerMaterializeStatus12004 CapturePass(
    const ck3_12002::ContextBindings &bindings,
    const FamilyRulerContextAccess12004 &access, const void *context,
    std::uintptr_t expected_definition, ContextHeader &header,
    FamilyRulerPreparedContextCopy12004 &copy) {
  using Status = FamilyRulerMaterializeStatus12004;
  const auto address = reinterpret_cast<std::uintptr_t>(context);
  if (!ReadHeader(access, address, expected_definition, header) ||
      !ValidHeader(header, expected_definition)) return Status::unavailable;
  copy.actual_definition = header.definition;
  copy.definition_hash = header.definition_hash;
  for (std::size_t index = 0; index < copy.roles.size(); ++index)
    copy.roles[index] = header.raw_roles[index];
  copy.options.reserve(static_cast<std::size_t>(header.count));
  for (std::int32_t index = 0; index < header.count; ++index) {
    FamilyOutgoingOptionCopy12004 option{};
    const auto ordinal = static_cast<std::size_t>(index);
    if (!ReadAt(access.memory, header.rows, ordinal * 0x730 + 0x368,
                option.flag) ||
        !ReadAt(access.memory, header.bank, ordinal, option.bank_byte) ||
        option.bank_byte > 1)
      return Status::unavailable;
    copy.options.push_back(option);
  }
  copy.can_send = bindings.validate(const_cast<void *>(context), nullptr);
  copy.matrilineal = access.read_boolean_option(context, header.matrilineal_id);
  copy.grand_wedding =
      access.read_boolean_option(context, header.grand_wedding_id);
  ContextHeader recheck{};
  if (!ReadHeader(access, address, expected_definition, recheck))
    return Status::unavailable;
  return recheck == header ? Status::complete : Status::changed;
}

} // namespace

FamilyRulerMaterializeStatus12004 CopyFamilyRulerPreparedContext12004(
    const ck3_12002::ContextBindings &bindings,
    const FamilyRulerContextAccess12004 &access,
    const void *actual_owned_context, std::uintptr_t expected_definition,
    FamilyRulerPreparedContextCopy12004 &output) noexcept {
  using Status = FamilyRulerMaterializeStatus12004;
  output = {};
  if (actual_owned_context == nullptr || expected_definition == 0)
    return Status::invalid_request;
  if (bindings.validate == nullptr || access.read_boolean_option == nullptr ||
      access.memory.read_memory == nullptr ||
      access.matrilineal_option_id_slot == 0 ||
      access.grand_wedding_option_id_slot == 0)
    return Status::unavailable;
  try {
    ContextHeader first_header{}, second_header{};
    FamilyRulerPreparedContextCopy12004 first{}, second{};
    auto status = CapturePass(bindings, access, actual_owned_context,
                              expected_definition, first_header, first);
    if (status != Status::complete) return status;
    status = CapturePass(bindings, access, actual_owned_context,
                          expected_definition, second_header, second);
    if (status != Status::complete) return status;
    if (first_header != second_header || first != second) return Status::changed;
    output = std::move(first);
    return Status::complete;
  } catch (...) {
    output = {};
    return Status::unavailable;
  }
}

} // namespace xar::bridge
