#include "xar_bridge/current_timeline_blocker_context_v1.hpp"

#include <array>
#include <string>

namespace xar::ck3_11906 {
namespace {

using Identity = xar::game::CurrentTimelineBlockerIdentityV1;
using ReadResult = xar::game::ReadCurrentTimelineBlockerContextResultV1;
using Status = xar::game::CurrentTimelineBlockerStatusV1;

constexpr std::string_view kSimulationUnknown =
    "succession_simulation_block_predicate_not_frozen";

void SetUnknown(xar::game::TimelineBlockerTypedBooleanV1 &field,
                std::string_view reason) {
  field.available = false;
  field.value = false;
  field.unavailable_reason.assign(reason);
}

void SetKnown(xar::game::TimelineBlockerTypedBooleanV1 &field, bool value) {
  field.available = true;
  field.value = value;
  field.unavailable_reason.clear();
}

void MakeUnavailable(const CurrentTimelineBlockerReadRequestV1 &request,
                     xar::game::CurrentTimelineBlockerContextV1 &output,
                     std::string_view reason) {
  output = {};
  output.status = Status::unavailable;
  output.snapshot_revision = request.snapshot_revision;
  output.date_raw = request.date_raw;
  output.unavailable_reason.assign(reason);
  SetUnknown(output.blocks_simulation, reason);
  SetUnknown(output.can_continue, reason);
}

bool Visible(const CurrentTimelineWidgetObservationV1 &widget) {
  return widget.exists && widget.effective_visible;
}

bool Actionable(const CurrentTimelineWidgetObservationV1 &widget) {
  return Visible(widget) && widget.enabled;
}

void SetEvidence(xar::game::CurrentTimelineBlockerContextV1 &output,
                 std::string_view root, std::string_view decisive) {
  output.evidence.source_kind =
      "exact-build-stock-gui-plus-native-widget-state";
  output.evidence.source_path.assign(kCurrentTimelineBlockerStockGuiPath);
  output.evidence.root_name.assign(root);
  output.evidence.decisive_widget_name.assign(decisive);
}

void AppendJsonString(std::string &output, std::string_view value) {
  output.push_back('"');
  for (const unsigned char byte : value) {
    switch (byte) {
    case '"':
      output += "\\\"";
      break;
    case '\\':
      output += "\\\\";
      break;
    case '\b':
      output += "\\b";
      break;
    case '\f':
      output += "\\f";
      break;
    case '\n':
      output += "\\n";
      break;
    case '\r':
      output += "\\r";
      break;
    case '\t':
      output += "\\t";
      break;
    default:
      if (byte < 0x20U) {
        constexpr char hex[] = "0123456789ABCDEF";
        output += "\\u00";
        output.push_back(hex[(byte >> 4U) & 0xFU]);
        output.push_back(hex[byte & 0xFU]);
      } else {
        output.push_back(static_cast<char>(byte));
      }
    }
  }
  output.push_back('"');
}

void AppendTypedBoolean(std::string &output,
                        const xar::game::TimelineBlockerTypedBooleanV1 &field) {
  output += "{\"status\":";
  AppendJsonString(output, field.available ? "available" : "unavailable");
  output += ",\"value\":";
  if (field.available) {
    output += field.value ? "true" : "false";
  } else {
    output += "null";
  }
  output += ",\"unavailable_reason\":";
  if (field.available) {
    output += "null";
  } else {
    AppendJsonString(output, field.unavailable_reason);
  }
  output.push_back('}');
}

std::string_view IdentityName(Identity identity) {
  switch (identity) {
  case Identity::none:
    return "none";
  case Identity::death_succession_modal:
    return "death_succession_modal";
  case Identity::game_over_modal:
    return "game_over_modal";
  case Identity::succession_select_destiny_modal:
    return "succession_select_destiny_modal";
  }
  return {};
}

} // namespace

ReadResult ReadCurrentTimelineBlockerContextV1(
    const CurrentTimelineBlockerReadRequestV1 &request,
    const CurrentTimelineBlockerSourceV1 &source,
    xar::game::CurrentTimelineBlockerContextV1 &output) noexcept {
  try {
    if (request.snapshot_revision == 0 || !request.paused ||
        source.observe_fixed_widget == nullptr) {
      MakeUnavailable(request, output, "invalid_query_boundary");
      return ReadResult::unavailable;
    }

    std::array<CurrentTimelineWidgetObservationV1,
               kCurrentTimelineFixedWidgetCountV1>
        widgets{};
    for (std::size_t index = 0; index < widgets.size(); ++index) {
      if (!source.observe_fixed_widget(
              source.context, static_cast<CurrentTimelineFixedWidgetV1>(index),
              widgets[index])) {
        MakeUnavailable(request, output, "fixed_widget_observation_failed");
        return ReadResult::unavailable;
      }
    }

    const auto &succession = widgets[0];
    const auto &bottom = widgets[1];
    const auto &close = widgets[2];
    const auto &menu = widgets[3];
    const auto &destiny = widgets[4];
    const auto &destiny_continue = widgets[5];
    const auto &destiny_continue_random = widgets[6];
    const auto &destiny_cancel = widgets[7];
    const bool succession_visible = Visible(succession);
    const bool destiny_visible = Visible(destiny);

    if (succession_visible && destiny_visible) {
      MakeUnavailable(request, output, "multiple_timeline_surfaces_visible");
      return ReadResult::unavailable;
    }

    output = {};
    output.status = Status::available;
    output.snapshot_revision = request.snapshot_revision;
    output.date_raw = request.date_raw;
    SetUnknown(output.blocks_simulation, kSimulationUnknown);

    if (destiny_visible) {
      output.identity = Identity::succession_select_destiny_modal;
      SetKnown(output.can_continue, Actionable(destiny_continue) ||
                                        Actionable(destiny_continue_random));
      SetEvidence(output, "succession_select_destiny_window",
                  output.can_continue.value
                      ? "continue_button"
                      : (Actionable(destiny_cancel) ? "cancel_button"
                                                    : "destiny_root"));
      return ReadResult::available;
    }

    if (!succession_visible) {
      output.identity = Identity::none;
      SetUnknown(output.can_continue, "no_supported_timeline_surface_visible");
      SetEvidence(output, "none", "none");
      return ReadResult::available;
    }

    // The stock GUI exposes menu_button only when GetPlayerHeir is invalid.
    // This is the supported game-over identity, regardless of whether the
    // separate observer/change-character controls are also available.
    if (Actionable(menu)) {
      output.identity = Identity::game_over_modal;
      SetKnown(output.can_continue, false);
      SetEvidence(output, "succession_event_window", "menu_button");
      return ReadResult::available;
    }

    // `bottom` is controlled by SuccessionEventWindow.IsSuccession. A visible,
    // enabled close_button then provides the exact stock continuation control.
    if (Visible(bottom) && Actionable(close)) {
      output.identity = Identity::death_succession_modal;
      SetKnown(output.can_continue, true);
      SetEvidence(output, "succession_event_window", "close_button");
      return ReadResult::available;
    }

    MakeUnavailable(request, output, "succession_surface_semantics_ambiguous");
    return ReadResult::unavailable;
  } catch (...) {
    MakeUnavailable(request, output, "internal_error");
    return ReadResult::unavailable;
  }
}

std::string SerializeCurrentTimelineBlockerContextV1(
    const xar::game::CurrentTimelineBlockerContextV1 &context) {
  const auto identity = IdentityName(context.identity);
  if (context.snapshot_revision == 0 || identity.empty() ||
      (context.status == Status::available &&
       !context.unavailable_reason.empty()) ||
      (context.status == Status::unavailable &&
       context.unavailable_reason.empty())) {
    return {};
  }
  std::string output = "{\"schema\":\"current-timeline-blocker-context-v1\",";
  output += "\"schema_version\":1,\"status\":";
  AppendJsonString(output, context.status == Status::available ? "available"
                                                               : "unavailable");
  output +=
      ",\"snapshot_revision\":" + std::to_string(context.snapshot_revision);
  output += ",\"date_raw\":" + std::to_string(context.date_raw);
  output += ",\"identity\":";
  AppendJsonString(output, identity);
  output += ",\"blocks_simulation\":";
  AppendTypedBoolean(output, context.blocks_simulation);
  output += ",\"can_continue\":";
  AppendTypedBoolean(output, context.can_continue);
  output += ",\"evidence_source\":{\"kind\":";
  AppendJsonString(output, context.evidence.source_kind);
  output += ",\"path\":";
  AppendJsonString(output, context.evidence.source_path);
  output += ",\"root_name\":";
  AppendJsonString(output, context.evidence.root_name);
  output += ",\"decisive_widget_name\":";
  AppendJsonString(output, context.evidence.decisive_widget_name);
  output += "},\"unavailable_reason\":";
  if (context.status == Status::available) {
    output += "null";
  } else {
    AppendJsonString(output, context.unavailable_reason);
  }
  output.push_back('}');
  return output;
}

} // namespace xar::ck3_11906
