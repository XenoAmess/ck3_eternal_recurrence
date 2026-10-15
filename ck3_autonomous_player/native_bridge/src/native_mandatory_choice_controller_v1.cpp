#include "native_mandatory_choice_controller_v1.hpp"

namespace xar::mandatory_choice_v1 {
QueryResult Controller::Query() {
  QueryResult result{};
  gate_.Clear();
  if (!fresh_frame_) {
    result.unavailable_reason = "fresh_native_frame_source_missing"; return result;
  }
  try {
    auto frame = fresh_frame_();
    if (!frame) {
      result.unavailable_reason = "fresh_native_frame_unavailable"; return result;
    }
    std::string reason;
    auto observed = CollectTopModalChoices(*frame,port_,reason);
    if (!observed) {result.unavailable_reason = reason; return result;}
    return gate_.Query(*observed,nonce_);
  } catch (...) {
    result.unavailable_reason = "native_choice_query_exception"; return result;
  }
}

SelectResult Controller::Select(const SelectRequest &request) {
  return gate_.Select(request,[&] {
    if (!fresh_frame_) return Observation{};
    auto frame = fresh_frame_();
    if (!frame) return Observation{};
    std::string reason;
    auto observed = CollectTopModalChoices(*frame,port_,reason);
    return observed.value_or(Observation{});
  },dispatch_);
}

} // namespace xar::mandatory_choice_v1
