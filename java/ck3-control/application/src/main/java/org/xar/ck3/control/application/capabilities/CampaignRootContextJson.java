package org.xar.ck3.control.application.capabilities;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** One strict native campaign-root normalizer, retaining baseline and full material wire variants. */
public final class CampaignRootContextJson {
 private CampaignRootContextJson() { }
 private static final Set<String> FIELDS=Set.of("adjacent_external_province_holder_character_ids","capital_province_id","council","date_raw","direct_landed_vassal_character_ids","government","held_title_partition","immediate_liege_character_id","independent","local_player_id","native_selected_game_rule_token_count","player_character_alive","player_character_id","player_domain_limit","player_domain_size","player_health","player_monthly_gold_income","player_targeting_faction_count","primary_title","primary_title_succession_character_ids","provenance","readiness","related_character_contexts","schema_version","selected_game_rule_tokens","snapshot_revision","status","top_liege_character_id","unavailable_reason");
 private static final Set<String> MATERIAL_FIELDS=Set.of("adjacent_external_province_holder_character_ids","capital_province_id","council","date_raw","direct_landed_vassal_character_ids","government","held_title_partition","immediate_liege_character_id","independent","local_player_id","native_selected_game_rule_token_count","player_character_alive","player_character_id","player_domain_limit","player_domain_size","player_health","player_legitimacy_v1","player_monthly_gold_income","player_targeting_faction_count","primary_title","primary_title_succession_character_ids","provenance","readiness","related_character_contexts","schema_version","selected_game_rule_tokens","snapshot_revision","status","top_liege_character_id","unavailable_reason");
 private static final Set<String> FINANCE_FIELDS=Set.of("adjacent_external_province_holder_character_ids","capital_province_id","council","date_raw","direct_landed_vassal_character_ids","government","held_title_partition","immediate_liege_character_id","independent","local_player_id","native_selected_game_rule_token_count","player_character_alive","player_character_id","player_domain_limit","player_domain_size","player_health","player_max_monthly_gold_maintenance_v1","player_monthly_gold_income","player_targeting_faction_count","primary_title","primary_title_succession_character_ids","provenance","readiness","related_character_contexts","schema_version","selected_game_rule_tokens","snapshot_revision","status","top_liege_character_id","unavailable_reason");
 private static final Set<String> ALL_MATERIAL_FIELDS=Set.of("adjacent_external_province_holder_character_ids","capital_province_id","council","date_raw","direct_landed_vassal_character_ids","government","held_title_partition","immediate_liege_character_id","independent","local_player_id","native_selected_game_rule_token_count","player_character_alive","player_character_id","player_domain_limit","player_domain_size","player_health","player_legitimacy_v1","player_max_monthly_gold_maintenance_v1","player_monthly_gold_income","player_targeting_faction_count","primary_title","primary_title_succession_character_ids","provenance","readiness","related_character_contexts","schema_version","selected_game_rule_tokens","snapshot_revision","status","top_liege_character_id","unavailable_reason");
 private static final Set<String> LEGITIMACY_FIELDS=Set.of("status","unavailable_reason","value");
 private static final Set<String> LEGITIMACY_UNAVAILABLE_REASONS=Set.of("actual4_legitimacy_field_source_unavailable","balance_invalid","balance_unreadable","data_absent","data_pointer_unreadable");
 private static final Set<String> PRIMARY_TITLE_FIELDS=Set.of("tier_key","tier_raw","title_id");
 private static final Set<String> HELD_TITLE_PARTITION_FIELDS=Set.of("capital_province_id","first_heir_character_id","primary","title");
 private static final Set<String> LANDLESS_NOBLE_FAMILY_PARTITION_FIELDS=Set.of("capital_province_id","capital_province_kind","first_heir_character_id","primary","title","title_key");
 private static final Set<String> LEGACY_HELD_TITLE_PARTITION_FIELDS=Set.of("first_heir_character_id","primary","title");
 private static final Set<String> FIXED_POINT_FIELDS=Set.of("raw","scale");
 private static final Set<String> RELATED_CHARACTER_FIELDS=Set.of("capital_province_id","character_id","immediate_liege_character_id","independent","primary_title","relationship_role","top_liege_character_id");
 private static final Set<String> GOVERNMENT_FIELDS=Set.of("flags","key","native_flag_count");
 private static final Set<String> COUNCIL_FIELDS=Set.of("auxiliary_vacancies_complete","coverage_key","owner_character_id","positions","status","unavailable_reason");
 private static final Set<String> COUNCIL_POSITION_FIELDS=Set.of("frozen","incumbent_character_id","position_key","progress","target","task_key","task_type");
 private static final Set<String> COUNCIL_PROVINCE_TARGET_FIELDS=Set.of("kind","province_id");
 private static final Set<String> COUNCIL_CHARACTER_TARGET_FIELDS=Set.of("character_id","kind");
 private static final Set<String> COUNCIL_PROGRESS_FIELDS=Set.of("current","kind","maximum");
 private static final Set<String> CORE_COUNCIL_POSITION_KEYS=Set.of("councillor_chancellor","councillor_court_chaplain","councillor_marshal","councillor_spymaster","councillor_steward");
 private static final Set<String> READINESS_KEYS=Set.of("adjacent_external_province_holders_ready","capital_ready","council_ready","direct_landed_vassals_ready","government_ready","held_title_partition_ready","lieges_ready","player_domain_ready","player_health_ready","player_identity_ready","player_monthly_gold_income_ready","player_targeting_factions_ready","primary_title_ready","primary_title_succession_ready","ready","related_character_contexts_ready","same_frame_ready","selected_game_rule_tokens_ready");
 private static final Set<String> READINESS_FIELDS=Set.of("adjacent_external_province_holders_ready","capital_ready","council_ready","direct_landed_vassals_ready","government_ready","held_title_partition_ready","lieges_ready","player_domain_ready","player_health_ready","player_identity_ready","player_monthly_gold_income_ready","player_targeting_factions_ready","primary_title_ready","primary_title_succession_ready","ready","related_character_contexts_ready","same_frame_ready","selected_game_rule_tokens_ready");
 private static final Set<String> PROVENANCE_FIELDS=Set.of("backend_id","capital_province_rva","character_health_rva","council_active_task_ids_enumerator_rva","council_active_task_storage_slot_rva","council_position_lookup_rva","council_value_progress_current_rva","council_value_progress_maximum_rva","domain_limit_rva","domain_size_rva","executable_sha256","game_version","government_rva","has_targeting_faction_trigger_rva","held_title_ids_offset","immediate_liege_rva","monthly_gold_income_rva","primary_title_rva","province_holder_character_id_rva","selected_game_rule_service_slot_rva","title_province_rva","top_liege_rva");
 private static final Set<String> BASELINE_12002_FIELDS=Set.of("capital_province_id","date_raw","government","immediate_liege_character_id","independent","local_player_id","native_selected_game_rule_token_count","player_character_alive","player_character_id","primary_title","provenance","readiness","schema_version","selected_game_rule_tokens","snapshot_revision","status","top_liege_character_id","unavailable_reason");
 private static final Set<String> BASELINE_12002_READINESS=Set.of("capital_ready","government_ready","lieges_ready","player_identity_ready","primary_title_ready","ready","same_frame_ready","selected_game_rule_tokens_ready");
 private static final Set<String> UNAVAILABLE_REASONS=Set.of("adjacent_external_province_holders_unavailable","capital_unavailable","council_unavailable","direct_landed_vassals_unavailable","government_flags_unavailable","held_title_partition_unavailable","internal_error","lieges_unavailable","map_not_ready","player_character_generation_mismatch","player_domain_unavailable","player_health_unavailable","player_identity_unavailable","player_monthly_gold_income_unavailable","player_targeting_factions_unavailable","primary_title_succession_unavailable","primary_title_unavailable","related_character_contexts_unavailable","requires_application_main","requires_paused","selected_game_rule_tokens_unavailable","state_changed","unsupported_build");
 private static final Set<String> UNAVAILABLE_NULL_FIELDS=Set.of("capital_province_id","council","government","immediate_liege_character_id","independent","local_player_id","player_character_alive","player_character_id","player_domain_limit","player_domain_size","player_health","player_legitimacy_v1","player_max_monthly_gold_maintenance_v1","player_monthly_gold_income","player_monthly_piety_v1","player_targeting_faction_count","primary_title","top_liege_character_id");
 private static final Map<String,Obj> BASELINE_PROVENANCE_BY_BUILD=Map.ofEntries(
  Map.entry("1.20.0.2",strings("game_version","1.20.0.2","executable_sha256","AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D","backend_id","ck3-1.20.0.2-native-campaign-root-context-v1","primary_title_rva","0x289DA30","capital_province_rva","0x28B1CD0","immediate_liege_rva","0x28BFC70","top_liege_rva","0x28BFDA0","government_rva","0x28C2E10","selected_game_rule_service_slot_rva","0x5CB3D78")),
  Map.entry("1.20.0.3",strings("game_version","1.20.0.3","executable_sha256","94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6","backend_id","ck3-1.20.0.3-native-campaign-root-context-v1","primary_title_rva","0x289DA30","capital_province_rva","0x28B1CD0","immediate_liege_rva","0x28BFC70","top_liege_rva","0x28BFDA0","government_rva","0x28C2E10","selected_game_rule_service_slot_rva","0x5CB3D78")),
  Map.entry("1.20.0.4",strings("game_version","1.20.0.4","executable_sha256","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518","backend_id","ck3-1.20.0.4-native-campaign-root-context-v1","primary_title_rva","0x289DA10","capital_province_rva","0x28B1CB0","immediate_liege_rva","0x28BFC50","top_liege_rva","0x28BFD80","government_rva","0x28C2DF0","selected_game_rule_service_slot_rva","0x5CB3D78")));
 private static final Map<String,Obj> PROVENANCE_BY_BUILD=Map.ofEntries(
  Map.entry("1.19.0.6",strings("game_version","1.19.0.6","executable_sha256","2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86","backend_id","ck3-1.19.0.6-native-campaign-root-context-v1","monthly_gold_income_rva","0x28DBE90","character_health_rva","0x2619AD0","domain_size_rva","0x260BA50","domain_limit_rva","0x260BA20","has_targeting_faction_trigger_rva","0x283FAE0","council_position_lookup_rva","0x23F7800","council_active_task_ids_enumerator_rva","0x2666CD0","council_active_task_storage_slot_rva","0x570C778","council_value_progress_current_rva","0x2D650A0","council_value_progress_maximum_rva","0x2D65390","primary_title_rva","0x25F3350","held_title_ids_offset","0x1E0","title_province_rva","0x20B6B20","capital_province_rva","0x2606760","immediate_liege_rva","0x2613480","top_liege_rva","0x2613600","government_rva","0x26165B0","province_holder_character_id_rva","0x220C3F0","selected_game_rule_service_slot_rva","0x5754B48")),
  Map.entry("1.20.0.2",strings("game_version","1.20.0.2","executable_sha256","AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D","backend_id","ck3-1.20.0.2-native-campaign-root-context-v1","primary_title_rva","0x289DA30","capital_province_rva","0x28B1CD0","immediate_liege_rva","0x28BFC70","top_liege_rva","0x28BFDA0","government_rva","0x28C2E10","selected_game_rule_service_slot_rva","0x5CB3D78","monthly_gold_income_rva","0x2BCA960","character_health_rva","0x28C6500","domain_size_rva","0x28B7200","domain_limit_rva","0x28B71D0","has_targeting_faction_trigger_rva","0x2B250D0","council_position_lookup_rva","0x2684F00","council_active_task_ids_enumerator_rva","0x2916CE0","council_active_task_storage_slot_rva","0x5D1DEA0","council_value_progress_current_rva","0x31AB520","council_value_progress_maximum_rva","0x31AB840","held_title_ids_offset","0x1E0","title_province_rva","0x230F900","province_holder_character_id_rva","0x247D030")),
  Map.entry("1.20.0.3",strings("game_version","1.20.0.3","executable_sha256","94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6","backend_id","ck3-1.20.0.3-native-campaign-root-context-v1","primary_title_rva","0x289DA30","capital_province_rva","0x28B1CD0","immediate_liege_rva","0x28BFC70","top_liege_rva","0x28BFDA0","government_rva","0x28C2E10","selected_game_rule_service_slot_rva","0x5CB3D78","monthly_gold_income_rva","0x2BCA960","character_health_rva","0x28C6500","domain_size_rva","0x28B7200","domain_limit_rva","0x28B71D0","has_targeting_faction_trigger_rva","0x2B250D0","council_position_lookup_rva","0x2684F00","council_active_task_ids_enumerator_rva","0x2916CE0","council_active_task_storage_slot_rva","0x5D1DEA0","council_value_progress_current_rva","0x31AB520","council_value_progress_maximum_rva","0x31AB840","held_title_ids_offset","0x1E0","title_province_rva","0x230F900","province_holder_character_id_rva","0x247D030")),
  Map.entry("1.20.0.4",strings("game_version","1.20.0.4","executable_sha256","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518","backend_id","ck3-1.20.0.4-native-campaign-root-context-v1","primary_title_rva","0x289DA10","capital_province_rva","0x28B1CB0","immediate_liege_rva","0x28BFC50","top_liege_rva","0x28BFD80","government_rva","0x28C2DF0","selected_game_rule_service_slot_rva","0x5CB3D78","monthly_gold_income_rva","0x2BCA940","character_health_rva","0x28C64E0","domain_size_rva","0x28B71E0","domain_limit_rva","0x28B71B0","has_targeting_faction_trigger_rva","0x2B250B0","council_position_lookup_rva","0x2684EE0","council_active_task_ids_enumerator_rva","0x2916CC0","council_active_task_storage_slot_rva","0x5D1DEA0","council_value_progress_current_rva","0x31AB500","council_value_progress_maximum_rva","0x31AB820","held_title_ids_offset","0x1E0","title_province_rva","0x230F8E0","province_holder_character_id_rva","0x247D010")));
 private static final String[] TIERS={"","barony","county","duchy","kingdom","empire","hegemony"};
 private static final BigInteger U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
 /** Validate the exact native reply before any consumer may store its normalized root. */
 public static Obj normalizeNativeResult(Obj original,BigInteger expectedDateRaw,BigInteger expectedNativeRevision) {
  exact(original,Set.of("step","accepted","status","query_sequence","snapshot_revision","campaign_root_context","backend_id"),"campaign-root native result");
  require(text(original.get("step"),"step").equals("query-campaign-root-context-v1")&&bool(original.get("accepted"),"accepted")
     &&range(original.get("snapshot_revision"),BigInteger.ONE,U64,"snapshot_revision").equals(expectedNativeRevision),"campaign-root native envelope malformed");
  range(original.get("query_sequence"),BigInteger.ONE,U64,"query_sequence");Obj normalized=normalize(original.get("campaign_root_context"),expectedDateRaw,expectedNativeRevision);
  require(Objects.equals(original.get("status"),normalized.get("status")),"native envelope and normalized root status disagree");
  return original.with("campaign_root_context",normalized);
 }
 /** Normalized values alone confer no custody or execution eligibility. The caller retains the actual read and guards. */
 public static Obj normalize(Value original,BigInteger expectedDateRaw,BigInteger expectedNativeRevision) {
  Obj input=object(original,"campaign_root_context");
  if(input.members().containsKey("player_heir_candidate_v1")) {
   Map<String,Value> base=new LinkedHashMap<>(input.members());Value component=base.remove("player_heir_candidate_v1");
   Obj normalized=normalize(new Obj(base),expectedDateRaw,expectedNativeRevision);Map<String,Value> output=new LinkedHashMap<>(normalized.members());
   var heir=org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.normalizeOptionalComponent(
      org.xar.ck3.control.contracts.StrictJson.parse(encode(component),1_048_576),org.xar.ck3.control.contracts.StrictJson.parse(encode(normalized),1_048_576));
   output.put("player_heir_candidate_v1",heir.isNull()?Nil.INSTANCE:org.xar.ck3.control.application.driver.DriverJson.object(org.xar.ck3.control.contracts.StrictJson.canonical(heir,1_048_576),1_048_576));return new Obj(output);
  }
  range(expectedDateRaw,Integer.MIN_VALUE,Integer.MAX_VALUE,"expected_date_raw");range(expectedNativeRevision,BigInteger.ONE,U64,"expected_native_revision");
  boolean baseline=input.members().keySet().equals(BASELINE_12002_FIELDS);
  if(!baseline) {
   Set<String> actual=new HashSet<>(input.members().keySet());actual.remove("player_monthly_piety_v1");
   require(actual.equals(FIELDS)||actual.equals(MATERIAL_FIELDS)||actual.equals(FINANCE_FIELDS)||actual.equals(ALL_MATERIAL_FIELDS),"campaign_root_context has invalid v1 fields");
  }
  require(integer(input.get("schema_version"),"schema_version").equals(BigInteger.ONE),"campaign_root_context schema_version must be integer one");
  String status=text(input.get("status"),"status");require(Set.of("available","unavailable").contains(status),"campaign root status invalid");boolean available=status.equals("available");
  require(range(input.get("snapshot_revision"),BigInteger.ONE,U64,"snapshot_revision").equals(expectedNativeRevision)
    && range(input.get("date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE,"date_raw").equals(expectedDateRaw),"campaign root snapshot/date binding changed");
  Obj provenance=provenance(input.get("provenance"),baseline);String build=text(provenance.get("game_version"),"game_version");
  Obj readiness=exact(input.get("readiness"),baseline?BASELINE_12002_READINESS:READINESS_FIELDS,"readiness");
  for(String key:readiness.members().keySet()) {
   boolean value=bool(readiness.get(key),key);
   if(!available||baseline)require(value==available,"campaign readiness disagrees with status: "+key);
   else if(!Set.of("council_ready","selected_game_rule_tokens_ready","ready").contains(key))require(value,"available campaign lacks required readiness: "+key);
  }
  if(available&&!baseline)require(bool(readiness.get("ready"),"ready")==bool(readiness.get("selected_game_rule_tokens_ready"),"selected_game_rule_tokens_ready"),"root/rule readiness disagree");
  List<String> tokens=lexical(input.get("selected_game_rule_tokens"),"selected_game_rule_tokens");
  require(range(input.get("native_selected_game_rule_token_count"),0,Integer.MAX_VALUE,"token_count").intValueExact()==tokens.size(),"native token count differs from full vector");
  if(available&&!bool(readiness.get("selected_game_rule_tokens_ready"),"selected_game_rule_tokens_ready"))require(tokens.isEmpty(),"unready selected tokens must be empty");
  Map<String,Value> out=new LinkedHashMap<>(input.members());out.put("provenance",provenance);
  if(!available) {
   require(UNAVAILABLE_REASONS.contains(text(input.get("unavailable_reason"),"unavailable_reason"))&&tokens.isEmpty(),"unavailable root reason/tokens invalid");
   Set<String> nulls=new HashSet<>(baseline?BASELINE_12002_FIELDS:UNAVAILABLE_NULL_FIELDS);
   if(baseline)nulls.removeAll(Set.of("schema_version","status","snapshot_revision","date_raw","selected_game_rule_tokens","native_selected_game_rule_token_count","readiness","unavailable_reason","provenance"));
   for(String key:nulls)if(input.members().containsKey(key))require(input.get(key)==Nil.INSTANCE,"unavailable root invented "+key);
   if(!baseline)for(String key:List.of("direct_landed_vassal_character_ids","adjacent_external_province_holder_character_ids","related_character_contexts","primary_title_succession_character_ids","held_title_partition"))require(array(input.get(key),key).isEmpty(),"unavailable root invented "+key);
   return new Obj(out);
  }
  require(input.get("unavailable_reason")==Nil.INSTANCE,"available root has unavailable reason");
  range(input.get("local_player_id"),0,Integer.MAX_VALUE,"local_player_id");BigInteger player=positive(input.get("player_character_id"),"player_character_id");
  bool(input.get("player_character_alive"),"player_character_alive");Obj primary=input.get("primary_title")==Nil.INSTANCE?null:title(input.get("primary_title"),1,"primary_title");
  optionalPositive(input.get("capital_province_id"),"capital_province_id");BigInteger immediate=optionalPositive(input.get("immediate_liege_character_id"),"immediate_liege_character_id");
  BigInteger top=positive(input.get("top_liege_character_id"),"top_liege_character_id");boolean independent=bool(input.get("independent"),"independent");
  lieges(player,immediate,top,independent,"root");Obj government=government(input.get("government"));
  if(baseline)return new Obj(out);
  fixed(input.get("player_monthly_gold_income"),"player_monthly_gold_income");fixed(input.get("player_health"),"player_health");
  for(String key:List.of("player_legitimacy_v1","player_max_monthly_gold_maintenance_v1","player_monthly_piety_v1"))if(input.members().containsKey(key))optionalObservation(input.get(key),key);
  range(input.get("player_domain_size"),0,Integer.MAX_VALUE,"player_domain_size");positive(input.get("player_domain_limit"),"player_domain_limit");range(input.get("player_targeting_faction_count"),0,Integer.MAX_VALUE,"player_targeting_faction_count");
  List<BigInteger> succession=identities(input.get("primary_title_succession_character_ids"),false,"primary_title_succession_character_ids");
  require(!succession.contains(player)&&(primary!=null||succession.isEmpty()),"root succession contains holder or landless succession");
  out.put("held_title_partition",partition(input.get("held_title_partition"),primary,succession.isEmpty()?null:succession.getFirst(),player,Set.of("1.20.0.3","1.20.0.4").contains(build)));
  List<BigInteger> direct=identities(input.get("direct_landed_vassal_character_ids"),true,"direct_vassals"),adjacent=identities(input.get("adjacent_external_province_holder_character_ids"),true,"adjacent_holders");
  require(!direct.contains(player)&&!adjacent.contains(player)&&Collections.disjoint(direct,adjacent),"root relationship vectors overlap or contain player");
  related(input.get("related_character_contexts"),player,top,direct,adjacent);
  Set<String> flags=government==null?Set.of():new HashSet<>(lexical(government.get("flags"),"government.flags"));
  boolean admitted=primary!=null&&government!=null&&Collections.disjoint(flags,Set.of("government_is_landless_adventurer","government_is_nomadic","government_is_celestial"));
  Obj council=council(input.get("council"),player,admitted,build);out.put("council",council);
  require(bool(readiness.get("council_ready"),"council_ready")==text(council.get("status"),"council.status").equals("available"),"root/council readiness disagree");return new Obj(out);
 }
 private static Obj provenance(Value original,boolean baseline) {
  Obj value=object(original,"provenance");Map<String,Obj> byBuild=baseline?BASELINE_PROVENANCE_BY_BUILD:PROVENANCE_BY_BUILD;
  String version=text(value.get("game_version"),"game_version");Obj expected=byBuild.get(version);
  require(expected!=null&&value.equals(expected),"campaign root provenance does not match frozen exact build");return expected;
 }
 private static Obj government(Value original) {
  if(original==Nil.INSTANCE)return null;Obj value=exact(original,GOVERNMENT_FIELDS,"government");stable(value.get("key"),"government.key");
  List<String> flags=lexical(value.get("flags"),"government.flags");require(range(value.get("native_flag_count"),0,Integer.MAX_VALUE,"native_flag_count").intValueExact()==flags.size(),"government flag count differs from full span");return value;
 }
 private static Obj title(Value original,int minimum,String name) {
  Obj value=exact(original,PRIMARY_TITLE_FIELDS,name);positive(value.get("title_id"),name+".title_id");int tier=range(value.get("tier_raw"),minimum,6,name+".tier_raw").intValueExact();
  require(text(value.get("tier_key"),name+".tier_key").equals(TIERS[tier]),"title tier pair invalid");return value;
 }
 private static Arr partition(Value original,Obj primary,BigInteger firstHeir,BigInteger player,boolean allowFamily) {
  List<Value> result=new ArrayList<>();BigInteger previous=BigInteger.valueOf(-1);int marked=0;
  for(Value item:array(original,"held_title_partition")) {
   Obj row=object(item,"held_title_partition.row");Set<String> keys=row.members().keySet();boolean family=keys.equals(LANDLESS_NOBLE_FAMILY_PARTITION_FIELDS);
   require(family||keys.equals(HELD_TITLE_PARTITION_FIELDS)||keys.equals(LEGACY_HELD_TITLE_PARTITION_FIELDS),"unsupported held title row variant");
   Obj t=title(row.get("title"),2,"held_title_partition.title");BigInteger id=positive(t.get("title_id"),"held.title_id");int tier=integer(t.get("tier_raw"),"tier_raw").intValueExact();
   require(id.compareTo(previous)>0,"held title partition must be sorted and unique");previous=id;
   BigInteger heir=optionalPositive(row.get("first_heir_character_id"),"first_heir_character_id");
   // The legacy row really omits capital; only normalization adds explicit null.
   Value capital=row.members().containsKey("capital_province_id")?row.get("capital_province_id"):Nil.INSTANCE;BigInteger province=optionalPositive(capital,"capital_province_id");
   if(family)require(allowFamily&&tier==2&&province==null&&text(row.get("capital_province_kind"),"capital_province_kind").equals("landless_noble_family_no_province")
      &&text(row.get("title_key"),"title_key").matches("c_[A-Za-z0-9][A-Za-z0-9_]{0,1021}"),"invalid landless noble family row");
   else if(row.members().containsKey("capital_province_id"))require((tier==2)==(province!=null),"only county partition has a province");
   require(!player.equals(heir),"held title heir equals its holder");boolean isPrimary=bool(row.get("primary"),"primary");
   if(isPrimary){marked++;require(Objects.equals(t,primary)&&Objects.equals(heir,firstHeir),"partition primary title/heir differs from root");}
   Map<String,Value> normalized=new LinkedHashMap<>(row.members());normalized.put("capital_province_id",capital);result.add(new Obj(normalized));
  }
  if(primary==null||integer(primary.get("tier_raw"),"tier_raw").equals(BigInteger.ONE))require(result.isEmpty(),"landless/barony root exposes realm partition");
  else require(marked==1,"held title partition must mark primary once");return new Arr(result);
 }
 private static void related(Value original,BigInteger player,BigInteger playerTop,List<BigInteger> direct,List<BigInteger> adjacent) {
  SortedSet<BigInteger> expected=new TreeSet<>(direct);expected.addAll(adjacent);List<BigInteger> observed=new ArrayList<>();
  for(Value item:array(original,"related_character_contexts")) {
   Obj row=exact(item,RELATED_CHARACTER_FIELDS,"related_character_context");BigInteger id=positive(row.get("character_id"),"related.character_id");observed.add(id);
   String role=text(row.get("relationship_role"),"relationship_role");title(row.get("primary_title"),1,"related.primary_title");optionalPositive(row.get("capital_province_id"),"capital_province_id");
   BigInteger immediate=optionalPositive(row.get("immediate_liege_character_id"),"immediate_liege_character_id"),top=positive(row.get("top_liege_character_id"),"top_liege_character_id");
   lieges(id,immediate,top,bool(row.get("independent"),"independent"),"related");
   if(role.equals("direct_landed_vassal"))require(direct.contains(id)&&player.equals(immediate)&&playerTop.equals(top),"related direct-vassal proof inconsistent");
   else require(role.equals("adjacent_external_province_holder")&&adjacent.contains(id)&&!player.equals(immediate),"related adjacent-holder proof inconsistent");
  }
  require(observed.equals(new ArrayList<>(expected)),"related contexts must exactly cover both vectors once in CharacterID order");
 }
 private static void lieges(BigInteger actor,BigInteger immediate,BigInteger top,boolean independent,String name) {
  require(independent==(immediate==null)&&!actor.equals(immediate)&&(independent?top.equals(actor):!top.equals(actor)),name+" liege identities disagree");
 }
 private static Obj council(Value original,BigInteger player,boolean admitted,String build) {
  Obj value=exact(original,COUNCIL_FIELDS,"council");require(text(value.get("coverage_key"),"coverage_key").equals("standard_landed_non_nomadic_core_v1")
     &&positive(value.get("owner_character_id"),"owner_character_id").equals(player)&&!bool(value.get("auxiliary_vacancies_complete"),"auxiliary_vacancies_complete"),"council coverage/owner invalid");
  String status=text(value.get("status"),"council.status");require(Set.of("available","unavailable").contains(status),"council status invalid");
  boolean available=status.equals("available");Value reason=value.get("unavailable_reason");
  boolean actual4Unavailable=!available&&build.equals("1.20.0.4")&&reason.equals(new Text("actual4_council_position_key_source_unavailable"));
  require(available==admitted||actual4Unavailable,"council status disagrees with coverage scope");List<Value> positions=array(value.get("positions"),"council.positions");
  if(!available){require(positions.isEmpty()&&(actual4Unavailable||reason.equals(new Text("outside_standard_landed_non_nomadic_core_scope"))),"unavailable council invented positions/reason");return value;}
  require(reason==Nil.INSTANCE,"available council has unavailable reason");List<String> keys=new ArrayList<>();
  for(Value item:positions) {
   Obj row=object(item,"council.position");Set<String> fields=new HashSet<>(COUNCIL_POSITION_FIELDS);if(row.members().containsKey("task_owner_monthly_piety_v1"))fields.add("task_owner_monthly_piety_v1");exact(row,fields,"council.position");
   if(row.members().containsKey("task_owner_monthly_piety_v1"))optionalObservation(row.get("task_owner_monthly_piety_v1"),"task_owner_monthly_piety_v1");
   keys.add(stable(row.get("position_key"),"position_key"));BigInteger incumbent=optionalPositive(row.get("incumbent_character_id"),"incumbent_character_id");
   if(incumbent==null){for(String key:List.of("task_key","task_type","target","frozen","progress"))require(row.get(key)==Nil.INSTANCE,"vacant council position invented active task");continue;}
   stable(row.get("task_key"),"task_key");String type=text(row.get("task_type"),"task_type");bool(row.get("frozen"),"frozen");progress(row.get("progress"));
   if(type.equals("general"))require(row.get("target")==Nil.INSTANCE,"general council task invented target");
   else {boolean county=type.equals("county");require(county||type.equals("court"),"invalid council task_type");String id=county?"province_id":"character_id";
    Obj target=exact(row.get("target"),Set.of("kind",id),"target");require(text(target.get("kind"),"kind").equals(county?"province":"character"),"council task target kind invalid");positive(target.get(id),id);}
  }
  List<String> sorted=new ArrayList<>(keys);sorted.sort(CampaignRootContextJson::compareUtf8);
  require(keys.equals(sorted)&&new HashSet<>(keys).size()==keys.size()&&keys.containsAll(CORE_COUNCIL_POSITION_KEYS),"council positions must be sorted, unique and cover core slots");return value;
 }
 private static void progress(Value original) {
  Obj value=exact(original,COUNCIL_PROGRESS_FIELDS,"progress");String kind=text(value.get("kind"),"kind");
  if(kind.equals("infinite")){require(value.get("current")==Nil.INSTANCE&&value.get("maximum")==Nil.INSTANCE,"infinite progress invented values");return;}
  require(kind.equals("percentage")||kind.equals("value"),"progress kind invalid");BigInteger current=fixed(value.get("current"),"progress.current"),maximum=fixed(value.get("maximum"),"progress.maximum");
  require(current.signum()>=0&&maximum.signum()>0&&current.compareTo(maximum)<=0&&(!kind.equals("percentage")||maximum.equals(BigInteger.valueOf(10000000))),"bounded progress range invalid");
 }
 private static void optionalObservation(Value original,String name) {
  Obj value=exact(original,LEGITIMACY_FIELDS,name);String status=text(value.get("status"),name+".status");
  if(status.equals("available")){BigInteger amount=fixed(value.get("value"),name+".value");require(value.get("unavailable_reason")==Nil.INSTANCE,"available observation has unavailable reason");
   if(name.equals("player_legitimacy_v1")||name.equals("player_max_monthly_gold_maintenance_v1"))require(amount.signum()>=0,"available amount is negative");return;}
  require(status.equals("unavailable")&&value.get("value")==Nil.INSTANCE,"unavailable observation invented balance");String reason=text(value.get("unavailable_reason"),"unavailable_reason");
  Set<String> reasons=switch(name){case "player_legitimacy_v1" -> LEGITIMACY_UNAVAILABLE_REASONS;case "player_max_monthly_gold_maintenance_v1" -> Set.of("getter_unavailable","getter_failed","amount_invalid");case "player_monthly_piety_v1" -> Set.of("monthly_piety_unavailable");case "task_owner_monthly_piety_v1" -> Set.of("task_owner_monthly_piety_unavailable");default -> throw new IllegalArgumentException("unknown material field");};
  require(reasons.contains(reason),"unavailable optional observation reason invalid");
 }
 private static BigInteger fixed(Value original,String name) {
  Obj value=exact(original,FIXED_POINT_FIELDS,name);BigInteger raw=range(value.get("raw"),BigInteger.ONE.shiftLeft(63).negate(),BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE),name+".raw");
  require(integer(value.get("scale"),name+".scale").equals(BigInteger.valueOf(100000)),"fixed-point scale must be integer 100000");return raw;
 }
 private static List<BigInteger> identities(Value original,boolean sorted,String name) {
  List<BigInteger> values=new ArrayList<>();for(Value item:array(original,name))values.add(positive(item,name));
  require(new HashSet<>(values).size()==values.size(),"duplicate identity: "+name);if(sorted){List<BigInteger> ordered=new ArrayList<>(values);Collections.sort(ordered);require(values.equals(ordered),"identity vector not sorted: "+name);}return values;
 }
 private static List<String> lexical(Value original,String name) {
  List<String> values=new ArrayList<>();for(Value item:array(original,name))values.add(stable(item,name));
  List<String> ordered=new ArrayList<>(values);ordered.sort(CampaignRootContextJson::compareUtf8);require(values.equals(ordered),"native keys must use UTF-8 byte order: "+name);return values;
 }
 private static String stable(Value original,String name) {
  String value=text(original,name);require(!value.isEmpty()&&value.codePoints().noneMatch(c->c<32)&&value.getBytes(StandardCharsets.UTF_8).length<=1024,"invalid stable native key: "+name);
  for(int i=0;i<value.length();i++){char c=value.charAt(i);if(Character.isHighSurrogate(c)){require(i+1<value.length()&&Character.isLowSurrogate(value.charAt(++i)),"invalid UTF-8 native key");}else require(!Character.isLowSurrogate(c),"invalid UTF-8 native key");}return value;
 }
 private static int compareUtf8(String a,String b){return Arrays.compareUnsigned(a.getBytes(StandardCharsets.UTF_8),b.getBytes(StandardCharsets.UTF_8));}
 private static BigInteger positive(Value value,String name){return range(value,1,Integer.MAX_VALUE,name);}
 private static BigInteger optionalPositive(Value value,String name){return value==Nil.INSTANCE?null:positive(value,name);}
 private static BigInteger range(Value value,long min,long max,String name){return range(integer(value,name),BigInteger.valueOf(min),BigInteger.valueOf(max),name);}
 private static BigInteger range(BigInteger value,long min,long max,String name){return range(value,BigInteger.valueOf(min),BigInteger.valueOf(max),name);}
 private static BigInteger range(Value value,BigInteger min,BigInteger max,String name){return range(integer(value,name),min,max,name);}
 private static BigInteger range(BigInteger value,BigInteger min,BigInteger max,String name){require(value!=null&&value.compareTo(min)>=0&&value.compareTo(max)<=0,"integer outside native range: "+name);return value;}
 private static Obj exact(Value value,Set<String> fields,String name){Obj row=object(value,name);require(row.members().keySet().equals(fields),"exact native fields required: "+name);return row;}
 private static Obj strings(String... pairs){Map<String,Value> values=new LinkedHashMap<>();for(int i=0;i<pairs.length;i+=2)values.put(pairs[i],new Text(pairs[i+1]));return new Obj(values);}
}
