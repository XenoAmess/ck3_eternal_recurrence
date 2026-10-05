// Included inside namespace xar::ck3_12002, before ContextSourceBindingsV1.
struct ContextSourceTraitStageBindingsV1 {
  bool enabled = false;
  const void *trait_database_slot = nullptr;
  const void *trait_definition_fallback_slot = nullptr;
  const void *definition_provider_slot = nullptr;
  const void *selector_a_storage_slot = nullptr;
  const void *selector_a_fallback_slot = nullptr;
  const void *selector_b_storage_slot = nullptr;
  const void *selector_b_fallback_slot = nullptr;
};
inline ContextSourceTraitStageBindingsV1 BindTraitStage291d46012003(
    std::uintptr_t base) noexcept {
  ContextSourceTraitStageBindingsV1 out{};
  if (!base) return out;
  out.enabled = true;
  out.trait_database_slot = reinterpret_cast<const void *>(base + 0x5C67528);
  out.trait_definition_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1E318);
  out.definition_provider_slot = reinterpret_cast<const void *>(base + 0x5C670F8);
  out.selector_a_storage_slot = reinterpret_cast<const void *>(base + 0x5D1E2F8);
  out.selector_a_fallback_slot = reinterpret_cast<const void *>(base + 0x5C67670);
  out.selector_b_storage_slot = reinterpret_cast<const void *>(base + 0x5D1E2F0);
  out.selector_b_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1E2E8);
  return out;
}
