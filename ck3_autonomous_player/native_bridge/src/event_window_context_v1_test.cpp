#include "xar_bridge/event_window_context_v1.hpp"
#include "xar_bridge/event_window_context_v1_mailbox.hpp"

#include <windows.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace {

constexpr std::int32_t kEventId = 0x01000029;
constexpr std::uint64_t kRevision = 17;
void *g_local_player = nullptr;
void *g_active_event = nullptr;

void *GetLocalPlayer(void *) { return g_local_player; }
void *GetCurrentEvent(void *) { return g_active_event; }

template <typename T>
void Store(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}

void StoreInlineString(void *object, const char *value) {
  const auto size = std::strlen(value);
  std::memcpy(object, value, size);
  Store<std::uint64_t>(object, 0x10, size);
  Store<std::uint64_t>(object, 0x18, 15);
}

struct Fixture {
  std::array<std::byte, 0xB0> game_state{};
  std::array<std::byte, 0x30> jomini{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x80> local_player{};
  std::array<std::byte, 0x20> game_data{};
  std::array<std::byte, 0x1C0> active_event{};
  std::array<std::byte, 0x1C0> event_definition{};
  std::array<std::byte, 0x98> idler{};
  std::array<std::byte, 0x30> manager{};
  std::array<void *, 2> windows{};
  std::array<std::byte, 0x838> window{};
  std::array<std::byte, 0x838> secondary_window{};
  std::array<std::byte, 0x370> option_items{};
  void *game_state_pointer = game_state.data();
  void *jomini_pointer = jomini.data();
  xar::ck3_11906::Bindings bindings{};

  Fixture() {
    g_local_player = local_player.data();
    g_active_event = active_event.data();
    Store<std::int32_t>(game_state.data(), 0x08, 741221);
    Store<std::int32_t>(game_state.data(), 0x70, 0);
    Store<void *>(game_state.data(), 0xA0, game_data.data());
    Store<void *>(jomini.data(), 0x10, idler.data());
    Store<void *>(jomini.data(), 0x18, players.data());
    Store<std::uint8_t>(jomini.data(), 0x20, 1);
    Store<std::int32_t>(players.data(), 0x1F0, 0);
    Store<std::int32_t>(local_player.data(), 0x70, 0);
    Store<void *>(active_event.data(), 0x1B0, event_definition.data());
    Store<std::int32_t>(active_event.data(), 0x1BC, kEventId);
    Store<std::int32_t>(event_definition.data(), 0x1BC, 4);

    bindings.enabled = true;
    bindings.game_state_slot = &game_state_pointer;
    bindings.jomini_state_slot = &jomini_pointer;
    bindings.get_local_player = &GetLocalPlayer;
    bindings.get_current_event = &GetCurrentEvent;
    bindings.event_manager_offset = 0;
    bindings.ingame_interface_idler_vtable = 0x140B1D30;
    bindings.event_window_primary_vtable = 0x1417F758;
    Store<std::uintptr_t>(idler.data(), 0,
                          bindings.ingame_interface_idler_vtable);
    Store<void *>(idler.data(), 0x28, manager.data());
    windows[0] = window.data();
    Store<void *>(manager.data(), 0x10, windows.data());
    Store<std::int32_t>(manager.data(), 0x1C, 1);
    Store<std::uintptr_t>(window.data(), 0,
                          bindings.event_window_primary_vtable);
    auto *data = window.data() + 0xE8;
    Store<std::int32_t>(data, 0x00, kEventId);
    Store<void *>(data, 0x10, option_items.data());
    Store<std::int32_t>(data, 0x18, 2);
    Store<std::int32_t>(data, 0x1C, 1);
    Store<std::int32_t>(data, 0x2C, 3);
    InitializeOption(0, 3, false, true);
  }

  void InitializeOption(std::size_t rendered, std::int32_t native_index,
                        bool enabled, bool fallback) {
    auto *const item = option_items.data() + rendered * 0x1B8;
    Store<void *>(item, 0x160, window.data() + 0xE8);
    StoreInlineString(item + 0x170, rendered == 0 ? "Wait" : "Leave");
    StoreInlineString(item + 0x190,
                      enabled ? "" : "Not today");
    Store<std::int32_t>(item, 0x1B0, native_index);
    Store<std::uint8_t>(item, 0x1B4, enabled ? 1 : 0);
    Store<std::uint8_t>(item, 0x1B5, fallback ? 1 : 0);
  }
};

bool ExpectUnavailable(Fixture &fixture, std::string_view reason) {
  xar::game::EventWindowContextV1 output{};
  return xar::ck3_11906::ReadEventWindowContextV1(
             fixture.bindings, kRevision, kEventId, output) ==
             xar::game::ReadEventWindowContextResultV1::unavailable &&
         output.unavailable_reason == reason;
}

bool TestReader() {
  Fixture fixture;
  xar::game::EventWindowContextV1 output{};
  if (xar::ck3_11906::ReadEventWindowContextV1(
          fixture.bindings, kRevision, kEventId, output) !=
          xar::game::ReadEventWindowContextResultV1::available ||
      output.status != xar::game::EventWindowContextStatusV1::available ||
      output.options.size() != 1 || output.options[0].rendered_index != 0 ||
      output.options[0].native_option_index != 3 ||
      output.options[0].shown != true || output.options[0].enabled != false ||
      output.options[0].fallback != true || output.options[0].cancel != true ||
      output.options[0].resolved_name != "Wait" ||
      output.options[0].unavailable_reason != "Not today") {
    return false;
  }
  Store<std::int32_t>(fixture.window.data() + 0xE8, 0x00,
                      kEventId + 1);
  if (xar::ck3_11906::ReadEventWindowContextV1(
          fixture.bindings, kRevision, kEventId, output) !=
          xar::game::ReadEventWindowContextResultV1::unavailable ||
      output.unavailable_reason != "event_window_not_materialized") {
    return false;
  }
  Store<std::int32_t>(fixture.window.data() + 0xE8, 0x00, kEventId);
  fixture.InitializeOption(1, 3, true, false);
  Store<std::int32_t>(fixture.window.data() + 0xE8, 0x1C, 2);
  if (xar::ck3_11906::ReadEventWindowContextV1(
          fixture.bindings, kRevision, kEventId, output) !=
          xar::game::ReadEventWindowContextResultV1::unavailable ||
      output.unavailable_reason != "event_window_layout_invalid") {
    return false;
  }
  Store<std::int32_t>(fixture.window.data() + 0xE8, 0x1C, 1);
  fixture.windows[0] = nullptr;
  return xar::ck3_11906::ReadEventWindowContextV1(
             fixture.bindings, kRevision, kEventId, output) ==
             xar::game::ReadEventWindowContextResultV1::unavailable &&
         output.unavailable_reason == "event_window_layout_invalid";
}

bool TestReaderProductionGates() {
  {
    Fixture fixture;
    fixture.windows[1] = fixture.secondary_window.data();
    Store<std::uintptr_t>(fixture.secondary_window.data(), 0,
                          fixture.bindings.event_window_primary_vtable);
    Store<std::int32_t>(fixture.secondary_window.data() + 0xE8, 0x00,
                        kEventId);
    Store<std::int32_t>(fixture.manager.data(), 0x1C, 2);
    if (!ExpectUnavailable(fixture, "event_window_ambiguous")) {
      return false;
    }
  }
  {
    Fixture fixture;
    Store<std::uintptr_t>(fixture.idler.data(), 0,
                          fixture.bindings.ingame_interface_idler_vtable + 8);
    if (!ExpectUnavailable(fixture, "ingame_idler_unavailable")) {
      return false;
    }
  }
  {
    Fixture fixture;
    Store<std::uintptr_t>(fixture.window.data(), 0,
                          fixture.bindings.event_window_primary_vtable + 8);
    if (!ExpectUnavailable(fixture, "event_window_layout_invalid")) {
      return false;
    }
  }
  for (const auto count : std::array<std::int32_t, 2>{-1, 33}) {
    Fixture fixture;
    Store<std::int32_t>(fixture.manager.data(), 0x1C, count);
    if (!ExpectUnavailable(fixture, "event_window_vector_invalid")) {
      return false;
    }
  }
  for (const auto [count, capacity] :
       std::array<std::array<std::int32_t, 2>, 3>{
           std::array<std::int32_t, 2>{-1, 2},
           std::array<std::int32_t, 2>{2, 1},
           std::array<std::int32_t, 2>{1, 65}}) {
    Fixture fixture;
    Store<std::int32_t>(fixture.window.data() + 0xE8, 0x1C, count);
    Store<std::int32_t>(fixture.window.data() + 0xE8, 0x18, capacity);
    if (!ExpectUnavailable(fixture, "event_window_layout_invalid")) {
      return false;
    }
  }
  {
    Fixture fixture;
    Store<void *>(fixture.option_items.data(), 0x160, nullptr);
    if (!ExpectUnavailable(fixture, "event_window_layout_invalid")) {
      return false;
    }
  }
  {
    Fixture fixture;
    Store<std::uint64_t>(fixture.option_items.data() + 0x170, 0x10,
                         16'385);
    if (!ExpectUnavailable(fixture, "event_window_layout_invalid")) {
      return false;
    }
  }
  {
    Fixture fixture;
    Store<std::uint64_t>(fixture.option_items.data() + 0x170, 0x10, 10);
    Store<std::uint64_t>(fixture.option_items.data() + 0x170, 0x18, 9);
    if (!ExpectUnavailable(fixture, "event_window_layout_invalid")) {
      return false;
    }
  }
  for (const auto offset : std::array<std::size_t, 2>{0x1B4, 0x1B5}) {
    Fixture fixture;
    Store<std::uint8_t>(fixture.option_items.data(), offset, 2);
    if (!ExpectUnavailable(fixture, "event_window_layout_invalid")) {
      return false;
    }
  }
  {
    Fixture fixture;
    Store<std::int32_t>(fixture.window.data() + 0xE8, 0x2C, 4);
    xar::game::EventWindowContextV1 output{};
    if (xar::ck3_11906::ReadEventWindowContextV1(
            fixture.bindings, kRevision, kEventId, output) !=
            xar::game::ReadEventWindowContextResultV1::available ||
        output.options.size() != 1 ||
        output.options[0].rendered_index != 0 ||
        output.options[0].native_option_index != 3 ||
        output.options[0].cancel) {
      return false;
    }
  }
  return true;
}

bool TestMailbox() {
  Fixture fixture;
  xar::game::Snapshot snapshot{};
  if (!xar::ck3_11906::ReadSnapshot(fixture.bindings, snapshot)) {
    return false;
  }
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::EventWindowContextMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 9;
  query.bindings = fixture.bindings;
  query.expected_snapshot = snapshot;
  query.expected_snapshot_revision = kRevision;
  query.expected_event_instance_id = kEventId;
  const auto thread_id = GetCurrentThreadId();
  mailbox.state.store(
      xar::ck3_11906::MainThreadQueryMailboxStateV1::executing);
  mailbox.published_sequence.store(query.ticket.sequence);
  mailbox.owner_thread_id.store(thread_id);
  mailbox.paused_owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor =
      &xar::ck3_11906::ExecuteEventWindowContextMailboxQueryV1;
  mailbox.executor_context = &query;
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 3;
  stamp.thread_id = thread_id;
  stamp.paused = true;
  stamp.date_raw = snapshot.date_raw;
  stamp.tls_initialized_flag_address = 1;
  stamp.tls_initialized = 1;
  stamp.tls_context = 2;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = reinterpret_cast<std::uintptr_t>(
      fixture.jomini.data());
  stamp.game_state = reinterpret_cast<std::uintptr_t>(
      fixture.game_state.data());
  return xar::ck3_11906::ExecuteEventWindowContextMailboxQueryV1(
             &query, stamp) &&
         query.completion == xar::ck3_11906::
                                 EventWindowContextMailboxCompletionV1::completed &&
         query.executor_invocations == 1 &&
         query.result.status ==
             xar::game::EventWindowContextStatusV1::available;
}

} // namespace

int main() {
  if (!TestReader()) {
    std::cerr << "event-window synthetic reader fixture failed\n";
    return 1;
  }
  if (!TestReaderProductionGates()) {
    std::cerr << "event-window production gate fixture failed\n";
    return 1;
  }
  if (!TestMailbox()) {
    std::cerr << "event-window owning-thread mailbox fixture failed\n";
    return 1;
  }
  return 0;
}
