#include "xar_bridge/army_late_context_copy12004.hpp"

#include <algorithm>
#include <cstring>

namespace xar::ck3_12004 {
namespace {
template <typename T>
T Decode(const std::byte *data, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, data + offset, sizeof(value));
  return value;
}
bool Copy(ArmyLateContextReadMemory12004 reader, void *context,
    const void *base, std::size_t offset, void *out, std::size_t size) noexcept {
  if (!reader || !base) return false;
  const auto *address = reinterpret_cast<const void *>(reinterpret_cast<std::uintptr_t>(base) + offset);
  return reader(context, address, out, size);
}
} // namespace
ArmyLateContextCopy12004 CopyActualArmyLateContext12004(const void *incoming,
    ArmyLateContextReadMemory12004 reader, void *reader_context) noexcept {
  ArmyLateContextCopy12004 out{};
  std::array<std::byte, 16> root{}, before{}, after{};
  if (!Copy(reader, reader_context, incoming, 0, root.data(), root.size())) return out;
  out.root_copy_ready = true;
  out.root_kind_raw_u16 = Decode<std::uint16_t>(root.data(), 0);
  out.root_subtype_raw_u16 = Decode<std::uint16_t>(root.data(), 2);
  out.root_payload_raw_u64 = Decode<std::uint64_t>(root.data(), 8);
  std::uint32_t seed = 0;
  if (Copy(reader, reader_context, incoming, 0x10, &seed, sizeof(seed))) out.context_seed_10_raw_u32 = seed;
  if (!Copy(reader, reader_context, incoming, 0x18, before.data(), before.size())) {
    out.unavailable_reason = "incoming_named_header_unavailable";
    return out;
  }
  out.named_header_copy_ready = true;
  const auto data = Decode<std::uintptr_t>(before.data(), 0);
  const auto capacity = Decode<std::int32_t>(before.data(), 8);
  const auto count = Decode<std::int32_t>(before.data(), 12);
  out.named_capacity_raw_i32 = capacity;
  out.named_count_raw_i32 = count;
  if (count < 0 || capacity < count || (count > 0 && data == 0)) {
    out.unavailable_reason = "incoming_named_header_not_copyable";
    return out;
  }
  const auto wanted = std::min(static_cast<std::size_t>(count), kArmyLateContextCopiedRows12004);
  out.named_rows_truncated = static_cast<std::size_t>(count) > wanted;
  bool complete = true;
  for (std::size_t i = 0; i < wanted; ++i) {
    std::array<std::byte, 24> raw{};
    if (!Copy(reader, reader_context, reinterpret_cast<const void *>(data), i * 0x18, raw.data(), raw.size())) {
      complete = false;
      break;
    }
    auto &row = out.rows[out.copied_row_count++];
    row.key_raw_u32 = Decode<std::uint32_t>(raw.data(), 0);
    row.kind_raw_u16 = Decode<std::uint16_t>(raw.data(), 8);
    row.subtype_raw_u16 = Decode<std::uint16_t>(raw.data(), 10);
    row.payload_raw_u64 = Decode<std::uint64_t>(raw.data(), 16);
  }
  if (!Copy(reader, reader_context, incoming, 0x18, after.data(), after.size())) {
    out.unavailable_reason = "incoming_named_header_reread_unavailable";
    return out;
  }
  out.named_header_unchanged = before == after;
  out.named_rows_copy_ready = complete && out.named_header_unchanged;
  out.unavailable_reason = !complete ? "incoming_named_row_copy_incomplete"
      : (!out.named_header_unchanged ? "incoming_named_header_changed"
      : (out.named_rows_truncated ? "incoming_named_rows_truncated" : "none"));
  return out;
}

ArmyLateContextSourceRoles12004 ClassifyActualArmyLateContextRoles12004(
    const ArmyLateContextCopy12004 &copy, std::span<const std::uint32_t, 3> keys) noexcept {
  ArmyLateContextSourceRoles12004 out{};
  if (copy.root_kind_raw_u16 && copy.root_subtype_raw_u16)
    out.root_kind27_subtype0_matches = *copy.root_kind_raw_u16 == 27 && *copy.root_subtype_raw_u16 == 0;
  out.named_keys_loaded = true;
  for (std::size_t n = 0; n < out.roles.size(); ++n) {
    auto &role = out.roles[n];
    role.loaded_key_raw_u32 = keys[n];
    const ArmyLateContextCopiedRow12004 *matched = nullptr;
    for (std::size_t i = 0; i < copy.copied_row_count; ++i)
      if (copy.rows[i].key_raw_u32 == keys[n]) {
        ++role.matching_key_count;
        matched = &copy.rows[i];
      }
    if (role.matching_key_count == 1 && matched && copy.named_rows_copy_ready) {
      role.token_kind_and_subtype_match = matched->kind_raw_u16 == role.expected_kind_raw_u16 && matched->subtype_raw_u16 == 0;
      role.payload_raw_u64 = matched->payload_raw_u64;
    }
  }
  out.complete_named_input_shape_matches = copy.named_rows_copy_ready && !copy.named_rows_truncated &&
      out.root_kind27_subtype0_matches.value_or(false) &&
      std::all_of(out.roles.begin(), out.roles.end(), [](const auto &role) {
        return role.token_kind_and_subtype_match.value_or(false);
      });
  return out;
}
} // namespace xar::ck3_12004
