// Included inside namespace xar::ck3_12002 before ContextSourceBindingsV1.
struct ContextSourceUncachedRecipientBindingsV1 {
  bool enabled = false;
  const void *first_registry_slot = nullptr, *first_fallback_slot = nullptr;
  const void *second_registry_slot = nullptr, *second_fallback_slot = nullptr;
  const void *fallback_key_slot = nullptr;
  const void *cap_slot = nullptr;
  const void *active_flag4_multiplier_slot = nullptr;
  const void *active_other_multiplier_slot = nullptr;
  const void *seed_boost_multiplier_slot = nullptr;
  const void *positive_fallback_slot = nullptr, *negative_fallback_slot = nullptr;
};
inline ContextSourceUncachedRecipientBindingsV1 BindUncachedRecipientSources12003(
    std::uintptr_t base) noexcept {
  const auto at = [base](std::uintptr_t rva) {
    return reinterpret_cast<const void *>(base + rva);
  };
  return {true, at(0x5D1E300), at(0x5D1E2E0), at(0x5D1DE88),
      at(0x5D1DE00), at(0x5D1E318), at(0x5C697EC), at(0x5C68CD0),
      at(0x5C69708), at(0x5C69710), at(0x5D1F6C0), at(0x5D1E288)};
}
