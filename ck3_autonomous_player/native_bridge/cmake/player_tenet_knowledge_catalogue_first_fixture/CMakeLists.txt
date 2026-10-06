cmake_minimum_required(VERSION 3.24)
project(xar_player_tenet_knowledge_catalogue_first_fixture LANGUAGES CXX)
get_filename_component(XAR_TENET_KNOWLEDGE_DEFAULT_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../../.." ABSOLUTE)
set(XAR_TENET_KNOWLEDGE_SOURCE_ROOT "${XAR_TENET_KNOWLEDGE_DEFAULT_ROOT}" CACHE PATH "Applied candidate repository root")
set(XAR_TENET_KNOWLEDGE_RUNTIME_LIBRARY "" CACHE FILEPATH "Root-built real xar_ck3_12002_runtime library")
if(NOT XAR_TENET_KNOWLEDGE_RUNTIME_LIBRARY)
  message(FATAL_ERROR "Pass the real xar_ck3_12002_runtime library built with this candidate and Tenet query enabled")
endif()
set(native "${XAR_TENET_KNOWLEDGE_SOURCE_ROOT}/ck3_autonomous_player/native_bridge")
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_library(xar_tenet_knowledge_actual_runtime STATIC IMPORTED)
set_target_properties(xar_tenet_knowledge_actual_runtime PROPERTIES
  IMPORTED_LOCATION "${XAR_TENET_KNOWLEDGE_RUNTIME_LIBRARY}")
add_executable(xar_ck3_12003_player_tenet_knowledge_catalogue_mailbox_test
  "${native}/src/protocol.cpp"
  "${native}/src/ck3_12002.cpp"
  "${native}/src/ck3_12002_query_mailbox.cpp"
  "${native}/src/ck3_12003_abi_profile.cpp"
  "${native}/src/ck3_12003_adapter.cpp"
  "${native}/src/main_thread_query_mailbox_v1.cpp"
  "${native}/src/ck3_12002_religion_context.cpp"
  "${native}/src/religion_doctrine12002_tenet_rows.cpp"
  "${native}/src/ck3_12003_target_rite_tenet_comparison.cpp"
  "${native}/src/ck3_12003_player_tenet_knowledge_catalogue.cpp"
  "${native}/src/religion_reform12002_tenet_sources.cpp"
  "${native}/src/religion_reform12002_window.cpp"
  "${native}/src/religion_doctrine12002_tenet_rows_mailbox.cpp"
  "${native}/src/ck3_12003_player_tenet_knowledge_catalogue_mailbox_test.cpp")
target_include_directories(xar_ck3_12003_player_tenet_knowledge_catalogue_mailbox_test PRIVATE "${native}/include")
target_link_libraries(xar_ck3_12003_player_tenet_knowledge_catalogue_mailbox_test PRIVATE
  xar_tenet_knowledge_actual_runtime user32 bcrypt)
target_compile_definitions(xar_ck3_12003_player_tenet_knowledge_catalogue_mailbox_test PRIVATE
  NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1=1
  XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1)
if(MSVC)
  target_compile_options(xar_ck3_12003_player_tenet_knowledge_catalogue_mailbox_test PRIVATE
    /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8 /Gy)
  target_link_options(xar_ck3_12003_player_tenet_knowledge_catalogue_mailbox_test PRIVATE /OPT:REF)
endif()
enable_testing()
add_test(NAME xar_ck3_12003_player_tenet_knowledge_catalogue_mailbox_test
  COMMAND xar_ck3_12003_player_tenet_knowledge_catalogue_mailbox_test
    "${CMAKE_BINARY_DIR}/player-tenet-knowledge-catalogue-wire")
