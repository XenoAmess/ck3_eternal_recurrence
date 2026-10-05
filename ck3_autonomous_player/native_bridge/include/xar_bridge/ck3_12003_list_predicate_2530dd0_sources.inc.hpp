// Included inside namespace xar::ck3_12002 before ContextSourceBindingsV1.
struct ContextSourceListPredicate2530dd0BindingsV1 {
  bool enabled = false;
  const void *default_inline_header = nullptr;
  const void *default_header_guard_slot = nullptr;
  const void *registry_storage_slot = nullptr;
  const void *registry_fallback_slot = nullptr;
  const void *named_binding_key_slot = nullptr;
};
inline ContextSourceListPredicate2530dd0BindingsV1 BindListPredicate2530dd0Sources12003(
    std::uintptr_t base) noexcept {
  const auto at = [base](std::uintptr_t rva) {
    return reinterpret_cast<const void *>(base + rva);
  };
  return {true, at(0x54E7180), at(0x5D67818), at(0x5D1DE68),
      at(0x5D1DE30), at(0x5D4C018)};
}
