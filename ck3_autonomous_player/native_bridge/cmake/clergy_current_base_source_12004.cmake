# Qualified Clergy copied-input providers; original native_can_fire/query stay registered as before.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/clergy_task_block_31b4810_12004.cpp
  src/clergy_position_check_31bd1a0_12004.cpp
  src/root_scope_initializer_889f60_12004.cpp
  src/clergy_shared_condition_31bdda0_12004.cpp
  src/clergy_mode0_task_raw_al_31b4a10_12004.cpp)

# Actual standalone compound closed with these twelve TUs only; no old case/provider archive.
if(BUILD_TESTING AND WIN32)
  add_executable(clergy_current_base_source_compound EXCLUDE_FROM_ALL
    src/clergy_task_block_31b4810_12004.cpp
    tests/clergy_task_block_31b4810_12004_new_cases.cpp
    tests/clergy_position_raw_al_31bde90_12004_new_cases.cpp
    src/clergy_position_check_31bd1a0_12004.cpp
    tests/clergy_position_check_31bd1a0_12004_new_cases.cpp
    src/root_scope_initializer_889f60_12004.cpp
    tests/root_scope_initializer_889f60_new_cases_12004.cpp
    src/clergy_shared_condition_31bdda0_12004.cpp
    src/clergy_shared_condition_31bdda0_12004_connected_cases.cpp
    src/clergy_mode0_task_raw_al_31b4a10_12004.cpp
    tests/clergy_mode0_task_raw_al_31b4a10_12004_newcases.cpp
    tests/clergy_current_base_source_compound.cpp)
  target_include_directories(clergy_current_base_source_compound PRIVATE include)
  target_compile_features(clergy_current_base_source_compound PRIVATE cxx_std_20)
  target_compile_definitions(clergy_current_base_source_compound PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE NDEBUG)
  if(MSVC)
    set_property(TARGET clergy_current_base_source_compound PROPERTY MSVC_RUNTIME_LIBRARY MultiThreadedDLL)
    target_compile_options(clergy_current_base_source_compound PRIVATE
      /O2 /Ob2 /EHsc /W4 /WX /permissive- /utf-8)
  endif()
  # This preserves the qualified Require-based fixture profile and does not auto-run it.
endif()
