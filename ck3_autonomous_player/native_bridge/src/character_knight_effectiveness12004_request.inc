// Included once by the existing request TU. Fixed readonly request; no skill
// enum, modifier index, selector, army or caller pointer is ever dispatched.
namespace xar::ck3_12004::character_skill_effects {
bool ParseKnightRequest(std::string_view payload,const game::Snapshot &current,
    std::uint64_t revision,std::uint64_t generation,std::uint32_t &target) noexcept {
  std::uint64_t a=0,b=0,date=0,played=0,pid=0,gen=0,id=0;
  if(!bridge::JsonUnsignedField(payload,"expected_revision",a)||!a||a!=revision||
      !bridge::JsonUnsignedField(payload,"expected_snapshot_revision",b)||b!=revision||
      !bridge::JsonUnsignedField(payload,"expected_date_raw",date)||
      date>static_cast<std::uint64_t>((std::numeric_limits<std::int32_t>::max)())||
      date!=static_cast<std::uint64_t>(current.date_raw)||
      !bridge::JsonUnsignedField(payload,"expected_actor_character_id",played)||
      played!=static_cast<std::uint64_t>(current.played_character_id)||
      !bridge::JsonUnsignedField(payload,"expected_game_pid",pid)||pid!=GetCurrentProcessId()||
      !bridge::JsonUnsignedField(payload,"expected_connection_generation",gen)||!gen||gen!=generation||
      !bridge::JsonUnsignedField(payload,"character_id",id)||id>=0xFFFFFFFFULL)return false;
  target=static_cast<std::uint32_t>(id);return true;
}
} // namespace xar::ck3_12004::character_skill_effects
