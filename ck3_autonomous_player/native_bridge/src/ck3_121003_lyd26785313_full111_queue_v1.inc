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

}
