#pragma once
#include "xar_bridge/ck3_121003_stock_bookmark107026785313_v1.hpp"
#include "xar_bridge/ck3_121003_lyd26785313_owner_v1.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
using StockBookmarkFrame267V1=LydFrame267V1;
struct StockBookmarkRaw267V1{LydRaw267V1 material{};StockBookmarkSource267V1 source{};friend bool operator==(const StockBookmarkRaw267V1&,const StockBookmarkRaw267V1&)=default;};
enum class StockBookmarkCallStatus267V1{refused,returned,indeterminate};
struct StockBookmarkCall267V1{StockBookmarkCallStatus267V1 status=StockBookmarkCallStatus267V1::refused;bool entered=false,native_returned=false,cleanup_known=true;};
struct StockBookmarkContext267V1;
class StockBookmarkSession267V1{public:StockBookmarkSession267V1();~StockBookmarkSession267V1();StockBookmarkSession267V1(const StockBookmarkSession267V1&)=delete;StockBookmarkSession267V1&operator=(const StockBookmarkSession267V1&)=delete;private:struct State;std::unique_ptr<State>state_;friend bool ExecuteStockBookmarkInner267V1(StockBookmarkContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;friend void BlockStockBookmarkUnknown267V1(StockBookmarkSession267V1&)noexcept;};
struct StockBookmarkContext267V1{ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};StockBookmarkRequest267V1 request{};StockBookmarkResult267V1 result{};StockBookmarkSession267V1*session=nullptr;std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool observation_entered=false;};
StockBookmarkSession267V1&RetainedStockBookmarkSession267V1();void BlockStockBookmarkUnknown267V1(StockBookmarkSession267V1&)noexcept;void ArmStockBookmarkDeadline267V1(StockBookmarkContext267V1&)noexcept;
bool ExecuteStockBookmarkInner267V1(StockBookmarkContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;bool ExecuteStockBookmarkOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadStockBookmarkFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,StockBookmarkFrame267V1&,std::string&)noexcept;
bool VerifyStockBookmarkImage267V1(std::uintptr_t)noexcept;
bool ReadStockBookmarkRaw267V1(const ReadonlyBindings&,const StockBookmarkFrame267V1&,const StockBookmarkRequest267V1&,std::uint64_t,StockBookmarkRaw267V1&,std::string&)noexcept;
StockBookmarkCall267V1 CallStockBookmarkRaw267V1(const ReadonlyBindings&,const StockBookmarkFrame267V1&,const StockBookmarkRequest267V1&,std::uint64_t,const StockBookmarkRaw267V1&)noexcept;
bool StockBookmarkStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchStockBookmarkRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
