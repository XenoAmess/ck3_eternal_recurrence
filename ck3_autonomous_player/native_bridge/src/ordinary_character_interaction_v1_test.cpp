#include "xar_bridge/ordinary_character_interaction_v1.hpp"

#include <bit>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

using namespace xar::ck3_12003::ordinary_interaction;
using Request = xar::ck3_12003::OrdinaryInteractionRequestV1;
namespace {
int checks = 0;
void Check(bool condition, const char *name) {
  if (!condition) { std::fprintf(stderr, "FAIL: %s\n", name); std::exit(1); }
  ++checks;
}
template <typename T> void Put(void *p, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *p, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(value)); return value;
}
struct Fixture;
Fixture *f = nullptr;
void Destroy(void *);
void *DeleteClone(void *, std::uint32_t);
void **Clone(const void *, void **);
struct Fixture {
  alignas(8) std::array<std::byte, 0x2720> definition{};
  alignas(8) std::array<std::byte, 0x1D8> actor{}, recipient{};
  alignas(8) std::array<std::byte, 0x30> storage{}, slots{};
  alignas(8) std::array<std::byte, 0xE60> options{};
  alignas(8) std::array<std::uintptr_t, 9> primary{};
  alignas(8) std::array<std::uintptr_t, 5> secondary{};
  void *storage_pointer = storage.data();
  std::string key = "generic_fixture_interaction";
  std::int32_t hash = std::bit_cast<std::int32_t>(std::uint32_t{0xFEDCBA98});
  bool shown = true, legal = true, automatic = false, trigger_mode = false;
  bool special = false, selected = false, constructor_fail = false, partial_constructor_fail = false;
  bool command_fail = false, command_partial_fail = false, wrong_primary = false, wrong_secondary = false;
  bool queue_accepts = true, clone_empty = false, mutate_recipient = false;
  bool score_bad_return = false, outer_bad_status = false;
  int destroys = 0, context_calls = 0, send_calls = 0, queue_calls = 0, clone_calls = 0, clone_deletes = 0;
  int reads = 0, refreshes = 0, finalizes = 0;
  int frame_calls = 0, frame_allow_count = 2;
  bool retained_context = false, channel_ok = false, role_argument_bits_ok = false;
  std::uint32_t option_count = 0;
  Fixture() {
    f = this;
    Put(definition.data(), 0x14, hash);
    Put(definition.data(), 0x18, key.c_str());
    Put(definition.data(), 0x28, static_cast<std::uint64_t>(key.size()));
    Put(definition.data(), 0x30, static_cast<std::uint64_t>(key.size()));
    Put(definition.data(), 0x2258, static_cast<void *>(options.data()));
    Put(definition.data(), 0x2264, std::int32_t{0});
    Put(storage.data(), 0x20, static_cast<void *>(slots.data()));
    Put(storage.data(), 0x2C, std::int32_t{3});
    Put(slots.data(), 0x18, static_cast<void *>(actor.data()));
    Put(slots.data(), 0x28, static_cast<void *>(recipient.data()));
    Put(actor.data(), 0x18, std::uint32_t{0x01000001});
    Put(recipient.data(), 0x18, std::uint32_t{0x80000002});
    Put(options.data(), 0x368, std::uint32_t{10});
    Put(options.data(), 0x730 + 0x368, std::uint32_t{20});
    primary[0] = reinterpret_cast<std::uintptr_t>(DeleteClone);
    primary[8] = reinterpret_cast<std::uintptr_t>(Clone);
  }
  void Options(std::uint32_t count) { option_count = count; Put(definition.data(), 0x2264, static_cast<std::int32_t>(count)); }
  Request RequestValue() const { return {key, 0x80000002, 9, 0x01000001, 42, 3}; }
};
void *Database() { return f; }
std::int32_t Hash(void *database, const char *key, std::uint32_t length) {
  Check(database == f && std::string_view(key, length) == f->key, "native hash exact bytes/length"); return f->hash;
}
void *Lookup(void *database, std::int32_t hash) {
  Check(database == f && hash == f->hash, "native lookup actual hash"); return f->definition.data();
}
void *Construct(void *context, void *definition, std::int32_t actor,
                std::int32_t recipient, void *optional, bool redirect) {
  ++f->context_calls;
  f->role_argument_bits_ok = actor == 0x01000001 &&
      std::bit_cast<std::uint32_t>(recipient) == 0x80000002 && optional == nullptr && redirect;
  if (f->constructor_fail && !f->partial_constructor_fail) return nullptr;
  Put(context, 0, definition);
  Put(context, 0x2D8, std::uint32_t{0x11000001}); // Actual redirected values.
  Put(context, 0x2DC, std::uint32_t{0xA0000002});
  Put(context, 0x2E0, std::uint32_t{0xF1000001});
  Put(context, 0x2E4, UINT32_MAX);
  Put(context, 0x2E8, UINT32_MAX);
  Put(context, 0x2EC, std::uint32_t{0x01000001});
  Put(context, 0x330, f->special ? static_cast<void *>(f) : nullptr);
  return f->constructor_fail ? nullptr : context;
}
void Refresh(void *, bool all) { Check(all, "full native refresh"); ++f->refreshes; }
void Finalize(void *) { ++f->finalizes; }
void Destroy(void *) { ++f->destroys; }
bool Shown(void *) { return f->shown; }
bool Legal(void *, void *tooltip) {
  Check(tooltip == nullptr, "complete CanSend null tooltip");
  if (f->mutate_recipient) Put(f->recipient.data(), 0x18, std::uint32_t{0x81000002});
  return f->legal;
}
bool Option(void *, std::uint32_t flag) { ++f->reads; return f->selected && flag == 20; }
void Costs(const void *declared, const void *context, std::int64_t *raw) {
  Check(declared == f->definition.data() + 0x40, "native cost declaration offset");
  Check(Get<void *>(static_cast<const std::byte *>(context) - 8, 0) == f->definition.data(), "native cost exact constructed context");
  for (int i = 0; i < 10; ++i) raw[i] = i == 0 ? -123456 : (i + 1) * 100001LL;
}
bool Trigger(void *trigger, const void *) { Check(trigger == f, "actual auto accept trigger"); return f->automatic; }
std::int64_t *RecipientScore(void *, std::int64_t *raw) { *raw = -7654321; return f->score_bad_return ? nullptr : raw; }
std::int64_t *IntermediaryScore(void *, std::int64_t *raw) { *raw = 2345678; return raw; }
std::uint8_t Outer(void *, std::uint8_t a, std::uint8_t b, void *c, void *d) {
  Check(a == 1 && b == 1 && c == nullptr && d == nullptr, "outer answer complete ABI"); return f->outer_bad_status ? 3 : 2;
}
void *ConstructSend(void *command, const void *context) {
  ++f->send_calls;
  f->retained_context = f->destroys == 0 && Get<void *>(context, 0) == f->definition.data();
  if (f->command_fail && !f->command_partial_fail) return nullptr;
  Put(command, 0, f->wrong_primary ? std::uintptr_t{1} : reinterpret_cast<std::uintptr_t>(f->primary.data()));
  Put(command, 0x18, f->wrong_secondary ? std::uintptr_t{2} : reinterpret_cast<std::uintptr_t>(f->secondary.data()));
  std::memcpy(static_cast<std::byte *>(command) + 0x20, context, kNativeContextBytes);
  return f->command_fail ? nullptr : command;
}
void *DeleteClone(void *command, std::uint32_t flags) {
  Check(flags == 1, "native deleting destructor flag");
  ++f->clone_deletes; Destroy(static_cast<std::byte *>(command) + 0x20);
  delete[] static_cast<std::byte *>(command); return nullptr;
}
void **Clone(const void *command, void **result) {
  ++f->clone_calls;
  if (f->clone_empty) return result;
  auto *copy = new std::byte[kNativeCommandBytes];
  std::memcpy(copy, command, kNativeCommandBytes); *result = copy; return result;
}
bool Queue(void *manager, void **owned, std::uint32_t flags) {
  ++f->queue_calls;
  f->channel_ok = manager == f && flags == 0x0E;
  Check(f->destroys == 0 && *owned != nullptr, "original context remains live through clone and queue");
  Check(Get<void *>(*owned, 0x20) == f->definition.data(), "queue receives actual copied definition");
  DeleteClone(*owned, 1); *owned = nullptr; return f->queue_accepts;
}
bool VerifyFrame(void *context) noexcept {
  Check(context == f, "internal frame callback exact owner context");
  return ++f->frame_calls <= f->frame_allow_count;
}
Bindings Bind() {
  Bindings b{}; b.enabled = true;
  auto &i = b.interaction; i.enabled = true; i.core.enabled = true;
  i.core.character_storage_slot = &f->storage_pointer;
  i.refresh = Refresh; i.finalize = Finalize; i.validate = Legal; i.destroy = Destroy;
  i.recipient_answer_score = RecipientScore; i.intermediary_answer_score = IntermediaryScore;
  i.evaluate_cost = Costs; i.evaluate_trigger = Trigger; i.construct_send_command = ConstructSend;
  i.send_primary_vtable = reinterpret_cast<std::uintptr_t>(f->primary.data());
  i.send_secondary_vtable = reinterpret_cast<std::uintptr_t>(f->secondary.data());
  i.commands.enabled = true; i.commands.command_manager = f; i.commands.queue_owned_command = Queue;
  b.get_database = Database; b.stable_hash = Hash; b.lookup_definition = Lookup;
  b.construct_two_role = Construct; b.is_shown = Shown; b.read_option = Option; b.outer_answer = Outer;
  b.dispatch_frame_context = f; b.verify_dispatch_frame = VerifyFrame;
  return b;
}
void CheckNoDispatch(const SendObservation &s, const char *name) {
  Check(!s.dispatch_invoked && !s.native_call_completed && s.native_queue_result == QueueResult::not_attempted &&
        f->queue_calls == 0 && f->clone_calls == 0, name);
}
} // namespace

int main() {
  {
    Check(!BindOrdinaryInteractionImage12003(0, kExecutableSha256).enabled, "zero image rejected");
    Check(!BindOrdinaryInteractionImage12003(0x1000, "wrong").enabled, "wrong exact build rejected");
    auto b = BindOrdinaryInteractionImage12003(0x1000, kExecutableSha256);
    Check(b.enabled && reinterpret_cast<std::uintptr_t>(b.construct_two_role) == 0x3077C90 &&
          reinterpret_cast<std::uintptr_t>(b.interaction.core.character_storage_slot) == 0x5C68568,
          "independent exact .3 bindings");
  }
  {
    Fixture fixture; Observation o{};
    Check(ReadOrdinaryInteractionContextV1(Bind(), fixture.RequestValue(), o), "complete context available");
    Check(o.native_context_available && o.ordinary_context_supported && o.unavailable_reason == nullptr &&
          o.unsupported_reason == nullptr && o.actor_binding_verified && o.recipient_binding_verified, "available shape/proofs");
    Check(fixture.role_argument_bits_ok && o.effective_roles[0] == 0x11000001U &&
          o.effective_roles[1] == 0xA0000002U && o.effective_roles[2] == 0xF1000001U &&
          !o.effective_roles[3] && !o.effective_roles[4] && o.effective_roles[5] == 0x01000001U,
          "high generation and actual redirected roles preserved");
    Check(o.costs_raw && (*o.costs_raw)[0] == -123456 && (*o.costs_raw)[9] == 1000010 &&
          o.recipient_score_raw == -7654321 && o.intermediary_score_raw == 2345678 &&
          o.outer_answer_status == 2 && o.definition_stable_hash == 0xFEDCBA98U,
          "all10 signed native costs and answers preserved");
    Check(fixture.context_calls == 1 && fixture.destroys == 1 && fixture.refreshes == 1 && fixture.finalizes == 1,
          "query native lifecycle exactly once");
  }
  {
    Fixture fixture; auto request = fixture.RequestValue(); request.recipient_id = 2;
    Observation o{}; Check(!ReadOrdinaryInteractionContextV1(Bind(), request, o) &&
          o.actor_binding_verified && !o.recipient_binding_verified && fixture.context_calls == 0,
          "low24 alias rejected by full generation");
  }
  {
    Fixture fixture; Put(fixture.recipient.data(), 0x18, std::uint32_t{0x81000002});
    Observation o{}; Check(!ReadOrdinaryInteractionContextV1(Bind(), fixture.RequestValue(), o), "stale generation rejected");
  }
  {
    Fixture fixture; fixture.definition[0x18] = std::byte{}; // Null heap key, same hash.
    Observation o{}; Check(!ReadOrdinaryInteractionContextV1(Bind(), fixture.RequestValue(), o) && fixture.context_calls == 0,
          "hash match without canonical key rejected");
  }
  {
    Fixture fixture; auto collision = fixture.key; collision[0] = 'G'; Put(fixture.definition.data(), 0x18, collision.c_str());
    Observation o{}; Check(!ReadOrdinaryInteractionContextV1(Bind(), fixture.RequestValue(), o) && fixture.context_calls == 0,
          "same hash same length different key rejected");
  }
  for (int which = 0; which < 2; ++which) {
    Fixture fixture; fixture.shown = which != 0; fixture.legal = which == 0;
    Observation o{}; Check(ReadOrdinaryInteractionContextV1(Bind(), fixture.RequestValue(), o) &&
          o.shown == fixture.shown && o.can_send == fixture.legal, "false legality is successful actual query");
    fixture.destroys = 0; SendObservation s{}; InitiateOrdinaryInteractionV1(Bind(), fixture.RequestValue(), s);
    CheckNoDispatch(s, "false Shown/CanSend never dispatches"); Check(fixture.destroys == 1, "refused send cleans rebuilt context");
  }
  {
    Fixture fixture; fixture.Options(2); fixture.selected = true;
    Observation o{}; Check(ReadOrdinaryInteractionContextV1(Bind(), fixture.RequestValue(), o) &&
          !o.ordinary_context_supported && o.declared_option_count == 2U && o.selected_option_count == 1U &&
          o.shown == true && o.costs_raw.has_value(), "unsupported options retain actual terms/default selections");
    fixture.destroys = 0; SendObservation s{}; InitiateOrdinaryInteractionV1(Bind(), fixture.RequestValue(), s);
    CheckNoDispatch(s, "declared options never sent by zero-option scope");
  }
  {
    Fixture fixture; fixture.special = true; SendObservation s{};
    InitiateOrdinaryInteractionV1(Bind(), fixture.RequestValue(), s);
    Check(s.preflight_context.native_context_available && s.preflight_context.special_payload_present == true &&
          !s.preflight_context.ordinary_context_supported, "actual special payload observed");
    CheckNoDispatch(s, "special payload never sent"); Check(fixture.destroys == 1, "special context cleanup");
  }
  for (int which = 0; which < 2; ++which) {
    Fixture fixture; Put(which == 0 ? fixture.actor.data() : fixture.recipient.data(), 0x1D0, static_cast<void *>(&fixture));
    SendObservation s{}; InitiateOrdinaryInteractionV1(Bind(), fixture.RequestValue(), s);
    Check(s.preflight_context.native_context_available &&
          (which == 0 ? s.preflight_context.actor_alive : s.preflight_context.recipient_alive) == false, "actual dead is complete query");
    CheckNoDispatch(s, "dead character blocks send");
  }
  for (bool partial : {false, true}) {
    Fixture fixture; fixture.constructor_fail = true; fixture.partial_constructor_fail = partial;
    SendObservation s{}; InitiateOrdinaryInteractionV1(Bind(), fixture.RequestValue(), s);
    Check(!s.preflight_context.native_context_available && !s.preflight_context.shown &&
          !s.preflight_context.costs_raw && !s.preflight_context.definition_stable_hash,
          "failed constructor nulls incomplete terms");
    Check(fixture.destroys == (partial ? 1 : 0), "partial context cleaned only after actual definition initialized");
    CheckNoDispatch(s, "failed context constructor never dispatches");
  }
  for (bool partial : {false, true}) {
    Fixture fixture; fixture.command_fail = true; fixture.command_partial_fail = partial;
    SendObservation s{}; InitiateOrdinaryInteractionV1(Bind(), fixture.RequestValue(), s);
    Check(fixture.retained_context && fixture.destroys == (partial ? 2 : 1), "failed send constructor lifetime/partial cleanup");
    CheckNoDispatch(s, "failed command constructor never dispatches");
  }
  for (int which = 0; which < 2; ++which) {
    Fixture fixture; fixture.wrong_primary = which == 0; fixture.wrong_secondary = which == 1;
    SendObservation s{}; InitiateOrdinaryInteractionV1(Bind(), fixture.RequestValue(), s);
    CheckNoDispatch(s, "both native vtables independently gate dispatch");
    Check(fixture.destroys == 2 && fixture.send_calls == 1, "vtable failure destroys both caller-owned contexts");
  }
  for (bool accepts : {true, false}) {
    Fixture fixture; fixture.queue_accepts = accepts; SendObservation s{};
    InitiateOrdinaryInteractionV1(Bind(), fixture.RequestValue(), s);
    Check(s.native_call_completed && s.dispatch_invoked &&
          s.native_queue_result == (accepts ? QueueResult::submitted : QueueResult::rejected), "actual native queue result retained");
    Check(fixture.queue_calls == 1 && fixture.clone_calls == 1 && fixture.send_calls == 1 && fixture.channel_ok &&
          fixture.retained_context && fixture.clone_deletes == 1 && fixture.destroys == 3 && fixture.frame_calls == 2,
          "one clone one queue correct allocator cleanup/lifetime");
    Check((s.reason == nullptr) == accepts, "only submitted result has null reason");
  }
  {
    Fixture fixture; fixture.clone_empty = true; SendObservation s{};
    InitiateOrdinaryInteractionV1(Bind(), fixture.RequestValue(), s);
    Check(s.dispatch_invoked && s.native_call_completed && s.native_queue_result == QueueResult::unavailable &&
          fixture.clone_calls == 1 && fixture.queue_calls == 0 && fixture.destroys == 2,
          "SubmitCommandCopy invocation remains pending even clone unavailable");
  }
  {
    Fixture fixture; fixture.mutate_recipient = true; SendObservation s{};
    InitiateOrdinaryInteractionV1(Bind(), fixture.RequestValue(), s);
    CheckNoDispatch(s, "final full generation reread blocks recipient changed during evaluation");
    Check(fixture.send_calls == 0 && fixture.destroys == 1, "changed recipient cleans context before command");
  }
  for (int which = 0; which < 4; ++which) {
    Fixture fixture; auto b = Bind();
    if (which == 0) b.verify_dispatch_frame = nullptr;
    if (which == 1) b.dispatch_frame_context = nullptr;
    if (which == 2) fixture.frame_allow_count = 0;
    if (which == 3) fixture.frame_allow_count = 1;
    SendObservation s{}; InitiateOrdinaryInteractionV1(b, fixture.RequestValue(), s);
    CheckNoDispatch(s, "missing/failed actual owner callback blocks dispatch");
    Check(fixture.send_calls == (which == 3 ? 1 : 0) && fixture.destroys == (which == 3 ? 2 : 1),
          "frame guards run before ctor and again immediately before queue");
  }
  for (int which = 0; which < 3; ++which) {
    Fixture fixture; auto b = Bind();
    if (which == 0) b.interaction.evaluate_cost = nullptr;
    if (which == 1) fixture.score_bad_return = true;
    if (which == 2) fixture.outer_bad_status = true;
    Observation o{}; Check(!ReadOrdinaryInteractionContextV1(b, fixture.RequestValue(), o) &&
          !o.native_context_available && !o.costs_raw && !o.shown && !o.outer_answer_status &&
          !o.effective_roles[0] && !o.declared_option_count, "incomplete final sample atomically unavailable");
  }
  {
    Fixture fixture; fixture.trigger_mode = true; fixture.automatic = true;
    Put(fixture.definition.data(), 0x2290, static_cast<void *>(&fixture));
    Observation o{}; Check(ReadOrdinaryInteractionContextV1(Bind(), fixture.RequestValue(), o) &&
          o.auto_accept == true, "actual trigger auto accept observed");
  }
  {
    Fixture fixture; Put(fixture.definition.data(), 0x2718, std::uint8_t{1}); Observation o{};
    Check(ReadOrdinaryInteractionContextV1(Bind(), fixture.RequestValue(), o) &&
          o.auto_accept == true, "actual scalar auto accept observed");
  }
  {
    Fixture fixture; auto request = fixture.RequestValue(); request.interaction_key = "illegal-key";
    Observation o{}; Check(!ReadOrdinaryInteractionContextV1(Bind(), request, o) && fixture.context_calls == 0,
          "bad key rejected before native calls");
  }
  std::printf("PASS: %d leaf checks; offline fixture-owned memory/functions only\n", checks);
  return 0;
}
