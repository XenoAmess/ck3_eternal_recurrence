#include "xar_bridge/religion_rite_governance12002_context.hpp"

#include <array>
#include <bit>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace c = xar::ck3_12002;
namespace r = c::religion;
namespace s = r::state_rite;
namespace h = r::head;
namespace o = r::organization;
namespace g = r::governance;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T> void Put(Buffer &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}

// The component fixtures' actual native-memory layouts are combined here. No
// provider result or command_result envelope is supplied by the fixture.
struct GovernanceFixture {
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{};
  Bytes<0x100> slots{};
  Bytes<0x1D8> actor{}, top_liege{}, actor_head{}, main_head{}, faith_holder{};
  Bytes<0x200> actor_landed{}, top_landed{};
  Bytes<0x310> own_title{}, realm_title{};
  Bytes<0x140> religious_title{};
  Bytes<0x500> actor_rite{}, main_rite{}, own_rite{}, realm_rite{};
  Bytes<0x320> actor_faith{};
  Bytes<0xA0> own_faith{}, realm_faith{};
  std::array<std::uint32_t, 1> actor_titles{0x8E000001U};
  std::array<std::uint32_t, 1> top_titles{0x8F000002U};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::int32_t date = 53175816;
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t top_id = 0x84000006U;
  static constexpr std::uint32_t actor_head_id = 0x85000005U;
  static constexpr std::uint32_t main_head_id = 0x86000007U;
  static constexpr std::uint32_t faith_holder_id = 0x87000008U;
  static constexpr std::uint32_t actor_faith_id = 0x88000009U;
  static constexpr std::uint32_t own_faith_id = 0x8900000AU;
  static constexpr std::uint32_t realm_faith_id = 0x8A00000BU;
  static constexpr std::uint32_t main_rite_id = 0x8B00000CU;
  static constexpr std::uint32_t own_rite_id = 0x8C00000DU;
  static constexpr std::uint32_t realm_rite_id = 0x8D00000EU;
  static constexpr std::uint32_t religious_title_id = 0x90000003U;
  bool bad_head_return = false;
  bool change_frame_on_count = false;
  unsigned follower_reads = 0;

  GovernanceFixture() {
    Put(state, 8, date); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{16});
    const auto character = [&](auto &object, std::uint32_t id) {
      Put(object, 0x18, id); Put(slots, (id & 0x00FFFFFFU) * 0x10ULL + 8, object.data());
    };
    character(actor, static_cast<std::uint32_t>(actor_id)); character(top_liege, top_id);
    character(actor_head, actor_head_id); character(main_head, main_head_id);
    character(faith_holder, faith_holder_id);
    Put(actor, s::kCharacterLandedDataOffset, actor_landed.data());
    Put(top_liege, s::kCharacterLandedDataOffset, top_landed.data());
    Put(actor_landed, s::kLandedTitlesOffset, actor_titles.data());
    Put(top_landed, s::kLandedTitlesOffset, top_titles.data());
    Put(actor_landed, s::kLandedTitlesCountOffset, std::int32_t{1});
    Put(top_landed, s::kLandedTitlesCountOffset, std::int32_t{1});
    Put(own_title, s::kTitleIdentityOffset, actor_titles[0]);
    Put(realm_title, s::kTitleIdentityOffset, top_titles[0]);
    Put(own_title, s::kTitleStateRiteIdOffset, own_rite_id);
    Put(realm_title, s::kTitleStateRiteIdOffset, realm_rite_id);
    Put(actor, r::kCharacterRiteIdOffset, std::uint32_t{0});
    Put(actor_rite, 8, std::uint32_t{0}); Put(actor_rite, r::kRiteFaithIdOffset, actor_faith_id);
    Put(main_rite, 8, main_rite_id); Put(own_rite, 8, own_rite_id); Put(realm_rite, 8, realm_rite_id);
    Put(own_rite, r::kRiteFaithIdOffset, own_faith_id);
    Put(realm_rite, r::kRiteFaithIdOffset, realm_faith_id);
    Put(actor_faith, 8, actor_faith_id); Put(actor_faith, r::kFaithMainRiteIdOffset, main_rite_id);
    Put(own_faith, 8, own_faith_id); Put(realm_faith, 8, realm_faith_id);
    Put(actor_rite, h::kRiteHeadCharacterIdOffset, actor_head_id);
    Put(main_rite, h::kRiteHeadCharacterIdOffset, main_head_id);
    Put(actor_faith, h::kFaithReligiousHeadTitleIdOffset, religious_title_id);
    Put(religious_title, h::kTitleReferenceIdOffset, religious_title_id);
    Put(religious_title, h::kTitleHolderCharacterIdOffset, faith_holder_id);
    Put(actor_rite, o::kCountyCountOffset, std::int32_t{0});
    Put(actor_rite, o::kCharacterFollowerCountOffset, std::int32_t{0});
  }
};
GovernanceFixture *fixture = nullptr;
void *Player(void *) { return fixture->player.data(); }
void *CharacterRite(void *) { return fixture->actor_rite.data(); }
void *CharacterFaith(void *) { return fixture->actor_faith.data(); }
void *RiteFaith(void *rite) {
  if (rite == fixture->actor_rite.data()) return fixture->actor_faith.data();
  return rite == fixture->own_rite.data() ? fixture->own_faith.data() : fixture->realm_faith.data();
}
void *MainRite(void *) { return fixture->main_rite.data(); }
void *TopLiege(void *) { return fixture->top_liege.data(); }
void *PrimaryTitle(void *character) {
  return character == fixture->actor.data() ? fixture->own_title.data() : fixture->realm_title.data();
}
void *TitleStateRite(void *title) {
  return title == fixture->own_title.data() ? fixture->own_rite.data() : fixture->realm_rite.data();
}
std::uint32_t *HeadId(void *rite, std::uint32_t *out) {
  *out = Get<std::uint32_t>(rite, h::kRiteHeadCharacterIdOffset);
  return fixture->bad_head_return ? nullptr : out;
}
c::CoreBindings Core() {
  return {true, &fixture->state_ptr, &fixture->jomini_ptr, &fixture->storage_ptr, &Player};
}
void *Head(void *rite) {
  return c::ResolveCoreCharacter(Core(), std::bit_cast<std::int32_t>(
      Get<std::uint32_t>(rite, h::kRiteHeadCharacterIdOffset)));
}
void *ReligiousTitle(void *) { return fixture->religious_title.data(); }
void *FaithHead(void *) {
  return c::ResolveCoreCharacter(Core(), std::bit_cast<std::int32_t>(
      Get<std::uint32_t>(fixture->religious_title.data(), h::kTitleHolderCharacterIdOffset)));
}
std::int32_t Counties(void *rite) { return Get<std::int32_t>(rite, o::kCountyCountOffset); }
std::int32_t Followers(void *rite) {
  if (fixture->change_frame_on_count && ++fixture->follower_reads == 2)
    Put(fixture->state, 8, GovernanceFixture::date + 1);
  return Get<std::int32_t>(rite, o::kCharacterFollowerCountOffset);
}
g::Bindings Bind(GovernanceFixture &value) {
  fixture = &value;
  r::Bindings religion{}; religion.enabled = true; religion.core = Core();
  religion.character_rite = &CharacterRite; religion.character_faith = &CharacterFaith;
  religion.rite_faith = &RiteFaith; religion.faith_main_rite = &MainRite;
  g::Bindings bindings{}; bindings.enabled = true; bindings.core = Core();
  bindings.state_rite = {true, religion, &TopLiege, &PrimaryTitle, &TitleStateRite};
  bindings.heads = {true, religion, &HeadId, &Head, &FaithHead, &ReligiousTitle};
  bindings.organization = {true, Core(), &CharacterRite, &Counties, &Followers};
  return bindings;
}
int checks = 0;
void Check(bool condition, const char *message) {
  ++checks;
  if (!condition) throw std::runtime_error(message);
}
[[maybe_unused]] void WriteWire(const std::filesystem::path &directory, const char *name, const g::Context &out) {
  std::ofstream(directory / name) << g::SerializePlayedRiteGovernance12002(out) << '\n';
}
void CheckDistinct(const g::Context &out) {
  Check(out.available && out.frame_available && out.failure == g::Failure::none,
        "actual aggregate observed frame");
  Check(out.state_rite.available && out.heads.available && out.organization.available,
        "all three actual components observed");
  Check(out.state_rite.actor_rite_id == std::uint32_t{0} && out.state_rite.actor_faith_main_rite_id == GovernanceFixture::main_rite_id &&
        out.state_rite.realm_primary_title.state_rite_id == GovernanceFixture::realm_rite_id &&
        out.state_rite.player_primary_title.state_rite_id == GovernanceFixture::own_rite_id,
        "actor main own-title and realm-state rites remain distinct");
  Check(out.heads.actor_rite_head_character_id == GovernanceFixture::actor_head_id &&
        out.heads.faith_main_rite_head_character_id == GovernanceFixture::main_head_id &&
        out.heads.faith_religious_head_holder_character_id == GovernanceFixture::faith_holder_id &&
        out.heads.faith_religious_head_title_id == GovernanceFixture::religious_title_id,
        "actor main and faith-title authority sources remain distinct");
  Check(out.organization.rite_id == std::uint32_t{0} && out.organization.county_count == 0 &&
        out.organization.character_follower_count == 0,
        "actual zero identity and cached counts remain observed zero");
}
void LegalAbsence(GovernanceFixture &value) {
  Put(value.actor, r::kCharacterRiteIdOffset, r::kAbsentReference);
  Put(value.realm_title, s::kTitleStateRiteIdOffset, r::kAbsentReference);
}
void CheckAbsence(const g::Context &out) {
  Check(out.available && out.state_rite.available && out.heads.available && out.organization.available,
        "legal absence is an observed aggregate");
  Check(!out.state_rite.actor_rite_id && !out.heads.actor_rite_id && !out.organization.rite_id &&
        !out.organization.county_count && !out.organization.character_follower_count,
        "actor rite absence remains null instead of zero");
  Check(out.state_rite.realm_primary_title.title_id && !out.state_rite.realm_primary_title.state_rite_id &&
        out.state_rite.player_primary_title.state_rite_id == GovernanceFixture::own_rite_id,
        "unset realm rite retains actual own title rite");
}
void CheckPartial(const g::Context &out) {
  Check(out.available && out.frame_available && out.state_rite.available && out.organization.available &&
        !out.heads.available && out.heads.failure == h::Failure::rite_head_unavailable,
        "actual failed head getter keeps two independent observations");
  Check(out.state_rite.realm_primary_title.state_rite_id == GovernanceFixture::realm_rite_id &&
        out.organization.county_count == 0 && !out.heads.actor_rite_head_character_id,
        "partial failure retains real state/count values and no false head");
}
} // namespace

#if !defined(XAR_RITE_GOVERNANCE_FIXTURE_ONLY)
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "output directory argument");
    const std::filesystem::path directory(argv[1]);
    GovernanceFixture value; auto bindings = Bind(value); g::Context out{};
    Check(g::ReadPlayedRiteGovernance12002(bindings, 501, out), "actual combined provider capture");
    CheckDistinct(out); WriteWire(directory, "distinct-zero.json", out);
    LegalAbsence(value);
    Check(g::ReadPlayedRiteGovernance12002(bindings, 502, out), "actual combined legal absence");
    CheckAbsence(out); WriteWire(directory, "legal-absent.json", out);
    Put(value.actor, r::kCharacterRiteIdOffset, std::uint32_t{0});
    Put(value.realm_title, s::kTitleStateRiteIdOffset, GovernanceFixture::realm_rite_id);
    value.bad_head_return = true;
    Check(g::ReadPlayedRiteGovernance12002(bindings, 503, out), "actual partial component failure");
    CheckPartial(out); WriteWire(directory, "heads-unavailable.json", out);
    bindings.state_rite.enabled = bindings.heads.enabled = bindings.organization.enabled = false;
    Check(!g::ReadPlayedRiteGovernance12002(bindings, 504, out) && !out.available && out.frame_available &&
          out.failure == g::Failure::components_unavailable, "actual frame with no available components");
    WriteWire(directory, "components-unavailable.json", out);
    bindings = Bind(value); value.bad_head_return = false; value.change_frame_on_count = true;
    Check(!g::ReadPlayedRiteGovernance12002(bindings, 505, out) && !out.available && !out.frame_available &&
          out.failure == g::Failure::state_changed && !out.state_rite.available && !out.heads.available &&
          !out.organization.available, "changed aggregate frame clears successful component output");
    WriteWire(directory, "frame-changed.json", out);
    std::cout << "PASS checks=" << checks << " cases=5 actual_combined_provider=true actual_serializer=true live=false\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
#endif
