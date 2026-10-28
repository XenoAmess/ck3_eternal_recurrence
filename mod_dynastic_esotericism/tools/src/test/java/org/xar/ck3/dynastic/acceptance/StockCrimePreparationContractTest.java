package org.xar.ck3.dynastic.acceptance;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.Clausewitz.Block;
import org.xar.ck3.save.Clausewitz.Entry;

/** Producer-to-contract regression; no CK3 runtime qualification. */
final class StockCrimePreparationContractTest {
 @TempDir Path temporary;
 private static Path repository() {
  return Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize().getParent();
 }
 @Test void actualProducerSeparatesReturnedMembershipFromCrime() throws IOException {
  Path fixture=FixtureEmitter.emit(repository(),temporary.resolve("actual"),"authored-machine").fixture();
  verify(Files.readString(fixture.resolve("common/decisions/des_acceptance_extended_decisions.txt"),StandardCharsets.UTF_8),
         Files.readString(fixture.resolve("events/des_acceptance_extended_events.txt"),StandardCharsets.UTF_8));
 }
 @Test void rejectsSameTickReturnMissingDayAndMissingAdoptionGuard() throws IOException {
  Path f=FixtureEmitter.emit(repository(),temporary.resolve("mutations"),"authored-machine").fixture();
  String d=Files.readString(f.resolve("common/decisions/des_acceptance_extended_decisions.txt"),StandardCharsets.UTF_8);
  String e=Files.readString(f.resolve("events/des_acceptance_extended_events.txt"),StandardCharsets.UTF_8);
  rejected(d,d.replace("subtract = 1","subtract = 0"),e,e);
  rejected(d,d.replace("id = des_acceptance_extended.18 days = 1","id = des_acceptance_extended.18 days = 0"),e,e);
  rejected(d,d.replace("var:des_adopted_bound_rite = scope:des_test_primary","always = yes"),e,e);
  rejected(d,d.replace("scope:des_test_target = { set_character_rite = scope:des_test_source_rite }",
   "scope:des_test_target = { set_character_rite = scope:des_test_primary set_character_rite = scope:des_test_source_rite }"),e,e);
  rejected(d,d,e,e.replace("delayed = yes","delayed = no"));
  rejected(d,d,e,e.replace("subtract = 1","subtract = 0"));
  rejected(d,d.replace("NOT = { has_character_flag = des_test_stock_crime_prepare_started }",""),e,e);
  rejected(d,d.replace("dynasty = scope:des_test_dynasty","dynasty = scope:des_test_second_dynasty"),e,e);
  rejected(d,d.replace("house = scope:des_test_primary.var:des_join_house","house = root.house"),e,e);
 }
 private static void rejected(String d,String changedD,String e,String changedE) {
  assertTrue(!d.equals(changedD)||!e.equals(changedE),"mutation must change emitted producer output");
  assertThrows(AssertionError.class,()->verify(changedD,changedE));
 }
 private static Block hidden(Block root,String key) {return root.block(key).block("effect").block("hidden_effect");}
 private static Stream<Entry> walk(Block b) {
  return b.entries().stream().flatMap(x->Stream.concat(Stream.of(x),x.value() instanceof Block child?walk(child):Stream.empty()));
 }
 private static void atom(Block b,String key,String value) {assertEquals(value,b.atom(key,null),key);}
 private static boolean notFlag(Block b,String flag) {
  return b.named("NOT").stream().anyMatch(x->x.value() instanceof Block n&&flag.equals(n.atom("has_character_flag",null)));
 }
 private static void fixtureOnly(Block b) {
  assertTrue(walk(b).noneMatch(x->List.of("set_house","set_dynasty","create_dynasty","add_trait","remove_trait","des_sync_character_effect","des_sync_rite_effect","remove_character_flag").contains(x.key())));
  walk(b).filter(x->x.key().equals("set_variable")).forEach(x->assertTrue(assertInstanceOf(Block.class,x.value()).atom("name","").startsWith("des_test_")));
 }
 private static void guard(Block g) {
  Entry date=g.named("var:des_test_stock_crime_return_input_date").getFirst();
  assertEquals("<=",date.operator());
  Block rhs=assertInstanceOf(Block.class,date.value());
  atom(rhs,"value","current_date");atom(rhs,"subtract","1");
  Block target=g.block("scope:des_test_target");
  atom(target,"is_alive","yes");atom(target,"rite","scope:des_test_primary");
  atom(target,"dynasty","scope:des_test_dynasty");
  atom(target,"house","scope:des_test_primary.var:des_join_house");
  atom(target,"var:des_adopted_bound_rite","scope:des_test_primary");
  assertTrue(target.named("NOT").stream().anyMatch(x->x.value() instanceof Block n&&"yes".equals(n.atom("des_is_apostate_trigger",null))));
 }
 private static void verify(String ds,String es) {
  Block d=Clausewitz.parse(ds),e=Clausewitz.parse(es);
  Block p=hidden(d,"des_acceptance_stock_crime_prepare_decision");
  atom(p,"add_character_flag","des_test_stock_crime_prepare_started");
  assertTrue(notFlag(d.block("des_acceptance_stock_crime_prepare_decision").block("is_shown"),"des_test_stock_crime_prepare_started"));
  fixtureOnly(p);
  assertTrue(p.entries().indexOf(p.named("add_character_flag").getFirst())<p.entries().indexOf(p.named("if").getFirst()));
  Block input=p.block("if");
  atom(input.block("scope:des_test_target"),"set_character_rite","scope:des_test_primary");
  atom(input.block("trigger_event"),"id","des_acceptance_extended.18");
  atom(input.block("trigger_event"),"days","1");
  assertEquals(0,walk(p).filter(x->x.key().equals("add_opinion")).count());
  atom(e.block("des_acceptance_extended.18").block("immediate").block("trigger_event"),"id","des_acceptance_extended.19");
  atom(e.block("des_acceptance_extended.18").block("immediate").block("trigger_event"),"delayed","yes");
  Block ready=e.block("des_acceptance_extended.19").block("immediate").block("if");
  guard(ready.block("limit"));
  atom(ready,"add_character_flag","des_test_stock_crime_primary_ready");
  atom(ready.block("set_variable"),"name","des_test_stock_crime_ready_readback_date");
  atom(ready.block("set_variable"),"value","current_date");
  fixtureOnly(ready);
  assertEquals(0,walk(ready).filter(x->List.of("add_opinion","set_character_rite").contains(x.key())).count());
  Block crime=hidden(d,"des_acceptance_stock_crime_decision");
  atom(crime,"add_character_flag","des_test_stock_crime_started");
  Block shown=d.block("des_acceptance_stock_crime_decision").block("is_shown");
  assertTrue(notFlag(shown,"des_test_stock_crime_started"));
  atom(shown,"has_character_flag","des_test_stock_crime_primary_ready");
  Block applied=crime.block("if");guard(applied.block("limit"));
  assertTrue(crime.entries().indexOf(crime.named("add_character_flag").getFirst())<crime.entries().indexOf(crime.named("if").getFirst()));
  fixtureOnly(crime);
  assertEquals(1,walk(applied).filter(x->x.key().equals("set_character_rite")).count());
  atom(applied.block("scope:des_test_target"),"set_character_rite","scope:des_test_source_rite");
  atom(applied.block("trigger_event"),"id","des_acceptance_extended.20");
  atom(applied.block("trigger_event"),"days","1");
  assertTrue(walk(p).noneMatch(x->List.of("set_house","add_trait","des_sync_character_effect").contains(x.key())));
  Block six=e.block("des_acceptance_extended.20").block("immediate").block("if").block("limit");
  assertEquals(6,six.entries().size());
  assertEquals(2,six.named("has_opinion_modifier").size());
  atom(six.block("scope:des_test_target"),"des_is_apostate_trigger","yes");
  Set<String> modifiers=six.named("has_opinion_modifier").stream().map(x->{
   Block op=assertInstanceOf(Block.class,x.value());atom(op,"target","scope:des_test_target");
   return op.atom("modifier",null);
  }).collect(java.util.stream.Collectors.toSet());
  assertEquals(Set.of("des_apostasy_opinion","attempted_murder_me_crime"),modifiers);
  for(String k:List.of("has_imprisonment_reason","has_banish_reason","has_execute_reason"))atom(six,k,"scope:des_test_target");
 }
}
