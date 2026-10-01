#include "xar_bridge/ck3_12002_events.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
using namespace xar::ck3_12002;
template <class T> void Put(std::span<std::byte> data, std::size_t offset, T value) {
  std::memcpy(data.data() + offset, &value, sizeof(value));
}
template <class T> T Get(const void *data, std::size_t offset) {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(data) + offset, sizeof(result));
  return result;
}
void *local_player = nullptr;
void *active_event = nullptr;
void *expected_event_manager = nullptr;
EventCommand queued{};
std::uint32_t queued_flags = 0;
int queue_calls = 0;
bool queue_accept = true;
bool validate_accept = true;
void *GetPlayer(void *) { return local_player; }
void *GetEvent(void *manager) {
  return manager == expected_event_manager ? active_event : nullptr;
}
bool ForCharacter(void *pending, void *character) {
  if (Get<std::uint32_t>(pending, 0x14) != 0x4368496eU ||
      Get<std::int32_t>(pending, 0x10) == -1) {
    return false;
  }
  const auto route = Get<std::int32_t>(pending, 0x5C0);
  const auto recipient = route == 1 ? 0x300 : 0x2F4;
  return route >= 0 && route <= 2 &&
         Get<std::int32_t>(pending, recipient) == Get<std::int32_t>(character, 0x18);
}
bool Validate(void *command) {
  return validate_accept || Get<std::int32_t>(command, 0x24) == 4;
}
bool Queue(void *, void *command, std::uint32_t flags) noexcept {
  ++queue_calls;
  std::memcpy(&queued, command, sizeof(queued));
  queued_flags = flags;
  return queue_accept;
}

struct Fixture {
  static constexpr std::int32_t character_id = 0x03000001;
  static constexpr std::int32_t pending_id = 0x04000002;
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xE0> record{};
  std::array<void *, 1> records{record.data()};
  std::array<std::byte, 0x30> character_storage{}, pending_storage{};
  std::array<std::byte, 0x40> character_slots{}, pending_slots{};
  std::array<std::byte, 0x1D8> character{};
  std::array<std::byte, 0x5C8> pending{};
  std::array<std::byte, 0x1C8> event{}, definition{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *character_storage_ptr = character_storage.data();
  void *pending_storage_ptr = pending_storage.data();
  EventsBindings bindings{};

  Fixture() {
    Put(state, 8, std::int32_t{53175816});
    Put(state, 0x70, std::int32_t{2});
    Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data());
    jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7});
    Put(player, 0x70, std::int32_t{7});
    Put(std::span(data), 0x222E8 + 0x58, records.data());
    Put(std::span(data), 0x222E8 + 0x64, std::int32_t{1});
    Put(record, 0xD8, std::int32_t{7});
    Put(record, 0xB0, character_id);
    Put(character_storage, 0x20, character_slots.data());
    Put(character_storage, 0x2C, std::int32_t{4});
    Put(character_slots, 0x18, character.data());
    Put(character, 0x18, character_id);
    Put(pending_storage, 0x20, pending_slots.data());
    Put(pending_storage, 0x2C, std::int32_t{4});
    Put(pending_slots, 0x28, pending.data());
    Put(pending, 0x10, pending_id);
    Put(pending, 0x14, std::uint32_t{0x4368496e});
    Put(pending, 0x2F0, std::int32_t{0x05000003});
    Put(pending, 0x2F4, character_id);
    Put(pending, 0x300, std::int32_t{-1});
    Put(event, 0x1B0, definition.data());
    Put(event, 0x1BC, std::int32_t{19});
    Put(definition, 0x1AC, std::int32_t{2});
    // The former option-count field is a deliberately incompatible decoy.
    Put(definition, 0x1BC, std::int32_t{19});
    bindings.core = {true, &state_ptr, &jomini_ptr, &character_storage_ptr, &GetPlayer};
    bindings.image_base = 0x140000000;
    bindings.get_current_event = &GetEvent;
    bindings.pending_interaction_storage_slot = &pending_storage_ptr;
    bindings.is_pending_for_character = &ForCharacter;
    bindings.validate_reply = &Validate;
    bindings.submit_command = &Queue;
    local_player = player.data();
    active_event = event.data();
    expected_event_manager = data.data() + 0x34480;
  }
};

bool Check() {
  using namespace xar::game;
  Fixture f{};
  Snapshot snapshot{};
  snapshot.played_character_spouse_ids = {77};
  if (!ReadEventsSnapshot(f.bindings, snapshot) ||
      !snapshot.has_active_event || snapshot.active_event_instance_id != 19 ||
      snapshot.active_event_option_count != 2 ||
      !snapshot.has_pending_character_interaction ||
      snapshot.pending_character_interaction_id != Fixture::pending_id ||
      snapshot.pending_sender_character_id != 0x05000003 ||
      snapshot.pending_auto_accept_notification ||
      snapshot.played_character_spouse_ids != std::vector<std::int32_t>{77}) return false;
  if (SubmitSelectEventOption(f.bindings, 2) != SelectEventOptionResult::option_out_of_range ||
      SubmitSelectEventOption(f.bindings, -1) != SelectEventOptionResult::option_out_of_range ||
      queue_calls != 0) return false;
  if (SubmitSelectEventOption(f.bindings, 1) != SelectEventOptionResult::submitted ||
      queued.instance_id != 19 || queued.choice != 1 || queued_flags != 7 ||
      queued.primary_vtable != 0x1447733D0 || queued.secondary_vtable != 0x144773530 ||
      queued.flags != 0) return false;
  for (auto byte : queued.reserved) if (byte != std::byte{}) return false;
  if (SubmitReplyToPendingInteraction(f.bindings, PendingInteractionReply::accept) !=
          ReplyPendingInteractionResult::submitted || queued.choice != 0 ||
      queued.instance_id != Fixture::pending_id || queued_flags != 0x0E ||
      queued.primary_vtable != 0x14448BC18 || queued.secondary_vtable != 0x14448BBE8) return false;
  if (SubmitReplyToPendingInteraction(f.bindings, PendingInteractionReply::reject) !=
          ReplyPendingInteractionResult::submitted || queued.choice != 1) return false;
  f.pending[0x5C6] = std::byte{1};
  validate_accept = false; // Native auto-accept notifications bypass reply legality.
  if (!ReadEventsSnapshot(f.bindings, snapshot) ||
      !snapshot.pending_auto_accept_notification ||
      SubmitReplyToPendingInteraction(f.bindings, PendingInteractionReply::accept) !=
          ReplyPendingInteractionResult::acknowledgement_required ||
      SubmitAcknowledgePendingInteraction(f.bindings, Fixture::pending_id) !=
          AcknowledgePendingInteractionResult::submitted || queued.choice != 4 ||
      queued_flags != 0x0E) return false;
  if (SubmitAcknowledgePendingInteraction(f.bindings, 0x05000002) !=
          AcknowledgePendingInteractionResult::pending_interaction_mismatch ||
      ResolveEventsPending(f.bindings, 0x05000002) != nullptr) return false;
  f.jomini[0x20] = std::byte{};
  if (SubmitAcknowledgePendingInteraction(f.bindings, Fixture::pending_id) !=
          AcknowledgePendingInteractionResult::requires_paused) return false;
  f.jomini[0x20] = std::byte{1};
  queue_accept = false;
  if (SubmitAcknowledgePendingInteraction(f.bindings, Fixture::pending_id) !=
          AcknowledgePendingInteractionResult::queue_rejected ||
      SubmitSelectEventOption(f.bindings, 0) != SelectEventOptionResult::unavailable) return false;
  queue_accept = true;
  // Alternate-recipient route must follow its own native identity slot.
  Put(f.pending, 0x5C0, std::int32_t{1});
  if (!ReadEventsSnapshot(f.bindings, snapshot) || snapshot.has_pending_character_interaction) return false;
  Put(f.pending, 0x300, Fixture::character_id);
  if (!ReadEventsSnapshot(f.bindings, snapshot) || !snapshot.has_pending_character_interaction) return false;
  Put(f.pending, 0x10, std::int32_t{0x04000001});
  if (!ReadEventsSnapshot(f.bindings, snapshot) || snapshot.has_pending_character_interaction) return false;
  Put(f.pending, 0x10, Fixture::pending_id);
  active_event = nullptr;
  if (!ReadEventsSnapshot(f.bindings, snapshot) || snapshot.has_active_event ||
      SubmitSelectEventOption(f.bindings, 0) != SelectEventOptionResult::no_active_event) return false;
  active_event = f.event.data();
  Put(f.definition, 0x1AC, std::int32_t{-1});
  if (ReadEventsSnapshot(f.bindings, snapshot)) return false;
  Put(f.definition, 0x1AC, std::int32_t{2});
  f.pending_storage_ptr = nullptr;
  if (ReadEventsSnapshot(f.bindings, snapshot)) return false;
  local_player = nullptr;
  if (!ReadEventsSnapshot(f.bindings, snapshot) || snapshot.has_active_event ||
      snapshot.has_pending_character_interaction) return false;
  const auto bound = BindEventsImage(0x140000000, kExecutableSha256);
  return bound.core.enabled &&
         reinterpret_cast<std::uintptr_t>(bound.pending_interaction_storage_slot) == 0x145D1EC80 &&
         reinterpret_cast<std::uintptr_t>(bound.is_pending_for_character) == 0x14136D1B0 &&
         !BindEventsImage(0x140000000, "wrong-build").core.enabled;
}
} // namespace

int main() {
  if (!Check()) { std::cerr << "FAIL events/pending offline fixture\n"; return 1; }
  std::cout << "PASS CK3 1.20.0.2 events/pending offline fixture\n";
}
