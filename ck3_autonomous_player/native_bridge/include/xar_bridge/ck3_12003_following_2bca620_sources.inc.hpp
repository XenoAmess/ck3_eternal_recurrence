// Included inside xar::ck3_12002; the main factory checks the exact build once.
struct ContextSourceFollowing2bca620BindingsV1 {
  bool enabled = false;
  const void *provider_slot = nullptr;
  const void *provider_fallback_slot = nullptr;
};
inline ContextSourceFollowing2bca620BindingsV1 BindFollowing2bca620Sources12003(std::uintptr_t base) {
  ContextSourceFollowing2bca620BindingsV1 out{};
  if (!base) return out;
  out.enabled = true;
  out.provider_slot = reinterpret_cast<const void *>(base + 0x5C670F8);
  out.provider_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1E0B0);
  return out;
}
