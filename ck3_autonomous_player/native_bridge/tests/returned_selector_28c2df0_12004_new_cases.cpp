#include "xar_bridge/returned_selector_28c2df0_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstring>
#include <map>
#include <vector>

namespace xar::ck3_12004::new_cases {
namespace {

struct CopiedFrame {
  std::map<std::uintptr_t, std::vector<unsigned char>> fields;
  std::size_t reads = 0;
  std::uintptr_t watched_address = 0;
  std::size_t watched_reads = 0;

  template <typename T> void Put(std::uintptr_t address, T value) {
    auto &field = fields[address];
    field.resize(sizeof(T));
    std::memcpy(field.data(), &value, sizeof(T));
  }

  static bool Read(void *context, std::uintptr_t address, void *destination,
                   std::size_t bytes) noexcept {
    auto &frame = *static_cast<CopiedFrame *>(context);
    ++frame.reads;
    if (address == frame.watched_address)
      ++frame.watched_reads;
    const auto field = frame.fields.find(address);
    if (field == frame.fields.end() || field->second.size() != bytes)
      return false;
    std::memcpy(destination, field->second.data(), bytes);
    return true;
  }
};

constexpr std::uintptr_t kBase = 0x140000000;
constexpr std::uintptr_t kInput = 0x10000;
constexpr std::uintptr_t kContext = 0x20000;
constexpr std::uintptr_t kObject = 0x30000;
constexpr std::uintptr_t kFallbackReceiver = 0x40000;
constexpr std::uintptr_t kFallbackObject = 0x50000;
constexpr std::uint64_t kFrame = 87;

CopiedFrame Entry(std::uintptr_t registry = 0) {
  CopiedFrame frame;
  frame.Put(kBase + 0x5C67568, registry);
  frame.Put(kBase + 0x5C67570, kFallbackReceiver);
  frame.Put(kBase + 0x5D1E2A8, kFallbackObject);
  frame.Put(kInput + 0x1C, std::uint32_t{0x43686172});
  frame.Put(kInput + 0x18, std::uint32_t{0x07000002});
  frame.Put(kFallbackReceiver + 0x1C, std::uint32_t{0});
  frame.Put(kFallbackObject + 0x4D6, std::uint8_t{9});
  return frame;
}

ReturnedSelector28C2DF0Result12004 Resolve(CopiedFrame &frame) {
  const auto binding = BindReturnedSelector28C2DF012004(
      kBase, kGameVersion, kExecutableSha256, CopiedFrame::Read, &frame);
  return ResolveReturnedSelector28C2DF012004(binding, kInput, kFrame);
}

bool PriorityKeepsActualIdentity() {
  auto frame = Entry();
  frame.Put(kInput + 0x1D0, kContext);
  // Deliberately omit 1C0: the earlier branch must not read it.
  frame.Put(kContext + 0x88, kObject);
  frame.Put(kObject + 0x4D6, std::uint8_t{0});
  const auto result = Resolve(frame);
  return result.source_ready && result.input_receiver == kInput &&
      result.frame_key == kFrame && result.returned_object == kObject &&
      result.selector_byte_4d6 == std::uint8_t{0} &&
      result.return_path == "receiver_1d0_object_88";
}

bool OtherContextCopiesRawFive() {
  auto frame = Entry();
  frame.Put(kInput + 0x1D0, std::uintptr_t{0});
  frame.Put(kInput + 0x1C0, kContext);
  frame.Put(kContext + 0x3F8, kObject);
  frame.Put(kObject + 0x4D6, std::uint8_t{5});
  const auto result = Resolve(frame);
  return result.source_ready && result.returned_object == kObject &&
      result.selector_byte_4d6 == std::uint8_t{5} &&
      result.return_path == "receiver_1c0_object_3f8";
}

bool FullIdSelectsMappedReceiver(bool matching_generation) {
  constexpr std::uintptr_t registry = 0x60000;
  constexpr std::uintptr_t slots = 0x70000;
  constexpr std::uintptr_t related = 0x80000;
  constexpr std::uintptr_t candidate = 0x90000;
  auto frame = Entry(registry);
  frame.Put(kInput + 0x1D0, std::uintptr_t{0});
  frame.Put(kInput + 0x1C0, std::uintptr_t{0});
  frame.Put(kInput + 0x1B8, related);
  frame.Put(related + 0xC8, std::uint32_t{0x07000002});
  frame.Put(registry + 0x2C, std::uint32_t{3});
  frame.Put(registry + 0x20, slots);
  frame.Put(slots + 2 * 16 + 8, candidate);
  frame.Put(candidate + 0x18, matching_generation
      ? std::uint32_t{0x07000002} : std::uint32_t{0x08000002});
  frame.Put(candidate + 0x1C, std::uint32_t{0x43686172});
  frame.Put(candidate + 0x1D0, kContext);
  frame.Put(kContext + 0x88, kObject);
  frame.Put(kObject + 0x4D6, std::uint8_t{5});
  const auto result = Resolve(frame);
  return result.source_ready && result.steps.size() == 2 &&
      result.steps[0].mapped_candidate_selected == matching_generation &&
      result.steps[1].receiver ==
          (matching_generation ? candidate : kFallbackReceiver) &&
      result.returned_object ==
          (matching_generation ? kObject : kFallbackObject) &&
      result.selector_byte_4d6 ==
          (matching_generation ? std::uint8_t{5} : std::uint8_t{9});
}

bool SelectedNullUsesActualGlobal() {
  auto frame = Entry();
  frame.Put(kInput + 0x1D0, kContext);
  frame.Put(kContext + 0x88, std::uintptr_t{0});
  const auto result = Resolve(frame);
  return result.source_ready && result.returned_object == kFallbackObject &&
      result.selector_byte_4d6 == std::uint8_t{9} &&
      result.return_path == "selected_null_global_fallback";
}

bool MissingRawBytePreservesUnknown() {
  auto frame = Entry();
  frame.Put(kInput + 0x1D0, kContext);
  frame.Put(kContext + 0x88, kObject);
  const auto result = Resolve(frame);
  return !result.source_ready && result.returned_object == kObject &&
      !result.selector_byte_4d6 &&
      result.unavailable_reason == "returned_selector_byte_4d6_unread";
}

bool ObjectOnlyNeedsNoConsumerByte() {
  auto frame = Entry();
  frame.watched_address = kObject + 0x4D6;
  frame.Put(kInput + 0x1D0, kContext);
  frame.Put(kContext + 0x88, kObject);
  const auto binding = BindReturnedSelector28C2DF012004(
      kBase, kGameVersion, kExecutableSha256, CopiedFrame::Read, &frame);
  const auto result =
      ResolveReturnedObject28C2DF012004(binding, kInput, kFrame);
  return result.source_ready && result.input_receiver == kInput &&
      result.frame_key == kFrame && result.returned_object == kObject &&
      result.unavailable_reason.empty() && frame.watched_reads == 0;
}

bool UnboundSourceDoesNotRead() {
  auto frame = Entry();
  const auto binding = BindReturnedSelector28C2DF012004(
      kBase, kGameVersion, "different-executable", CopiedFrame::Read, &frame);
  const auto result =
      ResolveReturnedSelector28C2DF012004(binding, kInput, kFrame);
  return !result.source_ready && frame.reads == 0 &&
      result.unavailable_reason == "exact4_source_binding_unavailable";
}

} // namespace

// No main: composed once by the current 03/10 integration verifier.
bool RunReturnedSelector28C2DF012004NewCases() {
  return PriorityKeepsActualIdentity() && OtherContextCopiesRawFive() &&
      FullIdSelectsMappedReceiver(true) && FullIdSelectsMappedReceiver(false) &&
      SelectedNullUsesActualGlobal() && MissingRawBytePreservesUnknown() &&
      ObjectOnlyNeedsNoConsumerByte() && UnboundSourceDoesNotRead();
}

} // namespace xar::ck3_12004::new_cases
