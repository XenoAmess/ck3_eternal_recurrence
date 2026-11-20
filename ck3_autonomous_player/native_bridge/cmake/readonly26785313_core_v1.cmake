# Independent default-OFF current-image readonly and Core-only wire route. No Full/GUI/actions.
option(XAR_CK3_ENABLE_121003_26785313_READONLY_V1 "Compile isolated exact26785313 Core/raw-resource owner reader" OFF)
if(XAR_CK3_ENABLE_121003_26785313_READONLY_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_121003_readonly26785313_v1.cpp)
endif()
option(XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1 "Enable exact26785313 paused living-player partial Core wire route only" OFF)
if(XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1)
  if(NOT XAR_CK3_ENABLE_121003_26785313_READONLY_V1)
    target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_121003_readonly26785313_v1.cpp)
  endif()
  target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_121003_core_route26785313_v1.cpp)
  target_compile_definitions(xar_ck3_12002_runtime PUBLIC XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1=1)
endif()
# The bounded internal index is not a GUI tree or an action route/capability.
option(XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1 "Enable exact current Core-bound readonly scripted root index only" OFF)
if(XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1)
  if(NOT XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1)
    message(FATAL_ERROR "Current GUI root index requires the current Core owner route")
  endif()
  set_property(SOURCE src/ck3_121003_readonly26785313_v1.cpp src/ck3_121003_gui_root_index26785313_wire_v1.cpp
      src/game_adapter.cpp src/bridge.cpp APPEND PROPERTY COMPILE_DEFINITIONS
      "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>,$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>>:XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1=1>")
  target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_121003_gui_root_index26785313_wire_v1.cpp)
endif()
option(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1 "Enable independent exact current paused Core normal-application-exit only" OFF)
if(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
  if(NOT XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1)
    message(FATAL_ERROR "Current application exit requires its reviewed current Core owner route")
  endif()
  target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_121003_application_exit26785313_v1.cpp
    src/ck3_121003_application_exit26785313_wire_v1.cpp)
  set_property(SOURCE src/ck3_121003_readonly26785313_v1.cpp src/ck3_121003_core_route26785313_v1.cpp
      src/ck3_121003_application_exit26785313_v1.cpp src/ck3_121003_application_exit26785313_wire_v1.cpp
      src/ck3_121003_personal_gold26785313_v2.cpp src/ck3_1210_adapter.cpp src/game_adapter.cpp src/bridge.cpp
      APPEND PROPERTY COMPILE_DEFINITIONS
      "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>,$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>>:XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1=1>")
endif()
option(XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1 "Enable independent exact current Core-bound named widget tree; no activation" OFF)
if(XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1)
  if(NOT XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1 OR NOT XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1)
    message(FATAL_ERROR "Current named-window reader requires the reviewed current Core and root image profile")
  endif()
  target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_121003_gui_window26785313_wire_v1.cpp)
  set_property(SOURCE src/ck3_121003_readonly26785313_v1.cpp src/ck3_121003_core_route26785313_v1.cpp
      src/ck3_121003_gui_window26785313_wire_v1.cpp src/game_adapter.cpp src/bridge.cpp
      APPEND PROPERTY COMPILE_DEFINITIONS
      "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>,$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>>:XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1=1>")
endif()
option(XAR_CK3_ENABLE_121003_26785313_RITE_DRAFT_V2 "Enable current Core-bound native Rite eligibility/fixed quote logical reads only" OFF)
if(XAR_CK3_ENABLE_121003_26785313_RITE_DRAFT_V2)
  if(NOT XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1 OR NOT XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1)
    message(FATAL_ERROR "Current Rite quote requires exact current Core/named-window owner profile")
  endif()
  target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_121003_rite_draft26785313_wire_v2.cpp)
  set_property(SOURCE src/ck3_121003_readonly26785313_v1.cpp src/ck3_121003_core_route26785313_v1.cpp
      src/ck3_121003_rite_draft26785313_wire_v2.cpp src/game_adapter.cpp src/bridge.cpp
      APPEND PROPERTY COMPILE_DEFINITIONS
      "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>,$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>>:XAR_CK3_ENABLE_121003_26785313_RITE_DRAFT_V2=1>")
endif()
if(BUILD_TESTING)
  add_library(xar_ck3_121003_26785313_core_route_compile OBJECT
    src/ck3_121003_core_route26785313_v1.cpp src/ck3_121003_readonly26785313_v1.cpp
    src/ck3_1210_adapter.cpp src/ck3_1210_core_frame_v1.cpp)
  set_target_properties(xar_ck3_121003_26785313_core_route_compile PROPERTIES EXCLUDE_FROM_ALL TRUE)
  target_include_directories(xar_ck3_121003_26785313_core_route_compile PRIVATE include src)
  target_compile_features(xar_ck3_121003_26785313_core_route_compile PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_121003_26785313_core_route_compile PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1=1)
  add_library(xar_ck3_121003_26785313_core_route_bridge_compile OBJECT src/bridge.cpp)
  set_target_properties(xar_ck3_121003_26785313_core_route_bridge_compile PROPERTIES EXCLUDE_FROM_ALL TRUE)
  target_include_directories(xar_ck3_121003_26785313_core_route_bridge_compile PRIVATE include research src
    $<TARGET_PROPERTY:xar_ck3_bridge,INCLUDE_DIRECTORIES>)
  target_compile_features(xar_ck3_121003_26785313_core_route_bridge_compile PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_121003_26785313_core_route_bridge_compile PRIVATE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>
    $<TARGET_PROPERTY:xar_ck3_12002_runtime,INTERFACE_COMPILE_DEFINITIONS>
    NOMINMAX WIN32_LEAN_AND_MEAN XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1=1)
  if(MSVC)
    target_compile_options(xar_ck3_121003_26785313_core_route_compile PRIVATE /W4 /WX /permissive- /EHsc)
    target_compile_options(xar_ck3_121003_26785313_core_route_bridge_compile PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_121003_26785313_core_wire_fixture
    COMMAND xar_ck3_1210_core_frame_test --verify-26785313-fixtures
      "${CMAKE_CURRENT_SOURCE_DIR}/../../java/ck3-control/native-transport/src/test/resources/native26785313")
  # Compile the actual production branch without the finite fixture macro.
  add_library(xar_ck3_121003_26785313_readonly_compile OBJECT
    src/ck3_121003_readonly26785313_v1.cpp)
  set_target_properties(xar_ck3_121003_26785313_readonly_compile PROPERTIES EXCLUDE_FROM_ALL TRUE)
  target_include_directories(xar_ck3_121003_26785313_readonly_compile PRIVATE include)
  target_compile_features(xar_ck3_121003_26785313_readonly_compile PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_121003_26785313_readonly_compile PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  add_executable(xar_ck3_121003_26785313_core_static_test EXCLUDE_FROM_ALL
    src/ck3_121003_readonly26785313_static_test.cpp)
  target_include_directories(xar_ck3_121003_26785313_core_static_test PRIVATE include src)
  target_compile_features(xar_ck3_121003_26785313_core_static_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_121003_26785313_core_static_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN XAR_CK3_26785313_OFFLINE_FIXTURE=1)
  target_link_libraries(xar_ck3_121003_26785313_core_static_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(xar_ck3_121003_26785313_readonly_compile PRIVATE /W4 /WX /permissive- /EHsc)
    target_compile_options(xar_ck3_121003_26785313_core_static_test PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_121003_26785313_core_synthetic
    COMMAND xar_ck3_121003_26785313_core_static_test --synthetic-image)
  # Actual disk qualification separately needs an explicit exact EXE path.
  # The default synthetic test supplies neither actual EXE nor live credit.
  add_library(xar_ck3_121003_26785313_gui_root_index_compile OBJECT src/ck3_121003_readonly26785313_v1.cpp)
  set_target_properties(xar_ck3_121003_26785313_gui_root_index_compile PROPERTIES EXCLUDE_FROM_ALL TRUE)
  target_include_directories(xar_ck3_121003_26785313_gui_root_index_compile PRIVATE include src)
  target_compile_features(xar_ck3_121003_26785313_gui_root_index_compile PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_121003_26785313_gui_root_index_compile PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1=1)
  add_executable(xar_ck3_121003_26785313_gui_root_index_static_test EXCLUDE_FROM_ALL src/ck3_121003_readonly26785313_static_test.cpp)
  target_include_directories(xar_ck3_121003_26785313_gui_root_index_static_test PRIVATE include src)
  target_compile_features(xar_ck3_121003_26785313_gui_root_index_static_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_121003_26785313_gui_root_index_static_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN
    XAR_CK3_26785313_OFFLINE_FIXTURE=1 XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1=1)
  target_link_libraries(xar_ck3_121003_26785313_gui_root_index_static_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(xar_ck3_121003_26785313_gui_root_index_compile PRIVATE /W4 /WX /permissive- /EHsc)
    target_compile_options(xar_ck3_121003_26785313_gui_root_index_static_test PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_121003_26785313_gui_root_index_synthetic
    COMMAND xar_ck3_121003_26785313_gui_root_index_static_test --synthetic-image)
  foreach(root_wire_mode IN ITEMS OFF ON)
    set(root_wire_target "xar_ck3_121003_26785313_gui_root_wire_${root_wire_mode}_test")
    add_executable(${root_wire_target} EXCLUDE_FROM_ALL src/ck3_121003_gui_root_index26785313_wire_v1_test.cpp
    src/ck3_1210_thread_runtime.cpp
    src/game_adapter_capabilities.cpp)
    target_include_directories(${root_wire_target} PRIVATE include src)
    target_compile_features(${root_wire_target} PRIVATE cxx_std_20)
    target_compile_definitions(${root_wire_target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
    if(root_wire_mode STREQUAL "ON")
      target_compile_definitions(${root_wire_target} PRIVATE XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1=1)
    endif()
    if(MSVC)
      target_compile_options(${root_wire_target} PRIVATE /W4 /WX /permissive- /EHsc)
    endif()
    add_test(NAME ${root_wire_target} COMMAND ${root_wire_target})
  endforeach()
  add_executable(xar_ck3_121003_26785313_application_exit_static_test EXCLUDE_FROM_ALL
    src/ck3_121003_application_exit26785313_static_test.cpp src/ck3_1210_thread_runtime.cpp src/game_adapter_capabilities.cpp)
  target_include_directories(xar_ck3_121003_26785313_application_exit_static_test PRIVATE include src)
  target_compile_features(xar_ck3_121003_26785313_application_exit_static_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_121003_26785313_application_exit_static_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN
    XAR_CK3_26785313_OFFLINE_FIXTURE=1 XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1=1
    XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2=1 XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1=1
    XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1=1)
  target_link_libraries(xar_ck3_121003_26785313_application_exit_static_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(xar_ck3_121003_26785313_application_exit_static_test PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_121003_26785313_application_exit_synthetic
    COMMAND xar_ck3_121003_26785313_application_exit_static_test --synthetic-image)

  # Same finite actual production-body/strict wire tests as the bounded offline leaf.
  foreach(mode IN ITEMS OFF ON)
    set(reader "xar_ck3_121003_26785313_gui_window_reader_${mode}_compile")
    add_library(${reader} OBJECT src/ck3_121003_readonly26785313_v1.cpp)
    set_target_properties(${reader} PROPERTIES EXCLUDE_FROM_ALL TRUE)
    set(st "xar_ck3_121003_26785313_gui_window_static_${mode}_test")
    add_executable(${st} EXCLUDE_FROM_ALL src/ck3_121003_gui_window26785313_static_test.cpp)
    target_compile_definitions(${st} PRIVATE XAR_CK3_26785313_OFFLINE_FIXTURE=1)
    target_link_libraries(${st} PRIVATE bcrypt)
    set(wt "xar_ck3_121003_26785313_gui_window_wire_${mode}_test")
    add_executable(${wt} EXCLUDE_FROM_ALL src/ck3_121003_gui_window26785313_wire_v1_test.cpp
      src/ck3_1210_thread_runtime.cpp src/game_adapter_capabilities.cpp)
    foreach(t IN ITEMS ${reader} ${st} ${wt})
      target_include_directories(${t} PRIVATE include src)
      target_compile_features(${t} PRIVATE cxx_std_20)
      target_compile_definitions(${t} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
      if(mode STREQUAL "ON")
        target_compile_definitions(${t} PRIVATE XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1=1
          XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1=1)
      endif()
      if(MSVC)
        target_compile_options(${t} PRIVATE /W4 /WX /permissive- /EHsc)
      endif()
    endforeach()
    add_test(NAME ${st} COMMAND ${st} --synthetic-image)
    add_test(NAME ${wt} COMMAND ${wt})
  endforeach()
foreach(mode IN ITEMS OFF ON)
 set(t "xar_ck3_121003_26785313_rite_reader_${mode}_compile")
 add_library(${t} OBJECT src/ck3_121003_readonly26785313_v1.cpp)
 set_target_properties(${t} PROPERTIES EXCLUDE_FROM_ALL TRUE)
 set(st "xar_ck3_121003_26785313_rite_static_${mode}_test")
 add_executable(${st} EXCLUDE_FROM_ALL src/ck3_121003_rite_draft26785313_static_test.cpp)
 target_link_libraries(${st} PRIVATE bcrypt)
 target_compile_definitions(${st} PRIVATE XAR_CK3_26785313_OFFLINE_FIXTURE=1)
 set(wt "xar_ck3_121003_26785313_rite_wire_${mode}_test")
 add_executable(${wt} EXCLUDE_FROM_ALL src/ck3_121003_rite_draft26785313_wire_v2_test.cpp
  src/ck3_1210_thread_runtime.cpp
  src/game_adapter_capabilities.cpp)
 foreach(tgt IN ITEMS ${t} ${st} ${wt})
  target_include_directories(${tgt} PRIVATE include src)
  target_compile_features(${tgt} PRIVATE cxx_std_20)
  target_compile_definitions(${tgt} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  target_compile_options(${tgt} PRIVATE /W4 /WX /permissive- /EHsc)
  if(mode STREQUAL "ON")
   target_compile_definitions(${tgt} PRIVATE XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1=1
    XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1=1 XAR_CK3_ENABLE_121003_26785313_RITE_DRAFT_V2=1)
  endif()
 endforeach()
 add_test(NAME ${st} COMMAND ${st} --synthetic-image)
 add_test(NAME ${wt} COMMAND ${wt})
endforeach()
endif()
