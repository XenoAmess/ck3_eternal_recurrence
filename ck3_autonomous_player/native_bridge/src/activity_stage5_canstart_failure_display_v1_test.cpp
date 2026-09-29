#include "activity_stage5_canstart_failure_display_v1.hpp"

#include <cassert>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string_view>

namespace {

using xar::ck3_11906::ActivityStage5FailureDisplayV1;
using xar::ck3_11906::InvokeActivityStage5CanStartWithDisplayV1;

struct NativeString {
  char storage[16];
  std::uint64_t size;
  std::uint64_t capacity;
};
static_assert(sizeof(NativeString) == 32);

struct Fixture {
  std::string_view text;
  bool allowed = false;
  bool invalid_size = false;
  int calls = 0;
  int destroys = 0;
};
Fixture *active = nullptr;

bool Predicate(void *opaque, void *native_output) {
  auto &fixture = *static_cast<Fixture *>(opaque);
  auto &native = *static_cast<NativeString *>(native_output);
  assert(native.size == 0 && native.capacity == 15 && native.storage[0] == 0);
  ++fixture.calls;
  if (fixture.text.size() < 16) {
    std::memcpy(native.storage, fixture.text.data(), fixture.text.size());
  } else {
    auto *data = static_cast<char *>(std::malloc(fixture.text.size() + 1));
    assert(data != nullptr);
    std::memcpy(data, fixture.text.data(), fixture.text.size());
    data[fixture.text.size()] = 0;
    std::memcpy(native.storage, &data, sizeof(data));
    native.capacity = fixture.text.size();
  }
  native.size = fixture.invalid_size ? native.capacity + 1 : fixture.text.size();
  return fixture.allowed;
}

void Destroy(void *native_output) {
  auto &native = *static_cast<NativeString *>(native_output);
  ++active->destroys;
  if (native.capacity >= 16) {
    char *data = nullptr;
    std::memcpy(&data, native.storage, sizeof(data));
    std::free(data);
  }
  native.size = 0;
  native.capacity = 15;
  native.storage[0] = 0;
}

void Check(Fixture &fixture, std::string_view expected, bool succeeds = true) {
  active = &fixture;
  ActivityStage5FailureDisplayV1 result{};
  const bool done = InvokeActivityStage5CanStartWithDisplayV1(
      &fixture, &Predicate, &Destroy, result);
  assert(done == succeeds);
  assert(fixture.calls == 1 && fixture.destroys == 1);
  if (succeeds) {
    assert(result.allowed == fixture.allowed);
    assert(std::string_view(result.bytes.data(), result.size) == expected);
  } else {
    assert(result.size == 0);
  }
}

} // namespace

int main() {
  Fixture inline_false{"missing guest", false};
  Check(inline_false, "missing guest");
  Fixture heap_false{"A native failure display longer than fifteen bytes", false};
  Check(heap_false, heap_false.text);
  Fixture empty_false{"", false};
  Check(empty_false, "");
  Fixture true_result{"stale text", true};
  Check(true_result, "");
  Fixture invalid{"A native failure display longer than fifteen bytes", false,
                  true};
  Check(invalid, "", false);
  ActivityStage5FailureDisplayV1 output{};
  assert(!InvokeActivityStage5CanStartWithDisplayV1(
      nullptr, &Predicate, &Destroy, output));
  std::cout << "GREEN: exact-build stage-5 CanStart failure display copy and destroy\n";
}
