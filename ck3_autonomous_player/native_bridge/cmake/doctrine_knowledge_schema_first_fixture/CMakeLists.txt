cmake_minimum_required(VERSION 3.24)
project(xar_doctrine_knowledge_schema_first_fixture LANGUAGES CXX)
get_filename_component(XAR_DOCTRINE_SCHEMA_DEFAULT_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../../.." ABSOLUTE)
set(XAR_DOCTRINE_SCHEMA_SOURCE_ROOT "${XAR_DOCTRINE_SCHEMA_DEFAULT_ROOT}" CACHE PATH "Applied candidate repository root")
set(XAR_DOCTRINE_SCHEMA_RUNTIME_LIBRARY "" CACHE FILEPATH "Root-built real xar_ck3_12002_runtime library")
if(NOT XAR_DOCTRINE_SCHEMA_RUNTIME_LIBRARY)
  message(FATAL_ERROR "Pass the actual xar_ck3_12002_runtime library built with DoctrineKnowledge enabled")
endif()
set(native "${XAR_DOCTRINE_SCHEMA_SOURCE_ROOT}/ck3_autonomous_player/native_bridge")
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_library(xar_doctrine_schema_actual_runtime STATIC IMPORTED)
set_target_properties(xar_doctrine_schema_actual_runtime PROPERTIES
  IMPORTED_LOCATION "${XAR_DOCTRINE_SCHEMA_RUNTIME_LIBRARY}")
add_executable(xar_ck3_12003_doctrine_knowledge_schema_mailbox_test
  "${native}/src/protocol.cpp"
  "${native}/src/ck3_12002.cpp"
  "${native}/src/ck3_12002_query_mailbox.cpp"
  "${native}/src/ck3_12003_abi_profile.cpp"
  "${native}/src/ck3_12003_adapter.cpp"
  "${native}/src/main_thread_query_mailbox_v1.cpp"
  "${native}/src/ck3_12002_religion_context.cpp"
  "${native}/src/religion_doctrine12002_intrinsic.cpp"
  "${native}/src/religion_doctrine12002_choices.cpp"
  "${native}/src/religion_doctrine12002_choices_mailbox.cpp"
  "${native}/src/ck3_12003_doctrine_knowledge_schema_mailbox_test.cpp")
target_include_directories(xar_ck3_12003_doctrine_knowledge_schema_mailbox_test PRIVATE "${native}/include")
target_link_libraries(xar_ck3_12003_doctrine_knowledge_schema_mailbox_test PRIVATE
  xar_doctrine_schema_actual_runtime user32 bcrypt)
target_compile_definitions(xar_ck3_12003_doctrine_knowledge_schema_mailbox_test PRIVATE
  NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1=1)
if(MSVC)
  target_compile_options(xar_ck3_12003_doctrine_knowledge_schema_mailbox_test PRIVATE
    /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8 /Gy)
  target_link_options(xar_ck3_12003_doctrine_knowledge_schema_mailbox_test PRIVATE /OPT:REF)
endif()
enable_testing()
add_test(NAME xar_ck3_12003_doctrine_knowledge_schema_mailbox_test
  COMMAND xar_ck3_12003_doctrine_knowledge_schema_mailbox_test
    "${CMAKE_BINARY_DIR}/doctrine-knowledge-schema-12003-wire")
