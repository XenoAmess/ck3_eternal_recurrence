#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace xar::ck3_11906 {

inline constexpr std::size_t kActivityStage5FailureDisplayCapacityV1 = 512;

using ActivityStage5CanStartPredicateV1 = bool (*)(void *, void *);
using ActivityStage5NativeStringDestroyV1 = void (*)(void *);

struct ActivityStage5FailureDisplayV1 {
  bool allowed = false;
  std::array<char, kActivityStage5FailureDisplayCapacityV1> bytes{};
  std::uint16_t size = 0;
};

// The exact CK3 1.19.0.6 evaluator accepts a caller-owned 32-byte MSVC
// string. Copy its optional display text before invoking the game's own
// destructor; this text is not a stable reason key.
bool InvokeActivityStage5CanStartWithDisplayV1(
    void *planner, ActivityStage5CanStartPredicateV1 predicate,
    ActivityStage5NativeStringDestroyV1 destroy_string,
    ActivityStage5FailureDisplayV1 &output) noexcept;

} // namespace xar::ck3_11906
