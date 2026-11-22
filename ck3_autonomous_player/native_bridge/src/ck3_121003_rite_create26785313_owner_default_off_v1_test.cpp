#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1
#error This independent executable must keep the Rite Create feature default OFF.
#endif
#include "rite_create_owner_nogame_fixture.hpp"
int main() {
  using namespace rite_owner_fixture;
  try {
    state.Reset(); Session session; auto mailbox = NewMailbox();
    for (auto action : {Action::query, Action::create, Action::query_confirmation, Action::accept_confirmation}) {
      auto q = Request(session, mailbox.get(), action); Run(q);
      Require(q.result.status == Status::unavailable && q.result.reason == "rite_create_default_off" &&
        !q.result.claim_sequence && !q.result.effect_attempted && !q.result.native_returned &&
        q.result.cleanup_known && !state.bindings && !state.frames && !state.observations &&
        !state.window_reads && !state.window_binds && !state.calls, "default-off actual owner performed work");
      NoSource(q); Wire(q);
    }
    std::cout << "PASS default_off_four_actions_no_observation_or_effect; NoGame\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}
