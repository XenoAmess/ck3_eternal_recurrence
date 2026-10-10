#include "xar_bridge/construction_owner_mode3_inputs_12004.hpp"
#include "xar_bridge/construction_owner_mode3_raw_eax_28be0b0_12004.hpp"
#include "xar_bridge/construction_owner_mode3_m4_12004.hpp"
#include "xar_bridge/construction_actual_2c42930_return_12004.hpp"
#include "xar_bridge/title_selected_full_id_12004.hpp"
#include "xar_bridge/returned_selector_28c2df0_12004.hpp"
#include "xar_bridge/construction_owner_factor_2b9cba0_12004.hpp"
#include "xar_bridge/construction_owner_modifier_4e_c86670_12004.hpp"
#include "xar_bridge/m4_factor_actor_context_12004.hpp"
#include "xar_bridge/construction_scaled_key_2c4d530_12004.hpp"
#include "xar_bridge/construction_character_modifier_2c4d1d0_12004.hpp"
#include "xar_bridge/construction_owner_mode3_context_scalar_12004.hpp"
#include "xar_bridge/construction_context_key_2c23340_12004.hpp"
#include "xar_bridge/construction_numeric_helper_2c39b80_12004.hpp"
#include "xar_bridge/construction_context_factor_2c399c0_12004.hpp"
#include "xar_bridge/construction_context_first_qword_24d3260_12004.hpp"
#include "xar_bridge/construction_context_predicate_2c25010_12004.hpp"
#include "xar_bridge/construction_pointer_membership_30a6080_12004.hpp"
#include "xar_bridge/construction_collection_predicate_a11cc0_12004.hpp"
#include "xar_bridge/loaded_singleton_d2be00_12004.hpp"
#include "xar_bridge/pointer_key_predicate_31c1d10_12004.hpp"
#include "xar_bridge/ck3_12004_person_first_title_vector.hpp"
#include <algorithm>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {

bool CopyAddress(void *context, std::uintptr_t address, void *out,
                 std::size_t count) noexcept {
  const auto *access = static_cast<const LoadedInputAccessV1 *>(context);
  if (!access || !access->read_memory || !address) return false;
  try {
    return access->read_memory(access->context,
        reinterpret_cast<const void *>(address), out, count);
  } catch (...) { return false; }
}

bool CopyRawAddress(void *context, const void *address, void *out,
                   std::size_t count) noexcept {
  return CopyAddress(context, reinterpret_cast<std::uintptr_t>(address), out, count);
}

bool ReadTitleChild(void *, const RawReceiverAccessV1 &access,
                    std::uintptr_t title, std::uintptr_t &out) noexcept {
  const LoadedInputAccessV1 loaded{access.context, access.read_memory,
                                   access.exact_12004_bound};
  TitleSelectedFullIdAccess12004 selected{
      const_cast<LoadedInputAccessV1 *>(&loaded), CopyAddress,
      access.module_base, access.exact_12004_bound};
  const RawTitleReturnAccessV1 child{access.context, access.read_memory,
      access.module_base, access.exact_12004_bound, &selected,
      ReadTitleSelectedFullIdAdapter12004};
  const auto value = ReadActual2C42930ReturnV1(child, title);
  if (!value.observed) return false;
  out = value.returned_pointer;
  return true;
}

bool ReadCharacterScalar(void *, const RawReceiverAccessV1 &access,
    std::uintptr_t character, std::uint16_t key, std::uintptr_t detail,
    std::int64_t scale, std::int64_t &out) noexcept {
  const auto value = ReadCharacterModifier2C4D1D012004(
      access, character, key, detail, scale);
  if (!value.ready || !value.value_raw_q64.has_value()) return false;
  out = *value.value_raw_q64;
  return true;
}

bool ReadLateReceiver(void *, const RawReceiverAccessV1 &access,
    const ContextPredicateInputsV1 &inputs, std::uintptr_t receiver,
    std::uintptr_t &out) noexcept {
  if (receiver != inputs.raw_receiver_pointer) return false;
  const LoadedInputAccessV1 loaded{access.context, access.read_memory,
                                  access.exact_12004_bound};
  const auto binding = BindPersonCarrierDirect12004(access.module_base,
      "1.20.0.4", kMode3InputSourcePin12004, CopyRawAddress,
      const_cast<LoadedInputAccessV1 *>(&loaded));
  try {
    const auto value = ReadPersonFirstTitleVectorReceiverForCharacter12004(
        binding, receiver);
    if (!value.ready || !value.selected_identity.has_value()) return false;
    out = *value.selected_identity; // A source-observed zero stays zero.
    return true;
  } catch (...) { return false; }
}

bool ReadLastPredicate(void *, const RawReceiverAccessV1 &access,
    const ContextPredicateInputsV1 &, std::uintptr_t singleton,
    std::uintptr_t first, bool &out) noexcept {
  const auto value = ReadPointerKeyPredicate31C1D10V1(access, singleton, first);
  if (!value.value.has_value()) return false;
  out = *value.value;
  return true;
}

std::int64_t AddRaw(std::int64_t a, std::int64_t b) noexcept {
  return SignedBitsV1(static_cast<std::uint64_t>(a) +
                      static_cast<std::uint64_t>(b));
}

std::int64_t SubRaw(std::int64_t a, std::int64_t b) noexcept {
  return SignedBitsV1(static_cast<std::uint64_t>(a) -
                      static_cast<std::uint64_t>(b));
}

} // namespace

ConstructionOwnerMode3InputsV1 ReadConstructionOwnerMode3InputsV1(
    const LoadedInputAccessV1 &access, const Mode3CurrentInputRequestV1 &request,
    const Mode3SignedEaxChildV1 &piety_child,
    const Mode3SignedEaxChildV1 &reduction_child) {
  ConstructionOwnerMode3InputsV1 out;
  out.snapshot_revision = request.snapshot_revision;
  out.province_id = request.expected_province_id;
  out.province_pointer = request.province_pointer;
  const auto fail = [&](std::string_view reason) {
    if (out.unavailable_input.empty()) out.unavailable_input = reason;
  };
  if (!request.exact_12004_bound || !access.exact_12004_bound ||
      !request.module_base || !access.read_memory) {
    fail("actual4_read_binding_unavailable");
    return out;
  }
  std::int32_t province_id = -1;
  if (request.expected_province_id <= 0 ||
      !ReadOffsetV1(access, request.province_pointer, 0x10, province_id) ||
      province_id != request.expected_province_id ||
      !AddOffsetV1(request.province_pointer, 0x620, out.slots_pointer) ||
      !ReadOffsetV1(access, out.slots_pointer, 0xF0, out.context_pointer)) {
    fail("actual_province_slots_binding_unavailable");
    return out;
  }
  std::int64_t publisher = 0;
  if (ReadOffsetV1(access, request.province_pointer, 0x718, publisher))
    out.loaded_publisher_718_raw = publisher;
  const auto key3f = ReadLoadedKey3FInputV1(access, request.province_pointer,
                                          request.expected_province_id);
  if (key3f.observed) out.loaded_key_3f_raw = key3f.signed_qword_raw;
  else fail("direct_key3f_input_unavailable");
  if (!ReadOffsetV1(access, out.context_pointer, 0x848, out.context_object_848))
    fail("actual_context_848_copy_unavailable");
  const RawReceiverAccessV1 raw{access.context, access.read_memory,
                               request.module_base, true};
  const auto receiver = ReadAggregateRawReceiverV1(raw, request.province_pointer,
      request.expected_province_id, {nullptr, ReadTitleChild});
  if (receiver.observed) out.returned_receiver_pointer = receiver.returned_receiver_pointer;
  else fail("actual2467660_return_unavailable");
  out.inputs_observed = true;
  const auto component = [&](std::uint32_t rva, std::uint16_t key,
      std::optional<std::int64_t> value, std::string_view missing) {
    out.components.push_back({rva, key, true, value,
                               value ? std::string{} : std::string(missing)});
    if (!value) fail(missing);
    return value;
  };
  const auto character_key = [&](std::uint16_t key) {
    const auto value = ReadCharacterModifier2C4D1D012004(
        raw, out.returned_receiver_pointer, key, 0, 100000);
    return component(0x2C4D530, key,
        value.ready ? value.value_raw_q64 : std::nullopt,
        "character_collection_key_unavailable");
  };
  const ReadContextScalarChild2C4D1D0V1 scalar_child{nullptr, ReadCharacterScalar, true};
  const auto context_scalar = [&](std::uint16_t key) {
    const auto value = ReadContextScalar2C82340V1(raw, out.context_object_848,
                                                key, 0, scalar_child);
    return component(0x2C82340, key,
        value.observed ? value.raw_qword : std::nullopt,
        "context_scalar_key_unavailable");
  };
  const auto a2 = character_key(0xA2);
  const auto a5 = context_scalar(0xA5);

  // Literal2468E6A..2468F3D resolves two full DWORD IDs before selecting
  // A3/A4 and A6/A7. Object+4B8 comparison is unnamed, not a government label.
  std::uintptr_t store = 0, fallback = 0, first = 0, second = 0;
  std::uint32_t first_id = 0, second_id = 0;
  std::int32_t first_scalar = 0, second_scalar = 0;
  bool matched = false;
  bool selector_ready = ReadOffsetV1(access, request.module_base, 0x5D242F8, store) &&
      ReadOffsetV1(access, request.module_base, 0x5C67670, fallback);
  first = second = fallback;
  if (selector_ready && store) {
    selector_ready = ReadOffsetV1(access, out.context_object_848, 0x384, first_id) &&
        ReadRawReceiverRegistryV1(raw, store, first_id, 8, fallback, first, matched);
  }
  if (selector_ready) selector_ready = ReadOffsetV1(access, first, 0x4B8, first_scalar);
  if (selector_ready && store) {
    selector_ready = ReadOffsetV1(access, out.returned_receiver_pointer, 0xB4, second_id) &&
        ReadRawReceiverRegistryV1(raw, store, second_id, 8, fallback, second, matched);
  }
  if (selector_ready) selector_ready = ReadOffsetV1(access, second, 0x4B8, second_scalar);
  std::optional<std::int64_t> a3, a6;
  if (selector_ready) {
    const bool unequal = first_scalar != second_scalar;
    out.selected_a3_or_a4_key = static_cast<std::uint16_t>(0xA3 + unequal);
    out.selected_a6_or_a7_key = static_cast<std::uint16_t>(0xA6 + unequal);
    a3 = character_key(*out.selected_a3_or_a4_key);
    a6 = context_scalar(*out.selected_a6_or_a7_key);
  } else fail("actual_key_selection_4b8_inputs_unavailable");
  const auto k1e9_source = ReadContextNumericKey2C23340V1(
      access, request.module_base, out.context_pointer, 0x1E9);
  const auto k1e9 = component(0x2C23340, 0x1E9,
      k1e9_source.observed ? k1e9_source.signed_qword_raw : std::nullopt,
      "context_key1e9_unavailable");
  std::uintptr_t key_root = 0, key_object = 0;
  std::uint16_t dynamic_key = 0;
  std::optional<std::int64_t> dynamic;
  if (ReadOffsetV1(access, out.context_pointer, 0x20, key_root) &&
      ReadOffsetV1(access, key_root, 0xB8, key_object) &&
      ReadOffsetV1(access, key_object, 0x78E, dynamic_key)) {
    out.context_dynamic_key = dynamic_key;
    const auto value = ReadContextNumericKey2C23340V1(
        access, request.module_base, out.context_pointer, dynamic_key);
    dynamic = component(0x2C23340, dynamic_key,
        value.observed ? value.signed_qword_raw : std::nullopt,
        "context_dynamic_key_unavailable");
  } else fail("context_dynamic_key_operand_unavailable");

  //2468FD3..2469017 searches only16-byte records for the actual slots first
  // pointer; a miss consumes the source's loaded inline default +8Q64.
  std::uintptr_t first_slot = 0, entries = 0;
  std::int32_t count = 0;
  std::optional<std::int64_t> association;
  if (ReadOffsetV1(access, out.slots_pointer, 0, first_slot) &&
      ReadOffsetV1(access, out.context_object_848, 0x310, entries) &&
      ReadOffsetV1(access, out.context_object_848, 0x31C, count) &&
      count >= 0 && count <= 4096) {
    std::uintptr_t selected = 0;
    bool copies_ready = true;
    for (std::int32_t i = 0; i < count; ++i) {
      std::uintptr_t candidate = 0;
      if (!ReadOffsetV1(access, entries, static_cast<std::size_t>(i) * 16, candidate)) {
        copies_ready = false; break;
      }
      if (candidate == first_slot) {
        copies_ready = AddOffsetV1(entries, static_cast<std::size_t>(i) * 16, selected);
        break;
      }
    }
    std::int64_t value = 0;
    if (copies_ready && (selected ? ReadOffsetV1(access, selected, 8, value)
        : ReadOffsetV1(access, request.module_base, 0x5C96180, value))) association = value;
  }
  association = component(0x2468FD3, 0, association, "context310_association_unavailable");
  const auto numeric = ReadConstructionNumericHelper2C39B80V1(access,
      request.province_pointer, request.expected_province_id,
      request.module_base, request.snapshot_revision);
  const auto numeric_factor = component(0x2C39B80, 0,
      numeric.observed && numeric.conditional_arithmetic
          ? std::optional<std::int64_t>(numeric.conditional_arithmetic->output_raw)
          : std::nullopt, "numeric_2c39b80_unavailable");

  std::int32_t piety = 0;
  if (piety_child.actual_12004_source_closed && piety_child.read && receiver.observed &&
      piety_child.read(piety_child.context, raw, out.returned_receiver_pointer,
                       request.snapshot_revision, piety))
    out.child_28be0b0_signed_eax = piety;
  else fail("source_child28be0b0_unavailable");
  std::uintptr_t collection = 0;
  std::optional<std::int64_t> k46, k1ea;
  if (out.child_28be0b0_signed_eax && AddOffsetV1(out.context_pointer, 0x30, collection)) {
    const auto scale = static_cast<std::int64_t>(piety) * 100000;
    const auto value46 = ReadScaledCollectionKey12004(access, collection, 0x46, scale, 0, 0);
    const auto value1ea = ReadScaledCollectionKey12004(access, collection, 0x1EA, scale, 0, 0);
    k46 = component(0x2C4D530, 0x46, value46.scaled_value_raw_q64,
                    "context_key46_unavailable");
    k1ea = component(0x2C4D530, 0x1EA, value1ea.scaled_value_raw_q64,
                     "context_key1ea_unavailable");
  }
  const auto selector_binding = BindReturnedSelector28C2DF012004(request.module_base,
      "1.20.0.4", kMode3InputSourcePin12004, CopyAddress,
      const_cast<LoadedInputAccessV1 *>(&access));
  const auto object = ResolveReturnedObject28C2DF012004(selector_binding,
      out.returned_receiver_pointer, request.snapshot_revision);
  const ReadContextPredicateChildrenV1 predicate_children{nullptr,
      ReadConstructionPointerMembership30A6080ChildV1,
      ReadConstructionCollectionPredicateA11CC0ChildV1, ReadLateReceiver,
      ReadLoadedD2BE00ContextChild12004, ReadLastPredicate};
  const auto predicate = ReadConstructionContextPredicate2C25010V1(
      raw, receiver, object, request.snapshot_revision, predicate_children);
  out.context_predicate_2c25010 = predicate.value;
  if (!predicate.value) fail("actual_context_predicate_unavailable");

  const auto context_inputs = ReadContextFactor2C399C0InputsV1(access,
      request.module_base, out.context_pointer, request.snapshot_revision);
  const auto provider = ReadContextFirstQword24D3260V1(access,
      request.module_base, context_inputs.context_object, request.snapshot_revision);
  const auto context_factor = EvaluateContextFactor2C399C0V1(context_inputs, provider.provider);
  out.context_factor_raw = context_factor.factor_qword_raw;
  if (!out.context_factor_raw) fail("actual_context_factor_unavailable");

  // Factor source: same object identity, one copied4D6 byte, conditional4E
  // constant/zero reader. A dynamic expression has no production witness and
  // remains unavailable; no evaluator or initialized-zero substitute is used.
  ConstructionOwnerFactorInputs12004 owner_inputs;
  owner_inputs.binding = {object.input_receiver, object.returned_object,
                          object.frame_key, object.source_ready};
  std::uint8_t selector_byte = 0;
  if (object.source_ready && ReadOffsetV1(access, object.returned_object, 0x4D6, selector_byte)) {
    owner_inputs.selector_byte_4d6 = selector_byte;
    if (selector_byte == 5) {
      M4FactorActorContext12004 actor_context;
      const M4FactorActorContextAccess12004 actor_access{
          const_cast<LoadedInputAccessV1 *>(&access), CopyAddress};
      const M4FactorActorContextRequest12004 actor_request{
          request.module_base, kMode3InputSourcePin12004,
          out.returned_receiver_pointer, request.snapshot_revision};
      if (ReadM4FactorActorContext12004(actor_access, actor_request, actor_context)) {
        const auto modifier = ReadConstructionOwnerModifier4E12004(
            {request.module_base, kMode3InputSourcePin12004, CopyAddress,
             const_cast<LoadedInputAccessV1 *>(&access)}, actor_context);
        owner_inputs.modifier_4e = modifier.factor_input;
      }
    }
  }
  const auto owner_factor = EvaluateNullDetailFactor12004(owner_inputs);
  out.owner_factor_raw = owner_factor.factor_raw;
  if (!out.owner_factor_raw) fail("actual_owner_factor_unavailable");

  if (a2 && a5 && a3 && a6 && k1e9 && dynamic && association && numeric_factor) {
    auto factor = AddRaw(*a6, 100000);
    factor = AddRaw(factor, AddRaw(*a2, *a5));
    factor = AddRaw(factor, *a3);
    factor = AddRaw(factor, *k1e9);
    factor = AddRaw(factor, *dynamic);
    factor = AddRaw(factor, *association);
    factor = AddRaw(factor, SubRaw(*numeric_factor, 100000));
    bool parent_factor_ready = true;
    if (predicate.value && *predicate.value) {
      std::uint8_t title_flag = 0;
      std::uint32_t title_reference = 0;
      if (!ReadOffsetV1(access, receiver.first_title_pointer, 0x130, title_flag) ||
          (!title_flag && !ReadOffsetV1(access, receiver.first_title_pointer,
                                      0x12C, title_reference))) {
        fail("actual_predicate_title_branch_unavailable");
        parent_factor_ready = false;
      } else if (!title_flag && title_reference == 0xFFFFFFFFu) {
        std::int32_t reduction = 0;
        if (!reduction_child.actual_12004_source_closed || !reduction_child.read ||
            !reduction_child.read(reduction_child.context, raw,
                out.returned_receiver_pointer, request.snapshot_revision, reduction)) {
          fail("source_child28b9300_unavailable");
          parent_factor_ready = false;
        } else {
          out.child_28b9300_signed_eax = reduction;
          if (reduction > 0) {
            std::int64_t loaded_scale = 0, loaded_cap = 0;
            if (!ReadOffsetV1(access, request.module_base, 0x5C69470, loaded_scale) ||
                !ReadOffsetV1(access, request.module_base, 0x5C69488, loaded_cap)) {
              fail("actual_reduction_loaded_scalar_unavailable");
              parent_factor_ready = false;
            } else {
              const auto reduced = std::min(WrappedProductV1(reduction, loaded_scale), loaded_cap);
              factor = SignedScaleProduct100000V1(factor, SubRaw(100000, reduced));
            }
          }
        }
      }
    }
    if (parent_factor_ready) out.factor_before_context = factor;
    if (out.loaded_key_3f_raw && k46 && k1ea && predicate.value &&
        out.context_factor_raw && out.owner_factor_raw && out.unavailable_input.empty()) {
      auto base = SignedScaleProduct100000V1(*out.loaded_key_3f_raw, 100000);
      base = AddRaw(base, *k46);
      base = AddRaw(base, *k1ea);
      if (!*predicate.value) base = 0;
      factor = SignedScaleProduct100000V1(factor, *out.context_factor_raw);
      factor = SignedScaleProduct100000V1(factor, *out.owner_factor_raw);
      const auto aggregate = SignedScaleProduct100000V1(base, factor);
      out.conditional_aggregate_raw = std::max<std::int64_t>(0, aggregate);
      out.all_reached_inputs_observed = true;
    }
  }
  // The current query performs full frame equality around this reader. Its
  // required Province/slots/context bookends are also preserved here.
  std::int32_t after_id = -1;
  std::uintptr_t after_context = 0, after_object = 0;
  if (!ReadOffsetV1(access, request.province_pointer, 0x10, after_id) ||
      after_id != request.expected_province_id ||
      !ReadOffsetV1(access, out.slots_pointer, 0xF0, after_context) ||
      after_context != out.context_pointer ||
      !ReadOffsetV1(access, out.context_pointer, 0x848, after_object) ||
      after_object != out.context_object_848) {
    fail("actual_source_pointer_bookends_changed");
    out.inputs_observed = false;
    out.all_reached_inputs_observed = false;
    out.conditional_aggregate_raw.reset();
  }
  return out;
}

ConstructionOwnerMode3InputsV1 ReadConstructionOwnerMode3InputsV1(
    const LoadedInputAccessV1 &access, const Mode3CurrentInputRequestV1 &request) {
  return ReadConstructionOwnerMode3InputsV1(access, request,
      {nullptr, ReadRaw28BE0B0EaxAdapter12004, true},
      {nullptr, ReadMode3M4SignedEaxChildV1, true});
}

} // namespace xar::ck3_12004::construction_owner_mode3
