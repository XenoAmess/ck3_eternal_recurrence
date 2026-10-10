# Existing Knight consumption calls these providers even when automatic installation is off.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/person_natural_lineage_clock_12004.cpp
  src/person_installed_transfer_capture_12004.cpp
  src/person_installed_transfer_capture_12004_serializer.cpp)

option(XAR_BRIDGE_ENABLE_12004_PERSON_INSTALLED_TRANSFER_CAPTURE
  "Install actual4 person transfer capture through the bridge startup path" ON)
if(XAR_BRIDGE_ENABLE_12004_PERSON_INSTALLED_TRANSFER_CAPTURE)
  target_compile_definitions(xar_ck3_12002_runtime PUBLIC
    XAR_BRIDGE_ENABLE_12004_PERSON_INSTALLED_TRANSFER_CAPTURE=1)
endif()

if(BUILD_TESTING AND WIN32)
  add_executable(person_installed_transfer_capture_12004_test EXCLUDE_FROM_ALL
    tests/person_installed_transfer_capture_12004_test.cpp)
  target_link_libraries(person_installed_transfer_capture_12004_test PRIVATE
    xar_ck3_12002_runtime kernel32)
  target_include_directories(person_installed_transfer_capture_12004_test PRIVATE include)
  target_compile_features(person_installed_transfer_capture_12004_test PRIVATE cxx_std_20)
  target_compile_definitions(person_installed_transfer_capture_12004_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(person_installed_transfer_capture_12004_test PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
  add_test(NAME person_installed_transfer_capture_12004
    COMMAND $<TARGET_FILE:person_installed_transfer_capture_12004_test>)
endif()
