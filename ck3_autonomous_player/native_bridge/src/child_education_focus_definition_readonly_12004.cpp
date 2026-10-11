#include "xar_bridge/child_education_focus_definition_readonly_12004.hpp"

#include "xar_bridge/player_lifestyle_window_candidates_v1.hpp"

#include <array>
#include <cstddef>
#include <limits>

namespace xar::ck3_12004::education {
namespace {

using Access = ChildEducationFocusDefinitionReadAccess12004;
using Result = ChildEducationFocusDefinitionRead12004;
using Status = ChildEducationFocusDefinitionStatus12004;
using RawSpan = ChildEducationFocusDefinitionRawSpan12004;
using StableKey = game::PlayerLifestyleStableKeyV1;

constexpr std::uintptr_t kFocusDatabaseGlobalRva = 0x5C67188;
constexpr std::size_t kDatabaseSpanOffset = 0xF08;
constexpr std::size_t kDefinitionKeyOffset = 0x18;
constexpr std::size_t kMaximumRows =
    game::kPlayerLifestyleWindowMaximumFocusesV1;
constexpr std::array<std::string_view, 5> kEducationKeys{
    "education_diplomacy", "education_martial", "education_stewardship",
    "education_intrigue", "education_learning"};

static_assert(sizeof(std::uintptr_t) == 8);
static_assert(sizeof(RawSpan) == 0x10);
static_assert(kMaximumRows == 64);

struct ReadContext {
  const Access *access = nullptr;
};

bool ReadMemory(void *opaque, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  const auto *context = static_cast<const ReadContext *>(opaque);
  if (context == nullptr || context->access == nullptr ||
      context->access->read_memory == nullptr || address == 0 ||
      output == nullptr || size == 0 ||
      size - 1 > std::numeric_limits<std::uintptr_t>::max() - address) {
    return false;
  }
  return context->access->read_memory(context->access->context, address,
                                       output, size);
}

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &output) noexcept {
  if (base == 0 || offset > std::numeric_limits<std::uintptr_t>::max() - base) {
    return false;
  }
  output = base + offset;
  return true;
}

struct Header {
  std::uintptr_t database = 0;
  RawSpan span{};
  friend bool operator==(const Header &, const Header &) = default;
};

struct Sample {
  Header header{};
  std::array<std::uintptr_t, kMaximumRows> definitions{};
  std::array<StableKey, kMaximumRows> keys{};
  friend bool operator==(const Sample &, const Sample &) = default;
};

bool ReadHeader(ReadContext &context, std::uintptr_t global_address,
                Header &header) noexcept {
  std::uintptr_t span_address = 0;
  return ReadMemory(&context, global_address, &header.database,
                    sizeof(header.database)) &&
         Add(header.database, kDatabaseSpanOffset, span_address) &&
         ReadMemory(&context, span_address, &header.span, sizeof(header.span));
}

std::string_view Capture(ReadContext &context, std::uintptr_t global_address,
                         Sample &sample) noexcept {
  if (!ReadHeader(context, global_address, sample.header)) {
    return "database_read_failed";
  }
  const auto &span = sample.header.span;
  if (span.count < 0 || span.capacity < 0 || span.count > span.capacity ||
      span.count > static_cast<std::int32_t>(kMaximumRows) ||
      (span.count != 0 && span.data == 0)) {
    return "database_span_invalid";
  }
  for (std::int32_t index = 0; index < span.count; ++index) {
    const auto slot = static_cast<std::size_t>(index);
    std::uintptr_t row_address = 0;
    std::uintptr_t key_address = 0;
    if (!Add(span.data, slot * sizeof(std::uintptr_t), row_address) ||
        !ReadMemory(&context, row_address, &sample.definitions[slot],
                    sizeof(std::uintptr_t)) ||
        !Add(sample.definitions[slot], kDefinitionKeyOffset, key_address) ||
        !lifestyle::ReadPlayerLifestyleMsvcStableKey12004V1(
            &context, ReadMemory, key_address, sample.keys[slot])) {
      return "definition_or_key_read_failed";
    }
  }
  Header after{};
  if (!ReadHeader(context, global_address, after)) {
    return "database_bookend_read_failed";
  }
  if (!(sample.header == after)) return "database_changed";
  return {};
}

bool EducationKey(std::string_view key) noexcept {
  for (const auto candidate : kEducationKeys) {
    if (key == candidate) return true;
  }
  return false;
}

} // namespace

Result ReadChildEducationFocusDefinitionReadonly12004(
    const Access &access, std::uintptr_t module_base,
    bool exact_build_admitted, std::string_view admitted_executable_sha256,
    std::string_view requested_key) noexcept {
  Result result{};
  if (!EducationKey(requested_key) ||
      !lifestyle::AssignPlayerLifestyleStableKey12004V1(
          requested_key, result.requested_key)) {
    result.unavailable_reason = "education_key_invalid";
    return result;
  }
  if (!exact_build_admitted ||
      admitted_executable_sha256 != ck3_12004::kExecutableSha256) {
    result.unavailable_reason = "exact_build_not_admitted";
    return result;
  }
  std::uintptr_t global_address = 0;
  if (access.read_memory == nullptr ||
      !Add(module_base, kFocusDatabaseGlobalRva, global_address)) {
    result.unavailable_reason = "memory_access_unavailable";
    return result;
  }
  ReadContext context{&access};
  Sample before{};
  auto failure = Capture(context, global_address, before);
  result.database_identity = before.header.database;
  result.rawspan = before.header.span;
  if (!failure.empty()) {
    result.unavailable_reason = failure;
    return result;
  }
  Sample after{};
  failure = Capture(context, global_address, after);
  if (!failure.empty()) {
    result.unavailable_reason = failure;
    return result;
  }
  if (!(before == after)) {
    result.unavailable_reason = "database_or_definition_keys_changed";
    return result;
  }
  result.table_stable = true;
  for (std::int32_t index = 0; index < before.header.span.count; ++index) {
    const auto slot = static_cast<std::size_t>(index);
    if (lifestyle::PlayerLifestyleStableKeyView12004V1(before.keys[slot]) ==
        requested_key) {
      ++result.match_count;
      result.uniqueindex = static_cast<std::uint32_t>(index);
    }
  }
  if (result.match_count == 0) {
    result.status = Status::missing;
    result.unavailable_reason = "education_definition_missing";
    return result;
  }
  if (result.match_count != 1) {
    result.uniqueindex.reset();
    result.status = Status::ambiguous;
    result.unavailable_reason = "education_definition_ambiguous";
    return result;
  }
  result.definition_identity = before.definitions[*result.uniqueindex];
  result.available = true;
  result.status = Status::resolved;
  result.unavailable_reason = {};
  return result;
}

} // namespace xar::ck3_12004::education
