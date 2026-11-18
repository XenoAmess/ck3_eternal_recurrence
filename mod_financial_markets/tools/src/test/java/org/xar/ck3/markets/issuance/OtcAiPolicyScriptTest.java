package org.xar.ck3.markets.issuance;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;

/** Reads actual native policy/event trees. The limited interpreter and accept port are not CK3. */
final class OtcAiPolicyScriptTest {
    private static final Path SOURCE=Path.of(System.getProperty("xfm.source",".."));
    private static final List<String> INPUTS=List.of("scripted_triggers/xfm_otc_ai_triggers.txt","script_values/xfm_otc_ai_values.txt",
            "scripted_triggers/xfm_finance_triggers.txt","script_values/xfm_finance_values.txt","script_values/xfm_finance_asset_values.txt");

    @Test void defaultD30DelistedProposalCanBeConsideredWithRealCertifiedHistoryWithoutFreshOracle() throws IOException {
        Vm v=fixture(); v.coin.number("xfm_oracle_reason",2).number("xfm_oracle_quality",0).number("xfm_last_price_cents",999999);
        assertFalse(v.test("xfm_otc_ai_fresh_trigger")); assertTrue(v.test("xfm_otc_ai_stale_trigger"));
        assertEquals(5,v.weight(v.accept.block("ai_chance"))); assertEquals(50,v.weight(v.decline.block("ai_chance")));
        v.quotePrice(26); assertFalse(v.test("xfm_otc_ai_eligible_trigger"));
        v.quotePrice(25); v.coin.vars.remove("xfm_termination_price_cents");
        assertFalse(v.test("xfm_otc_ai_eligible_trigger"),"last trade and issuer cash never replace missing certified price");
    }

    @Test void currentQualifiedIndexGetsFreshRiskDiscountAndWeightWithoutStaleFallback() throws IOException {
        Vm v=fixture(); v.coin.number("xfm_listing_state",1).number("xfm_trading_open",1).number("xfm_oracle_reason",0)
                .number("xfm_oracle_quality",1).number("xfm_oracle_day",30).number("xfm_index_cents",100).number("xfm_mark_cents",100);
        v.quotePrice(90); assertTrue(v.test("xfm_otc_ai_fresh_trigger")); assertFalse(v.test("xfm_otc_ai_stale_trigger"));
        assertEquals(10,v.weight(v.accept.block("ai_chance"))); v.quotePrice(91); assertFalse(v.test("xfm_otc_ai_eligible_trigger"));
        v.quotePrice(25); v.coin.number("xfm_oracle_day",29); assertFalse(v.test("xfm_otc_ai_eligible_trigger"));
        v.coin.number("xfm_oracle_day",30); v.coin.vars.remove("xfm_index_cents"); assertFalse(v.test("xfm_otc_ai_eligible_trigger"));
    }

    @Test void staleHistoryRequiresEveryProducerBindingAndFiniteRealTimeWindow() throws IOException {
        Vm v=fixture(); assertTrue(v.test("xfm_otc_ai_stale_trigger"));
        for(String field:List.of("xfm_notice_day","xfm_termination_price_certified","xfm_termination_price_cents","xfm_termination_samples",
                "xfm_termination_price_source_coin","xfm_termination_source_notice_day","xfm_termination_window_start_day","xfm_termination_window_end_day")) {
            Datum old=v.coin.vars.remove(field); assertFalse(v.test("xfm_otc_ai_stale_trigger"),"missing "+field); v.coin.vars.put(field,old);
        }
        v.coin.number("xfm_termination_samples",2); assertFalse(v.test("xfm_otc_ai_stale_trigger")); v.coin.number("xfm_termination_samples",3);
        v.coin.ref("xfm_termination_price_source_coin",new Node("xfm_finance_coin")); assertFalse(v.test("xfm_otc_ai_stale_trigger")); v.coin.ref("xfm_termination_price_source_coin",v.coin);
        v.coin.number("xfm_termination_source_notice_day",1); assertFalse(v.test("xfm_otc_ai_stale_trigger")); v.coin.number("xfm_termination_source_notice_day",0);
        v.coin.number("xfm_termination_window_end_day",21); assertFalse(v.test("xfm_otc_ai_stale_trigger")); v.coin.number("xfm_termination_window_end_day",20);
        v.expiry(117); v.exchange.number("xfm_day",110); assertTrue(v.test("xfm_otc_ai_stale_trigger"));
        v.exchange.number("xfm_day",111); assertFalse(v.test("xfm_otc_ai_stale_trigger"));
        v.exchange.number("xfm_day",19); assertFalse(v.test("xfm_otc_ai_stale_trigger"),"future certificate cannot be clamped to age zero");
    }

    @Test void actualFreeCashPlusGoldBudgetsKeepFiveGoldAndRespectTwoRiskCaps() throws IOException {
        Vm v=fixture(); v.buyer.gold=5; v.buyerAccount.number("xfm_free_cents",0).number("xfm_reserved_cents",999999);
        assertEquals(0,v.value("xfm_otc_ai_stale_budget_value",v.buyer,null)); assertFalse(v.test("xfm_otc_ai_eligible_trigger"));
        v.buyerAccount.number("xfm_free_cents",500); assertEquals(25,v.value("xfm_otc_ai_stale_budget_value",v.buyer,null));
        assertTrue(v.test("xfm_otc_ai_stale_trigger")); v.quotePrice(26); assertFalse(v.test("xfm_otc_ai_stale_trigger"));
        v.quotePrice(25); v.buyerAccount.number("xfm_free_cents",499); assertFalse(v.test("xfm_otc_ai_stale_trigger"));
        v.buyer.gold=10000; assertEquals(200,v.value("xfm_otc_ai_stale_budget_value",v.buyer,null));
        assertEquals(1000,v.value("xfm_otc_ai_fresh_budget_value",v.buyer,null));
        v.scopes.put("xfm_ui_otc_lots",new NumberValue(8)); v.seller.number("xfm_otc_offer_lots",8);
        assertTrue(v.test("xfm_otc_ai_stale_trigger")); v.scopes.put("xfm_ui_otc_lots",new NumberValue(9)); v.seller.number("xfm_otc_offer_lots",9);
        assertFalse(v.test("xfm_otc_ai_stale_trigger"),"total consideration, not unit price, is the risk budget");
    }

    @Test void invalidRightsRelatedBeneficiariesDestroyedAssetsAndMissingProposalFieldsAlwaysReject() throws IOException {
        Vm v=fixture();
        for(String scope:List.of("xfm_ui_otc_nonce","xfm_ui_otc_price_version","xfm_ui_otc_expiry_day","xfm_ui_otc_lots","xfm_ui_otc_limit_cents")) {
            Datum old=v.scopes.remove(scope); assertFalse(v.test("xfm_otc_ai_common_trigger"),"missing numeric "+scope);v.scopes.put(scope,old);
        }
        for(String field:List.of("xfm_free_cents","xfm_reserved_cents","xfm_account_frozen","xfm_system_account","xfm_holder","xfm_beneficial_owner")) {
            Datum old=v.buyerAccount.vars.remove(field); assertFalse(v.test("xfm_otc_ai_common_trigger"),"missing account "+field);v.buyerAccount.vars.put(field,old);
        }
        v.buyerAccount.ref("xfm_beneficial_owner",v.seller); assertFalse(v.test("xfm_otc_ai_common_trigger")); v.buyerAccount.ref("xfm_beneficial_owner",v.buyer);
        v.sellerAccount.ref("xfm_beneficial_owner",v.buyer); assertFalse(v.test("xfm_otc_ai_common_trigger")); v.sellerAccount.ref("xfm_beneficial_owner",v.seller);
        v.sellerPosition.number("xfm_reserved_units",10000); assertFalse(v.test("xfm_otc_ai_common_trigger")); v.sellerPosition.number("xfm_reserved_units",0);
        v.coin.number("xfm_supply_units",0); assertFalse(v.test("xfm_otc_ai_common_trigger")); v.coin.number("xfm_supply_units",10000);
        v.coin.number("xfm_listing_state",7); assertFalse(v.test("xfm_otc_ai_common_trigger")); v.coin.number("xfm_listing_state",5);
        v.sellerAccount.ref("xfm_holder",v.buyer); assertFalse(v.test("xfm_otc_ai_common_trigger"));
    }

    @Test void proposalNonceVersionExpiryWholeLotsAndSuccessfulSevenDayCooldownRecheck() throws IOException {
        Vm v=fixture(); v.seller.number("xfm_otc_offer_nonce",2); assertFalse(v.test("xfm_otc_ai_common_trigger")); v.seller.number("xfm_otc_offer_nonce",1);
        v.coin.number("xfm_price_version",2); assertFalse(v.test("xfm_otc_ai_common_trigger")); v.coin.number("xfm_price_version",1);
        v.expiry(30); assertFalse(v.test("xfm_otc_ai_common_trigger")); v.expiry(37);
        v.scopes.put("xfm_ui_otc_lots",new NumberValue(1.5));v.seller.number("xfm_otc_offer_lots",1.5);assertFalse(v.test("xfm_otc_ai_common_trigger"));
        v.scopes.put("xfm_ui_otc_lots",new NumberValue(1));v.seller.number("xfm_otc_offer_lots",1);
        v.executeOption(); assertEquals(1,v.acceptCalls); assertEquals(30,v.buyer.num("xfm_otc_ai_last_buy_day"));
        assertFalse(v.test("xfm_otc_ai_eligible_trigger")); v.exchange.number("xfm_day",36); assertFalse(v.test("xfm_otc_ai_eligible_trigger"));
        v.exchange.number("xfm_day",37); v.expiry(44); assertTrue(v.test("xfm_otc_ai_eligible_trigger"));
    }

    @Test void eventRevalidatesAfterWeightAndMarksOnlyRealSuccessWhileHumanConsentPathStaysOriginal() throws IOException {
        Vm v=fixture(); assertEquals(5,v.weight(v.accept.block("ai_chance")));
        v.buyer.gold=5; v.executeOption(); assertEquals(0,v.acceptCalls); assertFalse(v.buyer.vars.containsKey("xfm_otc_ai_last_buy_day"));
        v.buyer.gold=100;v.publicAcceptSucceeds=false;v.executeOption();assertEquals(1,v.acceptCalls);assertFalse(v.buyer.vars.containsKey("xfm_otc_ai_last_buy_day"));
        v.buyer.ai=false;v.buyer.gold=0;v.executeOption();assertEquals(2,v.acceptCalls,"human still calls the original public legal/consent validator");
        assertFalse(v.buyer.vars.containsKey("xfm_otc_ai_last_buy_day"));
        Block event=parse(Files.readString(SOURCE.resolve("events/xfm_market_otc_events.txt"))).block("xfm_market.120");
        assertEquals(parse("scope:xfm_ui_otc_seller = { has_variable = xfm_otc_consent var:xfm_otc_offer_nonce = scope:xfm_ui_otc_nonce } global_var:xfm_exchange.var:xfm_day < scope:xfm_ui_otc_expiry_day"),option(event,"xfm_market_otc_accept").block("trigger"));
        assertEquals(parse("name = xfm_market_otc_decline xfm_market_ui_otc_decline_effect = yes ai_chance = { base = 50 }"),option(event,"xfm_market_otc_decline"));
    }

    @Test void sourceUsesExistingAtomicDvpWithoutIssuerReserveFloorOrPriceWrites() throws IOException {
        Vm v=fixture();
        for(String name:List.of("xfm_otc_ai_fresh_trigger","xfm_otc_ai_stale_trigger"))assertTrue(v.defs.containsKey(name));
        String values=Files.readString(SOURCE.resolve("common/script_values/xfm_otc_ai_values.txt"));
        for(String forbidden:List.of("xfm_issuer_account","xfm_bond_reservation","xfm_maintenance_reservation","set_variable","xfm_last_price_cents"))assertFalse(values.contains(forbidden),forbidden);
        String listing=Files.readString(dependency("scripted_effects/xfm_listing_otc.txt"));
        assertTrue(listing.contains("xfm_finance_ensure_funds_effect = yes")); assertTrue(listing.contains("xfm_finance_otc_effect = yes"));
        String atomic=Files.readString(dependency("scripted_effects/xfm_finance_otc.txt"));assertTrue(atomic.contains("xfm_finance_position_available_value >="));
        for(String rel:List.of("events/xfm_market_otc_events.txt","common/scripted_triggers/xfm_otc_ai_triggers.txt","common/script_values/xfm_otc_ai_values.txt")) {
            byte[] bytes=Files.readAllBytes(SOURCE.resolve(rel));assertArrayEquals(new byte[]{(byte)0xef,(byte)0xbb,(byte)0xbf},java.util.Arrays.copyOf(bytes,3));rejectNumericEqualityBlock(parse(new String(bytes,StandardCharsets.UTF_8)));
        }
        assertThrows(AssertionError.class,()->v.evaluate(parse("unknown_policy_operator = 1"),v.buyer,null,0));
    }

    private static Path dependency(String relative){Path direct=SOURCE.resolve("common").resolve(relative).normalize();return Files.exists(direct)?direct:SOURCE.resolve("../baseline/mod_financial_markets/common").resolve(relative).normalize();}
    private static Vm fixture()throws IOException {
        Map<String,Block> defs=new LinkedHashMap<>();for(String rel:INPUTS)for(Entry e:parse(Files.readString(dependency(rel))).entries())defs.put(e.key(),(Block)e.value());
        return new Vm(defs,parse(Files.readString(SOURCE.resolve("events/xfm_market_otc_events.txt"))).block("xfm_market.120"));
    }
    private static Block option(Block event,String name){return event.entries().stream().filter(e->e.key().equals("option")).map(e->(Block)e.value()).filter(b->b.entries().contains(new Entry("name","=",new Atom(name)))).findFirst().orElseThrow();}
    private static void rejectNumericEqualityBlock(Block b){for(Entry e:b.entries())if(e.value()instanceof Block child){assertFalse(e.op().equals("=")&&(e.key().startsWith("var:")||e.key().startsWith("scope:")||e.key().startsWith("global_var:"))&&child.entries().stream().anyMatch(x->x.key().equals("value")));rejectNumericEqualityBlock(child);}}
    private sealed interface Expr permits Atom,Block{}
    private record Atom(String text)implements Expr{}
    private record Entry(String key,String op,Expr value){}
    private record Block(List<Entry> entries)implements Expr{Block{entries=List.copyOf(entries);}Block block(String key){return (Block)entries.stream().filter(e->e.key().equals(key)).findFirst().orElseThrow().value();}}
    private sealed interface Datum permits NumberValue,NodeValue{}
    private record NumberValue(double value)implements Datum{}
    private record NodeValue(Node value)implements Datum{}
    private static final class Node{final String type;final Map<String,Datum>vars=new HashMap<>();final Map<String,List<Node>>lists=new HashMap<>();double gold;boolean ai=true,alive=true,adult=true;Node(String type){this.type=type;}Node number(String key,double n){vars.put(key,new NumberValue(n));return this;}Node ref(String key,Node n){vars.put(key,new NodeValue(n));return this;}double num(String key){return ((NumberValue)vars.get(key)).value();}}
    private static Block parse(String source){var matcher=Pattern.compile("\"(?:\\\\.|[^\"\\\\])*\"|!=|>=|<=|[{}=<>]|[^\\s{}=<>]+").matcher(source.replace("\ufeff","").replaceAll("(?m)#.*$",""));List<String>tokens=new ArrayList<>();while(matcher.find())tokens.add(matcher.group());int[]at={0};Block result=block(tokens,at,false);assertEquals(tokens.size(),at[0]);return result;}
    private static Block block(List<String>tokens,int[]at,boolean nested){List<Entry>entries=new ArrayList<>();while(at[0]<tokens.size()){String key=tokens.get(at[0]++);if(key.equals("}")){assertTrue(nested);return new Block(entries);}String op=tokens.get(at[0]++);assertTrue(Set.of("=","!=",">=","<=",">","<").contains(op));String word=tokens.get(at[0]++);entries.add(new Entry(key,op,word.equals("{")?block(tokens,at,true):new Atom(word.startsWith("\"")?word.substring(1,word.length()-1):word)));}assertFalse(nested);return new Block(entries);}
    private static Block without(Block b,String...keys){Set<String>omit=Set.of(keys);return new Block(b.entries().stream().filter(e->!omit.contains(e.key())).toList());}
    private static String atom(Expr e){return ((Atom)e).text();}
    private static final class Vm {
        final Map<String,Block>defs;final Map<String,Datum>scopes=new HashMap<>();final Node exchange=new Node("xfm_finance_exchange"),buyer=new Node("character"),seller=new Node("character"),buyerAccount=new Node("xfm_finance_account"),sellerAccount=new Node("xfm_finance_account"),coin=new Node("xfm_finance_coin"),sellerPosition=new Node("xfm_finance_position");
        final Block accept,decline;boolean publicAcceptSucceeds=true;int acceptCalls;
        Vm(Map<String,Block>defs,Block event){this.defs=defs;accept=option(event,"xfm_market_otc_accept");decline=option(event,"xfm_market_otc_decline");exchange.number("xfm_day",30);buyer.gold=100;buyer.ref("xfm_account",buyerAccount);seller.ref("xfm_account",sellerAccount).ref("xfm_otc_buyer",buyer).number("xfm_otc_consent",1).number("xfm_otc_offer_nonce",1).ref("xfm_otc_offer_coin",coin).number("xfm_otc_offer_lots",1).number("xfm_otc_offer_price_cents",25).number("xfm_otc_offer_expires_day",37).number("xfm_otc_offer_price_version",1);
            for(Node a:List.of(buyerAccount,sellerAccount))a.number("xfm_free_cents",0).number("xfm_reserved_cents",0).number("xfm_account_frozen",0).number("xfm_system_account",0);
            buyerAccount.ref("xfm_holder",buyer).ref("xfm_beneficial_owner",buyer);sellerAccount.ref("xfm_holder",seller).ref("xfm_beneficial_owner",seller);sellerAccount.lists.put("xfm_positions",List.of(sellerPosition));sellerPosition.ref("xfm_account",sellerAccount).ref("xfm_coin",coin).number("xfm_quantity_units",10000).number("xfm_reserved_units",0);
            coin.number("xfm_listing_state",5).number("xfm_trading_open",0).number("xfm_supply_units",10000).number("xfm_price_version",1).number("xfm_termination_price_certified",1).number("xfm_termination_price_cents",100).number("xfm_termination_samples",3).ref("xfm_termination_price_source_coin",coin).number("xfm_notice_day",0).number("xfm_termination_source_notice_day",0).number("xfm_termination_window_start_day",15).number("xfm_termination_window_end_day",20);
            scopes.put("xfm_ui_otc_buyer",new NodeValue(buyer));scopes.put("xfm_ui_otc_seller",new NodeValue(seller));scopes.put("xfm_ui_otc_buyer_account",new NodeValue(buyerAccount));scopes.put("xfm_ui_otc_seller_account",new NodeValue(sellerAccount));scopes.put("xfm_ui_otc_coin",new NodeValue(coin));scopes.put("xfm_ui_otc_nonce",new NumberValue(1));scopes.put("xfm_ui_otc_price_version",new NumberValue(1));scopes.put("xfm_ui_otc_lots",new NumberValue(1));scopes.put("xfm_ui_otc_limit_cents",new NumberValue(25));scopes.put("xfm_ui_otc_expiry_day",new NumberValue(37));}
        void quotePrice(double n){scopes.put("xfm_ui_otc_limit_cents",new NumberValue(n));seller.number("xfm_otc_offer_price_cents",n);}
        void expiry(double n){scopes.put("xfm_ui_otc_expiry_day",new NumberValue(n));seller.number("xfm_otc_offer_expires_day",n);}
        boolean test(String name){return matches(defs.get(name),buyer,null);}
        Datum resolve(String text,Node here,Node prev){if(text.equals("this"))return new NodeValue(here);if(text.equals("prev"))return prev==null?null:new NodeValue(prev);if(text.equals("gold"))return new NumberValue(here.gold);if(text.equals("yes")||text.equals("no"))return new NumberValue(text.equals("yes")?1:0);
            if(text.matches("-?[0-9]+(?:\\.[0-9]+)?"))return new NumberValue(Double.parseDouble(text));String[]parts=text.split("\\.var:");Datum d;
            if(parts[0].equals("global_var:xfm_exchange"))d=new NodeValue(exchange);else if(parts[0].startsWith("scope:"))d=scopes.get(parts[0].substring(6));else if(parts[0].startsWith("var:"))d=here.vars.get(parts[0].substring(4));else if(defs.containsKey(text))return new NumberValue(value(text,here,prev));else throw new AssertionError("unknown path "+text);
            for(int i=1;i<parts.length;i++)d=d instanceof NodeValue n?n.value().vars.get(parts[i]):null;return d;}
        double number(String text,Node here,Node prev){Datum d=resolve(text,here,prev);if(!(d instanceof NumberValue n))throw new AssertionError("not a number "+text);return n.value();}
        double value(String name,Node here,Node prev){return evaluate(defs.get(name),here,prev,0);}
        double evaluate(Block b,Node here,Node prev,double result){for(Entry e:b.entries()){if(e.key().equals("floor")){result=Math.floor(result);continue;}double n=e.value()instanceof Block child?evaluate(child,here,prev,0):number(atom(e.value()),here,prev);result=switch(e.key()){case "value"->n;case "add"->result+n;case "subtract"->result-n;case "multiply"->result*n;case "divide"->result/n;case "max"->Math.min(result,n);case "min"->Math.max(result,n);default->throw new AssertionError("unknown value operation "+e.key());};}return result;}
        boolean matches(Block b,Node here,Node prev){return b.entries().stream().allMatch(e->check(e,here,prev));}
        boolean check(Entry e,Node here,Node prev){String k=e.key();if(k.equals("AND"))return matches((Block)e.value(),here,prev);if(k.equals("OR"))return ((Block)e.value()).entries().stream().anyMatch(x->check(x,here,prev));if(k.equals("NOT"))return !matches((Block)e.value(),here,prev);if(k.equals("exists"))return resolve(atom(e.value()),here,prev)!=null;if(k.equals("has_variable"))return here.vars.containsKey(atom(e.value()));if(k.equals("story_type"))return here.type.equals(atom(e.value()));
            if(k.equals("any_in_list")){Block child=(Block)e.value();String name=atom(child.entries().stream().filter(x->x.key().equals("variable")).findFirst().orElseThrow().value());return here.lists.getOrDefault(name,List.of()).stream().anyMatch(n->matches(without(child,"variable"),n,here));}
            if(k.endsWith("_trigger")){Block trigger=defs.get(k);if(trigger==null)throw new AssertionError("unknown trigger "+k);return matches(trigger,here,prev)==atom(e.value()).equals("yes");}
            if(e.value()instanceof Block child){Datum d=resolve(k,here,prev);return d instanceof NodeValue n&&matches(child,n.value(),here);}
            Datum left=switch(k){case "is_ai"->new NumberValue(here.ai?1:0);case "is_alive"->new NumberValue(here.alive?1:0);case "is_adult"->new NumberValue(here.adult?1:0);default->resolve(k,here,prev);};Datum right=resolve(atom(e.value()),here,prev);if(left==null||right==null)return false;
            if(left instanceof NumberValue l&&right instanceof NumberValue r)return switch(e.op()){case "="->l.value()==r.value();case "!="->l.value()!=r.value();case ">="->l.value()>=r.value();case "<="->l.value()<=r.value();case ">"->l.value()>r.value();case "<"->l.value()<r.value();default->throw new AssertionError(e.op());};if(!Set.of("=","!=").contains(e.op()))throw new AssertionError("reference operation "+e.op());return e.op().equals("=")?left.equals(right):!left.equals(right);}
        double weight(Block chance){double n=0;for(Entry e:chance.entries()){if(e.key().equals("base"))n=Double.parseDouble(atom(e.value()));else if(e.key().equals("modifier")){Block b=(Block)e.value();if(matches(without(b,"add"),buyer,null))n+=Double.parseDouble(atom(b.entries().stream().filter(x->x.key().equals("add")).findFirst().orElseThrow().value()));}else throw new AssertionError(e.key());}return n;}
        void executeOption(){execute(without(accept,"name","trigger","ai_chance"),buyer,null);}
        void execute(Block b,Node here,Node prev){boolean chain=false;for(Entry e:b.entries()){if(e.key().equals("if")){Block child=(Block)e.value();chain=matches(child.block("limit"),here,prev);if(chain)execute(without(child,"limit"),here,prev);}else if(e.key().equals("else")){if(!chain)execute((Block)e.value(),here,prev);chain=false;}else if(e.key().equals("xfm_market_ui_otc_accept_effect")){acceptCalls++;here.number("xfm_issuer_result",publicAcceptSucceeds?1:0);}else if(e.key().equals("set_variable")){Block child=(Block)e.value();String name=atom(child.entries().stream().filter(x->x.key().equals("name")).findFirst().orElseThrow().value());String input=atom(child.entries().stream().filter(x->x.key().equals("value")).findFirst().orElseThrow().value());here.vars.put(name,resolve(input,here,prev));}else throw new AssertionError("unknown effect "+e.key());}}
    }
}
