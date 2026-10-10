#include "xar_bridge/construction_context_first_qword_24d3260_12004.hpp"

#include <map>
#include <stdexcept>
#include <vector>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {
constexpr std::uintptr_t image = 0x10000000, context = 0x20000000;
constexpr std::uintptr_t first_registry = 0x21000000, first_entries = 0x21100000;
constexpr std::uintptr_t first_object = 0x21200000, first_fallback = 0x21300000;
constexpr std::uintptr_t second_registry = 0x22000000, second_entries = 0x22100000;
constexpr std::uintptr_t second_object = 0x22200000, second_fallback = 0x22300000;
constexpr std::uintptr_t linked = 0x23000000;
constexpr std::uint32_t first_id = UINT32_C(0xAB000003), second_id = UINT32_C(0xCD000007);
constexpr std::uint64_t frame = 91;

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

struct Memory {
  std::map<std::uintptr_t, std::vector<std::byte>> bytes;
  std::map<std::uintptr_t, std::size_t> reads;
  bool change_initial_on_second_read = false;

  template <typename T> void Put(std::uintptr_t address, T value) {
    std::vector<std::byte> data(sizeof(T));
    std::memcpy(data.data(), &value, sizeof(T));
    bytes[address] = data;
  }
};

bool Read(void *opaque, const void *pointer, void *out, std::size_t size) {
  auto &memory = *static_cast<Memory *>(opaque);
  const auto address = reinterpret_cast<std::uintptr_t>(pointer);
  const auto read_number = ++memory.reads[address];
  const auto found = memory.bytes.find(address);
  if (found == memory.bytes.end() || found->second.size() != size) return false;
  if (memory.change_initial_on_second_read && address == context + 0x398 && read_number == 2) {
    const std::int64_t changed = 10000001;
    std::memcpy(out, &changed, sizeof(changed));
    return true;
  }
  std::memcpy(out, found->second.data(), size);
  return true;
}

Memory Full(std::int64_t initial = 10000000, std::int64_t override_value = -7654321) {
  Memory memory;
  memory.Put(context + 0x398, initial);
  memory.Put(image + 0x5D1DAF8, first_registry);
  memory.Put(image + 0x5D1DAE0, first_fallback);
  memory.Put(context + 0x18, first_id);
  memory.Put(first_registry + 0x2C, std::uint32_t{20});
  memory.Put(first_registry + 0x20, first_entries);
  memory.Put(first_entries + 3 * 0x10 + 8, first_object);
  memory.Put(first_object + 0x10, first_id);
  memory.Put(first_object + 0x128, second_id);
  memory.Put(first_fallback + 0x128, second_id);
  memory.Put(image + 0x5C67568, second_registry);
  memory.Put(image + 0x5C67570, second_fallback);
  memory.Put(second_registry + 0x2C, std::uint32_t{20});
  memory.Put(second_registry + 0x20, second_entries);
  memory.Put(second_entries + 7 * 0x10 + 8, second_object);
  memory.Put(second_object + 0x18, second_id);
  memory.Put(second_object + 0x1C0, linked);
  memory.Put(second_fallback + 0x1C0, std::uintptr_t{0});
  memory.Put(linked + 0x4AB, std::uint8_t{0x80});
  memory.Put(image + 0x5C69698, override_value);
  return memory;
}

ContextFirstQword24D3260ObservationV1 Observe(Memory &memory) {
  LoadedInputAccessV1 access{&memory, &Read, true};
  return ReadContextFirstQword24D3260V1(access, image, context, frame);
}
} // namespace

void VerifyContextFirstQword24D3260ConnectedCasesV1() {
  // 1: Signed negative values bypass every registry/global and remain raw.
  {
    Memory memory;
    memory.Put(context + 0x398, std::numeric_limits<std::int64_t>::min());
    const auto out = Observe(memory);
    Require(out.provider.source_ready && out.provider.first_qword_raw ==
                std::numeric_limits<std::int64_t>::min() &&
                out.path == ContextFirstQword24D3260PathV1::below_signed_threshold &&
                out.scalar_source_reads == 1 && memory.reads.size() == 1,
            "signed initial fast path visited unrelated fields or lost raw bits");
  }
  // 2: Native zero is an observed value, not an unread/default value.
  {
    Memory memory;
    memory.Put(context + 0x398, std::int64_t{0});
    const auto out = Observe(memory);
    Require(out.provider.source_ready && out.provider.first_qword_raw == 0 &&
                !out.first_registry.visited && !out.second_registry.visited,
            "observed initial zero became unavailable or forced registry reads");
  }
  // 3: Last below-threshold value does not touch absent lookup inputs.
  {
    Memory memory;
    memory.Put(context + 0x398, std::int64_t{9999999});
    const auto out = Observe(memory);
    Require(out.provider.source_ready && out.provider.first_qword_raw == 9999999,
            "signed threshold comparison has the wrong boundary");
  }
  // 4: Exact threshold plus high-bit full IDs selects signed loaded override.
  {
    auto memory = Full();
    const auto out = Observe(memory);
    Require(out.provider.source_ready && out.provider.first_qword_raw == -7654321 &&
                out.path == ContextFirstQword24D3260PathV1::loaded_override &&
                out.first_registry.resolved_by_full_id && out.second_registry.resolved_by_full_id &&
                out.provider.frame_key == frame && out.provider.context_object == context &&
                out.provider.source_pin == kContextFactor2C399C0SourcePinV1,
            "actual full-ID override or direct20 provider binding was lost");
  }
  // 5: A loaded override of zero stays qualified.
  {
    auto memory = Full(10000000, 0);
    const auto out = Observe(memory);
    Require(out.provider.source_ready && out.override_qword_raw == 0 &&
                out.provider.first_qword_raw == 0,
            "loaded override zero was treated as missing");
  }
  // 6: Known null link returns initial without reading the absent byte/override.
  {
    auto memory = Full();
    memory.Put(second_object + 0x1C0, std::uintptr_t{0});
    memory.bytes.erase(linked + 0x4AB);
    memory.bytes.erase(image + 0x5C69698);
    const auto out = Observe(memory);
    Require(out.provider.source_ready && out.provider.first_qword_raw == 10000000 &&
                out.path == ContextFirstQword24D3260PathV1::null_link &&
                !out.linked_object_gate_byte && !out.override_qword_raw,
            "null link did not mirror the native local return branch");
  }
  // 7: Known zero byte returns initial without an override read.
  {
    auto memory = Full();
    memory.Put(linked + 0x4AB, std::uint8_t{0});
    memory.bytes.erase(image + 0x5C69698);
    const auto out = Observe(memory);
    Require(out.provider.source_ready && out.provider.first_qword_raw == 10000000 &&
                out.path == ContextFirstQword24D3260PathV1::zero_gate_byte,
            "zero gate byte was confused with an unread byte");
  }
  // 8: Same low24 first index, different generation uses exact fallback.
  {
    auto memory = Full();
    memory.Put(first_object + 0x10, UINT32_C(0xAC000003));
    const auto out = Observe(memory);
    Require(out.provider.source_ready && out.first_registry.used_fallback &&
                !out.first_registry.resolved_by_full_id &&
                out.first_registry.selected_object == first_fallback,
            "first registry accepted a stale full generation");
  }
  // 9: Second generation mismatch uses fallback and its own null-link branch.
  {
    auto memory = Full();
    memory.Put(second_object + 0x18, UINT32_C(0xCE000007));
    const auto out = Observe(memory);
    Require(out.provider.source_ready && out.second_registry.used_fallback &&
                out.second_registry.selected_object == second_fallback &&
                out.provider.first_qword_raw == 10000000,
            "second registry generation fallback was not consumed literally");
  }
  // 10: Known null storage takes fallback without manufacturing/read IDs.
  {
    auto memory = Full();
    memory.Put(image + 0x5D1DAF8, std::uintptr_t{0});
    memory.Put(image + 0x5C67568, std::uintptr_t{0});
    memory.bytes.erase(context + 0x18);
    memory.bytes.erase(first_fallback + 0x128);
    const auto out = Observe(memory);
    Require(out.provider.source_ready && out.first_registry.used_fallback &&
                out.second_registry.used_fallback &&
                !out.first_registry.requested_full_id_u32 &&
                !out.second_registry.requested_full_id_u32,
            "known null storage incorrectly required or invented an ID");
  }
  // 11: Native capacity comparison is unsigned, including high-bit capacity.
  {
    auto memory = Full();
    memory.Put(first_registry + 0x2C, UINT32_C(0x80000000));
    const auto out = Observe(memory);
    Require(out.provider.source_ready && out.first_registry.resolved_by_full_id &&
                out.first_registry.unsigned_capacity_u32 == UINT32_C(0x80000000),
            "unsigned registry bound was narrowed to signed capacity");
  }
  // 12: A known out-of-range index uses fallback, without reading slots.
  {
    auto memory = Full();
    memory.Put(first_registry + 0x2C, std::uint32_t{3});
    memory.bytes.erase(first_registry + 0x20);
    const auto out = Observe(memory);
    Require(out.provider.source_ready && out.first_registry.used_fallback &&
                !out.first_registry.entries_pointer,
            "out-of-range unsigned index read an unselected slot");
  }
  // 13: Unread storage remains unknown; it does not select a known fallback.
  {
    auto memory = Full();
    memory.bytes.erase(image + 0x5D1DAF8);
    const auto out = Observe(memory);
    Require(!out.provider.source_ready && !out.provider.first_qword_raw &&
                out.context_398_qword_raw == 10000000 && !out.first_registry.used_fallback &&
                out.failure == ContextFirstQword24D3260FailureV1::source_read,
            "unread registry was replaced with null/default/fallback");
  }
  // 14: Unknown object full ID cannot act as a generation mismatch.
  {
    auto memory = Full();
    memory.bytes.erase(first_object + 0x10);
    const auto out = Observe(memory);
    Require(!out.provider.source_ready && !out.first_registry.used_fallback &&
                out.failed_address == first_object + 0x10,
            "unread full ID was treated as a known mismatch");
  }
  // 15: Source bookend change retains raw diagnostics but denies ready value.
  {
    auto memory = Full();
    memory.change_initial_on_second_read = true;
    const auto out = Observe(memory);
    Require(!out.provider.source_ready && !out.provider.first_qword_raw &&
                out.context_398_qword_raw == 10000000 && out.override_qword_raw == -7654321 &&
                out.failure == ContextFirstQword24D3260FailureV1::source_changed,
            "changed paused source was promoted to qualified copied output");
  }
  // 16: Exact build/frame admission occurs before a memory read.
  {
    auto memory = Full();
    LoadedInputAccessV1 access{&memory, &Read, false};
    const auto wrong_build = ReadContextFirstQword24D3260V1(access, image, context, frame);
    access.exact_12004_bound = true;
    const auto no_frame = ReadContextFirstQword24D3260V1(access, image, context, 0);
    Require(!wrong_build.provider.source_ready && !no_frame.provider.source_ready &&
                wrong_build.failure == ContextFirstQword24D3260FailureV1::exact_build &&
                no_frame.failure == ContextFirstQword24D3260FailureV1::frame_key && memory.reads.empty(),
            "missing exact pin/frame admitted source reads or a synthetic frame");
  }
}
} // namespace xar::ck3_12004::construction_owner_mode3
