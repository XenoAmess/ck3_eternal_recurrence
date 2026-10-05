// Included inside xar::ck3_12002; the outer factory validates the exact build once.
struct ContextSourceProvider192And2920850BindingsV1 {
  bool enabled = false;
  const void *provider_slot = nullptr;
  const void *upper_slot = nullptr;
  const void *lower_slot = nullptr;
  const void *provider_fallback_slot = nullptr;
  const void *list_default_header = nullptr;
  const void *list_default_guard_slot = nullptr;
  const void *object_storage_slot = nullptr;
  const void *object_fallback_slot = nullptr;
  const void *rite_storage_slot = nullptr;
  const void *rite_fallback_slot = nullptr;
  const void *faith_storage_slot = nullptr;
  const void *faith_fallback_slot = nullptr;
  const void *mapped_default_pc = nullptr;
  const void *mapped_default_guard_slot = nullptr;
};
inline ContextSourceProvider192And2920850BindingsV1 BindProvider192And2920850Sources12003(std::uintptr_t base) {
  ContextSourceProvider192And2920850BindingsV1 out{};
  if (!base) return out;
  out.enabled = true;
  out.provider_slot = reinterpret_cast<const void *>(base + 0x5C670F8);
  out.upper_slot = reinterpret_cast<const void *>(base + 0x5C69FE4);
  out.lower_slot = reinterpret_cast<const void *>(base + 0x5C69FE0);
  out.provider_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1E0B0);
  out.list_default_header = reinterpret_cast<const void *>(base + 0x5D67E60);
  out.list_default_guard_slot = reinterpret_cast<const void *>(base + 0x5D67E58);
  out.object_storage_slot = reinterpret_cast<const void *>(base + 0x5D1EB60);
  out.object_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1EB90);
  out.rite_storage_slot = reinterpret_cast<const void *>(base + 0x5D1E2F8);
  out.rite_fallback_slot = reinterpret_cast<const void *>(base + 0x5C67670);
  out.faith_storage_slot = reinterpret_cast<const void *>(base + 0x5D1E300);
  out.faith_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1E2E0);
  out.mapped_default_pc = reinterpret_cast<const void *>(base + 0x5DC21B0);
  out.mapped_default_guard_slot = reinterpret_cast<const void *>(base + 0x5DC21A4);
  return out;
}
