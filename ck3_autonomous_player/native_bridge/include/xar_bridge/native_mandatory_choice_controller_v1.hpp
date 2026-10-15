#pragma once

#include "native_modal_choice_collector_v1.hpp"

#include <functional>
#include <optional>
#include <utility>

namespace xar::mandatory_choice_v1 {

// Bridge owns this object per connection, on the application owner thread.
// FreshFrame is a native same-game snapshot/stamp read, never caller payload.
class Controller {
 public:
  using FreshFrame = std::function<std::optional<Frame>()>;
  using Dispatch = std::function<bool(std::uintptr_t, bool &)>;
  Controller(NativeModalPort &port, FreshFrame fresh_frame,
             Gate::Nonce nonce, Dispatch dispatch)
      : port_(port), fresh_frame_(std::move(fresh_frame)),
        nonce_(std::move(nonce)), dispatch_(std::move(dispatch)) {}

  QueryResult Query();
  SelectResult Select(const SelectRequest &request);
  void Clear() noexcept {gate_.Clear();}

 private:
  NativeModalPort &port_;
  FreshFrame fresh_frame_;
  Gate::Nonce nonce_;
  Dispatch dispatch_;
  Gate gate_;
};

// Production Win32 implementation uses the system CSPRNG. The bridge must
// reject empty output, keeping tokens private and single-use in Controller.
std::string SecureNativeChoiceNonceV1();
} // namespace xar::mandatory_choice_v1
