#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include "xar_bridge/ck3_121003_gui_root_index26785313_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/ck3_121003_gui_window26785313_v1.hpp"
#include "xar_bridge/ck3_121003_rite_draft26785313_v2.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>

namespace xar::ck3_121003::build26785313 {
inline constexpr char kGameVersion[]="1.21.0.3";
inline constexpr char kSteamBuildId[]="26785313";
inline constexpr char kAdapterId[]="ck3-1.21.0.3-26785313-msvc-x64";
inline constexpr char kExecutableSha256[]="859F0D380098ADCB130EB9D453458222749FCDF6D46126AD0ED99D78F9A0AA28";
inline constexpr std::size_t kExecutableFileBytes=114758264;
inline constexpr std::uintptr_t kImageSize=0x6FE5000;
inline constexpr std::uint32_t kPeTimestamp=1795091113;
inline constexpr std::uintptr_t kGameStateSlotRva=0x68B2090;
inline constexpr std::uintptr_t kJominiStateSlotRva=0x68B3B00;
inline constexpr std::uintptr_t kCharacterStorageSlotRva=0x68A8928;
inline constexpr std::uintptr_t kGetLocalPlayerRva=0x3E65760;
inline constexpr std::uintptr_t kTlsFlagRva=0x695940C;
inline constexpr std::uintptr_t kTlsGetterRva=0x44FED60;
inline constexpr std::uintptr_t kPeekMessageWIatRva=0x49D8DE8;
inline constexpr std::uintptr_t kPeekReturnRva=0x4704920;
inline constexpr std::uintptr_t kRngWrapperSlotRva=0x5D559B8;
// This profile is independent. Do not add its SHA to old ImageBuildForSha:
// other old binders must continue to reject it.
struct ReadonlyBindings {
  bool exact_image_admitted=false;
  std::uintptr_t module_base=0;
  ck3_1210::CoreBindings core{};
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
  bool offline_fixture=false;
#endif
};
struct RawResources {
  std::int64_t personal_gold_raw=0,prestige_raw=0,piety_raw=0;
  std::int32_t stress_points=0;
  friend bool operator==(const RawResources&,const RawResources&)=default;
};
struct ReadonlyObservation {
  bool available=false;
  bool partial=true;
  bool main_owner_observed=false;
  bool offline_fixture=false;
  ck3_1210::CoreSnapshotPrefix core{};
  std::optional<RawResources> raw_resources;
  std::optional<GuiRootIndexV1> gui_root_index;
  std::optional<GuiWindowV1> gui_window;
  std::optional<RiteDraftV2> rite_draft;
  // Bounded named-widget data is independent of Full, actions and Core-only mode1.
  std::uint32_t core_read_attempts=0;
  std::string_view unavailable_reason="not_read";
};
enum class ReadonlyModeV1 { core_and_raw_resources, core_only, core_and_gui_root_index, core_and_gui_window, core_and_rite_draft_costs };
struct ReadonlyContext {
  ReadonlyBindings bindings{};
  ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  ReadonlyObservation observation{};
  // The production Core route must not read raw financial/resource storage.
  ReadonlyModeV1 mode=ReadonlyModeV1::core_and_raw_resources;
  std::optional<GuiRootIndexRequestV1> gui_root_request;
  std::optional<GuiWindowRequestV1> gui_window_request;
  std::optional<RiteDraftRequestV2> rite_draft_request;
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
  RiteDraftNativeFixtureV2 *rite_draft_fixture=nullptr;
#endif
};
struct ImagePin {std::uintptr_t rva;std::span<const unsigned char> bytes;};
std::span<const ImagePin> ReadonlyImagePins() noexcept;
std::span<const ImagePin> GuiRootIndexImagePinsV1() noexcept;
bool VerifyGuiRootIndexImageV1(std::uintptr_t image_base) noexcept;
std::span<const ImagePin> GuiWindowImagePinsV1() noexcept;
bool VerifyGuiWindowImageV1(std::uintptr_t image_base) noexcept;
std::span<const ImagePin> RiteDraftImagePinsV2() noexcept;
bool VerifyRiteDraftImageV2(std::uintptr_t image_base) noexcept;
bool VerifyReadonlyImage(std::uintptr_t image_base) noexcept;
ReadonlyBindings BindReadonlyImage(std::uintptr_t image_base,std::string_view sha256) noexcept;
const ck3_11906::MainThreadQueryBuildProfileV1 &ReadonlyThreadProfile() noexcept;
// The independent default-OFF Core route supplies its own capability and exact identity.
bool ExecuteReadonlyOnOwner(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
// Present only in the finite NoGame executable, never a production DLL.
ReadonlyBindings NoGameBindings(std::uintptr_t verified_image,ck3_1210::CoreBindings core) noexcept;
#endif
} // namespace xar::ck3_121003::build26785313
