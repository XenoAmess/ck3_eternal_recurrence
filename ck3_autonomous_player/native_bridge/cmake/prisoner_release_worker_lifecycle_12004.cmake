# Production code is the existing mailbox TU plus the new inline header.
if(BUILD_TESTING)
  add_executable(ck3_12004_prisoner_release_worker_lifecycle_first
    tests/ck3_12004_prisoner_release_worker_lifecycle_first.cpp)
  target_include_directories(ck3_12004_prisoner_release_worker_lifecycle_first
    PRIVATE include src research)
  target_compile_features(ck3_12004_prisoner_release_worker_lifecycle_first PRIVATE cxx_std_20)
  target_sources(ck3_12004_prisoner_release_worker_lifecycle_first PRIVATE
    $<TARGET_OBJECTS:xar_ck3_bridge>)
  get_target_property(_lifecycle_links xar_ck3_bridge LINK_LIBRARIES)
  target_link_libraries(ck3_12004_prisoner_release_worker_lifecycle_first
    PRIVATE xar_ck3_12002_runtime xar_bridge_protocol bcrypt ${_lifecycle_links})
  if(MSVC)
    target_compile_options(ck3_12004_prisoner_release_worker_lifecycle_first PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  else()
    target_compile_options(ck3_12004_prisoner_release_worker_lifecycle_first PRIVATE
      -UNDEBUG -Wall -Wextra -Werror)
  endif()
  add_test(NAME ck3_12004_prisoner_release_worker_lifecycle_first
    COMMAND $<TARGET_FILE:ck3_12004_prisoner_release_worker_lifecycle_first>
      "${CMAKE_CURRENT_BINARY_DIR}/wire/prisoner-release-lifecycle-first")
endif()
