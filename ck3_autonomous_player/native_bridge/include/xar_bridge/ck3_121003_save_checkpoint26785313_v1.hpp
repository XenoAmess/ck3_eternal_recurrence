#pragma once
#include "xar_bridge/ck3_121003_commands26785313_v1.hpp"
#include "xar_bridge/ck3_1210_core_control_v1.hpp"
#include <array>
#include <string>

namespace xar::ck3_121003::build26785313 {
inline constexpr char kSaveCheckpointSchema267V1[]="ck3_121003_core_checkpoint_save_v1";
inline constexpr char kSaveCheckpointResultSchema267V1[]="ck3_121003_core_checkpoint_save_result_v1";
inline constexpr char kSaveCheckpointCapability267V1[]="game.command.current-core-checkpoint-save.v1";
inline constexpr char kSaveCheckpointStep267V1[]="save-checkpoint";
inline constexpr char kSaveCheckpointBackend267V1[]="ck3-1.21.0.3-native-headless-main-thread";
inline constexpr char kSaveCheckpointFilename267V1[]="xar_checkpoint.ck3";
inline constexpr std::size_t kSaveCheckpointRetainedClaims267V1=64;

struct SaveCheckpointRequest267V1 {
  ck3_1210::CoreControlRequestV1 control{};
  std::array<char,97> request_id{};
  std::uint8_t request_id_size=0;
  std::string_view id() const noexcept {return {request_id.data(),request_id_size};}
};
enum class SaveCheckpointStatus267V1 {
  unavailable,expired,stale_core,requires_paused_map_living,claim_consumed,
  source_changed,capacity_exhausted,submitted,rejected,indeterminate
};
enum class SaveCheckpointClaimDecision267V1 { ready,invalid,consumed,source_changed,capacity_exhausted };
struct SaveCheckpointResult267V1 {
  SaveCheckpointStatus267V1 status=SaveCheckpointStatus267V1::unavailable;
  bool effect_attempted=false;
  std::uint64_t submission_sequence=0;
  ck3_1210::CoreSnapshotPrefix observed{};
};
// Internal source key, populated only from the verified current owner stamp.
// It is not a new request/transport authority field.
struct SaveCheckpointSource267V1 {
  std::uintptr_t module_base=0,game_state=0,jomini_state=0;
  std::uint64_t connection_generation=0;
};
class SaveCheckpointSession267V1 {
 public:
  SaveCheckpointSession267V1() noexcept=default;
  SaveCheckpointSession267V1(const SaveCheckpointSession267V1&)=delete;
  SaveCheckpointSession267V1&operator=(const SaveCheckpointSession267V1&)=delete;
  std::size_t claim_count() const noexcept {return size_;}
  bool unknown_blocked() const noexcept {return unknown_;}
 private:
  struct Claim {
    SaveCheckpointRequest267V1 request{};
    SaveCheckpointSource267V1 source{};
    SaveCheckpointStatus267V1 status=SaveCheckpointStatus267V1::indeterminate;
  };
  // Process-lifetime owner-only custody. No connection reset or retirement API.
  std::array<Claim,kSaveCheckpointRetainedClaims267V1> claims_{};
  std::size_t size_=0;
  bool unknown_=false;
  friend SaveCheckpointClaimDecision267V1 InspectSaveCheckpointClaim267V1(
      const SaveCheckpointSession267V1&,const SaveCheckpointRequest267V1&,
      const SaveCheckpointSource267V1&) noexcept;
  friend SaveCheckpointClaimDecision267V1 ClaimSaveCheckpoint267V1(
      SaveCheckpointSession267V1&,const SaveCheckpointRequest267V1&,
      const SaveCheckpointSource267V1&,std::uint64_t&) noexcept;
  friend void FinishSaveCheckpointClaim267V1(SaveCheckpointSession267V1&,
      std::uint64_t,SaveCheckpointStatus267V1) noexcept;
  friend void BlockSaveCheckpointUnknown267V1(SaveCheckpointSession267V1&) noexcept;
};
bool SaveCheckpointRequestShape267V1(const SaveCheckpointRequest267V1&) noexcept;
// Pure claim bookkeeping only; none of these functions proves owner or dispatches.
SaveCheckpointClaimDecision267V1 InspectSaveCheckpointClaim267V1(
    const SaveCheckpointSession267V1&,const SaveCheckpointRequest267V1&,
    const SaveCheckpointSource267V1&) noexcept;
SaveCheckpointClaimDecision267V1 ClaimSaveCheckpoint267V1(SaveCheckpointSession267V1&,
    const SaveCheckpointRequest267V1&,const SaveCheckpointSource267V1&,
    std::uint64_t &sequence) noexcept;
void FinishSaveCheckpointClaim267V1(SaveCheckpointSession267V1&,
    std::uint64_t sequence,SaveCheckpointStatus267V1) noexcept;
void BlockSaveCheckpointUnknown267V1(SaveCheckpointSession267V1&) noexcept;

struct SaveCheckpointContext267V1 {
  ReadonlyBindings bindings{};
  ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  SaveCheckpointRequest267V1 request{};
  SaveCheckpointSession267V1 *session=nullptr;
  SaveCheckpointResult267V1 result{};
  std::uint64_t connection_generation=0,monotonic_deadline_ms=0;
  bool command_ownership_entered=false;
};
void ArmSaveCheckpointDeadline267V1(SaveCheckpointContext267V1&) noexcept;
bool ExecuteSaveCheckpointOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
// Fixed role, like ApplicationExit's secondary owner reader. No arbitrary callback.
bool ReadSaveCheckpointCoreOnOwner267V1(const ReadonlyBindings&,
    ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
    const ck3_11906::MainThreadExecutionStampV1&,void *actual_context,ReadonlyObservation&) noexcept;
bool SaveCheckpointRouteEnabled267V1(const game::AdapterDescriptor&) noexcept;
bool ParseSaveCheckpointRequest267V1(std::string_view,SaveCheckpointRequest267V1&) noexcept;
std::string SerializeSaveCheckpointResult267V1(std::string_view,const SaveCheckpointResult267V1&);
} // namespace xar::ck3_121003::build26785313
