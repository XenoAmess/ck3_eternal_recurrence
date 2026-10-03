#include "xar_bridge/ck3_12003_player_mercenary_context.hpp"

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
int soldiers_calls = 0, hire_calls = 0, cost_calls = 0;
int payment_calls = 0, afford_calls = 0, duration_calls = 0;
int selector_calls = 0, title_calls = 0, destroyed = 0;
void *played = nullptr, *first_company = nullptr, *second_company = nullptr;
const void *home_title = nullptr, *home_province = nullptr;
const void *hire_province = nullptr;

void Require(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}
void WriteReason(void *sink, std::string_view text) {
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
  ++destroyed;
  if (Get<std::size_t>(sink, 0x18) >= 16)
    delete[] Get<char *>(sink, 0);
}
std::int32_t CurrentSoldiers(void *company) {
  ++soldiers_calls;
  return company == first_company ? 0 : 1500;
}
bool CanHire(void *company, void *actor, std::uint32_t mode, void *reason) {
  ++hire_calls;
  Require(actor == played && mode == 1, "aggregate passes played actor and normal Hire mode");
  WriteReason(reason, company == first_company ? std::string_view{} :
      std::string_view{"\x15Z Requires \"war\"\n\x15!"});
  return company == first_company;
}
std::int64_t *Cost(void *company, std::int64_t *out, void *actor,
                   std::int32_t landstate_value) {
  ++cost_calls;
  Require(actor == played && landstate_value == 7,
          "aggregate passes current played landstate quote input");
  const std::array<std::int64_t, 10> values = company == first_company ?
      std::array<std::int64_t, 10>{14250000, -50000, 300000, 11, 12,
          13, 14, 15, 16, 17} :
      std::array<std::int64_t, 10>{30000000, 0, 0, 0, 0, 0, 0, 0, 0, 0};
  std::memcpy(out, values.data(), sizeof(values));
  return out;
}
std::int32_t PaymentStatus(void *company, void *actor, std::uint32_t mode) {
  ++payment_calls;
  Require(actor == played && mode == 1,
          "payment allowance keeps actor and Hire mode");
  return company == first_company ? 1 : 0;
}
bool CanAfford(const std::int64_t *, void *actor, void *reason) {
  ++afford_calls;
  Require(actor == played, "generic affordability receives played actor");
  WriteReason(reason, "Not enough gold");
  return false;
}
std::int64_t Duration(void *company, void *actor) {
  ++duration_calls;
  Require(actor == played, "duration receives played actor");
  return company == first_company ? 36 : 24;
}
bool ReadMemory(void *, const void *source, void *output, std::size_t bytes) {
  if (source == nullptr) return false;
  std::memcpy(output, source, bytes);
  return true;
}
const void *ResolveTitle(void *, std::int32_t id) {
  return id == 2142 ? home_title : nullptr;
}
const void *ResolveProvince(void *, std::int32_t id) {
  if (id == 2640) return home_province;
  return id == 2604 ? hire_province : nullptr;
}
const void *TitleProvince(const void *title) {
  ++title_calls;
  Require(title == home_title, "actual native title helper receives resolved company title");
  return home_province;
}
std::int32_t SelectHireProvince(const void *actor) {
  ++selector_calls;
  Require(actor == played, "actual selector receives current played actor");
  return 2604;
}
void InitCompany(void *company, std::uint32_t id, std::uint32_t employer) {
  Put(company, 0x10, id);
  Put(company, 0x14, std::uint32_t{0x4D657263});
  Put(company, 0x24, std::int32_t{2142});
  Put(company, 0x48, employer);
}
void InitProvince(void *province, std::int32_t id) {
  Put(province, 0x10, id);
  Put(province, 0x85C, std::uint32_t{0x50726F76});
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "fixture requires output wire path");
    constexpr std::int32_t actor_id = 29829, date_raw = 53240904;
    constexpr std::uint64_t capture_epoch = 1, native_revision = 141;
    alignas(8) std::array<std::byte, 0x200> actor{};
    alignas(8) std::array<std::byte, 0x400> realm{};
    alignas(8) std::array<std::byte, 0x30> manager{};
    alignas(8) std::array<std::byte, 0x40> entries{};
    alignas(8) std::array<std::byte, 0x60> first{}, second{}, fallback{};
    alignas(8) std::array<std::byte, 0x20> title{};
    alignas(8) std::array<std::byte, 0x900> home{}, selected{};
    played = actor.data();
    first_company = first.data();
    second_company = second.data();
    home_title = title.data();
    home_province = home.data();
    hire_province = selected.data();
    Put(actor.data(), 0x18, actor_id);
    Put(actor.data(), 0x1C0, static_cast<const void *>(realm.data()));
    Put(realm.data(), 0x1D0, std::int32_t{7});
    Put(realm.data(), 0x324, std::int32_t{3});
    InitCompany(first_company, 0U, UINT32_MAX);
    InitCompany(second_company, 0x01000003U, 0U);
    Put(title.data(), 0x10, std::int32_t{2142});
    InitProvince(home.data(), 2640);
    InitProvince(selected.data(), 2604);
    void *manager_pointer = manager.data();
    void *fallback_pointer = fallback.data();
    Put(manager.data(), 0x20, static_cast<const void *>(entries.data()));
    Put(manager.data(), 0x2C, std::int32_t{4});
    Put(entries.data(), 0x08, first_company);
    Put(entries.data(), 0x28, fallback_pointer);
    Put(entries.data(), 0x38, second_company);
    mercenary::ContextBindings bindings{};
    bindings.candidates = {true, &manager_pointer, &fallback_pointer,
                           &CurrentSoldiers};
    bindings.final_terms = {true, &CanHire, &Cost, &PaymentStatus, &CanAfford,
                            &Duration, &ReasonDestroy};
    bindings.position = {&TitleProvince, &SelectHireProvince};
    bindings.world = {nullptr, &ReadMemory, &ResolveTitle, &ResolveProvince};
    mercenary::Context context{};
    Require(mercenary::ReadPlayerMercenaryContext12003(bindings, played,
        actor_id, date_raw, capture_epoch, context),
        "real aggregate reader succeeds");
    Require(context.available && context.unavailable_reason.empty(),
            "enumeration remains available");
    Require(context.actor_character_id == actor_id &&
        context.date_raw == date_raw && context.capture_epoch == capture_epoch,
        "synthetic paused frame metadata survives aggregate reader");
    Require(context.rows.size() == 2, "aggregate copies two companies across null and fallback slots");
    const auto &first_row = context.rows[0];
    const auto &second_row = context.rows[1];
    Require(first_row.candidate.company_id == 0U &&
        first_row.candidate.manager_slot_index == 0U &&
        !first_row.candidate.employer_id &&
        second_row.candidate.company_id == 0x01000003U &&
        second_row.candidate.manager_slot_index == 3U &&
        second_row.candidate.employer_id == 0U,
        "legal zero and generation-bearing identities remain distinct from absent employer");
    Require(first_row.candidate.troop_strength_available &&
        first_row.candidate.current_soldiers == 0 &&
        second_row.candidate.current_soldiers == 1500,
        "aggregate copies current soldiers");
    const auto &terms = first_row.final_terms;
    Require(terms.available && terms.can_hire == true &&
        terms.payment_status == 1 && terms.can_afford == false,
        "native debt allowance and final Hire remain independent of generic affordability");
    Require(terms.hire_duration_months == 36 &&
        terms.resource_costs_raw.has_value() &&
        *terms.resource_costs_raw == std::array<std::int64_t, 10>{
            14250000, -50000, 300000, 11, 12, 13, 14, 15, 16, 17},
        "complete signed quote and duration cross aggregate boundary");
    Require(terms.can_hire_reasons_available &&
        terms.can_hire_reason_literal == "" &&
        terms.can_afford_reasons_available &&
        terms.can_afford_reason_literal == "Not enough gold",
        "two native reasons retain legal empty and nonempty text");
    Require(second_row.final_terms.available &&
        second_row.final_terms.can_hire == false &&
        second_row.final_terms.payment_status == 0 &&
        second_row.final_terms.can_hire_reason_literal ==
            "\x15Z Requires \"war\"\n\x15!",
        "negative final Hire retains native control-character reason");
    for (const auto &row : context.rows) {
      Require(row.location.company_home_ready &&
          row.location.company_home_title_id == 2142 &&
          row.location.company_home_province_id == 2640 &&
          row.location.hire_auto_raise_position_ready &&
          row.location.hire_auto_raise_province_id == 2604 &&
          row.location.actor_active_war_count == 3 &&
          row.location.hire_auto_raise_attempted_in_active_war == true,
          "home and actual actor selector retain two independent ready positions");
    }
    Require(soldiers_calls == 2 && hire_calls == 2 && cost_calls == 2 &&
        payment_calls == 2 && afford_calls == 2 && duration_calls == 2 &&
        selector_calls == 2 && title_calls == 2 && destroyed == 4,
        "aggregate invokes each native component once per company and cleans reason sinks");
    const auto wire = mercenary::SerializePlayerMercenaryContextResultV1(
        context, "synthetic-mercenary-aggregate-fixture", 1, native_revision);
    Require(wire.find("\"type\":\"command_result\"") != std::string::npos &&
        wire.find("\"step\":\"query-player-mercenary-context-v1\"") != std::string::npos &&
        wire.find("\"player_mercenary_context\":{") != std::string::npos &&
        wire.find("\"snapshot_revision\":141") != std::string::npos &&
        wire.find("\"native_hire_mode\":1") != std::string::npos,
        "real serializer writes complete command_result envelope");
    Require(wire.find("\\u0015Z Requires \\\"war\\\"\\u000a\\u0015!") != std::string::npos &&
        wire.find("\"company_id\":0") != std::string::npos &&
        wire.find("\"employer_id\":null") != std::string::npos &&
        wire.find("\"employer_id\":0") != std::string::npos &&
        wire.find("\"can_hire\":true") != std::string::npos &&
        wire.find("\"can_afford\":false") != std::string::npos,
        "real serializer escapes reason text and preserves zero/null and independent legality");
    std::ofstream output(argv[1], std::ios::binary);
    output << wire << '\n';
    Require(output.good(), "native executable writes genuine full wire artifact");
    std::cout << "{\"status\":\"GREEN\",\"scenarios\":1,\"checks\":"
              << checks << ",\"synthetic_fixture\":true,\"component_case_reruns\":0}\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
