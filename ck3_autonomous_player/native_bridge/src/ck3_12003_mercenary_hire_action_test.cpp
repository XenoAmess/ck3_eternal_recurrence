#include "xar_bridge/ck3_12003_mercenary_hire_action.hpp"
#include "xar_bridge/ck3_12003_mercenary_hire_wire.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace mercenary = xar::ck3_12003::mercenary;
namespace {
template <typename T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}
int checks = 0;
void Require(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}
struct Fixture;
Fixture *fixture = nullptr;
using NativeCommand = std::array<std::byte, 0x30>;
void *CommandDelete(void *, std::uint32_t);
void **CommandClone(const void *, void **);
bool CommandQueue(void *, void **, std::uint32_t);
void *CommandFactory();
bool CommandValidator(const void *, void *);
bool CanHire(void *, void *, std::uint32_t, void *);
std::int64_t *Cost(void *, std::int64_t *, void *, std::int32_t);
std::int32_t PaymentStatus(void *, void *, std::uint32_t);
bool CanAfford(const std::int64_t *, void *, void *);
std::int64_t Duration(void *, void *);
void ReasonDestroy(void *);

struct Fixture {
  alignas(8) std::array<std::byte, 0x200> actor{};
  alignas(8) std::array<std::byte, 0x200> realm{};
  alignas(8) std::array<std::byte, 0x60> company{};
  alignas(8) std::array<std::byte, 0x60> fallback{};
  alignas(8) std::array<std::byte, 0x30> manager{};
  alignas(8) std::array<std::byte, 0x10> entries{};
  std::array<void *, 9> primary_vtable{};
  std::array<void *, 1> secondary_vtable{};
  void *manager_pointer = nullptr;
  void *fallback_pointer = nullptr;
  void *factory_source = nullptr;
  mercenary::HireActionBindings bindings{};
  std::int32_t actor_id = 29829;
  std::uint32_t company_id = 0;
  std::int32_t payment_status = 1;
  bool can_hire_result = true;
  bool validate_result = true;
  int factories = 0, validations = 0, clones = 0, queues = 0;
  int source_deletes = 0, clone_deletes = 0;
  int final_hire_calls = 0, payment_calls = 0, afford_calls = 0;
  int cost_calls = 0, duration_calls = 0, reason_deletes = 0;
  Fixture() {
    fixture = this;
    Put(actor.data(), 0x18, actor_id);
    Put(actor.data(), 0x1C0, static_cast<const void *>(realm.data()));
    Put(realm.data(), 0x1D0, std::int32_t{7});
    Put(company.data(), 0x10, company_id);
    Put(company.data(), 0x14, std::uint32_t{0x4D657263});
    Put(company.data(), 0x48, UINT32_MAX);
    manager_pointer = manager.data();
    fallback_pointer = fallback.data();
    Put(manager.data(), 0x20, static_cast<const void *>(entries.data()));
    Put(manager.data(), 0x2C, std::int32_t{1});
    Put(entries.data(), 8, static_cast<void *>(company.data()));
    primary_vtable[0] = reinterpret_cast<void *>(&CommandDelete);
    primary_vtable[8] = reinterpret_cast<void *>(&CommandClone);
    bindings.enabled = true;
    bindings.candidates = {true, &manager_pointer, &fallback_pointer, nullptr};
    bindings.final_terms = {true, &CanHire, &Cost, &PaymentStatus,
                            &CanAfford, &Duration, &ReasonDestroy};
    bindings.commands.enabled = true;
    bindings.commands.command_manager = this;
    bindings.commands.queue_owned_command = &CommandQueue;
    bindings.create_default = &CommandFactory;
    bindings.validate_source = &CommandValidator;
  }
};

void WriteReason(void *sink, std::string_view text) {
  if (sink == nullptr) return;
  if (text.size() <= 15) {
    std::memcpy(sink, text.data(), text.size());
    Put<char>(sink, text.size(), '\0');
  } else {
    auto *heap = new char[text.size() + 1];
    std::memcpy(heap, text.data(), text.size());
    heap[text.size()] = '\0';
    Put(sink, 0, heap);
    Put(sink, 0x18, text.size());
  }
  Put(sink, 0x10, text.size());
}
void ReasonDestroy(void *sink) {
  ++fixture->reason_deletes;
  if (Get<std::size_t>(sink, 0x18) >= 16)
    delete[] Get<char *>(sink, 0);
}
void CheckActorAndCompany(void *company, void *actor) {
  Require(company == fixture->company.data() && actor == fixture->actor.data(),
          "provider evaluates live resolved company and actual played actor pointers");
}
bool CanHire(void *company, void *actor, std::uint32_t mode, void *reason) {
  ++fixture->final_hire_calls;
  CheckActorAndCompany(company, actor);
  Require(mode == 1, "final Hire uses normal mode one");
  WriteReason(reason, fixture->can_hire_result ? std::string_view{} :
      std::string_view{"native Hire gate failed"});
  return fixture->can_hire_result;
}
std::int64_t *Cost(void *company, std::int64_t *out, void *actor,
                   std::int32_t landstate_value) {
  ++fixture->cost_calls;
  CheckActorAndCompany(company, actor);
  Require(landstate_value == 7, "quote uses current actor landstate value");
  const std::array<std::int64_t, 10> values{
      81100000, -50000, 300000, 11, 12, 13, 14, 15, 16, 17};
  std::memcpy(out, values.data(), sizeof(values));
  return out;
}
std::int32_t PaymentStatus(void *company, void *actor, std::uint32_t mode) {
  ++fixture->payment_calls;
  CheckActorAndCompany(company, actor);
  Require(mode == 1, "native payment status uses normal mode one");
  return fixture->payment_status;
}
bool CanAfford(const std::int64_t *, void *actor, void *reason) {
  ++fixture->afford_calls;
  Require(actor == fixture->actor.data(), "generic affordability retains actor");
  WriteReason(reason, "Not enough gold");
  return false;
}
std::int64_t Duration(void *company, void *actor) {
  ++fixture->duration_calls;
  CheckActorAndCompany(company, actor);
  return 36;
}
void CheckNativeFields(const void *command) {
  Require(Get<std::int32_t>(command, 0x20) == fixture->actor_id &&
      Get<std::uint32_t>(command, 0x24) == fixture->company_id,
      "provider writes actual actor and complete legal-zero company parameters");
  Require(Get<std::uint32_t>(command, 0x28) == 1 &&
      Get<std::uint8_t>(command, 8) == 0x20 &&
      Get<std::uint64_t>(command, 0x10) == 0x1020304050607080ULL &&
      Get<void *>(command, 0) == fixture->primary_vtable.data() &&
      Get<void *>(command, 0x18) == fixture->secondary_vtable.data(),
      "provider preserves native factory mode metadata and both vtables");
}
void *CommandFactory() {
  ++fixture->factories;
  auto *command = new NativeCommand{};
  fixture->factory_source = command;
  Put(command->data(), 0, fixture->primary_vtable.data());
  Put(command->data(), 8, std::uint8_t{0x20});
  Put(command->data(), 0x10, std::uint64_t{0x1020304050607080ULL});
  Put(command->data(), 0x18, fixture->secondary_vtable.data());
  Put(command->data(), 0x20, std::int32_t{-1});
  Put(command->data(), 0x24, UINT32_MAX);
  Put(command->data(), 0x28, std::uint32_t{1});
  return command;
}
bool CommandValidator(const void *command, void *reason) {
  ++fixture->validations;
  Require(reason == nullptr, "native command validator uses native no-text convention");
  CheckNativeFields(command);
  WriteReason(reason, fixture->validate_result ? std::string_view{} :
      std::string_view{"native command rejected"});
  return fixture->validate_result;
}
void **CommandClone(const void *command, void **returned_storage) {
  ++fixture->clones;
  CheckNativeFields(command);
  auto *copy = new NativeCommand{};
  std::memcpy(copy->data(), command, copy->size());
  *returned_storage = copy;
  return returned_storage;
}
void *CommandDelete(void *command, std::uint32_t flags) {
  Require(flags == 1, "native owning command deleting destructor receives flag one");
  if (command == fixture->factory_source) ++fixture->source_deletes;
  else ++fixture->clone_deletes;
  delete static_cast<NativeCommand *>(command);
  return nullptr;
}
bool CommandQueue(void *manager, void **owned, std::uint32_t flags) {
  ++fixture->queues;
  Require(manager == fixture && flags == 0x0E && owned != nullptr &&
      *owned != nullptr && *owned != fixture->factory_source,
      "actual SubmitCommandCopy transfers owned clone with native channel flags");
  CheckNativeFields(*owned);
  CommandDelete(*owned, 1);
  *owned = nullptr;
  return true;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "fixture requires genuine wire output path");
    constexpr std::uint64_t native_revision = 141;
    constexpr std::int32_t synthetic_date = 53240904;
    xar::ck3_12003::MercenaryHireRequestV1 request{};
    Require(xar::ck3_12003::ParseMercenaryHireRequestV1(
        xar::ck3_12003::kMercenaryHireStepV1,
        "{\"company_id\":0,\"expected_revision\":141}", request) &&
        request.company_id == 0 && request.expected_revision == native_revision,
        "real typed parser preserves legal zero company and current revision");
    std::string submitted_wire;
    std::array<std::string, 3> rejected_wire;
    {
      Fixture current;
      mercenary::HireActionResult result{};
      Require(mercenary::ApplyMercenaryHire12003(current.bindings,
          current.actor.data(), current.actor_id, request.company_id, result) ==
          mercenary::HireActionStatus::submitted,
          "real provider accepts permitted debt through normal native command path");
      Require(result.company_resolved && result.actor_character_id == 29829 &&
          result.company_id == 0 && !result.prior_employer_character_id &&
          result.final_terms.can_hire == true &&
          result.final_terms.payment_status == 1 &&
          result.final_terms.can_afford == false,
          "provider reports current company and final native terms independent of generic affordability");
      Require(result.native_command_validation_observable &&
          result.native_command_valid && result.command_submitted &&
          result.verification_pending,
          "provider reports native validation and submission pending independent observation");
      Require(current.factories == 1 && current.validations == 1 &&
          current.clones == 1 && current.queues == 1 &&
          current.source_deletes == 1 && current.clone_deletes == 1,
          "actual native-copy submission owns one factory source and one queue clone with balanced cleanup");
      Require(current.final_hire_calls == 1 && current.payment_calls == 1 &&
          current.cost_calls == 1 && current.afford_calls == 1 &&
          current.duration_calls == 1 && current.reason_deletes == 2,
          "provider freshly evaluates native terms once for selected current company");
      submitted_wire = xar::ck3_12003::SerializeMercenaryHireResultV1(
          result, "synthetic-mercenary-hire-permitted-debt", 1,
          native_revision, synthetic_date);
      Require(submitted_wire.find("\"type\":\"command_result\"") != std::string::npos &&
          submitted_wire.find("\"status\":\"submitted_verification_pending\"") != std::string::npos &&
          submitted_wire.find("\"status\":\"submitted\"") != std::string::npos &&
          submitted_wire.find("\"verification_pending\":true") != std::string::npos &&
          submitted_wire.find("\"after_state_observed\":false") != std::string::npos &&
          submitted_wire.find("\"company_id\":0") != std::string::npos &&
          submitted_wire.find("\"can_afford\":false") != std::string::npos &&
          submitted_wire.find("\"payment_status\":1") != std::string::npos,
          "real full serializer preserves submission status and pending material outcome");
    }
    {
      Fixture current;
      current.payment_status = 0;
      mercenary::HireActionResult result{};
      Require(mercenary::ApplyMercenaryHire12003(current.bindings,
          current.actor.data(), current.actor_id, request.company_id, result) ==
          mercenary::HireActionStatus::rejected &&
          result.unavailable_reason == "native_mercenary_payment_outside_allowance",
          "native payment status zero prevents action submission");
      Require(current.factories == 0 && current.validations == 0 &&
          current.clones == 0 && current.queues == 0 &&
          !result.command_submitted && !result.verification_pending &&
          !result.native_command_validation_observable,
          "outside payment allowance constructs no command and claims no queued action");
      rejected_wire[0] = xar::ck3_12003::SerializeMercenaryHireResultV1(
          result, "synthetic-mercenary-hire-payment-zero", 2,
          native_revision, synthetic_date);
      Require(rejected_wire[0].find("\"accepted\":false") != std::string::npos &&
          rejected_wire[0].find("\"native_command_valid\":null") != std::string::npos &&
          rejected_wire[0].find("\"command_submitted\":false") != std::string::npos,
          "real rejected payment wire distinguishes unobserved command validation");
    }
    {
      Fixture current;
      current.can_hire_result = false;
      mercenary::HireActionResult result{};
      Require(mercenary::ApplyMercenaryHire12003(current.bindings,
          current.actor.data(), current.actor_id, request.company_id, result) ==
          mercenary::HireActionStatus::rejected &&
          result.unavailable_reason == "native_mercenary_can_hire_false",
          "fresh native CanHire false prevents action submission");
      Require(current.factories == 0 && current.validations == 0 &&
          current.clones == 0 && current.queues == 0 &&
          !result.command_submitted && !result.verification_pending,
          "failed final Hire predicate creates no command or queued action");
      rejected_wire[1] = xar::ck3_12003::SerializeMercenaryHireResultV1(
          result, "synthetic-mercenary-hire-can-hire-false", 3,
          native_revision, synthetic_date);
    }
    {
      Fixture current;
      current.validate_result = false;
      mercenary::HireActionResult result{};
      Require(mercenary::ApplyMercenaryHire12003(current.bindings,
          current.actor.data(), current.actor_id, request.company_id, result) ==
          mercenary::HireActionStatus::rejected &&
          result.unavailable_reason == "native_mercenary_command_validator_false",
          "native command validator false prevents clone and queue submission");
      Require(current.factories == 1 && current.validations == 1 &&
          current.clones == 0 && current.queues == 0 &&
          current.source_deletes == 1 && current.clone_deletes == 0 &&
          result.native_command_validation_observable &&
          !result.native_command_valid && !result.command_submitted &&
          !result.verification_pending,
          "rejected native source is destroyed without a queued clone");
      rejected_wire[2] = xar::ck3_12003::SerializeMercenaryHireResultV1(
          result, "synthetic-mercenary-hire-native-validation-false", 4,
          native_revision, synthetic_date);
    }
    std::ofstream output(argv[1], std::ios::binary);
    output << submitted_wire << '\n';
    Require(output.good(), "native executable writes genuine submitted full wire");
    const std::array<std::string_view, 3> labels{
        "payment-zero", "can-hire-false", "native-validation-false"};
    for (std::size_t index = 0; index < rejected_wire.size(); ++index) {
      std::ofstream negative(std::string(argv[1]) + "." +
          std::string(labels[index]) + ".json", std::ios::binary);
      negative << rejected_wire[index] << '\n';
      Require(negative.good(), "native executable writes genuine rejected full wire");
    }
    std::cout << "{\"status\":\"GREEN\",\"scenarios\":4,\"checks\":" << checks
              << ",\"synthetic_fixture\":true,\"old_market_case_reruns\":0}\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
