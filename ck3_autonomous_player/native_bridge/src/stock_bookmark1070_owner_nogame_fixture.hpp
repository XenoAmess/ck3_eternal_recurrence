#pragma once
#include <windows.h>
#include <cassert>
#include <chrono>
#include <iostream>
#include <stdexcept>
#include "xar_bridge/ck3_121003_stock_bookmark107026785313_owner_v1.hpp"
namespace stock_owner_test {using namespace xar::ck3_121003::build26785313;
namespace ck3_1210=xar::ck3_1210;namespace ck3_11906=xar::ck3_11906;
inline StockBookmarkFrame267V1 frame;inline StockBookmarkRaw267V1 raw;inline bool read_good=true,frame_good=true;inline int calls=0,reads=0,frames=0;inline StockBookmarkCall267V1 response;
inline ck3_1210::CoreSnapshotPrefix Core(std::int32_t actor=36423){ck3_1210::CoreSnapshotPrefix c;c.clock={53145600,3,true};c.local_player_id=1;c.map_ready=c.has_played_character=c.played_character_alive=true;c.played_character_id=actor;return c;}
inline void Seed(std::int32_t actor=36423){frame={};raw={};read_good=frame_good=true;calls=reads=frames=0;response={StockBookmarkCallStatus267V1::returned,true,true,true};frame.facts_verified=true;frame.core=Core(actor);frame.scene.kind=LydKind267V1::events;frame.scene.global=0x1100;frame.scene.jomini=0x2200;frame.scene.context=0x3300;frame.scene.gfx=0x4400;frame.scene.handler=0x5500;frame.scene.application=0x6600;frame.scene.events_layer=0x7700;raw.source.sampled_twice=raw.source.event_census.census_complete=true;raw.source.event_census.named_root_count=1;LydEventRow267V1 row;row.instance_id=1;row.recipient_character_id=actor;row.authored_option_count=3;row.definition_key=kStockBookmarkDefinition267V1;row.opening="Original opening";row.description="Original description";row.named_root_bound=row.window_visible=row.window_enabled=true;for(int index:{2,0,1}){LydEventOption267V1 o;o.authored_option_index=index;o.native_can_select=index==2;o.text="Actual option "+std::to_string(index);row.options.push_back(o);}raw.source.event_census.events.push_back(row);raw.source.fixed_instance_id=1;raw.source.select_c_admissible=true;raw.material.manager_census.game=0x8800;raw.material.manager_census.jomini=frame.scene.jomini;raw.material.source.kind=LydKind267V1::events;raw.material.source.events=raw.source.event_census;raw.material.semantic_model.push_back(std::byte{1});}
inline void Check(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
struct Fixture{StockBookmarkSession267V1 session;ck3_11906::MainThreadQueryMailboxV1 mailbox{};ck3_11906::MainThreadExecutionStampV1 stamp{};std::uint64_t seq=0;Fixture(std::int32_t actor=36423){Seed(actor);mailbox.offline_fixture=false;mailbox.permitted_executor_untrigintary=&ExecuteStockBookmarkOnOwner267V1;stamp.thread_id=7;stamp.pump_epoch=9;}
 StockBookmarkContext267V1 Context(std::string_view id,StockBookmarkAction267V1 action=StockBookmarkAction267V1::query){StockBookmarkContext267V1 q;q.session=&session;q.mailbox=&mailbox;q.ticket.sequence=++seq;q.connection_generation=1;q.request.action=action;q.request.expected=frame.core;q.request.deadline_unix_ms=18446744073709551615ULL;std::copy(id.begin(),id.end(),q.request.request_id.begin());q.request.request_id_size=static_cast<std::uint8_t>(id.size());ArmStockBookmarkDeadline267V1(q);return q;}
 StockBookmarkContext267V1 Query(std::string_view id="query"){auto q=Context(id);Check(ExecuteStockBookmarkInner267V1(q,stamp),"owner returned");Check(q.result.status==StockBookmarkStatus267V1::available&&q.result.source_available&&q.result.source,"actual owner query Source");return q;}
 StockBookmarkContext267V1 Select(const StockBookmarkContext267V1&query,std::string_view id="select"){auto q=Context(id,StockBookmarkAction267V1::select_c);q.request.expected=query.request.expected;q.request.deadline_unix_ms=query.request.deadline_unix_ms;q.request.provider_generation=query.result.provider_generation;q.request.query_sequence=query.result.query_sequence;q.request.instance_id=query.result.source->fixed_instance_id;ArmStockBookmarkDeadline267V1(q);return q;}
 void Run(StockBookmarkContext267V1&q){Check(ExecuteStockBookmarkInner267V1(q,stamp),"owner execute");}
};
}
namespace xar::ck3_121003::build26785313 {
ReadonlyBindings BindReadonlyImage(std::uintptr_t,std::string_view)noexcept{ReadonlyBindings b;b.exact_image_admitted=true;return b;}
bool ReadStockBookmarkFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t wall,std::uint64_t,StockBookmarkFrame267V1&out,std::string&why)noexcept{++stock_owner_test::frames;out=stock_owner_test::frame;out.scene.wall_deadline=wall;why.clear();return stock_owner_test::frame_good;}
bool ReadStockBookmarkRaw267V1(const ReadonlyBindings&,const StockBookmarkFrame267V1&,const StockBookmarkRequest267V1&,std::uint64_t,StockBookmarkRaw267V1&out,std::string&why)noexcept{++stock_owner_test::reads;out=stock_owner_test::raw;why="self-owned adapter DATA";return stock_owner_test::read_good;}
StockBookmarkCall267V1 CallStockBookmarkRaw267V1(const ReadonlyBindings&,const StockBookmarkFrame267V1&,const StockBookmarkRequest267V1&,std::uint64_t,const StockBookmarkRaw267V1&)noexcept{++stock_owner_test::calls;return stock_owner_test::response;}
}
#ifndef XAR_STOCK_BOOKMARK_OWNER_SOURCE
#define XAR_STOCK_BOOKMARK_OWNER_SOURCE "ck3_121003_stock_bookmark107026785313_owner_v1.cpp"
#endif
#ifndef XAR_STOCK_BOOKMARK_WIRE_SOURCE
#define XAR_STOCK_BOOKMARK_WIRE_SOURCE "ck3_121003_stock_bookmark107026785313_wire_v1.cpp"
#endif
#include XAR_STOCK_BOOKMARK_OWNER_SOURCE
#include XAR_STOCK_BOOKMARK_WIRE_SOURCE
