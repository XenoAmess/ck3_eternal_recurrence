// Frozen memory/owner helpers only; the old twelve-case main is never run.
#define main FrozenReform12CaseMainNotExecuted
#include "religion_reform12002_query_mailbox_test.cpp"
#undef main
#include "xar_bridge/religion_reform12002_ai_inputs_mailbox.hpp"

namespace {
struct AIInputsBacking {
  Fixture base{};
  Bytes<0x30> holder{}, ordinary_a{}, ordinary_b{}, special{}, default_ai{}, other_ai{};
  Bytes<0x20> other_actor{};
  Bytes<0x2A0> extension_a{}, extension_b{};
  std::array<const void *, 5> controller_table{};
  std::array<std::int32_t, 7> periods{180, 720, 360, 180, 180, 180, 180};
  const std::int32_t *period_data = periods.data();
  const void *context_state_slot = base.state.data();
  std::uint8_t toggle = 0;
  unsigned tier_reads = 0, independent_reads = 0;
  AIInputsBacking() {
    Put(base.actor, f::kScheduleActorTagOffset, std::uint32_t{0x43686172});
    Put(base.data, f::kAIContextManagerOffset + f::kAIContextHolderOffset, holder.data());
    Put(holder, f::kAIContextDefaultOffset, default_ai.data());
    for (auto *controller : {&ordinary_a, &ordinary_b, &special, &default_ai}) {
      Put(*controller, f::kAIContextActorOffset, base.actor.data());
      Put(*controller, f::kAIContextTypeOffset, std::uint32_t{0x41495374});
      Put(*controller, f::kAIContextActiveOffset, std::uint8_t{1});
      Put(*controller, f::kScheduleAIGovernmentFlagsOffset, std::uint16_t{0x40});
      Put(*controller, f::kScheduleAIIndependentFlagsOffset, std::uint8_t{1});
    }
    Put(ordinary_b, f::kAIContextActiveOffset, std::uint8_t{0});
    Put(special, f::kAIContextSpecialOffset, std::uint8_t{1});
    Put(ordinary_a, f::kScheduleAIExtensionOffset, extension_a.data());
    Put(ordinary_b, f::kScheduleAIExtensionOffset, extension_b.data());
    Put(extension_a, f::kScheduleRareCountdownOffset, std::int32_t{-4});
    Put(extension_a, f::kScheduleRareSelectedOffset, std::uint8_t{1});
    Put(extension_b, f::kScheduleRareCountdownOffset, std::int32_t{12});
    Put(other_actor, 0x18, std::uint32_t{0x02000004});
    Put(other_actor, 0x1C, std::uint32_t{0x43686172});
    Put(other_ai, f::kAIContextActorOffset, other_actor.data());
    Put(other_ai, f::kAIContextTypeOffset, std::uint32_t{0x41495374});
    controller_table = {ordinary_a.data(), special.data(), ordinary_b.data(), other_ai.data(), default_ai.data()};
    Array(holder, f::kAIContextArrayOffset, controller_table.data(), 5);
  }
  void NoMatchingController() {
    controller_table[0] = other_ai.data(); controller_table[1] = default_ai.data();
    Array(holder, f::kAIContextArrayOffset, controller_table.data(), 2);
  }
};
AIInputsBacking *ai_inputs_backing = nullptr;
std::int32_t AIInputsTier(void *actor) {
  ++ai_inputs_backing->tier_reads;
  ai_inputs_backing->base.arguments_correct &= actor == ai_inputs_backing->base.actor.data();
  return 2;
}
bool AIInputsIndependent(void *actor) {
  ++ai_inputs_backing->independent_reads;
  ai_inputs_backing->base.arguments_correct &= actor == ai_inputs_backing->base.actor.data();
  return false;
}
c::PlayerReligionAIReformInputsObservation12002 AIInputsQuery(
    AIInputsBacking &backing, FrameAdapter &adapter, const std::filesystem::path &directory, const char *filename) {
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(backing.base, mailbox);
  mailbox.permitted_executor = &c::ExecutePlayerReligionAIReformInputsMailbox12002;
  c::PlayerReligionAIReformInputsMailboxContext12002 query{};
  query.envelope.game = &adapter; query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = adapter.frame;
  query.envelope.expected_snapshot_revision = 701;
  query.bindings.core = Bind(backing.base).core;
  query.bindings.context = {true, &backing.context_state_slot};
  query.bindings.schedule = {true, &AIInputsTier, &AIInputsIndependent, &backing.period_data, &backing.toggle};
  ai_inputs_backing = &backing;
  adapter.reads = 0;
  const auto before_holder = backing.holder, before_a = backing.ordinary_a, before_b = backing.ordinary_b,
             before_special = backing.special;
  const auto before_extension_a = backing.extension_a, before_extension_b = backing.extension_b;
  const auto before_table = backing.controller_table;
  std::atomic<bool> done{false}; bool result = false, drained = false;
  std::string serialized, failure;
  std::thread worker([&] {
    result = c::RunPlayerReligionAIReformInputsMailbox12002(
        query, "ai-inputs\"mailbox-fixture", serialized, failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(6);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      drained = api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(drained && mailbox.state == api::MainThreadQueryMailboxStateV1::idle,
        "actual combined AI query owner drain / terminal wait reclaim");
  Check(result && query.completed && query.envelope.frame_stable && !serialized.empty() && failure.empty(),
        "actual AI holder/schedule collector / Finish / complete native command_result");
  Check(query.observation.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
        query.observation.capture_epoch != 701, "AI inputs capture epoch is actual owner pump epoch");
  Check(backing.holder == before_holder && backing.ordinary_a == before_a && backing.ordinary_b == before_b &&
        backing.special == before_special && backing.extension_a == before_extension_a &&
        backing.extension_b == before_extension_b && backing.controller_table == before_table,
        "actual holder, controllers, extension and collection remain readonly");
  std::ofstream(directory / filename) << serialized << '\n';
  return query.observation;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    auto backing = std::make_unique<AIInputsBacking>();
    FrameAdapter adapter;
    adapter.frame.paused = adapter.frame.map_ready = true;
    adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = Fixture::actor_id;
    adapter.frame.date_raw = Fixture::date;
    auto out = AIInputsQuery(*backing, adapter, directory, "multiple-controllers.json");
    Check(out.available && out.gate_inputs_observation_complete &&
          out.context.status == f::AIContextStatus::observed_controllers && out.context.actual_holder_count == 5 &&
          out.context.controllers.size() == 3 && out.controller_inputs.size() == 3 &&
          out.context.controllers[0].actual_ai == backing->ordinary_a.data() &&
          out.context.controllers[1].actual_ai == backing->special.data() &&
          out.context.controllers[2].actual_ai == backing->ordinary_b.data(),
          "actual full matching controller table without default or guessed priority");
    Check(out.schedule_base.status == f::ScheduleStatus::observed &&
          out.schedule_base.ai_status == f::ScheduleAIStatus::not_supplied &&
          !out.schedule_base.reformation_enabled && !out.schedule_base.current_independent_ruler &&
          out.schedule_base.rare_period == 360 && out.controller_inputs[0].context_index == 0 &&
          out.controller_inputs[0].schedule.ai_status == f::ScheduleAIStatus::observed &&
          out.controller_inputs[0].schedule.rare_countdown_prepare_ticks == -4 &&
          out.controller_inputs[0].schedule.rare_selected_raw == 1 &&
          out.controller_inputs[0].schedule.handler_cache_gates_pass &&
          out.controller_inputs[1].context_index == 1 &&
          out.controller_inputs[1].schedule.ai_status == f::ScheduleAIStatus::gates_only &&
          out.controller_inputs[1].schedule.ai_special == 1 && !out.controller_inputs[1].schedule.handler_cache_gates_pass &&
          out.controller_inputs[2].context_index == 2 &&
          out.controller_inputs[2].schedule.ai_status == f::ScheduleAIStatus::observed &&
          out.controller_inputs[2].schedule.ai_active == 0 &&
          out.controller_inputs[2].schedule.rare_countdown_prepare_ticks == 12 &&
          backing->tier_reads == 4 && backing->independent_reads == 4 && backing->base.arguments_correct,
          "actual per-member schedules / player-special cache-only / inactive ordinary / valid false current globals");
    backing->NoMatchingController();
    out = AIInputsQuery(*backing, adapter, directory, "observed-no-ai.json");
    Check(out.available && out.gate_inputs_observation_complete &&
          out.context.status == f::AIContextStatus::observed_no_ai && out.context.actual_holder_count == 2 &&
          out.context.controllers.empty() && out.controller_inputs.empty() &&
          out.schedule_base.status == f::ScheduleStatus::observed &&
          out.schedule_base.ai_status == f::ScheduleAIStatus::not_supplied &&
          out.schedule_base.actor_id == Fixture::actor_id && out.schedule_base.rare_period == 360 &&
          backing->tier_reads == 5 && backing->independent_reads == 5,
          "legal no matching AI retains actual base actor/global observations and no controller fallback");
    std::cout << "PASS checks=" << checks << " cases=1 queued_commands=2 actual_ai_holder=true actual_schedule=true "
                 "actual_submit_owner_drain_finish_wait_reclaim=true actual_command_result=true "
                 "frozen_12_case_main_invoked=false ai_provider_matrix_repeated=false schedule_provider_matrix_repeated=false live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
