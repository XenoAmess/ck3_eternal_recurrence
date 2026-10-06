// Included inside xar::ck3_12002; the enclosing factory binds the exact EXE SHA.
struct ContextSourceFollowing2921350BindingsV1 {
  bool enabled = false;
  const void *title_storage_slot = nullptr, *title_fallback_slot = nullptr;
  const void *title_default_header = nullptr;
  const void *source_storage_slot = nullptr, *source_fallback_slot = nullptr;
  const void *manager_slot = nullptr;
  const void *tier_default_row = nullptr, *tier_default_guard = nullptr;
};
inline ContextSourceFollowing2921350BindingsV1 BindFollowing2921350Sources12003(std::uintptr_t base) {
  ContextSourceFollowing2921350BindingsV1 out{};
  if (!base) return out;
  out.enabled = true;
  out.title_storage_slot = reinterpret_cast<const void *>(base + 0x5D1DAF8);
  out.title_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DAE0);
  out.title_default_header = reinterpret_cast<const void *>(base + 0x5459C88);
  out.source_storage_slot = reinterpret_cast<const void *>(base + 0x5D1EC90);
  out.source_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1EC48);
  out.manager_slot = reinterpret_cast<const void *>(base + 0x5C671A8);
  out.tier_default_row = reinterpret_cast<const void *>(base + 0x5D65B00);
  out.tier_default_guard = reinterpret_cast<const void *>(base + 0x5D65AFC);
  return out;
}
