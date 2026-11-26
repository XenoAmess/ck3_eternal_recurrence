#pragma once
#include "xar_bridge/ck3_121003_full111.hpp"
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
}

struct Full111OrdinaryEventWitnessV1 {
  full111_event_queue::Sample queue;
  LydScene267V1 scene;
  std::vector<GuiWindowNodeV1> widgets;
  LydRaw267V1 raw;
  friend bool operator==(const Full111OrdinaryEventWitnessV1&,const Full111OrdinaryEventWitnessV1&)=default;
};

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
