namespace {
using OptionAction=Full111EventOptionAction267V2;
using OptionRequest=Full111EventOptionRequest267V2;
using OptionStatus=LydStatus267V1;
using fixture::require;

struct OptionOwnerFixture {
 LydSession267V1 session;
 xar::ck3_11906::MainThreadQueryMailboxV1 mailbox;
 xar::ck3_11906::MainThreadExecutionStampV1 stamp;
 std::uint64_t ticket=0;
 std::uint64_t wall=Wall()+60000;

 OptionOwnerFixture() {
  mailbox.offline_fixture=false;mailbox.permitted_executor_quinquevigintary=&ExecuteLydOnOwner267V1;
  stamp.game_state=0x4000;stamp.jomini_state=0x2000;stamp.thread_id=7;stamp.paused=true;
 }
 LydContext267V1 context(std::uint64_t revision=12,std::uint64_t connection=21) {
  LydContext267V1 q;q.session=&session;q.mailbox=&mailbox;q.published_revision=revision;q.connection_generation=connection;
  q.ticket.sequence=++ticket;q.full111_ordinary_events_only=q.full111_event_renderer=true;
  q.request.action=LydAction267V1::query_events;q.request.expected=fixture::core();q.request.deadline_unix_ms=wall;
  q.request.instance_id=fixture::foreground;return q;
 }
 LydContext267V1 renderer() {
  auto q=context();constexpr std::string_view id="renderer-v1";
  std::copy(id.begin(),id.end(),q.request.request_id.begin());q.request.request_id_size=static_cast<std::uint8_t>(id.size());
  ArmLydDeadline267V1(q);
  stamp.pump_epoch=q.ticket.sequence+11;
  require(ExecuteLydInner267V1(q,stamp)&&q.result.status==OptionStatus::available,"original renderer unavailable");
  require(q.result.renderer&&q.result.claim_sequence==0&&!q.result.effect_attempted,"v1 renderer conferred effect authority");
  return q;
 }
 LydContext267V1 run(const OptionRequest &request,std::uint64_t revision=12,std::uint64_t connection=21) {
  auto q=context(revision,connection);
  q.request.expected=request.expected;q.request.deadline_unix_ms=request.deadline_unix_ms;q.request.instance_id=request.target.instance_id;
  q.event_option_result.target=request.target;q.event_option_result.lineage=request.lineage;q.event_option_request=request;
  ArmLydDeadline267V1(q);
  stamp.pump_epoch=q.ticket.sequence+11;
  require(ExecuteLydInner267V1(q,stamp),"owner infrastructure failed");return q;
 }
 OptionRequest prepare(const LydContext267V1 &renderer) const {
  OptionRequest request;request.request_id="event-prepare-v2";request.expected=fixture::core();request.deadline_unix_ms=wall;
  request.target={fixture::foreground,request.expected.played_character_id,"bookmark.1070",4};
  request.lineage.source_revision=12;request.lineage.renderer_request_id=renderer.request.id();
  request.lineage.renderer_provider_generation=renderer.result.provider_generation;request.lineage.renderer_query_sequence=renderer.result.query_sequence;
  return request;
 }
 static OptionRequest select(OptionRequest request,const LydContext267V1 &prepared) {
  request.action=OptionAction::select;request.request_id="event-select-v2";request.expected_revision=12;
  request.lineage=*prepared.event_option_result.lineage;return request;
 }
 static OptionRequest queue(OptionRequest request,const LydContext267V1 &selected) {
  request.action=OptionAction::query_queue;request.request_id="event-queue-v2";request.expected_revision=0;
  request.deadline_unix_ms+=10000;request.lineage=*selected.event_option_result.lineage;return request;
 }
};

void VerifyStockOptionOwner() {
 using namespace fixture;
 OptionOwnerFixture fixture;
 const auto before=fixture.renderer();
 const auto prepare=fixture.prepare(before);
 require(fixture.run(prepare,13).result.status==OptionStatus::stale_source,"different published Full revision accepted");
 require(fixture.run(prepare,12,22).result.status==OptionStatus::stale_source,"renderer trusted a different connection");
 auto altered=prepare;++altered.deadline_unix_ms;
 require(fixture.run(altered).result.status==OptionStatus::stale_source,"prepare widened the original deadline");
 altered=prepare;altered.deadline_unix_ms=Wall()-1;
 require(fixture.run(altered).result.status==OptionStatus::expired,"expired quote accepted");
 altered=prepare;altered.target.authored_option_index=0;
 require(fixture.run(altered).result.status==OptionStatus::unavailable,"render index became authored index");
 const auto prepared=fixture.run(prepare);
 require(prepared.result.status==OptionStatus::available&&!effects&&prepared.event_option_result.lineage->lease_sequence==1,
     "qualified prepare failed or performed an effect");
 const auto select=OptionOwnerFixture::select(prepare,prepared);
 altered=select;altered.lineage.lease_sequence++;
 require(fixture.run(altered).result.status==OptionStatus::stale_source,"changed native lease was accepted");
 foreground=8;
 require(fixture.run(select).result.status!=OptionStatus::selection_dispatched&&!effects,"another foreground was selected");
 foreground=7;option_changed=true;
 require(fixture.run(select).result.status==OptionStatus::stale_source&&!effects,"a replaced model pointer was selected");
 option_changed=false;
 const auto selected=fixture.run(select);
 require(selected.result.status==OptionStatus::selection_dispatched&&effects==1&&selected.result.native_returned&&
     selected.event_option_result.lineage->claim_sequence==2,"exact stock choice was not dispatched once");
 require(fixture.run(select).result.status==OptionStatus::claim_consumed&&effects==1,"original ID replayed");
 altered=select;altered.request_id="another-id";
 require(fixture.run(altered).result.status==OptionStatus::stale_source&&effects==1,"consumed lease replayed with new ID");
 const auto read=OptionOwnerFixture::queue(select,selected);
 require(fixture.run(read,12,22).result.status==OptionStatus::stale_source,"cross-connection queue claim accepted");
 still_pending=true;
 const auto present=fixture.run(read);
 require(present.result.status==OptionStatus::available&&present.event_option_result.queue->target_present&&effects==1,
     "changed foreground hid the original pending event");
 still_pending=false;queue_available=false;
 require(fixture.run(read).result.status==OptionStatus::unavailable&&effects==1,"unavailable queue projected absence");
 queue_available=true;
 const auto absent=fixture.run(read);
 require(absent.result.status==OptionStatus::available&&!absent.event_option_result.queue->target_present&&effects==1,
     "clean exact empty queue did not confirm absence");
 require(fixture.run(read).result.status==OptionStatus::available&&effects==1,"lost read result could not be re-observed");
}

void VerifyStockOptionRefusals() {
 using namespace fixture;
 for (bool *flag : {&option_native,&option_visible,&option_enabled}) {
  *flag=false;
  OptionOwnerFixture fixture;
  const auto before=fixture.renderer();
  const auto no=fixture.run(fixture.prepare(before));
  require(no.result.status==OptionStatus::unavailable&&!no.result.effect_attempted&&
      !no.event_option_result.lineage->lease_sequence,"unqualified row issued a lease");
  *flag=true;
 }
 OptionOwnerFixture fixture;
 const auto before=fixture.renderer();
 const auto prepare=fixture.prepare(before);
 const auto prepared=fixture.run(prepare);
 require(prepared.result.status==OptionStatus::available,"unknown test lost original preparation");
 const auto select=OptionOwnerFixture::select(prepare,prepared);
 const auto calls=effects;
 uncertain=true;
 const auto unknown=fixture.run(select);
 require(unknown.result.status==OptionStatus::indeterminate&&unknown.result.effect_attempted&&!unknown.result.cleanup_known&&
     effects==calls+1,"uncertain native effect was not retained");
 require(fixture.run(select).result.status==OptionStatus::claim_consumed&&effects==calls+1,"unknown effect replayed");
 auto changed=select;changed.request_id="no-replay-on-new-id";
 require(fixture.run(changed).result.status==OptionStatus::indeterminate&&effects==calls+1,"unknown effect rearmed on fresh ID");
 const auto read=OptionOwnerFixture::queue(select,unknown);
 require(fixture.run(read).result.status==OptionStatus::indeterminate&&!fixture.run(read).event_option_result.queue,
     "unknown effect acquired after-ACK evidence");
 uncertain=false;
}

void VerifyStockRuntimeQueue() {
 constexpr std::size_t queue_offset=0x44BC0+0x1F18;
 std::array<std::byte,0xA8> game{};
 std::vector<std::byte> data(queue_offset+16);
 std::array<std::byte,0x1C8> first{}, second{};
 std::array<std::byte,0x40> definition{};
 std::array<std::uintptr_t,2> items{reinterpret_cast<std::uintptr_t>(second.data()),reinterpret_cast<std::uintptr_t>(first.data())};
 void *game_slot=game.data();
 const auto game_address=reinterpret_cast<std::uintptr_t>(game_slot);
 const auto put=[](auto &buffer,std::size_t offset,auto value) { std::memcpy(buffer.data()+offset,&value,sizeof(value)); };
 ReadonlyBindings bindings;bindings.exact_image_admitted=true;bindings.core.game_state_slot=&game_slot;
 const Full111EventOptionTarget267V2 target{7,fixture::core().played_character_id,"bookmark.1070",4};
 Full111EventQueue267V2 queue;
 std::memcpy(definition.data()+0x10,"bookmark.1070",14);
 put(game,0xA0,data.data());put(data,queue_offset,items.data());put(data,queue_offset+8,std::int32_t{2});
 put(first,0x1C4,std::int32_t{7});put(first,0x1C0,target.recipient_character_id);put(first,0x1B8,definition.data());
 put(second,0x1C4,std::int32_t{8});
 put(data,queue_offset+12,std::int32_t{2});
 require(SampleFull111EventQueue267V2(bindings,game_address,target,queue)&&queue.target_present&&queue.instance_ids==std::vector<std::int32_t>{8,7},
     "actual pending vector lost original instance after ordering change");
 put(first,0x1C0,std::int32_t{100});
 require(!SampleFull111EventQueue267V2(bindings,game_address,target,queue),"same ID with incompatible owner confirmed absence");
 put(first,0x1C0,target.recipient_character_id);definition[0x10]=std::byte{'q'};
 require(!SampleFull111EventQueue267V2(bindings,game_address,target,queue),"wrong definition accepted");
 definition[0x10]=std::byte{'b'};put(second,0x1C4,std::int32_t{7});
 require(!SampleFull111EventQueue267V2(bindings,game_address,target,queue),"duplicate runtime ID accepted");
 put(second,0x1C4,std::int32_t{8});put(data,queue_offset+12,std::int32_t{1});
 require(SampleFull111EventQueue267V2(bindings,game_address,target,queue)&&!queue.target_present&&queue.instance_ids==std::vector<std::int32_t>{8},
     "typed complete other-instance-only queue did not confirm absence");
 put(data,queue_offset,std::uintptr_t{0});
 require(!SampleFull111EventQueue267V2(bindings,game_address,target,queue),"missing positive vector accepted");
 put(data,queue_offset+12,std::int32_t{0});
 require(!SampleFull111EventQueue267V2(bindings,game_address,target,queue),"lost backing storage became an empty queue");
 put(data,queue_offset+8,std::int32_t{0});
 require(SampleFull111EventQueue267V2(bindings,game_address,target,queue)&&!queue.target_present&&queue.instance_ids.empty(),
     "known zero with empty storage unavailable");
 require(!SampleFull111EventQueue267V2(bindings,game_address+1,target,queue),"foreign Game accepted");
 put(data,queue_offset+12,std::int32_t{-1});
 require(!SampleFull111EventQueue267V2(bindings,game_address,target,queue),"negative queue count accepted");
 put(data,queue_offset+12,std::int32_t{33});put(data,queue_offset+8,std::int32_t{33});
 require(!SampleFull111EventQueue267V2(bindings,game_address,target,queue),"truncated overflow became complete");
}

std::string EncodeOptionFixtureRequest(const OptionRequest &request) {
 const auto &target=request.target;
 const auto &lineage=request.lineage;
 const auto index=static_cast<std::size_t>(request.action);
 Json j;
 j.data=R"({"type":"execute_step","protocol_version":1)";
 j.str("request_id",request.request_id);j.str("step",kFull111EventOptionSteps267V2[index]);
 j.num("expected_revision",static_cast<std::int64_t>(request.expected_revision));
 j.num("core_control_deadline_unix_ms",static_cast<std::int64_t>(request.deadline_unix_ms));
 j.key("arguments");j.data+="{}";
 j.key("ordinary_event");j.data+="{\"schema\":";String(j.data,kFull111EventOptionRequestSchema267V2);
 j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("adapter_id",xar::ck3_121003::full111::kAdapterId);
 j.str("backend",kLydBackend267V1);j.str("action",kEventOptionActions[index]);
 j.key("expected_core");j.data+="{\"date_raw\":"+std::to_string(request.expected.clock.date_raw);
 j.num("speed",request.expected.clock.speed);j.flag("paused",request.expected.clock.paused);
 j.num("local_player_id",request.expected.local_player_id);j.flag("map_ready",request.expected.map_ready);
 j.flag("has_played_character",request.expected.has_played_character);j.num("played_character_id",request.expected.played_character_id);
 j.flag("played_character_alive",request.expected.played_character_alive);j.data+='}';
 j.num("instance_id",target.instance_id);j.num("recipient_character_id",target.recipient_character_id);j.str("definition_key",target.definition_key);
 j.num("authored_option_index",target.authored_option_index);j.u64("source_revision",lineage.source_revision);
 j.str("renderer_request_id",lineage.renderer_request_id);j.u64("renderer_provider_generation",lineage.renderer_provider_generation);
 j.u64("renderer_query_sequence",lineage.renderer_query_sequence);j.nullable("prepare_request_id",lineage.prepare_request_id);
 j.u64("lease_sequence",lineage.lease_sequence);j.nullable("effect_request_id",lineage.effect_request_id);j.u64("claim_sequence",lineage.claim_sequence);
 j.data+="}}";return j.data;
}

void VerifyOptionWireRequest(const OptionRequest &request) {
 const auto bytes=EncodeOptionFixtureRequest(request);
 OptionRequest actual;
 require(ParseFull111EventOptionRequest267V2(bytes,actual)&&actual.action==request.action&&actual.target==request.target&&
     actual.lineage==request.lineage&&actual.expected_revision==request.expected_revision&&actual.deadline_unix_ms==request.deadline_unix_ms&&
     full111_event_effect::SameCore(actual.expected,request.expected),"v2 parser rejected the exact phase wire");
 LydRequest267V1 legacy;
 require(!ParseFull111EventRendererRequest267V1(bytes,legacy)&&!ParseFull111LydEventRequest267V1(bytes,legacy),
     "legacy read parser took v2 claim");
 auto altered=bytes;const auto actor=altered.find("\"recipient_character_id\":-16777215");
 altered.replace(actor,std::string_view("\"recipient_character_id\":-16777215").size(),"\"recipient_character_id\":-16777214");
 require(!ParseFull111EventOptionRequest267V2(altered,actual)&&actual.request_id.empty(),"wrong or partial typed recipient crossed the wire");
 altered=bytes;const auto index=altered.find("\"authored_option_index\":4");
 altered.replace(index,std::string_view("\"authored_option_index\":4").size(),"\"authored_option_index\":true");
 require(!ParseFull111EventOptionRequest267V2(altered,actual),"bool masqueraded as authored option index");
 auto wrong=request;wrong.expected_revision=request.action==OptionAction::select?0:12;
 require(!ParseFull111EventOptionRequest267V2(EncodeOptionFixtureRequest(wrong),actual),"wrong phase revision accepted");
}

void EmitOptionWire(const char *path) {
 OptionOwnerFixture fixture;
 const auto renderer=fixture.renderer();
 auto prepare=fixture.prepare(renderer);
 const auto prepared=fixture.run(prepare);
 auto select=OptionOwnerFixture::select(prepare,prepared);
 const auto selected=fixture.run(select);
 auto queue=OptionOwnerFixture::queue(select,selected);
 fixture::still_pending=true;const auto present=fixture.run(queue);
 fixture::still_pending=false;const auto absent=fixture.run(queue);
 fixture::queue_available=false;const auto unavailable=fixture.run(queue);fixture::queue_available=true;
 require(prepared.result.status==OptionStatus::available&&selected.result.status==OptionStatus::selection_dispatched&&
     present.result.status==OptionStatus::available&&absent.result.status==OptionStatus::available&&
     unavailable.result.status==OptionStatus::unavailable,"offline fixture phase failed");
 // Stable wire fixture identities only. Calls above use the production reducer with explicit NoGame DATA seams.
 for (auto *req : {&prepare,&select,&queue}) {
  req->lineage.renderer_provider_generation=3;req->lineage.renderer_query_sequence=10;
  req->deadline_unix_ms=1795777200000ULL+(req==&queue?10000ULL:0ULL);
  VerifyOptionWireRequest(*req);
 }
 const std::filesystem::path directory{path};
 if (!std::filesystem::exists(directory)) std::filesystem::create_directories(directory);
 const auto save=[&](std::string_view name, const std::string &bytes) {
  const auto file=directory/std::string(name);
  require(!std::filesystem::exists(file),"refusing to overwrite an existing offline fixture");
  std::ofstream out(file,std::ios::binary);out.write(bytes.data(),static_cast<std::streamsize>(bytes.size()));
  require(out.good(),"unable to write software fixture");
 };
 const auto save_result=[&](std::string_view name,const OptionRequest &request,const LydContext267V1 &response) {
  auto data=response.event_option_result;
  data.lineage->renderer_provider_generation=3;data.lineage->renderer_query_sequence=10;
  save(name,SerializeFull111EventOptionResult267V2(request.request_id,request.action,response.result,data));
 };
 save("v2-prepare-request.json",EncodeOptionFixtureRequest(prepare));
 save("v2-select-request.json",EncodeOptionFixtureRequest(select));
 save("v2-queue-request.json",EncodeOptionFixtureRequest(queue));
 save_result("v2-prepare-result.json",prepare,prepared);save_result("v2-select-result.json",select,selected);
 save_result("v2-queue-present.json",queue,present);save_result("v2-queue-absent.json",queue,absent);
 save_result("v2-queue-unavailable.json",queue,unavailable);
}
int ValidateOptionWire(const char *path) {
 std::ifstream input(path,std::ios::binary);
 std::string bytes{std::istreambuf_iterator<char>(input),std::istreambuf_iterator<char>()};
 OptionRequest request;
 return input.good()&&ParseFull111EventOptionRequest267V2(bytes,request)?0:1;
}
}
