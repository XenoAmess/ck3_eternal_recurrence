#pragma once
#include "xar_bridge/ck3_121003_full111.hpp"
#include <algorithm>
#include "xar_bridge/ck3_121003_lyd26785313_owner_v1.hpp"

namespace xar::ck3_121003::build26785313 {
namespace full111_event_queue {
constexpr std::size_t kMaximumRows=32;
struct Sample {
  std::uintptr_t game_data=0,items=0;
  std::int32_t capacity=0,count=0;
  std::array<std::uintptr_t,kMaximumRows> rows{};
  friend bool operator==(const Sample&,const Sample&)=default;
};
bool Capture(const ReadonlyBindings&,std::uintptr_t owner_game,Sample&, bool allow_empty=false) noexcept;

inline bool Matches(const Sample&queue,std::uintptr_t owner_game,std::int32_t played_character,
 const LydRaw267V1&raw)noexcept{
 if(raw.manager_census.game!=owner_game||!raw.source.events||
     raw.event_rows.size()!=static_cast<std::size_t>(queue.count)||
     raw.event_rows.size()!=raw.source.events->events.size())return false;
 const auto end=queue.rows.begin()+queue.count;
 std::array<bool,kMaximumRows> matched{};
 for(std::size_t i=0;i<raw.event_rows.size();++i){
  const auto&typed=raw.event_rows[i];
  const auto&event=raw.source.events->events[i];
  if(typed.material.game!=owner_game||typed.instance_id!=event.instance_id||
      event.recipient_character_id!=played_character||!typed.runtime)return false;
  const auto row=std::find(queue.rows.begin(),end,typed.runtime);
  if(row==end||matched[static_cast<std::size_t>(row-queue.rows.begin())])return false;
  matched[static_cast<std::size_t>(row-queue.rows.begin())]=true;
 }
 return true;
}
}

enum class Full111OrdinaryEventReadFailure {
  unknown, owner, scene_unavailable, scene_changed, queue_unavailable, foreground, queue_changed,
};

struct Full111OrdinaryEventWitnessV1 {
  full111_event_queue::Sample queue;
  LydScene267V1 scene;
  std::vector<GuiWindowNodeV1> widgets;
  LydRaw267V1 raw;
  Full111OrdinaryEventReadFailure failure=Full111OrdinaryEventReadFailure::unknown;
  friend bool operator==(const Full111OrdinaryEventWitnessV1&,const Full111OrdinaryEventWitnessV1&)=default;
};

inline std::uintptr_t Full111ForegroundEventRootV1(const Full111OrdinaryEventWitnessV1 &witness) noexcept {
  const auto &scene=witness.scene;
  const auto layer=std::find_if(witness.widgets.begin(),witness.widgets.end(),[&](const GuiWindowNodeV1 &node){
    return node.widget==scene.events_layer && node.parent==scene.global && node.name=="events";
  });
  if(layer==witness.widgets.end() || scene.event_roots.empty())return 0;
  std::uint32_t child_count=0;
  std::size_t eligible_count=0;
  std::uintptr_t foreground=0;
  for(const auto &child:witness.widgets){
    if(child.parent!=scene.events_layer)continue;
    if(!child.widget || child.sibling_index!=child_count)return 0;
    ++child_count;
    // Stock IsOnTop scans the GUI parent vector backwards, ignoring bit 8.
    if((child.flags&8U)!=0)continue;
    if(!child.visible || child.name!="character_event" || eligible_count>=scene.event_roots.size())return 0;
    const auto &root=scene.event_roots[eligible_count];
    if(root.widget!=child.widget || !root.visible)return 0;
    foreground=child.widget;
    ++eligible_count;
  }
  return child_count==static_cast<std::uint32_t>(layer->child_count) &&
    eligible_count==scene.event_roots.size()?foreground:0;
}

bool ReadFull111LydEventsWithQueueV1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,
    const LydScene267V1&,std::uint64_t,const LydRequest267V1&,std::uintptr_t,
    LydRaw267V1&,std::string&,full111_event_queue::Sample*) noexcept;
bool ReadFull111OrdinaryEventOnOwnerV1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,
    std::uintptr_t game,std::uintptr_t jomini,std::uint64_t wall_deadline,std::uint64_t monotonic_deadline,
    const void *owner_context,bool (*still_owned)(const void*) noexcept,Full111OrdinaryEventWitnessV1&);
}

namespace xar::ck3_121003::full111 {
struct OrdinaryEventReaderV1 {
  void *context=nullptr;
  bool (*read)(void*,const ck3_1210::CoreSnapshotPrefix&,build26785313::Full111OrdinaryEventWitnessV1&)=nullptr;
};

bool ReadFullWithOrdinaryEventV1(const ck3_1210::FullSnapshotBindingsV1&,xar::game::Snapshot&,
    ck3_1210::FullSnapshotDiagnosticsV1&,const OrdinaryEventReaderV1&) noexcept;
}
