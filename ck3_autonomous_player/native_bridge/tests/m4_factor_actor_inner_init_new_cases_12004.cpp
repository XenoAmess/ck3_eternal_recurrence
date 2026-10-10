// No main: central03/10's only fresh connected M4 compound calls this export.
#include "xar_bridge/m4_factor_actor_inner_init_12004.hpp"

#include <algorithm>
#include <cstring>
#include <stdexcept>

namespace xar::ck3_12004 {
namespace {
constexpr std::string_view sha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
constexpr std::uintptr_t module = 0x140000000;
constexpr std::uintptr_t receiver = 0x20000000;
constexpr std::uintptr_t storage = 0x30000000;
constexpr std::uintptr_t slots = 0x31000000;
constexpr std::uintptr_t fallback = 0x32000000;
constexpr std::uint32_t actor_id = 0xA5000002;
constexpr std::uint64_t frame = 0x123456789ABCDEF0;

void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}

template <class T, std::size_t N>
T Value(const std::array<std::byte, N> &raw, std::size_t offset) {
  T output{};
  std::memcpy(&output, raw.data() + offset, sizeof(output));
  return output;
}

struct Atom {
  std::uintptr_t address;
  std::size_t width;
  std::uint64_t bits;
};
struct RawActor {
  // Exact actual4 generation round-trip inputs used by08c; no constructor or
  // evaluator callback exists in this readonly access contract.
  std::array<Atom, 6> atoms{{
      {receiver + 0x18, 4, actor_id},
      {module + 0x5C67568, 8, storage},
      {module + 0x5C67570, 8, fallback},
      {storage + 0x20, 8, slots},
      {storage + 0x2C, 4, 3},
      {slots + 2 * 0x10 + 8, 8, receiver}}};
  static bool Read(void *context, std::uintptr_t address, void *output,
                   std::size_t width) noexcept {
    const auto &raw = *static_cast<RawActor *>(context);
    for (const auto &atom : raw.atoms) {
      if (atom.address == address && atom.width == width) {
        std::memcpy(output, &atom.bits, width);
        return true;
      }
    }
    return false;
  }
};
} // namespace

int RunActualContext8895D0NewCases12004() {
  int executed = 0;
  {
    M4FactorActorInnerInit12004 inner;
    Require(ProjectM4FactorActorInnerInit12004(module, sha, frame, inner) &&
            inner.complete_source && inner.module_base == module && inner.frame_key == frame,
            "8895d0_exact4_projection_metadata");
    Require(Value<std::uint32_t>(inner.raw, 8) == 8 &&
            Value<std::uint32_t>(inner.raw, 0xC) == 0 &&
            Value<std::uint64_t>(inner.raw, 0x18) == module + 0x448D2A0 &&
            Value<std::uint64_t>(inner.raw, 0xE0) == module + 0x54DE2E0,
            "8895d0_actual_current_capacity_and_pointers");
    Require(inner.self_pointer_patch_count == 2 &&
            inner.self_pointer_patches[0].offset == 0 && inner.self_pointer_patches[0].target == 0x20 &&
            inner.self_pointer_patches[1].offset == 0x10 && inner.self_pointer_patches[1].target == 0x18,
            "8895d0_source_self_relative_pointer_operations");
    for (std::size_t i = 0; i < inner.defined_bytes.size(); ++i) {
      const bool defined = i < 0x20 || (i >= 0xE0 && i < 0xE8);
      Require(inner.defined_bytes[i] == static_cast<std::uint8_t>(defined),
              "8895d0_exact40_defined_bytes_no_inline_or_padding_claim");
    }
    ++executed;
  }
  {
    M4FactorActorInnerInit12004 inner;
    Require(!ProjectM4FactorActorInnerInit12004(module, "different-image", frame, inner) &&
            !inner.complete_source && inner.self_pointer_patch_count == 0 &&
            std::all_of(inner.defined_bytes.begin(), inner.defined_bytes.end(),
                        [](std::uint8_t value) { return value == 0; }),
            "8895d0_wrong_image_remains_missing_source");
    ++executed;
  }
  {
    RawActor raw;
    M4FactorActorContextAccess12004 access{&raw, &RawActor::Read};
    M4FactorActorContextRequest12004 request{module, sha, receiver, frame};
    M4FactorActorContext12004 context;
    // Ordinary production overload obtains48c's projection internally.
    Require(ReadM4FactorActorContext12004(access, request, context) &&
            context.complete_source && context.actor_identity_qualified &&
            context.actor_full_id == actor_id && context.frame_key == frame &&
            context.context_receiver == receiver,
            "8895d0_connected08_production_context_join");
    const auto child = reinterpret_cast<std::uintptr_t>(context.raw.data()) + 0x18;
    Require(Value<std::uint64_t>(context.raw, 0x18) == child + 0x20 &&
            Value<std::uint64_t>(context.raw, 0x28) == child + 0x18 &&
            Value<std::uint32_t>(context.raw, 0x20) == 8 &&
            Value<std::uint32_t>(context.raw, 0x24) == 0 &&
            Value<std::uint64_t>(context.raw, 0xF8) == module + 0x54DE2E0,
            "8895d0_rebased_at_final_stable_outer_storage");
    Require(Value<std::uint64_t>(context.raw, 8) == static_cast<std::uint64_t>(actor_id),
            "8895d0_parent_zero_extends_complete_generation_id");
    for (std::size_t i = 0x38; i < 0xF8; ++i)
      Require(context.defined_bytes[i] == 0,
              "8895d0_connected_parent_keeps_inline_storage_undefined");
    ++executed;
  }
  {
    RawActor raw;
    M4FactorActorContextAccess12004 access{&raw, &RawActor::Read};
    M4FactorActorContextRequest12004 request{module, sha, receiver, frame};
    M4FactorActorInnerInit12004 other_frame;
    Require(ProjectM4FactorActorInnerInit12004(module, sha, frame + 1, other_frame),
            "8895d0_other_frame_source_projection_exists");
    M4FactorActorContext12004 context;
    Require(ReadM4FactorActorContext12004(access, request, other_frame, context) &&
            context.actor_identity_qualified && !context.complete_source &&
            context.actor_full_id == actor_id && context.frame_key == frame,
            "8895d0_other_frame_cannot_complete_current_inner_scope");
    ++executed;
  }
  return executed;
}
} // namespace xar::ck3_12004
