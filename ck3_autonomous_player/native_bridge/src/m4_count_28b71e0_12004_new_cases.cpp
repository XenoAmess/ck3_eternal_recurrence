#include "xar_bridge/m4_count_28b71e0_12004.hpp"

#include <map>
#include <set>
#include <stdexcept>
#include <utility>
#include <vector>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace count_28b71e0_cases {
constexpr std::uintptr_t image = 0x10000000, receiver = 0x200000;
constexpr std::uintptr_t context = 0x210000, ids = 0x220000;
constexpr std::uintptr_t registry = 0x230000, table = 0x240000;
constexpr std::uintptr_t title = 0x250000, rank = 0x260000;
constexpr std::uintptr_t province = 0x270000, slots = 0x280000;
constexpr std::uintptr_t buffer = 0x290000, interface_object = 0x2A0000;
constexpr std::uintptr_t object_context = 0x2B0000, returned_object = 0x2C0000;
constexpr std::uintptr_t fallback_title = 0x2D0000, fallback_rank = 0x2E0000;
constexpr std::uint64_t frame = 107;

void Need(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
struct CountMemory {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  std::set<std::uintptr_t> blocked;
  std::vector<std::pair<std::uintptr_t, std::size_t>> reads;
  bool change_buffer_byte_at_bookend = false;
  unsigned buffer_byte_reads = 0;
  template <typename T> void Put(std::uintptr_t address, T value) {
    const auto *raw = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(T); ++i) bytes[address + i] = raw[i];
  }
  void Block(std::uintptr_t address, std::size_t size) {
    for (std::size_t i = 0; i < size; ++i) blocked.insert(address + i);
  }
  bool Copy(std::uintptr_t address, void *out, std::size_t size) {
    reads.emplace_back(address, size);
    if (address == buffer + 8 && ++buffer_byte_reads == 2 &&
        change_buffer_byte_at_bookend) Put<std::uint8_t>(buffer + 8, 0);
    for (std::size_t i = 0; i < size; ++i)
      if (blocked.count(address + i) || !bytes.count(address + i)) return false;
    auto *raw = static_cast<std::uint8_t *>(out);
    for (std::size_t i = 0; i < size; ++i) raw[i] = bytes.at(address + i);
    return true;
  }
  bool Touched(std::uintptr_t address) const {
    for (const auto &read : reads) if (read.first == address) return true;
    return false;
  }
};
bool CopyCountMemory(void *context_ptr, const void *address, void *out, std::size_t size) {
  return static_cast<CountMemory *>(context_ptr)->Copy(
      reinterpret_cast<std::uintptr_t>(address), out, size);
}
RawReceiverAccessV1 Access(CountMemory &memory) {
  return {&memory, &CopyCountMemory, image, true};
}
CountMemory DirectCountSource() {
  CountMemory m;
  m.Put<std::uintptr_t>(receiver + 0x1C0, context);
  m.Put<std::uintptr_t>(context + 0x1E0, ids);
  m.Put<std::int32_t>(context + 0x1EC, 1);
  m.Put<std::uint32_t>(ids, 0xCD000001U);
  m.Put<std::uintptr_t>(image + 0x5D1DAF8, registry);
  m.Put<std::uintptr_t>(image + 0x5D1DAE0, fallback_title);
  m.Put<std::uint32_t>(registry + 0x2C, 2);
  m.Put<std::uintptr_t>(registry + 0x20, table);
  m.Put<std::uintptr_t>(table + 16 + 8, title);
  m.Put<std::uint32_t>(title + 0x10, 0xCD000001U);
  m.Put<std::uintptr_t>(title + 0x48, rank);
  m.Put<std::int32_t>(rank + 0x64, 1);
  m.Put<std::uintptr_t>(title + 0x338, province);
  m.Put<std::uint8_t>(title + 0x130, 0);
  m.Put<std::uint32_t>(title + 0x12C, 0xFFFFFFFFU);
  m.Put<std::uint32_t>(province + 0x85C, 0x50726F76U);
  m.Put<std::uint8_t>(province + 0x628, 1);
  m.Put<std::uint32_t>(province + 0x63C, 1);
  m.Put<std::uintptr_t>(province + 0x620, slots);
  m.Put<std::uintptr_t>(province + 0x630, buffer);
  m.Put<std::uintptr_t>(buffer, interface_object);
  m.Put<std::uint8_t>(buffer + 8, 1);
  m.Put<std::uint32_t>(interface_object + 0x38, 0x4744624FU);
  m.Put<std::uint8_t>(slots + 0xBC, 0);
  m.Put<std::uint32_t>(receiver + 0x1C, 0x43686172U);
  m.Put<std::uint32_t>(receiver + 0x18, 0xAB000007U);
  m.Put<std::uintptr_t>(receiver + 0x1D0, object_context);
  m.Put<std::uintptr_t>(object_context + 0x88, returned_object);
  m.Put<std::uintptr_t>(image + 0x5C67568, 0);
  m.Put<std::uintptr_t>(image + 0x5C67570, receiver);
  m.Put<std::uintptr_t>(returned_object + 0x418, slots);
  m.Put<std::uintptr_t>(fallback_title + 0x48, fallback_rank);
  m.Put<std::int32_t>(fallback_rank + 0x64, 2);
  return m;
}
Count28B71E0ObservationV1 Read(CountMemory &m) {
  return ReadConstructionCount28B71E0V1(Access(m), receiver, frame);
}
} // namespace count_28b71e0_cases

// Fresh export only for13e ->03d/10's one combined qualification.
void VerifyConstructionCount28B71E0OwnedCases12004() {
  using namespace count_28b71e0_cases;
  {
    auto m = DirectCountSource();
    const auto out = Read(m);
    Need(out.observed && out.input_receiver == receiver && out.frame_key == frame &&
             out.eax_signed_i32 == 1 && out.eax_raw_u32 == std::uint32_t{1} &&
             out.occurrences[0].path == Count28B71E0PathV1::count_returned_member_equal &&
             out.occurrences[0].returned_object_source->input_receiver == receiver &&
             !out.actual_original_consumed_values && !m.Touched(returned_object + 0x4D6),
         "71E0 reached object comparison lost original receiver/frame/EAX");
    std::int32_t adapted = 77;
    Need(ReadM4Count28B71E0Adapter12004(nullptr, Access(m), receiver, frame, adapted) && adapted == 1,
         "71E0 actual13 callback ABI did not consume qualified count");
  }
  {
    auto m = DirectCountSource();
    m.Put<std::int32_t>(context + 0x1EC, 3);
    m.Put<std::uint32_t>(ids + 4, 0xCD000001U);
    m.Put<std::uint32_t>(ids + 8, 0xCD000001U);
    const auto out = Read(m);
    Need(out.observed && out.eax_raw_u32 == std::uint32_t{3} && out.occurrences.size() == 3 &&
             out.occurrences[2].requested_full_id_u32 == 0xCD000001U,
         "71E0 deduplicated source occurrences or lost generation bits");
  }
  {
    auto m = DirectCountSource();
    m.Put<std::uint32_t>(interface_object + 0x38, 0);
    m.Block(buffer + 8, 1);
    const auto out = Read(m);
    Need(out.observed && out.eax_signed_i32 == 1 &&
             out.occurrences[0].path == Count28B71E0PathV1::count_interface_magic_mismatch &&
             !out.occurrences[0].returned_object_source && !m.Touched(buffer + 8),
         "71E0 interface magic mismatch incorrectly skipped increment");
  }
  {
    auto m = DirectCountSource();
    m.Put<std::uint8_t>(buffer + 8, 0);
    m.Block(slots + 0xBC, 1);
    const auto out = Read(m);
    Need(out.observed && out.eax_signed_i32 == 1 &&
             out.occurrences[0].path == Count28B71E0PathV1::count_buffer_byte_zero &&
             !m.Touched(slots + 0xBC), "71E0 zero buffer byte changed lazy increment");
  }
  {
    auto m = DirectCountSource();
    m.Put<std::uint8_t>(slots + 0xBC, 1);
    m.Block(image + 0x5C67568, 8);
    const auto out = Read(m);
    Need(out.observed && out.eax_signed_i32 == 1 &&
             out.occurrences[0].path == Count28B71E0PathV1::count_slots_byte_nonzero &&
             !m.Touched(image + 0x5C67568), "71E0 nonzero slots byte invoked unneeded child");
  }
  {
    auto m = DirectCountSource();
    m.Put<std::uintptr_t>(returned_object + 0x418, slots + 1);
    const auto out = Read(m);
    std::int32_t adapted = 77;
    Need(out.observed && out.eax_signed_i32 == 0 &&
             out.occurrences[0].path == Count28B71E0PathV1::skip_returned_member_unequal &&
             ReadM4Count28B71E0Adapter12004(nullptr, Access(m), receiver, frame, adapted) && adapted == 0,
         "71E0 observed inequality/zero became unavailable or count");
  }
  {
    auto m = DirectCountSource();
    m.Put<std::int32_t>(rank + 0x64, 2);
    m.Block(title + 0x338, 8);
    const auto out = Read(m);
    Need(out.observed && out.eax_signed_i32 == 0 && !m.Touched(title + 0x338),
         "71E0 rank>1 executed unneeded230F8E0 province source");
  }
  {
    auto m = DirectCountSource();
    m.Put<std::int32_t>(rank + 0x64, -1);
    const auto out = Read(m);
    Need(out.observed && out.eax_signed_i32 == 1 && out.occurrences[0].rank_i32 == -1,
         "71E0 signed rank comparison was changed to unsigned");
  }
  {
    auto m = DirectCountSource();
    m.Put<std::uint32_t>(title + 0x10, 0xCE000001U);
    const auto out = Read(m);
    Need(out.observed && out.eax_signed_i32 == 0 &&
             out.occurrences[0].requested_full_id_u32 == 0xCD000001U &&
             !out.occurrences[0].registry_matched &&
             out.occurrences[0].selected_title == fallback_title,
         "71E0 generation mismatch joined low24 title identity");
  }
  {
    auto m = DirectCountSource();
    m.Put<std::uintptr_t>(receiver + 0x1C0, 0);
    m.Put<std::uintptr_t>(image + 0x5459C88, 0);
    m.Put<std::int32_t>(image + 0x5459C88 + 0x0C, 0);
    m.Block(image + 0x5D1DAF8, 8);
    const auto out = Read(m);
    Need(out.observed && out.eax_signed_i32 == 0 && out.occurrences.empty() &&
             out.descriptor == image + 0x5459C88 && !m.Touched(image + 0x5D1DAF8),
         "71E0 null-context LEA descriptor/empty branch added a pointer load");
  }
  {
    auto m = DirectCountSource();
    m.Put<std::uint32_t>(province + 0x63C, 0);
    m.Put<std::uintptr_t>(image + 0x5D1E320, interface_object);
    m.Put<std::uint32_t>(interface_object + 0x38, 0);
    m.Block(province + 0x630, 8);
    const auto out = Read(m);
    Need(out.observed && out.eax_signed_i32 == 1 &&
             out.occurrences[0].interface_object == interface_object &&
             !m.Touched(province + 0x630),
         "71E0 zero63C global object path read unneeded buffer");
  }
  {
    auto m = DirectCountSource();
    m.Put<std::int32_t>(context + 0x1EC, -1);
    const auto out = Read(m);
    std::int32_t adapted = 77;
    Need(!out.observed && out.failure == Count28B71E0FailureV1::negative_source_extent &&
             out.count_raw_i32 == -1 && !out.eax_signed_i32 &&
             !ReadM4Count28B71E0Adapter12004(nullptr, Access(m), receiver, frame, adapted) && adapted == 77,
         "71E0 negative native extent was normalized to completed empty zero");
  }
  {
    auto m = DirectCountSource();
    m.Put<std::int32_t>(context + 0x1EC, 4097);
    const auto out = Read(m);
    std::int32_t adapted = 77;
    Need(!out.observed && out.failure == Count28B71E0FailureV1::native_copy_budget_exceeded &&
             out.count_raw_i32 == 4097 && out.occurrences.empty() &&
             !m.Touched(image + 0x5D1DAF8) &&
             !ReadM4Count28B71E0Adapter12004(nullptr, Access(m), receiver, frame, adapted) && adapted == 77,
         "71E0 readonly budget exceeded without preserving raw/unavailable source");
  }
  {
    auto m = DirectCountSource();
    m.Block(returned_object + 0x418, 8);
    const auto out = Read(m);
    std::int32_t adapted = 77;
    Need(!out.observed && out.failure == Count28B71E0FailureV1::returned_member &&
             !ReadM4Count28B71E0Adapter12004(nullptr, Access(m), receiver, frame, adapted) && adapted == 77,
         "71E0 missing reached member became synthetic zero");
  }
  {
    auto m = DirectCountSource();
    m.change_buffer_byte_at_bookend = true;
    const auto out = Read(m);
    Need(!out.observed && out.failure == Count28B71E0FailureV1::source_changed &&
             !out.eax_signed_i32 && !out.actual_original_consumed_values,
         "71E0 changed copied source obtained completed/original-consumed credit");
  }
}

} // namespace xar::ck3_12004::construction_owner_mode3
