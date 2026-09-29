#include "activity_stage5_canstart_failure_display_v1.hpp"

#include <cstring>

namespace xar::ck3_11906 {
namespace {

struct NativeFailureDisplayString {
  std::array<char, 16> storage{};
  std::uint64_t size = 0;
  std::uint64_t capacity = 15;
};
static_assert(sizeof(NativeFailureDisplayString) == 32);

} // namespace

bool InvokeActivityStage5CanStartWithDisplayV1(
    void *planner, ActivityStage5CanStartPredicateV1 predicate,
    ActivityStage5NativeStringDestroyV1 destroy_string,
    ActivityStage5FailureDisplayV1 &output) noexcept {
  output = {};
  if (planner == nullptr || predicate == nullptr || destroy_string == nullptr)
    return false;
  NativeFailureDisplayString native{};
  const bool allowed = predicate(planner, &native);
  ActivityStage5FailureDisplayV1 copied{};
  copied.allowed = allowed;
  bool valid = native.size <= native.capacity &&
               native.size < copied.bytes.size();
  if (valid && !allowed && native.size != 0) {
    const char *bytes = native.storage.data();
    if (native.capacity >= 16) {
      std::memcpy(&bytes, native.storage.data(), sizeof(bytes));
      valid = bytes != nullptr;
    }
    if (valid) {
      std::memcpy(copied.bytes.data(), bytes,
                  static_cast<std::size_t>(native.size));
      copied.size = static_cast<std::uint16_t>(native.size);
    }
  }
  destroy_string(&native);
  if (!valid) return false;
  output = copied;
  return true;
}

} // namespace xar::ck3_11906
