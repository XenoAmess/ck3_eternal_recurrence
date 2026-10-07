cmake_minimum_required(VERSION 3.24)

# AUTHORED_NOTRUN. The selected native tree must already contain the Root-owned
# M7 observer/header/capture/mailbox/router projection. This leaf changes no
# shared source list and introduces no stand-in production definitions.
if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
  project(xar_crown_authority_cooldown_whole_fixture_12004 LANGUAGES CXX)
  include(CTest)
  set(XAR_CROWN_NATIVE_SOURCE_DIR "" CACHE PATH
      "Complete actual4 native_bridge source tree with the M7 projection integrated")
  if(NOT XAR_CROWN_NATIVE_SOURCE_DIR)
    message(FATAL_ERROR "Root must select the complete integrated native_bridge source tree")
  endif()
  add_subdirectory("${XAR_CROWN_NATIVE_SOURCE_DIR}"
      "${CMAKE_CURRENT_BINARY_DIR}/production" EXCLUDE_FROM_ALL)
endif()

if(TARGET xar_crown_authority_cooldown_whole_fixture_12004)
  return()
endif()

if(BUILD_TESTING AND WIN32)
  if(NOT TARGET xar_ck3_12002_runtime OR NOT TARGET xar_bridge_protocol)
    message(FATAL_ERROR "The genuine existing runtime and protocol targets are required")
  endif()
  if(NOT XAR_CK3_ENABLE_G2_REALM_LAW_PAUSED_PRIVATE_QUERY_V1)
    message(FATAL_ERROR "Use the existing adopted private realm-law build option")
  endif()
  if(NOT XAR_CROWN_NATIVE_SOURCE_DIR)
    get_filename_component(XAR_CROWN_NATIVE_SOURCE_DIR
        "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
  endif()
  set(XAR_CROWN_WHOLE_OUTPUT_DIR
      "${CMAKE_CURRENT_BINARY_DIR}/crown_authority_cooldown_12004_whole_wires"
      CACHE PATH "Fresh directory for the six compiled M7 whole wires and receipt")
  add_executable(xar_crown_authority_cooldown_whole_fixture_12004
      "${CMAKE_CURRENT_LIST_DIR}/../crown_authority_cooldown_whole_fixture_12004.cpp"
      # The real Capture failure formatter is in this existing value TU, whose
      # object also references the existing active collection implementation.
      # Root registers these in Bridge, not the Runtime library.
      "${XAR_CROWN_NATIVE_SOURCE_DIR}/src/realm_law_candidate_collection_11906.cpp"
      "${XAR_CROWN_NATIVE_SOURCE_DIR}/src/realm_law_active_collection_11906.cpp")
  # The observer is a new owned leaf outside the old ck3_12002*.cpp glob.
  # Compile it here only when the integrated runtime does not already own it.
  get_target_property(crown_runtime_sources xar_ck3_12002_runtime SOURCES)
  set(crown_observer_already_linked FALSE)
  foreach(crown_runtime_source IN LISTS crown_runtime_sources)
    if(crown_runtime_source MATCHES "(^|/)crown_authority_cooldown_observer_12004\\.cpp$")
      set(crown_observer_already_linked TRUE)
    endif()
  endforeach()
  if(NOT crown_observer_already_linked)
    target_sources(xar_crown_authority_cooldown_whole_fixture_12004 PRIVATE
        "${XAR_CROWN_NATIVE_SOURCE_DIR}/src/crown_authority_cooldown_observer_12004.cpp")
  endif()
  target_include_directories(xar_crown_authority_cooldown_whole_fixture_12004
      PRIVATE "${XAR_CROWN_NATIVE_SOURCE_DIR}/include")
  target_compile_features(xar_crown_authority_cooldown_whole_fixture_12004
      PRIVATE cxx_std_20)
  # PUBLIC native feature definitions stay inherited from the actual library.
  target_link_libraries(xar_crown_authority_cooldown_whole_fixture_12004
      PRIVATE xar_bridge_protocol xar_ck3_12002_runtime bcrypt user32)
  target_compile_definitions(xar_crown_authority_cooldown_whole_fixture_12004
      PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_crown_authority_cooldown_whole_fixture_12004
        PRIVATE /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  add_test(NAME crown_authority_cooldown_whole_fixture_12004
      COMMAND xar_crown_authority_cooldown_whole_fixture_12004
          "${XAR_CROWN_WHOLE_OUTPUT_DIR}")
endif()
