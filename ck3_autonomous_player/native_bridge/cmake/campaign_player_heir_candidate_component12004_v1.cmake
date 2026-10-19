# Future clean whole-DLL adoption only. Does not alter frozen Native29 inputs.
option(XAR_CK3_ENABLE_G2_PLAYER_HEIR_CANDIDATE_COMPONENT12004_V1
  "Attach source-bound player-heir observation to the existing .4 root query" OFF)
if(XAR_CK3_ENABLE_G2_PLAYER_HEIR_CANDIDATE_COMPONENT12004_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE
    src/ck3_12004_player_heir_candidate_v1.cpp
    src/campaign_player_heir_candidate_component12004_v1.cpp
    src/campaign_player_heir_candidate_component12004_v1_serializer.cpp)
  target_compile_definitions(xar_ck3_12002_runtime PUBLIC
    XAR_CK3_ENABLE_PLAYER_HEIR_CANDIDATE12004_V1=1
    XAR_CK3_ENABLE_CAMPAIGN_ROOT_PLAYER_HEIR_CANDIDATE12004_V1=1)
endif()
