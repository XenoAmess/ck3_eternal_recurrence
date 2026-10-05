// Included inside xar::ck3_12002; exact-build validation belongs to the outer factory.
struct ContextSourceFollowing2920b50BindingsV1 {
  bool enabled = false;
  const void *accolade_storage_slot = nullptr;
  const void *accolade_fallback_slot = nullptr;
  const void *list_default_header = nullptr;
  const void *list_default_guard_slot = nullptr;
  const void *ranked_default_row = nullptr;
  const void *ranked_default_guard_slot = nullptr;
};
inline ContextSourceFollowing2920b50BindingsV1 BindFollowing2920b50Sources12003(std::uintptr_t base) {
  ContextSourceFollowing2920b50BindingsV1 out{};
  if (!base) return out;
  out.enabled = true;
  out.accolade_storage_slot = reinterpret_cast<const void *>(base + 0x5D1ECA0);
  out.accolade_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1EC40);
  out.list_default_header = reinterpret_cast<const void *>(base + 0x5D67E80);
  out.list_default_guard_slot = reinterpret_cast<const void *>(base + 0x5D67E78);
  out.ranked_default_row = reinterpret_cast<const void *>(base + 0x5D68FB0);
  out.ranked_default_guard_slot = reinterpret_cast<const void *>(base + 0x5D68FA8);
  return out;
}
