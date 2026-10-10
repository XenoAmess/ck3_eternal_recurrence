#include "xar_bridge/prisoner_cost_lane_9d7060_readonly_12004.hpp"

#include <array>
#include <cstring>
#include <map>
#include <stdexcept>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kImage = 0x140000000;
constexpr std::uintptr_t kLane = 0x300001000;
constexpr std::uintptr_t kNamed = 0x300002000;
constexpr std::uintptr_t kProvider = 0x300003000;
constexpr std::uintptr_t kVtable = 0x300004000;
constexpr std::uintptr_t kScopeRoot = 0x300005000;
constexpr std::uintptr_t kDescriptor = 0x300006000;

struct Memory {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  std::optional<std::int32_t> count_after_first_copy;
  std::size_t count_copies = 0;
  template <typename T> void Put(std::uintptr_t p, const T &v) {
    const auto *b = reinterpret_cast<const std::uint8_t *>(&v);
    for (std::size_t i = 0; i < sizeof(T); ++i) bytes[p + i] = b[i];
  }
  static bool Copy(void *context, const void *address, void *destination,
                   std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context);
    const auto p = reinterpret_cast<std::uintptr_t>(address);
    if (p == kLane + 0x14 && size == sizeof(std::int32_t) &&
        ++m.count_copies > 1 && m.count_after_first_copy) {
      std::memcpy(destination, &*m.count_after_first_copy, size);
      return true;
    }
    auto *b = static_cast<std::uint8_t *>(destination);
    for (std::size_t i = 0; i < size; ++i) {
      const auto found = m.bytes.find(p + i);
      if (found == m.bytes.end()) return false;
      b[i] = found->second;
    }
    return true;
  }
  PrisonerQuoteReadOnlyAccess12004 Access() { return {this, Copy, 16}; }
};

PrisonerCostLane9D7060Arguments12004 Arguments() {
  PrisonerCostLane9D7060Arguments12004 a;
  a.frame.executable_sha256 = kPrisonerQuoteSourceExecutableSha25612004;
  a.frame.module_base = kImage;
  a.frame.native_revision = 1;
  a.frame.query_sequence = 2;
  a.frame.proof_epoch = 3;
  a.frame.date_raw = 4;
  a.frame.jailer_full_id = 0x11000001;
  a.frame.prisoner_full_id = 0x22000002;
  a.frame.recipient_full_id = 0x33000003;
  a.frame.definition_identity = 0x300007000;
  a.frame.interaction_context_identity = 0x300008000;
  a.frame.original_scope_identity = 0x300009000;
  a.frame.roles_verified_in_owned_context = true;
  a.frame.same_frame_confirmed = true;
  a.lane_identity = kLane;
  a.descriptor_identity = kDescriptor;
  // No invented physical internal scope or support address.
  return a;
}

void NonProvider(Memory &m) {
  m.Put(kLane + 0xC0, std::int32_t{2});
  m.Put(kLane + 0xB8, std::uintptr_t{0});
  m.Put(kLane + 0xA8, std::uintptr_t{0});
}

PrisonerCostLaneConditionalResult12004 ProviderResult(
    const PrisonerCostLane9D7060Arguments12004 &args) {
  PrisonerCostLaneConditionalResult12004 r;
  r.frame = args.frame;
  r.lane_identity = args.lane_identity;
  r.internal_aliases = args.internal_aliases;
  r.descriptor_identity = args.descriptor_identity;
  r.receiver_identity = kProvider + 8;
  r.callback_identity = kImage + 0x123456;
  r.consumer_callsite_rva = 0x9D7141;
  r.source_result_ready = true;
  r.result_q64 = 250001;
  return r;
}

void Require(bool condition, const char *name) {
  if (!condition) throw std::runtime_error(name);
}
} // namespace

// This is one fragment of35's new connected-cost fixture, with no main and
// no independent execution or replay of old Army/calendar/role tests.
void RunPrisonerCostLane9D7060ReadonlyNewCases12004() {
  {
    Memory m;
    auto args = Arguments();
    m.Put(kLane + 0xC0, std::int32_t{0});
    m.Put(kLane + 0x98, std::int64_t{-7});
    const auto r = ReadPrisonerCostLane9D7060Readonly12004(m.Access(), args);
    Require(r.raw_temp_q64 == -7 && r.branch == "fixed_mode_zero" &&
            !r.provider_b8_identity, "cost_lane_mode_zero_needs_no_later_operands");
  }
  {
    Memory m; NonProvider(m);
    m.Put(kLane + 0x14, std::int32_t{0});
    m.Put(kLane + 0x98, std::int64_t{42});
    const auto r = ReadPrisonerCostLane9D7060Readonly12004(m.Access(), Arguments());
    Require(r.raw_temp_q64 == 42 && r.branch == "fixed_no_expression",
            "cost_lane_null_r9_mode_two_skips_interpolation");
  }
  {
    Memory m; NonProvider(m);
    m.Put(kLane + 0xA8, kNamed);
    m.Put(kNamed + 0x70, std::uintptr_t{0});
    m.Put(kNamed + 0x7B, std::uint8_t{1});
    m.Put(kNamed + 0x68, std::int64_t{-400001});
    const auto r = ReadPrisonerCostLane9D7060Readonly12004(m.Access(), Arguments());
    Require(r.raw_temp_q64 == -400001 && r.branch == "named" &&
            !r.expression_count_14_i32, "cost_lane_named_fixed_raw_q64");
  }
  {
    Memory m; NonProvider(m);
    m.Put(kLane + 0xA8, kNamed);
    m.Put(kNamed + 0x70, std::uintptr_t{0});
    m.Put(kNamed + 0x7B, std::uint8_t{0});
    const auto r = ReadPrisonerCostLane9D7060Readonly12004(m.Access(), Arguments());
    Require(r.raw_temp_q64 == 0 && r.named && !r.named->constant_raw_q64,
            "cost_lane_named_disabled_exact_zero_no_constant_copy");
  }
  {
    Memory m;
    auto args = Arguments();
    m.Put(kLane + 0xC0, std::int32_t{1});
    m.Put(kLane + 0xB8, kProvider);
    m.Put(kProvider + 8, kVtable);
    m.Put(kVtable + 0x30, std::uintptr_t{kImage + 0x123456});
    const auto unknown = ReadPrisonerCostLane9D7060Readonly12004(m.Access(), args);
    Require(!unknown.raw_temp_q64 && unknown.branch == "virtual_provider",
            "cost_lane_virtual_pointer_is_not_return_value");
    auto result = ProviderResult(args);
    const auto known = ReadPrisonerCostLane9D7060Readonly12004(m.Access(), args, &result);
    Require(known.raw_temp_q64 == 250001, "cost_lane_bound_conditional_provider_result");
    ++result.frame.query_sequence;
    const auto mismatched = ReadPrisonerCostLane9D7060Readonly12004(m.Access(), args, &result);
    Require(!mismatched.raw_temp_q64 &&
            mismatched.unavailable_reason == "cost_lane_dynamic_source_argument_mismatch",
            "cost_lane_other_frame_result_remains_unknown");
  }
  {
    Memory m; NonProvider(m);
    auto args = Arguments();
    args.internal_aliases.primary_scope = kScopeRoot;
    m.Put(kLane + 0x14, std::int32_t{-1});
    std::array<std::uint8_t, 16> root{};
    const std::uint16_t tag = 1;
    const std::int64_t payload = 321;
    std::memcpy(root.data(), &tag, sizeof(tag));
    std::memcpy(root.data() + 8, &payload, sizeof(payload));
    m.Put(kScopeRoot, root);
    const auto numeric = ReadPrisonerCostLane9D7060Readonly12004(m.Access(), args);
    Require(numeric.raw_temp_q64 == 321 && numeric.variant_tag_u16 == 1 &&
            numeric.variant && numeric.variant->source_result_ready,
            "cost_lane_owned_variant_numeric_payload");
    const std::uint16_t other_tag = 4;
    std::memcpy(root.data(), &other_tag, sizeof(other_tag));
    m.Put(kScopeRoot, root);
    m.Put(kLane + 0x98, std::int64_t{-500});
    const auto fallback = ReadPrisonerCostLane9D7060Readonly12004(m.Access(), args);
    Require(fallback.raw_temp_q64 == -500 && fallback.variant_tag_u16 == 4 &&
            fallback.branch == "fixed_nonnumeric_tag", "cost_lane_known_nonnumeric_uses_constant");
  }
  {
    Memory m; NonProvider(m);
    m.Put(kLane + 0x14, std::int32_t{-1});
    m.Put(kLane + 0x98, std::int64_t{999});
    const auto r = ReadPrisonerCostLane9D7060Readonly12004(m.Access(), Arguments());
    Require(!r.raw_temp_q64 && !r.variant_tag_u16 && r.variant &&
            !r.variant->source_result_ready, "cost_lane_unknown_tag_cannot_select_fallback");
  }
  {
    Memory m;
    auto args = Arguments();
    args.frame.same_frame_confirmed = false;
    m.Put(kLane + 0xC0, std::int32_t{0});
    m.Put(kLane + 0x98, std::int64_t{123});
    const auto r = ReadPrisonerCostLane9D7060Readonly12004(m.Access(), args);
    Require(!r.raw_temp_q64 && !r.mode_c0_i32,
            "cost_lane_unconfirmed_frame_is_unavailable");
  }
  {
    Memory m; NonProvider(m);
    m.Put(kLane + 0x14, std::int32_t{1});
    m.Put(kLane + 0x98, std::int64_t{999});
    m.count_after_first_copy = 0;
    const auto r = ReadPrisonerCostLane9D7060Readonly12004(m.Access(), Arguments());
    Require(!r.raw_temp_q64 && r.variant &&
            r.unavailable_reason == "cost_lane_variant_parent_count_changed_or_unavailable",
            "cost_lane_parent_child_count_view_mismatch_unknown");
  }
}
