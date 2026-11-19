package org.xar.ck3.markets.acceptance;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.markets.acceptance.FollowupContracts.*;

/** Consumes the real producer output. Tests a narrow trigger/value subset, not CK3 parsing or business. */
final class FollowupClaimEqualityTest {
    @TempDir Path temporary;
    private static final List<Profile> CLAIM_PROFILES=List.of(Profile.DERIVATIVES,Profile.NEWS_CRISIS);
    private static Request request(Profile profile,int epoch) {
        return new Request(2,profile,epoch,new ActorBinding(ActorMode.CURRENT_PLAYER,null),
                new Targets("1",profile==Profile.COLD_RELOAD?null:"2",null,null,
                    Set.of(Profile.NEWS_CRISIS,Profile.LIFECYCLE,Profile.INHERITANCE).contains(profile)?"3":null,null),
                profile==Profile.COLD_RELOAD?new ColdBaseline(1,new AccountBaseline(0,0,0,0,0),null,null,null):null,
                profile==Profile.AI_CAPACITY?ScaleTier.SMOKE:null);
    }

    @Test void everyProfileEmitsNoNumericEqualityToArithmeticBlockAndDeclaredProfilesGainValues() {
        for(Profile profile:Profile.values()) {
            Request input=request(profile,101); var files=FollowupObservationScripts.render(input);
            boolean hasValues = CLAIM_PROFILES.contains(profile) || profile == Profile.SPOT || profile == Profile.MARKET_EVOLUTION || profile == Profile.DELISTING_GUI;
            Set<String> expectedFiles = new HashSet<>(Set.of("descriptor.mod",
                    "common/scripted_guis/"+input.prefix()+".txt", "gui/scripted_widgets/"+input.prefix()+".txt",
                    "gui/"+input.prefix()+".gui", "localization/english/"+input.prefix()+"_l_english.yml",
                    "localization/simp_chinese/"+input.prefix()+"_l_simp_chinese.yml",
                    "common/story_cycles/"+input.prefix()+".txt", "common/scripted_triggers/"+input.prefix()+".txt",
                    "common/scripted_effects/"+input.prefix()+"_observe.txt"));
            if (hasValues) expectedFiles.add(valuePath(input));
            if (profile == Profile.MARKET_EVOLUTION) expectedFiles.add("common/on_action/"+input.prefix()+".txt");
            assertEquals(expectedFiles, files.keySet(), "the new named observer listener is evolution-only");
            assertEquals((hasValues?10:9)+(profile==Profile.MARKET_EVOLUTION?1:0),files.size());
            assertEquals(hasValues,files.containsKey(valuePath(input)));
            files.forEach((path,bytes)->{
                if(path.startsWith("common/")) rejectArithmeticEquality(parse(new String(bytes,StandardCharsets.UTF_8)),path);
                assertArrayEquals(new byte[]{(byte)0xef,(byte)0xbb,(byte)0xbf},java.util.Arrays.copyOf(bytes,3));
            });
        }
        // Prove the guard actually rejects the shape rejected by the engine, including nested use.
        assertThrows(AssertionError.class,()->rejectArithmeticEquality(parse("if = { limit = { var:xfm_original_cents = { value = var:xfm_outstanding_cents add = var:xfm_repaid_cents } } }"),"former claim"));
    }

    @Test void savedScopeLiteralsStayDistinctAndCannotHideForbiddenArithmeticEquality() {
        Request r=request(Profile.SPOT,107);
        Block generated=script(FollowupObservationScripts.render(r),"common/scripted_guis/"+r.prefix()+".txt");
        for(String polarity:List.of("positive","negative")) {
            Block saved=generated.block(r.prefix()+"_scope_id_"+polarity+"_gui").block("saved_scopes");
            assertEquals(List.of(new Atom("xfma_probe_order_id")),saved.literals());
            assertTrue(saved.entries().isEmpty(),"saved scope literal is not an assignment");
        }
        Block list=parse("saved_scopes = { xfma_probe_order_id \"second_scope\" }").block("saved_scopes");
        assertEquals(List.of(new Atom("xfma_probe_order_id"),new Atom("second_scope")),list.literals());
        assertTrue(list.entries().isEmpty());
        rejectArithmeticEquality(generated,"actual spot ScriptedGUI");
        assertThrows(AssertionError.class,()->rejectArithmeticEquality(parse(
                "if = { saved_scopes = { xfma_probe_order_id } limit = { scope:claim = { value = var:outstanding add = var:repaid } } }"),"arithmetic after literal"));
        assertThrows(AssertionError.class,()->parse("saved_scopes = { xfma_probe_order_id } limit = }"));
        assertThrows(AssertionError.class,()->parse("saved_scopes = { xfma_probe_order_id"));
        assertThrows(AssertionError.class,()->parse("xfma_probe_order_id"));
        assertThrows(AssertionError.class,()->matches(parse("predicate = { rogue_literal }").block("predicate"),new Node("claim"),parse("")));
        assertThrows(AssertionError.class,()->sum(parse("claim_sum = { value = 1 rogue_literal }").block("claim_sum"),new Node("claim"),parse("")));
    }

    @Test void namedSumsKeepDebtScopeOriginalOperandsAndBothComparisonDirections() {
        for(Profile p:CLAIM_PROFILES) {
            Request r=request(p,102); var files=FollowupObservationScripts.render(r); Block values=script(files,valuePath(r));
            String split=r.prefix()+"_claim_split_value",principal=r.prefix()+"_claim_principal_value";
            assertEquals(parse("value = var:xfm_winner_unpaid_cents add = var:xfm_fund_recourse_cents"),values.block(split));
            assertEquals(parse("value = var:xfm_outstanding_cents add = var:xfm_repaid_cents add = var:xfm_written_off_cents"),values.block(principal));
            assertEquals(2,values.entries().size());
            Block predicate=claimLimit(files,r); Block debt=predicate.block("var:xfma_debt");
            for(Entry e:List.of(new Entry("var:xfm_outstanding_cents",">=",new Atom(split)),new Entry("var:xfm_outstanding_cents","<=",new Atom(split)),
                    new Entry("var:xfm_original_cents",">=",new Atom(principal)),new Entry("var:xfm_original_cents","<=",new Atom(principal)))) assertTrue(debt.entries().contains(e),e.toString());
            assertEquals(0,countWrites(values));
        }
    }

    @Test void generatedPredicatesAcceptConservedClaimsAndRejectEitherSideOffByOneCent() {
        for(Profile p:CLAIM_PROFILES) {
            Request r=request(p,103); var files=FollowupObservationScripts.render(r); Block values=script(files,valuePath(r)),predicate=claimLimit(files,r);
            for(long unpaid:List.of(0L,1L,500L,999_999_999_000L)) {
                Node debt=debt(unpaid,400,100,25); Node observer=new Node("observer").ref("xfma_debt",debt);
                assertTrue(matches(predicate,observer,values));
                for(String field:List.of("xfm_outstanding_cents","xfm_original_cents")) {
                    long old=debt.num(field); debt.number(field,old+1); assertFalse(matches(predicate,observer,values),field+" +1");
                    debt.number(field,old-1); assertFalse(matches(predicate,observer,values),field+" -1"); debt.number(field,old);
                }
                for(String field:List.of("xfm_winner_unpaid_cents","xfm_fund_recourse_cents","xfm_repaid_cents","xfm_written_off_cents")) {
                    long old=debt.num(field); debt.number(field,old+1); assertFalse(matches(predicate,observer,values),field+" changed without conserved totals"); debt.number(field,old);
                }
            }
        }
    }

    @Test void originalFieldPresenceSourcePartiesAndNonnegativeGuardsRemainRequired() {
        for(Profile p:CLAIM_PROFILES) {
            Request r=request(p,104); var files=FollowupObservationScripts.render(r); Block values=script(files,valuePath(r)),predicate=claimLimit(files,r);
            Node debt=debt(500,400,100,0),observer=new Node("observer").ref("xfma_debt",debt);
            for(String field:List.of("xfm_original_cents","xfm_outstanding_cents","xfm_winner_unpaid_cents","xfm_fund_recourse_cents","xfm_repaid_cents","xfm_written_off_cents","xfm_source_day","xfm_source_kind","xfm_debtor_account","xfm_creditor_account","xfm_source")) {
                Datum old=debt.variables.remove(field); assertFalse(matches(predicate,observer,values),"missing "+field); debt.variables.put(field,old);
            }
            debt.number("xfm_original_cents",0); assertFalse(matches(predicate,observer,values));
            debt.number("xfm_original_cents",1000).number("xfm_winner_unpaid_cents",-1).number("xfm_fund_recourse_cents",901);
            assertFalse(matches(predicate,observer,values),"negative split cannot be hidden by arithmetic equality");
        }
    }

    @Test void generatedComparisonMatchesOriginalConservationLawAcrossAuthoredBoundarySamples() {
        Random random=new Random(20261118L);
        for(Profile p:CLAIM_PROFILES) {
            Request r=request(p,105); var files=FollowupObservationScripts.render(r); Block values=script(files,valuePath(r)),predicate=claimLimit(files,r);
            for(int i=0;i<128;i++) {
                long unpaid=random.nextLong(1_000_000_000_000L),fund=random.nextLong(100_000_000L),repaid=random.nextLong(100_000_000L),written=random.nextLong(100_000_000L);
                Node d=debt(unpaid,fund,repaid,written),observer=new Node("observer").ref("xfma_debt",d);
                if(i%2==1)d.number("xfm_original_cents",d.num("xfm_original_cents")+(i%3==0?-1:1));
                if(i%5==0)d.number("xfm_outstanding_cents",d.num("xfm_outstanding_cents")+1);
                boolean expected=d.num("xfm_original_cents")>0 && d.num("xfm_outstanding_cents")>=0 && unpaid>=0 && fund>=0
                        && d.num("xfm_outstanding_cents")==unpaid+fund
                        && d.num("xfm_original_cents")==d.num("xfm_outstanding_cents")+repaid+written;
                assertEquals(expected,matches(predicate,observer,values));
            }
        }
    }

    @Test void actualEmitterIncludesNewPureValueFileAndBothReachExistingSavedAndHostCopyConsumers() throws Exception {
        Path repo=Path.of(System.getProperty("xfm.source")).toAbsolutePath().normalize().getParent();
        Path shared=Path.of(System.getProperty("xfm.shared.source",repo.toString())).toAbsolutePath().normalize();
        for(Profile p:CLAIM_PROFILES) {
            Request input=request(p,106); var emitted=FixtureEmitter.emit(repo,temporary.resolve(p.wire()),"synthetic-fixture-machine",input);
            var manifest=FixtureEmitter.JSON.readTree(Files.readAllBytes(Path.of(emitted.manifest().path())));
            Path values=Path.of(emitted.fixture()).resolve(valuePath(input));
            assertTrue(Files.isRegularFile(values)); var actual=FixtureEmitter.pin(values);
            assertEquals(actual.sha256(),manifest.path("files").path(valuePath(input)).path("sha256").textValue());
            assertEquals(actual.bytes(),manifest.path("files").path(valuePath(input)).path("bytes").longValue());
            assertEquals(11,manifest.path("files").size()); // ten scripts plus the exact request
            assertFalse(emitted.gameStarted()); assertEquals("NOT_RUN",emitted.businessAcceptance());
            assertFalse(manifest.path("receipt").path("fixture_contains_business_effects").booleanValue());
            assertArrayEquals(FollowupObservationScripts.render(input).get(valuePath(input)),Files.readAllBytes(values));
            Path scratch=temporary.resolve("consumer-"+p.wire()),log=temporary.resolve("consumer-"+p.wire()+".log");
            var process=new ProcessBuilder(System.getProperty("xfm.python","python"),"-B","-X","utf8",
                    shared.resolve("mod_financial_markets/tools/src/test/resources/acceptance/verify_saved_observer_inventory.py").toString(),
                    "--repo-root",repo.toString(),"--shared-source",shared.toString(),"--manifest",emitted.manifest().path(),"--scratch",scratch.toString())
                    .directory(shared.toFile()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
            assertTrue(process.waitFor(90,TimeUnit.SECONDS),"Saved software consumer timed out: "+p);
            assertEquals(0,process.exitValue(),Files.readString(log));
            var result=FixtureEmitter.JSON.readTree(Files.readAllBytes(scratch.resolve("actual-result.json")));
            assertTrue(result.path("saved_inventory_verified").booleanValue());
            assertTrue(result.path("host_copy_readback_verified").booleanValue());
            assertFalse(result.path("game_started").booleanValue());
            assertFalse(result.path("business_acceptance_proven").booleanValue());
        }
    }

    private static String valuePath(Request r){return "common/script_values/"+r.prefix()+".txt";}
    private static Block script(Map<String,byte[]> files,String path){return parse(new String(files.get(path),StandardCharsets.UTF_8));}
    private static Node debt(long unpaid,long fund,long repaid,long written) {
        return new Node("xfm_debt_claim").number("xfm_original_cents",unpaid+fund+repaid+written).number("xfm_outstanding_cents",unpaid+fund)
                .number("xfm_winner_unpaid_cents",unpaid).number("xfm_fund_recourse_cents",fund).number("xfm_repaid_cents",repaid).number("xfm_written_off_cents",written)
                .number("xfm_source_day",1).number("xfm_source_kind",3).ref("xfm_debtor_account",new Node("account")).ref("xfm_creditor_account",new Node("account")).ref("xfm_source",new Node("position"));
    }
    private static Block claimLimit(Map<String,byte[]> files,Request r) {
        Block profile=script(files,"common/scripted_effects/"+r.prefix()+"_observe.txt").block(r.prefix()+"_profile_effect");
        for(Entry e:profile.entries())if(e.key().equals("if")&&e.value() instanceof Block body && body.entries().contains(new Entry("debug_log","=",new Atom("XFMAT: TEST PASS "+r.caseId().scriptKey()+"_claim_accounting_readback"))))return body.block("limit");
        throw new AssertionError("missing generated claim marker predicate");
    }
    private static void rejectArithmeticEquality(Block b,String path) {
        for(Entry e:b.entries())if(e.value() instanceof Block child) {
            assertFalse(e.op().equals("=")&&(e.key().startsWith("var:")||e.key().startsWith("global_var:")||e.key().startsWith("scope:"))&&child.entries().stream().anyMatch(x->x.key().equals("value")),path+": "+e.key());
            rejectArithmeticEquality(child,path);
        }
    }
    private static int countWrites(Block b){int count=0;for(Entry e:b.entries()){if(Set.of("set_variable","change_variable","remove_variable").contains(e.key()))count++;if(e.value() instanceof Block child)count+=countWrites(child);}return count;}
    private sealed interface Expr permits Atom,Block{}
    private record Atom(String text)implements Expr{}
    private record Entry(String key,String op,Expr value){}
    private record Block(List<Entry> entries,List<Atom> literals)implements Expr{
        Block{entries=List.copyOf(entries);literals=List.copyOf(literals);}
        Block block(String key){return entries.stream().filter(e->e.key().equals(key)).map(e->(Block)e.value()).findFirst().orElseThrow();}
    }
    private sealed interface Datum permits NumberValue,NodeValue{}
    private record NumberValue(long value)implements Datum{}
    private record NodeValue(Node value)implements Datum{}
    private static final class Node{final String type;final Map<String,Datum> variables=new HashMap<>();Node(String type){this.type=type;}Node number(String key,long value){variables.put(key,new NumberValue(value));return this;}Node ref(String key,Node value){variables.put(key,new NodeValue(value));return this;}long num(String key){return ((NumberValue)variables.get(key)).value();}}
    private static Block parse(String source) {
        var matcher=Pattern.compile("\"(?:\\\\.|[^\"\\\\])*\"|!=|>=|<=|[{}=<>]|[^\\s{}=<>]+").matcher(source.replace("\ufeff","").replaceAll("(?m)#.*$",""));
        List<String> tokens=new ArrayList<>();while(matcher.find())tokens.add(matcher.group());int[] index={0};Block result=block(tokens,index,false);assertEquals(tokens.size(),index[0]);return result;
    }
    private static Block block(List<String> tokens,int[] index,boolean nested){
        List<Entry> entries=new ArrayList<>();List<Atom> literals=new ArrayList<>();
        Set<String> operators=Set.of("=","!=",">=","<=",">","<");
        while(index[0]<tokens.size()){
            String key=tokens.get(index[0]++);
            if(key.equals("}")){assertTrue(nested);return new Block(entries,literals);}
            assertFalse(key.equals("{")||operators.contains(key),"expected script key or list literal");
            if(index[0]>=tokens.size()||!operators.contains(tokens.get(index[0]))){
                assertTrue(nested,"bare literal outside a block");
                literals.add(new Atom(key.startsWith("\"")?key.substring(1,key.length()-1):key));
                continue;
            }
            String op=tokens.get(index[0]++);
            assertTrue(index[0]<tokens.size(),"missing script value");
            String value=tokens.get(index[0]++);
            assertFalse(value.equals("}")||operators.contains(value),"missing script value");
            entries.add(new Entry(key,op,value.equals("{")?block(tokens,index,true):new Atom(value.startsWith("\"")?value.substring(1,value.length()-1):value)));
        }
        assertFalse(nested,"unclosed script");return new Block(entries,literals);
    }
    private static boolean matches(Block b,Node node,Block values){assertTrue(b.literals().isEmpty(),"bare list is not a trigger predicate");return b.entries().stream().allMatch(e->check(e,node,values));}
    private static boolean check(Entry e,Node node,Block values){
        if(e.key().equals("NOT"))return !matches((Block)e.value(),node,values);
        if(e.key().equals("has_variable"))return node.variables.containsKey(((Atom)e.value()).text());
        if(e.key().equals("story_type"))return node.type.equals(((Atom)e.value()).text());
        if(e.key().equals("exists"))return node.variables.containsKey(((Atom)e.value()).text().substring(4));
        if(e.value() instanceof Block child){Datum d=resolve(e.key(),node,values);return d instanceof NodeValue n&&matches(child,n.value(),values);}
        Datum left=resolve(e.key(),node,values),right=resolve(((Atom)e.value()).text(),node,values);if(!(left instanceof NumberValue l)||!(right instanceof NumberValue r))return false;
        return switch(e.op()){case "="->l.value()==r.value();case ">="->l.value()>=r.value();case "<="->l.value()<=r.value();case ">"->l.value()>r.value();default->throw new AssertionError("unknown trigger operator "+e.op());};
    }
    private static Datum resolve(String text,Node node,Block values){
        if(text.startsWith("var:"))return node.variables.get(text.substring(4));
        if(text.matches("-?[0-9]+"))return new NumberValue(Long.parseLong(text));
        for(Entry e:values.entries())if(e.key().equals(text))return new NumberValue(sum((Block)e.value(),node,values));
        throw new AssertionError("unknown fixture reference "+text);
    }
    private static long sum(Block b,Node node,Block values){assertTrue(b.literals().isEmpty(),"bare list is not arithmetic");long result=0;for(Entry e:b.entries()){Datum d=resolve(((Atom)e.value()).text(),node,values);if(!(d instanceof NumberValue n))throw new AssertionError("missing sum operand");result=switch(e.key()){case "value"->n.value();case "add"->Math.addExact(result,n.value());default->throw new AssertionError("unexpected value operation "+e.key());};}return result;}
}
