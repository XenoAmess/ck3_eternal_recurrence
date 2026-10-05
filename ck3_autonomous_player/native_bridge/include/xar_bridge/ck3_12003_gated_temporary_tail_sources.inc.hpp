// Included inside xar::ck3_12002. The outer exact-build factory checks SHA.
struct ContextSourceGatedTemporaryTailBindingsV1 {
  bool enabled = false;
  const void *global_flag_slot = nullptr;
  const void *provider_slot = nullptr;
  const void *selector_global_slot = nullptr;
  const void *named_db_slot = nullptr;
  const void *minimum_slot = nullptr;
  const void *maximum_slot = nullptr;
  const void *threshold_pointer_slot = nullptr;
  const void *threshold_count_slot = nullptr;
  const void *character_storage_slot = nullptr;
  const void *character_fallback_slot = nullptr;
};
inline ContextSourceGatedTemporaryTailBindingsV1
BindGatedTemporaryTailSources12003(std::uintptr_t base) noexcept {
  ContextSourceGatedTemporaryTailBindingsV1 out{};
  if (!base) return out;
  out.enabled = true;
  out.global_flag_slot = reinterpret_cast<const void *>(base + 0x5CB87F8);
  out.provider_slot = reinterpret_cast<const void *>(base + 0x5C670F8);
  out.selector_global_slot = reinterpret_cast<const void *>(base + 0x5C82C68);
  out.named_db_slot = reinterpret_cast<const void *>(base + 0x5D1DD50);
  out.minimum_slot = reinterpret_cast<const void *>(base + 0x5C68FF0);
  out.maximum_slot = reinterpret_cast<const void *>(base + 0x5C68D10);
  out.threshold_pointer_slot = reinterpret_cast<const void *>(base + 0x5456EA8);
  out.threshold_count_slot = reinterpret_cast<const void *>(base + 0x5456EB4);
  out.character_storage_slot = reinterpret_cast<const void *>(base + 0x5C67568);
  out.character_fallback_slot = reinterpret_cast<const void *>(base + 0x5C67570);
  return out;
}
