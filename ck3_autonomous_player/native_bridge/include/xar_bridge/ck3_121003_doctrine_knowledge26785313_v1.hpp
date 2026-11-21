#pragma once
#include "xar_bridge/ck3_121003_doctrine_key26785313_v1.hpp"

namespace xar::ck3_121003::build26785313 {
inline constexpr std::uintptr_t kKnowsDoctrineNativeRva267V1=0x2D96170;
enum class RawDoctrineKnowledgeStatus267V1 { unavailable,native_true,pam_unresolved };
struct RawDoctrineKnowledge267V1 {
  RawDoctrineKnowledgeStatus267V1 status=RawDoctrineKnowledgeStatus267V1::unavailable;
  std::int32_t actor_id=-1;
  DoctrineInternalKey267V1 exact_doctrine;
};
std::span<const ImagePin> DoctrineKnowledgeImagePins267V1() noexcept;
bool VerifyDoctrineKnowledgeImage267V1(std::uintptr_t image_base) noexcept;
// Independent defaultOFF raw predicate only. Not an owner/token/capability.
// The actual fixed Select executor must supply its own current double-Core,
// owner/TLS/deadline/generation checks and typed current item->doctrine/key chain.
// No request or caller supplies a knowledge/perk boolean.
RawDoctrineKnowledge267V1 ReadRawKnowsDoctrine267V1(const ReadonlyBindings&,
    std::uintptr_t actual_actor,std::uintptr_t typed_doctrine) noexcept;
} // namespace xar::ck3_121003::build26785313
