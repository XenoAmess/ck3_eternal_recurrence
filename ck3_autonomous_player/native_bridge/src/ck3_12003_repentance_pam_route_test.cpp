#include "xar_bridge/ck3_12003_repentance_pam_route.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace pam = xar::ck3_12003::religion::repentance_pam_route;
namespace religion = xar::ck3_12002::religion;
namespace doctrine = religion::doctrine12002;
namespace candidates = xar::ck3_12003::religion::repentance_candidates;
namespace {
int checks = 0, scenarios = 0;
void Check(bool value, const char *description) {
  ++checks;
  if (!value) throw std::runtime_error(description);
}
bool Value(const pam::BoolObservation &value) {
  Check(value.available && value.value.has_value(), "observation available");
  return *value.value;
}
struct Fixture {
  static constexpr std::int32_t actor = 201, date = 176440;
  static constexpr std::uint64_t epoch = 92;
  std::array<unsigned char, 0x2B8> feature{};
  std::array<std::uint32_t, 44> enums{};
  std::uintptr_t root = reinterpret_cast<std::uintptr_t>(feature.data());
  pam::Bindings bindings{};
  religion::Context rel{};
  doctrine::TenetParameterContext parameters{};
  doctrine::FaithMainRiteDoctrines doctrines{};
  candidates::Context recipients{};
  pam::RawRouteInputs raw{};
  Fixture() {
    bindings = {true, &root, enums.data()};
    enums[43] = 0x4169;
    Pam(true);
    rel.available = true; rel.played_character_id = actor; rel.date_raw = date; rel.capture_epoch = epoch;
    rel.rite_id = 23; rel.faith_id = 152; rel.faith_main_rite_id = 77;
    rel.religion_key = "christianity_religion";
    parameters.available = true; parameters.played_character_id = actor;
    parameters.date_raw = date; parameters.capture_epoch = epoch; parameters.faith_id = 152;
    parameters.current_rite = doctrine::RiteBooleanParameters{23, {{"wrong_actor_only_parameter", true}}};
    parameters.faith_main_rite = doctrine::RiteBooleanParameters{77, {{"spiritual_head_of_faith", true}}};
    doctrines.available = true; doctrines.played_character_id = actor;
    doctrines.date_raw = date; doctrines.capture_epoch = epoch; doctrines.faith_id = 152; doctrines.main_rite_id = 77;
    doctrines.rows.push_back({"doctrine_sacraments_central", "sacraments", "faith_main_rite"});
    recipients.available = true; recipients.played_character_id = actor;
    recipients.date_raw = date; recipients.capture_epoch = epoch;
    recipients.roles[1].available = true; recipients.roles[1].character_id = -1;
    recipients.roles[3].available = true; recipients.roles[3].character_id = 301;
    candidates::Candidate head, bishop;
    head.requested_recipient_character_id = 301;
    bishop.requested_recipient_character_id = 302;
    recipients.candidates = {head, bishop};
    raw.available = true; raw.played_character_id = actor; raw.date_raw = date; raw.capture_epoch = epoch;
    raw.pope_excom = false; raw.highest_held_title_tier = 3; raw.any_held_title_has_clerical_region = false;
  }
  void Pam(bool enabled) {
    const std::uint64_t bits = enabled ? std::uint64_t{1} << 43 : 0;
    std::memcpy(feature.data() + 0x2B0, &bits, sizeof(bits));
  }
  pam::Context Read() {
    pam::Context out;
    pam::ReadRepentancePamRoute12003(bindings, this, actor, date, epoch,
        rel, parameters, doctrines, recipients, raw, out);
    return out;
  }
};
void Save(const std::filesystem::path &folder, const char *name, const pam::Context &out) {
  ++scenarios;
  std::ofstream(folder / (std::string(name) + ".json")) << pam::SerializeRepentancePamRoute12003(out);
}
void Routes(const pam::Context &out, bool head, bool bishop) {
  Check(out.available, "complete fresh input result");
  Check(out.candidates.size() == 2, "both current candidates preserved");
  Check(Value(out.candidates[0].pam_ordinary_route_clause_passes) == head, "head route clause");
  Check(Value(out.candidates[1].pam_ordinary_route_clause_passes) == bishop, "bishop route clause");
}
} // namespace
int main(int argc, char **argv) {
  try {
    if (argc != 2) return 2;
    const std::filesystem::path folder(argv[1]);
    Fixture f;
    auto out = f.Read();
    Routes(out, false, true);
    Check(!Value(out.petition_head_of_faith_repentance_requires_petition), "duke ordinary rank");
    Check(!Value(out.capital_clerical_holder_is_actor), "absent scalar ?= actor false");
    Check(Value(out.faith_has_central_sacraments), "effective main Rite doctrine");
    Check(out.faith_main_rite_id == 77U && out.current_rite_id == 23U, "main Rite identity preserved separately");
    Save(folder, "duke_optional_absent", out);

    f.raw.pope_excom = true;
    out = f.Read(); Routes(out, false, false);
    Check(Value(out.petition_head_of_faith_repentance_requires_petition), "pope flag bypasses rank");
    Save(folder, "pope_flag_low_rank", out);

    f.raw.pope_excom = false; f.recipients.roles[1].character_id = 301;
    out = f.Read(); Routes(out, false, false);
    Check(Value(out.capital_clerical_holder_is_religious_authority), "capital authority exact full ID");
    Check(Value(out.petition_head_of_faith_repentance_requires_petition), "capital authority bypasses rank");
    Save(folder, "capital_authority", out);

    f.recipients.roles[1].character_id = Fixture::actor;
    out = f.Read(); Routes(out, false, false);
    Check(Value(out.capital_clerical_holder_is_actor), "capital actor exact full ID");
    Save(folder, "capital_actor", out);

    f.recipients.roles[1].character_id = -1; f.raw.highest_held_title_tier = 4;
    out = f.Read(); Routes(out, false, false);
    Check(Value(out.need_hof_for_clergy_interaction), "PAM kingdom threshold");
    Check(Value(out.petition_head_of_faith_repentance_requires_petition), "kingdom petition branch");
    Save(folder, "pam_kingdom", out);

    f.Pam(false);
    out = f.Read(); Routes(out, true, true);
    Check(!Value(out.need_hof_for_clergy_interaction), "non-PAM kingdom below empire");
    f.raw.highest_held_title_tier = 5;
    out = f.Read(); Routes(out, true, true);
    Check(Value(out.need_hof_for_clergy_interaction), "non-PAM empire threshold");
    Save(folder, "non_pam_empire", out);

    f.Pam(true); f.raw.highest_held_title_tier = 3;
    f.parameters.faith_main_rite->parameters.clear();
    f.parameters.current_rite->parameters = {{"spiritual_head_of_faith", true}};
    out = f.Read(); Routes(out, true, true);
    Check(!Value(out.faith_main_rite_spiritual_head_of_faith), "actor own Rite never substituted");
    Check(!Value(out.petition_head_of_faith_repentance_requires_petition), "complete absent parameter false");
    Save(folder, "actual_main_rite_parameter_absent", out);

    f.parameters.faith_main_rite->parameters = {{"spiritual_head_of_faith", true}};
    f.rel.religion_key = "islam_religion";
    out = f.Read(); Routes(out, true, true);
    Check(!Value(out.faith_qualifies_for_pam_clergy_route), "actual non-Christian religion");
    Save(folder, "non_christian_main_rite", out);

    f.rel.religion_key = "christianity_religion"; f.raw.any_held_title_has_clerical_region = true;
    out = f.Read(); Routes(out, true, true);
    Check(Value(out.is_archbishop_or_higher), "clerical region title rank branch");
    Save(folder, "held_clerical_region", out);

    f.raw.any_held_title_has_clerical_region = false;
    f.recipients.roles[3].character_id = Fixture::actor;
    out = f.Read(); Routes(out, true, true);
    Check(Value(out.is_archbishop_or_higher), "actor authority branch");
    Save(folder, "actor_is_authority", out);

    f.recipients.roles[3].character_id = -1;
    out = f.Read(); Routes(out, true, true);
    Check(!Value(out.capital_clerical_holder_is_religious_authority), "absent ?= absent false");
    Check(!Value(out.religious_authority_exists), "known absent authority false");
    Check(!Value(out.petition_head_of_faith_repentance_requires_petition), "no authority no petition");
    Save(folder, "both_character_scopes_absent", out);

    f.raw.capture_epoch = Fixture::epoch - 1;
    out = f.Read();
    Check(!out.available, "failed fresh raw frame remains unavailable");
    Check(!out.petition_head_of_faith_repentance_requires_petition.value, "missing raw is null not false");
    Check(Value(out.faith_has_central_sacraments), "independent doctrine observation preserved");
    Save(folder, "raw_provider_frame_mismatch", out);
    std::cout << "GREEN scenarios=" << scenarios << " checks=" << checks << '\n';
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
