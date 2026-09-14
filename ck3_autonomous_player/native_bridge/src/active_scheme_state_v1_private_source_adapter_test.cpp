#include "xar_bridge/active_scheme_state_v1_private_source_adapter.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <array>
#include <cassert>
#include <string_view>

namespace {

using Access = xar::bridge::ActiveSchemeStateV1PrivateSourceAccess;
using Container = xar::bridge::ActiveSchemeStateV1PrivateSourceContainer;
using Failure = xar::bridge::ActiveSchemeStateV1PrivateSourceFailure;
using Frame = xar::bridge::ActiveSchemeStateV1PrivateSourceFrame;
using Result = xar::bridge::ActiveSchemeStateV1PrivateSourceResult;
using Root = xar::bridge::ActiveSchemeStateV1PrivateSourceRoot;
using Row = xar::bridge::ActiveSchemeStateV1PrivateCapturedRow;
using TargetKind = xar::bridge::ActiveSchemeStateV1PrivateTargetKind;
using ValueStatus = xar::bridge::ActiveSchemeStateV1PrivateValueStatus;

template <std::size_t Size>
void SetKey(std::array<char, Size> &output, std::string_view value) {
  assert(value.size() < output.size());
  output.fill('\0');
  std::copy(value.begin(), value.end(), output.begin());
}

template <typename T>
void SetAvailable(xar::bridge::ActiveSchemeStateV1PrivateValue<T> &output,
                  T value) {
  output.status = ValueStatus::available;
  output.value = value;
}

Row MurderRow() {
  Row row{};
  row.scheme_identity_round_trip = true;
  row.scheme_instance_id = 456;
  row.scheme_instance_generation = 7;
  row.owner_character_id = 123;
  SetKey(row.scheme_type_key, "murder");
  SetKey(row.category_key, "hostile");
  row.target_identity_round_trip = true;
  row.target_kind = TargetKind::character;
  row.target_id = 789;
  row.definition_flags_verified = true;
  row.is_secret = true;
  SetAvailable(row.progress, 6);
  SetAvailable(row.progress_goal, 10);
  SetAvailable(row.success_chance, 63);
  SetAvailable(row.maximum_success_chance, 95);
  SetAvailable(row.secrecy, 72);
  SetAvailable(row.opportunity_charges, 2);
  SetAvailable(row.breaches, 1);
  SetAvailable(row.maximum_breaches, 5);
  SetAvailable(row.phases_remaining_until_opportunity, 1);
  return row;
}

Row SwayRow() {
  Row row{};
  row.scheme_identity_round_trip = true;
  row.scheme_instance_id = 457;
  row.scheme_instance_generation = 2;
  row.owner_character_id = 123;
  SetKey(row.scheme_type_key, "sway");
  SetKey(row.category_key, "personal");
  row.target_identity_round_trip = true;
  row.target_kind = TargetKind::character;
  row.target_id = 790;
  row.definition_flags_verified = true;
  row.is_basic = true;
  SetAvailable(row.progress, 3);
  SetAvailable(row.progress_goal, 10);
  return row;
}

struct Fixture {
  std::array<Frame, 2> frames{};
  std::array<Root, 2> roots{};
  std::array<Container, 2> containers{};
  std::array<std::array<Row, 2>, 2> rows{};
  std::size_t frame_calls = 0;
  std::size_t root_calls = 0;
  std::size_t container_calls = 0;
  std::size_t row_calls = 0;
  std::size_t fail_frame_call = 0;
  std::size_t fail_root_call = 0;
  std::size_t fail_container_call = 0;
  std::size_t fail_row_call = 0;

  Fixture() {
    frames.fill(Frame{44, 53183856, 123, true});
    roots.fill(Root{true, 0x1000, 11, 3});
    containers.fill(Container{true, 0x2000, 22, 4, 123, 2});
    rows[0][0] = MurderRow();
    rows[0][1] = SwayRow();
    rows[1] = rows[0];
  }
};

bool Capture(void *context, Frame &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.frame_calls;
  if (fixture.frame_calls == fixture.fail_frame_call) return false;
  output = fixture.frames[fixture.frame_calls > 1 ? 1 : 0];
  return true;
}

bool ResolveRoot(void *context, std::int64_t played_character_id,
                 Root &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.root_calls;
  if (fixture.root_calls == fixture.fail_root_call ||
      played_character_id != 123) {
    return false;
  }
  output = fixture.roots[fixture.root_calls > 1 ? 1 : 0];
  return true;
}

bool ResolveContainer(void *context, const Root &root,
                      std::int64_t played_character_id,
                      Container &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.container_calls;
  if (fixture.container_calls == fixture.fail_container_call ||
      played_character_id != 123) {
    return false;
  }
  const auto pass = fixture.container_calls > 1 ? 1U : 0U;
  if (root.native_address != fixture.roots[pass].native_address) return false;
  output = fixture.containers[pass];
  return true;
}

bool ReadRow(void *context, const Root &root, const Container &container,
             std::size_t index, Row &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.row_calls;
  if (fixture.row_calls == fixture.fail_row_call) return false;
  const auto first_count = fixture.containers[0].row_count;
  const auto pass = fixture.row_calls > first_count ? 1U : 0U;
  if (root.native_address != fixture.roots[pass].native_address ||
      container.native_address !=
          fixture.containers[pass].native_address ||
      index >= fixture.rows[pass].size()) {
    return false;
  }
  output = fixture.rows[pass][index];
  return true;
}

Access MakeAccess(Fixture &fixture) {
  Access access{};
  access.exact_build_admitted = true;
  access.admitted_executable_sha256 = xar::bridge::
      kActiveSchemeStateV1PrivateObserverExecutableSha256;
  access.current_thread_id = 77;
  access.application_main_thread_id = 77;
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.resolve_root = &ResolveRoot;
  access.resolve_container = &ResolveContainer;
  access.read_row = &ReadRow;
  return access;
}

void ExpectFailure(Access access, Failure failure,
                   xar::bridge::ActiveSchemeStateV1PrivateFailure
                       core_failure) {
  Result result{};
  result.observation.status =
      xar::bridge::ActiveSchemeStateV1PrivateStatus::available;
  result.observation.row_count = 1;
  assert(!xar::bridge::ObserveActiveSchemeStateV1PrivateSource(access,
                                                               result));
  assert(result.failure == failure);
  assert(result.core_failure == core_failure);
  assert(result.observation.status ==
         xar::bridge::ActiveSchemeStateV1PrivateStatus::unavailable);
  assert(result.observation.row_count == 0);
  assert(!xar::bridge::ActiveSchemeStateV1PrivateSourceFailureName(failure)
              .empty());
}

void TestStableTransactionReResolvesAndPublishes() {
  Fixture fixture{};
  Result result{};
  assert(xar::bridge::ObserveActiveSchemeStateV1PrivateSource(
      MakeAccess(fixture), result));
  assert(result.failure == Failure::none);
  assert(result.core_failure ==
         xar::bridge::ActiveSchemeStateV1PrivateFailure::none);
  assert(result.observation.status ==
         xar::bridge::ActiveSchemeStateV1PrivateStatus::available);
  assert(result.observation.row_count == 2);
  assert(result.observation.rows[0].scheme_instance_id == 456);
  assert(result.observation.rows[0].success_chance.value == 63);
  assert(result.observation.rows[0].secrecy.value == 72);
  assert(result.observation.rows[0].opportunity_charges.value == 2);
  assert(result.observation.rows[0].breaches.value == 1);
  assert(result.observation.rows[1].success_chance.status ==
         ValueStatus::not_applicable);
  assert(fixture.frame_calls == 2);
  assert(fixture.root_calls == 2);
  assert(fixture.container_calls == 2);
  assert(fixture.row_calls == 4);
}

void TestAdmissionAndThreadGatesPrecedeNativeReads() {
  Fixture fixture{};
  auto access = MakeAccess(fixture);
  access.admitted_executable_sha256 = "wrong";
  ExpectFailure(access, Failure::exact_build_mismatch,
                xar::bridge::ActiveSchemeStateV1PrivateFailure::
                    exact_build_mismatch);
  assert(fixture.frame_calls == 0);

  fixture = {};
  access = MakeAccess(fixture);
  access.read_row = nullptr;
  ExpectFailure(access, Failure::callbacks_unavailable,
                xar::bridge::ActiveSchemeStateV1PrivateFailure::
                    source_adapter_unavailable);
  assert(fixture.frame_calls == 0);

  fixture = {};
  access = MakeAccess(fixture);
  access.current_thread_id = 78;
  ExpectFailure(access, Failure::not_application_main_thread,
                xar::bridge::ActiveSchemeStateV1PrivateFailure::
                    not_application_main_thread);
  assert(fixture.frame_calls == 0);
}

void TestRootAndContainerDriftFailClosed() {
  Fixture fixture{};
  fixture.roots[1].generation++;
  ExpectFailure(MakeAccess(fixture), Failure::root_drift,
                xar::bridge::ActiveSchemeStateV1PrivateFailure::
                    container_drift);
  assert(fixture.root_calls == 2);
  assert(fixture.container_calls == 1);

  fixture = {};
  fixture.containers[1].generation++;
  ExpectFailure(MakeAccess(fixture), Failure::container_drift,
                xar::bridge::ActiveSchemeStateV1PrivateFailure::
                    container_drift);
  assert(fixture.container_calls == 2);

  fixture = {};
  fixture.containers[0].row_count =
      xar::bridge::kActiveSchemeStateV1PrivateMaximumRows + 1;
  ExpectFailure(MakeAccess(fixture), Failure::row_count_invalid,
                xar::bridge::ActiveSchemeStateV1PrivateFailure::
                    row_count_invalid);
  assert(fixture.row_calls == 0);
}

void TestRowFrameAndCoreDriftFailClosed() {
  Fixture fixture{};
  fixture.rows[1][0].secrecy.value++;
  ExpectFailure(MakeAccess(fixture), Failure::row_drift,
                xar::bridge::ActiveSchemeStateV1PrivateFailure::
                    scheme_identity_unavailable);

  fixture = {};
  fixture.frames[1].date_raw++;
  ExpectFailure(MakeAccess(fixture), Failure::frame_drift,
                xar::bridge::ActiveSchemeStateV1PrivateFailure::frame_drift);

  fixture = {};
  fixture.frames[0].paused = false;
  fixture.frames[1].paused = false;
  ExpectFailure(MakeAccess(fixture), Failure::not_paused,
                xar::bridge::ActiveSchemeStateV1PrivateFailure::not_paused);
  assert(fixture.root_calls == 0);

  fixture = {};
  SetKey(fixture.rows[0][0].category_key, "unknown_category");
  fixture.rows[1][0] = fixture.rows[0][0];
  ExpectFailure(MakeAccess(fixture), Failure::core_rejected,
                xar::bridge::ActiveSchemeStateV1PrivateFailure::
                    scheme_category_unavailable);
}

void TestReadFailuresAndEmptyContainer() {
  Fixture fixture{};
  fixture.fail_row_call = 1;
  ExpectFailure(MakeAccess(fixture), Failure::row_unavailable,
                xar::bridge::ActiveSchemeStateV1PrivateFailure::
                    enumeration_incomplete);

  fixture = {};
  fixture.containers[0].row_count = 0;
  fixture.containers[1].row_count = 0;
  Result result{};
  assert(xar::bridge::ObserveActiveSchemeStateV1PrivateSource(
      MakeAccess(fixture), result));
  assert(result.observation.row_count == 0);
  assert(fixture.root_calls == 2);
  assert(fixture.container_calls == 2);
  assert(fixture.row_calls == 0);
}

} // namespace

int main() {
  TestStableTransactionReResolvesAndPublishes();
  TestAdmissionAndThreadGatesPrecedeNativeReads();
  TestRootAndContainerDriftFailClosed();
  TestRowFrameAndCoreDriftFailClosed();
  TestReadFailuresAndEmptyContainer();
  return 0;
}
