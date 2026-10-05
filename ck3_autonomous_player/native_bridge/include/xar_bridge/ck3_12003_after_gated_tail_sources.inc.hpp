// Included inside xar::ck3_12002; outer factory validates exact SHA once.
struct ContextSourceAfterGatedTailBindingsV1 {
  bool enabled = false;
  const void *global_flag_slot = nullptr;
  const void *clock_slot = nullptr;
  const void *static_fifth_date = nullptr;
  const void *character_storage_slot = nullptr;
  const void *character_fallback_slot = nullptr;
  const void *position_storage_slot = nullptr;
  const void *position_fallback_slot = nullptr;
  const void *default_list_header = nullptr;
  const void *default_list_guard_slot = nullptr;
  const void *selector_a_storage_slot = nullptr;
  const void *selector_a_fallback_slot = nullptr;
  const void *selector_b_storage_slot = nullptr;
  const void *selector_b_fallback_slot = nullptr;
};
inline ContextSourceAfterGatedTailBindingsV1
BindAfterGatedTailSources12003(std::uintptr_t base) noexcept {
  ContextSourceAfterGatedTailBindingsV1 out{};
  if (!base) return out;
  out.enabled = true;
  out.global_flag_slot = reinterpret_cast<const void *>(base + 0x5CB87F8);
  out.clock_slot = reinterpret_cast<const void *>(base + 0x5C68C50);
  out.static_fifth_date = reinterpret_cast<const void *>(base + 0x4763CB8);
  out.character_storage_slot = reinterpret_cast<const void *>(base + 0x5C67568);
  out.character_fallback_slot = reinterpret_cast<const void *>(base + 0x5C67570);
  out.position_storage_slot = reinterpret_cast<const void *>(base + 0x5D1DD10);
  out.position_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DD08);
  out.default_list_header = reinterpret_cast<const void *>(base + 0x54E7220);
  out.default_list_guard_slot = reinterpret_cast<const void *>(base + 0x5D679E0);
  out.selector_a_storage_slot = reinterpret_cast<const void *>(base + 0x5D1E2F8);
  out.selector_a_fallback_slot = reinterpret_cast<const void *>(base + 0x5C67670);
  out.selector_b_storage_slot = reinterpret_cast<const void *>(base + 0x5D1E2F0);
  out.selector_b_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1E2E8);
  return out;
}
