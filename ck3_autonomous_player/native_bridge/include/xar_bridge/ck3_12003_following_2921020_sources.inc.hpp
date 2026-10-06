// Included inside xar::ck3_12002; the outer factory validates exact build.
struct ContextSourceFollowing2921020BindingsV1 {
  bool enabled = false;
  const void *lege_storage_slot = nullptr;
  const void *lege_fallback_slot = nullptr;
};
inline ContextSourceFollowing2921020BindingsV1 BindFollowing2921020Sources12003(std::uintptr_t base) {
  ContextSourceFollowing2921020BindingsV1 out{};
  if (!base) return out;
  out.enabled = true;
  out.lege_storage_slot = reinterpret_cast<const void *>(base + 0x5D1EC98);
  out.lege_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1EC50);
  return out;
}
