// Included inside xar::ck3_12002. Exact-build binding; never calls getters.
struct ContextSourceMiddleHelpersBindingsV1 {
  bool enabled = false;
  const void *manager_slot = nullptr;
  const void *rank_fallback_slot = nullptr;
  const void *threshold_pointer_slots[4]{};
  const void *threshold_count_slots[4]{};
  const void *weight_default_pc = nullptr;
  const void *weight_default_guard_slot = nullptr;
  const void *subc_registry_slot = nullptr;
  const void *subc_fallback_slot = nullptr;
  const void *null_land_list_header = nullptr;
  const void *modifier_default_base_slot = nullptr;
};
inline ContextSourceMiddleHelpersBindingsV1 BindMiddleHelperSources12003(std::uintptr_t base) noexcept {
  ContextSourceMiddleHelpersBindingsV1 out{};
  if (!base) return out;
  out.enabled = true;
  out.manager_slot = reinterpret_cast<const void *>(base + 0x5D1F6D0);
  out.rank_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1E0B0);
  constexpr std::uintptr_t pointers[] = {0x5457EF8, 0x54582D8, 0x5458168, 0x5458818};
  constexpr std::uintptr_t counts[] = {0x5457F04, 0x54582E4, 0x5458174, 0x5458824};
  for (int i = 0; i < 4; ++i) {
    out.threshold_pointer_slots[i] = reinterpret_cast<const void *>(base + pointers[i]);
    out.threshold_count_slots[i] = reinterpret_cast<const void *>(base + counts[i]);
  }
  out.weight_default_pc = reinterpret_cast<const void *>(base + 0x5D67B90);
  out.weight_default_guard_slot = reinterpret_cast<const void *>(base + 0x5D67B80);
  out.subc_registry_slot = reinterpret_cast<const void *>(base + 0x5D1EB88);
  out.subc_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1EB40);
  out.null_land_list_header = reinterpret_cast<const void *>(base + 0x54596D8);
  out.modifier_default_base_slot = reinterpret_cast<const void *>(base + 0x5D203E0);
  return out;
}
