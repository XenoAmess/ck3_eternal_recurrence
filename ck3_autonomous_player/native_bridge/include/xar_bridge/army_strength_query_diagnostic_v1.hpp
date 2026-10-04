#pragma once

#include <atomic>
#include <cstdint>
#include <string>

namespace xar::ck3_12002 {

// Progress for the existing army-strength command's failure text only.
// Fixed stage literals remain readable when the executor exits abnormally.
struct ArmyStrengthQueryDiagnosticV1 {
  std::atomic<const char *> worker{"not_started"};
  std::atomic<const char *> native{"not_started"};
  std::atomic<const char *> reader{"not_started"};
  std::atomic<std::int64_t> army_id{-1}, scope_rows{-1}, baseline_result{-1};
  std::atomic<std::int64_t> pre_snapshot{-1}, paused{-1}, map_ready{-1};
  std::atomic<std::int64_t> submit{-1}, wait{-1}, reclaim{-1};
  std::atomic<std::int64_t> enter_result{-1}, entered{-1};
  std::atomic<std::int64_t> native_snapshot{-1}, native_returned{-1};
  std::atomic<std::int64_t> finish_result{-1}, frame_stable{-1}, run_success{-1};

  void Reset() noexcept {
    worker.store("not_started"); native.store("not_started"); reader.store("not_started");
    army_id.store(-1); scope_rows.store(-1); baseline_result.store(-1);
    pre_snapshot.store(-1); paused.store(-1); map_ready.store(-1);
    submit.store(-1); wait.store(-1); reclaim.store(-1);
    enter_result.store(-1); entered.store(-1);
    native_snapshot.store(-1); native_returned.store(-1);
    finish_result.store(-1); frame_stable.store(-1); run_success.store(-1);
  }

  std::string FailureSuffix() const {
    std::string text = " [worker=";
    text += worker.load(); text += ";native="; text += native.load();
    text += ";reader="; text += reader.load();
    const auto add = [&text](const char *key, const std::atomic<std::int64_t> &value) {
      text += ';'; text += key; text += '='; text += std::to_string(value.load());
    };
    add("army_id", army_id); add("scope_rows", scope_rows); add("baseline_result", baseline_result);
    add("pre_snapshot", pre_snapshot); add("paused", paused); add("map_ready", map_ready);
    add("submit", submit); add("wait", wait); add("reclaim", reclaim);
    add("enter_result", enter_result); add("entered", entered);
    add("native_snapshot", native_snapshot); add("native_returned", native_returned);
    add("finish_result", finish_result); add("frame_stable", frame_stable); add("run_success", run_success);
    text += ']';
    return text;
  }
};

inline ArmyStrengthQueryDiagnosticV1 g_army_strength_query_diagnostic_v1;

} // namespace xar::ck3_12002
