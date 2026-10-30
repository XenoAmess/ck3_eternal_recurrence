#include "fixtures/sway_opinion_mailbox_world.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include <cstdlib>

namespace {
native::SwayOutcomeBindings *current_binding = nullptr;
int bind_calls = 0, abort_calls = 0;
[[noreturn]] void NotExercised() noexcept { ++abort_calls; std::abort(); }
void *tls_context = nullptr;
void *__fastcall Tls() noexcept { return tls_context; }
struct Pump {
  std::array<std::byte, 0x28> tls{}, jomini{};
  std::array<std::byte, 0x18> state{};
  std::uint8_t initialized = 1;
  void *jomini_pointer = jomini.data(), *state_pointer = state.data();
  std::uintptr_t unused_rng = 0;
  explicit Pump(xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; jomini[0x20] = std::byte{1};
    Put(state.data(), 8, std::int32_t{53220000}); tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&jomini_pointer);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&state_pointer);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &Tls;
    mailbox.executor_submission_enabled = true;
    mailbox.offline_fixture = true;
    mailbox.permitted_executor_sway_outcome_opinion12002 = &native::ExecuteSwayOutcomeMailboxV1;
    mailbox.iat_hook_installed = true;
    mailbox.state = xar::ck3_11906::MainThreadQueryMailboxStateV1::idle;
    for (int i = 0; i < 2; ++i)
      (void)xar::ck3_11906::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};
struct RouteResult { bool success{}; bool drained{}; std::string serialized, failure; };
bool OtherRegisteredExecutor(void *, const xar::ck3_11906::MainThreadExecutionStampV1 &) noexcept { NotExercised(); }
RouteResult Route(World &world, FrameAdapter &adapter, bool expected_submit,
                  std::string_view payload, bool register_callback = true,
                  std::string_view step = native::kSwayOutcomeOpinionStepV1) {
  namespace api = xar::ck3_11906;
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump(mailbox);
  if (!register_callback) {
    mailbox.permitted_executor_sway_outcome_opinion12002 = nullptr;
    mailbox.permitted_executor = &OtherRegisteredExecutor;
  }
  current_binding = &world.binding; adapter.reads = 0;
  RouteResult out{}; std::atomic<bool> done{false};
  std::thread worker([&] {
    out.success = native::HandleSwayOutcomeEventV1(adapter, mailbox, adapter.frame,
        7, step, payload, "m6-public-\"route", out.serialized, out.failure);
    done.store(true, std::memory_order_release);
  });
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(10);
  while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
    if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
      out.drained |= api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  worker.join();
  Check(out.drained == expected_submit, "public handler submission matches queue drain");
  Check(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "public handler reclaims queue slot");
  Check(mailbox.executed_requests == (expected_submit ? 1U : 0U), "one callback completion only when submitted");
  if (expected_submit) {
    Check(mailbox.completed_sequence == mailbox.published_sequence && mailbox.published_sequence == 1,
        "real queue completion identity retains submitted ticket");
    Check(mailbox.executor_started_requests == 1 && mailbox.failure_flags == 0,
        "real queue has one started callback and no infrastructure failure");
  } else Check(mailbox.next_sequence == 0, "rejected request never allocates a ticket");
  return out;
}
std::string Payload(std::int32_t actor, std::int32_t target, int revision = 7) {
  return "{\"expected_revision\":" + std::to_string(revision) + ",\"actor_character_id\":" +
      std::to_string(actor) + ",\"target_character_id\":" + std::to_string(target) + '}';
}
void Case(std::int32_t actor, std::int32_t target, const std::filesystem::path &output, int index) {
  World world(actor, target); FrameAdapter adapter;
  adapter.frame.paused = adapter.frame.map_ready = adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
  adapter.frame.played_character_id = actor; adapter.frame.date_raw = 53220000;
  auto route = Route(world, adapter, true, Payload(actor, target));
  Check(route.success && route.failure.empty() && adapter.reads == 2,
      "public handler performs owning entry/finish snapshots and succeeds");
  Check(route.serialized.find("\"status\":\"available\"") != std::string::npos &&
      route.serialized.find("\"actor_character_id\":" + std::to_string(actor)) != std::string::npos &&
      route.serialized.find("\"target_character_id\":" + std::to_string(target)) != std::string::npos,
      "public handler caller packet preserves signed pair and availability");
  Check(route.serialized.find("m6-public-\\\"route") != std::string::npos &&
      opinions == 2 && groups == 4 && callback_identity,
      "request id escaping and real material callbacks preserve direction/full raw word");
  std::ofstream file(output / ("pair-" + std::to_string(index) + ".response.json"), std::ios::binary);
  file << route.serialized << '\n'; Check(file.good(), "public handler packet saved");
  adapter.drift = true; opinions = groups = 0;
  route = Route(world, adapter, true, Payload(actor, target));
  Check(!route.success && route.serialized.empty() && route.failure == "sway_outcome_executor_result_unavailable" &&
      opinions == 2 && groups == 4 && adapter.reads == 2,
      "finish snapshot drift suppresses handler success after actual material read");
  adapter.drift = false;
  route = Route(world, adapter, false, Payload(actor, target, 8));
  Check(!route.success && route.failure == "sway_outcome_frame_or_request_invalid", "stale native revision rejected before queue");
  route = Route(world, adapter, false, Payload(actor, target), false);
  Check(!route.success && route.failure == "sway_outcome_executor_unavailable", "named callback registration required");
  route = Route(world, adapter, false,
      "{\"expected_revision\":7,\"actor_character_id\":1,\"target_character_id\":2,\"event_instance_id\":1,\"scheme_instance_id\":1}",
      true, native::kSwayOutcomeEventStepV1);
  Check(!route.success && route.failure == "sway_outcome_frame_or_request_invalid", "actual4 Event path remains explicitly unavailable");
}
}
// Explicit isolated I/O seams. The production handler, queue, pump, envelope,
// material reader and serializers all remain actual compiled source.
namespace xar::ck3_12004 {
ck3_12002::SwayOutcomeBindings BindSwayOutcomeOpinionImage12004(std::uintptr_t, std::string_view) noexcept {
  ++bind_calls; if (!current_binding) NotExercised(); return *current_binding;
}
ck3_12002::CommandBindings BindCommandImage12004(std::uintptr_t, std::string_view) noexcept { NotExercised(); }
}
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
GiftOpinionBindings12002 BindGiftOpinionImage12002(std::uintptr_t, std::string_view) noexcept { NotExercised(); }
void *CurrentEvent(const EventsBindings &) noexcept { NotExercised(); }
EventWindowBindings BindEventWindowImage(std::uintptr_t, std::string_view) noexcept { NotExercised(); }
game::ReadEventWindowContextResultV1 ReadEventWindowContextV1(const EventWindowBindings &, std::uint64_t,
    std::int32_t, game::EventWindowContextV1 &) noexcept { NotExercised(); }
}
namespace xar::game {
bool ReadCk3_12002TimelineCoreSnapshot(const GameAdapter &, Snapshot &) noexcept { NotExercised(); }
}
int main(int argc, char **argv) {
  try {
    if (argc != 2) throw std::runtime_error("wire output argument");
    const std::filesystem::path output(argv[1]); std::filesystem::create_directories(output);
    Case(-2, 0, output, 0); Case(0, INT32_MAX, output, 1); Case(INT32_MIN, INT32_MAX, output, 2);
    Check(abort_calls == 0 && bind_calls == 9, "only explicit owned image binding seam executed");
    std::cout << "CHECKS " << checks << " FAILED " << failures << " public-handler+queue+pump+entry+reader+finish+caller-packet; live NOT_RUN\n";
    return failures == 0 ? 0 : 1;
  } catch (const std::exception &e) { std::cerr << "ERROR " << e.what() << '\n'; return 2; }
}
