# Physical postimages are consumed by existing unguarded retained/Knight providers.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/person_transfer_postimage_capture_12004.cpp
  src/person_transfer_keys_snapshot_12004.cpp
  src/person_transfer_values_snapshot_12004.cpp
  src/person_transfer_block248_snapshot_adapter_12004.cpp
  src/person_transfer_postimage_12004_serializer.cpp)

if(BUILD_TESTING AND WIN32)
  # The29 fragment exports cases and shares the sole new13c main.
  add_executable(person_installed_transfer_physical_capture_12004_test EXCLUDE_FROM_ALL
    tests/person_installed_transfer_physical_capture_12004_test.cpp
    src/person_transfer_postimage_capture_12004_test.cpp)
  target_link_libraries(person_installed_transfer_physical_capture_12004_test PRIVATE
    xar_ck3_12002_runtime kernel32)
  target_include_directories(person_installed_transfer_physical_capture_12004_test PRIVATE include)
  target_compile_features(person_installed_transfer_physical_capture_12004_test PRIVATE cxx_std_20)
  target_compile_definitions(person_installed_transfer_physical_capture_12004_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(person_installed_transfer_physical_capture_12004_test PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
  add_test(NAME person_installed_transfer_physical_capture_12004
    COMMAND $<TARGET_FILE:person_installed_transfer_physical_capture_12004_test>)
endif()
