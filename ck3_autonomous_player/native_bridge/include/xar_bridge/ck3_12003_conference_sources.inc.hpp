// Included inside namespace xar::ck3_12002 before ContextSourceBindingsV1.
struct ContextSourceConferenceBindingsV1 {
  bool enabled = false;
  const void *conf_registry_slot = nullptr;
  const void *conf_fallback_slot = nullptr;
  const void *relation_registry_slot = nullptr;
  const void *relation_fallback_slot = nullptr;
  const void *inline_default_pack = nullptr;
  const void *default_guard_slot = nullptr;
};
inline ContextSourceConferenceBindingsV1 BindConferenceSources12003(std::uintptr_t base) noexcept {
  ContextSourceConferenceBindingsV1 out{};
  if (!base) return out;
  out.enabled = true;
  out.conf_registry_slot = reinterpret_cast<const void *>(base + 0x5D1EB78);
  out.conf_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1EB50);
  out.relation_registry_slot = reinterpret_cast<const void *>(base + 0x5D1DAF0);
  out.relation_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DAE8);
  out.inline_default_pack = reinterpret_cast<const void *>(base + 0x54EBAB0);
  out.default_guard_slot = reinterpret_cast<const void *>(base + 0x5D71B94);
  return out;
}
