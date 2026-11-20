# Private readonly producer scope; it adds no capability or public mailbox ABI.
option(XAR_CK3_ENABLE_26757580_OBSERVER_SCOPE92
  "Enable the exact26757580 registered native snapshot observer read scope" OFF)
if(XAR_CK3_ENABLE_26757580_OBSERVER_SCOPE92)
  # Keep unrelated object flags unchanged. All users of the private TLS header
  # belong to these three production translation units.
  foreach(_observer92_source IN ITEMS
      main_thread_query_mailbox_v1.cpp
      ck3_12002_semantic_adapter.cpp
      ck3_1210_adapter.cpp)
    set_property(SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/src/${_observer92_source}"
      APPEND PROPERTY COMPILE_DEFINITIONS
      XAR_CK3_ENABLE_26757580_OBSERVER_SCOPE92=1)
  endforeach()
  unset(_observer92_source)
endif()
