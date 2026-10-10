#include "xar_bridge/m4_subobject_predicate_12004.hpp"

namespace xar::ck3_12004 {

bool ReadM4SubobjectPredicate12004(
    const construction_owner_mode3::RawReceiverAccessV1 &access,
    std::uintptr_t actual_subobject, std::uint64_t unchanged_snapshot_revision,
    bool &out, M4SubobjectPredicateSource12004 *source) noexcept {
  using construction_owner_mode3::RawReceiverReadV1;
  M4SubobjectPredicateSource12004 captured;
  captured.original_subobject_identity = actual_subobject;
  captured.unchanged_snapshot_revision = unchanged_snapshot_revision;
  const auto publish = [&](bool complete) noexcept {
    captured.source_complete = complete;
    if (source) *source = captured;
    return complete;
  };
  if (!access.exact_12004_bound || !access.read_memory || !actual_subobject)
    return publish(false);
  std::uint32_t count = 0;
  if (!RawReceiverReadV1(access, actual_subobject, 0x1C, count)) return publish(false);
  captured.count_1c_raw_u32 = count;
  std::uintptr_t selected = 0;
  if (count != 0) {
    std::uintptr_t data = 0;
    if (!RawReceiverReadV1(access, actual_subobject, 0x10, data)) return publish(false);
    captured.first_data_identity = data;
    if (!RawReceiverReadV1(access, data, 0, selected)) return publish(false);
  } else if (!RawReceiverReadV1(access, access.module_base, 0x5D1E320, selected)) {
    return publish(false);
  }
  captured.selected_object_identity = selected;
  std::uint32_t magic = 0;
  if (!RawReceiverReadV1(access, selected, 0x38, magic)) return publish(false);
  captured.selected_magic_38_raw_u32 = magic;
  if (magic != 0x4744624FU) {
    captured.output_al = std::uint8_t{0};
    out = false;
    return publish(true);
  }
  // Native reloads RCX+10 after the magic branch, including its zero-count
  // path. Keep that operand distinct from the first selected-object load.
  std::uintptr_t data = 0;
  if (!RawReceiverReadV1(access, actual_subobject, 0x10, data)) return publish(false);
  captured.flag_data_identity = data;
  std::uint8_t flag = 0;
  if (!RawReceiverReadV1(access, data, 8, flag)) return publish(false);
  captured.flag_08_raw_u8 = flag;
  captured.output_al = flag != 0 ? std::uint8_t{1} : std::uint8_t{0};
  out = flag != 0;
  return publish(true);
}

bool ReadM4SubobjectPredicateAdapter12004(
    void *context, const construction_owner_mode3::RawReceiverAccessV1 &access,
    std::uintptr_t actual_subobject, std::uint64_t unchanged_snapshot_revision,
    bool &out) noexcept {
  (void)context;
  return ReadM4SubobjectPredicate12004(
      access, actual_subobject, unchanged_snapshot_revision, out);
}

} // namespace xar::ck3_12004
