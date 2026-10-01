#include "xar_bridge/ck3_12002_lifestyle.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string_view>

namespace {
namespace life = xar::ck3_12002::lifestyle;
namespace old = xar::ck3_11906;
namespace game = xar::game;

void Require(bool value, std::string_view message) {
  if (!value) throw std::runtime_error(std::string(message));
}
template <typename T, std::size_t Size>
void Put(std::array<std::byte, Size> &object, std::size_t offset, T value) {
  Require(offset + sizeof(value) <= Size, "fixture offset");
  std::memcpy(object.data() + offset, &value, sizeof(value));
}
template <std::size_t Size>
void Fixed(std::array<char, Size> &target, std::string_view value) {
  target = {};
  Require(value.size() < Size, "fixed string size");
  std::copy(value.begin(), value.end(), target.begin());
}
template <std::size_t Size>
void Key(std::array<std::byte, Size> &object, std::string_view key) {
  Put(object, 0x18, key.data());
  Put(object, 0x28, static_cast<std::uint64_t>(key.size()));
  Put(object, 0x30, std::uint64_t{127});
}
game::PlayerLifestyleWindowStableKeyV1 WindowKey(std::string_view key) {
  game::PlayerLifestyleWindowStableKeyV1 value{};
  Require(old::AssignPlayerLifestyleWindowStableKeyV1(key, value), "window key");
  return value;
}

struct Span {
  std::uintptr_t data = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};
struct NativeFixture {
  std::array<std::byte, 0x40> character{};
  std::array<std::byte, 0x840> focus{};
  std::array<std::byte, 0x160> lifestyle{};
  std::array<std::byte, 0x480> perk{};
  std::array<std::byte, 0xF30> focus_database{};
  std::array<std::byte, 0x80> perk_database{};
  std::array<std::byte, 0x80> trait_database{};
  std::array<std::array<std::byte, 0x40>, 32> traits{};
  std::array<std::uintptr_t, 32> trait_rows{};
  std::array<std::uintptr_t, 1> focus_rows{};
  std::array<std::uintptr_t, 1> perk_rows{};
  std::array<std::array<std::byte,0x480>,7> owned_perk_definitions{};
  std::array<std::uintptr_t,7> owned_perk_rows{};
  Span owned{};
  std::uintptr_t fallback = 0x11110000;
  std::uint32_t unused = 0;
  std::uint32_t used = 7;
  bool focus_present = true;
  bool native_legal = false;
  std::uint32_t validator_calls = 0;
  std::uint32_t submit_calls = 0;
  std::uint32_t frame_calls = 0;
  old::PlayerLifestyleSnapshotFrameV1 frame{};
  old::StockPerkLegalityFrameV1 stock_frame{};
  std::uint32_t player = 29829;
};
NativeFixture *g_fixture = nullptr;
const char *g_snapshot_output = nullptr;
constexpr std::uintptr_t kBase = 0x140000000;

bool ReadMemory(void *, std::uintptr_t address, void *output, std::size_t size) noexcept {
  if (g_fixture == nullptr || output == nullptr) return false;
  std::uintptr_t redirected = address;
  std::uintptr_t pointer = 0;
  if (address == kBase + 0x5C67188) {
    pointer = reinterpret_cast<std::uintptr_t>(g_fixture->focus_database.data());
  } else if (address == kBase + 0x4760BB0) {
    pointer = kBase + 0x288A890;
  } else if (address == kBase + 0x4760A20) {
    pointer = kBase + 0x288AE20;
  } else if (address == kBase + 0x54DBC00) {
    if (size != sizeof(g_fixture->player)) return false;
    std::memcpy(output, &g_fixture->player, size);
    return true;
  }
  if (pointer != 0) {
    if (size != sizeof(pointer)) return false;
    std::memcpy(output, &pointer, size);
    return true;
  }
  if (address == 0) return false;
  std::memcpy(output, reinterpret_cast<const void *>(redirected), size);
  return true;
}
bool Main(void *) noexcept { return true; }
bool StateFrame(void *, old::PlayerLifestyleSnapshotFrameV1 &output) noexcept {
  output = g_fixture->frame;
  ++g_fixture->frame_calls;
  return true;
}
bool StockFrame(void *, old::StockPerkLegalityFrameV1 &output) noexcept {
  output = g_fixture->stock_frame;
  return true;
}
void *Focus(void *) { return g_fixture->focus_present ? g_fixture->focus.data() : reinterpret_cast<void *>(g_fixture->fallback); }
void *Lifestyle(void *) { return g_fixture->lifestyle.data(); }
std::int32_t Unused(void *, void *) { return static_cast<std::int32_t>(g_fixture->unused); }
std::int32_t Used(void *, void *) { return static_cast<std::int32_t>(g_fixture->used); }
std::int64_t *Xp(void *, std::int64_t *output, void *, bool) {
  *output = 71'250'000;
  return output;
}
const void *Owned(void *) { return &g_fixture->owned; }
void *PerkDatabase() { return g_fixture->perk_database.data(); }
void *TraitDatabase() { return g_fixture->trait_database.data(); }
bool HasTrait(void *, const void *trait) {
  return trait == g_fixture->traits[9].data() || trait == g_fixture->traits[29].data();
}
bool Validator(void *command, void *) {
  ++g_fixture->validator_calls;
  std::uintptr_t table = 0;
  std::uint32_t player = 0;
  std::uintptr_t definition = 0;
  std::memcpy(&table, command, sizeof(table));
  std::memcpy(&player, static_cast<std::byte *>(command)+0x20, sizeof(player));
  std::memcpy(&definition, static_cast<std::byte *>(command)+0x28, sizeof(definition));
  if (player != g_fixture->player) return false;
  const bool focus = table == kBase+0x4760B80;
  if (!focus && table != kBase+0x47609F0) return false;
  if (definition != reinterpret_cast<std::uintptr_t>(focus ? g_fixture->focus.data() : g_fixture->perk.data())) return false;
  if (focus) {
    std::uint32_t current_player = 0;
    std::memcpy(&current_player, static_cast<std::byte *>(command)+0x30, sizeof(current_player));
    if (current_player != g_fixture->player) return false;
  }
  return g_fixture->native_legal;
}
bool Submit(void *, void *command, std::uint32_t flags) {
  Require(flags == 0x0E, "lifestyle command flags");
  Require(Validator(command,nullptr), "submit validator");
  ++g_fixture->submit_calls;
  return true;
}
bool Progress(void *, const old::StockFocusLegalityFrameV1 &, std::uintptr_t lifestyle,
              old::StockFocusTargetProgressV1 &output) noexcept {
  if (lifestyle != reinterpret_cast<std::uintptr_t>(g_fixture->lifestyle.data())) return false;
  output = {true, 71'250'000, 71'250'000, 1000,
            static_cast<std::int32_t>(g_fixture->unused), static_cast<std::int32_t>(g_fixture->used)};
  return true;
}
bool PlayerState(void *, const old::StockPerkLegalityFrameV1 &, std::uintptr_t,
                 old::StockPerkLegalityPlayerStateV1 &output) noexcept {
  output.target_lifestyle_key = WindowKey("stewardship_lifestyle");
  output.target_xp_total_raw = 71'250'000;
  output.target_xp_within_level_raw = 71'250'000;
  output.target_xp_per_level = 1000;
  output.unspent_perk_points = static_cast<std::int32_t>(g_fixture->unused);
  output.used_perk_points = static_cast<std::int32_t>(g_fixture->used);
  output.owned_perk_state_known = true;
  return true;
}

void Fill(NativeFixture &f) {
  g_fixture = &f;
  Put(f.character, 0x18, f.player);
  Key(f.focus,"stewardship_wealth_focus");
  Key(f.lifestyle,"stewardship_lifestyle");
  Key(f.perk,"cutting_corners_perk");
  Put(f.focus,0x7F8,reinterpret_cast<std::uintptr_t>(f.lifestyle.data()));
  Put(f.lifestyle,0x130,std::int32_t{1000});
  Put(f.perk,0x440,reinterpret_cast<std::uintptr_t>(f.lifestyle.data()));
  f.focus_rows[0]=reinterpret_cast<std::uintptr_t>(f.focus.data());
  f.perk_rows[0]=reinterpret_cast<std::uintptr_t>(f.perk.data());
  Put(f.focus_database,0xF08,Span{reinterpret_cast<std::uintptr_t>(f.focus_rows.data()),1,1});
  Put(f.perk_database,0x50,Span{reinterpret_cast<std::uintptr_t>(f.perk_rows.data()),1,1});
  constexpr std::array<std::string_view,7> owned_keys{{
    "golden_obligations_perk","this_is_my_domain_perk","at_any_cost_perk",
    "war_profiteer_perk","heregeld_perk","detailed_ledgers_perk","tax_man_perk"}};
  for(std::size_t i=0;i<owned_keys.size();++i) {
    Key(f.owned_perk_definitions[i],owned_keys[i]);
    Put(f.owned_perk_definitions[i],0x440,reinterpret_cast<std::uintptr_t>(f.lifestyle.data()));
    f.owned_perk_rows[i]=reinterpret_cast<std::uintptr_t>(f.owned_perk_definitions[i].data());
  }
  f.owned={reinterpret_cast<std::uintptr_t>(f.owned_perk_rows.data()),7,7};
  constexpr std::array<std::string_view,32> keys{{
    "education_diplomacy_1","education_diplomacy_2","education_diplomacy_3","education_diplomacy_4","education_diplomacy_5",
    "education_martial_1","education_martial_2","education_martial_3","education_martial_4","education_martial_5",
    "education_stewardship_1","education_stewardship_2","education_stewardship_3","education_stewardship_4","education_stewardship_5",
    "education_intrigue_1","education_intrigue_2","education_intrigue_3","education_intrigue_4","education_intrigue_5",
    "education_learning_1","education_learning_2","education_learning_3","education_learning_4","education_learning_5",
    "greedy","generous","shy","arrogant","ambitious","diligent","just"}};
  for(std::size_t i=0;i<keys.size();++i) { Key(f.traits[i],keys[i]); f.trait_rows[i]=reinterpret_cast<std::uintptr_t>(f.traits[i].data()); }
  Put(f.trait_database,0x50,Span{reinterpret_cast<std::uintptr_t>(f.trait_rows.data()),32,32});
  Fixed(f.frame.snapshot_id,"native:3");
  f.frame.public_revision=3;f.frame.native_revision=3;f.frame.proof_epoch=3;
  f.frame.date_raw=53220000;f.frame.paused=true;f.frame.map_ready=true;
  f.frame.has_played_character=true;f.frame.played_character_alive=true;
  f.frame.played_character_id=static_cast<std::int32_t>(f.player);
  f.frame.played_character=reinterpret_cast<std::uintptr_t>(f.character.data());
  f.frame.played_character_identity_round_trip=true;
  Fixed(f.stock_frame.episode_run_id,"fixture-life-12002");Fixed(f.stock_frame.snapshot_id,"native:3");
  f.stock_frame.public_revision=3;f.stock_frame.native_revision=3;f.stock_frame.proof_epoch=3;
  f.stock_frame.date_raw=53220000;f.stock_frame.played_character_id=f.player;
  f.stock_frame.played_character=f.frame.played_character;f.stock_frame.paused=true;
  f.stock_frame.map_ready=true;f.stock_frame.played_character_alive=true;f.stock_frame.storage_round_trip=true;
}

void TestState() {
  auto f=std::make_unique<NativeFixture>();Fill(*f);
  auto env=life::BindPlayerLifestyleSnapshotEnvironment12002V1(kBase,true,xar::ck3_12002::kExecutableSha256);
  Require(reinterpret_cast<std::uintptr_t>(env.current_focus)==kBase+0x29194D0,"new focus binder");
  Require(life::BindPlayerLifestyleSnapshotEnvironment12002V1(kBase,true,old::kPlayerLifestyleSnapshotExecutableSha256V1).current_focus==nullptr,"old build not bound");
  env.current_focus=&Focus;env.current_lifestyle=&Lifestyle;env.unspent_perk_points=&Unused;
  env.used_perk_points=&Used;env.lifestyle_xp=&Xp;env.unlocked_perks=&Owned;
  env.trait_database=&TraitDatabase;env.character_has_trait=&HasTrait;
  env.focus_fallback_slot_address=reinterpret_cast<std::uintptr_t>(&f->fallback);
  const old::PlayerLifestyleSnapshotAccessV1 access{nullptr,&StateFrame,&Main,&ReadMemory,nullptr};
  const old::PlayerLifestyleSnapshotRequestV1 request{"native:3",3,3,53220000,29829};
  auto state=std::make_unique<game::PlayerLifestyleSnapshotV1>();
  Require(life::ReadPlayerLifestyleSnapshot12002V1(env,access,request,*state)==game::ReadPlayerLifestyleSnapshotResultV1::available,"real native field reader");
  Require(state->state.current_lifestyle_progress.unspent_perk_points==0,"zero points observed");
  Require(state->state.current_lifestyle_progress.used_perk_points==7,"used points observed");
  Require(state->state.owned_perk_count==7,"complete owned perk collection");
  Require(state->state.current_lifestyle_progress.xp_total_raw==71250000,"XP observed");
  Require(state->state.actor_traits_ready && state->state.observed_actor_trait_count==2,"education/personality observed");
  Require(life::PlayerLifestyleStableKeyView12002V1(state->state.observed_actor_trait_keys[0])=="education_martial_5","held education");
  Require(f->frame_calls==2,"same frame double sample");
  if (g_snapshot_output != nullptr) {
    std::ofstream output(g_snapshot_output,std::ios::binary);
    output << life::SerializePlayerLifestyleSnapshot12002V1(*state) << '\n';
    Require(static_cast<bool>(output),"snapshot fixture output");
  }
  f->focus_present=false;
  Require(life::ReadPlayerLifestyleSnapshot12002V1(env,access,request,*state)==game::ReadPlayerLifestyleSnapshotResultV1::available,"known absent focus");
  Require(state->state.current_focus_presence==game::PlayerLifestyleFocusPresenceV1::absent,"focusless retained as absence");
}

void TestLegalityAndCommand() {
  auto f=std::make_unique<NativeFixture>();Fill(*f);
  auto focus_env=life::BindStockFocusLegalityEnvironment12002V1(kBase,true,xar::ck3_12002::kExecutableSha256);
  focus_env.offline_fixture=true;focus_env.validate_focus_command=&Validator;
  const old::StockFocusLegalityAccessV1 fa{nullptr,&Main,&StockFrame,&ReadMemory,&Progress};
  const auto focus=life::ReadStockFocusLegality12002V1(focus_env,fa);
  Require(focus.status==old::StockFocusLegalityStatusV1::observed_native_illegal && focus.validator_invoked_twice,"valid native focus false");
  Require(focus.target_progress.available && focus.target_progress.unspent_perk_points==0,"focus target progress");
  auto perk_env=life::BindStockPerkLegalityEnvironment12002V1(kBase,true,xar::ck3_12002::kExecutableSha256);
  perk_env.offline_fixture=true;perk_env.get_character_perk_database=&PerkDatabase;perk_env.validate_perk_command=&Validator;
  const old::StockPerkLegalityAccessV1 pa{nullptr,&Main,&StockFrame,&ReadMemory,&PlayerState,nullptr};
  const auto zero=life::ReadStockPerkLegality12002V1(perk_env,pa);
  Require(zero.status==old::StockPerkLegalityStatusV1::observed_native_illegal && zero.observed_unspent_points==0,"zero-point legal no-op");
  f->unused=1;f->native_legal=true;
  const auto perk=life::ReadStockPerkLegality12002V1(perk_env,pa);
  Require(perk.status==old::StockPerkLegalityStatusV1::observed_native_legal && perk.target_definition!=0,"positive perk exact definition");
  auto native=life::BindPlayerLifestyleSelectionNativeAdapterEnvironment12002V1(kBase,true,xar::ck3_12002::kExecutableSha256);
  Require(life::PlayerLifestyleSelectionNativeAdapterEnvironmentReady12002V1(native),"native new clone queue binder");
  native.offline_fixture_command=true;native.validate_focus_command=&Validator;native.validate_perk_command=&Validator;native.submit_command=&Submit;
  old::PlayerLifestyleSelectionNativeAdapterAccessV1 access{};
  access.is_application_main_thread=&Main;access.is_paused=&Main;
  Require(life::DispatchResolvedPlayerLifestylePerkNativeAdapter12002V1(native,access,f->player,perk.target_definition)==old::PlayerLifestyleSelectionNativeDispatchResultV1::submitted_verification_pending,"typed perk pending only");
  Require(f->submit_calls==1,"one typed native submit");
  Require(life::DispatchResolvedPlayerLifestyleFocusNativeAdapter12002V1(native,access,f->player,reinterpret_cast<std::uintptr_t>(f->focus.data()))==old::PlayerLifestyleSelectionNativeDispatchResultV1::submitted_verification_pending,"typed focus layout");
  Require(f->submit_calls==2,"one focus submit");
}

struct ActionFixture {
  game::PlayerLifestyleSelectionPreconditionV1 pre{};
  game::PlayerLifestyleSelectionStateObservationV1 post{};
  std::uint32_t submits=0;
};
bool Precondition(void *opaque,game::PlayerLifestyleSelectionPreconditionV1 &output) noexcept {
  output=static_cast<ActionFixture *>(opaque)->pre;return true;
}
bool Postcondition(void *opaque,game::PlayerLifestyleSelectionStateObservationV1 &output) noexcept {
  output=static_cast<ActionFixture *>(opaque)->post;return true;
}
bool ActionSubmit(void *opaque,game::PlayerLifestyleSelectionKindV1,
                  const game::PlayerLifestyleWindowStableKeyV1 &) noexcept {
  ++static_cast<ActionFixture *>(opaque)->submits;return true;
}
void TestActionAndIndependentReceipt() {
  auto fixture=std::make_unique<ActionFixture>();
  auto &state=fixture->pre.state;
  state.available=true;state.paused=true;Fixed(state.snapshot_id,"native:3");
  Fixed(state.episode_run_id,"fixture-life-12002");
  state.public_revision=3;state.native_revision=3;state.proof_epoch=3;
  state.date_raw=53220000;state.player_character_id=29829;
  state.current_focus_known=true;state.has_current_focus=true;
  state.current_focus_key=WindowKey("stewardship_wealth_focus");
  state.owned_perks_fully_materialized=true;state.lifestyle_progress_fully_materialized=true;
  state.lifestyle_progress_count=1;
  state.lifestyle_progress[0]={WindowKey("stewardship_lifestyle"),71250000,1};
  auto &c=fixture->pre.candidates;
  c.status=game::PlayerLifestyleWindowCandidatesStatusV1::available;
  Fixed(c.snapshot_id,"native:3");c.public_revision=3;c.native_revision=3;c.proof_epoch=3;
  c.date_raw=state.date_raw;c.player_character_id=29829;
  c.perk_status=game::PlayerLifestyleWindowCollectionStatusV1::available;
  c.perk_count=1;c.perks[0].key=WindowKey("cutting_corners_perk");
  c.perks[0].lifestyle_key=WindowKey("stewardship_lifestyle");c.perks[0].can_select=true;
  c.focus_status=game::PlayerLifestyleWindowCollectionStatusV1::available;
  c.focus_count=1;c.focuses[0].key=WindowKey("stewardship_wealth_focus");
  c.focuses[0].lifestyle_key=WindowKey("stewardship_lifestyle");c.focuses[0].can_select=true;
  c.readiness={true,true,true,true,true,true,true};
  const old::PlayerLifestyleSelectionActionAccessV1 access{fixture.get(),&Precondition,&Postcondition,&Main,&ActionSubmit};
  auto environment=life::BindPlayerLifestyleSelectionActionEnvironment12002V1(kBase,true,xar::ck3_12002::kExecutableSha256);
  environment.offline_fixture_command=true;
  game::PlayerLifestyleSelectionActionRequestV1 request{
    "fixture-perk-1",game::PlayerLifestyleSelectionKindV1::perk,"cutting_corners_perk",
    "native:3","fixture-life-12002",3,3,3,53220000,29829};
  game::PlayerLifestyleSelectionActionAckV1 ack{};
  Require(life::ExecutePlayerLifestyleSelectionAction12002V1(environment,access,request,ack)==game::PlayerLifestyleSelectionActionAckStatusV1::submitted_verification_pending,"semantic action pending");
  Require(ack.verification_pending && fixture->submits==1,"ACK not material success");
  fixture->post=state;
  game::PlayerLifestyleSelectionActionReceiptV1 receipt{};
  Require(life::VerifyPlayerLifestyleSelectionActionReceipt12002V1(access,ack,receipt)==game::PlayerLifestyleSelectionActionReceiptStatusV1::postcondition_failed,"same submit frame not receipt");
  Fixed(fixture->post.snapshot_id,"native:4");fixture->post.public_revision=4;
  fixture->post.native_revision=4;fixture->post.proof_epoch=4;
  fixture->post.owned_perk_count=1;fixture->post.owned_perk_keys[0]=WindowKey("cutting_corners_perk");
  fixture->post.lifestyle_progress[0].perk_points=0;
  Require(life::VerifyPlayerLifestyleSelectionActionReceipt12002V1(access,ack,receipt)==game::PlayerLifestyleSelectionActionReceiptStatusV1::applied && receipt.postcondition_verified,"independent state receipt applied");
  request.kind=game::PlayerLifestyleSelectionKindV1::focus;request.target_key="stewardship_wealth_focus";
  Require(life::ExecutePlayerLifestyleSelectionAction12002V1(environment,access,request,ack)==game::PlayerLifestyleSelectionActionAckStatusV1::rejected_before_submit && ack.rejection_reason=="target_already_applied","no repeated valid focus");
  Require(fixture->submits==1,"valid focus does not submit");
  request.kind=game::PlayerLifestyleSelectionKindV1::perk;request.target_key="cutting_corners_perk";
  state.lifestyle_progress[0].perk_points=0;c.perks[0].can_select=false;
  Require(life::ExecutePlayerLifestyleSelectionAction12002V1(environment,access,request,ack)==game::PlayerLifestyleSelectionActionAckStatusV1::rejected_before_submit,"zero-point target not submitted");
  Require(fixture->submits==1,"zero points no retry");
}
} // namespace

int main(int argc,char **argv) {
  if(argc==2)g_snapshot_output=argv[1];
  try { TestState();TestLegalityAndCommand();TestActionAndIndependentReceipt();std::cout<<"ck3_12002_lifestyle: 3 native-path and receipt suites GREEN\n";return 0; }
  catch(const std::exception &e) {std::cerr<<e.what()<<'\n';return 1;}
}
