package org.xar.ck3.markets.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;

/** Runs the actual public topup, purpose guard, real funding, escrow mutation and arrears scripts.
 * Account initialization, creation, registration and real gold funding use production AST; there are no account-selection ports.
 * The strict subset interpreter is adapted from CoinResidentCapacityScriptTest; it is not CK3.
 */
final class MaintenancePurposeTopupScriptTest {
    private static final Path SOURCE=Path.of(System.getProperty("xfm.source",".."));
    private static final Path BASE=Path.of(System.getProperty("xfm.base",SOURCE.toString()));
    private static final List<String> INPUTS=List.of(
        "scripted_effects/xfm_finance_maintenance.txt",
        "scripted_triggers/xfm_finance_maintenance_triggers.txt",
        "script_values/xfm_finance_maintenance_values.txt",
        "scripted_effects/xfm_issuer_maintenance.txt",
        "scripted_effects/xfm_finance_cash.txt",
        "scripted_effects/xfm_finance_init.txt",
        "scripted_effects/xfm_finance_reserve.txt",
        "scripted_triggers/xfm_finance_triggers.txt",
        "scripted_triggers/xfm_issuer_triggers.txt",
        "script_values/xfm_finance_values.txt",
        "script_values/xfm_issuer_values.txt");

    private record Fixture(Vm vm,Node coin,Node issuer,Node escrow) {}
    private static Fixture fixture()throws IOException {
        Vm v=vm();v.wallet.num("xfm_system_account",0).num("xfm_free_cents",1000000);
        v.actor.num("gold",0);
        Node c=v.coin(11,1).num("xfm_initial_maintenance_cents",60);
        Node issuer=c.ref("xfm_issuer_account").num("xfm_system_account",1).num("xfm_reserved_cents",10).ref("xfm_legal_entity",c);
        Node r=v.node("xfm_finance_reservation").num("xfm_reservation_id",7).num("xfm_status",1).num("xfm_remaining_cents",10).ref("xfm_account",issuer);
        issuer.list("xfm_reservations").add(r);c.ref("xfm_maintenance_reservation",r);
        v.actor.ref("xfm_selected_coin",c);v.exchange.num("xfm_next_reservation_id",7).num("xfm_fee_cents",0);
        return new Fixture(v,c,issuer,r);
    }
    private static long total(Fixture f){return f.vm.cashStock()+f.vm.exchange.n("xfm_fee_cents")+f.vm.actor.n("gold")*100;}
    private static long reservations(Fixture f){return f.vm.nodes.stream().filter(n->n.type.equals("xfm_finance_reservation")).count();}
    private static void topup(Fixture f){f.vm.run("xfm_listing_topup_effect",f.vm.actor);}

    @Test void oneThousandRealPaidTopupsRetainOnePurposeStoryAndPermanentId()throws IOException {
        Fixture f=fixture();long before=total(f);int stories=f.vm.nodes.size();
        for(int i=0;i<1000;i++){topup(f);assertEquals(1,f.vm.actor.n("xfm_topup_result"));}
        assertEquals(60010,f.escrow.n("xfm_remaining_cents"));assertEquals(60010,f.issuer.n("xfm_reserved_cents"));
        assertEquals(940000,f.vm.wallet.n("xfm_free_cents"));assertEquals(before,total(f));
        assertEquals(1,reservations(f));assertEquals(stories,f.vm.nodes.size());assertEquals(7,f.escrow.n("xfm_reservation_id"));
        assertEquals(7,f.vm.exchange.n("xfm_next_reservation_id"));assertSame(f.escrow,f.coin.ref("xfm_maintenance_reservation"));
        assertEquals(List.of(f.escrow),f.issuer.list("xfm_reservations"));assertEquals(0,f.vm.ended);
    }
    @Test void actualFeeConsumptionThenRefillRestartsOnlyTheSameZeroEscrow()throws IOException {
        Fixture f=fixture();long before=total(f);f.escrow.num("xfm_request_cents",10);
        f.vm.run("xfm_finance_fee_reserved_effect",f.escrow);assertEquals(2,f.escrow.n("xfm_status"));
        topup(f);assertEquals(1,f.escrow.n("xfm_status"));assertEquals(60,f.escrow.n("xfm_remaining_cents"));
        assertEquals(60,f.issuer.n("xfm_reserved_cents"));assertEquals(10,f.vm.exchange.n("xfm_fee_cents"));
        assertEquals(before,total(f));assertEquals(1,reservations(f));
    }
    @Test void actualImplicitGoldDepositFundsOnlyTheRequiredDifferenceBeforeEscrow()throws IOException {
        Fixture f=fixture();f.vm.wallet.num("xfm_free_cents",10);f.vm.actor.num("gold",1);
        long before=total(f);topup(f);
        assertEquals(0,new BigDecimal("0.5").compareTo(((Num)f.vm.actor.vars.get("gold")).value()));
        assertEquals(0,f.vm.wallet.n("xfm_free_cents"));assertEquals(70,f.escrow.n("xfm_remaining_cents"));
        BigDecimal exact=BigDecimal.valueOf(f.vm.cashStock());
        assertEquals(0,BigDecimal.valueOf(before).compareTo(exact.add(BigDecimal.valueOf(f.vm.exchange.n("xfm_fee_cents"))).add(((Num)f.vm.actor.vars.get("gold")).value().multiply(BigDecimal.valueOf(100)))));
        assertEquals(1,reservations(f));assertEquals(1,f.vm.actor.n("xfm_topup_result"));
    }
    @Test void realArrearsFeeIsConsumedOnceFromTheSameEscrowWithConservedTotal()throws IOException {
        Fixture f=fixture();f.coin.num("xfm_maintenance_arrears_cents",25);long before=total(f);topup(f);
        assertEquals(0,f.coin.n("xfm_maintenance_arrears_cents"));assertEquals(45,f.escrow.n("xfm_remaining_cents"));
        assertEquals(45,f.issuer.n("xfm_reserved_cents"));assertEquals(25,f.vm.exchange.n("xfm_fee_cents"));assertEquals(before,total(f));
        topup(f);assertEquals(25,f.vm.exchange.n("xfm_fee_cents"));assertEquals(105,f.escrow.n("xfm_remaining_cents"));
    }
    @Test void missingCurrentPurposeOrLegalEntityOrIssuerFailsBeforeCashOrGoldMoves()throws IOException {
        for(String missing:List.of("xfm_maintenance_reservation","xfm_issuer_account","xfm_coin_id","xfm_initial_maintenance_cents","legal-entity")){
            Fixture f=fixture();f.vm.wallet.num("xfm_free_cents",0);f.vm.actor.num("gold",5);
            if(missing.equals("legal-entity"))f.issuer.vars.remove("xfm_legal_entity");else f.coin.vars.remove(missing);
            long before=total(f);topup(f);assertEquals(before,total(f),missing);
            assertEquals(0,f.vm.wallet.n("xfm_free_cents"));assertEquals(5,f.vm.actor.n("gold"));assertEquals(10,f.escrow.n("xfm_remaining_cents"));assertEquals(0,f.vm.actor.n("xfm_topup_result"));
        }
    }
    @Test void everyForeignSourceOrClaimBindingRejectsWithoutReplacingOrDeletingIt()throws IOException {
        for(String field:List.of("xfm_source_spot_order","xfm_futures_position","xfm_source_futures_order","xfm_subscription_coin","xfm_subscription_buyer","xfm_pending_payment","xfm_debt_receipt_1","xfm_debt_receipt_2","xfm_debt_receipt_3","xfm_debt_receipt_4","xfm_claim_source","xfm_external_refs")){
            Fixture f=fixture();f.escrow.num(field,1);long before=total(f);topup(f);
            assertEquals(0,f.vm.actor.n("xfm_topup_result"),field);assertEquals(before,total(f),field);
            assertEquals(10,f.escrow.n("xfm_remaining_cents"));assertSame(f.escrow,f.coin.ref("xfm_maintenance_reservation"));assertEquals(1,reservations(f));assertEquals(0,f.vm.ended);
        }
        Fixture f=fixture();f.escrow.list("xfm_claims").add(f.vm.node("claim"));topup(f);assertEquals(0,f.vm.actor.n("xfm_topup_result"));assertEquals(10,f.escrow.n("xfm_remaining_cents"));
    }
    @Test void sharedBondMakerWrongAccountAndWrongPurposePinsFailClosed()throws IOException {
        for(String kind:List.of("bond","maker","wrong-account","partial-pin","wrong-coin","wrong-id","wrong-version")){
            Fixture f=fixture();
            switch(kind){
                case "bond"->f.coin.ref("xfm_bond_reservation",f.escrow);
                case "maker"->f.coin.ref("xfm_maker_reservation",f.escrow);
                case "wrong-account"->f.escrow.ref("xfm_account",f.vm.wallet);
                case "partial-pin"->f.escrow.num("xfm_maintenance_purpose_v1",1);
                default->{f.escrow.num("xfm_maintenance_purpose_v1",kind.equals("wrong-version")?2:1).ref("xfm_maintenance_coin",kind.equals("wrong-coin")?f.vm.coin(12,1):f.coin).num("xfm_maintenance_coin_id",kind.equals("wrong-id")?12:11);}
            }
            long before=total(f);topup(f);assertEquals(0,f.vm.actor.n("xfm_topup_result"),kind);assertEquals(before,total(f),kind);assertEquals(10,f.escrow.n("xfm_remaining_cents"));
        }
    }
    @Test void archivedFrozenMalformedOrUnbackedEscrowFailsBeforeSponsorFunding()throws IOException {
        for(String kind:List.of("archived","issuer-frozen","payer-frozen","fractional-id","fractional-cents","negative","unbacked","status","upper-bound")){
            Fixture f=fixture();f.vm.wallet.num("xfm_free_cents",0);f.vm.actor.num("gold",5);
            switch(kind){
                case "archived"->f.coin.num("xfm_listing_state",7);case "issuer-frozen"->f.issuer.num("xfm_account_frozen",1);
                case "payer-frozen"->f.vm.wallet.num("xfm_account_frozen",1);
                case "fractional-id"->f.escrow.num("xfm_reservation_id",7.5);case "fractional-cents"->f.escrow.num("xfm_remaining_cents",0.5);
                case "negative"->f.escrow.num("xfm_remaining_cents",-1);case "unbacked"->f.issuer.num("xfm_reserved_cents",9);
                case "status"->f.escrow.num("xfm_status",3);case "upper-bound"->{f.escrow.num("xfm_remaining_cents",99999980);f.issuer.num("xfm_reserved_cents",99999980);}
                default->throw new AssertionError(kind);
            }
            long before=total(f);topup(f);assertEquals(before,total(f),kind);assertEquals(0,f.vm.wallet.n("xfm_free_cents"));assertEquals(5,f.vm.actor.n("gold"));assertEquals(0,f.vm.actor.n("xfm_topup_result"),kind);
        }
    }
    @Test void insufficientSponsorCashAndGoldLeavesAllExistingRightsUntouched()throws IOException {
        Fixture f=fixture();f.vm.wallet.num("xfm_free_cents",59);long before=total(f);topup(f);
        assertEquals(0,f.vm.actor.n("xfm_topup_result"));assertEquals(59,f.vm.wallet.n("xfm_free_cents"));assertEquals(10,f.escrow.n("xfm_remaining_cents"));assertEquals(before,total(f));assertEquals(1,reservations(f));
    }
    @Test void historicalZeroReservationsAreRetainedWithoutBeingSelectedOrCompacted()throws IOException {
        Fixture f=fixture();Node old=f.vm.node("xfm_finance_reservation").num("xfm_reservation_id",3).num("xfm_status",2).num("xfm_remaining_cents",0).ref("xfm_account",f.issuer);
        f.issuer.list("xfm_reservations").add(old);topup(f);
        assertEquals(List.of(f.escrow,old),f.issuer.list("xfm_reservations"));assertEquals(2,reservations(f));assertEquals(0,old.n("xfm_remaining_cents"));assertEquals(0,f.vm.ended);
    }

    private static BigDecimal exactTotal(Fixture f){
        return BigDecimal.valueOf(f.vm.cashStock()+f.vm.exchange.n("xfm_fee_cents"))
                .add(((Num)f.vm.actor.vars.get("gold")).value().multiply(BigDecimal.valueOf(100)));
    }
    private static Map<String,List<Node>> snapshotLists(Node n){
        Map<String,List<Node>> out=new HashMap<>();n.lists.forEach((k,v)->out.put(k,List.copyOf(v)));return Map.copyOf(out);
    }
    private static Node makeWalletForeign(Fixture f){
        Node stranger=f.vm.node("character");
        f.vm.wallet.ref("xfm_holder",stranger).ref("xfm_beneficial_owner",stranger)
                .num("xfm_free_cents",333).num("xfm_reserved_cents",444).num("xfm_account_id",8);
        f.vm.wallet.list("xfm_orders").add(f.vm.node("foreign-existing-order"));
        return f.vm.wallet;
    }
    @Test void directHelperRejectsWrongHolderWithoutCorrectingOrPayingFromThatWallet()throws IOException{
        Fixture f=fixture();Node foreign=makeWalletForeign(f);f.vm.actor.num("gold",1);
        Map<String,Datum>before=Map.copyOf(foreign.vars);Map<String,List<Node>>beforeLists=snapshotLists(foreign);BigDecimal stock=exactTotal(f);
        f.vm.run("xfm_finance_maintenance_topup_effect",f.vm.actor);
        assertEquals(0,f.vm.actor.n("xfm_topup_result"));assertSame(foreign,f.vm.actor.ref("xfm_account"));
        assertEquals(before,foreign.vars);assertEquals(beforeLists,snapshotLists(foreign));assertEquals(stock,exactTotal(f));assertEquals(0,f.vm.createdAccounts);
        assertEquals(10,f.escrow.n("xfm_remaining_cents"));
    }
    @Test void coldPublicEntryCreatesAndRegistersItsOwnAccountThenDepositsActualOwnerGold()throws IOException{
        Fixture f=fixture();Node foreign=makeWalletForeign(f);Map<String,Datum>outside=Map.copyOf(foreign.vars);Map<String,List<Node>>outsideLists=snapshotLists(foreign);
        f.vm.actor.vars.remove("xfm_account");f.vm.actor.vars.remove("xfm_active_account");
        f.vm.actor.num("gold",1);f.vm.exchange.num("xfm_next_account_id",8);
        BigDecimal before=exactTotal(f);long reservations=reservations(f);topup(f);
        Node own=f.vm.actor.ref("xfm_account");assertNotNull(own);assertNotSame(foreign,own);
        assertEquals(1,f.vm.createdAccounts);assertEquals(9,own.n("xfm_account_id"));assertEquals(9,f.vm.exchange.n("xfm_next_account_id"));
        assertEquals(0,own.n("xfm_system_account"));assertSame(f.vm.actor,own.ref("xfm_holder"));
        assertSame(f.vm.actor,own.ref("xfm_beneficial_owner"));assertEquals(0,own.n("xfm_free_cents"));assertEquals(0,own.n("xfm_reserved_cents"));
        assertEquals(List.of(own),f.vm.global("xfm_account_registry"));assertEquals(List.of(own),f.vm.actor.list("xfm_accounts"));
        assertEquals(0,new BigDecimal("0.4").compareTo(((Num)f.vm.actor.vars.get("gold")).value()));
        assertEquals(70,f.escrow.n("xfm_remaining_cents"));assertEquals(70,f.issuer.n("xfm_reserved_cents"));
        assertEquals(0,before.compareTo(exactTotal(f)));assertEquals(outside,foreign.vars);assertEquals(outsideLists,snapshotLists(foreign));assertEquals(reservations,reservations(f));
        assertSame(f.escrow,f.coin.ref("xfm_maintenance_reservation"));assertEquals(7,f.escrow.n("xfm_reservation_id"));
        assertEquals(1,f.vm.actor.n("xfm_topup_result"));
    }
    @Test void publicWrongOwnerPointerIsRepairedByRealProducerWithoutWritingTheForeignWallet()throws IOException{
        Fixture f=fixture();Node foreign=makeWalletForeign(f);Map<String,Datum>outside=Map.copyOf(foreign.vars);Map<String,List<Node>>outsideLists=snapshotLists(foreign);
        f.vm.actor.ref("xfm_active_account",foreign).num("gold",1);f.vm.exchange.num("xfm_next_account_id",8);
        BigDecimal before=exactTotal(f);topup(f);Node own=f.vm.actor.ref("xfm_account");
        assertNotNull(own);assertNotSame(foreign,own);assertSame(f.vm.actor,own.ref("xfm_holder"));
        assertEquals(1,f.vm.createdAccounts);assertEquals(9,own.n("xfm_account_id"));assertEquals(1,f.vm.actor.n("xfm_topup_result"));
        assertEquals(List.of(own),f.vm.global("xfm_account_registry"));assertEquals(outside,foreign.vars);assertEquals(outsideLists,snapshotLists(foreign));
        assertSame(foreign,f.vm.actor.ref("xfm_active_account"),"the topup public API preserves the old active-wallet selector; it pays only its repaired primary");
        assertEquals(0,before.compareTo(exactTotal(f)));assertEquals(70,f.escrow.n("xfm_remaining_cents"));
    }
    @Test void actualColdAccountCreationFailureLeavesOwnerGoldForeignWalletAndEscrowUnchanged()throws IOException{
        Fixture f=fixture();Node foreign=makeWalletForeign(f);Map<String,Datum>outside=Map.copyOf(foreign.vars);Map<String,List<Node>>outsideLists=snapshotLists(foreign);
        f.vm.actor.num("gold",1);f.vm.exchange.num("xfm_next_account_id",8);
        f.vm.scopes.put("xfm_created_account",foreign);f.vm.scopes.put("xfm_account",foreign);
        f.vm.failNextAccountCreation=true;BigDecimal before=exactTotal(f);topup(f);
        assertNull(f.vm.actor.ref("xfm_account"));assertEquals(0,f.vm.createdAccounts);
        assertEquals(8,f.vm.exchange.n("xfm_next_account_id"));assertTrue(f.vm.global("xfm_account_registry").isEmpty());
        assertEquals(0,f.vm.actor.n("xfm_topup_result"));assertEquals(before,exactTotal(f));assertEquals(outside,foreign.vars);assertEquals(outsideLists,snapshotLists(foreign));
        assertEquals(10,f.escrow.n("xfm_remaining_cents"));assertEquals(10,f.issuer.n("xfm_reserved_cents"));assertEquals(1,reservations(f));
    }

    private static Vm vm()throws IOException{
        Map<String,Block>defs=new LinkedHashMap<>();for(String rel:INPUTS)for(Entry e:parse(Files.readString(Files.exists(SOURCE.resolve("common").resolve(rel))?SOURCE.resolve("common").resolve(rel):BASE.resolve("common").resolve(rel))).entries())defs.put(e.key(),e.value() instanceof Block b?b:new Block(List.of(new Entry("value","=",e.value()))));return new Vm(defs);
    }
    private sealed interface Expr permits Atom,Block{}
    private record Atom(String text)implements Expr{}
    private record Entry(String key,String op,Expr value){}
    private record Block(List<Entry>entries)implements Expr{Block{entries=List.copyOf(entries);}Block block(String key){return (Block)field(this,key);}}
    private sealed interface Datum permits Num,Node,Text{}
    private record Num(BigDecimal value)implements Datum{}
    private record Text(String value)implements Datum{}
    private static final class Node implements Datum{
        final String type;final Map<String,Datum>vars=new HashMap<>();final Map<String,List<Node>>lists=new HashMap<>();Node owner;boolean ai=true;
        Node(String type){this.type=type;}Node num(String k,double n){vars.put(k,new Num(BigDecimal.valueOf(n)));return this;}Node ref(String k,Node n){vars.put(k,n);return this;}Node ref(String k){return vars.get(k) instanceof Node n?n:null;}
        long n(String k){return vars.get(k) instanceof Num x?x.value().longValueExact():0;}List<Node>list(String k){return lists.computeIfAbsent(k,ignored->new ArrayList<>());}
    }
    private record Frame(Node here,Node previous,Node root){Frame enter(Node n){return new Frame(n,here,root);}}
    private static final class Vm{
        final Map<String,Block>defs;final Map<String,Datum>scopes=new HashMap<>();final Map<String,List<Node>>globals=new HashMap<>();final List<Node>nodes=new ArrayList<>();
        final Node actor,exchange,wallet;int globalVisits,ended,globalDepth,predicateListVisits,createdAccounts;boolean failNextAccountCreation;
        Vm(Map<String,Block>d){defs=d;actor=node("character");exchange=node("xfm_finance_exchange");exchange.owner=actor;exchange.num("xfm_day",1).num("xfm_next_coin_id",0).num("xfm_coin_count",0).num("xfm_registered_coin_count",0).num("xfm_pending_coin_count",0);wallet=account();actor.ref("xfm_account",wallet).ref("xfm_active_account",wallet);}
        Node node(String t){Node n=new Node(t);n.owner=actor;nodes.add(n);return n;}
        Node account(){return node("xfm_finance_account").ref("xfm_holder",actor).num("xfm_free_cents",0).num("xfm_reserved_cents",0).num("xfm_account_frozen",0).num("xfm_inheritance_state",0).num("xfm_holdings_count",0);}
        Node coin(int id,int state){return node("xfm_finance_coin").num("xfm_coin_id",id).num("xfm_listing_state",state).num("xfm_trading_open",0).num("xfm_supply_units",0).num("xfm_entity_type",1).num("xfm_unpaid_debt_cents",0).num("xfm_promises_due_cents",0).num("xfm_maintenance_arrears_cents",0).num("xfm_settlement_price_pending",0).num("xfm_unresolved_claim_count",0).num("xfm_asset_age",0).num("xfm_founder_locked_units",0).ref("xfm_controller",actor).ref("xfm_issuer_account",account()).ref("xfm_founder_account",account());}
        Node failedOffer(){return failedOffer(1);}
        Node failedOffer(int id){Node c=coin(id,6).num("xfm_supply_units",15000).num("xfm_founder_locked_units",2500);for(int i=0;i<2;i++){Node a=c.ref(i==0?"xfm_issuer_account":"xfm_founder_account"),p=node("xfm_finance_position").ref("xfm_account",a).ref("xfm_coin",c).num("xfm_quantity_units",i==0?12500:2500).num("xfm_reserved_units",0).num("xfm_counted",1);a.num("xfm_holdings_count",1).list("xfm_positions").add(p);c.list("xfm_holders").add(p);}c.list("xfm_subscriptions").add(node("xfm_finance_reservation").num("xfm_subscription_state",3).num("xfm_remaining_cents",0));hot(c);return c;}
        List<Node>global(String name){return globals.computeIfAbsent(name,k->new ArrayList<>());}void hot(Node c){global("xfm_coin_registry").add(c);}
        void queueAndFlush(Node c){run("xfm_registry_queue_retire_effect",c);run("xfm_registry_flush_retire_effect",exchange);}
        Map<Node,Map<String,Datum>>copyVars(){Map<Node,Map<String,Datum>>result=new HashMap<>();for(Node n:nodes)result.put(n,Map.copyOf(n.vars));return result;}
        long cashStock(){return nodes.stream().filter(n->n.type.equals("xfm_finance_account")).mapToLong(n->n.n("xfm_free_cents")+n.n("xfm_reserved_cents")).sum();}
        void run(String name,Node n){exec(defs.get(name),new Frame(n,null,n));}
        Datum resolve(String token,Frame f){try{return new Num(new BigDecimal(token));}catch(NumberFormatException ignored){}int dot=token.indexOf('.');if(dot>0){Datum base=resolve(token.substring(0,dot),f);return base instanceof Node n?resolve(token.substring(dot+1),f.enter(n)):null;}if(token.equals("gold"))return f.here().vars.getOrDefault("gold",new Num(BigDecimal.ZERO));if(token.equals("this"))return f.here();if(token.equals("prev"))return f.previous();if(token.equals("root"))return f.root();if(token.equals("story_owner"))return f.here().owner;if(Set.of("holder","house_head","dynast","religious_head").contains(token))return f.here().vars.get(token);if(token.equals("global_var:xfm_exchange"))return exchange;if(token.startsWith("scope:"))return scopes.get(token.substring(6));if(token.startsWith("var:"))return f.here().vars.get(token.substring(4));if(token.equals("xfm_config_registration_capacity_value"))return new Num(BigDecimal.valueOf(16384));if(token.equals("xfm_config_pending_capacity_value"))return new Num(BigDecimal.valueOf(240));if(defs.containsKey(token))return new Num(value(defs.get(token),f,BigDecimal.ZERO));return new Text(token);}
        BigDecimal number(Datum x){if(x==null)return BigDecimal.ZERO;if(x instanceof Num n)return n.value();throw new IllegalArgumentException("not a number "+x);}
        Datum eval(Expr x,Frame f){return x instanceof Block b?new Num(value(b,f,BigDecimal.ZERO)):resolve(atom(x),f);}
        BigDecimal value(Block b,Frame f,BigDecimal start){BigDecimal n=start;boolean chain=false;for(Entry e:b.entries()){String k=e.key();if(k.equals("if")||k.equals("else_if")){Block child=(Block)e.value();boolean yes=(!k.equals("else_if")||!chain)&&test(child.block("limit"),f);if(k.equals("if"))chain=false;if(yes){n=value(without(child,"limit"),f,n);chain=true;}continue;}if(k.equals("else")){if(!chain)n=value((Block)e.value(),f,n);chain=false;continue;}if(k.equals("every_in_list")){Block a=(Block)e.value();for(Node child:List.copyOf(f.here().list(atom(field(a,"variable")))))if(test(optionalLimit(a),f.enter(child)))n=value(without(a,"variable","limit"),f.enter(child),n);continue;}if(k.equals("floor")){n=n.setScale(0,RoundingMode.FLOOR);continue;}if(k.equals("ceiling")){n=n.setScale(0,RoundingMode.CEILING);continue;}BigDecimal x=number(eval(e.value(),f));n=switch(k){case "value"->x;case "add"->n.add(x);case "subtract"->n.subtract(x);case "multiply"->n.multiply(x);case "divide"->n.divide(x,18,RoundingMode.HALF_EVEN);case "min"->n.max(x);case "max"->n.min(x);default->throw new IllegalArgumentException("value "+k);};}return n;}
        boolean test(Block b,Frame f){
            Boolean conditional=null;
            for(Entry e:b.entries()){
                if(e.key().equals("trigger_if")){Block a=(Block)e.value();conditional=test(a.block("limit"),f);if(conditional&&!test(without(a,"limit"),f))return false;continue;}
                if(e.key().equals("trigger_else")){if(conditional==null)throw new IllegalArgumentException("trigger_else without trigger_if");if(!conditional&&!test((Block)e.value(),f))return false;conditional=null;continue;}
                if(!check(e,f))return false;
            }
            return true;
        }
        boolean check(Entry e,Frame f){String k=e.key();if(k.equals("always"))return atom(e.value()).equals("yes");if(k.equals("AND"))return test((Block)e.value(),f);if(k.equals("OR"))return ((Block)e.value()).entries().stream().anyMatch(x->check(x,f));if(k.equals("NOT"))return ((Block)e.value()).entries().stream().noneMatch(x->check(x,f));if(k.equals("exists"))return resolve(atom(e.value()),f)!=null;if(k.equals("has_variable"))return f.here().vars.containsKey(atom(e.value()));if(k.equals("story_type"))return f.here().type.equals(atom(e.value()));if(k.equals("is_ai"))return f.here().ai==atom(e.value()).equals("yes");if(k.equals("is_alive")||k.equals("is_adult"))return atom(e.value()).equals("yes");if(k.equals("trigger_if")){Block a=(Block)e.value();return !test(a.block("limit"),f)||test(without(a,"limit"),f);}if(k.equals("any_in_list")){Block a=(Block)e.value();for(Node n:f.here().lists.getOrDefault(atom(field(a,"variable")),List.of())){predicateListVisits++;if(test(without(a,"variable"),f.enter(n)))return true;}return false;}if(k.equals("is_target_in_variable_list")||k.equals("is_target_in_global_variable_list")){Block a=(Block)e.value();List<Node>list=k.equals("is_target_in_global_variable_list")?global(atom(field(a,"name"))):f.here().list(atom(field(a,"name")));return list.contains(eval(field(a,"target"),f));}if(k.endsWith("_trigger")&&defs.containsKey(k))return test(defs.get(k),f);Datum left=resolve(k,f);if(e.value() instanceof Block b&&left instanceof Node n)return test(b,f.enter(n));Datum right=eval(e.value(),f);if(left instanceof Num a&&right instanceof Num b){int c=a.value().compareTo(b.value());return switch(e.op()){case "="->c==0;case "!="->c!=0;case ">"->c>0;case "<"->c<0;case ">="->c>=0;case "<="->c<=0;default->throw new IllegalArgumentException(e.op());};}return e.op().equals("=")?Objects.equals(left,right):e.op().equals("!=")&&!Objects.equals(left,right);}
        void exec(Block b,Frame f){if(b==null)throw new IllegalArgumentException("missing definition");boolean chain=false;for(Entry e:b.entries()){String k=e.key();if(k.equals("if")||k.equals("else_if")){Block a=(Block)e.value();boolean yes=(!k.equals("else_if")||!chain)&&test(a.block("limit"),f);if(k.equals("if"))chain=false;if(yes){exec(without(a,"limit"),f);chain=true;}continue;}if(k.equals("else")){if(!chain)exec((Block)e.value(),f);chain=false;continue;}if(k.equals("save_scope_value_as")){Block a=(Block)e.value();scopes.put(atom(field(a,"name")),eval(field(a,"value"),f));continue;}if(k.equals("remove_short_term_gold")||k.equals("add_gold")){BigDecimal amount=number(eval(e.value(),f)),old=number(f.here().vars.get("gold"));f.here().vars.put("gold",new Num(k.equals("add_gold")?old.add(amount):old.subtract(amount)));continue;}if(k.equals("save_scope_as")){scopes.put(atom(e.value()),f.here());continue;}if(k.equals("clear_saved_scope")){scopes.remove(atom(e.value()));continue;}if(k.equals("remove_variable")){f.here().vars.remove(atom(e.value()));continue;}if(k.equals("set_variable")||k.equals("change_variable")){Block a=(Block)e.value();String name=atom(field(a,"name"));if(k.equals("set_variable"))f.here().vars.put(name,eval(field(a,"value"),f));else{boolean add=a.entries().stream().anyMatch(x->x.key().equals("add"));BigDecimal amount=number(eval(field(a,add?"add":"subtract"),f)),old=number(f.here().vars.get(name));f.here().vars.put(name,new Num(add?old.add(amount):old.subtract(amount)));}continue;}if(k.equals("clear_variable_list")){f.here().list(atom(e.value())).clear();continue;}if(Set.of("add_to_variable_list","add_to_global_variable_list","remove_list_global_variable").contains(k)){Block a=(Block)e.value();String name=atom(field(a,"name"));Node target=(Node)eval(field(a,"target"),f);List<Node>list=k.equals("add_to_variable_list")?f.here().list(name):global(name);if(k.equals("remove_list_global_variable")){if(globalDepth>0)throw new IllegalStateException("mutated live list inside traversal");list.remove(target);}else list.add(target);continue;}if(Set.of("every_in_list","every_in_global_list","random_in_list","random_in_global_list").contains(k)){Block a=(Block)e.value();boolean global=k.contains("global");List<Node>list=List.copyOf(global?global(atom(field(a,"variable"))):f.here().list(atom(field(a,"variable"))));if(global)globalDepth++;for(Node n:list){if(global)globalVisits++;if(test(optionalLimit(a),f.enter(n))){exec(without(a,"variable","limit"),f.enter(n));if(k.startsWith("random"))break;}}if(global)globalDepth--;continue;}if(k.equals("create_story")){Block a=(Block)e.value();String type=atom(field(a,"type"));if(type.equals("xfm_finance_account")&&failNextAccountCreation){failNextAccountCreation=false;continue;}Node n=node(type);if(type.equals("xfm_finance_account"))createdAccounts++;n.owner=f.here();scopes.put(atom(field(a,"save_scope_as")),n);continue;}if(k.equals("end_story")){ended++;throw new IllegalStateException("permanent identity was ended");}
            if(Set.of("xfm_oracle_init_coin_effect","xfm_spot_init_history_effect","xfm_issuer_adopt_legacy_defaults_effect","xfm_issuer_refresh_controller_effect","xfm_issuer_unlock_founder_effect","xfm_issuer_investigate_effect","xfm_issuer_revisit_offer_effect","xfm_news_record_effect").contains(k))continue; // unrelated existing modules, no fake price/cash/units
            if(e.value() instanceof Block a){Datum scope=resolve(k,f);if(!(scope instanceof Node n))throw new IllegalArgumentException("missing scope "+k);exec(a,f.enter(n));continue;}exec(defs.get(k),f);
        }}
    }
    private static String atom(Expr e){return ((Atom)e).text();}
    private static Expr field(Block b,String key){List<Entry>list=b.entries().stream().filter(e->e.key().equals(key)).toList();if(list.size()!=1)throw new IllegalArgumentException("one field "+key);return list.getFirst().value();}
    private static Block optionalLimit(Block b){return b.entries().stream().anyMatch(e->e.key().equals("limit"))?b.block("limit"):new Block(List.of());}
    private static Block without(Block b,String...keys){Set<String>skip=Set.of(keys);return new Block(b.entries().stream().filter(e->!skip.contains(e.key())).toList());}
    private static Block parse(String raw){var m=Pattern.compile("\"(?:\\\\.|[^\"\\\\])*\"|!=|>=|<=|[{}=<>]|[^\\s{}=<>]+").matcher(raw.replace("\ufeff","").replaceAll("(?m)#.*$",""));List<String>tokens=new ArrayList<>();while(m.find())tokens.add(m.group());int[]i={0};Block b=block(tokens,i,false);assertEquals(tokens.size(),i[0]);return b;}
    private static Block block(List<String>t,int[]i,boolean nested){List<Entry>entries=new ArrayList<>();while(i[0]<t.size()){String k=t.get(i[0]++);if(k.equals("}")){assertTrue(nested);return new Block(entries);}String op=t.get(i[0]++),v=t.get(i[0]++);assertTrue(Set.of("=","!=",">=","<=",">","<").contains(op));entries.add(new Entry(k,op,v.equals("{")?block(t,i,true):new Atom(v.startsWith("\"")?v.substring(1,v.length()-1):v)));}assertFalse(nested);return new Block(entries);}
}

