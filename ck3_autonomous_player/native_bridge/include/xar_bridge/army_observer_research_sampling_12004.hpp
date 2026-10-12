#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>
#include <mutex>

namespace xar::ck3_12004 {

// Sampling state is independent of every native binding and observed DTO.
// It describes retained research evidence, never Army or forecast readiness.
struct ArmyObserverResearchSamplingState12004 {
  bool available = false;
  bool enabled = false;
  bool busy = false;
  bool clear_completed = false;
  std::uint64_t epoch = 0;
  std::uint64_t active_captures = 0;
  std::size_t retained_records = 0;
  std::size_t qualified_records = 0;
};

namespace army_observer_research_detail_12004 {
// Every access is protected by the owner's existing journal mutex. Keeping
// policy and journal under one lock makes disable/clear/publication atomic.
struct Policy {
  bool enabled = false;
  bool clear_completed = true;
  std::uint64_t epoch = 0;
  std::uint64_t active = 0;

  bool ReadableLocked() const noexcept { return enabled && active == 0; }

  ArmyObserverResearchSamplingState12004 StateLocked(
      bool available, std::size_t retained, std::size_t qualified) const noexcept {
    return {available, enabled, active != 0, clear_completed, epoch, active,
            retained, qualified};
  }

  template<class Clear> bool SetLocked(bool requested, Clear clear) {
    if (requested) {
      if (enabled || active != 0) return true;
      if (epoch == (std::numeric_limits<std::uint64_t>::max)()) return false;
      clear();
      ++epoch;
      clear_completed = false;
      enabled = true;
    } else {
      enabled = false;
      if (active != 0) return true;
      if (!clear_completed) {
        if (epoch == (std::numeric_limits<std::uint64_t>::max)()) return false;
        clear();
        ++epoch;
        clear_completed = true;
      }
    }
    return true;
  }
};

class Permit {
 public:
  Permit(std::mutex &mutex, Policy &policy) noexcept
      : mutex_(mutex), policy_(policy) {
    try {
      const std::lock_guard lock(mutex_);
      if (policy_.enabled &&
          policy_.active != (std::numeric_limits<std::uint64_t>::max)()) {
        epoch_ = policy_.epoch;
        ++policy_.active;
        admitted_ = true;
      }
    } catch (...) {}
  }
  ~Permit() {
    if (!admitted_) return;
    try {
      const std::lock_guard lock(mutex_);
      if (policy_.active != 0) --policy_.active;
    } catch (...) {}
  }
  Permit(const Permit &) = delete;
  Permit &operator=(const Permit &) = delete;
  bool admitted() const noexcept { return admitted_; }
  // The caller holds the same journal mutex through the actual publication.
  bool CanPublishLocked() const noexcept {
    return admitted_ && policy_.enabled && policy_.epoch == epoch_;
  }
 private:
  std::mutex &mutex_;
  Policy &policy_;
  std::uint64_t epoch_ = 0;
  bool admitted_ = false;
};
} // namespace army_observer_research_detail_12004
} // namespace xar::ck3_12004
