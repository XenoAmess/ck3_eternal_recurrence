#ifndef NOMINMAX
#define NOMINMAX
#endif
#include "xar_bridge/player_control_identity_source_v1.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include "xar_bridge/protocol.hpp"
#include <windows.h>
#include <algorithm>
#include <array>
#include <limits>
#include <utility>

namespace xar::ck3_12003 {
namespace {
using namespace ck3_11906;
struct IdentitySourcePinV1 {
  std::uintptr_t rva;
  std::size_t bytes;
  std::array<unsigned char,128> code;
};
struct ControlCallbackLoadedPinV1 {
  std::uintptr_t rva;
  std::size_t bytes;
  std::array<unsigned char,128> code;
  std::size_t relocation_count;
  std::array<unsigned char,16> relocation_offsets;
};
#include "player_control_identity_pins_v1.inc"
constexpr std::uintptr_t kGameStateSlot=0x5C68C50;
constexpr std::uintptr_t kJominiStateSlot=0x5C6A520;
constexpr std::uintptr_t kCharacterStorageSlot=0x5C67568;
constexpr std::uintptr_t kCurrentLocalCharacterIdSlot=0x54DBC00;
constexpr std::uintptr_t kLocalPlayerIdSlot=0x5CC162C;
constexpr std::uintptr_t kPlayerVtable=0x491FDE8;
constexpr std::size_t kHumanIdsOffset=0x22358;
constexpr std::size_t kHumanCountOffset=0x22364;
constexpr std::int32_t kMaximumEntries=1024;
// This is an author safety bound, not a stock maximum. Above it the source
// remains incomplete; no truncated collection is ever marked complete.
constexpr std::int32_t kMaximumLivingCharacters=131072;
// Full source scanning and bounded wire publication are separate. Every source
// member is still checked; output consists only of actual living ruler playables.
constexpr std::size_t kMaximumRulerCandidates=8192;
constexpr std::size_t kPlayerControlEnvelopeReserve=4096;
static_assert(bridge::kMaximumFrameBytes>kPlayerControlEnvelopeReserve);
constexpr std::size_t kCharacterManagerOffset=0x2EE40;
constexpr std::uintptr_t kCharacterManagerVtable=0x47648F8;
constexpr std::uintptr_t kIdlerVtableRva=0x44BC408;
constexpr std::uintptr_t kHandlerVtableRva=0x44BA890;
constexpr std::uintptr_t kPauseVtableRva=0x44F7398;
constexpr std::uintptr_t kLobbyVtableRva=0x46AF770;
constexpr std::uintptr_t kPlayableSupplierSlot=0x5D28FD0;
constexpr std::uintptr_t kPlayableSupplierVtable=0x47581A0;
constexpr std::uintptr_t kCharacterPlayableVtable=0x4763C50;
constexpr std::uintptr_t kGameSetupSlot=0x5C6A468;
constexpr std::uintptr_t kIgnoreIronmanSlot=0x5C6A470;
constexpr std::uintptr_t kApplicationSlot=0x5CB87F8;
constexpr std::uintptr_t kMultiplayerModeSlot=0x5CC1628;
constexpr std::uintptr_t kPreparationLobbySlot=0x5CC1634;

template<class T> bool Read(std::uintptr_t address,T &value) noexcept {
  SIZE_T received=0;
  return address!=0 && ReadProcessMemory(GetCurrentProcess(),
      reinterpret_cast<const void *>(address),&value,sizeof(T),&received) &&
      received==sizeof(T);
}
template<class T> bool At(std::uintptr_t address,std::size_t offset,T &value) noexcept {
  return address<=(std::numeric_limits<std::uintptr_t>::max)()-offset &&
      Read(address+offset,value);
}
bool Pins(std::uintptr_t base) noexcept {
  for(const auto &pin:kIdentitySourcePins) {
    std::array<unsigned char,128> actual{};
    SIZE_T received=0;
    if(pin.bytes==0 || pin.bytes>actual.size() || base>(std::numeric_limits<std::uintptr_t>::max)()-pin.rva ||
        !ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(base+pin.rva),
            actual.data(),pin.bytes,&received) || received!=pin.bytes ||
        !std::equal(actual.begin(),actual.begin()+pin.bytes,pin.code.begin())) return false;
  }
  return true;
}
bool ControlCallbackPins(std::uintptr_t base) noexcept {
  if(base==0 || kControlCallbackLoadedPins.empty()) return false;
  constexpr std::uintptr_t disk_base=0x140000000ULL;
  const auto delta=static_cast<std::uint64_t>(base-disk_base);
  for(const auto &pin:kControlCallbackLoadedPins) {
    std::array<unsigned char,128> actual{};SIZE_T received=0;
    if(pin.bytes==0 || pin.bytes>actual.size() || pin.relocation_count>pin.relocation_offsets.size() ||
        pin.rva>=GuiExactImageSizeV1(GuiAbiRevisionV1::crozier12003) ||
        pin.bytes>GuiExactImageSizeV1(GuiAbiRevisionV1::crozier12003)-pin.rva ||
        base>(std::numeric_limits<std::uintptr_t>::max)()-pin.rva ||
        !ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void *>(base+pin.rva),
            actual.data(),pin.bytes,&received) || received!=pin.bytes) return false;
    for(std::size_t i=0;i<pin.relocation_count;++i) {
      const auto offset=pin.relocation_offsets[i];std::uint64_t word=0;
      if(offset>pin.bytes || pin.bytes-offset<sizeof(word)) return false;
      std::memcpy(&word,actual.data()+offset,sizeof(word));word-=delta;
      std::memcpy(actual.data()+offset,&word,sizeof(word));
    }
    if(!std::equal(actual.begin(),actual.begin()+pin.bytes,pin.code.begin())) return false;
  }
  return true;
}
bool Owner(const PlayerControlIdentitySourceContextV1 &ctx,
    const MainThreadQueryMailboxV1 &mailbox,const MainThreadExecutionStampV1 &stamp) noexcept {
  return ctx.ticket.sequence!=0 && ctx.owner_executor_context &&
      IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()) &&
      mailbox.state.load(std::memory_order_acquire)==MainThreadQueryMailboxStateV1::executing &&
      !mailbox.stop_requested.load(std::memory_order_acquire) &&
      mailbox.failure_flags.load(std::memory_order_acquire)==0 &&
      mailbox.published_sequence.load(std::memory_order_acquire)==ctx.ticket.sequence &&
      mailbox.permitted_frontend_executor && mailbox.executor==mailbox.permitted_frontend_executor &&
      mailbox.executor_context==ctx.owner_executor_context;
}
bool Process(const PlayerControlRequestV1 &request) noexcept {
  FILETIME creation{},exit{},kernel{},user{};
  if(request.expected_game_pid!=GetCurrentProcessId() ||
      request.expected_process_creation_filetime_100ns==0 ||
      !GetProcessTimes(GetCurrentProcess(),&creation,&exit,&kernel,&user)) return false;
  return ((std::uint64_t{creation.dwHighDateTime}<<32)|creation.dwLowDateTime)==
      request.expected_process_creation_filetime_100ns;
}
struct RawCurrentPlayerV1 {
  std::uintptr_t pointer=0,supplier=0;
  std::uint32_t player=0xFFFFFFFFU,playable=0xFFFFFFFFU;
  std::uint8_t flags=0;
  bool read_complete=false;
};
struct RawIdentitySourceV1 {
  std::uintptr_t game=0,jomini=0,campaign=0,players=0,storage=0;
  std::uintptr_t humans=0,entries=0;
  std::int32_t human_count=0,entry_count=0,local_player=-1;
  std::uint32_t current_character=0,local_command_player=0xFFFFFFFFU;
  std::uintptr_t setup=0,application=0,idler=0,handler=0,pause=0,lobby=0,supplier=0;
  std::int32_t peer_count=0,multiplayer_mode=0,handler_mode=0;
  std::uint8_t ignore_ironman=0,ironman_enabled=0,preparation_lobby=0;
  bool model_source_complete=false;
  std::optional<std::uint64_t> selected_character;
  std::optional<bool> selected_is_ruler;
  std::optional<std::uintptr_t> selected_actor,selected_actor_vtable;
  std::optional<bool> selected_alive;
  std::vector<std::uint32_t> human_ids;
  std::vector<PlayerControlControllerRecordV1> records;
  std::vector<RawCurrentPlayerV1> current_players;
  std::uintptr_t character_manager=0,living_array=0;
  std::int32_t living_count=0;
  bool living_members_complete=false;
  std::vector<std::uintptr_t> living_actors;
  std::vector<PlayerControlCandidateV1> living_candidates;
};
bool ValidId(std::uint32_t id) noexcept { return id!=0 && id!=0xFFFFFFFFU; }
bool Resolve(std::uintptr_t storage,std::uint32_t id,std::uintptr_t &actor,bool &alive) noexcept {
  actor=0;alive=false;
  std::uintptr_t rows=0,death=0;
  std::uint32_t count=0,actual=0,type=0;
  const auto index=id&0x00FFFFFFU;
  if(!ValidId(id) || !At(storage,0x20,rows) || rows==0 ||
      !At(storage,0x2C,count) || index>=count ||
      !At(rows,static_cast<std::size_t>(index)*0x10U+8,actor) || actor==0 ||
      !At(actor,0x18,actual) || actual!=id || !At(actor,0x1C,type) ||
      type!=0x43686172U || !At(actor,0x1D0,death)) return false;
  alive=death==0;return true;
}
bool Vtable(std::uintptr_t base,std::uintptr_t object,std::uintptr_t rva) noexcept {
  std::uintptr_t actual=0;
  return object!=0 && Read(object,actual) && actual==base+rva;
}
bool Supplier(std::uintptr_t base,RawIdentitySourceV1 &raw) noexcept {
  std::uintptr_t supplier_storage=0;
  return At(base,kPlayableSupplierSlot,raw.supplier) &&
      Vtable(base,raw.supplier,kPlayableSupplierVtable) &&
      At(raw.supplier,8,supplier_storage) && supplier_storage==raw.storage;
}
bool Models(std::uintptr_t base,RawIdentitySourceV1 &raw) noexcept {
  std::uintptr_t back=0,supplier_storage=0,selected_supplier=0,actor=0,ruler=0;
  std::uintptr_t phase=0,application=0;
  std::uint32_t selected_id=0;
  bool alive=false;
  if(!At(raw.jomini,0x10,raw.idler) || !Vtable(base,raw.idler,kIdlerVtableRva) ||
      !At(raw.idler,0x20,phase) || phase!=raw.jomini ||
      !At(raw.idler,0x90,application) || application!=raw.application ||
      !At(raw.idler,0x88,raw.handler) || !Vtable(base,raw.handler,kHandlerVtableRva) ||
      !At(raw.handler,0x60,raw.handler_mode) ||
      !At(raw.handler,0x1E0,raw.pause) || !Vtable(base,raw.pause,kPauseVtableRva) ||
      !At(raw.pause,0xA0,back) || back!=raw.handler ||
      !At(raw.handler,0x68,raw.lobby) || !Vtable(base,raw.lobby,kLobbyVtableRva) ||
      raw.handler>(std::numeric_limits<std::uintptr_t>::max)()-0x58 ||
      !At(raw.lobby,0xA0,back) || back!=raw.handler+0x58 ||
      !At(base,kPlayableSupplierSlot,raw.supplier) ||
      !Vtable(base,raw.supplier,kPlayableSupplierVtable) ||
      !At(raw.supplier,8,supplier_storage) || supplier_storage!=raw.storage ||
      !At(raw.lobby,0xA8,selected_supplier) || !At(raw.lobby,0xB0,selected_id)) return false;
  if(selected_supplier==0 && selected_id==0xFFFFFFFFU) return true;
  if(selected_supplier!=raw.supplier || !ValidId(selected_id) ||
      (!Resolve(raw.storage,selected_id,actor,alive)) ||
      actor>(std::numeric_limits<std::uintptr_t>::max)()-8 ||
      !Vtable(base,actor+8,kCharacterPlayableVtable)) return false;
  std::uintptr_t actor_vtable=0;
  if(!At(actor,0,actor_vtable) || actor_vtable<base || actor_vtable-base>=GuiExactImageSizeV1(GuiAbiRevisionV1::crozier12003)) return false;
  raw.selected_character=selected_id;
  raw.selected_actor=actor;raw.selected_actor_vtable=actor_vtable;raw.selected_alive=alive;
  if(alive) {
    if(!At(actor,0x1C0,ruler)) return false;
    // Exact registered Character.IsRuler predicate: actor+0x1C0 != NULL.
    raw.selected_is_ruler=ruler!=0;
  }
  return true;
}
bool LivingMembers(std::uintptr_t base,RawIdentitySourceV1 &raw) {
  if(raw.campaign>(std::numeric_limits<std::uintptr_t>::max)()-kCharacterManagerOffset) return false;
  raw.character_manager=raw.campaign+kCharacterManagerOffset;
  if(!Vtable(base,raw.character_manager,kCharacterManagerVtable) ||
      !At(raw.character_manager,0x20,raw.living_array) ||
      !At(raw.character_manager,0x2C,raw.living_count) || raw.living_count<0 ||
      raw.living_count>kMaximumLivingCharacters || (raw.living_count!=0 && raw.living_array==0)) return false;
  raw.living_actors.reserve(static_cast<std::size_t>(raw.living_count));
  raw.living_candidates.reserve((std::min)(static_cast<std::size_t>(raw.living_count),kMaximumRulerCandidates));
  std::vector<std::uint32_t> ids;
  ids.reserve(static_cast<std::size_t>(raw.living_count));
  for(std::int32_t i=0;i<raw.living_count;++i) {
    std::uintptr_t listed=0,resolved=0,ruler=0;
    std::uint32_t id=0;
    bool alive=false;
    if(!At(raw.living_array,static_cast<std::size_t>(i)*sizeof(std::uintptr_t),listed) || listed==0 ||
        !At(listed,0x18,id) || !ValidId(id) || !Resolve(raw.storage,id,resolved,alive) || resolved!=listed ||
        listed>(std::numeric_limits<std::uintptr_t>::max)()-8 ||
        !Vtable(base,listed+8,kCharacterPlayableVtable) || !At(listed,0x1C0,ruler)) return false;
    raw.living_actors.push_back(listed);ids.push_back(id);
    // A death awaiting maintenance is read and verified, then filtered by the
    // same actual death predicate used by the stock all-living ruler traversal.
    if(!alive || ruler==0) continue;
    if(raw.living_candidates.size()==kMaximumRulerCandidates) return false;
    PlayerControlCandidateV1 candidate{};
    candidate.character_id=id;candidate.playable_id=id;
    candidate.is_ruler=true;candidate.source_verified=true;
    // Source completeness concerns this actual living ruler/playable universe only.
    // Menu eligibility, CanControl and actual selection widget remain NULL.
    raw.living_candidates.push_back(candidate);
  }
  std::sort(ids.begin(),ids.end());
  if(std::adjacent_find(ids.begin(),ids.end())!=ids.end() ||
      !std::binary_search(ids.begin(),ids.end(),raw.current_character)) return false;
  // An independently resolved live selected character must belong to this
  // supposedly complete maintained collection; disagreement stays incomplete.
  return !raw.selected_character || !raw.selected_is_ruler.has_value() ||
      (*raw.selected_character<=0xFFFFFFFEULL &&
       std::binary_search(ids.begin(),ids.end(),static_cast<std::uint32_t>(*raw.selected_character)));
}
bool Raw(std::uintptr_t base,RawIdentitySourceV1 &raw) {
  if(!At(base,kGameStateSlot,raw.game) || raw.game==0 ||
      !At(base,kJominiStateSlot,raw.jomini) || raw.jomini==0 ||
      !At(base,kCharacterStorageSlot,raw.storage) || raw.storage==0 ||
      !At(base,kCurrentLocalCharacterIdSlot,raw.current_character) || !ValidId(raw.current_character) ||
      !At(raw.game,0xA0,raw.campaign) || raw.campaign==0 ||
      !At(raw.jomini,0x18,raw.players) || raw.players==0 ||
      !At(raw.players,0x1F0,raw.local_player) || raw.local_player<0 ||
      !At(base,kLocalPlayerIdSlot,raw.local_command_player) ||
      raw.local_command_player!=static_cast<std::uint32_t>(raw.local_player) ||
      !At(raw.campaign,kHumanIdsOffset,raw.humans) ||
      !At(raw.campaign,kHumanCountOffset,raw.human_count) ||
      raw.human_count<0 || raw.human_count>kMaximumEntries ||
      (raw.human_count!=0 && raw.humans==0) ||
      !At(raw.players,0x1D8,raw.entries) ||
      !At(raw.players,0x1E4,raw.entry_count) ||
      raw.entry_count<0 || raw.entry_count>kMaximumEntries ||
      (raw.entry_count!=0 && raw.entries==0)) return false;
  raw.human_ids.reserve(static_cast<std::size_t>(raw.human_count));
  for(std::int32_t i=0;i<raw.human_count;++i) {
    std::uint32_t id=0;
    if(!At(raw.humans,static_cast<std::size_t>(i)*4U,id) || !ValidId(id) ||
        std::find(raw.human_ids.begin(),raw.human_ids.end(),id)!=raw.human_ids.end()) return false;
    raw.human_ids.push_back(id);
  }
  if(!At(base,kGameSetupSlot,raw.setup) || raw.setup==0 ||
      !At(base,kIgnoreIronmanSlot,raw.ignore_ironman) ||
      !At(raw.setup,0x112,raw.ironman_enabled) ||
      !At(base,kApplicationSlot,raw.application) || raw.application==0 || raw.application!=raw.players ||
      !At(raw.application,0x1E4,raw.peer_count) || raw.peer_count!=raw.entry_count ||
      raw.peer_count<0 || raw.peer_count>kMaximumEntries ||
      !At(base,kMultiplayerModeSlot,raw.multiplayer_mode) ||
      !At(base,kPreparationLobbySlot,raw.preparation_lobby)) return false;
  // Bind the two actual stock GetLocalPlayer and LobbyPlayer.GetPlayable
  // owners to the same existing manager. Never call a mutex/lazy getter.
  if(!Supplier(base,raw)) return false;
  raw.model_source_complete=Models(base,raw);
  raw.living_members_complete=LivingMembers(base,raw);
  if(!raw.living_members_complete) raw.living_candidates.clear();
  raw.records.reserve(static_cast<std::size_t>(raw.entry_count));
  raw.current_players.reserve(static_cast<std::size_t>(raw.entry_count));
  std::vector<std::uint32_t> player_ids;
  player_ids.reserve(static_cast<std::size_t>(raw.entry_count));
  for(std::int32_t i=0;i<raw.entry_count;++i) {
    PlayerControlControllerRecordV1 record{};
    RawCurrentPlayerV1 source{};
    std::uintptr_t actor=0;
    bool alive=false;
    source.read_complete=At(raw.entries,static_cast<std::size_t>(i)*sizeof(std::uintptr_t),source.pointer) &&
        Vtable(base,source.pointer,kPlayerVtable) && At(source.pointer,0x70,source.player) &&
        source.player<=0x7FFFFFFFU && At(source.pointer,0x50,source.supplier) &&
        At(source.pointer,0x58,source.playable) && At(source.pointer,0x48,source.flags);
    raw.current_players.push_back(source);
    if(!source.read_complete) {
      // Every array member is emitted, including a NULL row. Unknown objects
      // never disappear to produce a fake unique local controller.
      raw.records.push_back(record);continue;
    }
    player_ids.push_back(source.player);record.player_id=source.player;
    if(source.supplier!=raw.supplier || !ValidId(source.playable) ||
        !Resolve(raw.storage,source.playable,actor,alive) ||
        actor>(std::numeric_limits<std::uintptr_t>::max)()-8 ||
        !Vtable(base,actor+8,kCharacterPlayableVtable)) {
      raw.records.push_back(record);continue;
    }
    record.character_id=source.playable;
    const bool human=alive && std::find(raw.human_ids.begin(),raw.human_ids.end(),source.playable)!=raw.human_ids.end();
    // Exact CIsAITrigger::predicate, independent of the lobby model.
    record.is_ai=!human;
    if((source.flags&0x20U)==0) {
      if(!human) record.is_current_controller=false;
      else if(source.player==static_cast<std::uint32_t>(raw.local_player) &&
          source.playable==raw.current_character) record.is_current_controller=true;
      // Other human-player membership remains NULL until independently proved.
    }
    // A stock observer or unresolved tuple also retains NULL membership.
    raw.records.push_back(record);
  }
  std::sort(player_ids.begin(),player_ids.end());
  if(std::adjacent_find(player_ids.begin(),player_ids.end())!=player_ids.end()) return false;
  return true;
}
bool Same(const RawIdentitySourceV1 &a,const RawIdentitySourceV1 &b) noexcept {
  if(a.game!=b.game || a.jomini!=b.jomini || a.campaign!=b.campaign ||
      a.players!=b.players || a.storage!=b.storage || a.humans!=b.humans ||
      a.entries!=b.entries || a.local_player!=b.local_player ||
       a.current_character!=b.current_character || a.local_command_player!=b.local_command_player ||
       a.human_ids!=b.human_ids ||
      a.records.size()!=b.records.size() || a.setup!=b.setup || a.application!=b.application ||
      a.peer_count!=b.peer_count || a.multiplayer_mode!=b.multiplayer_mode ||
      a.preparation_lobby!=b.preparation_lobby || a.handler_mode!=b.handler_mode ||
      a.ignore_ironman!=b.ignore_ironman || a.ironman_enabled!=b.ironman_enabled ||
      a.model_source_complete!=b.model_source_complete || a.idler!=b.idler ||
      a.handler!=b.handler || a.pause!=b.pause || a.lobby!=b.lobby ||
      a.supplier!=b.supplier || a.selected_character!=b.selected_character ||
       a.selected_is_ruler!=b.selected_is_ruler ||
       a.selected_actor!=b.selected_actor || a.selected_actor_vtable!=b.selected_actor_vtable ||
       a.selected_alive!=b.selected_alive ||
      a.character_manager!=b.character_manager || a.living_array!=b.living_array ||
      a.living_count!=b.living_count || a.living_members_complete!=b.living_members_complete ||
      a.living_actors!=b.living_actors || a.living_candidates.size()!=b.living_candidates.size() ||
      a.current_players.size()!=b.current_players.size()) return false;
  for(std::size_t i=0;i<a.current_players.size();++i) {
    const auto &x=a.current_players[i];const auto &y=b.current_players[i];
    if(x.pointer!=y.pointer || x.supplier!=y.supplier || x.player!=y.player ||
        x.playable!=y.playable || x.flags!=y.flags || x.read_complete!=y.read_complete) return false;
  }
  for(std::size_t i=0;i<a.living_candidates.size();++i) {
    const auto &x=a.living_candidates[i];const auto &y=b.living_candidates[i];
    if(x.character_id!=y.character_id || x.playable_id!=y.playable_id ||
        x.is_ruler!=y.is_ruler || x.source_verified!=y.source_verified) return false;
  }
  for(std::size_t i=0;i<a.records.size();++i) {
    const auto &x=a.records[i];const auto &y=b.records[i];
    if(x.player_id!=y.player_id || x.character_id!=y.character_id ||
        x.is_current_controller!=y.is_current_controller || x.is_ai!=y.is_ai) return false;
  }
  return true;
}
} // namespace
bool ReadPlayerControlOwnedIdentitySourceV1(const PlayerControlIdentitySourceContextV1 &ctx,
    const MainThreadQueryMailboxV1 &mailbox,const MainThreadExecutionStampV1 &stamp,
    const ZhongguoScoreboardNativeEnvironmentV1 &env,PlayerControlObservationV1 &out,
    PlayerControlOwnedIdentityBindingV1 &owned) noexcept {
  owned={};
  out.local_player_id.reset();out.controlled_character_id.reset();
  out.controlled_character_is_ai.reset();out.controller_records.clear();
  out.controller_records_complete=false;out.selected_character_id.reset();
  out.ironman.reset();out.multiple_players.reset();
  out.candidates.clear();out.candidates_complete=false;
  if(!kPlayerControlV1CompiledEnabled) { out.reason="player_control_identity_source_disabled";return false; }
  try {
    if(!ctx.request || !ctx.game || !ctx.game->enabled() ||
        ctx.game->descriptor().game_version!="1.20.0.3" ||
        ctx.game->descriptor().executable_sha256!="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6" ||
        !env.exact_build_admitted || env.offline_fixture_function_overrides ||
        env.module_base==0 || env.gui_abi_revision!=GuiAbiRevisionV1::crozier12003 ||
        env.module_base!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)) ||
        ctx.native_revision==0 || ctx.native_revision!=ctx.request->expected_revision ||
        ctx.connection_generation==0 || ctx.connection_generation!=ctx.request->expected_connection_generation ||
        ctx.request->expected_player_character_id>0xFFFFFFFEULL ||
        !IsCompletePlayerControlCharacterIdV1(ctx.request->expected_player_character_id) ||
        !Process(*ctx.request) || !Owner(ctx,mailbox,stamp) || !Pins(env.module_base)) {
      out.reason="player_control_identity_source_binding_or_owner_unverified";return false;
    }
    game::Snapshot before{},after{};
    if(!game::ReadSnapshot(*ctx.game,before) || before!=ctx.expected_snapshot ||
        !before.paused || !before.map_ready || !before.has_played_character || !before.played_character_alive ||
        before.played_character_id!=ctx.request->expected_player_character_id || before.date_raw!=stamp.date_raw) {
      out.reason="player_control_identity_source_frame_unverified";return false;
    }
    RawIdentitySourceV1 first{},second{};
    std::uintptr_t actor=0;bool alive=false;
    if(!Raw(env.module_base,first) || first.jomini!=stamp.jomini_state || first.game!=stamp.game_state ||
        first.current_character!=ctx.request->expected_player_character_id ||
        !Resolve(first.storage,first.current_character,actor,alive) || !alive ||
        !Raw(env.module_base,second) || !Same(first,second) ||
        !game::ReadSnapshot(*ctx.game,after) || after!=before || !Owner(ctx,mailbox,stamp)) {
      out.reason="player_control_identity_source_changed_or_incomplete";return false;
    }
    out.ironman=first.ignore_ironman==0 && first.ironman_enabled!=0;
    out.multiple_players=first.peer_count>1;
    if(first.multiplayer_mode!=0) {
      out.reason="player_control_actual_multiplayer_mode_unavailable";return false;
    }
    if(first.preparation_lobby!=0) {
      out.reason="player_control_actual_preparation_lobby_unavailable";return false;
    }
    if(first.living_members_complete) {
      out.candidates=std::move(first.living_candidates);
      // Entire actual living collection read twice at the
      // paused owner boundary and filtered by actual IsRuler, with no claim of
      // complete stock chooser eligibility or visibility.
      out.candidates_complete=true;
    }
    if(first.model_source_complete) {
      out.selected_character_id=first.selected_character;
      if(!first.living_members_complete && first.selected_character && first.selected_is_ruler.has_value()) {
        PlayerControlCandidateV1 selected{};
        selected.character_id=first.selected_character;
        // CCharacter IPlayable slot8 reads character+0x18 full uint32 ID.
        selected.playable_id=first.selected_character;
        selected.is_ruler=first.selected_is_ruler;
        selected.source_verified=true;
        // A selected member is actual source data, not full enumeration.
        // CanControl and GUI visibility/enabled stay NULL pending their sources.
        out.candidates.push_back(selected);
      }
    }
    out.local_player_id=static_cast<std::uint32_t>(first.local_player);
    out.controlled_character_id=first.current_character;
    out.controlled_character_is_ai=std::find(first.human_ids.begin(),first.human_ids.end(),first.current_character)==first.human_ids.end();
    out.controller_records=std::move(first.records);
    // Current-player array enumeration is complete, never played-history.
    // Unknown object/tuple/observer/other-human membership stays NULL and the
    // unchanged controller gate rejects it; no row is silently dropped.
    out.controller_records_complete=true;
    if(first.model_source_complete) {
      // These pointers originate solely from the fixed stock owner chain and
      // complete selected tuple/storage/type/IPlayable verification above.
      // Both raw passes, loaded code pins, identity snapshot and owner stamp
      // matched. The caller cannot set source booleans or an arbitrary address.
      owned.mailbox_sequence=ctx.ticket.sequence;owned.pump_epoch=stamp.pump_epoch;
      owned.owner_thread_id=stamp.thread_id;owned.date_raw=stamp.date_raw;
      owned.handler=first.handler;owned.pause_menu=first.pause;owned.lobby=first.lobby;
      owned.playable_supplier=first.supplier;
      owned.selected_character_id=first.selected_character;
      owned.selected_character=first.selected_actor;
      owned.selected_character_vtable=first.selected_actor_vtable;
      owned.selected_character_alive=first.selected_alive;
      owned.selected_character_is_ruler=first.selected_is_ruler;
      // Character context datatype, GUI semantic eligibility, model lifetime
      // beyond this pump and CanControl safe-query topology remain unavailable.
      owned.source_complete=true;
    }
    // Use the frozen actual encoder and the actual transport admission bound,
    // reserving space for the fixed command-result envelope. Never disconnect
    // the pipe by publishing a complete oversized candidate collector.
    if(SerializePlayerControlObservationV1(out).size()>
        bridge::kMaximumFrameBytes-kPlayerControlEnvelopeReserve) {
      out.candidates.clear();out.candidates_complete=false;
      out.reason="identity_sources_observed_candidate_wire_limit_complete_collection_unavailable";
      return true;
    }
    out.reason=first.living_members_complete
        ? "identity_living_ruler_playable_collection_and_legality_sources_observed_control_gui_actions_unavailable"
        : first.model_source_complete
          ? "identity_selected_ruler_and_legality_sources_observed_complete_candidates_and_actions_unavailable"
          : "identity_and_legality_sources_observed_actual_pause_lobby_model_unavailable";
    return true;
  } catch(...) {
    owned={};
    out.candidates.clear();out.candidates_complete=false;
    out.controller_records.clear();out.controller_records_complete=false;
    out.reason="player_control_identity_source_exception";return false;
  }
}
bool ReadPlayerControlIdentitySourceV1(const PlayerControlIdentitySourceContextV1 &ctx,
    const MainThreadQueryMailboxV1 &mailbox,const MainThreadExecutionStampV1 &stamp,
    const ZhongguoScoreboardNativeEnvironmentV1 &env,PlayerControlObservationV1 &out) noexcept {
  PlayerControlOwnedIdentityBindingV1 owned{};
  return ReadPlayerControlOwnedIdentitySourceV1(ctx,mailbox,stamp,env,out,owned);
}
} // namespace xar::ck3_12003

// External review candidate. No build, route, installation, or runtime execution.
// C++20. DEFAULT OFF. All native function pointers below are compared, never called.
// The owner must bind Source from its corrected fixed owner source reader and admit ABI_PINS.json
// before this zero-input private query. These internal arguments are not MCP fields.
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include <array>
#include <charconv>
#include <cstring>
#include <limits>
#include <optional>
#include <string>
#include <utility>
#include <vector>
#if defined(_MSC_VER)
#include <windows.h>
#endif
#ifndef XAR_CK3_ENABLE_CONTROL_CALLBACK_SOURCE_PRIVATE_V1
#define XAR_CK3_ENABLE_CONTROL_CALLBACK_SOURCE_PRIVATE_V1 0
#endif

namespace xar::ck3_11906 {
struct ControlCallbackOwnedSourceDraftV1 {
  // A fixed owner source query supplies these; no transport input may set them.
  bool exact_004_pinset_admitted = false, stock_gui_source_admitted = false;
  bool source_inventory_complete = false, selected_character_type_admitted = false;
  std::uintptr_t handler = 0, actual_lobby = 0, selected_supplier = 0;
  std::uint32_t selected_id = 0;
  std::optional<std::uintptr_t> selected_character, selected_character_vtable;
  // Type admission includes independently resolved character storage/full ID,
  // death, primary class and IPlayable subobject. No request may supply these.
  // The AST's observed key is read below, never supplied or named by a caller.
};
struct ControlCallbackQueryDraftV1 {
  std::string reason = "control_callback_source_private_default_off";
  std::optional<bool> read_complete, root_exists, root_visible, root_unique;
  std::optional<bool> target_exists, target_visible, target_enabled,
      unique_target, semantic_qualified, dispatch_admitted;
  std::optional<std::uint64_t> root_vtable_rva, target_vtable_rva;
  std::optional<std::uintptr_t> target;
};

#if XAR_CK3_ENABLE_CONTROL_CALLBACK_SOURCE_PRIVATE_V1
namespace control_callback_draft {
constexpr std::string_view kRoot = "lobbyview";
constexpr std::uintptr_t kButtonTypeDescriptor = 0x5B5B9D0;
struct ReadRecord { std::uintptr_t address; std::vector<std::byte> bytes; };
struct Trace {
  std::vector<ReadRecord> reads;
  std::size_t total_read_bytes=0;
  NamedGuiTreeInspectionV1 global_tree, local_tree;
  void *gui_context=nullptr, *gui_owner=nullptr;
  bool Read(std::uintptr_t p, void *out, std::size_t size) {
    if (!p || !out || size==0 || size > 16384 || reads.size()>=65536 ||
        total_read_bytes>16U*1024U*1024U || size>16U*1024U*1024U-total_read_bytes ||
        p > std::numeric_limits<std::uintptr_t>::max()-size)
      return false;
#if defined(_MSC_VER)
    if (!Guard(p, out, size)) return false;
#else
    return false; // no unguarded read fallback
#endif
    total_read_bytes+=size;
    ReadRecord row{p, std::vector<std::byte>(size)};
    std::memcpy(row.bytes.data(), out, size); reads.push_back(std::move(row));
    return true;
  }
#if defined(_MSC_VER)
  static bool Guard(std::uintptr_t p, void *out, std::size_t size) noexcept {
    __try { std::memcpy(out, reinterpret_cast<const void *>(p), size); return true; }
    __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
  }
#endif
  template<class T> bool At(std::uintptr_t p, std::size_t off, T &out) {
    if (p > std::numeric_limits<std::uintptr_t>::max()-off) return false;
    return Read(p+off, &out, sizeof out);
  }
};
struct VectorHead { std::uintptr_t data; std::int32_t capacity, count; };
bool Same(const Trace &a, const Trace &b) {
  const auto same_tree=[](const NamedGuiTreeInspectionV1 &x,
                          const NamedGuiTreeInspectionV1 &y) {
    if(x.scope_root_name!=y.scope_root_name || x.root_available!=y.root_available ||
       x.truncated!=y.truncated || x.widget_count!=y.widget_count ||
       x.widgets.size()!=y.widgets.size()) return false;
    for(std::size_t i=0;i<x.widgets.size();++i) {
      const auto &u=x.widgets[i], &v=y.widgets[i];
      if(u.runtime_name!=v.runtime_name || u.child_path!=v.child_path ||
         u.depth!=v.depth || u.child_count!=v.child_count || u.vtable_rva!=v.vtable_rva ||
         u.effective_visible!=v.effective_visible || u.enabled!=v.enabled) return false;
    }
    return true;
  };
  if (a.reads.size()!=b.reads.size() || a.gui_context!=b.gui_context ||
      a.gui_owner!=b.gui_owner || !same_tree(a.global_tree,b.global_tree) ||
      !same_tree(a.local_tree,b.local_tree)) return false;
  for (std::size_t i=0;i<a.reads.size();++i)
    if(a.reads[i].address!=b.reads[i].address || a.reads[i].bytes!=b.reads[i].bytes)
      return false;
  return true;
}
bool Head(Trace &t, std::uintptr_t p, VectorHead &h, std::int32_t max=64) {
  return t.At(p,0,h) && h.count>=0 && h.count<=max && h.capacity>=h.count &&
      h.capacity<=4096 && (h.count==0 || h.data!=0);
}
bool Module(std::uintptr_t base, std::uintptr_t p, std::size_t size) {
  const auto image=GuiExactImageSizeV1(GuiAbiRevisionV1::crozier12003);
  return p>=base && p-base<image && size<=image-(p-base);
}
// MSVC x64 RTTI identifies every census row before any button is excluded.
// An unreadable/unsupported RTTI row makes the entire census unavailable.
bool ButtonClass(Trace &t, std::uintptr_t base, std::uintptr_t vt, bool &is_button) {
  is_button=false; std::uintptr_t col=0; std::array<std::uint32_t,6> c{};
  if(vt<8 || !Module(base,vt,14*8) || !t.At(vt-8,0,col) ||
     !Module(base,col,24) || !t.At(col,0,c) || c[0]!=1 || c[5]!=col-base)
    return false;
  const auto chd=base+c[4]; std::array<std::uint32_t,4> h{};
  if(!Module(base,chd,16) || !t.At(chd,0,h) || h[2]==0 || h[2]>128)
    return false;
  const auto array=base+h[3];
  if(!Module(base,array,h[2]*4)) return false;
  for(std::uint32_t i=0;i<h[2];++i) {
    std::uint32_t bd=0, td=0;
    if(!t.At(array,i*4,bd) || !Module(base,base+bd,4) || !t.At(base+bd,0,td))
      return false;
    if(td==kButtonTypeDescriptor) is_button=true;
  }
  return !is_button || c[1]==0;
}
bool ParseActualPath(std::string_view path, std::vector<std::uint32_t> &out) {
  out.clear(); std::size_t start=0;
  while(start<path.size()) {
    const auto slash=path.find('/',start);
    const auto end=slash==std::string_view::npos ? path.size() : slash;
    std::uint32_t value=0;
    const auto r=std::from_chars(path.data()+start,path.data()+end,value);
    if(end==start || r.ec!=std::errc{} || r.ptr!=path.data()+end || out.size()>=64)
      return false;
    out.push_back(value); start=end+1;
  }
  return true;
}
bool Source(Trace &t, std::uintptr_t base, const ControlCallbackOwnedSourceDraftV1 &s) {
  std::uintptr_t lobby=0, vt=0, back=0, supplier=0, raw_supplier=0;
  std::uint32_t id=0;
  return s.handler && s.handler<=std::numeric_limits<std::uintptr_t>::max()-0x58 &&
      s.actual_lobby && s.selected_supplier && s.selected_id &&
      t.At(s.handler,0,vt) && vt==base+0x44BA890 &&
      t.At(s.handler,0x68,lobby) && lobby==s.actual_lobby &&
      t.At(lobby,0,vt) && vt==base+0x46AF770 &&
      t.At(lobby,0xA0,back) && back==s.handler+0x58 &&
      t.At(lobby,0xA8,raw_supplier) && raw_supplier==s.selected_supplier &&
      t.At(lobby,0xB0,id) && id==s.selected_id &&
      t.At(base+0x5D28FD0,0,supplier) && supplier==s.selected_supplier &&
      t.At(supplier,0,vt) && vt==base+0x47581A0;
}
// 3AC38E0 first resolves local rows; 3AC3F10 replaces unavailable local rows
// from the nearest available matching parent row. Its parent selection is
// context+0x108, otherwise widget+0xE8. Only direct kinds 0/1 are supported.
// A matching unavailable local row must also be direct: the native initial
// local pass would otherwise execute an unknown getter before inheritance.
bool Bound(Trace &t, std::uintptr_t widget, std::uint32_t dtype,
            std::uintptr_t expected) {
  std::array<std::uintptr_t,64> visited{}; std::size_t depth=0;
  std::uintptr_t current=widget;
  while(current) {
    if(depth==visited.size()) return false;
    for(std::size_t i=0;i<depth;++i) if(visited[i]==current) return false;
    visited[depth++]=current;
    std::uintptr_t context=0;
    if(!t.At(current,0xE0,context) || (depth==1 && !context)) return false;
    if(context) {
      std::uint8_t initialized=0; VectorHead rows{};
      if(depth==1 && (!t.At(context,0x115,initialized) || !initialized)) return false;
      if(!Head(t,context+0x90,rows)) return false;
      std::size_t found=0; bool available_match=false;
      for(std::int32_t i=0;i<rows.count;++i) {
        const auto row=rows.data+i*0x50; std::uint32_t type=0;
        if(!t.At(row,0x48,type)) return false;
        if(type!=dtype) continue;
        if(++found!=1) return false; // duplicates are unsupported, not skipped
        std::int8_t kind=-1; std::uint8_t available=0; std::uintptr_t ptr=0;
        if(!t.At(row,0x40,kind) || !t.At(row,0x4C,available) ||
           (kind!=0 && kind!=1) || !t.At(row,0,ptr)) return false;
        if(available) { if(ptr!=expected) return false; available_match=true; }
      }
      // A missing local row is unsafe: 3AC38E0 directly indexes the initial
      // local result. Parent absence can be skipped exactly as 3AC3F10 does.
      if(depth==1 && found!=1) return false;
      if(available_match) return true;
    }
    std::uintptr_t next=0;
    if(context && !t.At(context,0x108,next)) return false;
    if(!next && !t.At(current,0xE8,next)) return false;
    current=next;
  }
  return false;
}
struct Statement {
  VectorHead nodes{}, getters{}, literals{}, types{}, indices{};
  std::uint32_t parameter=0, kind=0, datatype=0;
  std::uintptr_t function=0, capture=0; std::uint8_t mode=0;
};
bool ReadStatement(Trace &t, std::uintptr_t p, Statement &s) {
  return Head(t,p,s.nodes) && Head(t,p+0x18,s.getters) &&
      Head(t,p+0x80,s.literals) && Head(t,p+0x98,s.types) &&
      Head(t,p+0xB0,s.indices) && t.At(p,0x30,s.parameter) &&
      t.At(p,0x34,s.kind) && t.At(p,0x38,s.function) &&
      t.At(p,0x40,s.capture) && t.At(p,0x48,s.datatype) &&
      t.At(p,0x4C,s.mode) && s.getters.count==0 && !s.capture && s.mode<=1 &&
      (s.kind==4 || s.kind==3) &&
      s.indices.count==s.nodes.count+1;
}
bool InputIndex(Trace &t, const Statement &s, std::size_t n,
                 std::uint32_t expected_type) {
  std::int32_t index=-1; std::uint32_t type=0;
  return n<static_cast<std::size_t>(s.indices.count) &&
      t.At(s.indices.data,n*4,index) && index>=0 && index<s.types.count &&
      t.At(s.types.data,index*8,type) && type==expected_type;
}
bool RequiredTypes(Trace &t, const Statement &s, std::uint32_t lobby,
                   std::optional<std::uint32_t> character) {
  if(s.types.count!=(character ? 2 : 1) || (character && *character==lobby)) return false;
  std::size_t lobby_rows=0,character_rows=0;
  for(std::int32_t i=0;i<s.types.count;++i) {
    std::array<std::uint32_t,2> row{};
    if(!t.At(s.types.data,i*8,row)) return false;
    if(row[0]==lobby) ++lobby_rows;
    else if(character && row[0]==*character) ++character_rows;
    else return false; // every required input is visited by the native resolver
  }
  return lobby_rows==1 && character_rows==(character ? 1U : 0U);
}
bool LiteralFindTitle(Trace &t, std::uintptr_t base, const Statement &s) {
  std::uintptr_t descriptor=0, dtype_vt=0; std::uint64_t size=0, capacity=0;
  std::uint32_t output=0; std::array<char,11> bytes{};
  // Exact stock literal fits CString's 15-byte inline storage. Heap strings
  // are intentionally unsupported in this first candidate, never guessed.
  return s.literals.count==1 && s.nodes.count==0 && s.types.count==0 &&
      s.datatype==0xFFFFFFFFU && s.indices.count==1 &&
      t.At(s.indices.data,0,output) && output==0xFFFFFFFFU &&
      t.At(s.literals.data,0,descriptor) && descriptor==base+0x542FD20 &&
      t.At(descriptor,0,dtype_vt) && dtype_vt==base+0x448BF80 &&
      t.At(s.literals.data,0x18,size) && size==10 &&
      t.At(s.literals.data,0x20,capacity) && capacity==15 &&
      t.At(s.literals.data,0x28,output) && output==s.parameter &&
      t.Read(s.literals.data+8,bytes.data(),bytes.size()) &&
      std::memcmp(bytes.data(),"find_title\0",11)==0;
}
bool CharacterArgument(Trace &t, std::uintptr_t base, std::uintptr_t widget,
    const Statement &s, const ControlCallbackOwnedSourceDraftV1 &source) {
  if(s.nodes.count!=1 || s.literals.count!=0 || s.types.count!=2 ||
     !source.selected_character ||
      !source.selected_character_vtable ||
     !source.selected_character_type_admitted) return false;
  VectorHead getters{}; std::uint32_t parameter=0, kind=0, type=0, output=0, id=0;
  std::uintptr_t function=0, capture=0, vt=0, iface_vt=0, slot1=0, slot2=0;
  std::uint8_t mode=0; const auto n=s.nodes.data;
  const auto character=*source.selected_character;
  return Head(t,n,getters) && getters.count==0 && t.At(n,0x18,parameter) &&
      parameter==0 && t.At(n,0x1C,kind) && kind==2 &&
      t.At(n,0x20,function) && function==base+0xC87DA0 &&
      t.At(n,0x28,capture) && !capture && t.At(n,0x30,type) &&
       type!=0xFFFFFFFFU && t.At(n,0x34,mode) &&
      mode==0 && t.At(n,0x38,output) && output==s.parameter &&
       InputIndex(t,s,0,type) && Bound(t,widget,type,character) &&
       t.At(character,0,vt) && vt==*source.selected_character_vtable && Module(base,vt,8) &&
       t.At(character,8,iface_vt) && iface_vt==base+0x4763C50 && Module(base,iface_vt,24) &&
      t.At(iface_vt,8,slot1) && slot1==base+0x9D09E0 &&
      t.At(iface_vt,16,slot2) && slot2==base+0x2802410 &&
      t.At(character,0x18,id) && id==source.selected_id;
}
// Activate(3ABC4D0) creates event type 0x1D then Deliver(3AA5A20) runs
// guiContext+0x260 and target+0x130 prehandlers before target slot13. Even a
// handler returning false could mutate the event. Support only absent handlers.
bool NoPrehandlers(Trace &t, std::uintptr_t widget) {
  std::uintptr_t context=0, manager=0, manager_context=0;
  std::uint8_t flags=0;
  if(!t.At(widget,0xD8,context) ||
     context!=reinterpret_cast<std::uintptr_t>(t.gui_context) ||
     !t.At(context,0x3E0,manager) || !manager ||
     !t.At(manager,0,manager_context) || manager_context!=context ||
     !t.At(widget,0xD0,flags) || (flags&0x0B)!=0) return false;
  for(const auto p: {context+0x260,widget+0x130}) {
    VectorHead before{},after{};
    if(!Head(t,p,before) || before.count!=0 || !Head(t,p,after) ||
       before.data!=after.data || before.capacity!=after.capacity ||
       before.count!=after.count) return false;
  }
  return true;
}
bool Semantic(Trace &t, std::uintptr_t base, std::uintptr_t widget,
               const ControlCallbackOwnedSourceDraftV1 &source) {
  std::uintptr_t vt=0, slot10=0, slot13=0; std::uint32_t lobby_type=0;
  if(!t.At(widget,0,vt) || !t.At(vt,10*8,slot10) || slot10!=base+0x3AA16D0 ||
     !t.At(vt,13*8,slot13) || slot13!=base+0x3AA0D40 ||
      !t.At(base+0x5D20C30,0,lobby_type) || lobby_type==0xFFFFFFFFU ||
      !NoPrehandlers(t,widget)) return false;
  for(std::size_t i=0;i<4;++i) {
    VectorHead primary{}; std::uint64_t cursor=0;
    if(!Head(t,widget+0x3F8+i*0x20,primary) || primary.count!=0 ||
       !t.At(widget+0x3F8+i*0x20,0x18,cursor) || cursor!=0) return false;
  }
  VectorHead actions{}; std::uint64_t cursor=0;
  if(!Head(t,widget+0x338,actions) || actions.count!=3 ||
     !t.At(widget+0x338,0x18,cursor) || cursor!=0) return false;
  constexpr std::array<std::uintptr_t,3> terminal{0xA98FB0,0x2164260,0x21646B0};
  for(std::size_t i=0;i<3;++i) {
    std::uintptr_t cb=0, cbvt=0, freefn=0, captured=0; Statement s{};
    if(!t.At(actions.data+i*0x48,0x40,cb) || !cb || !t.At(cb,0,cbvt) ||
       cbvt!=base+0x4965D48 || !t.At(cb,8,freefn) || freefn!=base+0x3A9F980 ||
       !t.At(cb,0xF0,captured) || captured!=widget || !ReadStatement(t,cb+0x10,s) ||
       s.function!=base+terminal[i]) return false;
    if(i==0) { if(!LiteralFindTitle(t,base,s)) return false; }
     else {
       std::optional<std::uint32_t> observed_argument_key;
       if(i==1) {
         std::uint32_t key=0;
         if(s.nodes.count!=1 || !t.At(s.nodes.data,0x30,key) || key==0xFFFFFFFFU) return false;
         observed_argument_key=key;
       }
       if((s.kind==3 && s.mode!=0) || s.datatype!=lobby_type ||
          !RequiredTypes(t,s,lobby_type,observed_argument_key) ||
          !InputIndex(t,s,s.nodes.count,lobby_type) ||
         !Bound(t,widget,lobby_type,source.actual_lobby)) return false;
      if(i==1) { if(!CharacterArgument(t,base,widget,s,source)) return false; }
      else if(s.nodes.count!=0 || s.literals.count!=0 || s.types.count!=1) return false;
    }
  }
  return true;
}
// This source qualification is a raw inspection only. The shared generic
// admission helper can call StrictDesc for a visible modal; its transitive TLS
// initialization closure has not been admitted here. Reject any modal receiver
// and reproduce the fixed address/manager/context/flags/callback checks without
// calling it, so a modal change cannot accidentally enter that native function.
bool NoCallDispatchAdmission(Trace &t,
    const ZhongguoScoreboardActionDispatchEnvironmentV1 &d,
    std::uintptr_t widget,std::uintptr_t expected_vt) {
  const auto base=d.module_base;const auto context=reinterpret_cast<std::uintptr_t>(t.gui_context);
  VectorHead modals{};std::uintptr_t manager=0,manager_context=0,target_context=0,vt=0;
  std::uint8_t flags=0;
  return base!=0 && d.exact_build_admitted && !d.offline_fixture_function_overrides &&
      d.gui_abi_revision==GuiAbiRevisionV1::crozier12003 &&
      reinterpret_cast<std::uintptr_t>(d.gui_global_slot)==base+GuiGlobalSlotRvaV1(d.gui_abi_revision) &&
      reinterpret_cast<std::uintptr_t>(d.activate_shortcut)==base+GuiShortcutManagerActivateRvaV1(d.gui_abi_revision) &&
      reinterpret_cast<std::uintptr_t>(d.is_strict_descendant)==base+GuiStrictDescendantRvaV1(d.gui_abi_revision) &&
      reinterpret_cast<std::uintptr_t>(d.button_base_slot13)==base+GuiButtonBaseSlot13RvaV1(d.gui_abi_revision) &&
      context!=0 && Head(t,context+kZhongguoGuiModalVectorOffset,modals,0) && modals.count==0 &&
      t.At(context,kZhongguoGuiShortcutManagerOffset,manager) && manager!=0 &&
      t.At(manager,0,manager_context) && manager_context==context &&
      t.At(widget,kZhongguoWidgetGuiContextOffset,target_context) && target_context==context &&
      t.At(widget,kZhongguoWidgetHiddenFlagsOffset,flags) &&
      (flags&kZhongguoWidgetShortcutRejectedMask)==0 &&
      t.At(widget,0,vt) && vt==expected_vt;
}
bool Pass(const ZhongguoScoreboardNativeEnvironmentV1 &env,
          const ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch,
          const ControlCallbackOwnedSourceDraftV1 &source, Trace &trace,
          ControlCallbackQueryDraftV1 &out) {
  ZhongguoScoreboardAccessV1 access{}; NamedGuiTreeInspectionV1 global{}, tree{};
  void *root=nullptr,*self=nullptr;
  if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,trace.gui_context,
                                                        trace.gui_owner) ||
     !Source(trace,env.module_base,source) || !InspectNamedGuiTreeV1(env,access,global) ||
     !global.root_available || global.truncated || global.widget_count!=global.widgets.size())
    return false;
  std::size_t roots=0;
  for(const auto &r:global.widgets) if(r.runtime_name==kRoot) ++roots;
  if(roots!=1 || !ResolveNamedGuiWidgetV1(env,access,kRoot,kRoot,root,self) ||
     !root || root!=self || !InspectNamedGuiSubtreeV1(access,env.module_base,root,kRoot,tree) ||
     !tree.root_available || tree.truncated || tree.widget_count!=tree.widgets.size()) return false;
  trace.global_tree=global; trace.local_tree=tree;
  std::string name; void *rootvt=nullptr; bool visible=false,enabled=false;
  if(!ReadGuiWidgetRuntimeV1(access,root,name,rootvt,visible,enabled) || name!=kRoot || !visible ||
     !Module(env.module_base,reinterpret_cast<std::uintptr_t>(rootvt),8))
    return false;
  out.root_exists=true; out.root_unique=true; out.root_visible=visible;
  out.root_vtable_rva=reinterpret_cast<std::uintptr_t>(rootvt)-env.module_base;
  std::size_t matches=0; std::uintptr_t candidate=0,candidatevt=0;
  for(const auto &r:tree.widgets) {
    std::vector<std::uint32_t> path;
    if(!ParseActualPath(r.child_path,path)) return false;
    void *resolved_root=nullptr,*widget=nullptr;
    if(!ResolveFixedGuiChildPathV1(env,access,kRoot,path.data(),path.size(),resolved_root,widget) ||
       resolved_root!=root || !widget) return false;
    void *vtptr=nullptr; bool v=false,e=false; std::string actual_name;
    if(!ReadGuiWidgetRuntimeV1(access,widget,actual_name,vtptr,v,e) ||
       actual_name!=r.runtime_name || v!=r.effective_visible || e!=r.enabled ||
       reinterpret_cast<std::uintptr_t>(vtptr)-env.module_base!=r.vtable_rva) return false;
    bool button=false;
    if(!ButtonClass(trace,env.module_base,reinterpret_cast<std::uintptr_t>(vtptr),button)) return false;
    if(!button) continue;
    const auto p=reinterpret_cast<std::uintptr_t>(widget);
    // Only observed arity or a fully read native statement's different terminal
    // can definitively exclude a button. Unreadable/custom captures stay unknown.
    VectorHead actions{};
    if(!Head(trace,p+0x338,actions)) return false;
    if(actions.count!=3) continue;
    std::uintptr_t cb=0, cbvt=0, freefn=0, captured=0, first_terminal=0;
    if(!trace.At(actions.data,0x40,cb) || !cb || !trace.At(cb,0,cbvt) ||
       cbvt!=env.module_base+0x4965D48 || !trace.At(cb,8,freefn) ||
       freefn!=env.module_base+0x3A9F980 || !trace.At(cb,0xF0,captured) ||
       captured!=p || !trace.At(cb+0x10,0x38,first_terminal)) return false;
    if(first_terminal!=env.module_base+0xA98FB0) continue;
    if(!Semantic(trace,env.module_base,p,source)) return false;
    ++matches; candidate=p; candidatevt=reinterpret_cast<std::uintptr_t>(vtptr);
    if(!v || !e) return false;
  }
  void *context_after=nullptr,*owner_after=nullptr;
  if(matches!=1 || !Source(trace,env.module_base,source) ||
     !ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,context_after,owner_after) ||
     context_after!=trace.gui_context || owner_after!=trace.gui_owner ||
     !NoCallDispatchAdmission(trace,dispatch,candidate,candidatevt)) return false;
  out.read_complete=true; out.target_exists=true; out.target_visible=true;
  out.target_enabled=true; out.unique_target=true; out.semantic_qualified=true;
  out.dispatch_admitted=true; out.target=candidate;
  out.target_vtable_rva=candidatevt-env.module_base;
  out.reason="control_callback_fixed_source_qualified";
  return true;
}
} // namespace control_callback_draft
#endif

bool ReadControlCallbackSourceDraftV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &env,
    const ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch,
    const ControlCallbackOwnedSourceDraftV1 &source,
    ControlCallbackQueryDraftV1 &out) noexcept {
  out={};
#if !XAR_CK3_ENABLE_CONTROL_CALLBACK_SOURCE_PRIVATE_V1
  (void)env; (void)dispatch; (void)source; return false;
#else
  try {
    if(!source.selected_character || !source.selected_character_vtable ||
        !source.selected_character_type_admitted) {
      out.reason="control_callback_selected_character_pointer_or_independent_type_source_unavailable";
      return false;
    }
    if(!env.exact_build_admitted || env.offline_fixture_function_overrides || !env.module_base ||
        env.gui_abi_revision!=GuiAbiRevisionV1::crozier12003 ||
        dispatch.module_base!=env.module_base || !dispatch.exact_build_admitted ||
        dispatch.offline_fixture_function_overrides ||
        dispatch.gui_abi_revision!=GuiAbiRevisionV1::crozier12003 ||
       !source.exact_004_pinset_admitted || !source.stock_gui_source_admitted ||
        !source.source_inventory_complete || !source.selected_character_type_admitted ||
        !source.selected_character || !source.selected_character_vtable) {
      out.reason="control_callback_owned_source_or_pins_unavailable"; return false;
    }
    control_callback_draft::Trace a{},b{}; ControlCallbackQueryDraftV1 x{},y{};
    if(!control_callback_draft::Pass(env,dispatch,source,a,x) ||
       !control_callback_draft::Pass(env,dispatch,source,b,y) ||
       !control_callback_draft::Same(a,b) || x.target!=y.target ||
       x.root_vtable_rva!=y.root_vtable_rva || x.target_vtable_rva!=y.target_vtable_rva) {
      out.reason="control_callback_full_census_or_source_chain_unavailable_or_changed";
      return false;
    }
    out=std::move(y); return true;
  } catch(...) { out={}; out.reason="control_callback_read_exception"; return false; }
#endif
}
} // namespace xar::ck3_11906

namespace xar::ck3_12003 {
bool ReadPlayerControlControlGuiSourceV1(
    const PlayerControlIdentitySourceContextV1 &ctx,
    const ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &env,
    const ck3_11906::ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch,
    const PlayerControlObservationV1 &proofs,PlayerControlTargetV1 &target,
    std::optional<std::uintptr_t> &internal_widget,std::string &reason) noexcept {
  target={};internal_widget.reset();reason="player_control_control_source_private_default_off";
  if(!kPlayerControlV1CompiledEnabled) return false;
  try {
    if(!ctx.request || !PlayerControlSourceProofV1(proofs) ||
        proofs.native_revision!=ctx.native_revision || proofs.connection_generation!=ctx.connection_generation ||
        proofs.game_pid!=ctx.request->expected_game_pid || proofs.played_character_id!=ctx.request->expected_player_character_id ||
        proofs.process_creation_filetime_100ns!=ctx.request->expected_process_creation_filetime_100ns ||
        proofs.pump_epoch!=stamp.pump_epoch) {
      reason="player_control_actual_owner_source_proofs_unavailable";return false;
    }
    PlayerControlObservationV1 first{};PlayerControlOwnedIdentityBindingV1 owned{};
    if(!ReadPlayerControlOwnedIdentitySourceV1(ctx,mailbox,stamp,env,first,owned) ||
        !owned.source_complete || owned.mailbox_sequence!=ctx.ticket.sequence ||
        owned.pump_epoch!=stamp.pump_epoch || owned.owner_thread_id!=stamp.thread_id ||
        owned.date_raw!=stamp.date_raw || !owned.selected_character_id ||
        !owned.selected_character || !owned.selected_character_vtable ||
        owned.selected_character_alive!=true || owned.selected_character_is_ruler!=true ||
        !ControlCallbackPins(env.module_base)) {
      reason="player_control_actual_selected_owner_source_or_callback_pins_unavailable";return false;
    }
    ck3_11906::ControlCallbackOwnedSourceDraftV1 source{};
    source.exact_004_pinset_admitted=true;
    source.stock_gui_source_admitted=proofs.stock_files_verified;
    source.source_inventory_complete=proofs.loaded_source_binding_verified;
    source.selected_character_type_admitted=true;
    source.handler=owned.handler;source.actual_lobby=owned.lobby;
    source.selected_supplier=owned.playable_supplier;
    source.selected_id=static_cast<std::uint32_t>(*owned.selected_character_id);
    source.selected_character=owned.selected_character;
    source.selected_character_vtable=owned.selected_character_vtable;
    ck3_11906::ControlCallbackQueryDraftV1 actual{};
    if(!ck3_11906::ReadControlCallbackSourceDraftV1(env,dispatch,source,actual)) {
      reason=actual.reason;return false;
    }
    PlayerControlObservationV1 after{};PlayerControlOwnedIdentityBindingV1 rebound{};
    if(!ReadPlayerControlOwnedIdentitySourceV1(ctx,mailbox,stamp,env,after,rebound) ||
        rebound!=owned || !actual.read_complete.value_or(false) ||
        !actual.semantic_qualified.value_or(false) || !actual.target || !actual.target_vtable_rva) {
      reason="player_control_actual_control_source_rebound_or_census_changed";return false;
    }
    target.read_complete=true;target.root_exists=actual.root_exists.value_or(false);
    target.root_visible=actual.root_visible.value_or(false);target.target_exists=actual.target_exists.value_or(false);
    target.target_visible=actual.target_visible.value_or(false);target.target_enabled=actual.target_enabled.value_or(false);
    target.unique_target=actual.unique_target.value_or(false);target.dispatch_admitted=actual.dispatch_admitted.value_or(false);
    target.target_vtable_rva=*actual.target_vtable_rva;internal_widget=actual.target;reason=actual.reason;
    return true;
  } catch(...) {target={};internal_widget.reset();reason="player_control_control_source_exception";return false;}
}
} // namespace xar::ck3_12003

// Fixed source-only inventory and current loaded-DLL binding for a typed partial
// read-only provider. None of these checks qualifies stock GUI mutations.
#if defined(XAR_CK3_ENABLE_PLAYER_CONTROL_PRIVATE_V1)
#include "xar_bridge/normal_exit_map_source_v1.hpp"
#include <shellapi.h>
#include <filesystem>
#include <fstream>
#include <map>
#include <set>

namespace xar::ck3_12003 {
namespace player_control_inventory {
// Parser/path/descriptor helpers are copied from the exact current reviewed
// normal-exit source. They are private here and tightened for the closed V1.
namespace fs = std::filesystem;
struct Node {
  enum Kind { object, array, string, number, boolean, null_value } kind = null_value;
  std::map<std::string, Node> fields;
  std::vector<Node> items;
  std::string text;
  std::uint64_t integer = 0;
};
class InventoryParser {
 public:
  explicit InventoryParser(std::string_view source) : source_(source) {}
  bool Parse(Node &node) {
    if (source_.empty() || source_.size() > 16U * 1024U * 1024U) return false;
    return Value(node, 0) && (Space(), at_ == source_.size());
  }
 private:
  std::string_view source_; std::size_t at_ = 0, nodes_ = 0;
  void Space() { while (at_ < source_.size() && (source_[at_]==' ' || source_[at_]=='\t' || source_[at_]=='\r' || source_[at_]=='\n')) ++at_; }
  bool Quote(std::string &value) {
    Space(); if (at_ >= source_.size() || source_[at_++]!='"') return false;
    value.clear();
    while (at_<source_.size()) {
      const auto c=static_cast<unsigned char>(source_[at_++]);
      if(c=='"') return true;
      if(c<0x20 || value.size()>=32768) return false;
      if(c=='\\') {
        if(at_>=source_.size()) return false;
        const char escaped=source_[at_++];
        if(escaped!='"' && escaped!='\\' && escaped!='/') return false;
        value+=escaped;
      } else value+=static_cast<char>(c);
    }
    return false;
  }
  bool Value(Node &node, std::size_t depth) {
    Space(); if(depth>12 || ++nodes_>250000 || at_>=source_.size()) return false;
    const char first=source_[at_];
    if(first=='"') { node.kind=Node::string; return Quote(node.text); }
    if(first=='{' || first=='[') {
      const char end=first=='{'?'}':']'; node.kind=first=='{'?Node::object:Node::array; ++at_; Space();
      if(at_<source_.size() && source_[at_]==end) { ++at_; return true; }
      while(at_<source_.size()) {
        std::string key;
        if(first=='{') {
          if(!Quote(key) || key.empty() || node.fields.contains(key)) return false;
          Space(); if(at_>=source_.size() || source_[at_++]!=':') return false;
        }
        Node item; if(!Value(item,depth+1)) return false;
        if(first=='{') node.fields.emplace(std::move(key),std::move(item)); else node.items.push_back(std::move(item));
        Space(); if(at_>=source_.size()) return false;
        if(source_[at_]==end) { ++at_; return true; }
        if(source_[at_++]!=',') return false;
      }
      return false;
    }
    if(source_.substr(at_,4)=="true" || source_.substr(at_,5)=="false") {
      node.kind=Node::boolean; at_+=source_[at_]=='t'?4:5; return true;
    }
    if(source_.substr(at_,4)=="null") { node.kind=Node::null_value; at_+=4; return true; }
    const auto start=at_;
    while(at_<source_.size() && source_[at_]>='0' && source_[at_]<='9') ++at_;
    if(at_==start || (at_-start>1 && source_[start]=='0')) return false;
    node.kind=Node::number;
    const auto result=std::from_chars(source_.data()+start,source_.data()+at_,node.integer);
    return result.ec==std::errc{} && result.ptr==source_.data()+at_;
  }
};
const Node *Field(const Node &node, const char *name, Node::Kind kind) {
  if(node.kind!=Node::object) return nullptr;
  const auto found=node.fields.find(name);
  return found!=node.fields.end() && found->second.kind==kind?&found->second:nullptr;
}
bool Hex(std::string_view value) noexcept {
  if(value.size()!=64) return false;
  for(char c:value) if(!((c>='0'&&c<='9')||(c>='a'&&c<='f'))) return false;
  return true;
}
std::wstring Wide(std::string_view text) {
  if(text.empty() || text.find('\0')!=std::string_view::npos || text.size()>32767) return {};
  const int size=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(text.size()),nullptr,0);
  if(size<=0) return {};
  std::wstring output(static_cast<std::size_t>(size),L'\0');
  return MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(text.size()),output.data(),size)==size?output:std::wstring{};
}
fs::path Path(const Node &node) { return fs::path(Wide(node.text)); }
bool SamePath(const fs::path &first, const fs::path &second) {
  if(first.empty() || second.empty() || !first.is_absolute() || !second.is_absolute()) return false;
  const auto a=fs::weakly_canonical(first).native(), b=fs::weakly_canonical(second).native();
  return CompareStringOrdinal(a.c_str(),static_cast<int>(a.size()),b.c_str(),static_cast<int>(b.size()),TRUE)==CSTR_EQUAL;
}
bool Plain(const fs::path &path) {
  const DWORD attributes=GetFileAttributesW(path.c_str());
  return attributes!=INVALID_FILE_ATTRIBUTES && (attributes&FILE_ATTRIBUTE_REPARSE_POINT)==0;
}
bool ReadFile(const fs::path &path, std::string &bytes, std::size_t bound) {
  bytes.clear(); if(!Plain(path) || !fs::is_regular_file(path)) return false;
  const auto size=fs::file_size(path); if(size>bound) return false;
  std::ifstream input(path,std::ios::binary); if(!input) return false;
  bytes.resize(static_cast<std::size_t>(size));
  input.read(bytes.data(),static_cast<std::streamsize>(bytes.size()));
  return static_cast<bool>(input);
}
bool FileRecord(const Node &node, const fs::path &expected, std::string *content=nullptr) {
  const auto *path=Field(node,"path",Node::string), *size=Field(node,"bytes",Node::number), *hash=Field(node,"sha256",Node::string);
  if(!path || !size || !hash || !Hex(hash->text) || !SamePath(Path(*path),expected)) return false;
  std::string bytes, actual;
  if(!ReadFile(expected,bytes,128U*1024U*1024U) || bytes.size()!=size->integer ||
      !NormalExitMapSha256V1(bytes,actual) || actual!=hash->text) return false;
  if(content) *content=std::move(bytes);
  return true;
}
bool Relative(std::string_view text, fs::path &path) {
  path=fs::path(Wide(text));
  if(path.empty() || path.is_absolute() || path.has_root_name() || path.has_root_directory()) return false;
  for(const auto &part:path) if(part==L".." || part==L".") return false;
  return path==path.lexically_normal();
}
std::wstring Lower(std::wstring value) {
  for(auto &c:value) if(c>=L'A' && c<=L'Z') c=static_cast<wchar_t>(c-L'A'+L'a');
  return value;
}
bool Descriptor(std::string_view bytes, const fs::path &root, bool outer) {
  // Limited first-pilot policy: no archive mount or GUI-affecting replace_path.
  // This lexical pass skips quoted values and comments before recognizing keys.
  std::size_t at=0, paths=0;
  while(at<bytes.size()) {
    if(bytes[at]=='#') { const auto end=bytes.find('\n',at); at=end==std::string_view::npos?bytes.size():end; continue; }
    if(bytes[at]=='"') { ++at; while(at<bytes.size() && bytes[at]!='"') ++at; if(at==bytes.size()) return false; ++at; continue; }
    if(!((bytes[at]>='a'&&bytes[at]<='z') || bytes[at]=='_')) { ++at; continue; }
    const auto start=at; while(at<bytes.size() && ((bytes[at]>='a'&&bytes[at]<='z') || bytes[at]=='_')) ++at;
    const auto key=bytes.substr(start,at-start);
    if(key!="path" && key!="replace_path" && key!="archive") continue;
    if(key=="archive" || key=="replace_path") return false;
    while(at<bytes.size() && (bytes[at]==' '||bytes[at]=='\t'||bytes[at]=='\r'||bytes[at]=='\n')) ++at;
    if(at==bytes.size() || bytes[at++]!='=') return false;
    while(at<bytes.size() && (bytes[at]==' '||bytes[at]=='\t')) ++at;
    if(at==bytes.size() || bytes[at++]!='"') return false;
    const auto value_start=at; while(at<bytes.size() && bytes[at]!='"' && bytes[at]!='\r' && bytes[at]!='\n') ++at;
    if(at==bytes.size() || bytes[at]!='"') return false;
    const auto value=bytes.substr(value_start,at-value_start); ++at;
    if(key=="path") {
      if(++paths>1 || !SamePath(fs::path(Wide(value)),root)) return false;
    } else {
      auto normalized=Lower(fs::path(Wide(value)).generic_wstring());
      while(!normalized.empty() && normalized.back()==L'/') normalized.pop_back();
      if(normalized.empty() || normalized==L"." || normalized==L"gui" || normalized.starts_with(L"gui/") ||
          normalized.starts_with(L"../") || normalized.find(L"/gui")!=std::wstring::npos) return false;
    }
  }
  return outer ? paths==1 : paths==0;
}
struct StockFile { const char *path; std::size_t bytes; const char *sha; };
constexpr std::array<StockFile,8> kStock{{
  {"gui/hud.gui",227658,"77d0beedefe23eee22b24c1c0b160ae5ee8ec938868d3f4b7ae76296347a6ac6"},
  {"gui/frontend_ingame_menu.gui",10812,"8498536c7d565bff610f592d45c79cbb2b0fa47ff184dafe3b324b355e0b0dfb"},
  {"gui/window_resign_confirmation.gui",3051,"9b8ca6d2cc17ecb575c21f5a683719d4ce6472958e3bf311e2419db09c34d1c9"},
  {"gui/shared/buttons_icons.gui",19034,"f5d8e398a396b75f588a3abd9cb07b51639d7201c71fe7a68ec869b40ce215e6"},
  {"gui/shared/buttons.gui",41901,"88403785a1acdacc628730aaa101a04b2ae6293e74aa706a93e0e1695f3b1a0c"},
  {"gui/shared/sounds.gui",10725,"88352f5f6ec36d9fbd703fc05f510d7ce26f6250531e152eb5f9d9131404b0fc"},
  {"gui/multiplayer_types.gui",56911,"93912d008d2362955470e7f42029280c41e3e316e28d8d1055ee09dfbe8bc3a3"},
  {"gui/multiplayer_lobby.gui",31165,"55704cf6aec8deaf01a0077aa19731ff7f1047f9491aa524b978ded7fc3f156f"},
}};
#include "player_control_compiled_sources_v1.inc"


bool Closed(const Node &n,std::initializer_list<const char *> fields) {
  if(n.kind!=Node::object || n.fields.size()!=fields.size()) return false;
  for(const auto *key:fields) if(!n.fields.contains(key)) return false;
  return true;
}
bool PlainChain(const fs::path &p) {
  if(p.empty() || !p.is_absolute()) return false;
  for(auto current=p;;current=current.parent_path()) {
    if(!Plain(current)) return false;
    if(current==current.parent_path()) break;
  }
  return true;
}
bool FixedFile(const Node &n,const fs::path &p) {
  return Closed(n,{"path","bytes","sha256"}) && PlainChain(p) && FileRecord(n,p);
}
bool NativeRelative(std::string_view text,fs::path &path) {
  return text.find('\\')==std::string_view::npos && Relative(text,path) &&
      path.generic_string()==text;
}
bool ReadDiskRva(const std::string &disk,const IMAGE_NT_HEADERS64 &nt,
    const std::vector<IMAGE_SECTION_HEADER> &sections,std::uint32_t rva,
    void *out,std::size_t size) {
  if(!out || size==0 || rva>=nt.OptionalHeader.SizeOfImage ||
      size>nt.OptionalHeader.SizeOfImage-rva) return false;
  std::size_t offset=0;
  if(rva<nt.OptionalHeader.SizeOfHeaders) offset=rva;
  else {
    bool found=false;
    for(const auto &s:sections) if(rva>=s.VirtualAddress &&
        rva-s.VirtualAddress<s.SizeOfRawData &&
        size<=s.SizeOfRawData-(rva-s.VirtualAddress)) {
      offset=s.PointerToRawData+(rva-s.VirtualAddress);found=true;break;
    }
    if(!found) return false;
  }
  if(offset>disk.size() || size>disk.size()-offset) return false;
  std::memcpy(out,disk.data()+offset,size);return true;
}
bool LoadedSourceModule(std::string &reason) {
  const auto reject=[&](const char *why) { reason=why;return false; };
  HMODULE module=nullptr;
  if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|
      GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
      reinterpret_cast<LPCWSTR>(&LoadedSourceModule),&module) || !module)
    return reject("player_control_loaded_reader_module_unavailable");
  std::array<wchar_t,32768> path{};
  const auto n=GetModuleFileNameW(module,path.data(),static_cast<DWORD>(path.size()));
  if(n==0 || n>=path.size() || !PlainChain(fs::path(path.data())))
    return reject("player_control_loaded_dll_plain_path_unavailable");
  std::string disk;
  if(!ReadFile(fs::path(path.data()),disk,256U*1024U*1024U) ||
      disk.size()<sizeof(IMAGE_DOS_HEADER)) return reject("player_control_loaded_dll_disk_unreadable");
  IMAGE_DOS_HEADER dos{};std::memcpy(&dos,disk.data(),sizeof(dos));
  if(dos.e_magic!=IMAGE_DOS_SIGNATURE || dos.e_lfanew<0 ||
      static_cast<std::size_t>(dos.e_lfanew)>disk.size() ||
      sizeof(IMAGE_NT_HEADERS64)>disk.size()-static_cast<std::size_t>(dos.e_lfanew))
    return reject("player_control_loaded_dll_disk_dos_invalid");
  IMAGE_NT_HEADERS64 nt{};
  std::memcpy(&nt,disk.data()+dos.e_lfanew,sizeof(nt));
  if(nt.Signature!=IMAGE_NT_SIGNATURE || nt.FileHeader.Machine!=IMAGE_FILE_MACHINE_AMD64 ||
      nt.FileHeader.SizeOfOptionalHeader!=sizeof(IMAGE_OPTIONAL_HEADER64) ||
      nt.OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR64_MAGIC ||
      nt.FileHeader.NumberOfSections==0 || nt.FileHeader.NumberOfSections>96 ||
      nt.OptionalHeader.SizeOfImage==0 || nt.OptionalHeader.SizeOfImage>256U*1024U*1024U ||
      nt.OptionalHeader.NumberOfRvaAndSizes<=IMAGE_DIRECTORY_ENTRY_BASERELOC)
    return reject("player_control_loaded_dll_disk_pe_invalid");
  const auto base=reinterpret_cast<std::uintptr_t>(module);
  if(base>(std::numeric_limits<std::uintptr_t>::max)()-nt.OptionalHeader.SizeOfImage)
    return reject("player_control_loaded_dll_image_overflow");
  IMAGE_DOS_HEADER loaded_dos{};IMAGE_NT_HEADERS64 loaded_nt{};
  if(!Read(base,loaded_dos) || loaded_dos.e_magic!=dos.e_magic ||
      loaded_dos.e_lfanew!=dos.e_lfanew ||
      !Read(base+static_cast<std::uintptr_t>(dos.e_lfanew),loaded_nt) ||
      std::memcmp(&loaded_nt,&nt,sizeof(nt))!=0)
    return reject("player_control_loaded_dll_headers_changed");
  const auto table=static_cast<std::size_t>(dos.e_lfanew)+sizeof(nt);
  const auto bytes=static_cast<std::size_t>(nt.FileHeader.NumberOfSections)*sizeof(IMAGE_SECTION_HEADER);
  if(table>disk.size() || bytes>disk.size()-table)
    return reject("player_control_loaded_dll_section_table_invalid");
  std::vector<IMAGE_SECTION_HEADER> sections(nt.FileHeader.NumberOfSections);
  std::memcpy(sections.data(),disk.data()+table,bytes);
  std::vector<std::uint32_t> relocs;
  const auto directory=nt.OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_BASERELOC];
  if(directory.Size>8U*1024U*1024U ||
      (directory.Size && (!directory.VirtualAddress || directory.VirtualAddress>=nt.OptionalHeader.SizeOfImage ||
       directory.Size>nt.OptionalHeader.SizeOfImage-directory.VirtualAddress)))
    return reject("player_control_loaded_dll_relocation_bound");
  std::uint32_t at=0;
  while(at<directory.Size) {
    IMAGE_BASE_RELOCATION block{};
    if(directory.VirtualAddress>(std::numeric_limits<std::uint32_t>::max)()-at ||
        !ReadDiskRva(disk,nt,sections,directory.VirtualAddress+at,&block,sizeof(block)) ||
        block.SizeOfBlock<sizeof(block) || block.SizeOfBlock>directory.Size-at ||
        (block.SizeOfBlock-sizeof(block))%sizeof(std::uint16_t))
      return reject("player_control_loaded_dll_relocation_block_invalid");
    const auto count=(block.SizeOfBlock-sizeof(block))/sizeof(std::uint16_t);
    for(std::size_t i=0;i<count;++i) {
      std::uint16_t row=0;
      const auto entry=directory.VirtualAddress+at+static_cast<std::uint32_t>(sizeof(block)+i*sizeof(row));
      if(!ReadDiskRva(disk,nt,sections,entry,&row,sizeof(row)))
        return reject("player_control_loaded_dll_relocation_entry_unreadable");
      if((row>>12)==IMAGE_REL_BASED_ABSOLUTE) continue;
      if((row>>12)!=IMAGE_REL_BASED_DIR64 ||
          block.VirtualAddress>(std::numeric_limits<std::uint32_t>::max)()-(row&0xFFFU))
        return reject("player_control_loaded_dll_relocation_type_unsupported");
      relocs.push_back(block.VirtualAddress+(row&0xFFFU));
      if(relocs.size()>1000000) return reject("player_control_loaded_dll_relocation_count_bound");
    }
    at+=block.SizeOfBlock;
  }
  std::sort(relocs.begin(),relocs.end());
  if(std::adjacent_find(relocs.begin(),relocs.end())!=relocs.end())
    return reject("player_control_loaded_dll_duplicate_relocation");
  const auto delta=static_cast<std::uint64_t>(base-nt.OptionalHeader.ImageBase);
  std::size_t executable_sections=0;
  for(const auto &s:sections) if((s.Characteristics&IMAGE_SCN_MEM_EXECUTE)!=0) {
    ++executable_sections;
    const auto length=std::max(s.Misc.VirtualSize,s.SizeOfRawData);
    if(length==0 || s.VirtualAddress>=nt.OptionalHeader.SizeOfImage ||
        length>nt.OptionalHeader.SizeOfImage-s.VirtualAddress ||
        s.PointerToRawData>disk.size() || s.SizeOfRawData>disk.size()-s.PointerToRawData ||
        (s.Characteristics&IMAGE_SCN_MEM_WRITE)!=0)
      return reject("player_control_loaded_dll_executable_section_invalid");
    std::string expected(length,'\0'),actual(length,'\0');
    std::memcpy(expected.data(),disk.data()+s.PointerToRawData,s.SizeOfRawData);
    SIZE_T received=0;
    if(!ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void *>(base+s.VirtualAddress),
        actual.data(),actual.size(),&received) || received!=actual.size())
      return reject("player_control_loaded_dll_code_unreadable");
    for(const auto rva:relocs) if(rva>=s.VirtualAddress && rva-s.VirtualAddress<length) {
      const auto offset=rva-s.VirtualAddress;std::uint64_t word=0;
      if(sizeof(word)>length-offset) return reject("player_control_loaded_dll_code_relocation_crosses_section");
      std::memcpy(&word,actual.data()+offset,sizeof(word));word-=delta;
      std::memcpy(actual.data()+offset,&word,sizeof(word));
    }
    if(actual!=expected) return reject("player_control_loaded_dll_actual_code_changed");
  }
  if(executable_sections==0) return reject("player_control_loaded_dll_code_missing");
  // Match the complete current immutable arrays, including their pointer and
  // byte-count slots. Checking only valid individual literals cannot detect a
  // replaced row pointing at another legitimate string already in the DLL.
  const auto immutable=[&](const void *p,std::size_t length) {
    const auto address=reinterpret_cast<std::uintptr_t>(p);MEMORY_BASIC_INFORMATION info{};
    if(!p || length==0 || length>1024U*1024U || address<base || address-base>=nt.OptionalHeader.SizeOfImage ||
        length>nt.OptionalHeader.SizeOfImage-(address-base) || VirtualQuery(p,&info,sizeof(info))!=sizeof(info) ||
        info.AllocationBase!=module || info.Type!=MEM_IMAGE || (info.Protect&0xFFU)!=PAGE_READONLY ||
        address<reinterpret_cast<std::uintptr_t>(info.BaseAddress) ||
        address-reinterpret_cast<std::uintptr_t>(info.BaseAddress)>info.RegionSize ||
        length>info.RegionSize-(address-reinterpret_cast<std::uintptr_t>(info.BaseAddress))) return false;
    std::string actual(length,'\0'),expected(length,'\0');SIZE_T received=0;
    const auto table_rva=static_cast<std::uint32_t>(address-base);
    if(!ReadProcessMemory(GetCurrentProcess(),p,actual.data(),length,&received) || received!=length ||
        !ReadDiskRva(disk,nt,sections,table_rva,expected.data(),length)) return false;
    for(const auto rva:relocs) if(rva>=table_rva && rva-table_rva<length) {
      const auto offset=rva-table_rva;std::uint64_t word=0;
      if(sizeof(word)>length-offset) return false;
      std::memcpy(&word,actual.data()+offset,sizeof(word));word-=delta;
      std::memcpy(actual.data()+offset,&word,sizeof(word));
    }
    return actual==expected;
  };
  if(!immutable(kImplementation.data(),sizeof(kImplementation)) ||
      !immutable(kStock.data(),sizeof(kStock)) ||
      !immutable(kIdentitySourcePins.data(),sizeof(kIdentitySourcePins)))
    return reject("player_control_loaded_dll_immutable_source_tables_changed");
  // Every compiled fixed name/digest originates from read-only current module
  // memory and equals its disk literal. The generated table is tied to the
  // exact build receipt; no expected DLL digest is circularly self-embedded.
  const auto literal=[&](const char *p,std::size_t limit) {
    const auto address=reinterpret_cast<std::uintptr_t>(p);
    MEMORY_BASIC_INFORMATION info{};
    if(!p || address<base || address-base>=nt.OptionalHeader.SizeOfImage ||
        VirtualQuery(p,&info,sizeof(info))!=sizeof(info) || info.AllocationBase!=module ||
        info.Type!=MEM_IMAGE || (info.Protect&0xFFU)!=PAGE_READONLY) return false;
    if(limit==0 || limit>256) return false;
    const auto readable=std::min(limit,static_cast<std::size_t>(nt.OptionalHeader.SizeOfImage-(address-base)));
    std::array<char,256> current{};SIZE_T received=0;
    if(!ReadProcessMemory(GetCurrentProcess(),p,current.data(),readable,&received) || received!=readable) return false;
    const auto end=std::find(current.begin(),current.begin()+readable,'\0');
    if(end==current.begin()+readable) return false;
    const auto length=static_cast<std::size_t>(end-current.begin())+1;
    std::string expected(length,'\0');
    return ReadDiskRva(disk,nt,sections,static_cast<std::uint32_t>(address-base),expected.data(),length) &&
        std::memcmp(current.data(),expected.data(),length)==0;
  };
  for(const auto &row:kImplementation) if(!literal(row.path,256) || !literal(row.sha,65))
    return reject("player_control_loaded_dll_compiled_source_literals_changed");
  std::string after;
  if(!ReadFile(fs::path(path.data()),after,256U*1024U*1024U) || after!=disk)
    return reject("player_control_loaded_dll_disk_changed_during_query");
  return true;
}
bool VerifySources(std::string_view expected_sha,std::string &reason) {
  const auto reject=[&](const char *why) { reason=why;return false; };
  if(!Hex(expected_sha)) return reject("player_control_source_inventory_reference_missing");
  // Attest current immutable rows before dereferencing any path/count from them.
  if(!LoadedSourceModule(reason)) return false;
  int argc=0;auto **argv=CommandLineToArgvW(GetCommandLineW(),&argc);
  if(!argv) return reject("player_control_actual_arguments_unreadable");
  NormalExitMapLaunchArgumentsV1 launch{};bool okay=false;
  if(argc>=2 && argc<=5) {
    std::array<std::wstring_view,5> arguments{};
    for(int i=0;i<argc;++i) arguments[static_cast<std::size_t>(i)]=argv[i];
    okay=ParseNormalExitMapLaunchArgumentsV1(
        std::span<const std::wstring_view>(arguments.data(),static_cast<std::size_t>(argc)),launch);
  }
  LocalFree(argv);
  if(!okay || !PlainChain(launch.userdir)) return reject("player_control_actual_userdir_contract_unavailable");
  const auto manifest=launch.userdir/L"player-control-source-inventory-v1.json";
  std::string bytes,digest;
  if(!ReadFile(manifest,bytes,16U*1024U*1024U) || !NormalExitMapSha256V1(bytes,digest) || digest!=expected_sha)
    return reject("player_control_fixed_inventory_actual_bytes_changed");
  Node inventory;
  if(!InventoryParser(bytes).Parse(inventory) || !Closed(inventory,{"schema","userdir","profile_binding_sha256",
      "settings_file","dlc_load","stock_game_root","source_executable","stock_gui","enabled_mods",
      "implementation_root","implementation_sources"})) return reject("player_control_closed_inventory_structure_invalid");
  const auto *schema=Field(inventory,"schema",Node::string),*userdir=Field(inventory,"userdir",Node::string);
  const auto *profile=Field(inventory,"profile_binding_sha256",Node::string);
  const auto *settings=Field(inventory,"settings_file",Node::object),*dlc=Field(inventory,"dlc_load",Node::object);
  const auto *mods=Field(inventory,"enabled_mods",Node::array),*stock=Field(inventory,"stock_gui",Node::array);
  const auto *game_root=Field(inventory,"stock_game_root",Node::string),*executable=Field(inventory,"source_executable",Node::object);
  const auto *root=Field(inventory,"implementation_root",Node::string),*implementation=Field(inventory,"implementation_sources",Node::array);
  if(!schema || schema->text!="ck3-player-control-source-inventory-v1" || !userdir ||
      !SamePath(Path(*userdir),launch.userdir) || !profile || !Hex(profile->text) ||
      !settings || !dlc || !mods || mods->items.size()>64 || !stock || stock->items.size()!=kStock.size() ||
      !game_root || !executable || !root || !implementation || implementation->items.size()!=kImplementation.size())
    return reject("player_control_inventory_fixed_binding_invalid");
  std::vector<std::pair<const Node *,fs::path>> recheck;
  const auto file=[&](const Node &n,const fs::path &p) {
    if(!FixedFile(n,p)) return false;
    recheck.emplace_back(&n,p);return true;
  };
  if(!file(*settings,launch.userdir/L"pdx_settings.txt") || !file(*dlc,launch.userdir/L"dlc_load.json"))
    return reject("player_control_actual_settings_or_dlc_changed");
  std::string dlc_bytes;
  if(!ReadFile(launch.userdir/L"dlc_load.json",dlc_bytes,16U*1024U*1024U))
    return reject("player_control_actual_dlc_unreadable");
  Node actual_dlc;
  if(!InventoryParser(dlc_bytes).Parse(actual_dlc)) return reject("player_control_actual_dlc_invalid");
  const auto *enabled=Field(actual_dlc,"enabled_mods",Node::array);
  if(!enabled || enabled->items.size()!=mods->items.size()) return reject("player_control_mod_order_changed");
  std::array<wchar_t,32768> image{};
  const auto length=GetModuleFileNameW(nullptr,image.data(),static_cast<DWORD>(image.size()));
  if(length==0 || length>=image.size()) return reject("player_control_actual_executable_path_unavailable");
  const fs::path image_path(image.data());
  const auto *image_name=Field(*executable,"path",Node::string),*image_sha=Field(*executable,"sha256",Node::string);
  std::string image_bytes;
  if(!Closed(*executable,{"path","sha256"}) || !image_name || !image_sha ||
      !SamePath(Path(*image_name),image_path) || image_sha->text!=
      "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6" ||
      !PlainChain(image_path) || !ReadFile(image_path,image_bytes,128U*1024U*1024U) ||
      !NormalExitMapSha256V1(image_bytes,digest) || digest!=image_sha->text)
    return reject("player_control_actual_executable_bytes_changed");
  const auto actual_game=image_path.parent_path().parent_path()/L"game";
  if(!SamePath(Path(*game_root),actual_game)) return reject("player_control_stock_game_root_changed");
  std::set<std::string> stock_paths;
  for(std::size_t i=0;i<kStock.size();++i) {
    const auto &row=stock->items[i];const auto &pin=kStock[i];
    if(!stock_paths.insert(pin.path).second) return reject("player_control_compiled_stock_path_duplicate");
    const auto *size=Field(row,"bytes",Node::number),*hash=Field(row,"sha256",Node::string);
    if(!size || !hash || size->integer!=pin.bytes || hash->text!=pin.sha ||
        !file(row,actual_game/fs::path(Wide(pin.path)))) return reject("player_control_stock_gui_exact_bytes_changed");
  }
  const auto implementation_root=Path(*root);
  if(!PlainChain(implementation_root) || !fs::is_directory(implementation_root))
    return reject("player_control_implementation_root_unavailable");
  std::set<std::string> implementation_paths;
  for(std::size_t i=0;i<kImplementation.size();++i) {
    const auto &row=implementation->items[i];const auto &pin=kImplementation[i];
    if(!implementation_paths.insert(pin.path).second) return reject("player_control_compiled_implementation_path_duplicate");
    const auto *size=Field(row,"bytes",Node::number),*hash=Field(row,"sha256",Node::string);
    if(!size || !hash || size->integer!=pin.bytes || hash->text!=pin.sha ||
        !file(row,implementation_root/fs::path(Wide(pin.path))))
      return reject("player_control_fixed20_compiled_source_bytes_changed");
  }
  std::set<std::wstring> roots;
  std::vector<std::pair<fs::path,std::set<std::wstring>>> censuses;
  for(std::size_t i=0;i<mods->items.size();++i) {
    const auto &mod=mods->items[i];
    const auto *registration=Field(mod,"registration",Node::string),*modroot=Field(mod,"root",Node::string);
    const auto *outer=Field(mod,"outer_descriptor",Node::object),*inner=Field(mod,"inner_descriptor",Node::object);
    const auto *files=Field(mod,"files",Node::array);
    fs::path registered;
    if(!Closed(mod,{"registration","root","outer_descriptor","inner_descriptor","files"}) ||
        !registration || !modroot || !outer || !inner || !files || files->items.size()>100000 ||
        enabled->items[i].kind!=Node::string || registration->text!=enabled->items[i].text ||
        !NativeRelative(registration->text,registered) || *registered.begin()!=L"mod")
      return reject("player_control_mod_closed_inventory_invalid");
    const auto actual_root=Path(*modroot);
    if(!PlainChain(actual_root) || !fs::is_directory(actual_root) ||
        !roots.insert(Lower(fs::weakly_canonical(actual_root).native())).second)
      return reject("player_control_mod_root_or_alias_unsupported");
    std::string outer_bytes,inner_bytes;
    if(!file(*outer,launch.userdir/registered) || !file(*inner,actual_root/L"descriptor.mod") ||
        !ReadFile(launch.userdir/registered,outer_bytes,1024U*1024U) ||
        !ReadFile(actual_root/L"descriptor.mod",inner_bytes,1024U*1024U) ||
        !Descriptor(outer_bytes,actual_root,true) || !Descriptor(inner_bytes,actual_root,false))
      return reject("player_control_mod_descriptor_changed");
    std::set<std::wstring> listed,actual;
    for(const auto &row:files->items) {
      const auto *relative=Field(row,"relative_path",Node::string),*size=Field(row,"bytes",Node::number),*hash=Field(row,"sha256",Node::string);
      fs::path path;
      if(!Closed(row,{"relative_path","bytes","sha256"}) || !relative || !size || !hash ||
          !Hex(hash->text) || !NativeRelative(relative->text,path) ||
          Lower(path.extension().native())==L".gui" || !listed.insert(Lower(path.native())).second ||
          !PlainChain(actual_root/path)) return reject("player_control_mod_gui_or_relative_source_unsupported");
      std::string actual_bytes,actual_sha;
      if(!ReadFile(actual_root/path,actual_bytes,128U*1024U*1024U) || actual_bytes.size()!=size->integer ||
          !NormalExitMapSha256V1(actual_bytes,actual_sha) || actual_sha!=hash->text)
        return reject("player_control_mod_actual_file_bytes_changed");
    }
    std::size_t entries=0;
    for(const auto &entry:fs::recursive_directory_iterator(actual_root)) {
      if(++entries>200000 || !Plain(entry.path())) return reject("player_control_mod_census_or_reparse_unsupported");
      if(entry.is_regular_file()) actual.insert(Lower(fs::relative(entry.path(),actual_root).native()));
    }
    if(actual!=listed) return reject("player_control_mod_complete_census_changed");
    censuses.emplace_back(actual_root,std::move(listed));
  }
  if(!LoadedSourceModule(reason)) return false;
  for(const auto &[record,path]:recheck) if(!FixedFile(*record,path))
    return reject("player_control_inventory_file_changed_during_validation");
  for(const auto &[modroot,listed]:censuses) {
    std::set<std::wstring> actual;std::size_t entries=0;
    for(const auto &entry:fs::recursive_directory_iterator(modroot)) {
      if(++entries>200000 || !Plain(entry.path())) return reject("player_control_mod_final_census_unsupported");
      if(entry.is_regular_file()) actual.insert(Lower(fs::relative(entry.path(),modroot).native()));
    }
    if(actual!=listed) return reject("player_control_mod_final_census_changed");
  }
  // Recheck every listed mod file after the current loaded module proof.
  for(const auto &mod:mods->items) {
    const auto *modroot=Field(mod,"root",Node::string),*files=Field(mod,"files",Node::array);
    if(!modroot || !files) return reject("player_control_mod_final_inventory_invalid");
    for(const auto &row:files->items) {
      const auto *relative=Field(row,"relative_path",Node::string),*size=Field(row,"bytes",Node::number),*hash=Field(row,"sha256",Node::string);
      fs::path path;std::string source,source_sha;
      if(!relative || !size || !hash || !NativeRelative(relative->text,path) ||
          !PlainChain(Path(*modroot)/path) || !ReadFile(Path(*modroot)/path,source,128U*1024U*1024U) ||
          source.size()!=size->integer || !NormalExitMapSha256V1(source,source_sha) || source_sha!=hash->text)
        return reject("player_control_mod_final_actual_bytes_changed");
    }
  }
  std::string final_image;
  if(!ReadFile(image_path,final_image,128U*1024U*1024U) || final_image!=image_bytes)
    return reject("player_control_executable_changed_during_source_validation");
  std::string final_bytes;
  if(!ReadFile(manifest,final_bytes,16U*1024U*1024U) || final_bytes!=bytes)
    return reject("player_control_fixed_inventory_changed_during_validation");
  reason.clear();return true;
}
} // namespace player_control_inventory

bool ExecutePlayerControlReadonlyV1(PlayerControlReadonlyContextV1 &ctx,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &env) noexcept {
  auto &out=ctx.observation;out=UnavailablePlayerControlObservationV1(ctx.request);
  out.native_revision=ctx.native_revision;out.connection_generation=ctx.connection_generation;
  out.pump_epoch=stamp.pump_epoch;
  try {
    const auto reject=[&](const char *why) { out.reason=why;return true; };
    // No mutation can reach a source reader, signature, flow, stage CAS or GUI callback.
    if(ctx.request.action!=PlayerControlActionV1::query_context)
      return reject("player_control_partial_readonly_mutation_unavailable_no_claim");
    PlayerControlIdentitySourceContextV1 identity{};
    identity.game=ctx.game;identity.request=&ctx.request;identity.expected_snapshot=ctx.expected_snapshot;
    identity.native_revision=ctx.native_revision;identity.connection_generation=ctx.connection_generation;
    identity.ticket=ctx.ticket;identity.owner_executor_context=ctx.owner_executor_context;
    if(!kPlayerControlV1CompiledEnabled || !ctx.game || !ctx.game->enabled() ||
        ctx.game->descriptor().game_version!="1.20.0.3" ||
        ctx.game->descriptor().executable_sha256!="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6" ||
        ctx.native_revision==0 || ctx.native_revision!=ctx.request.expected_revision ||
        ctx.connection_generation==0 || ctx.connection_generation!=ctx.request.expected_connection_generation ||
        !env.exact_build_admitted || env.offline_fixture_function_overrides ||
        env.gui_abi_revision!=ck3_11906::GuiAbiRevisionV1::crozier12003 ||
        env.module_base!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)))
      return reject("player_control_partial_exact_build_binding_unavailable");
    out.exact_build_verified=true;
    if(!Owner(identity,mailbox,stamp)) return reject("player_control_partial_owner_ticket_unavailable");
    out.owner_verified=true;
    if(!Process(ctx.request)) return reject("player_control_partial_process_identity_changed");
    out.process_identity_verified=true;
    // Verify current immutable own-module source arrays before probing their
    // exact game-image ranges. No table corruption can size an unchecked read.
    if(!player_control_inventory::VerifySources(ctx.request.source_inventory_sha256,out.reason)) return true;
    out.loaded_source_binding_verified=true;
    if(!Pins(env.module_base)) return reject("player_control_partial_identity_source_pins_changed");
    out.source_abi_pins_verified=true;
    game::Snapshot before{},after{};
    if(!game::ReadSnapshot(*ctx.game,before) || before!=ctx.expected_snapshot ||
        !before.paused || !before.map_ready || !before.has_played_character || !before.played_character_alive ||
        before.played_character_id!=ctx.request.expected_player_character_id || before.date_raw!=stamp.date_raw)
      return reject("player_control_partial_actual_frame_changed");
    out.frame_verified=true;
    PlayerControlOwnedIdentityBindingV1 owned{};
    const bool identity_observed=ReadPlayerControlOwnedIdentitySourceV1(identity,mailbox,stamp,env,out,owned);
    if(!game::ReadSnapshot(*ctx.game,after) || after!=before || !Owner(identity,mailbox,stamp)) {
      out.frame_verified=false;return reject("player_control_partial_postquery_frame_changed");
    }
    if(!identity_observed) {
      // Keep exact source failure and any actually observed partial fields.
      // Default status/phase/stock/flow/signature remain unavailable.
      if(out.reason.empty()) out.reason="player_control_partial_identity_source_unavailable";
      return true;
    }
    // File-source equality is useful partial evidence. Whole compiled stock GUI
    // topology/lifetime, CanControl, chooser selection and action sources remain
    // unproved. No GUI source callback is called and no query signature is issued.
    out.stock_files_verified=false;out.context_signature_verified=false;
    out.control_context_signature.clear();out.flow_id.reset();out.flow_complete=false;
    out.phase=PlayerControlPhaseV1::unavailable;out.status=PlayerControlStatusV1::unavailable;
    out.reason="player_control_partial_owner_identity_observed_whole_stock_flow_signature_and_mutations_unavailable";
    return true;
  } catch(...) {
    out.frame_verified=false;out.status=PlayerControlStatusV1::unavailable;
    try {out.reason="player_control_partial_inventory_or_reader_exception";} catch(...) {}
    return true;
  }
}
} // namespace xar::ck3_12003
#endif
