# The always-linked actual-.4 binders call these unchanged software readers.
# Their old query options control mailbox/capability registration, not whether
# the binder translation units have complete linker dependencies. The sparse
# LYD configuration exposed this distinction in the real 15-symbol link RED.
set(_xar_religion_12004_shared_readers
  ck3_12002_religion_context.cpp
  ck3_12003_player_tenet_knowledge_catalogue.cpp
  ck3_12003_target_rite_tenet_comparison.cpp
  religion_doctrine12002_choices.cpp
  religion_doctrine12002_intrinsic.cpp
  religion_doctrine12002_query.cpp
  religion_doctrine12002_rite.cpp
  religion_doctrine12002_selection.cpp
  religion_doctrine12002_tenet.cpp
  religion_doctrine12002_tenet_rows.cpp
  religion_reform12002_ai_context.cpp
  religion_reform12002_choices.cpp
  religion_reform12002_costs.cpp
  religion_reform12002_eligibility.cpp
  religion_reform12002_fullchoices.cpp
  religion_reform12002_group_model.cpp
  religion_reform12002_query_runtime.cpp
  religion_reform12002_rite.cpp
  religion_reform12002_schedule.cpp
  religion_reform12002_tenet_sources.cpp
  religion_reform12002_willingness.cpp
  religion_reform12002_window.cpp
  religion_reform12003_creation_terms.cpp
  religion_rite_governance12002_context.cpp
  religion_rite_governance12002_head.cpp
  religion_rite_governance12002_organization.cpp
  religion_rite_governance12002_organization_members.cpp
  religion_rite_governance12002_state_rite.cpp)

# Some general religion options already supply these files, sometimes using
# absolute paths. Compare their resolved paths before adding the missing ones.
get_target_property(_xar_religion_12004_source_dir
  xar_ck3_12002_runtime SOURCE_DIR)
get_target_property(_xar_religion_12004_sources
  xar_ck3_12002_runtime SOURCES)
set(_xar_religion_12004_absolute_sources)
foreach(_xar_religion_12004_source IN LISTS _xar_religion_12004_sources)
  get_filename_component(_xar_religion_12004_absolute
    "${_xar_religion_12004_source}" ABSOLUTE
    BASE_DIR "${_xar_religion_12004_source_dir}")
  list(APPEND _xar_religion_12004_absolute_sources
    "${_xar_religion_12004_absolute}")
endforeach()
foreach(_xar_religion_12004_reader IN LISTS _xar_religion_12004_shared_readers)
  set(_xar_religion_12004_absolute
    "${_xar_religion_12004_source_dir}/src/${_xar_religion_12004_reader}")
  if(NOT _xar_religion_12004_absolute IN_LIST
      _xar_religion_12004_absolute_sources)
    target_sources(xar_ck3_12002_runtime PRIVATE
      "${_xar_religion_12004_absolute}")
    list(APPEND _xar_religion_12004_absolute_sources
      "${_xar_religion_12004_absolute}")
  endif()
endforeach()
