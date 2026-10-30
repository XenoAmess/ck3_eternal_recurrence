#include "xar_bridge/ck3_12004_sway.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"
#include <array>
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <thread>
#include "fixtures/sway_action_public_route12004_world.hpp"

namespace {
namespace native = xar::ck3_12002;
namespace api = xar::ck3_11906;
int checks = 0, bind_state_calls = 0, bind_command_calls = 0, unused_calls = 0;
void Verify(bool condition, const char *message) { ++checks; Check(condition, message); }
[[noreturn]] void Unused() noexcept { ++unused_calls; std::abort(); }
std::int32_t Opinion(void *owner, void *toward) {
  return Load<std::int32_t>(owner, 0x18) == target_id &&
      Load<std::int32_t>(toward, 0x18) == actor_id ? 37 : 200;
}
struct World;
World *current_world = nullptr;
void ApplyQueued() noexcept;
struct World {
  Fixture fixture{};
  std::array<std::byte, 0x58> store{};
  std::array<std::byte, 0x10> slots{};
  std::array<std::byte, 0x358> scheme{};
  std::array<void *, 1> blocks{scheme.data()};
  std::array<std::byte, 0xA60> type{};
  native::SwayStateBindings12002 source{};
  World() {
    can_send = shown = valid = queue_accepted = true;
    copy_changes_recipient = context_changes_actor = drift = false;
    contexts = destroys = sends = clones = queues = deletes = 0;
    source.enabled = true; source.module_base = 0x140000000;
    source.core = fixture.bindings.context.core; source.opinion = &Opinion;
    source.executable_sha256 = xar::ck3_12004::kExecutableSha256;
    Put(fixture.game.data(), source.manager_offset, source.module_base + source.manager_vtable_rva);
    Put(fixture.game.data(), source.manager_offset + 0x20, store.data());
    Put(store.data(), 0, source.module_base + source.storage_vtable_rva);
    Put(store.data(), 8, blocks.data()); Put(store.data(), 0x20, slots.data());
    Put(store.data(), 0x2C, std::int32_t{1});
    Put(scheme.data(), 0, source.module_base + source.instance_vtable_rva);
    Put(scheme.data(), 0x10, std::uint32_t{0}); Put(scheme.data(), 0x20, type.data());
    Put(scheme.data(), 0x2C, static_cast<std::uint32_t>(actor_id));
    Put(scheme.data(), 0x34, static_cast<std::uint32_t>(target_id));
    Put(scheme.data(), 0x78, std::int32_t{1}); Put(scheme.data(), 0x350, std::int32_t{10});
    Put(type.data(), 0, source.module_base + source.type_vtable_rva);
    std::memcpy(type.data() + 0x18, "sway", 5);
    Put(type.data(), 0x28, std::uint64_t{4}); Put(type.data(), 0x30, std::uint64_t{15});
    Put(type.data(), 0x38, std::uint32_t{0x4744624F}); Put(type.data(), 0xA4E, std::uint8_t{1});
    current_world = this; apply_queued_scheme = &ApplyQueued;
  }
  ~World() { apply_queued_scheme = nullptr; current_world = nullptr; }
};
void ApplyQueued() noexcept {
  if (!current_world) Unused();
  Put(current_world->slots.data(), 8, current_world->scheme.data());
  Put(current_world->store.data(), 0x3C, std::int32_t{1});
}
void *tls_context = nullptr;
void *__fastcall Tls() noexcept { return tls_context; }
struct Pump {
  std::array<std::byte, 0x28> tls{}, jomini{};
  std::array<std::byte, 0x18> state{};
  std::uint8_t initialized = 1;
  void *jomini_pointer = jomini.data(), *state_pointer = state.data();
  std::uintptr_t unused_rng = 0;
  explicit Pump(api::MainThreadQueryMailboxV1 &mailbox) {
    tls[0x20] = std::byte{1}; jomini[0x20] = std::byte{1};
    Put(state.data(), 8, std::int32_t{53220000}); tls_context = tls.data();
    mailbox.global_rng_wrapper_slot = reinterpret_cast<std::uintptr_t>(&unused_rng);
    mailbox.jomini_state_slot = reinterpret_cast<std::uintptr_t>(&jomini_pointer);
    mailbox.game_state_slot = reinterpret_cast<std::uintptr_t>(&state_pointer);
    mailbox.tls_initialized_flag = reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter = &Tls;
    mailbox.executor_submission_enabled = true; mailbox.offline_fixture = true;
    mailbox.permitted_executor_octoquinquagintary = &native::ExecuteActiveSwayMailbox12002;
    mailbox.iat_hook_installed = true; mailbox.state = api::MainThreadQueryMailboxStateV1::idle;
    for (int i = 0; i < 2; ++i)
      (void)api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
  }
  ~Pump() { tls_context = nullptr; }
};
struct RouteResult { bool success{}, drained{}; std::string serialized, failure; };
struct Routes {
  FrameAdapter adapter{};
  api::MainThreadQueryMailboxV1 mailbox{};
  Pump pump{mailbox};
  native::ActiveSwayState12002 ledger{};
  Routes() {
    adapter.frame.paused = adapter.frame.map_ready = adapter.frame.has_played_character = adapter.frame.played_character_alive = true;
    adapter.frame.played_character_id = actor_id; adapter.frame.date_raw = 53220000;
  }
  RouteResult Call(std::string_view step, std::string_view payload, bool expected_queue) {
    RouteResult out{}; std::atomic<bool> done{false};
    const auto previous = mailbox.executed_requests.load();
    const auto sequence = mailbox.next_sequence.load();
    std::thread worker([&] {
      out.success = native::HandleActiveSwayPrivate12002(adapter, mailbox, adapter.frame,
          7, step, payload, "m6-public-action", ledger, out.serialized, out.failure);
      done.store(true, std::memory_order_release);
    });
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(12);
    while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
      if (mailbox.state.load(std::memory_order_acquire) == api::MainThreadQueryMailboxStateV1::queued)
        out.drained |= api::ObserveMainThreadPumpAndDrainV1(mailbox, mailbox.pump_exact_return_rva, GetCurrentThreadId());
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    worker.join();
    Verify(out.drained == expected_queue, "actual public action queue drain classification");
    Verify(mailbox.state == api::MainThreadQueryMailboxStateV1::idle, "actual public action reclaims mailbox");
    Verify(mailbox.executed_requests == previous + (expected_queue ? 1U : 0U), "exact named callback execution delta");
    Verify(mailbox.next_sequence == sequence + (expected_queue ? 1U : 0U), "ticket allocated only for actual queued request");
    if (expected_queue) Verify(mailbox.completed_sequence == mailbox.published_sequence &&
        mailbox.executor_started_requests == mailbox.executed_requests && mailbox.failure_flags == 0,
        "actual pump ticket completion and infrastructure counters");
    return out;
  }
};
constexpr std::string_view query_step = "query-active-scheme-sway-target-v1-private-0";
constexpr std::string_view submit_step = "submit-active-scheme-sway-v1-private-0";
constexpr std::string_view receipt_step = "receipt-active-scheme-sway-v1-private-0";
constexpr std::string_view action = "sway-canonical-minus2-zero";
std::uint64_t Number(std::string_view json, std::string_view name) {
  const auto key = '"' + std::string(name) + "\":";
  const auto at = json.find(key); Check(at != std::string_view::npos, "actual serialized numeric key present");
  const auto value = json.substr(at + key.size()); std::uint64_t result{};
  const auto [end, error] = std::from_chars(value.data(), value.data() + value.size(), result);
  Check(error == std::errc{} && end != value.data(), "actual serialized numeric value parse"); return result;
}
bool Has(std::string_view text, std::string_view part) { return text.find(part) != std::string_view::npos; }
std::string SubmitPayload(std::uint64_t epoch, std::uint64_t generation, int revision = 7) {
  return "{\"expected_revision\":" + std::to_string(revision) + ",\"action_id\":\"" +
      std::string(action) + "\",\"expected_capture_epoch\":" + std::to_string(epoch) +
      ",\"expected_container_generation\":" + std::to_string(generation) +
      ",\"expected_target_opinion_of_actor\":\"37\"}";
}
void Save(const std::filesystem::path &output, std::string_view leaf, std::string_view text) {
  std::ofstream file(output / leaf, std::ios::binary); file << text << '\n'; Check(file.good(), "actual wire packet saved");
}
void SaveCall(const std::filesystem::path &output, std::string_view name, std::string_view payload, const RouteResult &result) {
  const auto prefix = "canonical-minus2-zero." + std::string(name);
  Save(output, prefix + ".request.json", payload);
  if (result.success) Save(output, prefix + ".response.json", result.serialized);
}
void Canonical(const std::filesystem::path &output) {
  World world; Routes route;
  const std::string read = "{\"expected_revision\":7}";
  auto query = route.Call(query_step, read, true); SaveCall(output, "query", read, query);
  Verify(query.success && query.failure.empty() && Has(query.serialized, "\"actor_character_id\":-2") &&
      Has(query.serialized, "\"target_character_id\":0") && Has(query.serialized, "\"native_legal_now\":true") &&
      Number(query.serialized, "active_scheme_count") == 0, "public query retains canonical signed pair and empty legal state");
  const auto epoch = Number(query.serialized, "capture_epoch"), generation = Number(query.serialized, "container_generation");
  const auto submit_payload = SubmitPayload(epoch, generation);
  auto submit = route.Call(submit_step, submit_payload, true); SaveCall(output, "submit", submit_payload, submit);
  Verify(submit.success && submit.failure.empty() && Has(submit.serialized, "\"stage\":\"submitted_verification_pending\"") &&
      Has(submit.serialized, "\"actor_character_id\":-2") && Has(submit.serialized, "\"target_character_id\":0"),
      "public Handler accepted canonical signed action and serialized actual shared semantic ACK");
  Verify(route.ledger.may_have_submitted && route.ledger.pending_ack && queues == 1 && sends == 1 && clones == 1 && deletes == 1,
      "one native command copy and owning queue with residual release and retained pending ledger");
  const auto ack_epoch = Number(submit.serialized, "pre_capture_epoch");
  Verify(ack_epoch > epoch, "submit receives genuinely later pump epoch than quote");
  const auto stale_payload = SubmitPayload(epoch, generation, 6);
  auto stale = route.Call(submit_step, stale_payload, false);
  Verify(!stale.success && stale.serialized.empty() && stale.failure == "sway frame or request invalid" && queues == 1 &&
      route.ledger.pending_ack.has_value(), "stale revision rejected before queue without second native execution");
  auto duplicate = route.Call(submit_step, submit_payload, false);
  Verify(!duplicate.success && duplicate.serialized.empty() && duplicate.failure == "sway submit ledger or source invalid" && queues == 1,
      "same-source duplicate blocked by real public pending ledger before second execution");
  const auto receipt_payload = "{\"expected_revision\":7,\"action_id\":\"" + std::string(action) + "\"}";
  auto receipt = route.Call(receipt_step, receipt_payload, true); SaveCall(output, "receipt", receipt_payload, receipt);
  Verify(receipt.success && receipt.failure.empty() && Has(receipt.serialized, "\"stage\":\"applied\"") &&
      Has(receipt.serialized, "\"postcondition_verified\":true") && Number(receipt.serialized, "scheme_instance_id") == 0 &&
      Number(receipt.serialized, "scheme_instance_generation") == 0, "fresh actual receipt admits full SchemeID0 and generation0");
  const auto receipt_epoch = Number(receipt.serialized, "post_capture_epoch");
  Verify(receipt_epoch > ack_epoch && !route.ledger.may_have_submitted && !route.ledger.pending_ack && queues == 1,
      "fresh receipt clears ledger without another send");
  auto post = route.Call(query_step, read, true); SaveCall(output, "post-query", read, post);
  Verify(post.success && Has(post.serialized, "\"matching_sway_active\":true") &&
      Has(post.serialized, "\"native_legal_now\":false") && Number(post.serialized, "active_scheme_count") == 1 &&
      Number(post.serialized, "scheme_instance_id") == 0 && Number(post.serialized, "capture_epoch") > receipt_epoch && queues == 1,
      "independent real post-query later than receipt observes active full SchemeID0");
  Save(output, "canonical-minus2-zero.negative-actual.json", "{\"stale_revision_success\":false,\"stale_revision_queued\":false,\"stale_failure\":\"" + stale.failure +
      "\",\"duplicate_success\":false,\"duplicate_queued\":false,\"duplicate_failure\":\"" + duplicate.failure +
      "\",\"native_queue_calls\":" + std::to_string(queues) + ",\"completed_tickets\":" + std::to_string(route.mailbox.executed_requests.load()) + "}");
}
void WrongGeneration(const std::filesystem::path &output) {
  World world; Routes route;
  auto query = route.Call(query_step, "{\"expected_revision\":7}", true);
  Verify(query.success, "wrong-generation case starts from real valid public quote");
  const auto payload = SubmitPayload(Number(query.serialized, "capture_epoch"), Number(query.serialized, "container_generation"));
  Put(world.fixture.characters[1].data(), 0x18, std::int32_t{0x01000000});
  auto result = route.Call(submit_step, payload, true);
  Verify(!result.success && result.serialized.empty() && result.failure == "native_sway_target_opinion_red" &&
      queues == 0 && sends == 0 && clones == 0 && deletes == 0,
      "same slot wrong full generation rejected in actual executor before native command copy/queue");
  Verify(!route.ledger.may_have_submitted && !route.ledger.pending_ack,
      "entered known-safe rejection clears public submit marker");
  Save(output, "wrong-generation.actual.json", "{\"success\":false,\"queued_mailbox\":true,\"failure\":\"" + result.failure +
      "\",\"native_queue_calls\":" + std::to_string(queues) + ",\"same_slot_expected_full_id\":0,\"stored_full_id\":16777216,\"serialized_empty\":true}");
}
} // namespace

// Explicit isolated native-memory bindings; production action routing and
// algorithms remain compiled from the current source closure.
namespace xar::ck3_12004 {
ck3_12002::SwayStateBindings12002 BindSwayStateImage12004(std::uintptr_t, std::string_view sha) noexcept {
  ++bind_state_calls; if (!current_world || sha != kExecutableSha256) Unused(); return current_world->source;
}
ck3_12002::SwayCommandBindingsV1 BindSwayCommandImage12004(std::uintptr_t, std::string_view sha) noexcept {
  ++bind_command_calls; if (!current_world || sha != kExecutableSha256) Unused(); return current_world->fixture.bindings;
}
}
namespace xar::ck3_12002 {
const game::GameAdapter &NativeAdapter12002(const game::GameAdapter &adapter) noexcept { return adapter; }
bool ReadCharacterOpinion12002(std::uintptr_t, const CoreBindings &, std::uint32_t, std::uint32_t, std::int32_t &) noexcept { Unused(); }
}
namespace xar::game {
bool ReadCk3_12002TimelineCoreSnapshot(const GameAdapter &, Snapshot &) noexcept { Unused(); }
}
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire output argument"); actor_id = -2; target_id = 0;
    const std::filesystem::path output(argv[1]); std::filesystem::create_directories(output);
    Canonical(output); WrongGeneration(output);
    Verify(unused_calls == 0 && bind_state_calls == 6 && bind_command_calls == 6,
        "only explicit owned actual4 binding seams used; unused native fallbacks remain zero");
    std::cout << "CHECKS " << checks << " FAILED 0 public-action-handler+named-slot58+real-queue/pump+core/state/terms+semantic-command+receipt/serializer; game NOT_RUN; actual4-factory NOT_RUN\n";
    return 0;
  } catch (const std::exception &e) { std::cerr << "ERROR " << e.what() << '\n'; return 1; }
}
