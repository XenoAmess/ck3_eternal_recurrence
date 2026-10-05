// Included inside xar::ck3_12002. Binding does not invoke the provider getter.
struct ProviderBucket291c5b2BindingsV1 {
  bool enabled = false;
  const void *provider_slot = nullptr;
  const void *factor_denominator_slot = nullptr;
  const void *native_fallback_slot = nullptr;
};
inline ProviderBucket291c5b2BindingsV1
BindProviderBucket291c5b2Sources12003(std::uintptr_t base) noexcept {
  ProviderBucket291c5b2BindingsV1 out{};
  if (!base) return out;
  out.enabled = true;
  out.provider_slot = reinterpret_cast<const void *>(base + 0x5C670F8);
  out.factor_denominator_slot = reinterpret_cast<const void *>(base + 0x5C68CE8);
  out.native_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1E0B0);
  return out;
}
