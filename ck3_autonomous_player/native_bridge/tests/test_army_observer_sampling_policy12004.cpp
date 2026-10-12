#include "xar_bridge/army_observer_research_sampling_12004.hpp"
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12004;
using army_observer_research_detail_12004::Permit;
using army_observer_research_detail_12004::Policy;
unsigned assertions = 0;
void Require(bool ok, const char *message) {
  ++assertions;
  if (!ok) throw std::runtime_error(message);
}

// One owner mutex; only journal storage is local, policy is the actual header.
struct Owner {
  std::mutex mutex;
  Policy policy;
  std::vector<unsigned> journal;
  unsigned clears = 0;
  bool Set(bool requested) {
    const std::lock_guard lock(mutex);
    return policy.SetLocked(requested, [&] { ++clears; journal.clear(); });
  }
  auto State() {
    const std::lock_guard lock(mutex);
    return policy.StateLocked(true, journal.size(), journal.size());
  }
  bool Readable() {
    const std::lock_guard lock(mutex);
    return policy.ReadableLocked();
  }
  unsigned ClearCalls() {
    const std::lock_guard lock(mutex);
    return clears;
  }
  void Seed(unsigned value) {
    const std::lock_guard lock(mutex);
    journal.push_back(value);
  }
  bool Publish(const Permit &permit, unsigned value) {
    const std::lock_guard lock(mutex);
    if (!permit.CanPublishLocked()) return false;
    journal.push_back(value);
    return true;
  }
};

void DefaultOffNoAdmission() {
  Owner owner;
  const auto initial = owner.State();
  Require(initial.available && !initial.enabled && !initial.busy && initial.clear_completed &&
              initial.epoch == 0 && initial.active_captures == 0 &&
              initial.retained_records == 0 && initial.qualified_records == 0,
          "default: off, clear, empty");
  Require(!owner.Readable(), "off read denied");
  {
    Permit permit(owner.mutex, owner.policy);
    Require(!permit.admitted(), "off admission denied");
    Require(!owner.Publish(permit, 1), "off publish denied");
    Require(owner.State().active_captures == 0, "off active zero");
  }
  Require(owner.ClearCalls() == 0 && owner.State().epoch == 0,
          "off destructor: no clear/epoch");
}

void EnableIsIdempotent() {
  Owner owner;
  owner.Seed(7);
  Require(owner.Set(true), "enable ACK");
  const auto on = owner.State();
  Require(on.enabled && !on.busy && !on.clear_completed && on.epoch == 1 &&
              on.retained_records == 0 && owner.ClearCalls() == 1,
          "first enable: clear once, epoch one");
  owner.Seed(8);
  Require(owner.Set(true), "repeat enable ACK");
  const auto repeated = owner.State();
  Require(repeated.enabled && repeated.epoch == on.epoch &&
              repeated.retained_records == 1 && owner.ClearCalls() == 1,
          "repeat enable: epoch/storage unchanged");
  Require(owner.Readable(), "enabled idle read gate");
}

void EnabledActiveRepeat() {
  Owner owner;
  Require(owner.Set(true), "enable ACK");
  const auto before = owner.State();
  {
    Permit permit(owner.mutex, owner.policy);
    Require(permit.admitted(), "enabled admission");
    Require(!owner.Readable(), "inflight read denied");
    Require(owner.Set(true), "enabled active repeat ACK");
    const auto repeated = owner.State();
    Require(repeated.enabled && repeated.busy && repeated.active_captures == 1 &&
                repeated.epoch == before.epoch &&
                repeated.clear_completed == before.clear_completed && owner.ClearCalls() == 1,
            "active repeat: epoch/active/clear unchanged");
  }
  Require(owner.State().active_captures == 0 && owner.State().enabled,
          "destructor drains, owner stays enabled");
}

void BusyDisableCannotReopen() {
  Owner owner;
  Require(owner.Set(true), "enable ACK");
  owner.Seed(9);
  const auto before = owner.State();
  {
    Permit permit(owner.mutex, owner.policy);
    Require(owner.Set(false), "inflight disable returns");
    const auto off = owner.State();
    Require(!off.enabled && off.busy && !off.clear_completed && off.active_captures == 1 &&
                off.epoch == before.epoch && off.retained_records == 1 && owner.ClearCalls() == 1,
            "inflight disable: off, busy, pending clear");
    // ACK does not claim enabled; actual state proves refusal.
    Require(owner.Set(true), "busy reopen ACK");
    const auto denied = owner.State();
    Require(!denied.enabled && denied.busy && denied.epoch == before.epoch &&
                denied.retained_records == 1 && owner.ClearCalls() == 1 && !owner.Readable(),
            "disabled active reopen denied; storage retained");
  }
}

void OldPermitCannotPublishLate() {
  Owner owner;
  Require(owner.Set(true), "enable ACK");
  {
    Permit permit(owner.mutex, owner.policy);
    Require(permit.admitted() && owner.Publish(permit, 10),
            "current permit publishes");
    Require(owner.Set(false), "disable ACK");
    Require(!owner.Publish(permit, 11) && owner.State().retained_records == 1,
            "old permit late append denied");
  }
}

void DrainNeedsOneExplicitClear() {
  Owner owner;
  Require(owner.Set(true), "enable ACK");
  owner.Seed(12);
  const auto before = owner.State();
  {
    Permit permit(owner.mutex, owner.policy);
    Require(permit.admitted() && owner.Set(false), "admitted disable ACK");
  }
  const auto drained = owner.State();
  Require(!drained.enabled && !drained.busy && drained.active_captures == 0 &&
              !drained.clear_completed && drained.epoch == before.epoch &&
              drained.retained_records == 1 && owner.ClearCalls() == 1,
          "destructor: drain only, no clear/epoch");
  Require(owner.Set(false), "drained disable ACK");
  const auto cleared = owner.State();
  Require(cleared.clear_completed && !cleared.busy && cleared.epoch == before.epoch + 1 &&
              cleared.retained_records == 0 && cleared.qualified_records == 0 &&
              owner.ClearCalls() == 2,
          "drained retry: clear/epoch once");
  Require(owner.Set(false), "idle repeat disable ACK");
  Require(owner.State().epoch == cleared.epoch && owner.ClearCalls() == 2,
          "idle repeat: no clear/epoch");
}
} // namespace

int main() {
  try {
    DefaultOffNoAdmission(); EnableIsIdempotent(); EnabledActiveRepeat();
    BusyDisableCannotReopen(); OldPermitCannotPublishLate(); DrainNeedsOneExplicitClear();
    std::cout << "{\"status\":\"passed\",\"cases\":6,\"assertions\":" << assertions
              << ",\"actual_pure_header\":true,\"live_ck3\":false}\n";
    return EXIT_SUCCESS;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return EXIT_FAILURE;
  }
}
