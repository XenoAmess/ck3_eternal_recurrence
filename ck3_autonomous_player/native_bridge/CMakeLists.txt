cmake_minimum_required(VERSION 3.25)

project(xar_ck3_native_bridge VERSION 0.1.0 LANGUAGES CXX)

# Explicitly built research helper. It never starts CK3 or submits actions;
# production bridge builds do not include it by default.
add_executable(xar_ck3_war31_two_point_hwprobe EXCLUDE_FROM_ALL
  research/war31_two_point_hwprobe.cpp)
add_executable(xar_ck3_war31_two_point_hwprobe_fixture EXCLUDE_FROM_ALL
  research/war31_two_point_hwprobe.cpp)
target_compile_features(xar_ck3_war31_two_point_hwprobe PRIVATE cxx_std_20)
target_compile_features(xar_ck3_war31_two_point_hwprobe_fixture PRIVATE cxx_std_20)
target_compile_definitions(xar_ck3_war31_two_point_hwprobe PRIVATE
  NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
target_compile_definitions(xar_ck3_war31_two_point_hwprobe_fixture PRIVATE
  NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  XAR_WAR31_HWPROBE_FIXTURE=1)
if(MSVC)
  target_compile_options(xar_ck3_war31_two_point_hwprobe PRIVATE
    /W4 /permissive- /EHsc)
  target_compile_options(xar_ck3_war31_two_point_hwprobe_fixture PRIVATE
    /W4 /permissive- /EHsc)
endif()

set(
  XAR_CK3_EXECUTABLE_PATH
  "${CMAKE_CURRENT_SOURCE_DIR}/../../Crusader Kings III/binaries/ck3.exe"
  CACHE FILEPATH
  "Exact-build CK3 executable used only by read-only source-contract tests"
)

# Ninja discovers MSVC header dependencies by matching /showIncludes output.
# CMake 4.3 can misdecode the Simplified-Chinese prefix as mojibake while
# cl.exe and Ninja exchange UTF-8, leaving every object with zero header deps.
# Repair only that observed detection result; other compiler UI languages keep
# their own prefix.
if(
  MSVC AND
  CMAKE_CXX_CL_SHOWINCLUDES_PREFIX STREQUAL
    "娉ㄦ剰: 鍖呭惈鏂囦欢:  "
)
  set(CMAKE_CXX_CL_SHOWINCLUDES_PREFIX "注意: 包含文件:  ")
  set(CMAKE_CL_SHOWINCLUDES_PREFIX "${CMAKE_CXX_CL_SHOWINCLUDES_PREFIX}")
endif()

if(NOT WIN32)
  message(FATAL_ERROR "xar_ck3_native_bridge currently targets Windows only")
endif()

if(NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
  message(FATAL_ERROR "xar_ck3_native_bridge must be built for x64")
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(
  XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1
  "Install the exact-build no-suppression particle2 startup stage recorder"
  OFF
)

option(
  XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1
  "Enable the private research-only managed one-day phase trace command pair"
  OFF
)

option(
  XAR_CK3_ENABLE_AI_TERMINAL_REENTRY_DISPATCH_OBSERVER_V1
  "Install the private passive exact-build AI winner move-dispatch observer"
  OFF
)

option(
  XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1
  "Install the existing exact-build startup containment chain"
  OFF
)

option(
  XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1
  "Skip only the proven null-RDI startup widget flag call on the exact build"
  OFF
)

option(
  XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1
  "Skip only the proven null-RBX startup call on the exact build"
  OFF
)

option(
  XAR_CK3_ENABLE_COLD_MAP_VFS_OBSERVER_V1
  "Observe the exact-build cold-map VFS ctor, moved variant, and poll state"
  OFF
)

option(
  XAR_CK3_ENABLE_NAMED_PATH_583_ROOT_OBSERVER_V1
  "Observe the exact-build named-path 0x583 resolver and CMap root move chain"
  OFF
)

option(
  XAR_CK3_ENABLE_PDX_PATHS_583_PRODUCER_OBSERVER_V1
  "Observe the exact-build private pdx_paths lookup/parser/0x583 producer chain"
  OFF
)

option(
  XAR_CK3_ENABLE_VFS_MOUNT_LIFECYCLE_OBSERVER_V1
  "Observe exact-build VFS core init, mount publication, and settings lookups"
  OFF
)

option(
  XAR_CK3_ENABLE_PHYSFS_MOUNTED_DATA_OBSERVER_V1
  "Observe the exact-build PhysFS Mounted Data publisher callsite"
  OFF
)

option(
  XAR_CK3_ENABLE_ZHONGGUO_SCOREBOARD_PRODUCTION_V1
  "Enable the read-only scoreboard production-evidence candidate without advertising production capability"
  OFF
)

option(
  XAR_CK3_ENABLE_ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1
  "Advertise the read-only promotion/compensation provider only in a private paused-live candidate"
  OFF
)

option(
  XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1
  "Advertise the read-only projects/metrics provider only in a private paused-live candidate"
  OFF
)

option(
  XAR_CK3_ENABLE_ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1
  "Advertise the read-only career-HC/workforce provider only in a private paused-live candidate"
  OFF
)

option(
  XAR_CK3_ENABLE_H3937_PHYSICAL_INVENTORY_MAILBOX_V1
  "Attach the read-only H3937 physical army scan receipt to route-contact queries"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1
  "Write the private GEN-034 truce reader result before production reset"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1
  "Advertise the exact-build read-only persisted truce-expiry candidate"
  OFF
)

option(
  XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1
  "Enable the exact H2743 read-only attacker-to-defender existing-slot query"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1
  "Install the private exact-build G2 truce evaluator callsite observer"
  OFF
)

option(
  XAR_CK3_ENABLE_STEWARD_DEVELOP_COUNTY_ENUMERATOR_OBSERVER_V1
  "Install the private exact-build steward develop-county enumerator observer"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_DOMAIN_CONSTRUCTION_CANDIDATE_OBSERVER_V1
  "Install the private exact-build domain-construction candidate observer"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_DOMAIN_CONSTRUCTION_RUNTIME_OBSERVER_V1
  "Install the private exact-build native-runtime domain-construction observer"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1
  "Read the player HoldingView candidate-cache branch on paused application-main"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_PLAYER_WORLD_BUILDING_ACTION_PRIVATE_V1
  "Controlled exact-build stock-player construction submit; no public action"
  OFF
)
if(XAR_CK3_ENABLE_G2_PLAYER_WORLD_BUILDING_ACTION_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1)
  message(FATAL_ERROR
    "Private world-building action needs its paused player world source")
endif()

option(
  XAR_CK3_ENABLE_COUNCIL_COMPOSITION_CANDIDATE_OBSERVER_V1
  "Install the private exact-build paused council-candidate observer"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_MILITARY_PREPARATION_SUMMARY_PRIVATE_PROBE_V1
  "Run one private exact-build paused military-preparation summary probe"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_FACTION_TARGETING_ROW_ASYNC_PRIVATE_PROBE_V1
  "Run one private exact-build paused targeting-faction row probe"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1
  "Run the private exact-build faction gift preview/action mailbox"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1
  "Compile the private active-scheme observer/action core for a hash-bound candidate"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1
  "Expose the private typed sway submit/receipt mailbox only in a formal action candidate"
  OFF
)
if(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1 AND
   NOT XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  message(FATAL_ERROR "Private sway action requires the exact active-scheme candidate core")
endif()

option(
  XAR_CK3_ENABLE_G2_REALM_LAW_PAUSED_PRIVATE_QUERY_V1
  "Compile the private exact-build paused realm-law final-terms query"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1
  "Compile the private exact-build paused prisoner collection reader"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1
  "Add a private native-final unconditional-release preview to prisoner rows"
  OFF
)
if(XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
  message(FATAL_ERROR "prisoner release preview requires private prisoner collection")
endif()

option(
  XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1
  "Add a private exact-build selected-option ransom quote to prisoner rows"
  OFF
)
if(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1 AND
   (NOT XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1 OR
    NOT XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1))
  message(FATAL_ERROR "prisoner ransom preview requires private collection and release preview")
endif()

option(
  XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1
  "Allow a bounded private native ransom submission from a current quote"
  OFF
)
if(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1)
  message(FATAL_ERROR "private ransom action requires the exact ransom quote")
endif()

option(
  XAR_CK3_ENABLE_G2_PRISONER_CHILD_RELATION_PRIVATE_V1
  "Read an exact-build private child-of-player predicate in prisoner rows"
  OFF
)
if(XAR_CK3_ENABLE_G2_PRISONER_CHILD_RELATION_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1)
  message(FATAL_ERROR "prisoner child relation v5 requires the private v4 collection")
endif()

option(
  XAR_CK3_ENABLE_G2_PRISONER_TITLE_TIER_PRIVATE_V1
  "Read private exact-build prisoner title tiers and player dread for release value"
  OFF
)
if(XAR_CK3_ENABLE_G2_PRISONER_TITLE_TIER_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_PRISONER_CHILD_RELATION_PRIVATE_V1)
  message(FATAL_ERROR "prisoner title tier v6 requires the private v5 collection")
endif()

option(
  XAR_CK3_ENABLE_G2_CULTURE_INNOVATION_ASYNC_PRIVATE_PROBE_V1
  "Run one private exact-build paused culture/innovation snapshot query"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_COUNCIL_COMPOSITION_STEWARD_CANDIDATES_PRIVATE_PROBE_V1
  "Run one private exact-build paused steward-candidate query"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1
  "Enable the unadvertised Council application-main controlled acceptance transport"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_DEATH_SUCCESSION_MODAL_PRIVATE_V1
  "Admit the unadvertised exact-build succession blocker query and typed Close"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_CE1_TREATMENT_PRESENCE_PRIVATE_V1
  "Admit one fixed-key private read-only CE1 treatment modifier query"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_CE1_RECOVERY_PRIVATE_V1
  "Admit private exact-build CE1 recovery county list and modifier readback"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1
  "Admit unadvertised exact-build LIFE2/LIFE4 query and LIFE6/LIFE7 perk candidate on application-main"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_M5_WAR_PRIMARY_CURRENT_PRIVATE_V1
  "Admit one unadvertised same-paused-revision current primary war/supply readback"
  OFF
)

option(
  XAR_CK3_ENABLE_WAR_ACTOR_ARMY_ROLE_PRIVATE_V1
  "Admit unadvertised paused actor role read for one exact public ArmyID"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_MINOR_RELIGIOUS_WAR_DEFENDERS_PRIVATE_V1
  "Admit exact-build paused faith co-defender preview for one final-legal minor religious war"
  OFF
)

option(
  XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1
  "Admit one controlled exact-build selected-bookmark StartGame candidate"
  OFF
)

option(
  XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1
  "Admit unadvertised exact-build Bookmarks selected-model read-only candidate"
  OFF
)

option(
  XAR_CK3_ENABLE_FRONTEND_GAME_RULES_PRIVATE_V1
  "Admit exact .3 frontend current game-rule selection observation"
  OFF
)
if(XAR_CK3_ENABLE_FRONTEND_GAME_RULES_PRIVATE_V1 AND
   (NOT XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1 OR
    NOT XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1))
  message(FATAL_ERROR "Frontend rules candidate requires existing FEUDAL frontend admission")
endif()

option(XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1
  "Admit exact .3 map-only fixed stock normal exit with actual source inventory and independent process observation" OFF)
if(XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1 AND
   (NOT XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1 OR
    NOT XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1))
  message(FATAL_ERROR "Map normal exit requires existing exact-build frontend owner admission")
endif()

option(XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1
  "Admit exact .3 fixed HUD Decisions button through the original GUI callback" OFF)
if(XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1 AND
   (NOT XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1 OR
    NOT XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1))
  message(FATAL_ERROR "Decisions opener requires existing frontend main-thread admission")
endif()

option(XAR_CK3_ENABLE_AUB_CONFIRM_STATE_PRIVATE_V1
  "Exact .3 AUB four native flags and guarded policy Confirm once" OFF)
if(XAR_CK3_ENABLE_AUB_CONFIRM_STATE_PRIVATE_V1 AND NOT XAR_CK3_ENABLE_AUB_POLICY_OPTIONS_PRIVATE_V1)
  message(FATAL_ERROR "AUB Confirm requires the fixed actual six-key policy provider")
endif()
option(XAR_CK3_ENABLE_AUB_POLICY_OPTIONS_PRIVATE_V1
  "Admit exact .3 fixed six AUB option-list query/source OnSelect; no Confirm" OFF)
if(XAR_CK3_ENABLE_AUB_POLICY_OPTIONS_PRIVATE_V1 AND NOT XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1)
  message(FATAL_ERROR "AUB policies require exact .3 Decisions owner/query admission")
endif()
option(XAR_CK3_ENABLE_WHITE_CONTROL_ACTIONS_PRIVATE_V1
  "Admit exact .3 fixed White age+1 callback with separate actual after proof" OFF)

option(XAR_CK3_ENABLE_WHITE_RENDERED_TEXT_PRIVATE_V1
  "Admit exact .3 nine fixed actual White TextBox values; no down state" OFF)

option(XAR_CK3_ENABLE_WHITE_PLAYER_BUSINESS_VARIABLES_PRIVATE_V1
  "Admit exact .3 fixed current-player White configuration variable observation" OFF)

option(XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1
  "Admit exact .3 actual-row OnSelect and fixed detail Confirm callback once" OFF)
if(XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1)
  message(FATAL_ERROR "Decision item actions require the exact .3 Decisions owner/query admission")
endif()

option(XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1
  "Admit guarded stock Confirm once with independent event-window or closed-detail verification" OFF)
if(XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1)
  message(FATAL_ERROR "Decision outcome confirmation requires exact .3 keyed item actions")
endif()

option(
  XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1
  "Bind the exact-build supported 1066 bookmark candidate to Duke Robert"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_COUNCIL_ASSIGN_PRIVATE_ACTION_GATE_V1
  "Admit exact Council final gates only in the unadvertised controlled action candidate"
  OFF
)
if(XAR_CK3_ENABLE_G2_COUNCIL_ASSIGN_PRIVATE_ACTION_GATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1)
  message(FATAL_ERROR "Council private action gates require the controlled private route")
endif()
option(
  XAR_CK3_ENABLE_G2_COUNCIL_FINAL_GATE_PRIVATE_QUERY_V1
  "Read exact Council final gates on application-main without admitting a helper action"
  OFF
)
if(XAR_CK3_ENABLE_G2_COUNCIL_FINAL_GATE_PRIVATE_QUERY_V1 AND
   NOT XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1)
  message(FATAL_ERROR "Council final-gate query requires the controlled private route")
endif()
option(
  XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1
  "Enable one unadvertised exact-build paused ranked-marriage query for controlled acceptance"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_M5_HEIR_MARRIAGE_PRIVATE_ACTION_V1
  "Enable unadvertised observed-first-heir marriage submit and material readback"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_M5_CHILD_MATRILINEAL_PRIVATE_ACTION_V1
  "Enable unadvertised selected-option player-child marriage submit"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1
  "Enable unadvertised five-candidate paused application-main alliance projection"
  OFF
)
if(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1 AND
   NOT XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1)
  message(FATAL_ERROR "Alliance projection requires the private first-heir legality query")
endif()
if(XAR_CK3_ENABLE_G2_M5_HEIR_MARRIAGE_PRIVATE_ACTION_V1 AND
   NOT XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1)
  message(FATAL_ERROR "First-heir marriage action requires its private legality query")
endif()
if(XAR_CK3_ENABLE_G2_M5_CHILD_MATRILINEAL_PRIVATE_ACTION_V1 AND
   (NOT XAR_CK3_ENABLE_G2_M5_HEIR_MARRIAGE_PRIVATE_ACTION_V1 OR
    NOT XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1))
  message(FATAL_ERROR "Player-child marriage action requires private submit and selected value query")
endif()

option(
  XAR_CK3_ENABLE_G2_ACTIVITY_PLANNING_SNAPSHOT_PRIVATE_GLUE_V1
  "Link the activity-owned paused application-main snapshot glue"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_PLANNER_DIAG_PRIVATE_QUERY_V1
  "Enable default-off paused activity planner metadata diagnostic"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1
  "Enable default-off paused native feast planner open probe"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1
  "Enable default-off paused native feast stage-1 option read"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_CONFIRM_PRIVATE_V1
  "Enable default-off paused native feast stage-1-only confirm action"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_OPTION_READ_PRIVATE_V1
  "Enable default-off paused native feast stage-2 selected option read"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_GATE_READ_PRIVATE_V1
  "Enable default-off paused native feast stage-2 CanProgress read"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_LOCATION_READ_PRIVATE_V1
  "Enable default-off paused native feast stage-2 location legality read"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1
  "Enable default-off bounded feast stage-2 destination select action"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1
  "Enable default-off paused native feast stage-5 final CanStart read"
  OFF
)
if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_CONFIRM_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1)
  message(FATAL_ERROR "Activity stage-1 confirm requires option read")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_OPTION_READ_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1)
  message(FATAL_ERROR "Activity stage-2 option read requires stage-1 reader")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_GATE_READ_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1)
  message(FATAL_ERROR "Activity stage-2 gate read requires stage-1 reader")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_LOCATION_READ_PRIVATE_V1 AND
   (NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1 OR
    NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_GATE_READ_PRIVATE_V1))
  message(FATAL_ERROR "Activity stage-2 location read requires option and gate readers")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_LOCATION_READ_PRIVATE_V1)
  message(FATAL_ERROR "Activity stage-2 destination action requires location reader")
endif()
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_COST_SLOT12_PASSIVE_PRIVATE_V1
  "Enable default-off passive native activity cost slot12 raw capture"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1
  "Enable default-off paused native feast stage-5 named Gold cost read"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1
  "Enable default-off paused native feast stage-5 four-resource cost and CanStart read"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1
  "Enable default-off paused feast Stage-5 inputs, guarded Start and hosted post"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_CANDIDATE_PRIVATE_V1
  "Enable default-off paused read-only feast Stage-5 native-filtered guest candidate"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_TOGGLE_PRIVATE_V1
  "Enable default-off paused private feast guest invitation rule read and toggle"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_OPINION_PRIVATE_V1
  "Enable default-off paused read-only feast guest opinion of host"
  OFF
)
option(
  XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1
  "Enable default-off passive per-rule feast guest membership read"
  OFF
)
if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_ACTIVITY_COST_SLOT12_PASSIVE_PRIVATE_V1)
  message(FATAL_ERROR "Activity stage-5 named Gold read requires passive slot12 capture")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1 AND
   (NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1 OR
    NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1))
  message(FATAL_ERROR "Activity stage-5 feast full cost read requires Gold cost and CanStart readers")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1)
  message(FATAL_ERROR "Activity Stage-5 Start requires full cost and CanStart readers")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_CANDIDATE_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1)
  message(FATAL_ERROR "Feast guest candidate read requires Stage-5 Start native inputs")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_TOGGLE_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_ACTIVITY_COST_SLOT12_PASSIVE_PRIVATE_V1)
  message(FATAL_ERROR "Feast guest rule toggle requires passive slot12 capture")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_TOGGLE_PRIVATE_V1)
  message(FATAL_ERROR "Feast guest rule provenance requires private rule read")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1 AND
   XAR_CK3_ENABLE_G2_ACTIVITY_PLANNER_DIAG_PRIVATE_QUERY_V1)
  message(FATAL_ERROR "Activity feast open and planner diagnostic use the same private mailbox executor slot")
endif()
option(
  XAR_CK3_ENABLE_G2_MAJOR_DECISION_FOUND_KINGDOM_INTERNAL_ROUTE_V1
  "Arm the private fixed-candidate found-kingdom submit/receipt route"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1
  "Emit private diagnostics for the exact-vtable G2 truce preview observer"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2
  "Evaluate the private G2 target only inside its exact native leaf-preview context"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_TRUCE_DEFAULT_LEAF_DIAGNOSTICS_V1
  "Log failure stages from the unchanged default G2 truce leaf reader"
  OFF
)

if(
  XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1 AND
  XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1
)
  message(FATAL_ERROR
    "The native callsite observer cannot be combined with direct evaluator capture")
endif()
if(
  XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2 AND
  (XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1 OR
   XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1)
)
  message(FATAL_ERROR
    "The leaf-context capture is a standalone private candidate")
endif()
if(
  XAR_CK3_ENABLE_G2_TRUCE_DEFAULT_LEAF_DIAGNOSTICS_V1 AND
  (XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1 OR
   XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1 OR
   XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1 OR
   XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2)
)
  message(FATAL_ERROR
    "Default-leaf diagnostics must use the otherwise unchanged production reader")
endif()

option(
  XAR_CK3_ENABLE_G2_WAR_BOUND_PRIVATE_CAPTURE_V1
  "Build the private exact-build Raiktor spawn-army debugger capture"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_WAR_BOUND_LOSS_CANDIDATE_V1
  "Build the private read-only paired war-bound loss candidate"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_COMPLETION_OBSERVER_V1
  "Install the private exact-build phase-two completion observer"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_WRAPPER_ENTRY_OBSERVER_V1
  "Install the private exact-build phase-two wrapper entry observer"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_POST_CALL_OBSERVER_V1
  "Install the private exact-build phase-two post-call observer"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_POST_CALL_LIST_IDENTITY_OBSERVER_V1
  "Install the private exact-build phase-two post-call list identity observer"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1
  "Install the private exact-build phase-two producer identity observer"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_PRODUCER_CONSUMER_CORRELATION_OBSERVER_V1
  "Correlate the private phase-two producer selection with its completion consumer"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_V1
  "Classify post-publish phase-two wrapper and exact consumer call edges"
  OFF
)

if(
  XAR_CK3_ENABLE_PHASE2_POST_CALL_OBSERVER_V1 AND
  XAR_CK3_ENABLE_PHASE2_POST_CALL_LIST_IDENTITY_OBSERVER_V1
)
  message(FATAL_ERROR
    "The two private phase-two post-call observers share RVA 0x3407DA1")
endif()

add_library(xar_bridge_protocol STATIC
  src/protocol.cpp
)
target_include_directories(xar_bridge_protocol PUBLIC include)
target_compile_definitions(xar_bridge_protocol PUBLIC
  NOMINMAX
  WIN32_LEAN_AND_MEAN
  UNICODE
  _UNICODE
)

add_library(xar_bridge_injector STATIC
  src/injector.cpp
)
target_include_directories(xar_bridge_injector PUBLIC include)
target_compile_definitions(xar_bridge_injector PUBLIC
  NOMINMAX
  WIN32_LEAN_AND_MEAN
  UNICODE
  _UNICODE
)

# Exact 1.20 readers retain the verified adapter layer while this tree keeps
# the delivered master nonwar consumers and their fixed private interfaces.
option(XAR_CK3_ENABLE_G2_GOVERNMENT_RUNTIME_PRIVATE_QUERY_V1
  "Compile the exact-build 1.20 government observation candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1
  "Compile the exact-build 1.20 full faction observation candidate" OFF)
option(XAR_CK3_ENABLE_G2_M5_WAR_CASH_PRIVATE_QUERY_V1
  "Compile the completed 1.20 war-cash candidate; combat authorization restored 2026-10-03" OFF)
option(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1
  "Compile the exact-build 1.20 family lineage and break-terms candidate" OFF)
option(XAR_CK3_ENABLE_G2_M5_PREWAR_SOURCES_PRIVATE_QUERY_V1
  "Compile the 1.20 prewar candidate; combat authorization restored 2026-10-03" OFF)
option(XAR_CK3_ENABLE_G2_REALM_LAW_ENACT_PRIVATE_V1
  "Compile the exact-build paused crown-law action candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1
  "Compile the exact-build paused player religion observation candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1
  "Compile the private READY player_rite_governance_private_query_v1 candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1
  "Compile the private READY player_clergy_appointment_private_query_v1 candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1
  "Compile the private READY player_rite_members_private_query_v1 candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1
  "Compile the private READY player_religion_doctrines_private_query_v1 candidate" OFF)
option(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1
  "Compile the private READY religion_conversion_private_query_v1 candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1
  "Compile the private READY player_religion_hostility_private_query_v1 candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1
  "Compile the private READY player_religion_doctrine_knowledge_private_query_v1 candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1
  "Compile the private READY player_religion_tenets_private_query_v1 candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1
  "Compile the private READY player_epidemic_treatment_private_query_v1 candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1
  "Compile the private READY player_epidemic_recovery_private_query_v1 candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1
  "Compile the private READY player_religion_reform_context_private_query_v1 candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1
  "Compile the private READY player_religion_doctrine_catalogue_private_query_v1 candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1
  "Compile the private READY player religion numeric special parameters candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1
  "Compile the private READY player religion personal parameters candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1
  "Compile the private READY player religion DraftGroups readonly candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1
  "Compile the private READY player_religion_draft_doctrine_choices_private_query_v1 readonly candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1
  "Compile the private READY player_religion_draft_tenet_choices_private_query_v1 readonly candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1
  "Compile the private READY player_religion_draft_resource_costs_private_query_v1 readonly candidate" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1
  "Compile the private READY actual AI controller and schedule readonly inputs" OFF)
option(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1
  "Compile the private READY Sway pair opinion material readonly query" OFF)
file(GLOB XAR_CK3_12002_SOURCES CONFIGURE_DEPENDS
  "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002*.cpp")
list(FILTER XAR_CK3_12002_SOURCES EXCLUDE REGEX "_test(_only)?\\.cpp$")
list(APPEND XAR_CK3_12002_SOURCES
  "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_context_sources.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_task_position_inputs.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_battle_current_state.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_maa_recruitment.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/owned_regiments.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_maa_create.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_maa_create_private_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_army_supply_timing.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_army_replenishment_records.cpp")
# R11 owns only explicitly READY outcome production CPPs below.
list(FILTER XAR_CK3_12002_SOURCES EXCLUDE REGEX "/ck3_12002_sway_outcome.*\\.cpp$")
# READY explicit source lists below own these namespaces.
# Later religion, Sway completion, and epidemic work stays excluded unless explicitly READY below.
list(FILTER XAR_CK3_12002_SOURCES EXCLUDE REGEX
  "/ck3_12002_(religion.*|sway_completion.*|epidemic.*|personal.*)\\.cpp$")
if(NOT XAR_CK3_ENABLE_G2_M5_WAR_CASH_PRIVATE_QUERY_V1)
  # War research/execution is authorized as of 2026-10-03. This OFF build
  # choice retains snapshot treasury while the separate cash producer stays excluded.
  list(FILTER XAR_CK3_12002_SOURCES EXCLUDE REGEX
    "/ck3_12002_war_cash(_serializer|_mailbox|_maintenance|_action_fees)?\\.cpp$")
endif()
if(NOT XAR_CK3_ENABLE_G2_M5_PREWAR_SOURCES_PRIVATE_QUERY_V1)
  list(FILTER XAR_CK3_12002_SOURCES EXCLUDE REGEX "/ck3_12002_prewar.*\\.cpp$")
endif()
if(NOT (XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1 AND
        XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1))
  list(FILTER XAR_CK3_12002_SOURCES EXCLUDE REGEX
    "/ck3_12002_family_obligations_alliance\\.cpp$")
endif()
if(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_call_ally_private_action.cpp")
endif()
# The delivered queries share the current-player religion leaf.
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_religion_context.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_religion_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_spiritual_fulfillment_progress.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_mystical_communion_decision_terms.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_pilgrimage_activity_type_terms.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_pilgrimage_candidate_factory.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_pilgrimage_activity_terms.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_pilgrimage_candidate_route.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_activity_phase_dates.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_confession_decision_terms.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_confession_rite_permission.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_tenet_rows.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_tenet_sources.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_window.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_church_income_profile.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_spiritual_fulfillment_type.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_church_tax_inputs.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_devotion_profile.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_rite_virtue_sin_profile.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_vow_of_poverty_terms.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_holy_order_loan_context.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_holy_order_loan_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_holy_order_loan_wire.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_hof_gold_context.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_hof_gold_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_hof_gold_wire.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_repentance_context.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_rite_governance12002_clergy.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_repentance_recipient_candidates.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_repentance_fallback.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_repentance_recovery_inputs.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_repentance_pam_route.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_repentance_petition_decision_terms.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_repentance_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_repentance_wire.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_holy_order_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_holy_order_wire.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_holy_order_selected_parameters.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_holy_order_selected_candidates.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_holy_order_selected_title_terms.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_holy_order_selected_title_terms_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_holy_order_selected_title_terms_wire.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_rite_governance12002_state_rite.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_rite_governance12002_head.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_rite_governance12002_organization.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_rite_governance12002_context.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_rite_governance12002_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_rite_governance12002_clergy.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_rite_governance12002_clergy_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_county_conversion.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_county_conversion_task_action_v1.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_county_conversion_task_action_serializer.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_county_conversion_task_action_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_rite_governance12002_organization_members.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_rite_governance12002_members_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_intrinsic.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_rite.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_tenet.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_query.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_religion_conversion_rite.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_religion_conversion_cost.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_religion_conversion_terms.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_religion_conversion_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_religion_conversion_action_v1.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_religion_conversion_action_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_religion_conversion_faith.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_religion_conversion_choices_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_religion_conversion_gates.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_religion_conversion_ai_inputs.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_religion_conversion_inputs_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_rite_governance12002_state_rite.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_hostility.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_hostility_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_choices.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_choices_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_tenet_rows.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_tenet_rows_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_handler.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_serializer.cpp")
endif()
# R4 READY production sources, including their exact frozen provider dependencies.
if(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_epidemic_treatment_presence.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_epidemic_treatment_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_epidemic_recovery.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_epidemic_recovery_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/player_epidemic_recovery_v1.cpp")
endif()
if(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_religion_conversion_reasons.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_religion_conversion_reasons_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_execution.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_execution_handler.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_execution_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_execution_serializer.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_execution_install.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1 OR XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_rite.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_willingness.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_window.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_costs.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_eligibility.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_choices.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_intrinsic.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_choices.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_tenet_rows.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_selection.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_query_runtime.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_query_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_intrinsic.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_catalogue.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_catalogue_mailbox.cpp")
endif()
# R5 READY queries; Sway termination's installer is in its main source.
if(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/conversion_outcome12002_actor.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/conversion_outcome12002_state.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/conversion_outcome12002_query.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/conversion_outcome12002_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_numeric.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_numeric_final.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_numeric_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_termination.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_termination_handler.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_termination_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_termination_serializer.cpp")
endif()
# R6 READY readonly Personal query and specific Sway invalidation reason source/query.
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_personal_parameters.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_personal_parameters_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_tenet_rows.cpp")
endif()
if(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_invalidation_reason.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_invalidation_reason_handler.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_invalidation_reason_mailbox.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_completion_invalidation_reason_serializer.cpp")
endif()
# R7 DraftGroups reads reuse the existing Reform provider dependencies.
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_group_model.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_group_mailbox.cpp")
endif()
# R8 READY readonly choices and native base-resource quotes.
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_fullchoices.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_fullchoices_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_tenet_sources.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_tenet_sources_mailbox.cpp")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_resource_costs.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_resource_costs_mailbox.cpp")
endif()
# R9 READY actual AI controller table plus per-member schedule inputs.
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_schedule.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_ai_context.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_ai_inputs_mailbox.cpp")
endif()
# R11 READY readonly Sway opinion material; no event selector or action registration.
if(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1)
  list(APPEND XAR_CK3_12002_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_outcome.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_sway_outcome_mailbox.cpp")
endif()
list(REMOVE_DUPLICATES XAR_CK3_12002_SOURCES)
add_library(xar_ck3_12002_runtime STATIC
  ${XAR_CK3_12002_SOURCES}
  src/ck3_12003_adapter.cpp
  src/ck3_12003_commander.cpp
  src/ck3_12003_war_occupation.cpp
  src/ck3_12003_title_holder.cpp
  src/ck3_12003_commander_mailbox.cpp
  src/ck3_12002_prewar_muster.cpp
  src/ck3_12003_default_raise_mailbox.cpp
  src/ck3_12003_war_cash_current_reader.cpp
  src/ck3_12003_war_cash_current_serializer.cpp
  src/ck3_12003_war_cash_current_mailbox.cpp
  src/ck3_12003_mercenary_candidates.cpp
  src/ck3_12003_mercenary_composition.cpp
  src/ck3_12003_mercenary_final_terms.cpp
  src/ck3_12003_mercenary_position.cpp
  src/ck3_12003_player_mercenary_context.cpp
  src/ck3_12003_player_mercenary_wire.cpp
  src/ck3_12003_player_mercenary_mailbox.cpp
  src/ck3_12003_mercenary_hire_action.cpp
  src/ck3_12003_mercenary_hire_wire.cpp
  src/ck3_12003_player_mercenary_hire_mailbox.cpp
  src/ck3_12003_player_holy_order_context.cpp
  src/ck3_12003_holy_order_hire_action.cpp
  src/ck3_12003_holy_order_hire_wire.cpp
  src/ck3_12003_player_holy_order_hire_mailbox.cpp
  src/ck3_12003_army_reserve.cpp
  src/ck3_12003_commander_assignment.cpp
  src/ck3_12003_commander_assignment_mailbox.cpp
  src/ck3_12003_family_terminal_events.cpp
  src/ck3_12003_abi_profile.cpp
  src/county_faction_final_12003.cpp
  research/ck3_12002_construction_submit_binding.cpp
  src/player_lifestyle_window_candidates_v1.cpp
  src/main_thread_query_mailbox_v1.cpp)
target_include_directories(xar_ck3_12002_runtime PUBLIC include PRIVATE src research)
target_compile_definitions(xar_ck3_12002_runtime PUBLIC
  NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
target_link_libraries(xar_ck3_12002_runtime PUBLIC bcrypt)
if(MSVC)
  target_compile_options(xar_ck3_12002_runtime PRIVATE
    /W4 /permissive- /EHsc)
endif()
add_executable(xar_ck3_12003_player_mercenary_context_test
  src/ck3_12003_player_mercenary_context_test.cpp
  src/ck3_12003_player_mercenary_context.cpp
  src/ck3_12003_player_mercenary_wire.cpp
  src/ck3_12003_mercenary_candidates.cpp
  src/ck3_12003_mercenary_composition.cpp
  src/ck3_12003_mercenary_final_terms.cpp
  src/ck3_12003_mercenary_position.cpp)
target_include_directories(xar_ck3_12003_player_mercenary_context_test PRIVATE include)
target_compile_definitions(xar_ck3_12003_player_mercenary_context_test PRIVATE NOMINMAX)
if(MSVC)
  target_compile_options(xar_ck3_12003_player_mercenary_context_test PRIVATE
    /W4 /WX /permissive- /EHsc /utf-8)
endif()
add_test(NAME ck3_12003_player_mercenary_context
  COMMAND xar_ck3_12003_player_mercenary_context_test
    "${CMAKE_CURRENT_BINARY_DIR}/ck3_12003_player_mercenary_context_wire.json")

add_executable(xar_ck3_12003_mercenary_hire_action_test
  src/ck3_12003_mercenary_hire_action_test.cpp
  src/ck3_12003_mercenary_hire_action.cpp
  src/ck3_12003_mercenary_hire_wire.cpp
  src/ck3_12003_mercenary_candidates.cpp
  src/ck3_12003_mercenary_final_terms.cpp
  src/ck3_12002_commands.cpp
  src/ck3_12002.cpp)
target_include_directories(xar_ck3_12003_mercenary_hire_action_test PRIVATE include)
target_compile_definitions(xar_ck3_12003_mercenary_hire_action_test PRIVATE NOMINMAX NDEBUG)
if(MSVC)
  target_compile_options(xar_ck3_12003_mercenary_hire_action_test PRIVATE
    /O2 /W4 /WX /permissive- /EHsc /utf-8 /Gy)
  target_link_options(xar_ck3_12003_mercenary_hire_action_test PRIVATE
    /OPT:REF /INCREMENTAL:NO)
endif()
add_test(NAME ck3_12003_mercenary_hire_action
  COMMAND xar_ck3_12003_mercenary_hire_action_test
    "${CMAKE_CURRENT_BINARY_DIR}/ck3_12003_mercenary_hire_action_wire.json")
add_executable(xar_ck3_12003_holy_order_hire_action_test
  src/ck3_12003_holy_order_hire_action_test.cpp
  src/ck3_12003_holy_order_hire_action.cpp
  src/ck3_12003_holy_order_hire_wire.cpp
  src/ck3_12003_player_holy_order_context.cpp
  src/ck3_12002_commands.cpp
  src/ck3_12002.cpp)
target_include_directories(xar_ck3_12003_holy_order_hire_action_test PRIVATE include)
target_compile_definitions(xar_ck3_12003_holy_order_hire_action_test PRIVATE NOMINMAX NDEBUG)
if(MSVC)
  target_compile_options(xar_ck3_12003_holy_order_hire_action_test PRIVATE
    /O2 /W4 /WX /permissive- /EHsc /utf-8 /Gy)
  target_link_options(xar_ck3_12003_holy_order_hire_action_test PRIVATE
    /OPT:REF /INCREMENTAL:NO)
endif()
add_test(NAME ck3_12003_holy_order_hire_action
  COMMAND xar_ck3_12003_holy_order_hire_action_test
    "${CMAKE_CURRENT_BINARY_DIR}/ck3_12003_holy_order_hire_action_wire.json")

add_executable(xar_ck3_12003_holy_order_war_eligibility_test
  src/ck3_12003_holy_order_war_eligibility_test.cpp
  src/ck3_12003_player_holy_order_context.cpp
  src/ck3_12003_player_holy_order_wire.cpp)
target_include_directories(xar_ck3_12003_holy_order_war_eligibility_test PRIVATE include)
target_compile_definitions(xar_ck3_12003_holy_order_war_eligibility_test PRIVATE
  NOMINMAX XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
if(MSVC)
  target_compile_options(xar_ck3_12003_holy_order_war_eligibility_test PRIVATE
    /W4 /WX /permissive- /EHsc /utf-8)
endif()
add_test(NAME ck3_12003_holy_order_war_eligibility
  COMMAND xar_ck3_12003_holy_order_war_eligibility_test
    "${CMAKE_CURRENT_BINARY_DIR}/ck3_12003_holy_order_war_eligibility_wire.json")

if(XAR_CK3_ENABLE_WHITE_CONTROL_ACTIONS_PRIVATE_V1 AND (NOT XAR_CK3_ENABLE_WHITE_RENDERED_TEXT_PRIVATE_V1 OR NOT XAR_CK3_ENABLE_WHITE_PLAYER_BUSINESS_VARIABLES_PRIVATE_V1 OR NOT XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1 OR NOT XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1))
  message(FATAL_ERROR "White age+1 action requires actual White business/text providers and owning frontend main-thread admission")
endif()

foreach(private_option IN ITEMS
    XAR_CK3_ENABLE_AUB_CONFIRM_STATE_PRIVATE_V1
    XAR_CK3_ENABLE_AUB_POLICY_OPTIONS_PRIVATE_V1
    XAR_CK3_ENABLE_WHITE_PLAYER_BUSINESS_VARIABLES_PRIVATE_V1
    XAR_CK3_ENABLE_WHITE_RENDERED_TEXT_PRIVATE_V1
    XAR_CK3_ENABLE_WHITE_CONTROL_ACTIONS_PRIVATE_V1
    XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1
    XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1
    XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1
    XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1
    XAR_CK3_ENABLE_FRONTEND_GAME_RULES_PRIVATE_V1
    XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1
    XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1
    XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1
    XAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1
    XAR_CK3_ENABLE_G2_PLAYER_WORLD_BUILDING_ACTION_PRIVATE_V1
    XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_M5_HEIR_MARRIAGE_PRIVATE_ACTION_V1
    XAR_CK3_ENABLE_G2_M5_CHILD_MATRILINEAL_PRIVATE_ACTION_V1
    XAR_CK3_ENABLE_G2_COUNCIL_COMPOSITION_STEWARD_CANDIDATES_PRIVATE_PROBE_V1
    XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1
    XAR_CK3_ENABLE_G2_COUNCIL_ASSIGN_PRIVATE_ACTION_GATE_V1
    XAR_CK3_ENABLE_G2_COUNCIL_FINAL_GATE_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1
    XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1
    XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1
    XAR_CK3_ENABLE_G2_REALM_LAW_PAUSED_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_REALM_LAW_ENACT_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_CONFIRM_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_OPTION_READ_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_GATE_READ_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_LOCATION_READ_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_COST_SLOT12_PASSIVE_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_CANDIDATE_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_TOGGLE_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_OPINION_PRIVATE_V1
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1
    XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1
    XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1
    XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1
    XAR_CK3_ENABLE_G2_PRISONER_CHILD_RELATION_PRIVATE_V1
    XAR_CK3_ENABLE_G2_PRISONER_TITLE_TIER_PRIVATE_V1
    XAR_CK3_ENABLE_G2_GOVERNMENT_RUNTIME_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_M5_WAR_CASH_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_M5_PREWAR_SOURCES_PRIVATE_QUERY_V1)
  if(${private_option})
    target_compile_definitions(xar_ck3_12002_runtime PUBLIC ${private_option}=1)
  endif()
endforeach()

add_library(xar_ck3_bridge SHARED
  src/cold_map_vfs_observer_v1.cpp
  src/named_path_583_root_observer_v1.cpp
  src/pdx_paths_583_producer_observer_v1.cpp
  src/vfs_mount_lifecycle_observer_v1.cpp
  src/physfs_mounted_data_observer_v1.cpp
  src/actual_contact_scope_v1_mailbox.cpp
  src/battle_control_snapshot_v1_mailbox.cpp
  src/battle_reinforcement_assignment_v1_mailbox.cpp
  src/battle_terminal_journal_v1.cpp
  src/battle_terminal_transition_v1_mailbox.cpp
  src/battle_transition_v1_mailbox.cpp
  src/bridge.cpp
  src/campaign_root_context_v1.cpp
  src/campaign_root_context_v1_mailbox.cpp
  src/campaign_root_context_v1_serializer.cpp
  src/player_faction_alerts_v1.cpp
  src/player_faction_alerts_v1_mailbox.cpp
  src/player_faction_alerts_v1_serializer.cpp
  src/player_construction_view_probe_v1.cpp
  src/player_construction_view_probe_v1_process.cpp
  src/player_construction_view_probe_v1_mailbox.cpp
  src/player_held_construction_model_enumerator_v1.cpp
  src/player_world_building_definition_source_v1.cpp
  src/player_world_building_definition_source_v1_process.cpp
  src/player_world_building_action_candidate_v1.cpp
  src/steward_develop_county_candidates_v1.cpp
  src/ck3_12003_steward_develop_county.cpp
  src/steward_develop_county_candidates_v1_mailbox.cpp
  src/steward_develop_county_candidates_v1_serializer.cpp
  src/steward_develop_county_action_v1.cpp
  src/steward_develop_county_enumerator_observer_v1.cpp
  research/domain_construction_candidate_identity_decoder_v1.cpp
  research/domain_construction_candidate_cost_legality_decoder_v1.cpp
  research/domain_construction_cost_legality_collector_source_adapter_v1.cpp
  research/domain_construction_cost_legality_live_observer_v1.cpp
  research/domain_construction_semantic_action_core_v1.cpp
  research/domain_construction_native_submit_adapter_v1.cpp
  src/domain_construction_shared_glue_v1.cpp
  src/domain_construction_application_main_runtime_v1.cpp
  src/council_composition_candidate_observer_v1.cpp
  src/council_composition_candidate_observer_v1_serializer.cpp
  src/council_composition_steward_candidates_reader_v1.cpp
  src/council_composition_steward_candidates_binding_v1.cpp
  src/council_composition_candidates_enrichment_v1.cpp
  src/council_composition_candidates_public_v1.cpp
  src/council_composition_candidates_public_v1_serializer.cpp
  src/council_assign_councillor_action_v1.cpp
  src/council_assign_councillor_native_submit_adapter_v1.cpp
  src/council_replacement_fireability_v1.cpp
  src/council_production_final_gates_v1.cpp
  src/council_application_main_v1.cpp
  src/council_application_main_private_transport_v1.cpp
  src/ck3_11906.cpp
  src/ck3_11906_adapter.cpp
  src/coat_of_arms_designer_probe_v1.cpp
  src/combat_phase_event_trace_v1.cpp
  src/combat_phase_event_trace_v1_mailbox.cpp
  src/combat_phase_event_trace_detour_v1.cpp
  src/combat_counter_output_detour_v1.cpp
  src/combat_advantage_components_observer_v1.cpp
  src/combat_phase_event_trace_managed_v1.cpp
  src/combat_phase_event_trace_ring_v1.cpp
  src/combat_scoped_transition_chain_v1.cpp
  src/combat_scoped_transition_chain_v1_wire.cpp
  src/scoped_character_variable_monitor_v1.cpp
  src/combat_counter_output_readout_v1.cpp
  src/combat_phase_event_trace_wire_v1.cpp
  src/combat_simulation_inputs_v3_mailbox.cpp
  src/combat_v3.cpp
  src/combat_v3_serializer.cpp
  src/combat_v3_test_only.cpp
  src/current_timeline_blocker_context_v1.cpp
  src/current_timeline_blocker_context_v1_mailbox.cpp
  src/ck3_12003_succession_modal.cpp
  src/current_timeline_blocker_context_v1_native.cpp
  src/player_epidemic_treatment_presence_v1.cpp
  src/player_epidemic_treatment_presence_v1_mailbox.cpp
  src/player_epidemic_recovery_v1.cpp
  src/player_epidemic_recovery_v1_mailbox.cpp
  src/death_succession_modal_continue_v1.cpp
  src/death_succession_modal_continue_v1_mailbox.cpp
  src/event_window_context_v1.cpp
  src/event_window_context_v1_mailbox.cpp
  src/event_window_context_v1_serializer.cpp
  src/frontend_bookmark_model_probe_v1.cpp
  src/frontend_gui_route_v1.cpp
  src/ingame_decisions_opener_v1.cpp
  src/normal_exit_map_v1.cpp
  src/normal_exit_map_request_v1.cpp
  src/normal_exit_map_source_v1.cpp
  src/ingame_decision_item_v1.cpp
  src/white_player_business_variables_v1.cpp
  src/white_rendered_text_v1.cpp
  src/aub_policy_options_v1.cpp
  src/aub_policy_options_mailbox_v1.cpp
  src/aub_business_state_v1.cpp
  src/white_control_action_v1.cpp
  src/frontend_game_rules_v1.cpp
  src/game_adapter.cpp
  src/government_runtime_adapter_observer_v1.cpp
  src/government_runtime_adapter_source_adapter_v1.cpp
  src/government_runtime_adapter_bridge_binder_v1.cpp
  src/g2_truce_native_callsite_observer_v1.cpp
  src/g2_truce_preview_entry_observer_v1.cpp
  src/loaded_feature_manifest_v1.cpp
  src/loaded_feature_manifest_v1_mailbox.cpp
  src/loaded_feature_manifest_v1_serializer.cpp
  src/main_thread_query_mailbox_v1.cpp
  src/major_decision_found_kingdom_observer_v1.cpp
  src/major_decision_found_kingdom_source_adapter_v1.cpp
  src/major_decision_found_kingdom_native_binder_v1.cpp
  src/major_decision_found_kingdom_action_core_v1.cpp
  src/major_decision_found_kingdom_native_submit_v1.cpp
  src/major_decision_found_kingdom_shared_glue_v1.cpp
  src/major_decision_found_kingdom_internal_route_v1.cpp
  src/marriage_application_main_receipt_v1.cpp
  src/marriage_candidate_internal_route_v1.cpp
  src/current_first_heir_relationship_v1.cpp
  src/observed_heir_marriage_private_v1.cpp
  src/marriage_alliance_projection_adapter_v1.cpp
  src/marriage_alliance_readback_adapter_v1.cpp
  src/marriage_matchmaking_observer_v1.cpp
  src/marriage_matchmaking_source_adapter_v1.cpp
  src/marriage_native_outcome_classifier_v1.cpp
  src/marriage_proposal_action_core_v1.cpp
  src/marriage_proposal_native_binder_v1.cpp
  src/marriage_proposal_resolution_journal_v1.cpp
  src/marriage_ranked_container_adapter_v1.cpp
  src/marriage_shared_glue_v1.cpp
  src/realm_law_governance_snapshot_v1.cpp
  src/realm_law_governance_source_adapter_v1.cpp
  src/realm_law_enact_action_v1.cpp
  src/realm_law_native_binder_v1.cpp
  src/realm_law_enact_mutation_abi_v1.cpp
  src/realm_law_native_shared_glue_v1.cpp
  src/realm_law_application_main_v1.cpp
  src/pending_character_interaction_context_v1.cpp
  src/pending_character_interaction_context_v1_mailbox.cpp
  src/pending_character_interaction_context_v1_serializer.cpp
  src/phase2_completion_observer_v1.cpp
  src/phase2_post_call_list_identity_observer_v1.cpp
  src/phase2_post_call_observer_v1.cpp
  src/phase2_producer_identity_observer_v1.cpp
  src/phase2_wrapper_entry_observer_v1.cpp
  src/phase2_wrapper_consumer_edge_observer_v1.cpp
  src/route_contact_horizon_v1_mailbox.cpp
  src/set_played_character_v1_mailbox.cpp
  src/raiktor_war_bound_regiment_v1.cpp
  src/raiktor_surrender_truce_v1.cpp
  src/raiktor_actual_truce_expiry_v1.cpp
  src/startup_dx11_render_context_draw_guard_v1.cpp
  src/startup_localize_current_root_guard_v1.cpp
  src/startup_rbx_null_call_guard_v1.cpp
  src/startup_widget_null_flag_call_guard_v1.cpp
  src/startup_particle2_consumer_null_guard_v1.cpp
  src/startup_particle2_null_guard_v1.cpp
  src/startup_particle2_stage_recorder_v1.cpp
  src/tactical_daily_sentinel_v1.cpp
  src/title_map_navigation_v1.cpp
  src/ingame_ui_navigation_v1.cpp
  src/title_map_navigation_v1_camera.cpp
  src/title_map_navigation_v1_mailbox.cpp
  src/title_map_navigation_v1_serializer.cpp
  src/war_entry_assessments_v1.cpp
  src/war_entry_assessments_v1_serializer.cpp
  src/war_occupation_targets_v1_serializer.cpp
  src/title_holder_v1_serializer.cpp
  src/projected_contact_scope_v1_serializer.cpp
  src/war_entry_assessments_v1_mailbox.cpp
  src/zhongguo_case_snapshot_v1.cpp
  src/zhongguo_case_snapshot_v1_mailbox.cpp
  src/zhongguo_case_snapshot_v1_serializer.cpp
  src/zhongguo_b1_cycle_snapshot_v1.cpp
  src/zhongguo_b1_cycle_snapshot_v1_mailbox.cpp
  src/zhongguo_b1_cycle_snapshot_v1_serializer.cpp
  src/zhongguo_ai_owned_case_snapshot_v1.cpp
  src/zhongguo_ai_owned_case_snapshot_v1_mailbox.cpp
  src/zhongguo_ai_owned_case_snapshot_v1_serializer.cpp
  src/zhongguo_b2_pip_snapshot_v1.cpp
  src/zhongguo_b2_pip_snapshot_v1_mailbox.cpp
  src/zhongguo_b2_pip_snapshot_v1_serializer.cpp
  src/zhongguo_incident_snapshot_v1.cpp
  src/zhongguo_incident_snapshot_v1_mailbox.cpp
  src/zhongguo_incident_snapshot_v1_serializer.cpp
  src/zhongguo_manager_governance_snapshot_v1.cpp
  src/zhongguo_manager_governance_snapshot_v1_mailbox.cpp
  src/zhongguo_manager_governance_snapshot_v1_serializer.cpp
  src/zhongguo_manager_subordinate_selector_v1.cpp
  src/zhongguo_manager_subordinate_selector_v1_serializer.cpp
  src/zhongguo_promotion_compensation_postcondition_v1.cpp
  src/zhongguo_promotion_compensation_postcondition_v1_mailbox.cpp
  src/zhongguo_compensation_af5_snapshot_v1.cpp
  src/zhongguo_compensation_af5_snapshot_v1_mailbox.cpp
  src/zhongguo_promotion_source_progress_v1_mailbox.cpp
  src/zhongguo_career_hc_workforce_postcondition_v1.cpp
  src/zhongguo_career_hc_workforce_postcondition_v1_serializer.cpp
  src/zhongguo_career_hc_workforce_postcondition_v1_mailbox.cpp
  src/zhongguo_projects_metrics_postcondition_v1.cpp
  src/zhongguo_projects_metrics_postcondition_v1_serializer.cpp
  src/zhongguo_projects_metrics_postcondition_v1_mailbox.cpp
  src/zhongguo_scoreboard_action_v1.cpp
  src/zhongguo_scoreboard_action_v1_mailbox.cpp
  src/zhongguo_scoreboard_production_v1.cpp
  src/zhongguo_scoreboard_state_v1.cpp
  src/zhongguo_scoreboard_state_v1_mailbox.cpp
  src/zhongguo_scoreboard_state_v1_serializer.cpp
  src/zhongguo_workforce_collective_snapshot_v1.cpp
  src/zhongguo_workforce_collective_snapshot_v1_mailbox.cpp
  src/zhongguo_workforce_owner_snapshot_v1.cpp
  src/zhongguo_workforce_owner_snapshot_v1_mailbox.cpp
  src/zhongguo_workforce_collective_snapshot_v1_serializer.cpp
  src/zhongguo_workforce_normal_exit_snapshot_v1.cpp
  src/zhongguo_workforce_normal_exit_snapshot_v1_mailbox.cpp
  src/zhongguo_workforce_normal_exit_snapshot_v1_serializer.cpp
  src/zhongguo_result_case_snapshot_v1.cpp
  src/zhongguo_result_case_snapshot_v1_mailbox.cpp
  src/zhongguo_result_case_snapshot_v1_serializer.cpp
)
target_include_directories(xar_ck3_bridge PRIVATE research src)
if(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  if(NOT XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
    target_sources(xar_ck3_bridge PRIVATE src/faction_gift_receivers_v1.cpp)
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/active_scheme_state_v1_private_observer.cpp
    src/active_scheme_state_v1_private_source_adapter.cpp
    src/active_scheme_state_v1_private_native_binder.cpp
    src/active_scheme_semantic_action_v1_private.cpp
    src/active_scheme_semantic_action_v1_private_native_command_adapter.cpp
    src/active_scheme_interaction_definition_resolver_v1_private.cpp
    src/active_scheme_paused_live_native_glue_v1_private.cpp
    src/active_scheme_precondition_command_binders_v1_private.cpp
    src/active_scheme_sway_private_transport_v1.cpp
  )
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/active_scheme_sway_formal_private_transport_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_REALM_LAW_PAUSED_PRIVATE_QUERY_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/realm_law_active_collection_11906.cpp
    src/realm_law_candidate_collection_11906.cpp
    src/realm_law_final_terms_11906.cpp
    src/realm_law_paused_private_transport_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_REALM_LAW_PAUSED_PRIVATE_QUERY_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/player_prisoner_collection_query_v1_private.cpp
    src/player_prisoner_collection_private_transport_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/character_interaction_preview_v1.cpp
    src/character_interaction_preview_v1_source_adapter.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/player_prisoner_ransom_private_v1.cpp
    src/player_prisoner_ransom_wire_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_PRISONER_CHILD_RELATION_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_PRISONER_CHILD_RELATION_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_PRISONER_TITLE_TIER_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_PRISONER_TITLE_TIER_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_WAR_BOUND_LOSS_CANDIDATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/raiktor_war_bound_loss_candidate_v1.cpp
  )
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_WAR_BOUND_LOSS_CANDIDATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_MAJOR_DECISION_FOUND_KINGDOM_INTERNAL_ROUTE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_MAJOR_DECISION_FOUND_KINGDOM_INTERNAL_ROUTE_V1=1
  )
endif()
target_link_libraries(xar_ck3_bridge PRIVATE
  xar_bridge_protocol xar_ck3_12002_runtime bcrypt)
target_compile_definitions(xar_ck3_bridge PRIVATE
  XAR_BRIDGE_VERSION="${PROJECT_VERSION}"
)
if(XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1=1
  )
endif()
if(XAR_CK3_ENABLE_AI_TERMINAL_REENTRY_DISPATCH_OBSERVER_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/ai_terminal_reentry_dispatch_observer_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_AI_TERMINAL_REENTRY_DISPATCH_OBSERVER_V1=1)
endif()
if(XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
  )
endif()
if(XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1)
  # The fifth caller-local guard is meaningful only after the four previously
  # live-proven startup faults are contained.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
    XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1=1
  )
endif()
if(XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1)
  # This successor seam is reached only after all five previous live-proven
  # startup faults are contained in the same exact-build bridge.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
    XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1=1
  )
endif()
if(XAR_CK3_ENABLE_COLD_MAP_VFS_OBSERVER_V1)
  # Read-only successor observer. It is reached in the frozen G2 startup
  # candidate only after the six independently live-proven guards.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
    XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_COLD_MAP_VFS_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_NAMED_PATH_583_ROOT_OBSERVER_V1)
  # Caller-local successor observer for the R275 chain. It coexists with the
  # cold-map VFS observer and records only the 0x583 resolver/root assignment.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
    XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_COLD_MAP_VFS_OBSERVER_V1=1
    XAR_CK3_ENABLE_NAMED_PATH_583_ROOT_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PDX_PATHS_583_PRODUCER_OBSERVER_V1)
  # Private read-only producer observer. The named-path and cold-map
  # downstream observers remain enabled for the same exact-build correlation.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
    XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_COLD_MAP_VFS_OBSERVER_V1=1
    XAR_CK3_ENABLE_NAMED_PATH_583_ROOT_OBSERVER_V1=1
    XAR_CK3_ENABLE_PDX_PATHS_583_PRODUCER_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_VFS_MOUNT_LIFECYCLE_OBSERVER_V1)
  # Private read-only successor observer. Keep the complete R280 producer and
  # downstream observer set in the same exact-build dump for time correlation.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
    XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_COLD_MAP_VFS_OBSERVER_V1=1
    XAR_CK3_ENABLE_NAMED_PATH_583_ROOT_OBSERVER_V1=1
    XAR_CK3_ENABLE_PDX_PATHS_583_PRODUCER_OBSERVER_V1=1
    XAR_CK3_ENABLE_VFS_MOUNT_LIFECYCLE_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHYSFS_MOUNTED_DATA_OBSERVER_V1)
  # Caller-local exact-build successor for the unique "Mounted Data" log
  # path. Keep the generic lifecycle observer enabled for an A/B receipt.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
    XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_COLD_MAP_VFS_OBSERVER_V1=1
    XAR_CK3_ENABLE_NAMED_PATH_583_ROOT_OBSERVER_V1=1
    XAR_CK3_ENABLE_PDX_PATHS_583_PRODUCER_OBSERVER_V1=1
    XAR_CK3_ENABLE_VFS_MOUNT_LIFECYCLE_OBSERVER_V1=1
    XAR_CK3_ENABLE_PHYSFS_MOUNTED_DATA_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_ZHONGGUO_SCOREBOARD_PRODUCTION_V1)
  # Candidate-only read-only verifier diagnostics. The action result and
  # hello capability list remain fail-closed until a retained live artifact
  # is reviewed and production promotion is made as a separate source change.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_ZHONGGUO_SCOREBOARD_PRODUCTION_V1=1
  )
endif()
if(XAR_CK3_ENABLE_ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1)
  # Private candidate-only exposure of the already wired read-only provider.
  # The default build remains unadvertised until a retained paused-live
  # source -> action -> provider-result artifact is reviewed separately.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1)
  # Private candidate-only exposure of the already wired read-only provider.
  # The default build remains unadvertised until a retained paused-live
  # source -> action -> provider-result artifact is reviewed separately.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1)
  # Private candidate-only exposure of the already wired read-only provider.
  # The default build remains unadvertised until the B4 route-B checkpoint
  # yields a retained provider frame and the promotion is reviewed separately.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1 OR
   XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1)
  # Read-only post-application provider. It remains absent from the default
  # capability list until a retained paused-live result is reviewed.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/h2743_preaction_existing_truce_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_H3937_PHYSICAL_INVENTORY_MAILBOX_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_H3937_PHYSICAL_INVENTORY_MAILBOX_V1=1
  )
endif()
if(XAR_CK3_ENABLE_STEWARD_DEVELOP_COUNTY_ENUMERATOR_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STEWARD_DEVELOP_COUNTY_ENUMERATOR_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_DOMAIN_CONSTRUCTION_CANDIDATE_OBSERVER_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/domain_construction_candidate_observer_v1.cpp
    src/domain_construction_candidate_observer_v1_serializer.cpp
  )
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_DOMAIN_CONSTRUCTION_CANDIDATE_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_DOMAIN_CONSTRUCTION_RUNTIME_OBSERVER_V1)
  if(MSVC)
    set_source_files_properties(
      src/bridge.cpp
      src/domain_construction_runtime_callsite_observer_v1.cpp
      src/domain_construction_runtime_callsite_observer_v1_serializer.cpp
      PROPERTIES COMPILE_OPTIONS "/W4;/WX;/permissive-"
    )
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/domain_construction_runtime_callsite_observer_v1.cpp
    src/domain_construction_runtime_callsite_observer_v1_serializer.cpp
  )
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_DOMAIN_CONSTRUCTION_RUNTIME_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_WORLD_BUILDING_ACTION_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_PLAYER_WORLD_BUILDING_ACTION_PRIVATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_COUNCIL_COMPOSITION_CANDIDATE_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_COUNCIL_COMPOSITION_CANDIDATE_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_MILITARY_PREPARATION_SUMMARY_PRIVATE_PROBE_V1)
  if(MSVC)
    set_source_files_properties(
      src/military_preparation_summary_v1.cpp
      src/military_preparation_summary_v1_binding.cpp
      src/military_preparation_summary_v1_private_probe.cpp
      src/military_preparation_summary_v1_serializer.cpp
      PROPERTIES COMPILE_OPTIONS "/W4;/WX;/permissive-"
    )
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/military_preparation_summary_v1.cpp
    src/military_preparation_summary_v1_binding.cpp
    src/military_preparation_summary_v1_private_probe.cpp
    src/military_preparation_summary_v1_serializer.cpp
  )
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_MILITARY_PREPARATION_SUMMARY_PRIVATE_PROBE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_FACTION_TARGETING_ROW_ASYNC_PRIVATE_PROBE_V1 OR
   XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  if(MSVC)
    set_source_files_properties(
      src/bridge.cpp
      src/faction_targeting_row_observer_v1.cpp
      src/faction_targeting_row_observer_v1_serializer.cpp
      src/faction_targeting_row_probe_v1.cpp
      src/faction_targeting_row_probe_v1_serializer.cpp
      PROPERTIES COMPILE_OPTIONS "/W4;/WX;/permissive-"
    )
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/faction_targeting_row_observer_v1.cpp
    src/faction_targeting_row_observer_v1_serializer.cpp
    src/faction_targeting_row_probe_v1.cpp
    src/faction_targeting_row_probe_v1_serializer.cpp
  )
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_FACTION_TARGETING_ROW_ASYNC_PRIVATE_PROBE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  if(MSVC)
    set_source_files_properties(
      src/bridge.cpp
      src/ck3_11906.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/faction_gift_mitigation_action_v1.cpp
      src/faction_gift_mitigation_source_action_adapter_v1.cpp
      src/faction_gift_mitigation_native_binder_v1.cpp
      src/faction_gift_receivers_v1.cpp
      src/faction_gift_mitigation_integration_gate_v1.cpp
      src/faction_gift_mitigation_async_glue_v1.cpp
      src/faction_gift_cold_recovery_v1.cpp
      PROPERTIES COMPILE_OPTIONS "/W4;/WX;/permissive-"
    )
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/faction_gift_mitigation_action_v1.cpp
    src/faction_gift_mitigation_source_action_adapter_v1.cpp
    src/faction_gift_mitigation_native_binder_v1.cpp
    src/faction_gift_receivers_v1.cpp
    src/faction_gift_mitigation_integration_gate_v1.cpp
    src/faction_gift_mitigation_async_glue_v1.cpp
    src/faction_gift_cold_recovery_v1.cpp
  )
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1=1
    XAR_CK3_ENABLE_G2_FACTION_TARGETING_ROW_ASYNC_PRIVATE_PROBE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_COUNCIL_COMPOSITION_STEWARD_CANDIDATES_PRIVATE_PROBE_V1)
  if(MSVC)
    set_source_files_properties(
      src/bridge.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/council_composition_steward_candidates_reader_v1.cpp
      src/council_composition_steward_candidates_binding_v1.cpp
      src/council_composition_steward_candidates_private_probe_v1.cpp
      PROPERTIES COMPILE_OPTIONS "/W4;/WX;/permissive-"
    )
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/council_composition_steward_candidates_private_probe_v1.cpp
  )
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_COUNCIL_COMPOSITION_STEWARD_CANDIDATES_PRIVATE_PROBE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_DEATH_SUCCESSION_MODAL_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_DEATH_SUCCESSION_MODAL_PRIVATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_CE1_TREATMENT_PRESENCE_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_CE1_TREATMENT_PRESENCE_PRIVATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_CE1_RECOVERY_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_CE1_RECOVERY_PRIVATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/player_lifestyle_snapshot_v1.cpp
    src/player_lifestyle_window_candidates_v1.cpp
    src/player_lifestyle_window_source_adapter_v1.cpp
    src/player_lifestyle_selection_action_v1.cpp
    src/player_lifestyle_selection_native_adapter_v1.cpp
    src/player_lifestyle_stock_perk_legality_v1.cpp
    src/player_lifestyle_stock_focus_legality_v1.cpp
    src/player_lifestyle_formal_precondition_v1.cpp
    src/player_lifestyle_formal_wire_v1.cpp
  )
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_M5_WAR_PRIMARY_CURRENT_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/prewar_scope_v1.cpp
    src/m5_primary_army_supply_v1.cpp
    src/m5_war_primary_readback_v1.cpp
    src/m5_war_primary_private_wire_v1.cpp
  )
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_M5_WAR_PRIMARY_CURRENT_PRIVATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_WAR_ACTOR_ARMY_ROLE_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/actor_army_role_private_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_WAR_ACTOR_ARMY_ROLE_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_MINOR_RELIGIOUS_WAR_DEFENDERS_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/minor_religious_war_defenders_v1.cpp
    src/minor_religious_war_defenders_private_wire_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_MINOR_RELIGIOUS_WAR_DEFENDERS_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_AUB_CONFIRM_STATE_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_CK3_ENABLE_AUB_CONFIRM_STATE_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_AUB_POLICY_OPTIONS_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_CK3_ENABLE_AUB_POLICY_OPTIONS_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_WHITE_CONTROL_ACTIONS_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_CK3_ENABLE_WHITE_CONTROL_ACTIONS_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_WHITE_RENDERED_TEXT_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_CK3_ENABLE_WHITE_RENDERED_TEXT_PRIVATE_V1=1)
endif()

if(XAR_CK3_ENABLE_WHITE_PLAYER_BUSINESS_VARIABLES_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_CK3_ENABLE_WHITE_PLAYER_BUSINESS_VARIABLES_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_FRONTEND_GAME_RULES_PRIVATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_FRONTEND_GAME_RULES_PRIVATE_V1=1)
endif()
if(XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_COUNCIL_ASSIGN_PRIVATE_ACTION_GATE_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_COUNCIL_ASSIGN_PRIVATE_ACTION_GATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_COUNCIL_FINAL_GATE_PRIVATE_QUERY_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_COUNCIL_FINAL_GATE_PRIVATE_QUERY_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_M5_HEIR_MARRIAGE_PRIVATE_ACTION_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_M5_HEIR_MARRIAGE_PRIVATE_ACTION_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_M5_CHILD_MATRILINEAL_PRIVATE_ACTION_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_M5_CHILD_MATRILINEAL_PRIVATE_ACTION_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/marriage_candidate_alliance_projection_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_CULTURE_INNOVATION_ASYNC_PRIVATE_PROBE_V1)
  if(MSVC)
    set_source_files_properties(
      src/bridge.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/culture_innovation_snapshot_v1.cpp
      src/culture_innovation_source_adapter_v1.cpp
      src/culture_innovation_snapshot_v1_mailbox.cpp
      PROPERTIES COMPILE_OPTIONS "/W4;/WX;/permissive-"
    )
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/culture_innovation_snapshot_v1.cpp
    src/culture_innovation_source_adapter_v1.cpp
    src/culture_innovation_snapshot_v1_mailbox.cpp
  )
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_CULTURE_INNOVATION_ASYNC_PRIVATE_PROBE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_PLANNING_SNAPSHOT_PRIVATE_GLUE_V1)
  if(MSVC)
    set_source_files_properties(
      src/activity_planning_snapshot_v1_private_observer.cpp
      src/activity_planning_snapshot_v1_source_adapter.cpp
      src/activity_planning_snapshot_v1_native_binder.cpp
      src/activity_planning_snapshot_v1_application_glue.cpp
      PROPERTIES COMPILE_OPTIONS "/W4;/WX;/permissive-"
    )
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/activity_planning_snapshot_v1_private_observer.cpp
    src/activity_planning_snapshot_v1_source_adapter.cpp
    src/activity_planning_snapshot_v1_native_binder.cpp
    src/activity_planning_snapshot_v1_application_glue.cpp
  )
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVITY_PLANNING_SNAPSHOT_PRIVATE_GLUE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_PLANNER_DIAG_PRIVATE_QUERY_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/activity_planner_diag_v1.cpp
    src/activity_planner_diag_private_transport_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVITY_PLANNER_DIAG_PRIVATE_QUERY_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/activity_planner_diag_v1.cpp
    src/activity_feast_planner_open_v1.cpp
    src/activity_feast_planner_open_private_transport_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1)
  if(NOT XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1 AND
     NOT XAR_CK3_ENABLE_G2_ACTIVITY_PLANNER_DIAG_PRIVATE_QUERY_V1)
    target_sources(xar_ck3_bridge PRIVATE src/activity_planner_diag_v1.cpp)
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/activity_stage1_option_read_v1.cpp
    src/activity_stage1_option_read_private_transport_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1=1)
  if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_CONFIRM_PRIVATE_V1)
    target_compile_definitions(xar_ck3_bridge PRIVATE
      XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_CONFIRM_PRIVATE_V1=1)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_OPTION_READ_PRIVATE_V1)
    target_compile_definitions(xar_ck3_bridge PRIVATE
      XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_OPTION_READ_PRIVATE_V1=1)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_GATE_READ_PRIVATE_V1)
    target_sources(xar_ck3_bridge PRIVATE
      src/activity_stage2_gate_read_v1.cpp)
    target_compile_definitions(xar_ck3_bridge PRIVATE
      XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_GATE_READ_PRIVATE_V1=1)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_LOCATION_READ_PRIVATE_V1)
    target_sources(xar_ck3_bridge PRIVATE
      src/activity_stage2_location_read_v1.cpp)
    target_compile_definitions(xar_ck3_bridge PRIVATE
      XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_LOCATION_READ_PRIVATE_V1=1)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1)
    target_sources(xar_ck3_bridge PRIVATE
      src/activity_stage2_destination_select_v1.cpp
      src/activity_stage2_confirm_v1.cpp
      src/activity_stage2_destination_select_private_transport_v1.cpp)
    target_compile_definitions(xar_ck3_bridge PRIVATE
      XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1=1)
  endif()
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1)
  if(NOT XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1 AND
     NOT XAR_CK3_ENABLE_G2_ACTIVITY_PLANNER_DIAG_PRIVATE_QUERY_V1 AND
     NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1)
    target_sources(xar_ck3_bridge PRIVATE src/activity_planner_diag_v1.cpp)
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/activity_stage5_canstart_read_v1.cpp
    src/activity_stage5_canstart_private_transport_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_COST_SLOT12_PASSIVE_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/activity_cost_slot12_passive_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVITY_COST_SLOT12_PASSIVE_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1)
  if(NOT XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1 AND
     NOT XAR_CK3_ENABLE_G2_ACTIVITY_PLANNER_DIAG_PRIVATE_QUERY_V1 AND
     NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1 AND
     NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1)
    target_sources(xar_ck3_bridge PRIVATE src/activity_planner_diag_v1.cpp)
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/activity_stage5_gold_cost_v1.cpp
    src/activity_stage5_gold_cost_private_transport_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/activity_stage5_feast_full_cost_v1.cpp
    src/activity_stage5_canstart_failure_display_v1.cpp
    src/activity_stage5_feast_full_cost_private_transport_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/activity_feast_resource_balance_v1.cpp
    src/activity_hosted_identity_v1.cpp
    src/activity_stage5_feast_guest_join_v1.cpp
    src/activity_feast_guest_candidate_v1.cpp
    src/activity_feast_stage5_start_v1.cpp
    src/activity_feast_stage5_start_private_transport_v1.cpp
    src/activity_feast_stage5_start_private_serializer_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_CANDIDATE_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/activity_feast_guest_candidate_private_transport_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_CANDIDATE_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_OPINION_PRIVATE_V1)
  if(NOT XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1 AND
     NOT XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
    target_sources(xar_ck3_bridge PRIVATE src/faction_gift_receivers_v1.cpp)
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/activity_feast_guest_opinion_v1.cpp
    src/activity_feast_guest_opinion_private_transport_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_OPINION_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_TOGGLE_PRIVATE_V1)
  if(NOT XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1 AND
     NOT XAR_CK3_ENABLE_G2_ACTIVITY_PLANNER_DIAG_PRIVATE_QUERY_V1 AND
     NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1 AND
     NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1 AND
     NOT XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1)
    target_sources(xar_ck3_bridge PRIVATE src/activity_planner_diag_v1.cpp)
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/activity_feast_guest_rule_toggle_v1.cpp
    src/activity_feast_guest_rule_toggle_private_transport_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_TOGGLE_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/activity_feast_guest_rule_provenance_v1.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1=1)
endif()
if(XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1 OR
   XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2=1
  )
endif()
if(XAR_CK3_ENABLE_G2_TRUCE_DEFAULT_LEAF_DIAGNOSTICS_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_G2_TRUCE_DEFAULT_LEAF_DIAGNOSTICS_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_COMPLETION_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_COMPLETION_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_WRAPPER_ENTRY_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_WRAPPER_ENTRY_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_POST_CALL_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_POST_CALL_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_POST_CALL_LIST_IDENTITY_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_POST_CALL_LIST_IDENTITY_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_PRODUCER_CONSUMER_CORRELATION_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_PRODUCER_CONSUMER_CORRELATION_OBSERVER_V1=1
    XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1=1
    XAR_CK3_ENABLE_PHASE2_COMPLETION_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_V1=1
    XAR_CK3_ENABLE_PHASE2_WRAPPER_ENTRY_OBSERVER_V1=1
    XAR_CK3_ENABLE_PHASE2_PRODUCER_CONSUMER_CORRELATION_OBSERVER_V1=1
    XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1=1
    XAR_CK3_ENABLE_PHASE2_COMPLETION_OBSERVER_V1=1
  )
endif()
set_target_properties(xar_ck3_bridge PROPERTIES
  OUTPUT_NAME "xar_ck3_bridge"
)
file(GENERATE OUTPUT "${CMAKE_BINARY_DIR}/ck3_12002_runtime_sources.txt"
  CONTENT "$<JOIN:$<TARGET_PROPERTY:xar_ck3_12002_runtime,SOURCES>,\n>\n")
file(GENERATE OUTPUT "${CMAKE_BINARY_DIR}/ck3_bridge_sources.txt"
  CONTENT "$<JOIN:$<TARGET_PROPERTY:xar_ck3_bridge,SOURCES>,\n>\n")

add_executable(xar_ck3_bridge_host
  src/host.cpp
)
target_link_libraries(xar_ck3_bridge_host PRIVATE xar_bridge_protocol)

add_executable(xar_ck3_bridge_attach_host
  src/attach_host.cpp
)
target_link_libraries(xar_ck3_bridge_attach_host PRIVATE xar_bridge_protocol)

add_executable(xar_ck3_bridge_injector
  src/injector_main.cpp
)
target_link_libraries(xar_ck3_bridge_injector PRIVATE xar_bridge_injector)

add_executable(xar_ck3_bridge_target
  src/target.cpp
)

if(XAR_CK3_ENABLE_G2_WAR_BOUND_PRIVATE_CAPTURE_V1)
  add_executable(xar_ck3_raiktor_war_bound_private_capture_v1
    research/raiktor_war_bound_private_capture_v1.cpp
  )
  target_compile_definitions(
    xar_ck3_raiktor_war_bound_private_capture_v1 PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_raiktor_war_bound_private_capture_v1 PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_raiktor_war_bound_private_capture_v1 PRIVATE
      /W4 /permissive- /EHsc)
  endif()
endif()

if(MSVC)
  foreach(target
      xar_bridge_protocol
      xar_bridge_injector
      xar_ck3_bridge
      xar_ck3_bridge_host
      xar_ck3_bridge_attach_host
      xar_ck3_bridge_injector
      xar_ck3_bridge_target)
    target_compile_options(${target} PRIVATE /W4 /permissive- /EHsc)
  endforeach()
endif()

include(CTest)
if(BUILD_TESTING)
  add_executable(xar_ck3_12003_siege_membership_test
    src/ck3_12002_province.cpp
    src/war_occupation_targets_v1_serializer.cpp
    src/ck3_12003_siege_membership_test.cpp)
  target_include_directories(xar_ck3_12003_siege_membership_test PRIVATE include)
  if(MSVC)
    target_compile_options(xar_ck3_12003_siege_membership_test PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  add_test(NAME xar_ck3_12003_siege_membership_test
    COMMAND xar_ck3_12003_siege_membership_test)
  add_executable(xar_ck3_12003_title_holder_test
    src/ck3_12002_province.cpp
    src/ck3_12003_title_holder.cpp
    src/title_holder_v1_serializer.cpp
    src/ck3_12003_title_holder_test.cpp)
  target_include_directories(xar_ck3_12003_title_holder_test PRIVATE include)
  target_compile_definitions(xar_ck3_12003_title_holder_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_title_holder_test PRIVATE
      /W4 /WX /Gy /permissive- /EHsc)
    target_link_options(xar_ck3_12003_title_holder_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_title_holder_test
    COMMAND xar_ck3_12003_title_holder_test
      "${CMAKE_BINARY_DIR}/ck3_12003_title_holder_wire")
  if(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1 AND
     XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
    add_executable(xar_ck3_12002_call_ally_sender_test
      src/ck3_12002.cpp
      src/ck3_12002_commands.cpp
      src/ck3_12002_context.cpp
      src/ck3_12002_family_obligations_alliance.cpp
      src/ck3_12002_call_ally_sender_test.cpp)
    add_executable(xar_ck3_12003_call_ally_mailbox_test
      src/ck3_12002_family_obligations_mailbox.cpp
      src/ck3_12002_family_obligations_wire.cpp
      src/ck3_12003_call_ally_private_action.cpp
      src/ck3_12002_query_mailbox.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/protocol.cpp
      src/ck3_12003_abi_profile.cpp
      src/ck3_12003_adapter.cpp
      src/ck3_12003_call_ally_mailbox_test.cpp)
    add_executable(xar_ck3_12002_family_obligations_no_entry_test
      src/ck3_12002.cpp
      src/ck3_12002_commands.cpp
      src/ck3_12002_context.cpp
      src/ck3_12002_family_obligations_alliance.cpp
      src/ck3_12002_family_obligations_wire.cpp
      src/ck3_12002_family_obligations_no_entry_test.cpp)
    foreach(call_ally_target IN ITEMS
        xar_ck3_12002_call_ally_sender_test xar_ck3_12003_call_ally_mailbox_test
        xar_ck3_12002_family_obligations_no_entry_test)
      target_include_directories(${call_ally_target} PRIVATE include)
      target_compile_definitions(${call_ally_target} PRIVATE
        NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
        XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1=1)
      if(MSVC)
        target_compile_options(${call_ally_target} PRIVATE /W4 /WX /Gy /permissive- /EHsc)
        target_link_options(${call_ally_target} PRIVATE /OPT:REF)
      endif()
    endforeach()
    target_link_libraries(xar_ck3_12003_call_ally_mailbox_test PRIVATE user32)
    add_test(NAME xar_ck3_12002_call_ally_sender_test
      COMMAND xar_ck3_12002_call_ally_sender_test)
    add_test(NAME xar_ck3_12002_family_obligations_no_entry_test
      COMMAND xar_ck3_12002_family_obligations_no_entry_test
        "${CMAKE_BINARY_DIR}/ck3_12002_call_ally_no_entry.json")
    add_test(NAME xar_ck3_12003_call_ally_mailbox_test
      COMMAND xar_ck3_12003_call_ally_mailbox_test
        "${CMAKE_BINARY_DIR}/ck3_12003_call_ally_to_war_submit.json"
        "${CMAKE_BINARY_DIR}/ck3_12003_call_ally_to_war_quote.json")
  endif()
  # The 1.20 feast fixtures exercise pure shared readers even when the
  # corresponding private live feature is disabled in the production DLL.
  add_library(xar_ck3_12002_feast_fixture_support STATIC
    src/activity_planner_diag_v1.cpp
    src/activity_cost_slot12_passive_v1.cpp
    src/activity_stage5_gold_cost_v1.cpp
    src/activity_stage5_canstart_read_v1.cpp
    src/activity_stage5_canstart_failure_display_v1.cpp
    src/activity_stage5_feast_full_cost_v1.cpp
    src/activity_stage5_feast_guest_join_v1.cpp
    src/activity_feast_guest_candidate_v1.cpp
    src/activity_feast_guest_opinion_v1.cpp
    src/activity_feast_guest_rule_provenance_v1.cpp
    src/activity_feast_guest_rule_toggle_v1.cpp
    src/activity_feast_planner_open_v1.cpp
    src/activity_feast_resource_balance_v1.cpp
    src/activity_feast_stage5_start_v1.cpp
    src/activity_feast_stage5_start_private_serializer_v1.cpp
    src/activity_hosted_identity_v1.cpp)
  target_include_directories(xar_ck3_12002_feast_fixture_support PRIVATE include)
  target_compile_definitions(xar_ck3_12002_feast_fixture_support PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12002_feast_fixture_support PRIVATE
      /UNDEBUG /W4 /permissive- /EHsc)
  endif()
  set(XAR_CK3_12002_FROZEN_EXE "${XAR_CK3_EXECUTABLE_PATH}"
    CACHE FILEPATH "Frozen 1.20 executable for offline reader fixtures")
  file(GLOB XAR_CK3_12002_FIXTURES CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_*_test.cpp")
  foreach(fixture IN LISTS XAR_CK3_12002_FIXTURES)
    get_filename_component(fixture_name "${fixture}" NAME_WE)
    if((fixture_name MATCHES "^ck3_12002_prewar" AND
        NOT XAR_CK3_ENABLE_G2_M5_PREWAR_SOURCES_PRIVATE_QUERY_V1) OR
       (fixture_name MATCHES "^ck3_12002_war_cash" AND
        NOT XAR_CK3_ENABLE_G2_M5_WAR_CASH_PRIVATE_QUERY_V1) OR
       fixture_name MATCHES "^ck3_12002_(sway_completion|sway_outcome|epidemic)" OR
        fixture_name STREQUAL "ck3_12002_family_obligations_alliance_test" OR
        fixture_name STREQUAL "ck3_12002_family_obligations_no_entry_test" OR
        fixture_name STREQUAL "ck3_12002_call_ally_sender_test" OR
       (fixture_name MATCHES "^ck3_12002_religion" AND
        (NOT XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1 OR
         NOT fixture_name STREQUAL "ck3_12002_religion_context_test")) OR
       fixture_name STREQUAL "ck3_12002_religion_mailbox_test" OR
       fixture_name STREQUAL "ck3_12002_nonwar_router_test")
      continue()
    endif()
    if(fixture_name MATCHES "^ck3_12002_family" AND
       NOT XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
      continue()
    endif()
    set(fixture_target "xar_${fixture_name}")
    add_executable(${fixture_target} "${fixture}")
    target_link_libraries(${fixture_target} PRIVATE xar_ck3_12002_runtime)
    target_include_directories(${fixture_target} PRIVATE src research)
    if(fixture_name MATCHES "^ck3_12002_(activity_feast_(costs|guest_rule|guest_wire|wire|planner_open_v1|start)|activity_hosted_identity|feast_guests|feast_outcome_values)_test$")
      target_link_libraries(${fixture_target} PRIVATE
        xar_ck3_12002_feast_fixture_support)
    endif()
    if(fixture_name STREQUAL "ck3_12002_activity_feast_router_test")
      # Dispatcher spies exercise these routes without enabling their private
      # production features or the real native transport callbacks.
      target_sources(${fixture_target} PRIVATE
        src/ck3_12002_activity_feast_router.cpp)
      target_compile_definitions(${fixture_target} PRIVATE
        XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1=1
        XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1=1
        XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1=1)
      target_link_libraries(${fixture_target} PRIVATE
        xar_ck3_12002_feast_fixture_support xar_bridge_protocol)
    endif()
    if(fixture_name STREQUAL "ck3_12002_nonwar_mailbox_test")
      target_link_libraries(${fixture_target} PRIVATE user32)
    endif()
    if(fixture_name MATCHES "^ck3_12002_family" OR
       (XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1 AND
        fixture_name MATCHES "^ck3_12002_(adapter|semantic_adapter)_test$"))
      target_sources(${fixture_target} PRIVATE
        src/current_first_heir_relationship_v1.cpp
        src/observed_heir_marriage_private_v1.cpp)
    endif()
    if(fixture_name STREQUAL "ck3_12002_family_ranked_test")
      target_sources(${fixture_target} PRIVATE
        src/marriage_matchmaking_observer_v1.cpp)
    endif()
    if(MSVC)
      target_compile_options(${fixture_target} PRIVATE /UNDEBUG /W4 /permissive- /EHsc)
    else()
      target_compile_options(${fixture_target} PRIVATE -UNDEBUG)
    endif()
    if(fixture_name STREQUAL "ck3_12002_thread_runtime_test")
      add_test(NAME "xar_${fixture_name}" COMMAND ${fixture_target}
        "${XAR_CK3_12002_FROZEN_EXE}")
    elseif(fixture_name STREQUAL "ck3_12002_activity_feast_wire_test")
      add_test(NAME "xar_${fixture_name}" COMMAND ${fixture_target}
        "${CMAKE_CURRENT_BINARY_DIR}/${fixture_name}-hosted.json"
        "${CMAKE_CURRENT_BINARY_DIR}/${fixture_name}-ordinary.json")
    else()
      add_test(NAME "xar_${fixture_name}" COMMAND ${fixture_target})
    endif()
    if(fixture_name STREQUAL "ck3_12002_semantic_adapter_test")
      add_test(NAME xar_ck3_12003_semantic_worker_test
        COMMAND ${fixture_target} --patch3)
    endif()
  endforeach()

  # Dispatcher spies cover only the production routing seam; they deliberately
  # do not link the runtime's actual domain executors or adapter implementation.
  foreach(router_variant IN ITEMS default selected)
    set(router_target "xar_ck3_12002_nonwar_router_${router_variant}_test")
    add_executable(${router_target}
      src/ck3_12002_nonwar_router.cpp
      src/ck3_12003_abi_profile.cpp
      src/ck3_12002_nonwar_router_test.cpp)
    target_link_libraries(${router_target} PRIVATE xar_bridge_protocol)
    target_include_directories(${router_target} PRIVATE include src)
    if(router_variant STREQUAL "selected")
      target_compile_definitions(${router_target} PRIVATE
        XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1=1
        XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1=1
        XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1=1
        XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1=1
        XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1=1)
    endif()
    if(MSVC)
      target_compile_options(${router_target} PRIVATE /W4 /WX /permissive- /EHsc)
    endif()
    add_test(NAME ${router_target} COMMAND ${router_target})
  endforeach()

  foreach(county_router_variant IN ITEMS default clergy)
    set(county_router_target "xar_ck3_12003_county_task_router_${county_router_variant}_test")
    add_executable(${county_router_target}
      src/ck3_12002_nonwar_router.cpp
      src/ck3_12003_abi_profile.cpp
      src/ck3_12002_nonwar_router_test.cpp)
    target_link_libraries(${county_router_target} PRIVATE xar_bridge_protocol)
    target_include_directories(${county_router_target} PRIVATE include src)
    target_compile_definitions(${county_router_target} PRIVATE
      XAR_G2_ROUTER_INCREMENT_COUNTY_TASK_ACTION_ONLY=1)
    if(county_router_variant STREQUAL "clergy")
      target_compile_definitions(${county_router_target} PRIVATE
        XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1=1)
    endif()
    if(MSVC)
      target_compile_options(${county_router_target} PRIVATE /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME ${county_router_target} COMMAND ${county_router_target})
  endforeach()

  if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/religion-mailbox-wire")
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/repentance-mailbox-wire")
    add_executable(xar_ck3_12003_player_repentance_context_test
      src/ck3_12002.cpp
      src/religion_rite_governance12002_clergy.cpp
      src/ck3_12003_mystical_communion_decision_terms.cpp
      src/ck3_12003_repentance_petition_decision_terms.cpp
      src/ck3_12003_repentance_recipient_candidates.cpp
      src/ck3_12003_player_repentance_context.cpp
      src/ck3_12003_player_repentance_wire.cpp
      src/ck3_12003_repentance_fallback.cpp
      src/ck3_12003_repentance_recovery_inputs.cpp
      src/ck3_12003_repentance_pam_route.cpp
      src/ck3_12002_phase_character.cpp
      src/ck3_12003_player_repentance_context_test.cpp)
    add_executable(xar_ck3_12003_repentance_petition_decision_terms_test
      src/ck3_12003_mystical_communion_decision_terms.cpp
      src/ck3_12003_repentance_petition_decision_terms.cpp
      src/ck3_12003_repentance_petition_decision_terms_test.cpp)
    target_include_directories(xar_ck3_12003_repentance_petition_decision_terms_test PRIVATE include)
    if(MSVC)
      target_compile_options(xar_ck3_12003_repentance_petition_decision_terms_test PRIVATE
        /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/repentance-petition-wire")
    add_test(NAME xar_ck3_12003_repentance_petition_decision_terms_test
      COMMAND xar_ck3_12003_repentance_petition_decision_terms_test
        "${CMAKE_BINARY_DIR}/repentance-petition-wire")

    add_executable(xar_ck3_12003_repentance_recipient_candidates_test
      src/ck3_12002.cpp
      src/religion_rite_governance12002_clergy.cpp
      src/ck3_12002_phase_character.cpp
      src/ck3_12003_player_repentance_context.cpp
      src/ck3_12003_repentance_recipient_candidates.cpp
      src/ck3_12003_repentance_petition_decision_terms.cpp
      src/ck3_12003_mystical_communion_decision_terms.cpp
      src/ck3_12003_player_repentance_wire.cpp
      src/ck3_12003_repentance_fallback.cpp
      src/ck3_12003_repentance_recovery_inputs.cpp
      src/ck3_12003_repentance_pam_route.cpp
      src/ck3_12003_repentance_recipient_candidates_test.cpp)
    target_include_directories(xar_ck3_12003_repentance_recipient_candidates_test PRIVATE include)
    target_compile_definitions(xar_ck3_12003_repentance_recipient_candidates_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1)
    if(MSVC)
      target_compile_options(xar_ck3_12003_repentance_recipient_candidates_test PRIVATE
        /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/repentance-candidates-wire")
    add_test(NAME xar_ck3_12003_repentance_recipient_candidates_test
      COMMAND xar_ck3_12003_repentance_recipient_candidates_test
        "${CMAKE_BINARY_DIR}/repentance-candidates-wire")

    add_executable(xar_ck3_12003_repentance_fallback_test
      src/ck3_12003_repentance_fallback.cpp
      src/ck3_12003_repentance_fallback_test.cpp)
    add_executable(xar_ck3_12003_repentance_recovery_inputs_test
      src/ck3_12003_repentance_recovery_inputs.cpp
      src/ck3_12003_repentance_recovery_inputs_test.cpp)
    add_executable(xar_ck3_12003_repentance_pam_route_test
      src/ck3_12003_repentance_pam_route.cpp
      src/ck3_12003_repentance_pam_route_test.cpp)
    add_executable(xar_ck3_12003_repentance_fallback_merge_test
      src/ck3_12002_phase_character.cpp
      src/ck3_12003_player_repentance_context.cpp
      src/ck3_12003_repentance_recipient_candidates.cpp
      src/ck3_12003_repentance_petition_decision_terms.cpp
      src/ck3_12003_mystical_communion_decision_terms.cpp
      src/ck3_12003_repentance_fallback.cpp
      src/ck3_12003_repentance_recovery_inputs.cpp
      src/ck3_12003_repentance_pam_route.cpp
      src/ck3_12003_player_repentance_wire.cpp
      src/ck3_12003_repentance_fallback_merge_test.cpp)
    foreach(repentance_v36_test
        xar_ck3_12003_repentance_fallback_test
        xar_ck3_12003_repentance_recovery_inputs_test
        xar_ck3_12003_repentance_pam_route_test
        xar_ck3_12003_repentance_fallback_merge_test)
      target_include_directories(${repentance_v36_test} PRIVATE include)
      target_compile_definitions(${repentance_v36_test} PRIVATE
        XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1)
      if(MSVC)
        target_compile_options(${repentance_v36_test} PRIVATE
          /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
      endif()
      add_test(NAME ${repentance_v36_test} COMMAND ${repentance_v36_test}
        "${CMAKE_BINARY_DIR}/repentance-v36-wire")
    endforeach()
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/repentance-v36-wire")

    target_include_directories(xar_ck3_12003_player_repentance_context_test PRIVATE include)
    target_compile_definitions(xar_ck3_12003_player_repentance_context_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1)
    if(MSVC)
      target_compile_options(xar_ck3_12003_player_repentance_context_test PRIVATE
        /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_ck3_12003_player_repentance_context_test
      COMMAND xar_ck3_12003_player_repentance_context_test
        "${CMAKE_BINARY_DIR}/repentance-mailbox-wire")

    add_executable(xar_ck3_12002_religion_mailbox_test
      src/ck3_12002.cpp
      src/ck3_12002_religion_context.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_religion_mailbox.cpp
      src/ck3_12003_spiritual_fulfillment_progress.cpp
      src/ck3_12003_mystical_communion_decision_terms.cpp
      src/ck3_12003_pilgrimage_activity_type_terms.cpp
      src/ck3_12003_confession_decision_terms.cpp
      src/ck3_12003_confession_rite_permission.cpp
      src/religion_doctrine12002_tenet_rows.cpp
      src/religion_reform12002_tenet_sources.cpp
      src/religion_reform12002_window.cpp
      src/ck3_12003_church_income_profile.cpp
      src/ck3_12003_spiritual_fulfillment_type.cpp
      src/ck3_12003_church_tax_inputs.cpp
      src/ck3_12003_player_devotion_profile.cpp
      src/ck3_12003_player_rite_virtue_sin_profile.cpp
      src/ck3_12003_vow_of_poverty_terms.cpp
      src/ck3_12002_religion_mailbox_test.cpp)
    target_include_directories(xar_ck3_12002_religion_mailbox_test PRIVATE include)
    target_link_libraries(xar_ck3_12002_religion_mailbox_test PRIVATE
      xar_bridge_protocol user32)
    target_compile_definitions(xar_ck3_12002_religion_mailbox_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1
      XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1)
    if(MSVC)
      target_compile_options(xar_ck3_12002_religion_mailbox_test PRIVATE
        /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_ck3_12002_religion_mailbox_test
      COMMAND xar_ck3_12002_religion_mailbox_test
        "${CMAKE_BINARY_DIR}/religion-mailbox-wire")

    # Fixed permission shared wiring: one owner case, false/read-fault frames.
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/religion-confession-permission-mailbox-wire")
    add_executable(xar_ck3_12003_confession_permission_mailbox_test
      src/ck3_12002.cpp
      src/ck3_12002_religion_context.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/ck3_12003_adapter.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_religion_mailbox.cpp
      src/ck3_12003_spiritual_fulfillment_progress.cpp
      src/ck3_12003_mystical_communion_decision_terms.cpp
      src/ck3_12003_pilgrimage_activity_type_terms.cpp
      src/ck3_12003_confession_decision_terms.cpp
      src/ck3_12003_confession_rite_permission.cpp
      src/religion_doctrine12002_tenet_rows.cpp
      src/religion_reform12002_tenet_sources.cpp
      src/religion_reform12002_window.cpp
      src/ck3_12003_church_income_profile.cpp
      src/ck3_12003_spiritual_fulfillment_type.cpp
      src/ck3_12003_church_tax_inputs.cpp
      src/ck3_12003_confession_permission_mailbox_test.cpp)
    target_include_directories(xar_ck3_12003_confession_permission_mailbox_test PRIVATE include)
    target_link_libraries(xar_ck3_12003_confession_permission_mailbox_test PRIVATE
      xar_bridge_protocol user32)
    target_compile_definitions(xar_ck3_12003_confession_permission_mailbox_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1
      XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1
      XAR_RELIGION_CONFESSION_PERMISSION_STANDALONE_RENDERER=1)
    if(MSVC)
      target_compile_options(xar_ck3_12003_confession_permission_mailbox_test PRIVATE
        /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_ck3_12003_confession_permission_mailbox_test
      COMMAND xar_ck3_12003_confession_permission_mailbox_test
        "${CMAKE_BINARY_DIR}/religion-confession-permission-mailbox-wire")

    # One synthetic owner case covers both new siblings through the real mailbox.
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/religion-type-tax-mailbox-wire")
    add_executable(xar_ck3_12003_religion_type_tax_mailbox_test
      src/ck3_12002.cpp
      src/ck3_12002_religion_context.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/ck3_12003_adapter.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_religion_mailbox.cpp
      src/ck3_12003_spiritual_fulfillment_progress.cpp
      src/ck3_12003_mystical_communion_decision_terms.cpp
      src/ck3_12003_pilgrimage_activity_type_terms.cpp
      src/ck3_12003_confession_decision_terms.cpp
      src/ck3_12003_confession_rite_permission.cpp
      src/religion_doctrine12002_tenet_rows.cpp
      src/religion_reform12002_tenet_sources.cpp
      src/religion_reform12002_window.cpp
      src/ck3_12003_church_income_profile.cpp
      src/ck3_12003_spiritual_fulfillment_type.cpp
      src/ck3_12003_church_tax_inputs.cpp
      src/ck3_12003_player_devotion_profile.cpp
      src/ck3_12003_player_rite_virtue_sin_profile.cpp
      src/ck3_12003_vow_of_poverty_terms.cpp
      src/ck3_12003_religion_type_tax_mailbox_test.cpp)
    target_include_directories(xar_ck3_12003_religion_type_tax_mailbox_test PRIVATE include)
    target_link_libraries(xar_ck3_12003_religion_type_tax_mailbox_test PRIVATE
      xar_bridge_protocol user32)
    target_compile_definitions(xar_ck3_12003_religion_type_tax_mailbox_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1
      XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1
      XAR_RELIGION_TYPE_TAX_STANDALONE_RENDERER=1)
    if(MSVC)
      target_compile_options(xar_ck3_12003_religion_type_tax_mailbox_test PRIVATE
        /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_ck3_12003_religion_type_tax_mailbox_test
      COMMAND xar_ck3_12003_religion_type_tax_mailbox_test
        "${CMAKE_BINARY_DIR}/religion-type-tax-mailbox-wire")

    # Focused synthetic owner fixture for devotion, current Rite classification and vow terms.
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/religion-devotion-virtues-mailbox-wire")
    add_executable(xar_ck3_12003_religion_devotion_virtues_mailbox_test
      src/ck3_12002.cpp
      src/ck3_12002_religion_context.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/ck3_12003_adapter.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_religion_mailbox.cpp
      src/ck3_12003_spiritual_fulfillment_progress.cpp
      src/ck3_12003_mystical_communion_decision_terms.cpp
      src/ck3_12003_pilgrimage_activity_type_terms.cpp
      src/ck3_12003_confession_decision_terms.cpp
      src/ck3_12003_church_income_profile.cpp
      src/ck3_12003_spiritual_fulfillment_type.cpp
      src/ck3_12003_church_tax_inputs.cpp
      src/ck3_12003_player_devotion_profile.cpp
      src/ck3_12003_player_rite_virtue_sin_profile.cpp
      src/ck3_12003_vow_of_poverty_terms.cpp
      src/ck3_12003_religion_devotion_virtues_mailbox_test.cpp)
    target_include_directories(xar_ck3_12003_religion_devotion_virtues_mailbox_test PRIVATE include)
    target_link_libraries(xar_ck3_12003_religion_devotion_virtues_mailbox_test PRIVATE
      xar_bridge_protocol user32)
    target_compile_definitions(xar_ck3_12003_religion_devotion_virtues_mailbox_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1
      XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1
      XAR_RELIGION_TYPE_TAX_STANDALONE_RENDERER=1)
    if(MSVC)
      target_compile_options(xar_ck3_12003_religion_devotion_virtues_mailbox_test PRIVATE
        /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_ck3_12003_religion_devotion_virtues_mailbox_test
      COMMAND xar_ck3_12003_religion_devotion_virtues_mailbox_test
        "${CMAKE_BINARY_DIR}/religion-devotion-virtues-mailbox-wire")
  endif()

  # R3 named mailbox fixtures use owner standalone source recipes.
  if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/pilgrimage-headless-mailbox-wire")
    add_executable(xar_ck3_12003_pilgrimage_headless_mailbox_test
      src/ck3_12002.cpp
      src/ck3_12002_religion_context.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/ck3_12003_adapter.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_religion_mailbox.cpp
      src/ck3_12003_spiritual_fulfillment_progress.cpp
      src/ck3_12003_mystical_communion_decision_terms.cpp
      src/ck3_12003_pilgrimage_activity_type_terms.cpp
      src/ck3_12003_confession_decision_terms.cpp
      src/ck3_12003_church_income_profile.cpp
      src/ck3_12003_spiritual_fulfillment_type.cpp
      src/ck3_12003_church_tax_inputs.cpp
      src/ck3_12003_pilgrimage_headless_mailbox_test.cpp)
    target_include_directories(xar_ck3_12003_pilgrimage_headless_mailbox_test PRIVATE include)
    target_link_libraries(xar_ck3_12003_pilgrimage_headless_mailbox_test PRIVATE
      xar_bridge_protocol user32)
    target_compile_definitions(xar_ck3_12003_pilgrimage_headless_mailbox_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1
      XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1
      XAR_PILGRIMAGE_COMBINED_STANDALONE_RENDERER=1)
    if(MSVC)
      target_compile_options(xar_ck3_12003_pilgrimage_headless_mailbox_test PRIVATE
        /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_ck3_12003_pilgrimage_headless_mailbox_test
      COMMAND xar_ck3_12003_pilgrimage_headless_mailbox_test
        "${CMAKE_BINARY_DIR}/pilgrimage-headless-mailbox-wire")
  endif()

  # Their sole argument is an output directory, never the frozen game EXE.
  if(XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/r3-rite-governance-wire")
    add_executable(xar_r3_rite_governance_named_test
      src/ck3_12002.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_religion_context.cpp
      src/religion_rite_governance12002_state_rite.cpp
      src/religion_rite_governance12002_head.cpp
      src/religion_rite_governance12002_organization.cpp
      src/religion_rite_governance12002_context.cpp
      src/religion_rite_governance12002_mailbox.cpp
      src/r3_rite_governance_named_test.cpp)
    target_include_directories(xar_r3_rite_governance_named_test PRIVATE include)
    target_link_libraries(xar_r3_rite_governance_named_test PRIVATE xar_bridge_protocol user32)
    target_compile_definitions(xar_r3_rite_governance_named_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1=1
      XAR_RITE_GOVERNANCE_STANDALONE_ADAPTER=1)
    if(MSVC)
      target_compile_options(xar_r3_rite_governance_named_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_r3_rite_governance_named_test
      COMMAND xar_r3_rite_governance_named_test "${CMAKE_BINARY_DIR}/r3-rite-governance-wire")
  endif()

  if(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/r3-clergy-wire")
    add_executable(xar_r3_clergy_named_test
      src/ck3_12002.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/religion_rite_governance12002_clergy.cpp
      src/religion_rite_governance12002_clergy_mailbox.cpp
      src/ck3_12003_county_conversion.cpp
      src/ck3_12002_council_candidates.cpp
      src/council_composition_candidates_public_v1.cpp
      src/council_composition_candidates_public_v1_serializer.cpp
      src/r3_clergy_named_test.cpp)
    target_include_directories(xar_r3_clergy_named_test PRIVATE include)
    target_link_libraries(xar_r3_clergy_named_test PRIVATE xar_bridge_protocol user32)
    target_compile_definitions(xar_r3_clergy_named_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1=1
      XAR_CLERGY_MAILBOX_STANDALONE_ADAPTER=1)
    if(MSVC)
      target_compile_options(xar_r3_clergy_named_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_r3_clergy_named_test
      COMMAND xar_r3_clergy_named_test "${CMAKE_BINARY_DIR}/r3-clergy-wire")

    # One new full command-result fixture. Replays a frozen actual county leaf
    # through the production serializer and exact .3 identity renderer; no game.
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/county-conversion-clergy-full-wire")
    add_executable(xar_ck3_12003_county_conversion_clergy_full_wire_test
      src/ck3_12002.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/ck3_12003_adapter.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/religion_rite_governance12002_clergy.cpp
      src/religion_rite_governance12002_clergy_mailbox.cpp
      src/ck3_12003_county_conversion.cpp
      src/ck3_12002_council_candidates.cpp
      src/council_composition_candidates_public_v1.cpp
      src/council_composition_candidates_public_v1_serializer.cpp
      src/ck3_12003_county_conversion_clergy_full_wire_test.cpp)
    target_include_directories(xar_ck3_12003_county_conversion_clergy_full_wire_test PRIVATE include)
    target_link_libraries(xar_ck3_12003_county_conversion_clergy_full_wire_test PRIVATE xar_bridge_protocol user32)
    target_compile_definitions(xar_ck3_12003_county_conversion_clergy_full_wire_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1=1)
    if(MSVC)
      target_compile_options(xar_ck3_12003_county_conversion_clergy_full_wire_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /Gy /permissive- /EHsc /utf-8)
      target_link_options(xar_ck3_12003_county_conversion_clergy_full_wire_test PRIVATE /OPT:REF)
    endif()
    add_test(NAME xar_ck3_12003_county_conversion_clergy_full_wire_test
      COMMAND xar_ck3_12003_county_conversion_clergy_full_wire_test
        "${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/county_conversion_clergy_full_wire_leaf_12003.json"
        "${CMAKE_BINARY_DIR}/county-conversion-clergy-full-wire")

    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/county-conversion-values")
    add_executable(xar_ck3_12003_county_conversion_values_test
      src/ck3_12002.cpp
      src/ck3_12002_council_candidates.cpp
      src/council_composition_candidates_public_v1.cpp
      src/council_composition_candidates_public_v1_serializer.cpp
      src/religion_rite_governance12002_clergy.cpp
      src/ck3_12003_county_conversion.cpp
      src/ck3_12003_county_conversion_values_test.cpp)
    target_include_directories(xar_ck3_12003_county_conversion_values_test PRIVATE include)
    target_link_libraries(xar_ck3_12003_county_conversion_values_test PRIVATE xar_bridge_protocol user32)
    if(MSVC)
      target_compile_options(xar_ck3_12003_county_conversion_values_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /Gy /permissive- /EHsc /utf-8)
      target_link_options(xar_ck3_12003_county_conversion_values_test PRIVATE /OPT:REF)
    endif()
    add_test(NAME xar_ck3_12003_county_conversion_values_test
      COMMAND xar_ck3_12003_county_conversion_values_test "${CMAKE_BINARY_DIR}/county-conversion-values")

    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/county-conversion-dispatch")
    add_executable(xar_ck3_12003_county_conversion_dispatch_test
      src/ck3_12002.cpp
      src/ck3_12002_council_candidates.cpp
      src/council_composition_candidates_public_v1.cpp
      src/council_composition_candidates_public_v1_serializer.cpp
      src/religion_rite_governance12002_clergy.cpp
      src/ck3_12003_county_conversion.cpp
      src/ck3_12003_county_conversion_dispatch_test.cpp)
    target_include_directories(xar_ck3_12003_county_conversion_dispatch_test PRIVATE include)
    target_link_libraries(xar_ck3_12003_county_conversion_dispatch_test PRIVATE xar_bridge_protocol user32)
    if(MSVC)
      target_compile_options(xar_ck3_12003_county_conversion_dispatch_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /Gy /permissive- /EHsc /utf-8)
      target_link_options(xar_ck3_12003_county_conversion_dispatch_test PRIVATE /OPT:REF)
    endif()
    add_test(NAME xar_ck3_12003_county_conversion_dispatch_test
      COMMAND xar_ck3_12003_county_conversion_dispatch_test "${CMAKE_BINARY_DIR}/county-conversion-dispatch")

    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/county-conversion-task-action")
    add_executable(xar_ck3_12003_county_conversion_task_action_v1_test
      src/ck3_12002.cpp
      src/ck3_12002_commands.cpp
      src/ck3_12002_council_candidates.cpp
      src/council_composition_candidates_public_v1.cpp
      src/council_composition_candidates_public_v1_serializer.cpp
      src/religion_rite_governance12002_clergy.cpp
      src/ck3_12003_county_conversion.cpp
      src/ck3_12003_county_conversion_task_action_v1.cpp
      src/ck3_12003_county_conversion_task_action_serializer.cpp
      src/ck3_12003_county_conversion_task_action_v1_test.cpp)
    target_include_directories(xar_ck3_12003_county_conversion_task_action_v1_test PRIVATE include)
    target_link_libraries(xar_ck3_12003_county_conversion_task_action_v1_test PRIVATE xar_bridge_protocol user32)
    if(MSVC)
      target_compile_options(xar_ck3_12003_county_conversion_task_action_v1_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /Gy /permissive- /EHsc /utf-8)
      target_link_options(xar_ck3_12003_county_conversion_task_action_v1_test PRIVATE /OPT:REF)
    endif()
    add_test(NAME xar_ck3_12003_county_conversion_task_action_v1_test
      COMMAND xar_ck3_12003_county_conversion_task_action_v1_test "${CMAKE_BINARY_DIR}/county-conversion-task-action")
  endif()

  if(XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/r3-rite-members-wire")
    add_executable(xar_r3_rite_members_named_test
      src/ck3_12002.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/religion_rite_governance12002_organization_members.cpp
      src/religion_rite_governance12002_members_mailbox.cpp
      src/r3_rite_members_named_test.cpp)
    target_include_directories(xar_r3_rite_members_named_test PRIVATE include)
    target_link_libraries(xar_r3_rite_members_named_test PRIVATE xar_bridge_protocol user32)
    target_compile_definitions(xar_r3_rite_members_named_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1=1
      XAR_RITE_MEMBERS_MAILBOX_STANDALONE_ADAPTER=1)
    if(MSVC)
      target_compile_options(xar_r3_rite_members_named_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_r3_rite_members_named_test
      COMMAND xar_r3_rite_members_named_test "${CMAKE_BINARY_DIR}/r3-rite-members-wire")
  endif()

  if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/r3-religion-doctrines-wire")
    add_executable(xar_r3_religion_doctrines_named_test
      src/ck3_12002.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_religion_context.cpp
      src/religion_doctrine12002_intrinsic.cpp
      src/religion_doctrine12002_rite.cpp
      src/religion_doctrine12002_tenet.cpp
      src/religion_doctrine12002_query.cpp
      src/religion_doctrine12002_mailbox.cpp
      src/r3_religion_doctrines_named_test.cpp)
    target_include_directories(xar_r3_religion_doctrines_named_test PRIVATE include)
    target_link_libraries(xar_r3_religion_doctrines_named_test PRIVATE xar_bridge_protocol user32)
    target_compile_definitions(xar_r3_religion_doctrines_named_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1=1)
    if(MSVC)
      target_compile_options(xar_r3_religion_doctrines_named_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_r3_religion_doctrines_named_test
      COMMAND xar_r3_religion_doctrines_named_test "${CMAKE_BINARY_DIR}/r3-religion-doctrines-wire")
  endif()

  if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/r3-religion-hostility-wire")
    add_executable(xar_r3_religion_hostility_named_test
      src/ck3_12002.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_religion_context.cpp
      src/religion_doctrine12002_hostility.cpp
      src/religion_doctrine12002_hostility_mailbox.cpp
      src/r3_religion_hostility_named_test.cpp)
    target_include_directories(xar_r3_religion_hostility_named_test PRIVATE include)
    target_link_libraries(xar_r3_religion_hostility_named_test PRIVATE xar_bridge_protocol user32)
    target_compile_definitions(xar_r3_religion_hostility_named_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1=1
      XAR_HOSTILITY_MAILBOX_STANDALONE_ADAPTER=1)
    if(MSVC)
      target_compile_options(xar_r3_religion_hostility_named_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_r3_religion_hostility_named_test
      COMMAND xar_r3_religion_hostility_named_test "${CMAKE_BINARY_DIR}/r3-religion-hostility-wire")
  endif()

  if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/r3-religion-doctrine-knowledge-wire")
    add_executable(xar_r3_religion_doctrine_knowledge_named_test
      src/ck3_12002.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_religion_context.cpp
      src/religion_doctrine12002_intrinsic.cpp
      src/religion_doctrine12002_choices.cpp
      src/religion_doctrine12002_choices_mailbox.cpp
      src/r3_religion_doctrine_knowledge_named_test.cpp)
    target_include_directories(xar_r3_religion_doctrine_knowledge_named_test PRIVATE include)
    target_link_libraries(xar_r3_religion_doctrine_knowledge_named_test PRIVATE xar_bridge_protocol user32)
    target_compile_definitions(xar_r3_religion_doctrine_knowledge_named_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1=1
      XAR_DOCTRINE_KNOWLEDGE_MAILBOX_STANDALONE_ADAPTER=1)
    if(MSVC)
      target_compile_options(xar_r3_religion_doctrine_knowledge_named_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_r3_religion_doctrine_knowledge_named_test
      COMMAND xar_r3_religion_doctrine_knowledge_named_test "${CMAKE_BINARY_DIR}/r3-religion-doctrine-knowledge-wire")
  endif()

  if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/r3-religion-tenets-wire")
    add_executable(xar_r3_religion_tenets_named_test
      src/ck3_12002.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_religion_context.cpp
      src/religion_doctrine12002_tenet_rows.cpp
      src/religion_doctrine12002_tenet_rows_mailbox.cpp
      src/r3_religion_tenets_named_test.cpp)
    target_include_directories(xar_r3_religion_tenets_named_test PRIVATE include)
    target_link_libraries(xar_r3_religion_tenets_named_test PRIVATE xar_bridge_protocol user32)
    target_compile_definitions(xar_r3_religion_tenets_named_test PRIVATE
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1=1
      XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1)
    if(MSVC)
      target_compile_options(xar_r3_religion_tenets_named_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_r3_religion_tenets_named_test
      COMMAND xar_r3_religion_tenets_named_test "${CMAKE_BINARY_DIR}/r3-religion-tenets-wire")
  endif()

  if(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/r3-religion-conversion-terms-wire")
    add_executable(xar_r3_religion_conversion_terms_named_test
      src/ck3_12002.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_religion_conversion_rite.cpp
      src/ck3_12002_religion_conversion_cost.cpp
      src/ck3_12002_religion_conversion_terms.cpp
      src/ck3_12002_religion_conversion_mailbox.cpp
      src/ck3_12002_religion_conversion_terms_test.cpp)
    target_include_directories(xar_r3_religion_conversion_terms_named_test PRIVATE include)
    target_link_libraries(xar_r3_religion_conversion_terms_named_test PRIVATE xar_bridge_protocol user32)
    target_compile_definitions(xar_r3_religion_conversion_terms_named_test PRIVATE
      XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1=1
      XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1)
    if(MSVC)
      target_compile_options(xar_r3_religion_conversion_terms_named_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_r3_religion_conversion_terms_named_test
      COMMAND xar_r3_religion_conversion_terms_named_test "${CMAKE_BINARY_DIR}/r3-religion-conversion-terms-wire")
  endif()

  if(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/r3-religion-conversion-choices-wire")
    add_executable(xar_r3_religion_conversion_choices_named_test
      src/ck3_12002.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_religion_conversion_faith.cpp
      src/ck3_12002_religion_conversion_rite.cpp
      src/ck3_12002_religion_conversion_choices_mailbox.cpp
      src/ck3_12002_religion_conversion_choices_mailbox_test.cpp)
    target_include_directories(xar_r3_religion_conversion_choices_named_test PRIVATE include)
    target_link_libraries(xar_r3_religion_conversion_choices_named_test PRIVATE xar_bridge_protocol user32)
    target_compile_definitions(xar_r3_religion_conversion_choices_named_test PRIVATE
      XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1=1
      XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1)
    if(MSVC)
      target_compile_options(xar_r3_religion_conversion_choices_named_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_r3_religion_conversion_choices_named_test
      COMMAND xar_r3_religion_conversion_choices_named_test "${CMAKE_BINARY_DIR}/r3-religion-conversion-choices-wire")
  endif()

  if(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/r3-religion-conversion-inputs-wire")
    add_executable(xar_r3_religion_conversion_inputs_named_test
      src/ck3_12002.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_religion_context.cpp
      src/religion_rite_governance12002_state_rite.cpp
      src/ck3_12002_religion_conversion_gates.cpp
      src/ck3_12002_religion_conversion_ai_inputs.cpp
      src/ck3_12002_religion_conversion_inputs_mailbox.cpp
      src/ck3_12002_religion_conversion_inputs_mailbox_test.cpp)
    target_include_directories(xar_r3_religion_conversion_inputs_named_test PRIVATE include)
    target_link_libraries(xar_r3_religion_conversion_inputs_named_test PRIVATE xar_bridge_protocol user32)
    target_compile_definitions(xar_r3_religion_conversion_inputs_named_test PRIVATE
      XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1=1
      XAR_RELIGION_CONVERSION_INPUTS_MAILBOX_STANDALONE_ADAPTER=1)
    if(MSVC)
      target_compile_options(xar_r3_religion_conversion_inputs_named_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_r3_religion_conversion_inputs_named_test
      COMMAND xar_r3_religion_conversion_inputs_named_test "${CMAKE_BINARY_DIR}/r3-religion-conversion-inputs-wire")
  endif()

  if(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/r3-sway-completion-wire")
    add_executable(xar_r3_sway_completion_named_test
      src/ck3_12002.cpp
      src/ck3_12002_query_mailbox.cpp
      src/ck3_12003_abi_profile.cpp
      src/main_thread_query_mailbox_v1.cpp
      src/ck3_12002_sway_completion.cpp
      src/ck3_12002_sway_completion_mailbox.cpp
      src/ck3_12002_sway_completion_serializer.cpp
      src/r3_sway_completion_named_test.cpp)
    target_include_directories(xar_r3_sway_completion_named_test PRIVATE include)
    target_link_libraries(xar_r3_sway_completion_named_test PRIVATE xar_bridge_protocol user32)
    target_compile_definitions(xar_r3_sway_completion_named_test PRIVATE
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1=1)
    if(MSVC)
      target_compile_options(xar_r3_sway_completion_named_test PRIVATE
        /O2 /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_r3_sway_completion_named_test
      COMMAND xar_r3_sway_completion_named_test "${CMAKE_BINARY_DIR}/r3-sway-completion-wire")
  endif()

  add_executable(xar_ck3_ingame_ui_navigation_v1_test
    tests/ingame_ui_navigation_v1_test.cpp src/protocol.cpp)
  target_include_directories(xar_ck3_ingame_ui_navigation_v1_test PRIVATE include)
  target_compile_definitions(xar_ck3_ingame_ui_navigation_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  add_test(NAME xar_ck3_ingame_ui_navigation_v1_test
    COMMAND xar_ck3_ingame_ui_navigation_v1_test)
  if(XAR_CK3_ENABLE_G2_ACTIVITY_COST_SLOT12_PASSIVE_PRIVATE_V1)
    add_executable(xar_ck3_activity_cost_slot12_passive_v1_test
      src/activity_cost_slot12_passive_v1.cpp
      src/activity_cost_slot12_passive_v1_test.cpp)
    target_include_directories(
      xar_ck3_activity_cost_slot12_passive_v1_test PRIVATE include)
    target_compile_definitions(
      xar_ck3_activity_cost_slot12_passive_v1_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(
        xar_ck3_activity_cost_slot12_passive_v1_test PRIVATE
        /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_cost_slot12_passive_v1
      COMMAND xar_ck3_activity_cost_slot12_passive_v1_test)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1)
    add_executable(xar_ck3_activity_stage5_gold_cost_v1_test
      src/activity_planner_diag_v1.cpp
      src/activity_cost_slot12_passive_v1.cpp
      src/activity_stage5_gold_cost_v1.cpp
      src/activity_stage5_gold_cost_v1_test.cpp)
    target_include_directories(
      xar_ck3_activity_stage5_gold_cost_v1_test PRIVATE include)
    target_compile_definitions(
      xar_ck3_activity_stage5_gold_cost_v1_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(
        xar_ck3_activity_stage5_gold_cost_v1_test PRIVATE
        /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_stage5_gold_cost_v1
      COMMAND xar_ck3_activity_stage5_gold_cost_v1_test)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1)
    add_executable(xar_ck3_activity_stage5_canstart_failure_display_v1_test
      src/activity_stage5_canstart_failure_display_v1.cpp
      src/activity_stage5_canstart_failure_display_v1_test.cpp)
    target_include_directories(
      xar_ck3_activity_stage5_canstart_failure_display_v1_test PRIVATE include)
    target_compile_definitions(
      xar_ck3_activity_stage5_canstart_failure_display_v1_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(
        xar_ck3_activity_stage5_canstart_failure_display_v1_test PRIVATE
        /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_stage5_canstart_failure_display_v1
      COMMAND xar_ck3_activity_stage5_canstart_failure_display_v1_test)
    add_executable(xar_ck3_activity_stage5_feast_full_cost_v1_test
      src/activity_planner_diag_v1.cpp
      src/activity_cost_slot12_passive_v1.cpp
      src/activity_stage5_gold_cost_v1.cpp
      src/activity_stage5_feast_full_cost_v1.cpp
      src/activity_stage5_feast_full_cost_v1_test.cpp)
    target_include_directories(
      xar_ck3_activity_stage5_feast_full_cost_v1_test PRIVATE include)
    target_compile_definitions(
      xar_ck3_activity_stage5_feast_full_cost_v1_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(
        xar_ck3_activity_stage5_feast_full_cost_v1_test PRIVATE
        /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_stage5_feast_full_cost_v1
      COMMAND xar_ck3_activity_stage5_feast_full_cost_v1_test)
    find_package(Python3 COMPONENTS Interpreter REQUIRED)
    add_test(NAME xar_ck3_native_bridge_activity_stage5_feast_full_cost_route_v1
      COMMAND ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/research/verify_activity_stage5_feast_full_cost_route.py
        ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1)
    add_executable(xar_ck3_activity_stage5_feast_guest_join_v1_test
      src/activity_planner_diag_v1.cpp
      src/activity_cost_slot12_passive_v1.cpp
      src/activity_stage5_gold_cost_v1.cpp
      src/activity_stage5_feast_guest_join_v1.cpp
      src/activity_stage5_feast_guest_join_v1_test.cpp)
    target_include_directories(xar_ck3_activity_stage5_feast_guest_join_v1_test
      PRIVATE include)
    target_compile_definitions(xar_ck3_activity_stage5_feast_guest_join_v1_test
      PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(xar_ck3_activity_stage5_feast_guest_join_v1_test
        PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_stage5_feast_guest_join_v1
      COMMAND xar_ck3_activity_stage5_feast_guest_join_v1_test)
    add_executable(xar_ck3_activity_feast_guest_candidate_v1_test
      src/activity_planner_diag_v1.cpp
      src/activity_cost_slot12_passive_v1.cpp
      src/activity_stage5_gold_cost_v1.cpp
      src/activity_stage5_feast_guest_join_v1.cpp
      src/activity_feast_guest_candidate_v1.cpp
      src/activity_feast_guest_candidate_v1_test.cpp)
    target_include_directories(xar_ck3_activity_feast_guest_candidate_v1_test
      PRIVATE include)
    target_compile_definitions(xar_ck3_activity_feast_guest_candidate_v1_test
      PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(xar_ck3_activity_feast_guest_candidate_v1_test
        PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_feast_guest_candidate_v1
      COMMAND xar_ck3_activity_feast_guest_candidate_v1_test)
    add_executable(xar_ck3_activity_feast_stage5_start_v1_test
      src/activity_feast_resource_balance_v1.cpp
      src/activity_feast_stage5_start_v1.cpp
      src/activity_feast_stage5_start_v1_test.cpp)
    target_include_directories(xar_ck3_activity_feast_stage5_start_v1_test
      PRIVATE include)
    target_compile_definitions(xar_ck3_activity_feast_stage5_start_v1_test
      PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(xar_ck3_activity_feast_stage5_start_v1_test
        PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_feast_stage5_start_v1
      COMMAND xar_ck3_activity_feast_stage5_start_v1_test)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_TOGGLE_PRIVATE_V1)
    add_executable(xar_ck3_activity_feast_guest_rule_toggle_v1_test
      src/activity_planner_diag_v1.cpp
      src/activity_cost_slot12_passive_v1.cpp
      src/activity_feast_guest_rule_toggle_v1.cpp
      src/activity_feast_guest_rule_toggle_v1_test.cpp)
    target_include_directories(xar_ck3_activity_feast_guest_rule_toggle_v1_test
      PRIVATE include)
    target_compile_definitions(xar_ck3_activity_feast_guest_rule_toggle_v1_test
      PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(xar_ck3_activity_feast_guest_rule_toggle_v1_test
        PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_feast_guest_rule_toggle_v1
      COMMAND xar_ck3_activity_feast_guest_rule_toggle_v1_test)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_OPINION_PRIVATE_V1)
    add_executable(xar_ck3_activity_feast_guest_opinion_v1_test
      src/activity_feast_guest_opinion_v1.cpp
      src/activity_feast_guest_opinion_v1_test.cpp)
    target_include_directories(xar_ck3_activity_feast_guest_opinion_v1_test
      PRIVATE include)
    target_compile_definitions(xar_ck3_activity_feast_guest_opinion_v1_test
      PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(xar_ck3_activity_feast_guest_opinion_v1_test
        PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_feast_guest_opinion_v1
      COMMAND xar_ck3_activity_feast_guest_opinion_v1_test)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
    add_executable(xar_ck3_activity_feast_guest_rule_provenance_v1_test
      src/activity_feast_guest_rule_provenance_v1.cpp
      src/activity_feast_guest_rule_provenance_v1_test.cpp)
    target_include_directories(xar_ck3_activity_feast_guest_rule_provenance_v1_test
      PRIVATE include)
    target_compile_definitions(xar_ck3_activity_feast_guest_rule_provenance_v1_test
      PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(xar_ck3_activity_feast_guest_rule_provenance_v1_test
        PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_feast_guest_rule_provenance_v1
      COMMAND xar_ck3_activity_feast_guest_rule_provenance_v1_test)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1)
    add_executable(xar_ck3_activity_stage1_option_read_v1_test
      src/activity_planner_diag_v1.cpp
      src/activity_stage1_option_read_v1.cpp
      src/activity_stage1_option_read_v1_test.cpp)
    target_include_directories(
      xar_ck3_activity_stage1_option_read_v1_test PRIVATE include)
    target_compile_definitions(
      xar_ck3_activity_stage1_option_read_v1_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(
        xar_ck3_activity_stage1_option_read_v1_test PRIVATE
        /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_stage1_option_read_v1
      COMMAND xar_ck3_activity_stage1_option_read_v1_test)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_GATE_READ_PRIVATE_V1)
    add_executable(xar_ck3_activity_stage2_gate_read_v1_test
      src/activity_planner_diag_v1.cpp
      src/activity_stage1_option_read_v1.cpp
      src/activity_stage2_gate_read_v1.cpp
      src/activity_stage2_gate_read_v1_test.cpp)
    target_include_directories(
      xar_ck3_activity_stage2_gate_read_v1_test PRIVATE include)
    target_compile_definitions(
      xar_ck3_activity_stage2_gate_read_v1_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(
        xar_ck3_activity_stage2_gate_read_v1_test PRIVATE
        /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_stage2_gate_read_v1
      COMMAND xar_ck3_activity_stage2_gate_read_v1_test)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_LOCATION_READ_PRIVATE_V1)
    add_executable(xar_ck3_activity_stage2_location_read_v1_test
      src/activity_planner_diag_v1.cpp
      src/activity_stage1_option_read_v1.cpp
      src/activity_stage2_gate_read_v1.cpp
      src/activity_stage2_location_read_v1.cpp
      src/activity_stage2_location_read_v1_test.cpp)
    target_include_directories(
      xar_ck3_activity_stage2_location_read_v1_test PRIVATE include)
    target_compile_definitions(
      xar_ck3_activity_stage2_location_read_v1_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(
        xar_ck3_activity_stage2_location_read_v1_test PRIVATE
        /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_stage2_location_read_v1
      COMMAND xar_ck3_activity_stage2_location_read_v1_test)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1)
    add_executable(xar_ck3_activity_stage2_destination_select_v1_test
      src/activity_stage2_destination_select_v1.cpp
      src/activity_stage2_destination_select_v1_test.cpp)
    target_include_directories(
      xar_ck3_activity_stage2_destination_select_v1_test PRIVATE include)
    target_compile_definitions(
      xar_ck3_activity_stage2_destination_select_v1_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
      XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1=1)
    if(MSVC)
      target_compile_options(
        xar_ck3_activity_stage2_destination_select_v1_test PRIVATE
        /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_stage2_destination_select_v1
      COMMAND xar_ck3_activity_stage2_destination_select_v1_test)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1)
    add_executable(xar_ck3_activity_stage5_canstart_read_v1_test
      src/activity_planner_diag_v1.cpp
      src/activity_stage5_canstart_read_v1.cpp
      src/activity_stage5_canstart_read_v1_test.cpp)
    target_include_directories(
      xar_ck3_activity_stage5_canstart_read_v1_test PRIVATE include)
    target_compile_definitions(
      xar_ck3_activity_stage5_canstart_read_v1_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(
        xar_ck3_activity_stage5_canstart_read_v1_test PRIVATE
        /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_stage5_canstart_read_v1
      COMMAND xar_ck3_activity_stage5_canstart_read_v1_test)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1)
    add_executable(xar_ck3_activity_feast_planner_open_v1_test
      src/activity_planner_diag_v1.cpp
      src/activity_feast_planner_open_v1.cpp
      src/activity_feast_planner_open_v1_test.cpp)
    target_include_directories(
      xar_ck3_activity_feast_planner_open_v1_test PRIVATE include)
    target_compile_definitions(
      xar_ck3_activity_feast_planner_open_v1_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(
        xar_ck3_activity_feast_planner_open_v1_test PRIVATE
        /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_activity_feast_planner_open_v1
      COMMAND xar_ck3_activity_feast_planner_open_v1_test)
  endif()
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
  add_executable(xar_ck3_ai_terminal_reentry_dispatch_observer_v1_test
    src/ai_terminal_reentry_dispatch_observer_v1.cpp
    src/battle_terminal_journal_v1.cpp
    src/ai_terminal_reentry_dispatch_observer_v1_test.cpp)
  target_include_directories(
    xar_ck3_ai_terminal_reentry_dispatch_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_ai_terminal_reentry_dispatch_observer_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_ai_terminal_reentry_dispatch_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_ai_terminal_reentry_dispatch_observer_v1
    COMMAND xar_ck3_ai_terminal_reentry_dispatch_observer_v1_test)
  add_test(
    NAME xar_ck3_ai_terminal_reentry_dispatch_observer_v1_source_contract
    COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/test_ai_terminal_reentry_dispatch_observer_v1_source_contract.py
      --ck3-executable "${XAR_CK3_EXECUTABLE_PATH}")
  add_executable(xar_ck3_player_prisoner_collection_query_v1_private_test
    src/player_prisoner_collection_query_v1_private.cpp
    src/player_prisoner_collection_query_v1_private_test.cpp)
  target_include_directories(
    xar_ck3_player_prisoner_collection_query_v1_private_test PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_player_prisoner_collection_query_v1_private_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_player_prisoner_collection_query_v1_private
    COMMAND xar_ck3_player_prisoner_collection_query_v1_private_test)

  add_executable(xar_ck3_minor_religious_war_defenders_v1_test
    src/minor_religious_war_defenders_v1.cpp
    src/minor_religious_war_defenders_v1_test.cpp)
  target_include_directories(
    xar_ck3_minor_religious_war_defenders_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_minor_religious_war_defenders_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_minor_religious_war_defenders_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_native_bridge_minor_religious_war_defenders_v1
    COMMAND xar_ck3_minor_religious_war_defenders_v1_test)
  if(XAR_CK3_ENABLE_WAR_ACTOR_ARMY_ROLE_PRIVATE_V1)
    add_executable(xar_ck3_actor_army_role_source_gate_v1_test
      src/actor_army_role_source_gate_v1_test.cpp)
    target_include_directories(xar_ck3_actor_army_role_source_gate_v1_test
      PRIVATE include)
    if(MSVC)
      target_compile_options(xar_ck3_actor_army_role_source_gate_v1_test
        PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_actor_army_role_source_gate_v1
      COMMAND xar_ck3_actor_army_role_source_gate_v1_test)
  endif()
  if(XAR_CK3_ENABLE_G2_M5_WAR_PRIMARY_CURRENT_PRIVATE_V1)
    add_executable(xar_ck3_m5_prewar_scope_v1_test
      src/prewar_scope_v1.cpp src/prewar_scope_v1_test.cpp)
    add_executable(xar_ck3_m5_primary_supply_v1_test
      src/m5_primary_army_supply_v1.cpp
      src/m5_primary_army_supply_v1_test.cpp)
    add_executable(xar_ck3_m5_war_primary_readback_v1_test
      src/m5_war_primary_readback_v1.cpp
      src/m5_war_primary_readback_v1_test.cpp)
    foreach(target
        xar_ck3_m5_prewar_scope_v1_test
        xar_ck3_m5_primary_supply_v1_test
        xar_ck3_m5_war_primary_readback_v1_test)
      target_include_directories(${target} PRIVATE include)
      target_compile_definitions(${target} PRIVATE
        NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
      if(MSVC)
        target_compile_options(${target} PRIVATE
          /W4 /WX /permissive- /EHsc)
      endif()
    endforeach()
    add_test(NAME xar_ck3_m5_prewar_scope_v1
      COMMAND xar_ck3_m5_prewar_scope_v1_test)
    add_test(NAME xar_ck3_m5_primary_supply_v1
      COMMAND xar_ck3_m5_primary_supply_v1_test)
    add_test(NAME xar_ck3_m5_war_primary_readback_v1
      COMMAND xar_ck3_m5_war_primary_readback_v1_test)
  endif()
  if(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
    add_executable(xar_ck3_current_first_heir_relationship_v1_test
      src/current_first_heir_relationship_v1.cpp
      src/current_first_heir_relationship_v1_test.cpp)
    target_include_directories(
      xar_ck3_current_first_heir_relationship_v1_test PRIVATE include)
    target_compile_definitions(
      xar_ck3_current_first_heir_relationship_v1_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
      XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1=1)
    if(MSVC)
      target_compile_options(
        xar_ck3_current_first_heir_relationship_v1_test PRIVATE
        /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_current_first_heir_relationship_v1
      COMMAND xar_ck3_current_first_heir_relationship_v1_test)
    add_executable(xar_ck3_marriage_candidate_alliance_projection_v1_test
      src/marriage_candidate_alliance_projection_v1.cpp
      src/marriage_candidate_alliance_projection_v1_test.cpp)
    target_include_directories(
      xar_ck3_marriage_candidate_alliance_projection_v1_test PRIVATE include)
    target_compile_definitions(
      xar_ck3_marriage_candidate_alliance_projection_v1_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(
        xar_ck3_marriage_candidate_alliance_projection_v1_test PRIVATE
        /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_native_bridge_marriage_candidate_alliance_projection_v1
      COMMAND xar_ck3_marriage_candidate_alliance_projection_v1_test)
  endif()
  find_package(Python3 COMPONENTS Interpreter REQUIRED)

  add_executable(xar_ck3_named_gui_tree_budget_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_scoreboard_state_v1.cpp
    src/zhongguo_scoreboard_state_v1_serializer.cpp
    src/named_gui_tree_budget_v1_test.cpp)
  target_include_directories(xar_ck3_named_gui_tree_budget_v1_test PRIVATE include)
  target_compile_definitions(xar_ck3_named_gui_tree_budget_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_named_gui_tree_budget_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_native_bridge_named_gui_tree_budget_v1
    COMMAND xar_ck3_named_gui_tree_budget_v1_test)

  add_executable(xar_ck3_frontend_game_rules_v1_test
    src/frontend_game_rules_v1.cpp
    src/frontend_game_rules_v1_test.cpp)
  target_include_directories(xar_ck3_frontend_game_rules_v1_test PRIVATE include)
  target_compile_definitions(xar_ck3_frontend_game_rules_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_frontend_game_rules_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_native_bridge_frontend_game_rules_v1
    COMMAND xar_ck3_frontend_game_rules_v1_test)

  add_executable(xar_ck3_frontend_applied_game_rules_v1_test
    src/frontend_game_rules_v1.cpp
    src/frontend_applied_game_rules_v1_test.cpp)
  target_include_directories(xar_ck3_frontend_applied_game_rules_v1_test PRIVATE include)
  target_compile_definitions(xar_ck3_frontend_applied_game_rules_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_frontend_applied_game_rules_v1_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc)
  else()
    target_compile_options(xar_ck3_frontend_applied_game_rules_v1_test PRIVATE -UNDEBUG)
  endif()
  add_test(NAME xar_ck3_native_bridge_frontend_applied_game_rules_v1
    COMMAND xar_ck3_frontend_applied_game_rules_v1_test)

  add_executable(xar_ck3_frontend_game_rules_control_v1_test
    src/frontend_game_rules_v1.cpp
    src/frontend_game_rules_control_v1_test.cpp)
  target_include_directories(xar_ck3_frontend_game_rules_control_v1_test PRIVATE include)
  target_compile_definitions(xar_ck3_frontend_game_rules_control_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_frontend_game_rules_control_v1_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc)
  else()
    target_compile_options(xar_ck3_frontend_game_rules_control_v1_test PRIVATE -UNDEBUG)
  endif()
  add_test(NAME xar_ck3_native_bridge_frontend_game_rules_control_v1
    COMMAND xar_ck3_frontend_game_rules_control_v1_test)

  add_executable(xar_ck3_frontend_bookmark_model_probe_v1_test
    src/frontend_bookmark_model_probe_v1.cpp
    src/frontend_bookmark_model_probe_v1_test.cpp)
  target_include_directories(
    xar_ck3_frontend_bookmark_model_probe_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_frontend_bookmark_model_probe_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1)
    target_compile_definitions(
      xar_ck3_frontend_bookmark_model_probe_v1_test PRIVATE
      XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1=1)
  endif()
  if(MSVC)
    target_compile_options(
      xar_ck3_frontend_bookmark_model_probe_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_frontend_bookmark_model_probe_v1
    COMMAND xar_ck3_frontend_bookmark_model_probe_v1_test)

  add_executable(xar_ck3_activity_planning_snapshot_v1_application_glue_test
    src/activity_planning_snapshot_v1_private_observer.cpp
    src/activity_planning_snapshot_v1_source_adapter.cpp
    src/activity_planning_snapshot_v1_native_binder.cpp
    src/activity_planning_snapshot_v1_application_glue.cpp
    src/activity_planning_snapshot_v1_application_glue_test.cpp
  )
  target_include_directories(
    xar_ck3_activity_planning_snapshot_v1_application_glue_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_activity_planning_snapshot_v1_application_glue_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_activity_planning_snapshot_v1_application_glue_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_activity_planning_snapshot_v1_application_glue
    COMMAND xar_ck3_activity_planning_snapshot_v1_application_glue_test)

  foreach(marriage_component IN ITEMS
      marriage_ranked_container_adapter_v1
      marriage_native_outcome_classifier_v1
      marriage_alliance_projection_adapter_v1
      marriage_alliance_readback_adapter_v1
      marriage_proposal_resolution_journal_v1)
    set(marriage_test_target "xar_ck3_${marriage_component}_test")
    add_executable(${marriage_test_target}
      src/${marriage_component}.cpp
      src/${marriage_component}_test.cpp
    )
    target_include_directories(${marriage_test_target} PRIVATE include)
    target_compile_definitions(${marriage_test_target} PRIVATE
      NOMINMAX
      WIN32_LEAN_AND_MEAN
      UNICODE
      _UNICODE
    )
    if(MSVC)
      target_compile_options(${marriage_test_target} PRIVATE
        /W4 /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(
      NAME xar_ck3_native_bridge_${marriage_component}
      COMMAND ${marriage_test_target}
    )
  endforeach()

  add_executable(xar_ck3_marriage_character_fertility_v1_test
    src/marriage_character_fertility_v1_test.cpp)
  target_include_directories(xar_ck3_marriage_character_fertility_v1_test
    PRIVATE include)
  if(MSVC)
    target_compile_options(xar_ck3_marriage_character_fertility_v1_test
      PRIVATE /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_native_bridge_marriage_character_fertility_v1
    COMMAND xar_ck3_marriage_character_fertility_v1_test)

  add_executable(xar_ck3_marriage_shared_glue_v1_test
    src/marriage_alliance_projection_adapter_v1.cpp
    src/marriage_alliance_readback_adapter_v1.cpp
    src/marriage_matchmaking_observer_v1.cpp
    src/marriage_matchmaking_source_adapter_v1.cpp
    src/marriage_native_outcome_classifier_v1.cpp
    src/marriage_proposal_action_core_v1.cpp
    src/marriage_proposal_native_binder_v1.cpp
    src/marriage_proposal_resolution_journal_v1.cpp
    src/marriage_ranked_container_adapter_v1.cpp
    src/marriage_shared_glue_v1.cpp
    src/marriage_shared_glue_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_marriage_shared_glue_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_marriage_shared_glue_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_marriage_shared_glue_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_marriage_shared_glue_v1
    COMMAND xar_ck3_marriage_shared_glue_v1_test
  )
  add_executable(xar_ck3_observed_heir_marriage_private_v1_test
    src/observed_heir_marriage_private_v1.cpp
    src/observed_heir_marriage_private_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_observed_heir_marriage_private_v1_test PRIVATE include)
  target_compile_options(
    xar_ck3_observed_heir_marriage_private_v1_test PRIVATE /W4 /WX)
  if(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
    target_compile_definitions(xar_ck3_observed_heir_marriage_private_v1_test PRIVATE
      XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_observed_heir_marriage_private_v1
    COMMAND xar_ck3_observed_heir_marriage_private_v1_test
  )
  add_executable(xar_ck3_marriage_proposal_native_binder_v1_test
    src/marriage_matchmaking_observer_v1.cpp
    src/marriage_matchmaking_source_adapter_v1.cpp
    src/marriage_proposal_action_core_v1.cpp
    src/marriage_proposal_native_binder_v1.cpp
    src/marriage_proposal_native_binder_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_marriage_proposal_native_binder_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_marriage_proposal_native_binder_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_marriage_proposal_native_binder_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_marriage_proposal_native_binder_v1
    COMMAND xar_ck3_marriage_proposal_native_binder_v1_test
  )
  add_executable(xar_ck3_marriage_proposal_action_core_v1_test
    src/marriage_matchmaking_observer_v1.cpp
    src/marriage_proposal_action_core_v1.cpp
    src/marriage_proposal_action_core_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_marriage_proposal_action_core_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_marriage_proposal_action_core_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_marriage_proposal_action_core_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_marriage_proposal_action_core_v1
    COMMAND xar_ck3_marriage_proposal_action_core_v1_test
  )

  add_executable(xar_ck3_marriage_application_main_receipt_v1_test
    src/marriage_alliance_projection_adapter_v1.cpp
    src/marriage_alliance_readback_adapter_v1.cpp
    src/marriage_application_main_receipt_v1.cpp
    src/marriage_matchmaking_observer_v1.cpp
    src/marriage_matchmaking_source_adapter_v1.cpp
    src/marriage_native_outcome_classifier_v1.cpp
    src/marriage_proposal_action_core_v1.cpp
    src/marriage_proposal_native_binder_v1.cpp
    src/marriage_proposal_resolution_journal_v1.cpp
    src/marriage_ranked_container_adapter_v1.cpp
    src/marriage_shared_glue_v1.cpp
    src/marriage_application_main_receipt_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_marriage_application_main_receipt_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_marriage_application_main_receipt_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_marriage_application_main_receipt_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_marriage_application_main_receipt_v1
    COMMAND xar_ck3_marriage_application_main_receipt_v1_test
  )

  add_executable(xar_ck3_marriage_candidate_internal_route_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/marriage_alliance_projection_adapter_v1.cpp
    src/marriage_alliance_readback_adapter_v1.cpp
    src/marriage_application_main_receipt_v1.cpp
    src/marriage_candidate_internal_route_v1.cpp
    src/marriage_matchmaking_observer_v1.cpp
    src/marriage_matchmaking_source_adapter_v1.cpp
    src/marriage_native_outcome_classifier_v1.cpp
    src/marriage_proposal_action_core_v1.cpp
    src/marriage_proposal_native_binder_v1.cpp
    src/marriage_proposal_resolution_journal_v1.cpp
    src/marriage_ranked_container_adapter_v1.cpp
    src/marriage_shared_glue_v1.cpp
    src/marriage_candidate_internal_route_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_marriage_candidate_internal_route_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_marriage_candidate_internal_route_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_marriage_candidate_internal_route_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_marriage_candidate_internal_route_v1
    COMMAND xar_ck3_marriage_candidate_internal_route_v1_test
  )

  if(XAR_CK3_ENABLE_G2_WAR_BOUND_PRIVATE_CAPTURE_V1)
    add_test(
      NAME xar_ck3_native_bridge_raiktor_war_bound_private_capture_v1
      COMMAND xar_ck3_raiktor_war_bound_private_capture_v1 --self-test
    )
  endif()

  add_executable(xar_bridge_protocol_test
    src/protocol_test.cpp
  )
  target_include_directories(xar_bridge_protocol_test PRIVATE include)
  target_link_libraries(xar_bridge_protocol_test PRIVATE xar_bridge_protocol)
  if(MSVC)
    target_compile_options(xar_bridge_protocol_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_protocol
    COMMAND xar_bridge_protocol_test
  )

  add_executable(xar_ck3_event_window_context_v1_serializer_test
    src/event_window_context_v1_serializer.cpp
    src/event_window_context_v1_serializer_test.cpp
  )
  target_include_directories(
    xar_ck3_event_window_context_v1_serializer_test PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_event_window_context_v1_serializer_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_event_window_context_v1_serializer
    COMMAND xar_ck3_event_window_context_v1_serializer_test
  )

  add_executable(xar_ck3_event_window_context_v1_test
    src/battle_terminal_journal_v1.cpp
    src/ck3_11906.cpp
    src/g2_truce_preview_entry_observer_v1.cpp
    src/raiktor_war_bound_regiment_v1.cpp
    src/raiktor_surrender_truce_v1.cpp
    src/raiktor_actual_truce_expiry_v1.cpp
    src/event_window_context_v1.cpp
    src/event_window_context_v1_mailbox.cpp
    src/event_window_context_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_event_window_context_v1_test PRIVATE include)
  target_link_libraries(
    xar_ck3_event_window_context_v1_test PRIVATE bcrypt)
  target_compile_definitions(
    xar_ck3_event_window_context_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_event_window_context_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_event_window_context_v1
    COMMAND xar_ck3_event_window_context_v1_test
  )

  add_executable(xar_ck3_game_access_test
    src/actual_contact_scope_v1_mailbox.cpp
    src/battle_control_snapshot_v1_mailbox.cpp
    src/battle_reinforcement_assignment_v1_mailbox.cpp
    src/battle_terminal_journal_v1.cpp
    src/battle_terminal_transition_v1_mailbox.cpp
    src/battle_transition_v1_mailbox.cpp
    src/ck3_11906.cpp
    src/g2_truce_preview_entry_observer_v1.cpp
    src/raiktor_war_bound_regiment_v1.cpp
    src/raiktor_surrender_truce_v1.cpp
    src/raiktor_actual_truce_expiry_v1.cpp
    src/ck3_11906_test.cpp
    src/route_contact_horizon_v1_mailbox.cpp
  )
  target_include_directories(xar_ck3_game_access_test PRIVATE include)
  target_link_libraries(xar_ck3_game_access_test PRIVATE bcrypt)
  target_compile_definitions(xar_ck3_game_access_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
    XAR_CK3_WAR_EXIT_TERMS_OFFLINE_RE_TEST
  )
  if(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
    target_sources(xar_ck3_game_access_test PRIVATE
      src/current_first_heir_relationship_v1.cpp
      src/marriage_candidate_alliance_projection_v1.cpp
      src/marriage_native_outcome_classifier_v1.cpp)
    target_compile_definitions(xar_ck3_game_access_test PRIVATE
      XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1=1)
  endif()
  if(MSVC)
    target_compile_options(xar_ck3_game_access_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_game_access_fixture
    COMMAND xar_ck3_game_access_test
  )

  # One focused diagnostics fixture, with the production TU included by the
  # test so its private canonical classifier is exercised without old tests.
  get_target_property(H3937_DIAGNOSTIC_FIXTURE_SOURCES
    xar_ck3_game_access_test SOURCES)
  list(REMOVE_ITEM H3937_DIAGNOSTIC_FIXTURE_SOURCES
    src/ck3_11906.cpp src/ck3_11906_test.cpp)
  add_executable(xar_ck3_physical_inventory_diagnostics_v1_test EXCLUDE_FROM_ALL
    ${H3937_DIAGNOSTIC_FIXTURE_SOURCES}
    src/physical_army_inventory_diagnostics_v1_test.cpp)
  target_include_directories(
    xar_ck3_physical_inventory_diagnostics_v1_test PRIVATE include)
  target_link_libraries(
    xar_ck3_physical_inventory_diagnostics_v1_test PRIVATE bcrypt)
  get_target_property(H3937_DIAGNOSTIC_FIXTURE_DEFINITIONS
    xar_ck3_game_access_test COMPILE_DEFINITIONS)
  target_compile_definitions(
    xar_ck3_physical_inventory_diagnostics_v1_test PRIVATE
    ${H3937_DIAGNOSTIC_FIXTURE_DEFINITIONS})
  if(MSVC)
    target_compile_options(
      xar_ck3_physical_inventory_diagnostics_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_physical_inventory_diagnostics_v1
    COMMAND xar_ck3_physical_inventory_diagnostics_v1_test)

  # The H3 producer fixture calls the actual route-contact executor through the
  # installed SDL return-site hook; it does not run the game-access/queue suites.
  get_target_property(H3937_DISPATCH_FIXTURE_SOURCES
    xar_ck3_game_access_test SOURCES)
  list(REMOVE_ITEM H3937_DISPATCH_FIXTURE_SOURCES src/ck3_11906_test.cpp)
  add_executable(xar_ck3_h3937_route_contact_queued_retry_v1_test EXCLUDE_FROM_ALL
    ${H3937_DISPATCH_FIXTURE_SOURCES}
    src/main_thread_query_mailbox_v1.cpp
    src/h3937_route_contact_queued_retry_v1_test.cpp)
  target_include_directories(
    xar_ck3_h3937_route_contact_queued_retry_v1_test PRIVATE include)
  target_link_libraries(
    xar_ck3_h3937_route_contact_queued_retry_v1_test PRIVATE bcrypt)
  target_compile_definitions(
    xar_ck3_h3937_route_contact_queued_retry_v1_test PRIVATE
    ${H3937_DIAGNOSTIC_FIXTURE_DEFINITIONS})
  if(MSVC)
    target_compile_options(
      xar_ck3_h3937_route_contact_queued_retry_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_h3937_route_contact_queued_retry_v1
    COMMAND xar_ck3_h3937_route_contact_queued_retry_v1_test)
  set_tests_properties(
    xar_ck3_native_bridge_h3937_route_contact_queued_retry_v1
    PROPERTIES TIMEOUT 30 LABELS "h3937-focused")

  add_executable(xar_ck3_adapter_registry_test
    src/actual_contact_scope_v1_mailbox.cpp
    src/battle_control_snapshot_v1_mailbox.cpp
    src/battle_reinforcement_assignment_v1_mailbox.cpp
    src/battle_terminal_journal_v1.cpp
    src/battle_terminal_transition_v1_mailbox.cpp
    src/battle_transition_v1_mailbox.cpp
    src/campaign_root_context_v1.cpp
    src/campaign_root_context_v1_mailbox.cpp
    src/player_faction_alerts_v1.cpp
    src/player_faction_alerts_v1_mailbox.cpp
    src/steward_develop_county_candidates_v1.cpp
    src/ck3_12003_steward_develop_county.cpp
    src/council_composition_steward_candidates_reader_v1.cpp
    src/council_composition_candidates_public_v1.cpp
    src/council_composition_candidates_public_v1_serializer.cpp
    src/steward_develop_county_candidates_v1_mailbox.cpp
    src/combat_simulation_inputs_v3_mailbox.cpp
    src/game_adapter.cpp
    src/loaded_feature_manifest_v1.cpp
    src/loaded_feature_manifest_v1_mailbox.cpp
    src/main_thread_query_mailbox_v1.cpp
    src/pending_character_interaction_context_v1.cpp
    src/pending_character_interaction_context_v1_mailbox.cpp
    src/ck3_11906_adapter.cpp
    src/ck3_11906.cpp
    src/g2_truce_preview_entry_observer_v1.cpp
    src/raiktor_war_bound_regiment_v1.cpp
    src/raiktor_surrender_truce_v1.cpp
    src/raiktor_actual_truce_expiry_v1.cpp
    src/combat_v3.cpp
    src/route_contact_horizon_v1_mailbox.cpp
    src/set_played_character_v1_mailbox.cpp
    src/tactical_daily_sentinel_v1.cpp
    src/war_entry_assessments_v1.cpp
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_case_snapshot_v1_mailbox.cpp
    src/zhongguo_b1_cycle_snapshot_v1.cpp
    src/zhongguo_b1_cycle_snapshot_v1_mailbox.cpp
    src/zhongguo_ai_owned_case_snapshot_v1.cpp
    src/zhongguo_ai_owned_case_snapshot_v1_mailbox.cpp
    src/zhongguo_b2_pip_snapshot_v1.cpp
    src/zhongguo_b2_pip_snapshot_v1_mailbox.cpp
    src/zhongguo_incident_snapshot_v1.cpp
    src/zhongguo_incident_snapshot_v1_mailbox.cpp
    src/zhongguo_manager_governance_snapshot_v1.cpp
    src/zhongguo_manager_governance_snapshot_v1_mailbox.cpp
    src/zhongguo_manager_subordinate_selector_v1.cpp
    src/zhongguo_promotion_compensation_postcondition_v1.cpp
    src/zhongguo_promotion_compensation_postcondition_v1_mailbox.cpp
    src/zhongguo_compensation_af5_snapshot_v1.cpp
    src/zhongguo_compensation_af5_snapshot_v1_mailbox.cpp
    src/zhongguo_promotion_source_progress_v1_mailbox.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1_mailbox.cpp
    src/zhongguo_projects_metrics_postcondition_v1.cpp
    src/zhongguo_projects_metrics_postcondition_v1_mailbox.cpp
    src/zhongguo_scoreboard_action_v1.cpp
    src/zhongguo_scoreboard_action_v1_mailbox.cpp
    src/zhongguo_scoreboard_state_v1.cpp
    src/zhongguo_scoreboard_state_v1_mailbox.cpp
    src/zhongguo_workforce_collective_snapshot_v1.cpp
    src/zhongguo_workforce_collective_snapshot_v1_mailbox.cpp
    src/zhongguo_workforce_owner_snapshot_v1.cpp
    src/zhongguo_workforce_owner_snapshot_v1_mailbox.cpp
    src/zhongguo_workforce_normal_exit_snapshot_v1.cpp
    src/zhongguo_workforce_normal_exit_snapshot_v1_mailbox.cpp
    src/zhongguo_result_case_snapshot_v1.cpp
    src/zhongguo_result_case_snapshot_v1_mailbox.cpp
    src/game_adapter_test.cpp
  )
  target_include_directories(xar_ck3_adapter_registry_test PRIVATE include)
  target_link_libraries(xar_ck3_adapter_registry_test PRIVATE
    xar_ck3_12002_runtime bcrypt)
  if(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
    target_sources(xar_ck3_adapter_registry_test PRIVATE
      src/current_first_heir_relationship_v1.cpp
      src/observed_heir_marriage_private_v1.cpp
      src/marriage_candidate_alliance_projection_v1.cpp
      src/marriage_native_outcome_classifier_v1.cpp)
  endif()
  target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(XAR_CK3_ENABLE_AI_TERMINAL_REENTRY_DISPATCH_OBSERVER_V1)
    target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE
      XAR_CK3_ENABLE_AI_TERMINAL_REENTRY_DISPATCH_OBSERVER_V1=1)
  endif()
  if(XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1)
    target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE
      XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1=1)
  endif()
  if(XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1)
    target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE
      XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1=1)
  endif()
  if(XAR_CK3_ENABLE_ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1)
    target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE
      XAR_CK3_ENABLE_ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1=1)
  endif()
  if(XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1)
    target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE
      XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1=1)
  endif()
  if(XAR_CK3_ENABLE_ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1)
    target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE
      XAR_CK3_ENABLE_ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1=1)
  endif()
  if(XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1)
    target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE
      XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1=1)
  endif()
  if(XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1)
    target_sources(xar_ck3_adapter_registry_test PRIVATE
      src/h2743_preaction_existing_truce_v1.cpp)
    target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE
      XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1=1)
  endif()
  if(XAR_CK3_ENABLE_G2_WAR_BOUND_LOSS_CANDIDATE_V1)
    target_sources(xar_ck3_adapter_registry_test PRIVATE
      src/raiktor_war_bound_loss_candidate_v1.cpp)
    target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE
      XAR_CK3_ENABLE_G2_WAR_BOUND_LOSS_CANDIDATE_V1=1)
  endif()
  if(MSVC)
    target_compile_options(xar_ck3_adapter_registry_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_12003_frontend_private_capabilities
    COMMAND xar_ck3_adapter_registry_test --frontend-private-capabilities-only
  )
  add_test(
    NAME xar_ck3_native_bridge_adapter_registry
    COMMAND xar_ck3_adapter_registry_test
  )

  add_executable(xar_ck3_raiktor_actual_truce_expiry_v1_test
    src/raiktor_actual_truce_expiry_v1.cpp
    src/raiktor_actual_truce_expiry_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_raiktor_actual_truce_expiry_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_raiktor_actual_truce_expiry_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_raiktor_actual_truce_expiry_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_raiktor_actual_truce_expiry_v1
    COMMAND xar_ck3_raiktor_actual_truce_expiry_v1_test
  )

  add_executable(xar_ck3_h2743_preaction_existing_truce_v1_test
    src/h2743_preaction_existing_truce_v1.cpp
    src/h2743_preaction_existing_truce_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_h2743_preaction_existing_truce_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_h2743_preaction_existing_truce_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_h2743_preaction_existing_truce_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_h2743_preaction_existing_truce_v1
    COMMAND xar_ck3_h2743_preaction_existing_truce_v1_test
  )

  add_executable(xar_ck3_tactical_daily_sentinel_v1_test
    src/tactical_daily_sentinel_v1.cpp
    src/tactical_daily_sentinel_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_tactical_daily_sentinel_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_tactical_daily_sentinel_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_tactical_daily_sentinel_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_tactical_daily_sentinel_v1
    COMMAND xar_ck3_tactical_daily_sentinel_v1_test
  )

  add_executable(xar_ck3_battle_control_snapshot_v1_mailbox_test
    src/battle_control_snapshot_v1_mailbox.cpp
    src/battle_control_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_battle_control_snapshot_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_battle_control_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_battle_control_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_battle_control_snapshot_v1_mailbox
    COMMAND xar_ck3_battle_control_snapshot_v1_mailbox_test
  )

  add_executable(xar_ck3_culture_innovation_snapshot_v1_mailbox_test
    src/main_thread_query_mailbox_v1.cpp
    src/culture_innovation_snapshot_v1.cpp
    src/culture_innovation_source_adapter_v1.cpp
    src/culture_innovation_snapshot_v1_mailbox.cpp
    src/culture_innovation_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_culture_innovation_snapshot_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_culture_innovation_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_culture_innovation_snapshot_v1_mailbox_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_culture_innovation_snapshot_v1_mailbox_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_culture_innovation_snapshot_v1_mailbox
    COMMAND xar_ck3_culture_innovation_snapshot_v1_mailbox_test
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/culture_innovation_snapshot_v1_async_candidate_manifest.json
  )

  add_executable(xar_ck3_battle_transition_v1_mailbox_test
    src/battle_transition_v1_mailbox.cpp
    src/battle_transition_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_battle_transition_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_battle_transition_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_battle_transition_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_battle_transition_v1_mailbox
    COMMAND xar_ck3_battle_transition_v1_mailbox_test
  )

  add_executable(xar_ck3_battle_reinforcement_assignment_v1_mailbox_test
    src/battle_reinforcement_assignment_v1_mailbox.cpp
    src/battle_reinforcement_assignment_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_battle_reinforcement_assignment_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_battle_reinforcement_assignment_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_battle_reinforcement_assignment_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_battle_reinforcement_assignment_v1_mailbox
    COMMAND xar_ck3_battle_reinforcement_assignment_v1_mailbox_test
  )

  add_executable(xar_ck3_battle_terminal_transition_v1_mailbox_test
    src/battle_terminal_journal_v1.cpp
    src/battle_terminal_transition_v1_mailbox.cpp
    src/battle_terminal_transition_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_battle_terminal_transition_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_battle_terminal_transition_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_battle_terminal_transition_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_battle_terminal_transition_v1_mailbox
    COMMAND xar_ck3_battle_terminal_transition_v1_mailbox_test
  )

  add_executable(xar_ck3_combat_v3_test_only_serializer_test
    src/combat_v3_test_only.cpp
    src/combat_v3_test_only_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_v3_test_only_serializer_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_combat_v3_test_only_serializer_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_v3_test_only_serializer_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_v3_test_only_serializer
    COMMAND xar_ck3_combat_v3_test_only_serializer_test
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/combat_phase_inputs_v3_test_only_golden.json
  )

  add_executable(xar_ck3_combat_v3_serializer_test
    src/combat_v3_serializer.cpp
    src/combat_v3_serializer_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_v3_serializer_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_combat_v3_serializer_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_v3_serializer_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_v3_serializer
    COMMAND xar_ck3_combat_v3_serializer_test
  )

  add_executable(xar_ck3_combat_v3_source_contract_test
    src/combat_v3_source_contract_test.cpp
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_v3_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_v3_source_contract
    COMMAND xar_ck3_combat_v3_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/src/combat_v3.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/combat_simulation_inputs_v3_mailbox.cpp
  )

  add_executable(xar_ck3_combat_phase_event_trace_v1_source_contract_test
    src/combat_phase_event_trace_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_phase_event_trace_v1_source_contract_test PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_phase_event_trace_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc /utf-8)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_phase_event_trace_v1_source_contract
    COMMAND xar_ck3_combat_phase_event_trace_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/src/combat_phase_event_trace_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/combat_phase_event_trace_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/combat_phase_event_trace_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/combat_phase_event_trace_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/combat-phase-event-trace.md
  )

  add_executable(xar_ck3_combat_counter_output_readout_v1_test
    src/combat_counter_output_readout_v1.cpp
    src/combat_counter_output_readout_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_counter_output_readout_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_combat_counter_output_readout_v1_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_counter_output_readout_v1_test PRIVATE
        /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_counter_output_readout_v1
    COMMAND xar_ck3_combat_counter_output_readout_v1_test)

  add_executable(xar_ck3_combat_phase_event_trace_ring_v1_test
    src/combat_phase_event_trace_ring_v1.cpp
    src/combat_scoped_transition_chain_v1.cpp
    src/combat_counter_output_readout_v1.cpp
    src/combat_phase_event_trace_ring_v1_test.cpp
  )
  add_executable(xar_ck3_scoped_character_variable_monitor_v1_test
    src/combat_scoped_transition_chain_v1.cpp
    src/combat_scoped_transition_chain_v1_wire.cpp
    src/scoped_character_variable_monitor_v1.cpp
    src/scoped_character_variable_monitor_v1_test.cpp)
  target_include_directories(xar_ck3_scoped_character_variable_monitor_v1_test PRIVATE include)
  target_compile_definitions(xar_ck3_scoped_character_variable_monitor_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_scoped_character_variable_monitor_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_native_bridge_scoped_character_variable_monitor_v1
    COMMAND xar_ck3_scoped_character_variable_monitor_v1_test)
  add_executable(xar_ck3_combat_scoped_transition_chain_v1_test
    src/combat_scoped_transition_chain_v1.cpp
    src/combat_scoped_transition_chain_v1_wire.cpp
    src/combat_scoped_transition_chain_v1_test.cpp)
  target_include_directories(xar_ck3_combat_scoped_transition_chain_v1_test PRIVATE include)
  target_compile_definitions(xar_ck3_combat_scoped_transition_chain_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_combat_scoped_transition_chain_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_native_bridge_combat_scoped_transition_chain_v1
    COMMAND xar_ck3_combat_scoped_transition_chain_v1_test)
  target_include_directories(
    xar_ck3_combat_phase_event_trace_ring_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_combat_phase_event_trace_ring_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_phase_event_trace_ring_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_phase_event_trace_ring_v1
    COMMAND xar_ck3_combat_phase_event_trace_ring_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/combat_phase_event_trace_ring_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/src/combat_phase_event_trace_ring_v1.cpp
  )

  add_executable(xar_ck3_combat_phase_event_trace_detour_v1_test
    src/combat_phase_event_trace_detour_v1.cpp
    src/combat_counter_output_detour_v1.cpp
    src/combat_phase_event_trace_ring_v1.cpp
    src/combat_scoped_transition_chain_v1.cpp
    src/combat_counter_output_readout_v1.cpp
    src/combat_phase_event_trace_detour_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_phase_event_trace_detour_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_combat_phase_event_trace_detour_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_phase_event_trace_detour_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_phase_event_trace_detour_v1
    COMMAND xar_ck3_combat_phase_event_trace_detour_v1_test
  )

  add_executable(xar_ck3_combat_phase_event_trace_wire_v1_test
    src/combat_phase_event_trace_wire_v1.cpp
    src/combat_phase_event_trace_wire_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_phase_event_trace_wire_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_combat_phase_event_trace_wire_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_phase_event_trace_wire_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_phase_event_trace_wire_v1
    COMMAND xar_ck3_combat_phase_event_trace_wire_v1_test
  )

  add_executable(xar_ck3_combat_phase_event_trace_managed_v1_test
    src/combat_phase_event_trace_detour_v1.cpp
    src/combat_counter_output_detour_v1.cpp
    src/combat_advantage_components_observer_v1.cpp
    src/combat_phase_event_trace_managed_v1.cpp
    src/combat_phase_event_trace_ring_v1.cpp
    src/combat_scoped_transition_chain_v1.cpp
    src/combat_scoped_transition_chain_v1_wire.cpp
    src/combat_counter_output_readout_v1.cpp
    src/combat_phase_event_trace_wire_v1.cpp
    src/combat_phase_event_trace_managed_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_phase_event_trace_managed_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_combat_phase_event_trace_managed_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_phase_event_trace_managed_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_phase_event_trace_managed_v1
    COMMAND xar_ck3_combat_phase_event_trace_managed_v1_test
  )

  add_executable(xar_ck3_campaign_root_context_v1_test
    src/campaign_root_context_v1.cpp
    src/campaign_root_context_v1_serializer.cpp
    src/campaign_root_context_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_campaign_root_context_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_campaign_root_context_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_campaign_root_context_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_campaign_root_context_v1
    COMMAND xar_ck3_campaign_root_context_v1_test
  )

  add_executable(xar_ck3_campaign_root_context_v1_mailbox_test
    src/campaign_root_context_v1_mailbox.cpp
    src/campaign_root_context_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_campaign_root_context_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_campaign_root_context_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_campaign_root_context_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_campaign_root_context_v1_mailbox
    COMMAND xar_ck3_campaign_root_context_v1_mailbox_test
  )

  add_executable(xar_ck3_campaign_root_context_v1_source_contract_test
    src/campaign_root_context_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_campaign_root_context_v1_source_contract_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_campaign_root_context_v1_source_contract_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_campaign_root_context_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_campaign_root_context_v1_source_contract
    COMMAND xar_ck3_campaign_root_context_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/campaign_root_context_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/campaign_root_context_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/campaign_root_context_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/campaign_root_context_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/main_thread_query_mailbox_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/main_thread_query_mailbox_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/campaign_root_context_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/campaign_root_context_v1_source_contract.json
  )

  add_executable(xar_ck3_government_runtime_adapter_bridge_binder_v1_test
    src/government_runtime_adapter_observer_v1.cpp
    src/government_runtime_adapter_source_adapter_v1.cpp
    src/campaign_root_context_v1.cpp
    src/loaded_feature_manifest_v1.cpp
    src/government_runtime_adapter_bridge_binder_v1.cpp
    src/government_runtime_adapter_bridge_binder_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_government_runtime_adapter_bridge_binder_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_government_runtime_adapter_bridge_binder_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_government_runtime_adapter_bridge_binder_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_government_runtime_adapter_bridge_binder_v1
    COMMAND xar_ck3_government_runtime_adapter_bridge_binder_v1_test
  )

  add_executable(xar_ck3_player_faction_alerts_v1_test
    src/player_faction_alerts_v1.cpp
    src/player_faction_alerts_v1_serializer.cpp
    src/player_faction_alerts_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_player_faction_alerts_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_player_faction_alerts_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_player_faction_alerts_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_native_bridge_player_faction_alerts_v1
    COMMAND xar_ck3_player_faction_alerts_v1_test)

  add_executable(xar_ck3_player_faction_alerts_v1_serializer_test
    src/player_faction_alerts_v1_serializer.cpp
    src/player_faction_alerts_v1_serializer_test.cpp
  )
  target_include_directories(
    xar_ck3_player_faction_alerts_v1_serializer_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_player_faction_alerts_v1_serializer_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_player_faction_alerts_v1_serializer_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_native_bridge_player_faction_alerts_v1_serializer
    COMMAND xar_ck3_player_faction_alerts_v1_serializer_test)

  add_executable(xar_ck3_player_faction_alerts_v1_mailbox_test
    src/player_faction_alerts_v1_mailbox.cpp
    src/player_faction_alerts_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_player_faction_alerts_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_player_faction_alerts_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_player_faction_alerts_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_native_bridge_player_faction_alerts_v1_mailbox
    COMMAND xar_ck3_player_faction_alerts_v1_mailbox_test)

  add_executable(xar_ck3_player_faction_alerts_v1_source_contract_test
    src/player_faction_alerts_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_player_faction_alerts_v1_source_contract_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_player_faction_alerts_v1_source_contract_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_player_faction_alerts_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_native_bridge_player_faction_alerts_v1_source_contract
    COMMAND xar_ck3_player_faction_alerts_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/player_faction_alerts_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/player_faction_alerts_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/player_faction_alerts_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/player_faction_alerts_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/campaign_root_context_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/campaign_root_context_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/player_faction_alerts_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/player_faction_alerts_v1_source_contract.json
  )

  add_executable(xar_ck3_steward_develop_county_candidates_v1_test
    src/ck3_12003_steward_develop_county.cpp
    src/council_composition_steward_candidates_reader_v1.cpp
    src/council_composition_candidates_public_v1.cpp
    src/council_composition_candidates_public_v1_serializer.cpp
    src/ck3_12002.cpp
    src/ck3_12002_council_candidates.cpp
    src/steward_develop_county_candidates_v1.cpp
    src/steward_develop_county_candidates_v1_serializer.cpp
    src/steward_develop_county_candidates_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_steward_develop_county_candidates_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_steward_develop_county_candidates_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_steward_develop_county_candidates_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_steward_develop_county_candidates_v1
    COMMAND xar_ck3_steward_develop_county_candidates_v1_test
  )

  add_executable(xar_ck3_steward_develop_county_action_v1_test
    src/steward_develop_county_action_v1.cpp
    src/steward_develop_county_action_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_steward_develop_county_action_v1_test PRIVATE include)
  target_compile_features(
    xar_ck3_steward_develop_county_action_v1_test PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(
      xar_ck3_steward_develop_county_action_v1_test PRIVATE /W4 /permissive-)
  else()
    target_compile_options(
      xar_ck3_steward_develop_county_action_v1_test PRIVATE
      -Wall -Wextra -Wpedantic)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_steward_develop_county_action_v1
    COMMAND xar_ck3_steward_develop_county_action_v1_test
  )

  add_executable(xar_ck3_major_decision_found_kingdom_shared_glue_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/major_decision_found_kingdom_observer_v1.cpp
    src/major_decision_found_kingdom_source_adapter_v1.cpp
    src/major_decision_found_kingdom_native_binder_v1.cpp
    src/major_decision_found_kingdom_action_core_v1.cpp
    src/major_decision_found_kingdom_native_submit_v1.cpp
    src/major_decision_found_kingdom_shared_glue_v1.cpp
    src/major_decision_found_kingdom_shared_glue_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_major_decision_found_kingdom_shared_glue_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_major_decision_found_kingdom_shared_glue_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  target_link_libraries(
    xar_ck3_major_decision_found_kingdom_shared_glue_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_major_decision_found_kingdom_shared_glue_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_major_decision_found_kingdom_shared_glue_v1
    COMMAND xar_ck3_major_decision_found_kingdom_shared_glue_v1_test
  )

  add_executable(xar_ck3_major_decision_found_kingdom_internal_route_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/major_decision_found_kingdom_observer_v1.cpp
    src/major_decision_found_kingdom_source_adapter_v1.cpp
    src/major_decision_found_kingdom_native_binder_v1.cpp
    src/major_decision_found_kingdom_action_core_v1.cpp
    src/major_decision_found_kingdom_native_submit_v1.cpp
    src/major_decision_found_kingdom_shared_glue_v1.cpp
    src/major_decision_found_kingdom_internal_route_v1.cpp
    src/major_decision_found_kingdom_internal_route_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_major_decision_found_kingdom_internal_route_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_major_decision_found_kingdom_internal_route_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_G2_MAJOR_DECISION_FOUND_KINGDOM_INTERNAL_ROUTE_V1=1)
  target_link_libraries(
    xar_ck3_major_decision_found_kingdom_internal_route_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_major_decision_found_kingdom_internal_route_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_major_decision_found_kingdom_internal_route_v1
    COMMAND xar_ck3_major_decision_found_kingdom_internal_route_v1_test
  )

  add_executable(
    xar_ck3_major_decision_found_kingdom_internal_route_v1_source_contract_test
    src/major_decision_found_kingdom_internal_route_v1_source_contract_test.cpp
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_major_decision_found_kingdom_internal_route_v1_source_contract_test
      PRIVATE /W4 /WX /permissive-)
  endif()
  add_test(
    NAME
      xar_ck3_native_bridge_major_decision_found_kingdom_internal_route_v1_source_contract
    COMMAND
      xar_ck3_major_decision_found_kingdom_internal_route_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/main_thread_query_mailbox_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/main_thread_query_mailbox_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/major_decision_found_kingdom_shared_glue_v1_test.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/major_decision_found_kingdom_internal_route_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/major_decision_found_kingdom_internal_route_v1_test.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt
  )

  add_executable(
    xar_ck3_steward_develop_county_action_v1_source_contract_test
    src/steward_develop_county_action_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_steward_develop_county_action_v1_source_contract_test
    PRIVATE include)
  target_compile_features(
    xar_ck3_steward_develop_county_action_v1_source_contract_test
    PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(
      xar_ck3_steward_develop_county_action_v1_source_contract_test
      PRIVATE /W4 /permissive-)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_steward_develop_county_action_v1_source_contract
    COMMAND xar_ck3_steward_develop_county_action_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/steward_develop_county_action_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/steward_develop_county_action_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/steward_develop_county_action_v1_abi.json
  )

  add_executable(xar_ck3_steward_develop_county_candidates_v1_serializer_test
    src/steward_develop_county_candidates_v1_serializer.cpp
    src/steward_develop_county_candidates_v1_serializer_test.cpp
  )
  target_include_directories(
    xar_ck3_steward_develop_county_candidates_v1_serializer_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_steward_develop_county_candidates_v1_serializer_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_steward_develop_county_candidates_v1_serializer_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_steward_develop_county_candidates_v1_serializer
    COMMAND xar_ck3_steward_develop_county_candidates_v1_serializer_test
  )

  add_executable(xar_ck3_steward_develop_county_candidates_v1_mailbox_test
    src/ck3_12003_steward_develop_county.cpp
    src/council_composition_steward_candidates_reader_v1.cpp
    src/council_composition_candidates_public_v1.cpp
    src/council_composition_candidates_public_v1_serializer.cpp
    src/ck3_12002.cpp
    src/ck3_12002_council_candidates.cpp
    src/ck3_12002_nonwar_mailbox.cpp
    src/ck3_12002_thread_runtime.cpp
    src/main_thread_query_mailbox_v1.cpp
    src/steward_develop_county_candidates_v1_mailbox.cpp
    src/steward_develop_county_candidates_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_steward_develop_county_candidates_v1_mailbox_test PRIVATE include)
  target_link_libraries(
    xar_ck3_steward_develop_county_candidates_v1_mailbox_test PRIVATE user32)
  target_compile_definitions(
    xar_ck3_steward_develop_county_candidates_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_steward_develop_county_candidates_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_steward_develop_county_candidates_v1_mailbox
    COMMAND xar_ck3_steward_develop_county_candidates_v1_mailbox_test
  )

  add_executable(
    xar_ck3_steward_develop_county_candidates_v1_source_contract_test
    src/steward_develop_county_candidates_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_steward_develop_county_candidates_v1_source_contract_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_steward_develop_county_candidates_v1_source_contract_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_steward_develop_county_candidates_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_steward_develop_county_candidates_v1_source_contract
    COMMAND xar_ck3_steward_develop_county_candidates_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/steward_develop_county_candidates_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/steward_develop_county_candidates_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/steward_develop_county_candidates_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/steward_develop_county_candidates_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/steward_develop_county_candidates_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/steward_develop_county_candidates_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/steward_develop_county_enumerator_observer_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/steward_develop_county_enumerator_observer_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/steward_develop_county_enumerator_observer_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/steward_develop_county_enumerator_observer_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt
  )

  add_executable(xar_ck3_steward_develop_county_enumerator_observer_v1_test
    src/steward_develop_county_enumerator_observer_v1.cpp
    src/steward_develop_county_enumerator_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_steward_develop_county_enumerator_observer_v1_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_steward_develop_county_enumerator_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_steward_develop_county_enumerator_observer_v1_test
      PRIVATE /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_steward_develop_county_enumerator_observer_v1
    COMMAND xar_ck3_steward_develop_county_enumerator_observer_v1_test
  )

  add_executable(xar_ck3_domain_construction_candidate_observer_v1_test
    src/domain_construction_candidate_observer_v1.cpp
    src/domain_construction_candidate_observer_v1_serializer.cpp
    src/domain_construction_candidate_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_domain_construction_candidate_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_domain_construction_candidate_observer_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_domain_construction_candidate_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_domain_construction_candidate_observer_v1
    COMMAND xar_ck3_domain_construction_candidate_observer_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/g2-domain-construction-candidate-observer-v1_capture_fixture.json
  )

  add_executable(
    xar_ck3_domain_construction_candidate_observer_v1_suspended_injection_test
    src/domain_construction_candidate_observer_v1.cpp
    src/domain_construction_candidate_observer_v1_suspended_injection_test.cpp
  )
  target_include_directories(
    xar_ck3_domain_construction_candidate_observer_v1_suspended_injection_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_domain_construction_candidate_observer_v1_suspended_injection_test
    PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_domain_construction_candidate_observer_v1_suspended_injection_test
      PRIVATE /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_domain_construction_candidate_observer_v1_suspended_injection
    COMMAND xar_ck3_domain_construction_candidate_observer_v1_suspended_injection_test
  )
  set_tests_properties(
    xar_ck3_native_bridge_domain_construction_candidate_observer_v1_suspended_injection
    PROPERTIES TIMEOUT 30)

  add_test(
    NAME xar_ck3_native_bridge_domain_construction_candidate_observer_v1_source_contract
    COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/test_domain_construction_candidate_observer_v1_source_contract.py
      --root ${CMAKE_CURRENT_SOURCE_DIR}/../..
      --ck3-executable "${XAR_CK3_EXECUTABLE_PATH}"
  )

  add_executable(xar_ck3_domain_construction_runtime_callsite_observer_v1_test
    src/domain_construction_runtime_callsite_observer_v1.cpp
    src/domain_construction_runtime_callsite_observer_v1_serializer.cpp
    src/domain_construction_runtime_callsite_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_domain_construction_runtime_callsite_observer_v1_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_domain_construction_runtime_callsite_observer_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_domain_construction_runtime_callsite_observer_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_domain_construction_runtime_callsite_observer_v1
    COMMAND xar_ck3_domain_construction_runtime_callsite_observer_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/g2-domain-construction-native-runtime-callsite-observer-v1_capture_fixture.json
  )

  add_executable(
    xar_ck3_domain_construction_runtime_callsite_observer_v1_suspended_injection_test
    src/domain_construction_runtime_callsite_observer_v1.cpp
    src/domain_construction_runtime_callsite_observer_v1_suspended_injection_test.cpp
  )
  target_include_directories(
    xar_ck3_domain_construction_runtime_callsite_observer_v1_suspended_injection_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_domain_construction_runtime_callsite_observer_v1_suspended_injection_test
    PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_domain_construction_runtime_callsite_observer_v1_suspended_injection_test
      PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_domain_construction_runtime_callsite_observer_v1_suspended_injection
    COMMAND xar_ck3_domain_construction_runtime_callsite_observer_v1_suspended_injection_test
  )
  set_tests_properties(
    xar_ck3_native_bridge_domain_construction_runtime_callsite_observer_v1_suspended_injection
    PROPERTIES TIMEOUT 30)

  add_test(
    NAME xar_ck3_native_bridge_domain_construction_runtime_callsite_observer_v1_source_contract
    COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/test_domain_construction_runtime_callsite_observer_v1_source_contract.py
      --root ${CMAKE_CURRENT_SOURCE_DIR}/../..
      --ck3-executable "${XAR_CK3_EXECUTABLE_PATH}"
  )

  add_executable(xar_ck3_domain_construction_shared_glue_v1_test
    research/domain_construction_semantic_action_core_v1.cpp
    research/domain_construction_native_submit_adapter_v1.cpp
    src/domain_construction_shared_glue_v1.cpp
    src/domain_construction_shared_glue_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_domain_construction_shared_glue_v1_test PRIVATE research src)
  if(MSVC)
    target_compile_options(
      xar_ck3_domain_construction_shared_glue_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_domain_construction_shared_glue_v1
    COMMAND xar_ck3_domain_construction_shared_glue_v1_test
  )

  add_executable(xar_ck3_domain_construction_application_main_runtime_v1_test
    research/domain_construction_candidate_identity_decoder_v1.cpp
    research/domain_construction_candidate_cost_legality_decoder_v1.cpp
    research/domain_construction_cost_legality_collector_source_adapter_v1.cpp
    research/domain_construction_cost_legality_live_observer_v1.cpp
    research/domain_construction_semantic_action_core_v1.cpp
    research/domain_construction_native_submit_adapter_v1.cpp
    src/domain_construction_shared_glue_v1.cpp
    src/domain_construction_application_main_runtime_v1.cpp
    src/domain_construction_application_main_runtime_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_domain_construction_application_main_runtime_v1_test
    PRIVATE include research src)
  target_compile_definitions(
    xar_ck3_domain_construction_application_main_runtime_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_domain_construction_application_main_runtime_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_domain_construction_application_main_runtime_v1
    COMMAND xar_ck3_domain_construction_application_main_runtime_v1_test
  )
  add_test(
    NAME xar_ck3_native_bridge_domain_construction_application_main_runtime_v1_source_contract
    COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/test_domain_construction_application_main_runtime_v1_source_contract.py
      --root ${CMAKE_CURRENT_SOURCE_DIR}/../..
      --ck3-executable "${XAR_CK3_EXECUTABLE_PATH}"
  )

  add_executable(xar_ck3_council_composition_candidate_observer_v1_test
    src/council_composition_candidate_observer_v1.cpp
    src/council_composition_candidate_observer_v1_serializer.cpp
    src/council_composition_candidate_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_council_composition_candidate_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_council_composition_candidate_observer_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_council_composition_candidate_observer_v1_test
      PRIVATE /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_council_composition_candidate_observer_v1
    COMMAND xar_ck3_council_composition_candidate_observer_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/council_composition_candidate_observer_v1_capture.json
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/council_composition_candidate_observer_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/council_composition_candidate_observer_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/research/council_composition_candidate_observer_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/council_composition_candidate_observer_v1_source_contract.json
  )

  add_executable(xar_ck3_council_assign_councillor_action_v1_test
    src/council_assign_councillor_action_v1.cpp
    src/council_assign_councillor_action_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_council_assign_councillor_action_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_council_assign_councillor_action_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_council_assign_councillor_action_v1_test
      PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_council_assign_councillor_action_v1
    COMMAND xar_ck3_council_assign_councillor_action_v1_test
  )
  add_test(
    NAME xar_ck3_native_bridge_council_assign_councillor_action_v1_source_contract
    COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/verify_council_assignment_action_1_19_0_6.py
      --exe "${XAR_CK3_EXECUTABLE_PATH}"
  )

  add_executable(xar_ck3_council_assign_councillor_native_submit_adapter_v1_test
    src/council_assign_councillor_native_submit_adapter_v1.cpp
    src/council_assign_councillor_native_submit_adapter_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_council_assign_councillor_native_submit_adapter_v1_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_council_assign_councillor_native_submit_adapter_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_council_assign_councillor_native_submit_adapter_v1_test
      PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_council_assign_councillor_native_submit_adapter_v1
    COMMAND xar_ck3_council_assign_councillor_native_submit_adapter_v1_test
  )

  add_executable(xar_ck3_council_replacement_fireability_v1_test
    src/council_replacement_fireability_v1.cpp
    src/council_replacement_fireability_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_council_replacement_fireability_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_council_replacement_fireability_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_council_replacement_fireability_v1_test
      PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_council_replacement_fireability_v1
    COMMAND xar_ck3_council_replacement_fireability_v1_test
  )

  add_executable(xar_ck3_military_preparation_summary_v1_private_probe_test
    src/military_preparation_summary_v1.cpp
    src/military_preparation_summary_v1_private_probe.cpp
    src/military_preparation_summary_v1_serializer.cpp
    src/military_preparation_summary_v1_private_probe_test.cpp
  )
  target_include_directories(
    xar_ck3_military_preparation_summary_v1_private_probe_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_military_preparation_summary_v1_private_probe_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_military_preparation_summary_v1_private_probe_test
      PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_military_preparation_summary_v1_private_probe
    COMMAND xar_ck3_military_preparation_summary_v1_private_probe_test
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/main_thread_query_mailbox_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/main_thread_query_mailbox_v1.cpp
  )

  add_executable(xar_ck3_faction_targeting_row_probe_v1_test
    src/faction_targeting_row_probe_v1.cpp
    src/faction_targeting_row_probe_v1_serializer.cpp
    src/faction_targeting_row_probe_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_faction_targeting_row_probe_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_faction_targeting_row_probe_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_faction_targeting_row_probe_v1_test
      PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_faction_targeting_row_probe_v1
    COMMAND xar_ck3_faction_targeting_row_probe_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/main_thread_query_mailbox_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/main_thread_query_mailbox_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/faction_targeting_row_async_glue_v1_source_contract.json
  )

  add_executable(xar_ck3_faction_gift_mitigation_async_glue_v1_test
    src/faction_gift_mitigation_action_v1.cpp
    src/faction_gift_mitigation_source_action_adapter_v1.cpp
    src/faction_gift_mitigation_native_binder_v1.cpp
    src/faction_gift_receivers_v1.cpp
    src/faction_gift_mitigation_integration_gate_v1.cpp
    src/faction_gift_mitigation_async_glue_v1.cpp
    src/faction_gift_mitigation_async_glue_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_faction_gift_mitigation_async_glue_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_faction_gift_mitigation_async_glue_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_faction_gift_mitigation_async_glue_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_faction_gift_mitigation_async_glue_v1
    COMMAND xar_ck3_faction_gift_mitigation_async_glue_v1_test
  )

  add_executable(xar_ck3_faction_gift_cold_recovery_v1_test
    src/faction_gift_mitigation_action_v1.cpp
    src/faction_gift_cold_recovery_v1.cpp
    src/faction_gift_cold_recovery_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_faction_gift_cold_recovery_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_faction_gift_cold_recovery_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_faction_gift_cold_recovery_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_faction_gift_cold_recovery_v1
    COMMAND xar_ck3_faction_gift_cold_recovery_v1_test
  )

  add_executable(
    xar_ck3_council_composition_steward_candidates_private_probe_v1_test
    src/council_composition_steward_candidates_reader_v1.cpp
    src/council_composition_steward_candidates_private_probe_v1.cpp
    src/council_composition_steward_candidates_private_probe_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_council_composition_steward_candidates_private_probe_v1_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_council_composition_steward_candidates_private_probe_v1_test
    PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_council_composition_steward_candidates_private_probe_v1_test
      PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_council_composition_steward_candidates_private_probe_v1
    COMMAND xar_ck3_council_composition_steward_candidates_private_probe_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/main_thread_query_mailbox_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/main_thread_query_mailbox_v1.cpp
  )

  add_executable(xar_ck3_council_composition_candidates_public_v1_test
    src/council_composition_candidates_public_v1.cpp
    src/council_composition_candidates_public_v1_serializer.cpp
    src/council_composition_candidates_public_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_council_composition_candidates_public_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_council_composition_candidates_public_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_council_composition_candidates_public_v1_test
      PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_council_composition_candidates_public_v1
    COMMAND xar_ck3_council_composition_candidates_public_v1_test
  )

  add_executable(
    xar_ck3_council_composition_steward_candidates_binding_v1_test
    src/council_composition_steward_candidates_reader_v1.cpp
    src/council_composition_steward_candidates_binding_v1.cpp
    src/council_composition_candidates_enrichment_v1.cpp
    src/council_composition_candidates_public_v1.cpp
    src/council_composition_steward_candidates_binding_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_council_composition_steward_candidates_binding_v1_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_council_composition_steward_candidates_binding_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_council_composition_steward_candidates_binding_v1_test
      PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_council_composition_steward_candidates_binding_v1
    COMMAND xar_ck3_council_composition_steward_candidates_binding_v1_test
  )

  add_executable(xar_ck3_council_application_main_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/council_composition_steward_candidates_reader_v1.cpp
    src/council_composition_steward_candidates_binding_v1.cpp
    src/council_composition_candidates_enrichment_v1.cpp
    src/council_composition_candidates_public_v1.cpp
    src/council_composition_candidates_public_v1_serializer.cpp
    src/council_assign_councillor_action_v1.cpp
    src/council_assign_councillor_native_submit_adapter_v1.cpp
    src/council_replacement_fireability_v1.cpp
    src/council_production_final_gates_v1.cpp
    src/council_application_main_v1.cpp
    src/council_application_main_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_council_application_main_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_council_application_main_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  target_link_libraries(
    xar_ck3_council_application_main_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_council_application_main_v1_test
      PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_council_application_main_v1
    COMMAND xar_ck3_council_application_main_v1_test
  )
  add_test(
    NAME xar_ck3_native_bridge_council_application_main_v1_source_contract
    COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/verify_council_application_main_v1_source.py
      --manifest
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/council_application_main_v1_source_contract.json
      --header
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/council_application_main_v1.hpp
      --implementation
      ${CMAKE_CURRENT_SOURCE_DIR}/src/council_application_main_v1.cpp
      --bridge
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      --mailbox-header
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/main_thread_query_mailbox_v1.hpp
      --mailbox-source
      ${CMAKE_CURRENT_SOURCE_DIR}/src/main_thread_query_mailbox_v1.cpp
      --action-header
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/council_assign_councillor_action_v1.hpp
      --action-source
      ${CMAKE_CURRENT_SOURCE_DIR}/src/council_assign_councillor_action_v1.cpp
  )
  add_test(
    NAME xar_ck3_native_bridge_council_application_main_private_transport_source
    COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/test_council_application_main_private_transport_source.py
  )

  add_executable(xar_ck3_council_composition_candidates_enrichment_v1_test
    src/council_composition_candidates_enrichment_v1.cpp
    src/council_composition_candidates_public_v1.cpp
    src/council_composition_candidates_enrichment_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_council_composition_candidates_enrichment_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_council_composition_candidates_enrichment_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_council_composition_candidates_enrichment_v1_test
      PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_council_composition_candidates_enrichment_v1
    COMMAND xar_ck3_council_composition_candidates_enrichment_v1_test
  )

  add_executable(xar_ck3_zhongguo_case_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_case_snapshot_v1_serializer.cpp
    src/zhongguo_case_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_case_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_case_snapshot_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_case_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_case_snapshot_v1
    COMMAND xar_ck3_zhongguo_case_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_b1_cycle_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_b1_cycle_snapshot_v1.cpp
    src/zhongguo_b1_cycle_snapshot_v1_mailbox.cpp
    src/zhongguo_b1_cycle_snapshot_v1_serializer.cpp
    src/zhongguo_b1_cycle_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_b1_cycle_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_b1_cycle_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_b1_cycle_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_b1_cycle_snapshot_v1
    COMMAND xar_ck3_zhongguo_b1_cycle_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_case_snapshot_v1_mailbox_test
    src/zhongguo_case_snapshot_v1_mailbox.cpp
    src/zhongguo_case_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_case_snapshot_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_case_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_case_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_case_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_case_snapshot_v1_mailbox_test
  )

  add_executable(xar_ck3_zhongguo_ai_owned_case_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_ai_owned_case_snapshot_v1.cpp
    src/zhongguo_ai_owned_case_snapshot_v1_serializer.cpp
    src/zhongguo_ai_owned_case_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_ai_owned_case_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_ai_owned_case_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_ai_owned_case_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_ai_owned_case_snapshot_v1
    COMMAND xar_ck3_zhongguo_ai_owned_case_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_ai_owned_case_snapshot_v1_mailbox_test
    src/zhongguo_ai_owned_case_snapshot_v1_mailbox.cpp
    src/zhongguo_ai_owned_case_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_ai_owned_case_snapshot_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_ai_owned_case_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_ai_owned_case_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_ai_owned_case_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_ai_owned_case_snapshot_v1_mailbox_test
  )

  add_executable(
    xar_ck3_zhongguo_ai_owned_case_snapshot_v1_source_contract_test
    src/zhongguo_ai_owned_case_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_ai_owned_case_snapshot_v1_source_contract_test
    PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_ai_owned_case_snapshot_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_ai_owned_case_snapshot_v1_source_contract
    COMMAND xar_ck3_zhongguo_ai_owned_case_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_ai_owned_case_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_ai_owned_case_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_ai_owned_case_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_ai_owned_case_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_ai_owned_case_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_ai_owned_case_snapshot_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/zhongguo-ai-owned-case-snapshot-v1.md
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/tools/gen_361_b1_runtime.py
  )

  add_executable(xar_ck3_zhongguo_case_snapshot_v1_source_contract_test
    src/zhongguo_case_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_case_snapshot_v1_source_contract_test PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_case_snapshot_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_case_snapshot_v1_source_contract
    COMMAND xar_ck3_zhongguo_case_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_case_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_case_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_case_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_case_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_case_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_case_snapshot_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/tools/gen_361_b1_runtime.py
  )

  add_executable(xar_ck3_zhongguo_result_case_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_result_case_snapshot_v1.cpp
    src/zhongguo_result_case_snapshot_v1_serializer.cpp
    src/zhongguo_result_case_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_result_case_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_result_case_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_result_case_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_result_case_snapshot_v1
    COMMAND xar_ck3_zhongguo_result_case_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_b2_pip_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_b2_pip_snapshot_v1.cpp
    src/zhongguo_b2_pip_snapshot_v1_serializer.cpp
    src/zhongguo_b2_pip_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_b2_pip_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_b2_pip_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_b2_pip_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_b2_pip_snapshot_v1
    COMMAND xar_ck3_zhongguo_b2_pip_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_b2_pip_snapshot_v1_mailbox_test
    src/zhongguo_b2_pip_snapshot_v1_mailbox.cpp
    src/zhongguo_b2_pip_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_b2_pip_snapshot_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_b2_pip_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_b2_pip_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_b2_pip_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_b2_pip_snapshot_v1_mailbox_test
  )

  add_executable(xar_ck3_zhongguo_b2_pip_snapshot_v1_source_contract_test
    src/zhongguo_b2_pip_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_b2_pip_snapshot_v1_source_contract_test PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_b2_pip_snapshot_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_b2_pip_snapshot_v1_source_contract
    COMMAND xar_ck3_zhongguo_b2_pip_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_b2_pip_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_b2_pip_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_b2_pip_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_b2_pip_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_b2_pip_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_b2_pip_snapshot_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/tools/gen_361_b2_runtime.py
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/zhongguo-b2-pip-snapshot-v1.md
  )

  add_executable(xar_ck3_zhongguo_incident_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_incident_snapshot_v1.cpp
    src/zhongguo_incident_snapshot_v1_serializer.cpp
    src/zhongguo_incident_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_incident_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_incident_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_incident_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_incident_snapshot_v1
    COMMAND xar_ck3_zhongguo_incident_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_manager_governance_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_manager_governance_snapshot_v1.cpp
    src/zhongguo_manager_governance_snapshot_v1_serializer.cpp
    src/zhongguo_manager_governance_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_manager_governance_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_manager_governance_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_manager_governance_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_manager_governance_snapshot_v1
    COMMAND xar_ck3_zhongguo_manager_governance_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_manager_subordinate_selector_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_ai_owned_case_snapshot_v1.cpp
    src/zhongguo_manager_subordinate_selector_v1.cpp
    src/zhongguo_manager_subordinate_selector_v1_serializer.cpp
    src/zhongguo_manager_subordinate_selector_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_manager_subordinate_selector_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_manager_subordinate_selector_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_manager_subordinate_selector_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_manager_subordinate_selector_v1
    COMMAND xar_ck3_zhongguo_manager_subordinate_selector_v1_test
  )

  add_executable(xar_ck3_zhongguo_incident_snapshot_v1_mailbox_test
    src/zhongguo_incident_snapshot_v1_mailbox.cpp
    src/zhongguo_incident_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_incident_snapshot_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_incident_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_incident_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_incident_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_incident_snapshot_v1_mailbox_test
  )

  add_executable(xar_ck3_zhongguo_incident_snapshot_v1_source_contract_test
    src/zhongguo_incident_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_incident_snapshot_v1_source_contract_test PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_incident_snapshot_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  set(ZG361_INCIDENT_PRODUCER_SHARDS
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_capture_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_policy_debt_consume_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_policy_debt_stage_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_portfolio_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_apply_192_198_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_apply_199_204_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_deadline_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_debt_192_198_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_debt_199_204_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_dispatch_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_lifecycle_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_probe_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_apply_205_210_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_apply_211_216_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_deadline_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_debt_205_210_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_debt_211_216_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_dispatch_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_lifecycle_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_yz_probe_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_apply_adoption_value_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_apply_cost_migration_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_apply_reuse_fork_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_apply_credit_liability_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_deadline_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_debt_217_222_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_debt_223_228_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_dispatch_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_lifecycle_effects.txt
  )
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_incident_snapshot_v1_source_contract
    COMMAND xar_ck3_zhongguo_incident_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_incident_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_incident_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_incident_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_incident_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_incident_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_incident_snapshot_v1_source_contract.json
      ${ZG361_INCIDENT_PRODUCER_SHARDS}
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/zhongguo-incident-snapshot-v1.md
  )

  add_executable(xar_ck3_zhongguo_scoreboard_state_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_scoreboard_state_v1.cpp
    src/zhongguo_scoreboard_state_v1_serializer.cpp
    src/zhongguo_scoreboard_state_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_scoreboard_state_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_scoreboard_state_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_scoreboard_state_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_scoreboard_state_v1
    COMMAND xar_ck3_zhongguo_scoreboard_state_v1_test
  )

  add_executable(xar_ck3_current_timeline_blocker_12003_production_test
    src/ck3_12002.cpp
    src/ck3_12003_succession_modal.cpp
    src/current_timeline_blocker_context_v1.cpp
    src/death_succession_modal_continue_v1.cpp
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_scoreboard_state_v1.cpp
    src/current_timeline_blocker_12003_production_test.cpp
  )
  target_include_directories(
    xar_ck3_current_timeline_blocker_12003_production_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_current_timeline_blocker_12003_production_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_current_timeline_blocker_12003_production_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy)
    target_link_options(
      xar_ck3_current_timeline_blocker_12003_production_test PRIVATE /OPT:REF)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_current_timeline_blocker_12003_production
    COMMAND xar_ck3_current_timeline_blocker_12003_production_test
      ${CMAKE_CURRENT_BINARY_DIR}/succession-modal-12003-production-packets
  )

  add_executable(xar_ck3_current_timeline_blocker_context_v1_test
    src/current_timeline_blocker_context_v1.cpp
    src/current_timeline_blocker_context_v1_native.cpp
    src/current_timeline_blocker_context_v1_test.cpp
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_scoreboard_state_v1.cpp
  )
  target_include_directories(
    xar_ck3_current_timeline_blocker_context_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_current_timeline_blocker_context_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_current_timeline_blocker_context_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_current_timeline_blocker_context_v1
    COMMAND xar_ck3_current_timeline_blocker_context_v1_test
  )

  add_executable(xar_ck3_player_epidemic_treatment_presence_v1_test
    src/player_epidemic_treatment_presence_v1.cpp
    src/player_epidemic_treatment_presence_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_player_epidemic_treatment_presence_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_player_epidemic_treatment_presence_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_player_epidemic_treatment_presence_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_player_epidemic_treatment_presence_v1
    COMMAND xar_ck3_player_epidemic_treatment_presence_v1_test
  )

  add_executable(xar_ck3_player_epidemic_recovery_v1_test
    src/player_epidemic_recovery_v1.cpp
    src/player_epidemic_recovery_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_player_epidemic_recovery_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_player_epidemic_recovery_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_player_epidemic_recovery_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_player_epidemic_recovery_v1
    COMMAND xar_ck3_player_epidemic_recovery_v1_test
  )

  add_executable(xar_ck3_death_succession_modal_continue_v1_test
    src/death_succession_modal_continue_v1.cpp
    src/death_succession_modal_continue_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_death_succession_modal_continue_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_death_succession_modal_continue_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_death_succession_modal_continue_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_death_succession_modal_continue_v1
    COMMAND xar_ck3_death_succession_modal_continue_v1_test
  )

  add_executable(xar_ck3_death_succession_modal_continue_v1_source_contract_test
    src/death_succession_modal_continue_v1_source_contract_test.cpp
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_death_succession_modal_continue_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_death_succession_modal_continue_v1_source_contract
    COMMAND xar_ck3_death_succession_modal_continue_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/src/death_succession_modal_continue_v1.cpp
  )

  add_executable(xar_ck3_zhongguo_scoreboard_state_v1_mailbox_test
    src/zhongguo_scoreboard_state_v1_mailbox.cpp
    src/zhongguo_scoreboard_state_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_scoreboard_state_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_scoreboard_state_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_scoreboard_state_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_scoreboard_state_v1_mailbox
    COMMAND xar_ck3_zhongguo_scoreboard_state_v1_mailbox_test
  )

  add_executable(xar_ck3_zhongguo_scoreboard_action_v1_test
    src/zhongguo_scoreboard_action_v1.cpp
    src/zhongguo_scoreboard_action_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_scoreboard_action_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_scoreboard_action_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_scoreboard_action_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_scoreboard_action_v1
    COMMAND xar_ck3_zhongguo_scoreboard_action_v1_test
  )

  add_executable(xar_ck3_zhongguo_scoreboard_production_v1_test
    src/zhongguo_scoreboard_production_v1.cpp
    src/zhongguo_scoreboard_production_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_scoreboard_production_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_scoreboard_production_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_scoreboard_production_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_scoreboard_production_v1
    COMMAND xar_ck3_zhongguo_scoreboard_production_v1_test
  )

  add_executable(xar_ck3_zhongguo_scoreboard_production_v1_candidate_test
    src/zhongguo_scoreboard_production_v1.cpp
    src/zhongguo_scoreboard_production_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_scoreboard_production_v1_candidate_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_scoreboard_production_v1_candidate_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_ZHONGGUO_SCOREBOARD_PRODUCTION_V1=1)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_scoreboard_production_v1_candidate_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_scoreboard_production_v1_candidate
    COMMAND xar_ck3_zhongguo_scoreboard_production_v1_candidate_test
  )

  add_executable(xar_ck3_zhongguo_scoreboard_action_v1_mailbox_test
    src/zhongguo_scoreboard_action_v1.cpp
    src/zhongguo_scoreboard_action_v1_mailbox.cpp
    src/zhongguo_scoreboard_action_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_scoreboard_action_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_scoreboard_action_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_scoreboard_action_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_scoreboard_action_v1_mailbox
    COMMAND xar_ck3_zhongguo_scoreboard_action_v1_mailbox_test
  )

  add_executable(xar_ck3_zhongguo_workforce_collective_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_workforce_collective_snapshot_v1.cpp
    src/zhongguo_workforce_collective_snapshot_v1_serializer.cpp
    src/zhongguo_workforce_collective_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_workforce_collective_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_workforce_collective_snapshot_v1
    COMMAND xar_ck3_zhongguo_workforce_collective_snapshot_v1_test
  )


  add_executable(xar_ck3_zhongguo_workforce_owner_snapshot_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_workforce_owner_snapshot_v1.cpp
    src/zhongguo_workforce_owner_snapshot_v1_mailbox.cpp
    src/zhongguo_workforce_owner_snapshot_v1_test.cpp
  )
  target_include_directories(xar_ck3_zhongguo_workforce_owner_snapshot_v1_test PRIVATE include)
  target_compile_definitions(xar_ck3_zhongguo_workforce_owner_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_zhongguo_workforce_owner_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_native_bridge_zhongguo_workforce_owner_snapshot_v1
    COMMAND xar_ck3_zhongguo_workforce_owner_snapshot_v1_test)

  add_executable(xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_workforce_normal_exit_snapshot_v1.cpp
    src/zhongguo_workforce_normal_exit_snapshot_v1_serializer.cpp
    src/zhongguo_workforce_normal_exit_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_workforce_normal_exit_snapshot_v1
    COMMAND xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_test
  )


  add_executable(xar_ck3_zhongguo_compensation_af5_snapshot_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_compensation_af5_snapshot_v1.cpp
    src/zhongguo_compensation_af5_snapshot_v1_mailbox.cpp
    src/zhongguo_compensation_af5_snapshot_v1_test.cpp
  )
  target_include_directories(xar_ck3_zhongguo_compensation_af5_snapshot_v1_test PRIVATE include)
  target_compile_definitions(xar_ck3_zhongguo_compensation_af5_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_zhongguo_compensation_af5_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_native_bridge_zhongguo_compensation_af5_snapshot_v1
    COMMAND xar_ck3_zhongguo_compensation_af5_snapshot_v1_test)

  add_executable(xar_ck3_zhongguo_promotion_compensation_postcondition_v1_test
    src/zhongguo_promotion_compensation_postcondition_v1.cpp
    src/zhongguo_promotion_compensation_postcondition_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_promotion_compensation_postcondition_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_promotion_compensation_postcondition_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_promotion_compensation_postcondition_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_promotion_compensation_postcondition_v1
    COMMAND xar_ck3_zhongguo_promotion_compensation_postcondition_v1_test
  )

  add_executable(
    xar_ck3_zg_promo_comp_mailbox_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/zhongguo_promotion_compensation_postcondition_v1.cpp
    src/zhongguo_promotion_compensation_postcondition_v1_mailbox.cpp
    src/zhongguo_promotion_compensation_postcondition_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zg_promo_comp_mailbox_v1_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_zg_promo_comp_mailbox_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zg_promo_comp_mailbox_v1_test
      PRIVATE /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_promotion_compensation_postcondition_v1_mailbox
    COMMAND xar_ck3_zg_promo_comp_mailbox_v1_test
  )

  add_executable(xar_ck3_zhongguo_projects_metrics_postcondition_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_projects_metrics_postcondition_v1.cpp
    src/zhongguo_projects_metrics_postcondition_v1_serializer.cpp
    src/zhongguo_projects_metrics_postcondition_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_projects_metrics_postcondition_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_projects_metrics_postcondition_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_projects_metrics_postcondition_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_projects_metrics_postcondition_v1
    COMMAND xar_ck3_zhongguo_projects_metrics_postcondition_v1_test
  )

  add_executable(xar_ck3_zg_projects_metrics_mailbox_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_projects_metrics_postcondition_v1.cpp
    src/zhongguo_projects_metrics_postcondition_v1_serializer.cpp
    src/zhongguo_projects_metrics_postcondition_v1_mailbox.cpp
    src/zhongguo_projects_metrics_postcondition_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zg_projects_metrics_mailbox_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zg_projects_metrics_mailbox_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zg_projects_metrics_mailbox_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_projects_metrics_postcondition_v1_mailbox
    COMMAND xar_ck3_zg_projects_metrics_mailbox_v1_test
  )

  add_executable(xar_ck3_zg_career_hc_workforce_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1_serializer.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zg_career_hc_workforce_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zg_career_hc_workforce_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zg_career_hc_workforce_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_career_hc_workforce_postcondition_v1
    COMMAND xar_ck3_zg_career_hc_workforce_v1_test
  )

  add_executable(xar_ck3_zg_career_hc_workforce_mailbox_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1_serializer.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1_mailbox.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zg_career_hc_workforce_mailbox_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zg_career_hc_workforce_mailbox_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zg_career_hc_workforce_mailbox_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_career_hc_workforce_postcondition_v1_mailbox
    COMMAND xar_ck3_zg_career_hc_workforce_mailbox_v1_test
  )

  add_executable(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_mailbox_test
    src/zhongguo_workforce_normal_exit_snapshot_v1_mailbox.cpp
    src/zhongguo_workforce_normal_exit_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_mailbox_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_workforce_normal_exit_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_mailbox_test
  )

  add_executable(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_source_contract_test
    src/zhongguo_workforce_normal_exit_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_source_contract_test
    PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_source_contract_test
      PRIVATE /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_workforce_normal_exit_snapshot_v1_source_contract
    COMMAND
      xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_workforce_normal_exit_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_normal_exit_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_normal_exit_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_normal_exit_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_workforce_normal_exit_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_workforce_normal_exit_snapshot_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/zhongguo-workforce-normal-exit-snapshot-v1.md
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_workforce_normal_exit_fact_effects.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_workforce_rehire_fact_effects.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_b2_075_exit_offer_effects.txt
  )

  add_executable(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_mailbox_test
    src/zhongguo_workforce_collective_snapshot_v1_mailbox.cpp
    src/zhongguo_workforce_collective_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_mailbox_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_workforce_collective_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_workforce_collective_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_workforce_collective_snapshot_v1_mailbox_test
  )

  add_executable(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_source_contract_test
    src/zhongguo_workforce_collective_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_source_contract_test
    PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_workforce_collective_snapshot_v1_source_contract_test
      PRIVATE /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_workforce_collective_snapshot_v1_source_contract
    COMMAND
      xar_ck3_zhongguo_workforce_collective_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_workforce_collective_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_collective_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_collective_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_collective_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_workforce_collective_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_workforce_collective_snapshot_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/zhongguo-workforce-collective-snapshot-v1.md
  )

  add_executable(xar_ck3_zhongguo_result_case_snapshot_v1_mailbox_test
    src/zhongguo_result_case_snapshot_v1_mailbox.cpp
    src/zhongguo_result_case_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_result_case_snapshot_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_result_case_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_result_case_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_result_case_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_result_case_snapshot_v1_mailbox_test
  )

  add_executable(xar_ck3_zhongguo_result_case_snapshot_v1_source_contract_test
    src/zhongguo_result_case_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_result_case_snapshot_v1_source_contract_test
    PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_result_case_snapshot_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_result_case_snapshot_v1_source_contract
    COMMAND xar_ck3_zhongguo_result_case_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_result_case_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_result_case_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_result_case_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_result_case_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_result_case_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_result_case_snapshot_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_core_result_delivery_effects.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/events/zg361_events.txt
  )

  add_executable(xar_ck3_title_map_navigation_v1_test
    src/title_map_navigation_v1.cpp
    src/title_map_navigation_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_title_map_navigation_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_title_map_navigation_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_title_map_navigation_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_title_map_navigation_v1
    COMMAND xar_ck3_title_map_navigation_v1_test
  )

  add_executable(xar_ck3_title_map_navigation_v1_camera_test
    src/title_map_navigation_v1.cpp
    src/title_map_navigation_v1_camera.cpp
    src/title_map_navigation_v1_camera_test.cpp
  )
  target_include_directories(
    xar_ck3_title_map_navigation_v1_camera_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_title_map_navigation_v1_camera_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_title_map_navigation_v1_camera_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_title_map_navigation_v1_camera
    COMMAND xar_ck3_title_map_navigation_v1_camera_test
  )

  add_executable(xar_ck3_title_map_navigation_v1_serializer_test
    src/title_map_navigation_v1.cpp
    src/title_map_navigation_v1_camera.cpp
    src/title_map_navigation_v1_serializer.cpp
    src/title_map_navigation_v1_serializer_test.cpp
  )
  target_include_directories(
    xar_ck3_title_map_navigation_v1_serializer_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_title_map_navigation_v1_serializer_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_title_map_navigation_v1_serializer_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_title_map_navigation_v1_serializer
    COMMAND xar_ck3_title_map_navigation_v1_serializer_test
  )

  add_executable(xar_ck3_title_map_navigation_v1_mailbox_test
    src/main_thread_query_mailbox_v1.cpp
    src/title_map_navigation_v1.cpp
    src/title_map_navigation_v1_mailbox.cpp
    src/title_map_navigation_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_title_map_navigation_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_title_map_navigation_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_title_map_navigation_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_title_map_navigation_v1_mailbox
    COMMAND xar_ck3_title_map_navigation_v1_mailbox_test
  )

  add_executable(xar_ck3_loaded_feature_manifest_v1_test
    src/loaded_feature_manifest_v1.cpp
    src/loaded_feature_manifest_v1_serializer.cpp
    src/loaded_feature_manifest_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_loaded_feature_manifest_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_loaded_feature_manifest_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_loaded_feature_manifest_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_loaded_feature_manifest_v1
    COMMAND xar_ck3_loaded_feature_manifest_v1_test
  )

  add_executable(xar_ck3_loaded_feature_manifest_v1_mailbox_test
    src/loaded_feature_manifest_v1_mailbox.cpp
    src/loaded_feature_manifest_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_loaded_feature_manifest_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_loaded_feature_manifest_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_loaded_feature_manifest_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_loaded_feature_manifest_v1_mailbox
    COMMAND xar_ck3_loaded_feature_manifest_v1_mailbox_test
  )

  add_executable(xar_ck3_loaded_feature_manifest_v1_source_contract_test
    src/loaded_feature_manifest_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_loaded_feature_manifest_v1_source_contract_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_loaded_feature_manifest_v1_source_contract_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_loaded_feature_manifest_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_loaded_feature_manifest_v1_source_contract
    COMMAND xar_ck3_loaded_feature_manifest_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/loaded_feature_manifest_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/loaded_feature_manifest_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/loaded_feature_manifest_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/loaded_feature_manifest_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/main_thread_query_mailbox_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/main_thread_query_mailbox_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/loaded_feature_manifest_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/loaded_feature_manifest_v1_source_contract.json
  )

  add_executable(xar_ck3_pending_character_interaction_context_v1_test
    src/pending_character_interaction_context_v1.cpp
    src/pending_character_interaction_context_v1_serializer.cpp
    src/pending_character_interaction_context_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_pending_character_interaction_context_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_pending_character_interaction_context_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_pending_character_interaction_context_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_pending_character_interaction_context_v1
    COMMAND xar_ck3_pending_character_interaction_context_v1_test
  )

  add_executable(xar_ck3_pending_character_interaction_context_v1_mailbox_test
    src/pending_character_interaction_context_v1_mailbox.cpp
    src/pending_character_interaction_context_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_pending_character_interaction_context_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_pending_character_interaction_context_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_pending_character_interaction_context_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_pending_character_interaction_context_v1_mailbox
    COMMAND xar_ck3_pending_character_interaction_context_v1_mailbox_test
  )

  add_executable(xar_ck3_pending_interaction_v1_source_contract_test
    src/pending_character_interaction_context_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_pending_interaction_v1_source_contract_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_pending_interaction_v1_source_contract_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_pending_interaction_v1_source_contract_test
      PRIVATE /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_pending_character_interaction_context_v1_source_contract
    COMMAND xar_ck3_pending_interaction_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/pending_character_interaction_context_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/pending_character_interaction_context_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/pending_character_interaction_context_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/pending_character_interaction_context_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/pending_character_interaction_context_v1_source_contract.json
  )

  add_executable(xar_ck3_verified_owner_wake_v1_test src/verified_owner_wake_v1_test.cpp)
  target_include_directories(xar_ck3_verified_owner_wake_v1_test PRIVATE include)
  target_compile_features(xar_ck3_verified_owner_wake_v1_test PRIVATE cxx_std_20)
  target_link_libraries(xar_ck3_verified_owner_wake_v1_test PRIVATE user32)
  add_test(NAME xar_ck3_native_bridge_verified_owner_wake_v1 COMMAND xar_ck3_verified_owner_wake_v1_test)

  add_executable(xar_ck3_main_thread_query_mailbox_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/main_thread_query_mailbox_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_main_thread_query_mailbox_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_main_thread_query_mailbox_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_main_thread_query_mailbox_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_main_thread_query_mailbox_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_main_thread_query_mailbox_v1
    COMMAND xar_ck3_main_thread_query_mailbox_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/src/main_thread_query_mailbox_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/main_thread_query_mailbox_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/main_thread_query_mailbox_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/main-thread-query-mailbox.md
      "${XAR_CK3_EXECUTABLE_PATH}"
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/route_contact_horizon_v1_dispatch.hpp
  )

  add_executable(xar_ck3_war_entry_assessments_v1_test
    src/war_entry_assessments_v1.cpp
    src/war_entry_assessments_v1_serializer.cpp
    src/war_entry_assessments_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_war_entry_assessments_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_war_entry_assessments_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_war_entry_assessments_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_war_entry_assessments_v1
    COMMAND xar_ck3_war_entry_assessments_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/war_entry_assessments_v1_golden.json
  )

  add_executable(xar_ck3_war_entry_assessments_v1_source_contract_test
    src/war_entry_assessments_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_war_entry_assessments_v1_source_contract_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_war_entry_assessments_v1_source_contract_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_war_entry_assessments_v1_source_contract_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_war_entry_assessments_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_war_entry_assessments_v1_source_contract
    COMMAND xar_ck3_war_entry_assessments_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/war_entry_assessments_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/war_entry_assessments_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/war_entry_assessments_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/war_entry_assessments_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/war_entry_assessments_v1_golden.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/war-declaration.md
      "${XAR_CK3_EXECUTABLE_PATH}"
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
  )

  add_executable(xar_ck3_war_termination_same_frame_source_contract_test
    src/war_termination_same_frame_source_contract_test.cpp
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_war_termination_same_frame_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_war_termination_same_frame_source_contract
    COMMAND xar_ck3_war_termination_same_frame_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
  )

  add_executable(xar_ck3_raiktor_surrender_six_domain_v1_test
    src/raiktor_surrender_six_domain_v1.cpp
    src/raiktor_surrender_six_domain_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_raiktor_surrender_six_domain_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_raiktor_surrender_six_domain_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_raiktor_surrender_six_domain_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_raiktor_surrender_six_domain_v1
    COMMAND xar_ck3_raiktor_surrender_six_domain_v1_test
  )

  add_executable(xar_ck3_raiktor_surrender_truce_v1_test
    src/raiktor_surrender_truce_v1.cpp
    src/raiktor_surrender_truce_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_raiktor_surrender_truce_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_raiktor_surrender_truce_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1 OR
     XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2)
    target_compile_definitions(
      xar_ck3_raiktor_surrender_truce_v1_test PRIVATE
      XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1=1
    )
  endif()
  if(MSVC)
    target_compile_options(
      xar_ck3_raiktor_surrender_truce_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_raiktor_surrender_truce_v1
    COMMAND xar_ck3_raiktor_surrender_truce_v1_test
  )

  add_executable(xar_ck3_g2_truce_native_callsite_observer_v1_test
    src/g2_truce_native_callsite_observer_v1.cpp
    src/g2_truce_native_callsite_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_g2_truce_native_callsite_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_g2_truce_native_callsite_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_g2_truce_native_callsite_observer_v1_test
      PRIVATE /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_g2_truce_native_callsite_observer_v1
    COMMAND xar_ck3_g2_truce_native_callsite_observer_v1_test
  )

  add_executable(xar_ck3_g2_truce_preview_entry_observer_v1_test
    src/g2_truce_preview_entry_observer_v1.cpp
    src/g2_truce_preview_entry_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_g2_truce_preview_entry_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_g2_truce_preview_entry_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_g2_truce_preview_entry_observer_v1_test
      PRIVATE /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_g2_truce_preview_entry_observer_v1
    COMMAND xar_ck3_g2_truce_preview_entry_observer_v1_test
  )

  add_executable(xar_ck3_raiktor_war_bound_regiment_v1_test
    src/raiktor_war_bound_regiment_v1.cpp
    src/raiktor_war_bound_regiment_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_raiktor_war_bound_regiment_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_raiktor_war_bound_regiment_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_raiktor_war_bound_regiment_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_raiktor_war_bound_regiment_v1
    COMMAND xar_ck3_raiktor_war_bound_regiment_v1_test
  )

  add_executable(xar_ck3_raiktor_war_bound_loss_candidate_v1_test
    src/raiktor_war_bound_regiment_v1.cpp
    src/raiktor_war_bound_loss_candidate_v1.cpp
    src/raiktor_war_bound_loss_candidate_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_raiktor_war_bound_loss_candidate_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_raiktor_war_bound_loss_candidate_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_raiktor_war_bound_loss_candidate_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_raiktor_war_bound_loss_candidate_v1
    COMMAND xar_ck3_raiktor_war_bound_loss_candidate_v1_test
  )

  add_executable(xar_ck3_war_entry_assessments_v1_mailbox_test
    src/main_thread_query_mailbox_v1.cpp
    src/war_entry_assessments_v1.cpp
    src/war_entry_assessments_v1_mailbox.cpp
    src/war_entry_assessments_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_war_entry_assessments_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_war_entry_assessments_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_war_entry_assessments_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_war_entry_assessments_v1_mailbox
    COMMAND xar_ck3_war_entry_assessments_v1_mailbox_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/war_entry_assessments_v1_mailbox.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/war_entry_assessments_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/war_entry_assessments_v1_mailbox_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/war-declaration.md
  )

  add_executable(xar_ck3_exit_terms_v2_test_only_serializer_test
    src/war_exit_terms_v2_test_only.cpp
    src/war_exit_terms_wire.cpp
    src/war_exit_terms_v2_test_only_test.cpp
  )
  target_include_directories(
    xar_ck3_exit_terms_v2_test_only_serializer_test PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_exit_terms_v2_test_only_serializer_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_exit_terms_v2_test_only_serializer
    COMMAND xar_ck3_exit_terms_v2_test_only_serializer_test
      ${CMAKE_CURRENT_SOURCE_DIR}/../tests/fixtures/war_termination_exit_terms_v2_synthetic.json
  )

  add_executable(xar_ck3_startup_particle2_stage_recorder_v1_test
    src/startup_particle2_stage_recorder_v1.cpp
    src/startup_particle2_stage_recorder_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_particle2_stage_recorder_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_particle2_stage_recorder_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_startup_particle2_stage_recorder_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_particle2_stage_recorder_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_particle2_stage_recorder_v1
    COMMAND xar_ck3_startup_particle2_stage_recorder_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/startup_particle2_stage_recorder_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/startup_particle2_stage_recorder_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/startup_particle2_stage_recorder_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/startup_particle2_stage_recorder_v1_source_contract.json
      "${XAR_CK3_EXECUTABLE_PATH}"
      ${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
  )

  add_executable(xar_ck3_particle2_factory_debug_capture
    research/particle2_factory_debug_capture.cpp
  )
  target_compile_definitions(
    xar_ck3_particle2_factory_debug_capture PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_particle2_factory_debug_capture PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_particle2_factory_debug_capture PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_particle2_factory_debug_capture_self_test
    COMMAND xar_ck3_particle2_factory_debug_capture --self-test
  )

  add_executable(xar_ck3_startup_particle2_null_guard_v1_test
    src/startup_particle2_null_guard_v1.cpp
    src/startup_particle2_null_guard_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_particle2_null_guard_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_particle2_null_guard_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_startup_particle2_null_guard_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_particle2_null_guard_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_particle2_null_guard_v1
    COMMAND xar_ck3_startup_particle2_null_guard_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/startup_particle2_null_guard_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/startup_particle2_null_guard_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/startup_particle2_null_guard_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/startup_particle2_null_guard_v1_source_contract.json
      "${XAR_CK3_EXECUTABLE_PATH}"
  )

  add_executable(xar_ck3_startup_particle2_consumer_null_guard_v1_test
    src/startup_particle2_consumer_null_guard_v1.cpp
    src/startup_particle2_consumer_null_guard_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_particle2_consumer_null_guard_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_particle2_consumer_null_guard_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_startup_particle2_consumer_null_guard_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_particle2_consumer_null_guard_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_particle2_consumer_null_guard_v1
    COMMAND xar_ck3_startup_particle2_consumer_null_guard_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/startup_particle2_consumer_null_guard_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/startup_particle2_consumer_null_guard_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/startup_particle2_consumer_null_guard_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/startup_particle2_consumer_null_guard_v1_source_contract.json
      "${XAR_CK3_EXECUTABLE_PATH}"
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
  )

  add_executable(xar_ck3_startup_dx11_render_context_draw_guard_v1_test
    src/startup_dx11_render_context_draw_guard_v1.cpp
    src/startup_dx11_render_context_draw_guard_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_dx11_render_context_draw_guard_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_dx11_render_context_draw_guard_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_startup_dx11_render_context_draw_guard_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_dx11_render_context_draw_guard_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_dx11_render_context_draw_guard_v1
    COMMAND xar_ck3_startup_dx11_render_context_draw_guard_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/startup_dx11_render_context_draw_guard_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/startup_dx11_render_context_draw_guard_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/startup_dx11_render_context_draw_guard_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/startup_dx11_render_context_draw_guard_v1_source_contract.json
      "${XAR_CK3_EXECUTABLE_PATH}"
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
  )

  add_executable(xar_ck3_startup_localize_current_root_guard_v1_test
    src/startup_localize_current_root_guard_v1.cpp
    src/startup_localize_current_root_guard_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_localize_current_root_guard_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_localize_current_root_guard_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_startup_localize_current_root_guard_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_localize_current_root_guard_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_localize_current_root_guard_v1
    COMMAND xar_ck3_startup_localize_current_root_guard_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/startup_localize_current_root_guard_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/startup_localize_current_root_guard_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/startup_localize_current_root_guard_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/startup_localize_current_root_guard_v1_source_contract.json
      "${XAR_CK3_EXECUTABLE_PATH}"
      ${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
  )

  add_executable(xar_ck3_startup_widget_null_flag_call_guard_v1_test
    src/startup_widget_null_flag_call_guard_v1.cpp
    src/startup_widget_null_flag_call_guard_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_widget_null_flag_call_guard_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_widget_null_flag_call_guard_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_widget_null_flag_call_guard_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_widget_null_flag_call_guard_v1
    COMMAND xar_ck3_startup_widget_null_flag_call_guard_v1_test
  )

  add_executable(xar_ck3_startup_rbx_null_call_guard_v1_test
    src/startup_rbx_null_call_guard_v1.cpp
    src/startup_rbx_null_call_guard_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_rbx_null_call_guard_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_rbx_null_call_guard_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_rbx_null_call_guard_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_rbx_null_call_guard_v1
    COMMAND xar_ck3_startup_rbx_null_call_guard_v1_test
  )

  add_executable(xar_ck3_phase2_completion_observer_v1_test
    src/phase2_completion_observer_v1.cpp
    src/phase2_completion_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_phase2_completion_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_phase2_completion_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_phase2_completion_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_phase2_completion_observer_v1
    COMMAND xar_ck3_phase2_completion_observer_v1_test
  )

  add_executable(xar_ck3_phase2_wrapper_entry_observer_v1_test
    src/phase2_wrapper_entry_observer_v1.cpp
    src/phase2_wrapper_entry_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_phase2_wrapper_entry_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_phase2_wrapper_entry_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_phase2_wrapper_entry_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_phase2_wrapper_entry_observer_v1
    COMMAND xar_ck3_phase2_wrapper_entry_observer_v1_test
  )

  add_executable(xar_ck3_phase2_wrapper_consumer_edge_observer_v1_test
    src/phase2_wrapper_consumer_edge_observer_v1.cpp
    src/phase2_wrapper_consumer_edge_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_phase2_wrapper_consumer_edge_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_phase2_wrapper_consumer_edge_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_phase2_wrapper_consumer_edge_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_phase2_wrapper_consumer_edge_observer_v1
    COMMAND xar_ck3_phase2_wrapper_consumer_edge_observer_v1_test
  )

  add_executable(xar_ck3_phase2_post_call_observer_v1_test
    src/phase2_post_call_observer_v1.cpp
    src/phase2_post_call_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_phase2_post_call_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_phase2_post_call_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_phase2_post_call_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_phase2_post_call_observer_v1
    COMMAND xar_ck3_phase2_post_call_observer_v1_test
  )

  add_executable(xar_ck3_phase2_post_call_list_identity_observer_v1_test
    src/phase2_post_call_list_identity_observer_v1.cpp
    src/phase2_post_call_list_identity_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_phase2_post_call_list_identity_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_phase2_post_call_list_identity_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_phase2_post_call_list_identity_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_phase2_post_call_list_identity_observer_v1
    COMMAND xar_ck3_phase2_post_call_list_identity_observer_v1_test
  )

  add_executable(xar_ck3_phase2_producer_identity_observer_v1_test
    src/phase2_producer_identity_observer_v1.cpp
    src/phase2_producer_identity_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_phase2_producer_identity_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_phase2_producer_identity_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_phase2_producer_identity_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_phase2_producer_identity_observer_v1
    COMMAND xar_ck3_phase2_producer_identity_observer_v1_test
  )

  add_executable(xar_ck3_cold_map_vfs_observer_v1_test
    src/cold_map_vfs_observer_v1.cpp
    src/cold_map_vfs_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_cold_map_vfs_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_cold_map_vfs_observer_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_cold_map_vfs_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_cold_map_vfs_observer_v1
    COMMAND xar_ck3_cold_map_vfs_observer_v1_test
  )

  add_executable(xar_ck3_named_path_583_root_observer_v1_test
    src/named_path_583_root_observer_v1.cpp
    src/named_path_583_root_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_named_path_583_root_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_named_path_583_root_observer_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_named_path_583_root_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_named_path_583_root_observer_v1
    COMMAND xar_ck3_named_path_583_root_observer_v1_test
  )
  add_test(
    NAME xar_ck3_native_bridge_named_path_583_root_observer_v1_source_contract
    COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/test_named_path_583_root_observer_v1_source_contract.py
      --root ${CMAKE_CURRENT_SOURCE_DIR}/../..
      --ck3-executable "${XAR_CK3_EXECUTABLE_PATH}"
  )

  add_executable(xar_ck3_pdx_paths_583_producer_observer_v1_test
    src/pdx_paths_583_producer_observer_v1.cpp
    src/pdx_paths_583_producer_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_pdx_paths_583_producer_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_pdx_paths_583_producer_observer_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_pdx_paths_583_producer_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_pdx_paths_583_producer_observer_v1
    COMMAND xar_ck3_pdx_paths_583_producer_observer_v1_test
  )
  add_test(
    NAME xar_ck3_native_bridge_pdx_paths_583_producer_observer_v1_source_contract
    COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/test_pdx_paths_583_producer_observer_v1_source_contract.py
      --root ${CMAKE_CURRENT_SOURCE_DIR}/../..
      --ck3-executable "${XAR_CK3_EXECUTABLE_PATH}"
  )

  add_executable(xar_ck3_vfs_mount_lifecycle_observer_v1_test
    src/vfs_mount_lifecycle_observer_v1.cpp
    src/vfs_mount_lifecycle_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_vfs_mount_lifecycle_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_vfs_mount_lifecycle_observer_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_vfs_mount_lifecycle_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_vfs_mount_lifecycle_observer_v1
    COMMAND xar_ck3_vfs_mount_lifecycle_observer_v1_test
  )
  add_test(
    NAME xar_ck3_native_bridge_vfs_mount_lifecycle_observer_v1_source_contract
    COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/test_vfs_mount_lifecycle_observer_v1_source_contract.py
      --root ${CMAKE_CURRENT_SOURCE_DIR}/../..
      --ck3-executable "${XAR_CK3_EXECUTABLE_PATH}"
  )

  add_executable(xar_ck3_physfs_mounted_data_observer_v1_test
    src/physfs_mounted_data_observer_v1.cpp
    src/physfs_mounted_data_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_physfs_mounted_data_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_physfs_mounted_data_observer_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_physfs_mounted_data_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_physfs_mounted_data_observer_v1
    COMMAND xar_ck3_physfs_mounted_data_observer_v1_test
  )
  add_test(
    NAME xar_ck3_native_bridge_physfs_mounted_data_observer_v1_source_contract
    COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/test_physfs_mounted_data_observer_v1_source_contract.py
      --root ${CMAKE_CURRENT_SOURCE_DIR}/../..
      --ck3-executable "${XAR_CK3_EXECUTABLE_PATH}"
  )
  add_test(
    NAME xar_ck3_native_bridge_extract_bridge_observer_state_from_minidump
    COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/test_extract_bridge_observer_state_from_minidump.py
  )
  add_executable(xar_ck3_h2743_war_storage_candidate_v1_test
    src/h2743_war_storage_candidate_v1_test.cpp)
  target_include_directories(xar_ck3_h2743_war_storage_candidate_v1_test
    PRIVATE include)
  if(MSVC)
    target_compile_options(xar_ck3_h2743_war_storage_candidate_v1_test
      PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_h2743_war_storage_candidate_v1
    COMMAND xar_ck3_h2743_war_storage_candidate_v1_test)

  add_test(
    NAME xar_ck3_native_bridge_suspended_injection
    COMMAND xar_ck3_bridge_host
      $<TARGET_FILE:xar_ck3_bridge>
      $<TARGET_FILE:xar_ck3_bridge_injector>
      $<TARGET_FILE:xar_ck3_bridge_target>
  )
  set_tests_properties(xar_ck3_native_bridge_suspended_injection
    PROPERTIES TIMEOUT 30)

  add_test(
    NAME xar_ck3_native_bridge_running_attach
    COMMAND xar_ck3_bridge_attach_host
      $<TARGET_FILE:xar_ck3_bridge>
      $<TARGET_FILE:xar_ck3_bridge_injector>
      $<TARGET_FILE:xar_ck3_bridge_target>
  )
  set_tests_properties(xar_ck3_native_bridge_running_attach
    PROPERTIES TIMEOUT 30)
endif()

# The flag stays numeric and default OFF. Only the fixed H2743 callback is
# admitted by the bridge install owner when this candidate is explicitly ON.
include(cmake/h2743_stock_predicate_reader_v1.cmake)

# Every fixture compiling the shared religion mailbox needs all its siblings.
if(BUILD_TESTING AND XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
  set(XAR_G2_RELIGION_CONTEXT_FIXTURE_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_devotion_profile.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_rite_virtue_sin_profile.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_vow_of_poverty_terms.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_confession_rite_permission.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_doctrine12002_tenet_rows.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_tenet_sources.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/religion_reform12002_window.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_pilgrimage_candidate_factory.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_pilgrimage_activity_terms.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_pilgrimage_candidate_route.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_province.cpp")
  foreach(religion_target IN ITEMS
      xar_ck3_12002_religion_mailbox_test
      xar_ck3_12003_religion_type_tax_mailbox_test
      xar_ck3_12003_religion_devotion_virtues_mailbox_test
      xar_ck3_12003_confession_permission_mailbox_test
      xar_ck3_12003_pilgrimage_headless_mailbox_test)
    if(TARGET ${religion_target})
      target_sources(${religion_target} PRIVATE ${XAR_G2_RELIGION_CONTEXT_FIXTURE_SOURCES})
    endif()
  endforeach()
endif()

if(BUILD_TESTING)
  add_executable(xar_ck3_12003_battle_current_state_test
    src/ck3_12002_phase_character.cpp
    src/ck3_12003_context_sources.cpp
    src/ck3_12003_task_position_inputs.cpp
    src/ck3_12002_battle.cpp
    src/ck3_12002_combat.cpp
    src/ck3_12002_battle_journal.cpp
    src/ck3_12002_routes.cpp
    src/ck3_12003_battle_current_state.cpp
    src/battle_transition_v1_mailbox.cpp
    src/battle_control_snapshot_v1_mailbox.cpp
    src/ck3_12003_battle_current_state_test.cpp)
  target_include_directories(xar_ck3_12003_battle_current_state_test PRIVATE include)
  target_compile_features(xar_ck3_12003_battle_current_state_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_battle_current_state_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_SELECTED_ROLL_WIRE_FIXTURE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_battle_current_state_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  target_link_libraries(xar_ck3_12003_battle_current_state_test PRIVATE kernel32)
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/ck3_12003_battle_current_state_wire")
  add_test(NAME xar_ck3_12003_battle_current_state_test
    COMMAND xar_ck3_12003_battle_current_state_test
      "${CMAKE_BINARY_DIR}/ck3_12003_battle_current_state_wire")
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/ck3_12003_selected_roll_wire")
  add_test(NAME xar_ck3_12003_selected_commander_next_roll_bounds
    COMMAND xar_ck3_12003_battle_current_state_test --selected-roll-only
      "${CMAKE_BINARY_DIR}/ck3_12003_selected_roll_wire")
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/ck3_12003_actual_geography_wire")
  add_test(NAME xar_ck3_12003_actual_battle_geography
    COMMAND xar_ck3_12003_battle_current_state_test --actual-geography-only
      "${CMAKE_BINARY_DIR}/ck3_12003_actual_geography_wire")
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/ck3_12003_retained_rule_effects_wire")
  add_test(NAME xar_ck3_12003_retained_rule_effects
    COMMAND xar_ck3_12003_battle_current_state_test --retained-rule-effects-only
      "${CMAKE_BINARY_DIR}/ck3_12003_retained_rule_effects_wire")
endif()

# Focused current knight effectiveness context reader and literal bridge wire.
if(BUILD_TESTING AND WIN32)
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
  set(XAR_KNIGHT_CONTEXT_FIXTURE_DIR
    "${CMAKE_BINARY_DIR}/ck3_12003_knight_effectiveness_context_wire")
  set(XAR_KNIGHT_CONTEXT_SERIALIZER
    "${XAR_KNIGHT_CONTEXT_FIXTURE_DIR}/production_knights_serializer.cpp")
  add_custom_command(
    OUTPUT "${XAR_KNIGHT_CONTEXT_SERIALIZER}"
    COMMAND "${Python3_EXECUTABLE}" -B
      "${CMAKE_CURRENT_SOURCE_DIR}/tests/project_knight_context_serializer.py"
      --source "${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp"
      --output "${XAR_KNIGHT_CONTEXT_SERIALIZER}"
      --receipt "${XAR_KNIGHT_CONTEXT_FIXTURE_DIR}/SERIALIZER-PROJECTION.json"
    DEPENDS src/bridge.cpp tests/project_knight_context_serializer.py
    VERBATIM)
  add_executable(xar_ck3_12003_knight_effectiveness_context_test
    src/ck3_12002_combat.cpp
    tests/knight_effectiveness_context_12003_test.cpp
    "${XAR_KNIGHT_CONTEXT_SERIALIZER}")
  target_include_directories(xar_ck3_12003_knight_effectiveness_context_test PRIVATE include)
  target_compile_features(xar_ck3_12003_knight_effectiveness_context_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_knight_effectiveness_context_test PRIVATE NOMINMAX)
  if(MSVC)
    target_compile_options(xar_ck3_12003_knight_effectiveness_context_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_12003_knight_effectiveness_context_test
    COMMAND xar_ck3_12003_knight_effectiveness_context_test
      "${XAR_KNIGHT_CONTEXT_FIXTURE_DIR}")
endif()

if(BUILD_TESTING)
  add_executable(xar_ck3_12003_pre_291e210_1640_test
    src/ck3_12003_context_sources.cpp
    tests/pre_291e210_1640_12003_test.cpp)
  target_include_directories(xar_ck3_12003_pre_291e210_1640_test PRIVATE include)
  target_compile_features(xar_ck3_12003_pre_291e210_1640_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_pre_291e210_1640_test PRIVATE NOMINMAX)
  if(MSVC)
    target_compile_options(xar_ck3_12003_pre_291e210_1640_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_12003_pre_291e210_1640_test
    COMMAND xar_ck3_12003_pre_291e210_1640_test)
endif()

if(BUILD_TESTING)
  add_executable(xar_ck3_12003_post_291d7e0_sources_test
    src/ck3_12003_context_sources.cpp
    tests/post_291d7e0_sources_12003_test.cpp)
  target_include_directories(xar_ck3_12003_post_291d7e0_sources_test PRIVATE include)
  target_compile_features(xar_ck3_12003_post_291d7e0_sources_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_post_291d7e0_sources_test PRIVATE NOMINMAX)
  if(MSVC)
    target_compile_options(xar_ck3_12003_post_291d7e0_sources_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_12003_post_291d7e0_sources_test
    COMMAND xar_ck3_12003_post_291d7e0_sources_test
      "${CMAKE_BINARY_DIR}/post_291d7e0_sources_wire.json")
endif()

if(BUILD_TESTING)
  add_executable(xar_ck3_12003_person_later_direct_test
    src/ck3_12003_context_sources.cpp
    tests/person_later_direct_12003_test.cpp)
  target_include_directories(xar_ck3_12003_person_later_direct_test PRIVATE include)
  target_compile_features(xar_ck3_12003_person_later_direct_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_person_later_direct_test PRIVATE NOMINMAX)
  if(MSVC)
    target_compile_options(xar_ck3_12003_person_later_direct_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_12003_person_later_direct_test
    COMMAND xar_ck3_12003_person_later_direct_test
      "${CMAKE_BINARY_DIR}/ck3_12003_person_later_direct_wire")
endif()

if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_person_auxiliary_scratch_test
    src/ck3_12002_phase_character.cpp
    src/ck3_12003_context_sources.cpp
    src/ck3_12003_task_position_inputs.cpp
    src/ck3_12002_battle.cpp
    src/ck3_12002_combat.cpp
    src/ck3_12002_battle_journal.cpp
    src/ck3_12002_routes.cpp
    src/ck3_12003_battle_current_state.cpp
    tests/person_auxiliary_scratch_12003_test.cpp)
  target_include_directories(xar_ck3_12003_person_auxiliary_scratch_test PRIVATE include)
  target_compile_features(xar_ck3_12003_person_auxiliary_scratch_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_person_auxiliary_scratch_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_person_auxiliary_scratch_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  target_link_libraries(xar_ck3_12003_person_auxiliary_scratch_test PRIVATE kernel32)
  add_test(NAME xar_ck3_12003_person_auxiliary_scratch_test
    COMMAND xar_ck3_12003_person_auxiliary_scratch_test
      "${CMAKE_BINARY_DIR}/person_auxiliary_scratch_12003.json")
endif()

if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_person_nine_cache_bytes_test
    src/ck3_12002_phase_character.cpp
    src/ck3_12003_context_sources.cpp
    src/ck3_12003_task_position_inputs.cpp
    src/ck3_12002_battle.cpp
    src/ck3_12002_combat.cpp
    src/ck3_12002_battle_journal.cpp
    src/ck3_12002_routes.cpp
    src/ck3_12003_battle_current_state.cpp
    tests/person_nine_cache_bytes_12003_test.cpp)
  target_include_directories(xar_ck3_12003_person_nine_cache_bytes_test PRIVATE include)
  target_compile_features(xar_ck3_12003_person_nine_cache_bytes_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_person_nine_cache_bytes_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_person_nine_cache_bytes_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  target_link_libraries(xar_ck3_12003_person_nine_cache_bytes_test PRIVATE kernel32)
  add_test(NAME xar_ck3_12003_person_nine_cache_bytes_test
    COMMAND xar_ck3_12003_person_nine_cache_bytes_test
      "${CMAKE_BINARY_DIR}/person_nine_cache_bytes_12003.json")
endif()

if(BUILD_TESTING)
  add_executable(xar_ck3_12003_person_helper_291f0a0_test
    src/ck3_12003_context_sources.cpp
    tests/person_helper_291f0a0_12003_test.cpp)
  target_include_directories(xar_ck3_12003_person_helper_291f0a0_test PRIVATE include)
  target_compile_features(xar_ck3_12003_person_helper_291f0a0_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_person_helper_291f0a0_test PRIVATE NOMINMAX)
  if(MSVC)
    target_compile_options(xar_ck3_12003_person_helper_291f0a0_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_12003_person_helper_291f0a0_test
    COMMAND xar_ck3_12003_person_helper_291f0a0_test
      "${CMAKE_BINARY_DIR}/ck3_12003_person_helper_291f0a0_wire")
endif()

# Selected-unit total rates: new focused production reader/serializer/MCP cases.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_commander_movement_speed_test
    src/ck3_12002_army.cpp
    src/ck3_12003_army_replenishment_records.cpp
    src/ck3_12003_army_supply_timing.cpp
    src/ck3_12003_commander.cpp
    src/ck3_12003_commander_mailbox.cpp
    src/ck3_12002_query_mailbox.cpp
    src/ck3_12003_abi_profile.cpp
    src/ck3_12003_commander_movement_speed_test.cpp)
  target_include_directories(xar_ck3_12003_commander_movement_speed_test PRIVATE include)
  target_compile_features(xar_ck3_12003_commander_movement_speed_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_commander_movement_speed_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_commander_movement_speed_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy)
    target_link_options(xar_ck3_12003_commander_movement_speed_test PRIVATE /OPT:REF)
  endif()
  target_link_libraries(xar_ck3_12003_commander_movement_speed_test PRIVATE user32)
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/ck3_12003_commander_movement_speed_wire")
  add_test(NAME xar_ck3_12003_commander_movement_speed
    COMMAND xar_ck3_12003_commander_movement_speed_test
      "${CMAKE_BINARY_DIR}/ck3_12003_commander_movement_speed_wire")
  add_test(NAME xar_ck3_12003_commander_movement_speed_registered_mcp
    COMMAND ${Python3_EXECUTABLE}
      "${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/run_commander_movement_speed_mcp_fixture.py"
      --projection-root "${CMAKE_CURRENT_SOURCE_DIR}/../.."
      --native-dir "${CMAKE_BINARY_DIR}/ck3_12003_commander_movement_speed_wire")
  set_tests_properties(xar_ck3_12003_commander_movement_speed PROPERTIES
    FIXTURES_SETUP commander_movement_speed_wire)
  set_tests_properties(xar_ck3_12003_commander_movement_speed_registered_mcp PROPERTIES
    FIXTURES_REQUIRED commander_movement_speed_wire)
endif()

# Observed army update clock: exactly two new production reader/wire cases.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_army_update_clock_test
    src/ck3_12002_army.cpp
    src/ck3_12003_army_replenishment_records.cpp
    src/ck3_12003_army_supply_timing.cpp
    src/ck3_12003_army_update_clock_test.cpp)
  target_include_directories(xar_ck3_12003_army_update_clock_test PRIVATE include)
  target_compile_features(xar_ck3_12003_army_update_clock_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_army_update_clock_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_army_update_clock_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2)
    target_link_options(xar_ck3_12003_army_update_clock_test PRIVATE /OPT:REF)
  endif()
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/ck3_12003_army_update_clock_wire")
  add_test(NAME xar_ck3_12003_army_update_clock_two_cases
    COMMAND xar_ck3_12003_army_update_clock_test
      "${CMAKE_BINARY_DIR}/ck3_12003_army_update_clock_wire")
  add_test(NAME xar_ck3_12003_army_update_clock_registered_mcp
    COMMAND ${Python3_EXECUTABLE} -O
      "${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/run_army_update_clock_mcp_fixture.py"
      --projection-root "${CMAKE_CURRENT_SOURCE_DIR}/../.."
      --native-dir "${CMAKE_BINARY_DIR}/ck3_12003_army_update_clock_wire"
      --output-dir "${CMAKE_BINARY_DIR}/ck3_12003_army_update_clock_registered")
  set_tests_properties(xar_ck3_12003_army_update_clock_two_cases PROPERTIES
    FIXTURES_SETUP army_update_clock_wire)
  set_tests_properties(xar_ck3_12003_army_update_clock_registered_mcp PROPERTIES
    FIXTURES_REQUIRED army_update_clock_wire)
endif()

# Complete stored persistent DATA: two new production reader/wire cases only.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_army_replenishment_records_test
    src/ck3_12002_army.cpp
    src/ck3_12003_army_supply_timing.cpp
    src/ck3_12003_army_replenishment_records.cpp
    src/ck3_12003_army_replenishment_records_test.cpp)
  target_include_directories(xar_ck3_12003_army_replenishment_records_test PRIVATE include)
  target_compile_features(xar_ck3_12003_army_replenishment_records_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_army_replenishment_records_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_army_replenishment_records_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2)
    target_link_options(xar_ck3_12003_army_replenishment_records_test PRIVATE /OPT:REF)
  endif()
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/ck3_12003_army_replenishment_records_wire")
  add_test(NAME xar_ck3_12003_army_replenishment_records_two_cases
    COMMAND xar_ck3_12003_army_replenishment_records_test
      "${CMAKE_BINARY_DIR}/ck3_12003_army_replenishment_records_wire")
  add_test(NAME xar_ck3_12003_army_replenishment_records_registered_mcp
    COMMAND ${Python3_EXECUTABLE} -O
      "${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/run_army_replenishment_records_mcp_fixture.py"
      --projection-root "${CMAKE_CURRENT_SOURCE_DIR}/../.."
      --native-dir "${CMAKE_BINARY_DIR}/ck3_12003_army_replenishment_records_wire"
      --output-dir "${CMAKE_BINARY_DIR}/ck3_12003_army_replenishment_records_registered")
  set_tests_properties(xar_ck3_12003_army_replenishment_records_two_cases PROPERTIES
    FIXTURES_SETUP army_replenishment_records_wire)
  set_tests_properties(xar_ck3_12003_army_replenishment_records_registered_mcp PROPERTIES
    FIXTURES_REQUIRED army_replenishment_records_wire)
endif()

# Readonly writer admission and associated DATA setter operands: one new target.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_loss_writer_inputs_test
    src/ck3_12003_army_replenishment_records.cpp
    src/ck3_12003_loss_writer_inputs_test.cpp)
  target_include_directories(xar_ck3_12003_loss_writer_inputs_test PRIVATE include)
  target_compile_features(xar_ck3_12003_loss_writer_inputs_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_loss_writer_inputs_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_loss_writer_inputs_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2)
  endif()
  add_test(NAME xar_ck3_12003_loss_writer_inputs
    COMMAND xar_ck3_12003_loss_writer_inputs_test)
endif()

# Complete committed-route predictions reuse the production route reader and
# strengths serializer; the registered MCP consumes the four emitted packets.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_committed_route_timeline_test
    src/ck3_12002_army.cpp
    src/ck3_12002_routes.cpp
    src/ck3_12003_army_supply_timing.cpp
    src/ck3_12003_army_replenishment_records.cpp
    src/ck3_12003_committed_route_timeline_test.cpp)
  target_include_directories(xar_ck3_12003_committed_route_timeline_test PRIVATE include)
  target_compile_features(xar_ck3_12003_committed_route_timeline_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_committed_route_timeline_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_committed_route_timeline_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2)
    target_link_options(xar_ck3_12003_committed_route_timeline_test PRIVATE /OPT:REF)
  endif()
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/ck3_12003_committed_route_timeline_wire")
  add_test(NAME xar_ck3_12003_committed_route_timeline_four_cases
    COMMAND xar_ck3_12003_committed_route_timeline_test
      "${CMAKE_BINARY_DIR}/ck3_12003_committed_route_timeline_wire")
  add_test(NAME xar_ck3_12003_committed_route_timeline_registered_mcp
    COMMAND ${Python3_EXECUTABLE} -O
      "${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/run_committed_route_timeline_mcp_fixture.py"
      --projection-root "${CMAKE_CURRENT_SOURCE_DIR}/../.."
      --native-dir "${CMAKE_BINARY_DIR}/ck3_12003_committed_route_timeline_wire"
      --output-dir "${CMAKE_BINARY_DIR}/ck3_12003_committed_route_timeline_registered")
  set_tests_properties(xar_ck3_12003_committed_route_timeline_four_cases PROPERTIES
    FIXTURES_SETUP committed_route_timeline_wire)
  set_tests_properties(xar_ck3_12003_committed_route_timeline_registered_mcp PROPERTIES
    FIXTURES_REQUIRED committed_route_timeline_wire)
endif()

# Per-ArRg supply-loss eligibility: new focused production reader/wire fixture.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_supply_loss_eligibility_test
    src/ck3_12002_army.cpp
    src/ck3_12003_army_supply_timing.cpp
    src/ck3_12003_army_replenishment_records.cpp
    src/ck3_12003_supply_loss_eligibility_test.cpp)
  target_include_directories(xar_ck3_12003_supply_loss_eligibility_test PRIVATE include)
  target_compile_features(xar_ck3_12003_supply_loss_eligibility_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_supply_loss_eligibility_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_supply_loss_eligibility_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2)
    target_link_options(xar_ck3_12003_supply_loss_eligibility_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_supply_loss_eligibility
    COMMAND xar_ck3_12003_supply_loss_eligibility_test)
endif()

# Outcome invariants are synthetic DTO tests and never start or attach CK3.
if(BUILD_TESTING AND XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1)
  add_executable(xar_ck3_ingame_decision_outcome_contract_v1_test
    tests/ingame_decision_outcome_contract_v1_test.cpp src/protocol.cpp)
  target_include_directories(xar_ck3_ingame_decision_outcome_contract_v1_test PRIVATE include)
  target_compile_features(xar_ck3_ingame_decision_outcome_contract_v1_test PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(xar_ck3_ingame_decision_outcome_contract_v1_test PRIVATE /W4 /WX /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_ingame_decision_outcome_contract_v1 COMMAND xar_ck3_ingame_decision_outcome_contract_v1_test)
endif()

# Fixed text memory/UTF-8 tests; this target never starts or attaches CK3.
if(XAR_CK3_ENABLE_WHITE_RENDERED_TEXT_PRIVATE_V1)
  add_executable(xar_ck3_white_rendered_text_v1_test tests/white_rendered_text_v1_test.cpp)
  target_include_directories(xar_ck3_white_rendered_text_v1_test PRIVATE include)
  target_compile_features(xar_ck3_white_rendered_text_v1_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_white_rendered_text_v1_test PRIVATE NOMINMAX)
  target_compile_options(xar_ck3_white_rendered_text_v1_test PRIVATE $<$<CXX_COMPILER_ID:MSVC>:/UNDEBUG>)
  add_test(NAME xar_ck3_white_rendered_text_v1_test COMMAND xar_ck3_white_rendered_text_v1_test)
endif()

# Fixed six-policy tests use synthetic read_memory only; never attach CK3.
if(XAR_CK3_ENABLE_AUB_POLICY_OPTIONS_PRIVATE_V1)
  add_executable(xar_ck3_aub_policy_options_v1_test
    src/aub_policy_options_v1.cpp tests/aub_policy_options_delta.cpp)
  target_include_directories(xar_ck3_aub_policy_options_v1_test PRIVATE include)
  target_compile_features(xar_ck3_aub_policy_options_v1_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_aub_policy_options_v1_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  target_compile_options(xar_ck3_aub_policy_options_v1_test PRIVATE $<$<CXX_COMPILER_ID:MSVC>:/EHsc> $<$<CXX_COMPILER_ID:MSVC>:/W4> $<$<CXX_COMPILER_ID:MSVC>:/WX> $<$<CXX_COMPILER_ID:MSVC>:/UNDEBUG>)
  add_test(NAME xar_ck3_aub_policy_options_v1_test COMMAND xar_ck3_aub_policy_options_v1_test)
endif()

if(WIN32 AND MSVC)
  add_executable(xar_ck3_aub_business_state_v1_test
    src/aub_business_state_v1.cpp tests/aub_business_state_delta.cpp)
  target_include_directories(xar_ck3_aub_business_state_v1_test PRIVATE include)
  target_compile_features(xar_ck3_aub_business_state_v1_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_aub_business_state_v1_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  target_compile_options(xar_ck3_aub_business_state_v1_test PRIVATE /EHsc /W4 /WX /UNDEBUG)
  add_test(NAME xar_ck3_aub_business_state_v1_test COMMAND xar_ck3_aub_business_state_v1_test)
  add_test(NAME xar_ck3_aub_business_state_serialization_v1_test COMMAND xar_ck3_aub_business_state_v1_test serialization)
endif()

# Six literal skill+1 mappings; never starts or attaches CK3.
if(XAR_CK3_ENABLE_WHITE_CONTROL_ACTIONS_PRIVATE_V1)
  add_executable(xar_ck3_white_numeric_control_specs_v1_test tests/white_numeric_control_specs_v1_test.cpp)
  target_include_directories(xar_ck3_white_numeric_control_specs_v1_test PRIVATE include)
  target_compile_features(xar_ck3_white_numeric_control_specs_v1_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_white_numeric_control_specs_v1_test PRIVATE NOMINMAX)
  target_compile_options(xar_ck3_white_numeric_control_specs_v1_test PRIVATE $<$<CXX_COMPILER_ID:MSVC>:/UNDEBUG>)
  add_test(NAME xar_ck3_white_numeric_control_specs_v1_test COMMAND xar_ck3_white_numeric_control_specs_v1_test)
endif()

# True monthly NET: real production reader/serializer with fake native bindings.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_war_cash_net_income_test
    src/ck3_12003_war_cash_current_reader.cpp
    src/ck3_12003_war_cash_current_serializer.cpp
    src/ck3_12003_war_cash_net_income_test.cpp)
  target_include_directories(xar_ck3_12003_war_cash_net_income_test PRIVATE include)
  target_compile_features(xar_ck3_12003_war_cash_net_income_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_war_cash_net_income_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_war_cash_net_income_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2)
    target_link_options(xar_ck3_12003_war_cash_net_income_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_war_cash_net_income
    COMMAND xar_ck3_12003_war_cash_net_income_test
      "${CMAKE_BINARY_DIR}/ck3_12003_war_cash_net_income_wire")
  add_test(NAME xar_ck3_12003_war_cash_net_income_registered_mcp
    COMMAND ${Python3_EXECUTABLE} -O
      "${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/run_war_cash_net_income_mcp_fixture.py"
      --projection-root "${CMAKE_CURRENT_SOURCE_DIR}/../.."
      --native-dir "${CMAKE_BINARY_DIR}/ck3_12003_war_cash_net_income_wire"
      --output-dir "${CMAKE_BINARY_DIR}/ck3_12003_war_cash_net_income_registered")
  set_tests_properties(xar_ck3_12003_war_cash_net_income PROPERTIES
    FIXTURES_SETUP war_cash_net_income_wire)
  set_tests_properties(xar_ck3_12003_war_cash_net_income_registered_mcp PROPERTIES
    FIXTURES_REQUIRED war_cash_net_income_wire)
endif()

# Independent next-epoch current-player stress observation. OFF never advertises it.
option(XAR_CK3_ENABLE_CURRENT_ACTOR_STRESS_ADJUSTMENT_PRIVATE_V1
  "Admit exact .3 owner-bound readonly stress aggregate and delta consumer" OFF)
if(XAR_CK3_ENABLE_CURRENT_ACTOR_STRESS_ADJUSTMENT_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/current_actor_stress_adjustment_v1.cpp
    src/current_actor_stress_adjustment_v1_mailbox.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_CURRENT_ACTOR_STRESS_ADJUSTMENT_PRIVATE_V1=1)
  # The exact .3 descriptor belongs to the separately compiled runtime target.
  target_compile_definitions(xar_ck3_12002_runtime PRIVATE
    XAR_CK3_ENABLE_CURRENT_ACTOR_STRESS_ADJUSTMENT_PRIVATE_V1=1)
endif()
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_current_actor_stress_adjustment_v1_test
    tests/current_actor_stress_adjustment_v1_test.cpp
    src/current_actor_stress_adjustment_v1.cpp
    src/current_actor_stress_adjustment_v1_mailbox.cpp
    src/main_thread_query_mailbox_v1.cpp
    src/ck3_12002_query_mailbox.cpp
    src/ck3_12003_abi_profile.cpp)
  target_link_libraries(xar_ck3_current_actor_stress_adjustment_v1_test PRIVATE user32)
  target_include_directories(xar_ck3_current_actor_stress_adjustment_v1_test PRIVATE include)
  target_compile_features(xar_ck3_current_actor_stress_adjustment_v1_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_current_actor_stress_adjustment_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_current_actor_stress_adjustment_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_current_actor_stress_adjustment_v1
    COMMAND xar_ck3_current_actor_stress_adjustment_v1_test)
endif()


option(XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1
  "Admit exact .3 ordinary key/full-recipient context query and single owned send" OFF)
if(XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1)
  target_sources(xar_ck3_bridge PRIVATE
    src/ordinary_interaction_request_v1.cpp
    src/ordinary_character_interaction_v1.cpp
    src/ordinary_interaction_mailbox_v1.cpp)
  target_compile_definitions(xar_ck3_12002_runtime PRIVATE
    XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1=1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1=1)
endif()
if(BUILD_TESTING)
  add_executable(xar_ck3_ordinary_interaction_request_v1_test
    src/ordinary_interaction_request_v1.cpp
    src/ordinary_interaction_request_v1_test.cpp)
  target_include_directories(xar_ck3_ordinary_interaction_request_v1_test PRIVATE include)
  target_compile_features(xar_ck3_ordinary_interaction_request_v1_test PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(xar_ck3_ordinary_interaction_request_v1_test PRIVATE /W4 /WX /permissive-)
  endif()
  add_test(NAME xar_ck3_ordinary_interaction_request_v1
    COMMAND xar_ck3_ordinary_interaction_request_v1_test)
endif()

if(BUILD_TESTING AND WIN32)
  if(XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1)
    target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE
      XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1=1)
  endif()
  if(XAR_CK3_ENABLE_CURRENT_ACTOR_STRESS_ADJUSTMENT_PRIVATE_V1)
    target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE
      XAR_CK3_ENABLE_CURRENT_ACTOR_STRESS_ADJUSTMENT_PRIVATE_V1=1)
  endif()
  add_test(NAME xar_ck3_ordinary_interaction_production_registry_v1
    COMMAND xar_ck3_adapter_registry_test --ordinary-interaction-capabilities-only)
  add_executable(xar_ck3_ordinary_character_interaction_v1_test
    src/ordinary_character_interaction_v1_test.cpp
    src/ordinary_character_interaction_v1.cpp
    src/ordinary_interaction_request_v1.cpp
    src/ck3_12002.cpp
    src/ck3_12002_commands.cpp)
  target_include_directories(xar_ck3_ordinary_character_interaction_v1_test PRIVATE include)
  target_compile_features(xar_ck3_ordinary_character_interaction_v1_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_ordinary_character_interaction_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_ordinary_character_interaction_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_ordinary_character_interaction_v1
    COMMAND xar_ck3_ordinary_character_interaction_v1_test)
  add_executable(xar_ck3_ordinary_interaction_mailbox_v1_test
    tests/ordinary_interaction_mailbox_v1_test.cpp
    src/ordinary_interaction_mailbox_v1.cpp
    src/ordinary_character_interaction_v1.cpp
    src/ordinary_interaction_request_v1.cpp
    src/ck3_12002.cpp
    src/ck3_12002_commands.cpp
    src/main_thread_query_mailbox_v1.cpp
    src/ck3_12002_query_mailbox.cpp
    src/ck3_12003_abi_profile.cpp)
  target_link_libraries(xar_ck3_ordinary_interaction_mailbox_v1_test PRIVATE user32)
  target_include_directories(xar_ck3_ordinary_interaction_mailbox_v1_test PRIVATE include)
  target_compile_features(xar_ck3_ordinary_interaction_mailbox_v1_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_ordinary_interaction_mailbox_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_ordinary_interaction_mailbox_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_ordinary_interaction_mailbox_v1
    COMMAND xar_ck3_ordinary_interaction_mailbox_v1_test)
endif()

# Pure actual-argv regression; no game, UI, pipe or native provider invocation.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_normal_exit_map_launch_arguments_v1_test
    tests/normal_exit_map_launch_arguments_v1_test.cpp
    src/normal_exit_map_source_v1.cpp)
  target_link_libraries(xar_ck3_normal_exit_map_launch_arguments_v1_test PRIVATE bcrypt shell32)
  target_include_directories(xar_ck3_normal_exit_map_launch_arguments_v1_test PRIVATE include)
  target_compile_features(xar_ck3_normal_exit_map_launch_arguments_v1_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_normal_exit_map_launch_arguments_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_normal_exit_map_launch_arguments_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_normal_exit_map_launch_arguments_v1
    COMMAND xar_ck3_normal_exit_map_launch_arguments_v1_test)
endif()

# Pure production request/stage gates; no native receiver or process invocation.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_normal_exit_map_continuation_v1_test
    tests/normal_exit_map_continuation_v1_test.cpp
    src/normal_exit_map_request_v1.cpp)
  target_include_directories(xar_ck3_normal_exit_map_continuation_v1_test PRIVATE include)
  target_compile_features(xar_ck3_normal_exit_map_continuation_v1_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_normal_exit_map_continuation_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_normal_exit_map_continuation_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_normal_exit_map_continuation_v1
    COMMAND xar_ck3_normal_exit_map_continuation_v1_test)
endif()
