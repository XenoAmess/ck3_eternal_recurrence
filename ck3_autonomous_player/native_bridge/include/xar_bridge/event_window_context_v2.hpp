#pragma once

#include "xar_bridge/event_window_context_v1.hpp"
#include <variant>

namespace xar::game {

struct EventGuiAvailabilityObservedV2 {
  bool is_valid = false;
  friend bool operator==(const EventGuiAvailabilityObservedV2 &,
                         const EventGuiAvailabilityObservedV2 &) = default;
};

enum class EventGuiAvailabilityFailureV2 {
  native_binding_unavailable,
  native_read_unavailable,
};

struct EventGuiAvailabilityUnobservedV2 {
  EventGuiAvailabilityFailureV2 reason =
      EventGuiAvailabilityFailureV2::native_binding_unavailable;
  friend bool operator==(const EventGuiAvailabilityUnobservedV2 &,
                         const EventGuiAvailabilityUnobservedV2 &) = default;
};

using EventGuiAvailabilityObservationV2 =
    std::variant<EventGuiAvailabilityObservedV2,
                 EventGuiAvailabilityUnobservedV2>;

struct EventOptionGuiObservationV2 {
  std::int32_t rendered_index = -1;
  std::int32_t native_option_index = -1;
  EventGuiAvailabilityObservationV2 gui_availability =
      EventGuiAvailabilityUnobservedV2{};
  friend bool operator==(const EventOptionGuiObservationV2 &,
                         const EventOptionGuiObservationV2 &) = default;
};

struct EventWindowContextV2 {
  // The v1 projection remains the sole producer of raw enabled and all other
  // existing presentation fields. Observations bind to its exact row indices.
  EventWindowContextV1 presentation;
  std::vector<EventOptionGuiObservationV2> gui_observations;
  friend bool operator==(const EventWindowContextV2 &,
                         const EventWindowContextV2 &) = default;
};

} // namespace xar::game
