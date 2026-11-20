package org.xar.ck3.markets.issuance;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Consumer;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;

/** Executes production registration/receipt and actual ensure_funds/fee/value/trigger AST.
 * Engine admission/account/story allocation/mint/index ports are explicit, not CK3 evidence.
 * This bounded interpreter follows the existing AiAttention test subset; unknown syntax fails.
 */
final class IssuanceOriginReceiptScriptTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static final List<String> INPUTS = List.of(
        "scripted_effects/xfm_issuer_registration.txt", "scripted_effects/xfm_issuer_receipts.txt",
        "scripted_effects/xfm_finance_cash.txt", "scripted_triggers/xfm_finance_triggers.txt",
        "script_values/xfm_finance_values.txt", "script_values/xfm_issuer_values.txt",
        "script_values/xfm_config_values.txt");

    @Test void actualMicroLandlessAiPaysMixedPrimaryGoldAndFreeAndKeepsActiveWalletSeparate() throws IOException {
        Vm v = vm(); Node a = issuer(v, "unlanded", "8.12345", "40");
        Node primary = (Node)a.vars.get("xfm_account"), active = account(v, "active", a, "900", false);
        a.vars.put("xfm_active_account", active);
        v.run("xfm_issuer_register_micro_effect", a);
        Node c = v.createdCoin;
        assertEquals(bd("1"), a.vars.get("xfm_issuer_result"));
        assertReceipt(c, a, primary, 100, 1, 0, -1);
        assertEquals(bd("40"), c.vars.get("xfm_issue_receipt_free_before"));
        assertEquals(bd("100"), c.vars.get("xfm_issue_receipt_free_pre_fee"));
        assertEquals(bd("0"), c.vars.get("xfm_issue_receipt_free_after"));
        assertEquals(bd("60"), c.vars.get("xfm_issue_receipt_topup_cents"));
        assertEquals(bd("8.12345"), c.vars.get("xfm_issue_receipt_gold_before"));
        assertEquals(bd("7.52345"), c.vars.get("xfm_issue_receipt_gold_after"));
        assertEquals(bd("900"), active.vars.get("xfm_free_cents"));
        assertEquals(bd("120"), v.exchange.vars.get("xfm_fee_cents"));
        assertEquals(1, v.feeExecutions); assertEquals(1, v.topupExecutions);
        clean(v, a);
    }

    @Test void actualStandardCountyAndHumanHegemonySnapshotNativePredicatesNotPlayerInference() throws IOException {
        for (boolean ai : List.of(true, false)) {
            Vm v = vm(); Node a = issuer(v, ai ? "count" : "human", "200", "300");
            a.ai = ai; a.landed = true; a.tier = ai ? "tier_county" : "tier_hegemony";
            v.run("xfm_issuer_register_standard_effect", a);
            assertReceipt(v.createdCoin, a, (Node)a.vars.get("xfm_account"), 500, ai ? 1 : 0, 1, ai ? 2 : 6);
            assertEquals(bd("200"), v.createdCoin.vars.get("xfm_issue_receipt_topup_cents"));
            assertEquals(bd("198"), a.gold); assertEquals(bd("520"), v.exchange.vars.get("xfm_fee_cents"));
            clean(v, a);
        }
    }

    @Test void exactNativeTierBranchesRemainIndependentFromLandlessness() throws IOException {
        List<String> tiers=List.of("tier_barony","tier_county","tier_duchy","tier_kingdom","tier_empire","tier_hegemony");
        for(int index=0;index<tiers.size();index++) {
            Vm v=vm();Node a=issuer(v,"tier-"+index,"10","100");a.tier=tiers.get(index);a.landed=index!=2;
            v.run("xfm_issuer_register_micro_effect",a);
            assertEquals(bd(Integer.toString(index+1)),v.createdCoin.vars.get("xfm_issue_receipt_highest_tier"));
            assertEquals(bd(a.landed?"1":"0"),v.createdCoin.vars.get("xfm_issue_receipt_is_landed"));
            assertEquals(bd("0"),v.createdCoin.vars.get("xfm_issue_receipt_topup_cents"));
            assertEquals(bd("10"),a.gold);clean(v,a);
        }
    }

    @Test void insufficientRealMoneyAndNativeAdmissionFailurePublishNoReceiptOrTransientState() throws IOException {
        Vm v = vm(); Node a = issuer(v, "poor", "0.49", "50");
        v.run("xfm_issuer_register_micro_effect", a);
        assertNull(v.createdCoin); assertEquals(0, v.feeExecutions);
        assertEquals(bd("0.49"), a.gold); assertEquals(bd("50"), ((Node)a.vars.get("xfm_account")).vars.get("xfm_free_cents"));
        clean(v, a);
        a.adult = false; a.gold = bd("10"); v.run("xfm_issuer_register_micro_effect", a);
        assertNull(v.createdCoin); assertEquals(bd("20"), v.exchange.vars.get("xfm_fee_cents")); clean(v, a);
    }

    @Test void failedActualFeeOrConstructionNeverPublishesNominalInitializationAsReceipt() throws IOException {
        for (String fault : List.of("fee", "mint")) {
            Vm v = vm(); Node a = issuer(v, fault, "10", "100");
            if (fault.equals("fee")) v.beforeFee = payer -> payer.vars.put("xfm_free_cents", bd("0"));
            else v.failMint = true;
            v.run("xfm_issuer_register_micro_effect", a);
            assertNotNull(v.createdCoin);
            assertEquals(bd("100"), v.createdCoin.vars.get("xfm_registration_paid_cents"));
            assertFalse(v.createdCoin.vars.containsKey("xfm_issue_receipt_version"));
            assertEquals(bd(fault.equals("fee") ? "20" : "120"), v.exchange.vars.get("xfm_fee_cents"));
            assertEquals(1, v.feeExecutions); clean(v, a);
        }
    }

    @Test void failedCoinAllocationPreservesOriginalTopupButNeverChargesFeeOrIssuesReceipt() throws IOException {
        Vm v = vm(); Node a = issuer(v, "no-allocation", "10", "0"); v.failCreate = true;
        v.run("xfm_issuer_register_micro_effect", a);
        assertNull(v.createdCoin); assertEquals(0, v.feeExecutions);
        assertEquals(bd("9"), a.gold); assertEquals(bd("100"), ((Node)a.vars.get("xfm_account")).vars.get("xfm_free_cents"));
        assertEquals(bd("20"), v.exchange.vars.get("xfm_fee_cents")); clean(v, a);
    }

    @Test void immutableReceiptSurvivesOwnerWealthChangesAndOldOrUnrelatedCoinIsNotBackfilled() throws IOException {
        Vm v = vm(); Node a = issuer(v, "issuer", "10", "100");
        v.run("xfm_issuer_register_micro_effect", a); Node c = v.createdCoin;
        Map<String,Object> before = new LinkedHashMap<>(c.vars);
        a.ai = false; a.landed = true; a.tier = "tier_empire"; a.gold = bd("999");
        v.run("xfm_issuer_receipt_commit_effect", c);
        assertEquals(before, c.vars);
        Node legacy = v.node("old"); legacy.type = "xfm_finance_coin";
        legacy.vars.put("xfm_coin_id", bd("1")); legacy.vars.put("xfm_supply_units", bd("15000"));
        legacy.vars.put("xfm_original_issuer", a);
        v.run("xfm_issuer_receipt_commit_effect", legacy);
        assertFalse(legacy.vars.containsKey("xfm_issue_receipt_version")); clean(v, a);
    }

    @Test void primaryOrFeePoolMismatchIsNotCertifiedAndUnsupportedTierStaysUnknown() throws IOException {
        for (String fault : List.of("primary", "pool", "reserved")) {
            Vm v = vm(); Node a = issuer(v, fault, "10", "100");
            if (fault.equals("primary")) v.afterAllocation = actor -> actor.vars.put("xfm_account", account(v, "replacement", actor, "100", false));
            if (fault.equals("pool")) v.afterFee = payer -> v.exchange.vars.put("xfm_fee_cents", v.num(v.exchange,"xfm_fee_cents").add(bd("1")));
            if (fault.equals("reserved")) v.afterFee = payer -> payer.vars.put("xfm_reserved_cents", bd("99"));
            v.run("xfm_issuer_register_micro_effect", a);
            assertFalse(v.createdCoin.vars.containsKey("xfm_issue_receipt_version")); clean(v, a);
        }
        Vm v = vm(); Node a = issuer(v, "unknown-tier", "10", "100"); a.landed = true; a.tier = "unrecognized_tier";
        v.run("xfm_issuer_register_micro_effect", a);
        assertEquals(bd("-1"), v.createdCoin.vars.get("xfm_issue_receipt_highest_tier"));
    }

    @Test void guardsAndOriginalMoneyBodiesAreExecutedWithoutSilentUnknownOperations() throws IOException {
        Vm v = vm(); Node a = issuer(v, "missing", "10", "100"); Node p = (Node)a.vars.get("xfm_account");
        p.vars.remove("xfm_account_id"); v.run("xfm_issuer_register_micro_effect", a);
        assertFalse(v.createdCoin.vars.containsKey("xfm_issue_receipt_version")); clean(v, a);
        assertThrows(IllegalArgumentException.class, () -> v.execute(parse("unknown_operation = yes"), a, null));
        assertThrows(IllegalArgumentException.class, () -> v.value(parse("value = 1 imaginary = 2"), a, null));
        assertTrue(v.executed.containsKey("xfm_finance_ensure_funds_effect"));
        assertTrue(v.executed.containsKey("xfm_finance_fee_effect"));
    }

    @Test void removingOnlyReceiptHooksRestoresOriginalBusinessAndMoneyOutcomes() throws IOException {
        for(String free:List.of("0","40","100","900")) {
            Vm recorded=vm(),original=vm();
            for(String name:List.of("xfm_issuer_register_effect","xfm_issuer_register_micro_effect","xfm_issuer_register_standard_effect"))
                original.program.put(name,withoutReceiptCalls(original.program.get(name)));
            Node a=issuer(recorded,"same","8.12345",free),b=issuer(original,"same","8.12345",free);
            recorded.run("xfm_issuer_register_micro_effect",a);original.run("xfm_issuer_register_micro_effect",b);
            assertEquals(businessGraph(original),businessGraph(recorded));
            clean(recorded,a);
        }
    }

    private static void assertReceipt(Node c, Node a, Node payer, int fee, int ai, int landed, int tier) {
        assertEquals(bd("1"), c.vars.get("xfm_issue_receipt_version"));
        assertSame(a, c.vars.get("xfm_issue_receipt_actor")); assertSame(payer, c.vars.get("xfm_issue_receipt_payer"));
        assertEquals(payer.vars.get("xfm_account_id"), c.vars.get("xfm_issue_receipt_payer_id"));
        assertEquals(bd(Integer.toString(fee)), c.vars.get("xfm_issue_receipt_fee_cents"));
        assertEquals(bd(Integer.toString(ai)), c.vars.get("xfm_issue_receipt_is_ai"));
        assertEquals(bd(Integer.toString(landed)), c.vars.get("xfm_issue_receipt_is_landed"));
        assertEquals(bd(Integer.toString(tier)), c.vars.get("xfm_issue_receipt_highest_tier"));
        assertEquals(bd("23"), c.vars.get("xfm_issue_receipt_day"));
        assertEquals(c.vars.get("xfm_coin_id"), c.vars.get("xfm_issue_receipt_coin_id"));
        assertEquals(c.vars.get("xfm_issue_receipt_reserved_before"), c.vars.get("xfm_issue_receipt_reserved_after"));
    }
    private static void clean(Vm v, Node a) {
        assertTrue(a.vars.keySet().stream().noneMatch(key -> key.startsWith("xfm_ir_")));
        assertTrue(v.scopes.keySet().stream().noneMatch(key -> key.startsWith("xfm_ir_")));
    }
    private static Map<String,Map<String,Object>> businessGraph(Vm v) {
        Map<String,Map<String,Object>> graph=new LinkedHashMap<>();
        for(Node node:v.nodes.values()) {
            Map<String,Object> fields=new LinkedHashMap<>();fields.put("gold",node.gold);fields.put("type",node.type);
            for(var field:node.vars.entrySet())if(!field.getKey().startsWith("xfm_issue_receipt_"))
                fields.put(field.getKey(),field.getValue() instanceof Node n?n.id:field.getValue());
            graph.put(node.id,fields);
        }return graph;
    }
    private static Block withoutReceiptCalls(Block block) {
        return new Block(block.entries().stream().filter(e->!e.key().startsWith("xfm_issuer_receipt_"))
            .map(e->new Entry(e.key(),e.op(),e.term() instanceof Block child?withoutReceiptCalls(child):e.term())).toList());
    }
    private static Node issuer(Vm v, String id, String gold, String free) {
        Node a = v.node(id); a.gold = bd(gold); a.vars.put("xfm_requested_entity_type", bd("1"));
        a.vars.put("xfm_account", account(v,id+"-primary",a,free,false)); return a;
    }
    private static Node account(Vm v, String id, Node holder, String free, boolean system) {
        Node p = v.node(id); p.type = "xfm_finance_account";
        p.vars.put("xfm_account_id", bd(Integer.toString(++v.nextAccount)));
        p.vars.put("xfm_holder",holder); p.vars.put("xfm_beneficial_owner",holder);
        p.vars.put("xfm_free_cents",bd(free)); p.vars.put("xfm_reserved_cents",bd("7"));
        p.vars.put("xfm_system_account",bd(system?"1":"0")); p.vars.put("xfm_account_frozen",bd("0")); return p;
    }
    private static Vm vm() throws IOException {
        Map<String,Block> defs = new LinkedHashMap<>();
        for(String relative:INPUTS) for(Entry e:parse(Files.readString(SOURCE.resolve("common").resolve(relative),StandardCharsets.UTF_8)).entries()) {
            Block b=e.term() instanceof Block block?block:new Block(List.of(new Entry("value","=",e.term())));
            if(defs.put(e.key(),b)!=null) throw new IllegalArgumentException("definition "+e.key());
        }
        return new Vm(defs);
    }
    private static BigDecimal bd(String text) { return new BigDecimal(text).setScale(5, RoundingMode.UNNECESSARY); }
    private static BigDecimal fixed(BigDecimal n) { return n.setScale(5,RoundingMode.DOWN); }
    private sealed interface Term permits Text, Block { }
    private record Text(String text) implements Term { }
    private record Block(List<Entry> entries) implements Term { Block { entries=List.copyOf(entries); } }
    private record Entry(String key,String op,Term term) { }
    private static Block parse(String source) {
        List<String> tokens=new ArrayList<>(); var match=Pattern.compile("#[^\\r\\n]*|[\\s\\uFEFF]+|>=|<=|!=|[{}=<>]|[^\\s{}=<>!#\\uFEFF]+").matcher(source);
        while(match.find()) {String token=match.group();if(!token.isBlank()&&!token.startsWith("#")&&!token.equals("\uFEFF"))tokens.add(token);}
        int[] at={0}; Block result=block(tokens,at,false);if(at[0]!=tokens.size())throw new IllegalArgumentException("trailing tokens");return result;
    }
    private static Block block(List<String> tokens,int[] at,boolean nested) {
        List<Entry> entries=new ArrayList<>();while(at[0]<tokens.size()) {
            String key=tokens.get(at[0]++);if(key.equals("}")){if(!nested)throw new IllegalArgumentException("unexpected }");return new Block(entries);}
            String op=tokens.get(at[0]++);if(!List.of("=","!=",">","<",">=","<=").contains(op))throw new IllegalArgumentException("operator "+op);
            String atom=tokens.get(at[0]++);entries.add(new Entry(key,op,atom.equals("{")?block(tokens,at,true):new Text(atom)));
        }if(nested)throw new IllegalArgumentException("missing }");return new Block(entries);
    }
    private static final class Node {
        final String id; final Map<String,Object> vars=new LinkedHashMap<>();
        final Map<String,List<Node>> lists=new HashMap<>();
        String type="",tier="none"; boolean alive=true,adult=true,ai=true,landed=false; BigDecimal gold=bd("0");
        Node(String id){this.id=id;}
    }
    private static final class Vm {
        final Map<String,Block> program; final Map<String,Node> nodes=new LinkedHashMap<>();
        final Map<String,Node> scopes=new HashMap<>(); final Map<String,Integer> executed=new HashMap<>(); final Node exchange;
        int nextAccount=100,feeExecutions,topupExecutions; boolean failCreate,failMint; Node createdCoin;
        Consumer<Node> beforeFee=p->{},afterFee=p->{},afterAllocation=a->{};
        Vm(Map<String,Block> program){this.program=program;exchange=node("exchange");exchange.type="xfm_finance_exchange";
            exchange.vars.put("xfm_day",bd("23"));exchange.vars.put("xfm_fee_cents",bd("20"));exchange.vars.put("xfm_next_coin_id",bd("0"));}
        Node node(String id){return nodes.computeIfAbsent(id,Node::new);}
        BigDecimal num(Node n,String key){Object value=n.vars.get(key);if(!(value instanceof BigDecimal b))throw new IllegalArgumentException("missing numeric "+n.id+"."+key);return b;}
        Object resolve(String text,Node here,Node prev){
            if(text.equals("this"))return here;if(text.equals("prev"))return prev;
            String global="global_var:xfm_exchange";if(text.equals(global))return exchange;
            if(text.startsWith(global+"."))return resolve(text.substring(global.length()+1),exchange,here);
            int dot=text.indexOf('.');if(dot>0){Object base=resolve(text.substring(0,dot),here,prev);return base instanceof Node n?resolve(text.substring(dot+1),n,here):null;}
            if(text.startsWith("scope:")){String name=text.substring(6);return scopes.containsKey(name)?scopes.get(name):numericScopes.get(name);}
            if(text.startsWith("var:"))return here.vars.get(text.substring(4));
            if(text.equals("gold"))return here.gold;
            if(program.containsKey(text))return value(program.get(text),here,prev);
            try{return bd(text);}catch(NumberFormatException ignored){return text;}
        }
        private String text(Term t){if(!(t instanceof Text a))throw new IllegalArgumentException("expected atom");return a.text();}
        private Object term(Term t,Node here,Node prev){return t instanceof Block b?value(b,here,prev):resolve(text(t),here,prev);}
        BigDecimal value(Block b,Node here,Node prev){
            BigDecimal n=bd("0");for(Entry e:b.entries()) {
                if(e.key().equals("floor")){n=n.setScale(0,RoundingMode.FLOOR).setScale(5);continue;}
                Object resolved=term(e.term(),here,prev);if(!(resolved instanceof BigDecimal operand))throw new IllegalArgumentException("non-numeric operand "+e.key());
                n=fixed(switch(e.key()){case "value"->operand;case "add"->n.add(operand);case "subtract"->n.subtract(operand);
                    case "multiply"->n.multiply(operand);case "divide"->n.divide(operand,5,RoundingMode.DOWN);
                    case "min"->n.max(operand);case "max"->n.min(operand);default->throw new IllegalArgumentException("value op "+e.key());});
            }return n;
        }
        boolean test(Block b,Node here,Node prev){for(Entry e:b.entries())if(!check(e,here,prev))return false;return true;}
        boolean check(Entry e,Node here,Node prev){String key=e.key();
            if(key.equals("always"))return text(e.term()).equals("yes");
            if(key.equals("AND"))return test((Block)e.term(),here,prev);
            if(key.equals("OR"))return ((Block)e.term()).entries().stream().anyMatch(x->check(x,here,prev));
            if(key.equals("NOT"))return ((Block)e.term()).entries().stream().noneMatch(x->check(x,here,prev));
            if(key.equals("has_variable"))return here.vars.containsKey(text(e.term()));
            if(key.equals("exists"))return resolve(text(e.term()),here,prev)!=null;
            if(key.equals("story_type"))return here.type.equals(text(e.term()));
            if(key.equals("is_alive"))return here.alive==text(e.term()).equals("yes");
            if(key.equals("is_adult"))return here.adult==text(e.term()).equals("yes");
            if(key.equals("is_ai"))return here.ai==text(e.term()).equals("yes");
            if(key.equals("is_landed"))return here.landed==text(e.term()).equals("yes");
            if(key.equals("highest_held_title_tier"))return here.tier.equals(text(e.term()));
            if(key.equals("any_in_list")){Block fields=(Block)e.term();String name=text(field(fields,"variable"));
                return here.lists.getOrDefault(name,List.of()).stream().anyMatch(n->test(without(fields,"variable"),n,here));}
            if(key.equals("xfm_issuer_can_register_trigger"))return here.alive&&here.adult; // explicit engine-admission port, not source coverage
            if(key.endsWith("_trigger")&&program.containsKey(key))return test(program.get(key),here,prev);
            if(key.endsWith("_trigger"))throw new IllegalArgumentException("unknown trigger "+key);
            if(!key.startsWith("var:")&&!key.startsWith("scope:")&&!key.startsWith("global_var:")&&!key.equals("this")&&!key.equals("prev")&&!key.equals("gold"))
                throw new IllegalArgumentException("unknown condition "+key);
            if(e.term() instanceof Block b){Object target=resolve(key,here,prev);return target instanceof Node n&&test(b,n,here);}
            Object left=resolve(key,here,prev),right=term(e.term(),here,prev);
            if(left instanceof BigDecimal x&&right instanceof BigDecimal y){int c=x.compareTo(y);return switch(e.op()){case "="->c==0;case "!="->c!=0;case ">"->c>0;case "<"->c<0;case ">="->c>=0;case "<="->c<=0;default->throw new IllegalArgumentException("compare "+e.op());};}
            if(e.op().equals("="))return Objects.equals(left,right);if(e.op().equals("!="))return !Objects.equals(left,right);
            throw new IllegalArgumentException("non-numeric comparison "+key);
        }
        void run(String name,Node here){
            Block b=program.get(name);if(b==null)throw new IllegalArgumentException("unknown effect "+name);
            executed.merge(name,1,Integer::sum);if(name.equals("xfm_finance_fee_effect")){feeExecutions++;beforeFee.accept(here);}
            if(name.equals("xfm_finance_ensure_funds_effect"))topupExecutions++;
            execute(b,here,null);if(name.equals("xfm_finance_fee_effect"))afterFee.accept(here);
        }
        void execute(Block b,Node here,Node prev){boolean chain=false;
            for(Entry e:b.entries()){String key=e.key();
                if(key.equals("if")||key.equals("else_if")){Block branch=(Block)e.term();boolean applies=(!key.equals("else_if")||!chain)&&test(child(branch,"limit"),here,prev);if(key.equals("if"))chain=false;if(applies){execute(without(branch,"limit"),here,prev);chain=true;}continue;}
                if(key.equals("else")){if(!chain)execute((Block)e.term(),here,prev);chain=false;continue;}
                if(key.equals("save_scope_as")){scopes.put(text(e.term()),here);continue;}
                if(key.equals("clear_saved_scope")){scopes.remove(text(e.term()));numericScopes.remove(text(e.term()));continue;}
                if(key.equals("save_scope_value_as")){Block f=(Block)e.term();numericScopes.put(text(field(f,"name")),term(field(f,"value"),here,prev));continue;}
                if(key.equals("remove_variable")){here.vars.remove(text(e.term()));continue;}
                if(key.equals("set_variable")||key.equals("change_variable")){Block f=(Block)e.term();String name=text(field(f,"name"));
                    if(key.equals("set_variable")){Term value=optional(f,"value");if(value==null)value=field(f,"days");here.vars.put(name,term(value,here,prev));}
                    else if(optional(f,"add")!=null)here.vars.put(name,fixed(num(here,name).add((BigDecimal)term(field(f,"add"),here,prev))));
                    else here.vars.put(name,fixed(num(here,name).subtract((BigDecimal)term(field(f,"subtract"),here,prev))));continue;}
                if(key.equals("remove_short_term_gold")){here.gold=fixed(here.gold.subtract((BigDecimal)term(e.term(),here,prev)));continue;}
                if(key.equals("xfm_finance_ensure_account_effect")){scopes.remove("xfm_account");Object a=here.vars.get("xfm_account");if(!(a instanceof Node n))throw new IllegalArgumentException("fixture PRIMARY required");scopes.put("xfm_account",n);continue;}
                if(key.equals("xfm_finance_create_coin_effect")){here.vars.remove("xfm_result_coin");scopes.remove("xfm_coin");here.vars.put("xfm_result",bd("0"));
                    if(!failCreate){Node c=node("new-coin");c.type="xfm_finance_coin";createdCoin=c;exchange.vars.put("xfm_next_coin_id",num(exchange,"xfm_next_coin_id").add(bd("1")));
                        c.vars.put("xfm_coin_id",num(exchange,"xfm_next_coin_id"));c.vars.put("xfm_supply_units",bd("0"));scopes.put("xfm_coin",c);here.vars.put("xfm_result_coin",c);here.vars.put("xfm_result",bd("1"));
                        if(here.vars.get("xfm_active_account") instanceof Node active)scopes.put("xfm_account",active);afterAllocation.accept(here);}continue;}
                if(key.equals("xfm_finance_create_account_effect")){Node a=account(this,"new-system-"+nextAccount,node("technical"),"0",true);a.vars.put("xfm_reserved_cents",bd("0"));scopes.put("xfm_created_account",a);continue;}
                if(key.equals("xfm_finance_mint_effect")){if(!failMint)here.vars.put("xfm_supply_units",num(here,"xfm_supply_units").add(num(here,"xfm_request_units")));continue;}
                if(key.equals("xfm_issuer_public_ipo_enqueue_effect"))continue; // independent index port; no payment/identity source
                if(key.equals("xfm_config_issuance_cooldown_days_value"))throw new IllegalArgumentException("value used as effect");
                if(e.term() instanceof Block branch){Object target=resolve(key,here,prev);if(!(target instanceof Node n))throw new IllegalArgumentException("missing scope "+key);execute(branch,n,here);continue;}
                run(key,here);
            }
        }
        final Map<String,Object> numericScopes=new HashMap<>();
    }
    private static Term optional(Block b,String key){for(Entry e:b.entries())if(e.key().equals(key))return e.term();return null;}
    private static Term field(Block b,String key){Term t=optional(b,key);if(t==null)throw new IllegalArgumentException("missing field "+key);return t;}
    private static Block child(Block b,String key){return (Block)field(b,key);}
    private static Block without(Block b,String key){return new Block(b.entries().stream().filter(e->!e.key().equals(key)).toList());}
}
