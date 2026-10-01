// Reuse the owning native interaction fixture, including production clone/queue.
#define main SwayCommandProviderFixtureMain
#include "ck3_12002_sway_command_test.cpp"
#undef main
#include "xar_bridge/ck3_12002_sway_mailbox.hpp"
#include <fstream>
#include <filesystem>

namespace {
using namespace xar::bridge;
struct StateFixture {
  Fixture command{};
  std::array<std::byte, 0x58> storage{};
  std::array<std::byte, 16 * 16> scheme_slots{};
  std::vector<std::byte> block = std::vector<std::byte>(0x400 * 0x358);
  std::array<void *, 1> blocks{block.data()};
  std::array<std::byte, 0xA60> type{};
  std::array<std::byte, 0xA60> other_type{};
  SwayStateBindings12002 source{};
  std::uint64_t epoch = 40;
  StateFixture() {
    source.enabled = true; source.module_base = 0x140000000;
    source.core = command.bindings.context.core;
    source.opinion = [](void *owner, void *toward) {
      Check(Load<std::int32_t>(owner, 0x18) == target_id &&
          Load<std::int32_t>(toward, 0x18) == actor_id, "opinion receiver direction");
      return std::int32_t{-15};
    };
    Put(command.game.data(), kSwayManagerOffset12002,
        source.module_base + kSwayManagerVtableRva12002);
    Put(command.game.data(), kSwayManagerOffset12002 + 0x20, storage.data());
    Put(storage.data(), 0, source.module_base + kSwayStorageVtableRva12002);
    Put(storage.data(), 8, blocks.data());
    Put(storage.data(), 0x20, scheme_slots.data());
    Put(storage.data(), 0x2C, std::int32_t{16});
    Put(type.data(), 0, source.module_base + kSwayTypeVtableRva12002);
    std::memcpy(type.data() + 0x18, "sway", 5);
    Put(type.data(), 0x28, std::uint64_t{4}); Put(type.data(), 0x30, std::uint64_t{15});
    Put(type.data(), 0x38, std::uint32_t{0x4744624F});
    Put(type.data(), 0xA4E, std::uint8_t{1});
    Put(other_type.data(), 0, source.module_base + kSwayTypeVtableRva12002);
    std::memcpy(other_type.data() + 0x18, "murder", 7);
    Put(other_type.data(), 0x28, std::uint64_t{6}); Put(other_type.data(), 0x30, std::uint64_t{15});
  }
  void Add(std::int32_t index, std::uint32_t id, bool sway = true) {
    auto *scheme = block.data() + index * 0x358;
    Put(scheme_slots.data(), index * 16 + 8, scheme);
    Put(scheme, 0, source.module_base + kSwayInstanceVtableRva12002);
    Put(scheme, 0x10, id); Put(scheme, 0x20, sway ? type.data() : other_type.data());
    Put(scheme, 0x2C, actor_id); Put(scheme, 0x30, std::uint32_t{0});
    Put(scheme, 0x34, target_id); Put(scheme, 0x78, std::int32_t{355});
    Put(scheme, 0x350, std::int32_t{365});
    Put(storage.data(), 0x3C, Load<std::int32_t>(storage.data(), 0x3C) + 1);
  }
};
bool Observe(void *opaque, ActiveSchemeStateV1PrivateObservation &out) noexcept {
  auto &f = *static_cast<StateFixture *>(opaque);
  return ReadActiveSwayState12002(f.source, f.epoch, out);
}
bool Terms(void *opaque, ActiveSchemeSemanticActionV1PrivatePrecondition &out) noexcept {
  auto &f = *static_cast<StateFixture *>(opaque); SwayCommandTermsV1 terms{};
  if (!ReadSwayCommandTermsV1(f.command.bindings, actor_id, target_id, f.epoch, terms)) return false;
  out = terms.precondition; return true;
}
bool SendActual(void *opaque, const ActiveSchemeSemanticActionV1PrivateCommand &command) noexcept {
  return SubmitSwayCommandV1(static_cast<StateFixture *>(opaque)->command.bindings, command) ==
      SwayCommandSubmitResultV1::submitted;
}
void Save(const std::filesystem::path &dir, const char *name, const std::string &json) {
  Check(!json.empty(), "actual serializer emits wire");
  std::ofstream file(dir / name); file << json << '\n'; Check(file.good(), "wire fixture file");
}
}
#ifndef XAR_SWAY_STATE_FIXTURE_NO_MAIN
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument"); const std::filesystem::path output{argv[1]};
    StateFixture f; can_send = true;
    ActiveSwayMailboxContext12002 query{};
    query.target = target_id; query.envelope.expected_snapshot_revision = 7; query.completed = true;
    Check(ReadActiveSwayState12002(f.source, f.epoch, query.active) && query.active.row_count == 0,
        "actual new manager/storage empty owner state");
    Check(ReadSwayCommandTermsV1(f.command.bindings, actor_id, target_id, f.epoch, query.terms),
        "actual complete native legal pre-submit terms");
    Check(ReadSwayTargetOpinion12002(f.source, actor_id, target_id, query.opinion) && query.opinion == -15,
        "actual recipient opinion preserves negative value");
    const auto suffix = std::to_string(target_id);
    Save(output, "ck3_12002_sway_query_wire.json", SerializeActiveSwayEnvelope12002(query,
        "query-active-scheme-sway-target-v1-private-" + suffix, "fixture-read"));
    ActiveSchemeSemanticActionV1PrivateRequest request{
        "sway-fixture-start", "sway_interaction", actor_id,
        ActiveSchemeStateV1PrivateTargetKind::character, target_id,
        ++f.epoch, query.active.container_generation, query.active.date_raw, {}};
    const ActiveSchemeSemanticActionV1PrivateAccess access{&f, &Observe, &Terms, &SendActual};
    const ActiveSchemeSemanticActionV1PrivateEnvironment environment{
        f.source.module_base, true, kExecutableSha256, true, false};
    ActiveSwayMailboxContext12002 formal{}; formal.target = target_id;
    formal.formal = true; formal.completed = true; formal.action_id = request.request_id;
    Check(ExecuteActiveSchemeSemanticActionV1Private(environment, access, request, formal.ack) ==
        ActiveSchemeSemanticActionV1PrivateAckStatus::submitted_verification_pending &&
        formal.ack.submit_call_count == 1 && queues == 1 && clones == 1,
        "new exact SHA Sway action runs actual native owning command once");
    Save(output, "ck3_12002_sway_submit_wire.json", SerializeActiveSwayEnvelope12002(formal,
        "submit-active-scheme-sway-v1-private-" + suffix, "fixture-submit"));
    formal.receipt_mode = true; ++f.epoch;
    Check(VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(access, formal.ack, formal.receipt) ==
        ActiveSchemeSemanticActionV1PrivateReceiptStatus::red && !formal.receipt.postcondition_verified,
        "ACK alone is not the start postcondition");
    f.Add(1, 1); // Engine's next pump creates a complete-ID instance; generation zero is legitimate.
    Check(VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(access, formal.ack, formal.receipt) ==
        ActiveSchemeSemanticActionV1PrivateReceiptStatus::applied &&
        formal.receipt.scheme_instance_id == 1 && formal.receipt.scheme_instance_generation == 0,
        "fresh actual instance validates start receipt with generation zero");
    Save(output, "ck3_12002_sway_receipt_wire.json", SerializeActiveSwayEnvelope12002(formal,
        "receipt-active-scheme-sway-v1-private-" + suffix, "fixture-receipt"));
    ActiveSchemeStateV1PrivateObservation active{};
    Check(ReadActiveSwayState12002(f.source, f.epoch, active) && active.row_count == 1 &&
        active.rows[0].progress.value == 355 && active.rows[0].progress_goal.value == 365 &&
        active.rows[0].success_chance.status == ActiveSchemeStateV1PrivateValueStatus::not_applicable,
        "basic Sway real progress and nonapplicable complex metrics");
    f.Add(2, 0x04000002, false);
    Check(ReadActiveSwayState12002(f.source, f.epoch, active) && active.row_count == 2 &&
        active.rows[1].scheme_instance_generation == 4 &&
        active.rows[1].progress.status == ActiveSchemeStateV1PrivateValueStatus::unavailable,
        "other owner scheme remains counted with opaque fields");
    query.active = active; query.matching = true;
    Check(ReadSwayCommandTermsV1(f.command.bindings, actor_id, target_id, f.epoch, query.terms),
        "active Sway read terms after start");
    const auto active_wire = SerializeActiveSwayEnvelope12002(query,
        "query-active-scheme-sway-target-v1-private-" + suffix, "fixture-active-read");
    Check(active_wire.find("\"progress\":355") != std::string::npos &&
        active_wire.find("\"active_scheme_count\":2") != std::string::npos &&
        active_wire.find("\"native_legal_now\":false") != std::string::npos,
        "active serializer publishes actual Sway progress and other owner occupancy");
    Save(output, "ck3_12002_sway_active_wire.json", active_wire);
    Put(f.block.data() + 0x358, 0x10, std::uint32_t{2});
    Check(!ReadActiveSwayState12002(f.source, f.epoch, active),
        "actual full-ID storage slot roundtrip is required");
    std::cout << "PASS Sway new active reader, real command provider, pending/start receipt and native serializer\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
#endif
