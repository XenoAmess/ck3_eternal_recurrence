#include "xar_bridge/zhongguo_promotion_compensation_postcondition_v1.hpp"

#include <cstdint>
#include <iostream>
#include <map>
#include <string>
#include <string_view>
#include <utility>

namespace {

using Raw = xar::ck3_11906::ZhongguoPromotionCompensationRawVariableV1;

struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{
      41, 1066123, true, true, true, true, 200};
  std::map<std::pair<std::int32_t, std::string>, Raw> variables;
  std::size_t reads = 0;
  bool drift_frame = false;
};

Raw Number(std::int64_t value) { return {true, 1, value * 100'000}; }
Raw Character(std::int32_t value) { return {true, 4, value}; }

void Set(Fixture &fixture, std::int32_t character, std::string_view key,
         Raw value) {
  fixture.variables[{character, std::string(key)}] = value;
}

bool Capture(void *context, xar::game::ZhongguoCaseFrameV1 &frame) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  frame = fixture.frame;
  if (fixture.drift_frame && fixture.reads > 0) ++frame.snapshot_revision;
  return true;
}

bool MainThread(void *) noexcept { return true; }

bool ValidateCharacter(void *, std::int32_t character) noexcept {
  return character == 100 || character == 200;
}

bool ReadVariable(void *context, std::int32_t character, std::string_view key,
                  Raw &value) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.reads;
  const auto found = fixture.variables.find({character, std::string(key)});
  value = found == fixture.variables.end() ? Raw{} : found->second;
  return true;
}

xar::ck3_11906::ZhongguoPromotionCompensationNativeEnvironmentV1
Environment() {
  xar::ck3_11906::ZhongguoPromotionCompensationNativeEnvironmentV1 result{};
  result.exact_build_admitted = true;
  result.offline_fixture_function_overrides = true;
  return result;
}

xar::ck3_11906::ZhongguoPromotionCompensationAccessV1 Access(
    Fixture &fixture) {
  xar::ck3_11906::ZhongguoPromotionCompensationAccessV1 result{};
  result.context = &fixture;
  result.capture_frame = &Capture;
  result.is_main_thread = &MainThread;
  result.validate_character = &ValidateCharacter;
  result.read_allowlisted_variable = &ReadVariable;
  return result;
}

xar::ck3_11906::ZhongguoPromotionCompensationRequestV1 Request() {
  return {41, "promotion-compensation-fixture-01"};
}

void Populate(Fixture &fixture, std::int64_t source_case = 903,
              std::int64_t result_case = 903,
              std::int64_t numbered_case = 1203) {
  Set(fixture, 200, "zg361_comp_portfolio_domain", Number(1));
  Set(fixture, 200, "zg361_comp_portfolio_subject", Character(100));
  Set(fixture, 200, "zg361_comp_portfolio_result_owner", Character(200));
  Set(fixture, 200, "zg361_comp_portfolio_result_subject", Character(100));
  Set(fixture, 200, "zg361_comp_portfolio_result_cycle", Number(7));
  Set(fixture, 200, "zg361_comp_portfolio_result_case", Number(result_case));
  Set(fixture, 200, "zg361_comp_portfolio_result_snapshot_applied", Number(1));

  Set(fixture, 100, "zg361_pp_m147_receipt_active", Number(1));
  Set(fixture, 100, "zg361_pp_m147_consumed", Number(1));
  Set(fixture, 100, "zg361_pp_m147_receipt_owner", Character(200));
  Set(fixture, 100, "zg361_pp_m147_receipt_subject", Character(100));
  Set(fixture, 100, "zg361_pp_m147_receipt_cycle", Number(7));
  Set(fixture, 100, "zg361_pp_m147_receipt_case", Number(503));
  Set(fixture, 100, "zg361_pp_m147_receipt_route", Number(1));
  Set(fixture, 100, "zg361_pp_m147_consumer_revision", Number(6));
  Set(fixture, 100, "zg361_pp_m147_receipt_serial", Number(source_case));
  Set(fixture, 100, "zg361_pp_m147_receipt_revision", Number(6));

  Set(fixture, 100, "zg361_comp_promotion_receipt_active", Number(1));
  Set(fixture, 100, "zg361_comp_promotion_receipt_posted", Number(1));
  Set(fixture, 100, "zg361_comp_promotion_receipt_owner", Character(200));
  Set(fixture, 100, "zg361_comp_promotion_receipt_subject", Character(100));
  Set(fixture, 100, "zg361_comp_promotion_receipt_cycle", Number(7));
  Set(fixture, 100, "zg361_comp_promotion_receipt_case", Number(result_case));
  Set(fixture, 100, "zg361_comp_promotion_receipt_choice_serial",
      Number(source_case));
  Set(fixture, 100, "zg361_comp_promotion_receipt_serial",
      Number(source_case));
  Set(fixture, 100, "zg361_comp_promotion_receipt_choice_revision", Number(6));
  Set(fixture, 100, "zg361_comp_promotion_receipt_revision", Number(9));
  Set(fixture, 100, "zg361_comp_promotion_receipt_operation", Number(89));
  Set(fixture, 100, "zg361_comp_promotion_receipt_route", Number(1));

  Set(fixture, 100, "zg361_case_l_owner", Character(200));
  Set(fixture, 100, "zg361_case_l_subject", Character(100));
  Set(fixture, 100, "zg361_case_l_cycle_serial", Number(7));
  Set(fixture, 100, "zg361_case_l_case_serial", Number(numbered_case));
  Set(fixture, 100, "zg361_case_l_revision", Number(9));
  Set(fixture, 100, "zg361_comp_l_last_operation", Number(89));
  Set(fixture, 100, "zg361_comp_l_last_route", Number(1));
  Set(fixture, 100, "zg361_case_l_active", Number(1));

  Set(fixture, 100, "zg361_comp_m089_receipt_active", Number(1));
  Set(fixture, 100, "zg361_comp_m089_consumed", Number(1));
  Set(fixture, 100, "zg361_comp_m089_receipt_owner", Character(200));
  Set(fixture, 100, "zg361_comp_m089_receipt_subject", Character(100));
  Set(fixture, 100, "zg361_comp_m089_receipt_cycle", Number(7));
  Set(fixture, 100, "zg361_comp_m089_receipt_case", Number(numbered_case));
  Set(fixture, 100, "zg361_comp_m089_receipt_route", Number(1));
  Set(fixture, 100, "zg361_comp_m089_visible_revision", Number(9));
}

bool Read(Fixture &fixture,
          xar::game::ZhongguoPromotionCompensationPostconditionV1 &output) {
  return xar::ck3_11906::ReadZhongguoPromotionCompensationPostconditionV1(
             Environment(), Access(fixture), Request(), output) ==
         xar::game::ReadZhongguoPromotionCompensationResultV1::available;
}

bool TestClosedProjection() {
  Fixture fixture;
  Populate(fixture);
  xar::game::ZhongguoPromotionCompensationPostconditionV1 output{};
  if (!Read(fixture, output) ||
      output.status !=
          xar::game::ZhongguoPromotionCompensationStatusV1::available ||
      !output.readiness.source_identity_ready ||
      !output.readiness.result_identity_ready ||
      !output.readiness.frozen_case_identity_ready ||
      !output.readiness.promotion_choice_receipt_ready ||
      !output.readiness.compensation_receipt_posted ||
      !output.readiness.same_case_identity_ready ||
      !output.readiness.revision_binding_ready ||
      !output.readiness.receipt_serials_ready || !output.readiness.ready ||
      fixture.reads != 2 * (7 + 46 + 8)) {
    return false;
  }
  const auto json =
      xar::ck3_11906::SerializeZhongguoPromotionCompensationPostconditionV1(
          output);
  return json.find(
             "game.command.query-zhongguo-promotion-compensation-"
             "postcondition-v1") != std::string::npos &&
         json.find("\"compensation_receipt_posted\":true") !=
             std::string::npos &&
         json.find("product_receipt_serial_not_persisted") ==
             std::string::npos &&
         json.find("\"receipt_serial\":{\"status\":\"available\",\"value\":903") !=
             std::string::npos &&
         json.find("\"ready\":true") != std::string::npos;
}

bool TestCrossCaseDoesNotBecomeReady() {
  Fixture fixture;
  Populate(fixture, 902, 903);
  xar::game::ZhongguoPromotionCompensationPostconditionV1 output{};
  return Read(fixture, output) && output.readiness.source_identity_ready &&
         output.readiness.compensation_receipt_posted &&
         !output.readiness.same_case_identity_ready && !output.readiness.ready;
}

bool TestUncorrelatedReceiptSerialDoesNotBecomeReady() {
  Fixture fixture;
  Populate(fixture);
  Set(fixture, 100, "zg361_comp_promotion_receipt_serial", Number(904));
  xar::game::ZhongguoPromotionCompensationPostconditionV1 output{};
  return Read(fixture, output) && output.readiness.compensation_receipt_posted &&
         !output.readiness.receipt_serials_ready && !output.readiness.ready;
}

bool TestAbsentChoiceFieldIsTypedUnavailable() {
  Fixture fixture;
  Populate(fixture);
  fixture.variables.erase({100, "zg361_pp_m147_receipt_route"});
  xar::game::ZhongguoPromotionCompensationPostconditionV1 output{};
  if (!Read(fixture, output) ||
      output.promotion_choice.option_number.available ||
      output.promotion_choice.option_number.value.has_value() ||
      output.promotion_choice.option_number.unavailable_reason !=
          "variable_absent" ||
      output.readiness.promotion_choice_receipt_ready ||
      output.readiness.ready) {
    return false;
  }
  const auto json =
      xar::ck3_11906::SerializeZhongguoPromotionCompensationPostconditionV1(
          output);
  return json.find(
             "\"option_number\":{\"status\":\"unavailable\",\"value\":null,"
             "\"unavailable_reason\":\"variable_absent\"}") !=
         std::string::npos;
}

bool TestWrongKindReceiptFieldIsTypedUnavailable() {
  Fixture fixture;
  Populate(fixture);
  Set(fixture, 100, "zg361_comp_promotion_receipt_serial", Character(904));
  xar::game::ZhongguoPromotionCompensationPostconditionV1 output{};
  return Read(fixture, output) &&
         !output.compensation_receipt.receipt_serial.available &&
         !output.compensation_receipt.receipt_serial.value.has_value() &&
         output.compensation_receipt.receipt_serial.unavailable_reason ==
             "variable_kind_mismatch" &&
         !output.readiness.receipt_serials_ready && !output.readiness.ready;
}

bool TestUnknownOperationFailsClosed() {
  Fixture fixture;
  Populate(fixture);
  Set(fixture, 100, "zg361_comp_l_last_operation", Number(777));
  xar::game::ZhongguoPromotionCompensationPostconditionV1 output{};
  return !Read(fixture, output) &&
         output.unavailable_reason == "compensation_operation_unavailable";
}

bool TestFrameDriftFailsClosed() {
  Fixture fixture;
  Populate(fixture);
  fixture.drift_frame = true;
  xar::game::ZhongguoPromotionCompensationPostconditionV1 output{};
  return !Read(fixture, output) && output.unavailable_reason == "state_changed";
}

} // namespace

int main() {
  if (!TestClosedProjection() ||
      !TestCrossCaseDoesNotBecomeReady() ||
      !TestUncorrelatedReceiptSerialDoesNotBecomeReady() ||
      !TestAbsentChoiceFieldIsTypedUnavailable() ||
      !TestWrongKindReceiptFieldIsTypedUnavailable() ||
      !TestUnknownOperationFailsClosed() || !TestFrameDriftFailsClosed()) {
    std::cerr << "zhongguo promotion/compensation provider fixture failed\n";
    return 1;
  }
  return 0;
}
