#pragma once

#include "xar_bridge/ck3_12002_event_window_context_v2_query.hpp"

#include <cstdint>
#include <optional>
#include <type_traits>

namespace xar::ck3_12002 {

enum class EventWindowMailboxKindV2 { event_window, incompatible };

// A view over the existing worker-owned query, not a second envelope or lease.
// The caller retains this context and every referenced object until matching
// terminal completion/reclaim. The parsed request fields remain immutable.
struct EventWindowMailboxContextV2 {
  QueryMailboxEnvelope &envelope;
  EventWindowMailboxKindV2 kind;
  std::uintptr_t image_base;
  EventWindowGuiRequestVersionV2 version;
  std::int32_t event_instance_id;
  bool &typed_result;
  std::optional<bool> &executor_enter;
  std::optional<bool> &executor_typed_result;
  std::optional<bool> &executor_finish;
  game::EventWindowContextV1 &presentation;
  game::EventWindowContextV2 &gui;
};

bool ExecuteEventWindowContextMailboxV2(
    void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

static_assert(std::is_same_v<decltype(&ExecuteEventWindowContextMailboxV2),
                            ck3_11906::MainThreadQueryExecutorV1>);

} // namespace xar::ck3_12002
