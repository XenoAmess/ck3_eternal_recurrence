# SOURCE_PREPARED / NOTRUN. Include after both existing owning targets exist.
# These are actual .4 native TUs; the existing software DTOs, candidate policy,
# full receipt serializer and shared command/core/envelope foundations are reused.
if(XAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE
    src/ck3_12004_construction.cpp
    src/ck3_12004_construction_held.cpp
    src/ck3_12004_construction_process.cpp
    src/ck3_12004_construction_submit_binding.cpp)
  target_sources(xar_ck3_bridge PRIVATE
    src/ck3_12004_construction_mailbox.cpp)
endif()
