// Included inside namespace xar::ck3_12002, before ContextSourceBindingsV1.
struct ContextSourceAbsentRecipientBindingsV1 {
  bool enabled = false;
  const void *associated_storage_slot = nullptr;
  const void *associated_fallback_slot = nullptr;
  const void *membership_inline_header = nullptr;
  const void *membership_guard_slot = nullptr;
  const void *aggregate_inline_context = nullptr;
  const void *aggregate_guard_slot = nullptr;
  const void *member_multiplier_slot = nullptr;
  const void *clamp_lower_slot = nullptr;
  const void *clamp_upper_slot = nullptr;
};
inline ContextSourceAbsentRecipientBindingsV1 BindAbsentRecipientSources12003(
    std::uintptr_t base) noexcept {
  ContextSourceAbsentRecipientBindingsV1 out{};
  if (!base) return out;
  out.enabled = true;
  out.associated_storage_slot = reinterpret_cast<const void *>(base + 0x5D1E2F8);
  out.associated_fallback_slot = reinterpret_cast<const void *>(base + 0x5C67670);
  out.membership_inline_header = reinterpret_cast<const void *>(base + 0x5D67E40);
  out.membership_guard_slot = reinterpret_cast<const void *>(base + 0x5D67E38);
  out.aggregate_inline_context = reinterpret_cast<const void *>(base + 0x5D67B90);
  out.aggregate_guard_slot = reinterpret_cast<const void *>(base + 0x5D67B80);
  out.member_multiplier_slot = reinterpret_cast<const void *>(base + 0x5C696F8);
  out.clamp_lower_slot = reinterpret_cast<const void *>(base + 0x5C68E00);
  out.clamp_upper_slot = reinterpret_cast<const void *>(base + 0x5C68DF8);
  return out;
}
