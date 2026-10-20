# Qualification consumers only. Production allON runtime/DLL are built once.
# No provider capability, fixture callback or alternate worker enters runtime.
if(BUILD_TESTING AND WIN32)
  function(_b11_consumer target)
    add_executable(${target} EXCLUDE_FROM_ALL ${ARGN})
    target_compile_features(${target} PRIVATE cxx_std_20)
    target_include_directories(${target} PRIVATE include src tests src/ghw_permission_observer)
    target_compile_definitions(${target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    set_target_properties(${target} PROPERTIES INTERPROCEDURAL_OPTIMIZATION FALSE)
    if(MSVC)
      target_compile_options(${target} PRIVATE /UNDEBUG /Od /Ob0 /GL- /W4 /EHsc /permissive- /utf-8)
      target_link_options(${target} PRIVATE /DEBUG:NONE /INCREMENTAL:NO /LTCG:OFF)
    endif()
  endfunction()
  _b11_consumer(xar_ck3_12004_b11_shared_mailbox_cohort
    tests/b11_shared_mailbox_cohort.cpp)
  target_link_libraries(xar_ck3_12004_b11_shared_mailbox_cohort PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol user32 bcrypt)

  # These exact profiles cover the production classifier/Populate/Register TUs.
  # Actual provider library stays allON. Other production ABI feature definitions
  # are inherited consistently; each wrapper undefines just these five flags and
  # byte-includes its unchanged real .cpp in THIS final frozen source snapshot.
  foreach(_profile IN ITEMS off:0 artifact_read:1 artifact_action:3 ghw:4 actor:8 inventory:16)
    string(REPLACE ":" ";" _pair "${_profile}")
    list(GET _pair 0 _name)
    list(GET _pair 1 _mask)
    set(_target xar_ck3_12004_b11_gates_${_name})
    _b11_consumer(${_target}
      tests/b11_five_flag_consumer.cpp
      tests/b11_gate_router_profile.cpp
      tests/b11_gate_registrar_profile.cpp
      tests/b11_gate_provider_profile.cpp)
    target_compile_definitions(${_target} PRIVATE XAR_B11_PROFILE_MASK=${_mask})
    target_link_libraries(${_target} PRIVATE
      xar_ck3_12002_runtime xar_bridge_protocol user32 bcrypt)
  endforeach()
  # Separate actual factory source with all five flags absent. Never links the
  # allON factory object. This target proves only compile/invalid-context guards.
  _b11_consumer(xar_ck3_12004_b11_actor_factory_off
    tests/b11_actor_factory_guard.cpp tests/b11_actor_factory_off.cpp)
  target_compile_definitions(xar_ck3_12004_b11_actor_factory_off PRIVATE XAR_B11_PROFILE_MASK=0)
endif()
