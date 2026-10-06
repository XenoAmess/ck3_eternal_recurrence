# Existing adopted ON route migration; no new feature or action permission.
# Root includes this leaf after the shared runtime and ordinary legacy targets.
if(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE
    src/ck3_12004_clergy_appointment.cpp
    src/ck3_12004_county_conversion.cpp
    src/ck3_12004_county_conversion_task_action_v1.cpp)
endif()

if(BUILD_TESTING AND WIN32 AND
   XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
  # These old direct-source targets now reference the independent actual4 leaf
  # from the shared owning mailbox. Import its real runtime definitions; this
  # only repairs link closure and does not replay old fixtures.
  foreach(clergy_legacy_target IN ITEMS
      xar_r3_clergy_named_test
      xar_ck3_12003_county_conversion_clergy_full_wire_test
      xar_ck3_12003_clergy_candidate_terms_whole_mailbox_test)
    if(TARGET ${clergy_legacy_target})
      target_link_libraries(${clergy_legacy_target} PRIVATE
        xar_ck3_12002_runtime)
    endif()
  endforeach()

  add_executable(xar_ck3_12004_clergy_appointment_whole_mailbox_test
    src/ck3_12004_clergy_appointment_whole_mailbox_test.cpp)
  target_include_directories(xar_ck3_12004_clergy_appointment_whole_mailbox_test
    PRIVATE include)
  target_compile_features(xar_ck3_12004_clergy_appointment_whole_mailbox_test
    PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_clergy_appointment_whole_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1=1)
  target_link_libraries(xar_ck3_12004_clergy_appointment_whole_mailbox_test PRIVATE
    xar_bridge_protocol xar_ck3_12002_runtime user32 bcrypt)
  if(MSVC)
    target_compile_options(xar_ck3_12004_clergy_appointment_whole_mailbox_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8 /Gy)
    target_link_options(xar_ck3_12004_clergy_appointment_whole_mailbox_test PRIVATE
      /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12004_clergy_appointment_whole_mailbox_first
    COMMAND xar_ck3_12004_clergy_appointment_whole_mailbox_test
      "${CMAKE_CURRENT_BINARY_DIR}/clergy-appointment-12004-whole-wire")

  add_executable(xar_ck3_12004_county_conversion_whole_mailbox_test
    src/ck3_12004_county_conversion_whole_mailbox_test.cpp)
  target_include_directories(xar_ck3_12004_county_conversion_whole_mailbox_test
    PRIVATE include)
  target_compile_features(xar_ck3_12004_county_conversion_whole_mailbox_test
    PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_county_conversion_whole_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1=1)
  target_link_libraries(xar_ck3_12004_county_conversion_whole_mailbox_test PRIVATE
    xar_bridge_protocol xar_ck3_12002_runtime user32 bcrypt)
  if(MSVC)
    target_compile_options(xar_ck3_12004_county_conversion_whole_mailbox_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8 /Gy)
    target_link_options(xar_ck3_12004_county_conversion_whole_mailbox_test PRIVATE
      /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12004_county_conversion_whole_mailbox_first
    COMMAND xar_ck3_12004_county_conversion_whole_mailbox_test
      "${CMAKE_CURRENT_BINARY_DIR}/county-conversion-12004-whole-wire")
endif()
