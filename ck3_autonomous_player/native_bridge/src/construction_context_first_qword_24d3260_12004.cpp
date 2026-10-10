#include "xar_bridge/construction_context_first_qword_24d3260_12004.hpp"

#include <array>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {
struct ScalarCopy {
  std::uintptr_t address = 0;
  std::size_t size = 0;
  std::array<std::byte, 8> bytes{};
};

struct SourceCopies {
  const LoadedInputAccessV1 &access;
  ContextFirstQword24D3260ObservationV1 &observation;
  std::array<ScalarCopy, 32> copies{};
  std::size_t count = 0;

  template <typename T>
  bool Read(std::uintptr_t base, std::size_t offset, T &value) noexcept {
    static_assert(sizeof(T) <= 8);
    std::uintptr_t address = 0;
    if (!AddOffsetV1(base, offset, address) || count == copies.size() ||
        !ReadOffsetV1(access, base, offset, value)) {
      observation.failed_address = address;
      observation.failed_bytes = sizeof(T);
      return false;
    }
    auto &copy = copies[count++];
    copy.address = address;
    copy.size = sizeof(T);
    std::memcpy(copy.bytes.data(), &value, sizeof(T));
    observation.scalar_source_reads = count;
    return true;
  }

  bool Unchanged() noexcept {
    for (std::size_t index = 0; index < count; ++index) {
      const auto &copy = copies[index];
      std::array<std::byte, 8> current{};
      if (!access.read_memory(access.context,
                             reinterpret_cast<const void *>(copy.address),
                             current.data(), copy.size) ||
          std::memcmp(copy.bytes.data(), current.data(), copy.size) != 0) {
        observation.failed_address = copy.address;
        observation.failed_bytes = copy.size;
        return false;
      }
    }
    return true;
  }
};

bool Resolve(SourceCopies &sources, std::uintptr_t image_base,
             std::uintptr_t id_source, std::size_t id_offset,
             std::uintptr_t registry_rva, std::uintptr_t fallback_rva,
             std::size_t full_id_offset,
             ContextFirstQword24D3260RegistryV1 &trace,
             std::uintptr_t &selected) noexcept {
  trace.visited = true;
  std::uintptr_t registry = 0;
  if (!sources.Read(image_base, registry_rva, registry)) return false;
  trace.registry_pointer = registry;
  if (registry != 0) {
    std::uint32_t full_id = 0, capacity = 0;
    if (!sources.Read(id_source, id_offset, full_id)) return false;
    trace.requested_full_id_u32 = full_id;
    const auto index = full_id & UINT32_C(0xFFFFFF);
    trace.index_low24_u32 = index;
    if (!sources.Read(registry, 0x2C, capacity)) return false;
    trace.unsigned_capacity_u32 = capacity;
    if (index < capacity) {
      std::uintptr_t entries = 0, object = 0;
      if (!sources.Read(registry, 0x20, entries)) return false;
      trace.entries_pointer = entries;
      if (!sources.Read(entries, static_cast<std::size_t>(index) * 0x10 + 8,
                        object)) return false;
      trace.slot_object = object;
      if (object != 0) {
        std::uint32_t observed_id = 0;
        if (!sources.Read(object, full_id_offset, observed_id)) return false;
        trace.object_full_id_u32 = observed_id;
        if (observed_id == full_id) {
          selected = object;
          trace.resolved_by_full_id = true;
          trace.selected_object = selected;
          return true;
        }
      }
    }
  }
  if (!sources.Read(image_base, fallback_rva, selected)) return false;
  trace.used_fallback = true;
  trace.selected_object = selected;
  return true;
}
} // namespace

ContextFirstQword24D3260ObservationV1 ReadContextFirstQword24D3260V1(
    const LoadedInputAccessV1 &access, std::uintptr_t image_base,
    std::uintptr_t context_object, std::uint64_t frame_key) noexcept {
  ContextFirstQword24D3260ObservationV1 result{};
  result.image_base = image_base;
  result.provider.source_pin = kContextFactor2C399C0SourcePinV1;
  result.provider.context_object = context_object;
  result.provider.frame_key = frame_key;
  const auto fail = [&](ContextFirstQword24D3260FailureV1 failure) {
    result.failure = failure;
    result.provider.source_ready = false;
    result.provider.first_qword_raw.reset();
    return result;
  };
  if (!access.exact_12004_bound) return fail(ContextFirstQword24D3260FailureV1::exact_build);
  if (frame_key == 0) return fail(ContextFirstQword24D3260FailureV1::frame_key);
  if (access.read_memory == nullptr) return fail(ContextFirstQword24D3260FailureV1::read_callback);
  if (image_base == 0) return fail(ContextFirstQword24D3260FailureV1::image_base);
  if (context_object == 0) return fail(ContextFirstQword24D3260FailureV1::context_object);
  SourceCopies sources{access, result};
  std::int64_t initial = 0, selected_qword = 0;
  if (!sources.Read(context_object, 0x398, initial))
    return fail(ContextFirstQword24D3260FailureV1::source_read);
  result.context_398_qword_raw = initial;
  selected_qword = initial;
  if (initial < INT64_C(10000000)) {
    result.path = ContextFirstQword24D3260PathV1::below_signed_threshold;
  } else {
    std::uintptr_t first = 0, second = 0, link = 0;
    if (!Resolve(sources, image_base, context_object, 0x18,
                 0x5D1DAF8, 0x5D1DAE0, 0x10, result.first_registry, first) ||
        !Resolve(sources, image_base, first, 0x128,
                 0x5C67568, 0x5C67570, 0x18, result.second_registry, second) ||
        !sources.Read(second, 0x1C0, link))
      return fail(ContextFirstQword24D3260FailureV1::source_read);
    result.second_object_link = link;
    if (link == 0) {
      result.path = ContextFirstQword24D3260PathV1::null_link;
    } else {
      std::uint8_t gate = 0;
      if (!sources.Read(link, 0x4AB, gate))
        return fail(ContextFirstQword24D3260FailureV1::source_read);
      result.linked_object_gate_byte = gate;
      if (gate == 0) {
        result.path = ContextFirstQword24D3260PathV1::zero_gate_byte;
      } else {
        if (!sources.Read(image_base, kContextFirstQword24D3260OverrideSlotRvaV1,
                          selected_qword))
          return fail(ContextFirstQword24D3260FailureV1::source_read);
        result.override_qword_raw = selected_qword;
        result.path = ContextFirstQword24D3260PathV1::loaded_override;
      }
    }
  }
  if (!sources.Unchanged()) return fail(ContextFirstQword24D3260FailureV1::source_changed);
  result.copied_sources_unchanged = true;
  result.provider.first_qword_raw = selected_qword;
  result.provider.source_ready = true;
  return result;
}
} // namespace xar::ck3_12004::construction_owner_mode3
