// Included inside namespace xar::ck3_12002 before ContextSourceBindingsV1.
struct ContextSourceQualifier28bc0d0BindingsV1 {
  bool enabled = false;
  const void *manager_slot = nullptr;
  const void *fallback_definition_slot = nullptr;
};
inline ContextSourceQualifier28bc0d0BindingsV1 BindQualifier28bc0d0Sources12003(
    std::uintptr_t base) noexcept {
  return {true, reinterpret_cast<const void *>(base + 0x5D1E2B0),
      reinterpret_cast<const void *>(base + 0x5D1EBF8)};
}
