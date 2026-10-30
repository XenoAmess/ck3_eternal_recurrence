# Raw private IDs keep their ABI bits through the complete gift route.
if(BUILD_TESTING AND WIN32 AND
   XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  foreach(kind IN ITEMS whole controls)
    set(target xar_ck3_12004_faction_gift_raw_identity_${kind}_test)
    add_executable(${target}
      tests/ck3_12004_faction_gift_raw_identity_${kind}_test.cpp
      src/ck3_12004_faction_gift_router.cpp)
    # Keep the router TU under the fixture's transport aliases; all other
    # providers come from the actual Bridge object set without source duplicates.
    target_sources(${target} PRIVATE
      "$<FILTER:$<TARGET_OBJECTS:xar_ck3_bridge>,EXCLUDE,(^|[/\\\\])ck3_12004_faction_gift_router[.]cpp[.](obj|o)$>")
    target_link_libraries(${target} PRIVATE
      xar_ck3_12002_runtime xar_bridge_protocol bcrypt user32
      $<TARGET_PROPERTY:xar_ck3_bridge,LINK_LIBRARIES>)
    target_include_directories(${target} PRIVATE include)
    target_compile_features(${target} PRIVATE cxx_std_20)
    target_compile_definitions(${target} PRIVATE
      $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
      TrySubmitMainThreadQueryV1=FactionIdentityFixtureSubmit12004
      WaitForMainThreadQueryV1=FactionIdentityFixtureWait12004
      ReclaimMainThreadQueryV1=FactionIdentityFixtureReclaim12004)
    if(MSVC)
      target_compile_options(${target} PRIVATE
        /W4 /permissive- /EHsc /UNDEBUG /utf-8)
    endif()
  endforeach()
  add_test(NAME xar_ck3_12004_faction_gift_raw_identity_positive
    COMMAND xar_ck3_12004_faction_gift_raw_identity_whole_test 50331649 67108866
      "${CMAKE_CURRENT_BINARY_DIR}/faction-gift-raw-identity/positive")
  add_test(NAME xar_ck3_12004_faction_gift_raw_identity_actor_zero
    COMMAND xar_ck3_12004_faction_gift_raw_identity_whole_test 0 67108866
      "${CMAKE_CURRENT_BINARY_DIR}/faction-gift-raw-identity/actor_zero")
  add_test(NAME xar_ck3_12004_faction_gift_raw_identity_recipient_zero
    COMMAND xar_ck3_12004_faction_gift_raw_identity_whole_test 50331649 0
      "${CMAKE_CURRENT_BINARY_DIR}/faction-gift-raw-identity/recipient_zero")
  add_test(NAME xar_ck3_12004_faction_gift_raw_identity_actor_min
    COMMAND xar_ck3_12004_faction_gift_raw_identity_whole_test 2147483648 67108866
      "${CMAKE_CURRENT_BINARY_DIR}/faction-gift-raw-identity/actor_min")
  add_test(NAME xar_ck3_12004_faction_gift_raw_identity_recipient_min
    COMMAND xar_ck3_12004_faction_gift_raw_identity_whole_test 50331649 2147483648
      "${CMAKE_CURRENT_BINARY_DIR}/faction-gift-raw-identity/recipient_min")
  add_test(NAME xar_ck3_12004_faction_gift_raw_identity_both_high
    COMMAND xar_ck3_12004_faction_gift_raw_identity_whole_test 4278190081 2147483650
      "${CMAKE_CURRENT_BINARY_DIR}/faction-gift-raw-identity/both_high")
  add_test(NAME xar_ck3_12004_faction_gift_raw_identity_controls_actor_zero
    COMMAND xar_ck3_12004_faction_gift_raw_identity_controls_test 0 67108866
      "${CMAKE_CURRENT_BINARY_DIR}/faction-gift-raw-identity/controls-actor_zero")
  add_test(NAME xar_ck3_12004_faction_gift_raw_identity_controls_recipient_zero
    COMMAND xar_ck3_12004_faction_gift_raw_identity_controls_test 50331649 0
      "${CMAKE_CURRENT_BINARY_DIR}/faction-gift-raw-identity/controls-recipient_zero")
  add_test(NAME xar_ck3_12004_faction_gift_raw_identity_controls_both_high
    COMMAND xar_ck3_12004_faction_gift_raw_identity_controls_test 4278190081 2147483650
      "${CMAKE_CURRENT_BINARY_DIR}/faction-gift-raw-identity/controls-both_high")
endif()
