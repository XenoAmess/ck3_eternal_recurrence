// Included inside xar::ck3_12002; exact-build binding is checked by the outer factory.
struct ContextSourceFollowing312a950BindingsV1 {
  bool enabled = false;
  const void *character_storage_slot = nullptr;
  const void *character_fallback_slot = nullptr;
  const void *government_fallback_slot = nullptr;
  const void *land_storage_slot = nullptr;
  const void *land_fallback_slot = nullptr;
  const void *provider_slot = nullptr;
};
inline ContextSourceFollowing312a950BindingsV1 BindFollowing312a950Sources12003(std::uintptr_t base) {
  ContextSourceFollowing312a950BindingsV1 out{};
  if (!base) return out;
  out.enabled = true;
  out.character_storage_slot = reinterpret_cast<const void *>(base + 0x5C67568);
  out.character_fallback_slot = reinterpret_cast<const void *>(base + 0x5C67570);
  out.government_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1E2A8);
  out.land_storage_slot = reinterpret_cast<const void *>(base + 0x5D1DAF8);
  out.land_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DAE0);
  out.provider_slot = reinterpret_cast<const void *>(base + 0x5C670F8);
  return out;
}
