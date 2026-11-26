// The Full111 queue and the ordinary GUI census are independent witnesses.
namespace full111_event_queue {
bool Capture(const ReadonlyBindings&bindings,std::uintptr_t owner_game,Sample&out)noexcept{
 using lyd_common::At;
 constexpr std::size_t queue_offset=0x44BC0+0x1F18;
 std::uintptr_t game=0;
 if(!bindings.exact_image_admitted||!owner_game||
     !At(reinterpret_cast<std::uintptr_t>(bindings.core.game_state_slot),0,game)||game!=owner_game||
     !At(game,0xA0,out.game_data)||!out.game_data||
     out.game_data>(std::numeric_limits<std::uintptr_t>::max)()-queue_offset)return false;
 const auto header=out.game_data+queue_offset;
 if(!At(header,0,out.items)||!At(header,8,out.capacity)||!At(header,12,out.count)||
     out.count<=0||static_cast<std::size_t>(out.count)>out.rows.size()||
     out.capacity<out.count||!out.items)return false;
 for(std::int32_t i=0;i<out.count;++i){
  const auto index=static_cast<std::size_t>(i);
  if(!At(out.items,index*sizeof(std::uintptr_t),out.rows[index])||!out.rows[index])return false;
 }
 return true;
}

bool Matches(const Sample&queue,std::uintptr_t owner_game,std::int32_t played_character,
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
