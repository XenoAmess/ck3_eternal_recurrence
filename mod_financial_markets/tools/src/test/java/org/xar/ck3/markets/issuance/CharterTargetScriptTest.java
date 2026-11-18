package org.xar.ck3.markets.issuance;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;

/** Executes actual candidate event/context code and actual production freeze/project/transfer effects.
 * Other business/ensure-account ports are explicitly named fixtures. This is not CK3 execution.
 */
final class CharterTargetScriptTest {
    private static final Path SOURCE=Path.of(System.getProperty("xfm.source",".."));
    private static final List<String> INPUTS=List.of("scripted_effects/xfm_charter_context.txt","scripted_triggers/xfm_charter_context_triggers.txt",
            "scripted_effects/xfm_market_ui_confirmations.txt","scripted_effects/xfm_issuer_governance.txt","scripted_effects/xfm_finance_cash.txt",
            "scripted_triggers/xfm_issuer_triggers.txt","scripted_triggers/xfm_finance_triggers.txt","script_values/xfm_issuer_values.txt","script_values/xfm_finance_values.txt","script_values/xfm_config_values.txt");

    @Test void actualFreezeOfCharterAAfterSelectingBMutatesOnlyAAndRestoresBTicketAndActiveWallet()throws IOException{
        Vm v=fixture();Context a=v.open(v.a);v.actor.ref("xfm_selected_coin",v.b).ref("xfm_active_account",v.otherWallet).num("xfm_order_lots",9).num("xfm_order_limit_cents",777).num("xfm_order_ioc",1);
        v.choose(a,"xfm_issuer_fix_supply");
        assertEquals(0,v.a.n("xfm_mint_permitted"));assertEquals(15000,v.a.n("xfm_maximum_supply_units"));assertEquals(1,v.b.n("xfm_mint_permitted"));
        assertSame(v.b,v.actor.ref("xfm_selected_coin"));assertSame(v.otherWallet,v.actor.ref("xfm_active_account"));
        assertEquals(9,v.actor.n("xfm_order_lots"));assertEquals(777,v.actor.n("xfm_order_limit_cents"));assertEquals(1,v.actor.n("xfm_order_ioc"));
        assertSame(v.a,v.businessTargets.getFirst());
    }

    @Test void actualProjectTransferUsesFrozenPrimaryRecipientNotCurrentlyViewedWalletOrCoinB()throws IOException{
        Vm v=fixture();Context a=v.open(v.a);Node treasury=v.a.ref("xfm_issuer_account"),bTreasury=v.b.ref("xfm_issuer_account");
        v.actor.ref("xfm_selected_coin",v.b).ref("xfm_active_account",v.otherWallet);
        v.choose(a,"xfm_issuer_release_project");
        assertEquals(900,treasury.n("xfm_free_cents"));assertEquals(100,v.primary.n("xfm_free_cents"));assertEquals(1000,bTreasury.n("xfm_free_cents"));assertEquals(0,v.otherWallet.n("xfm_free_cents"));
        assertEquals(100,v.a.n("xfm_project_spent_cents"));assertEquals(0,v.b.n("xfm_project_spent_cents"));assertSame(v.b,v.actor.ref("xfm_selected_coin"));
    }

    @Test void allNineOptionsConsumeFrozenTargetAndNeverCurrentlySelectedB()throws IOException{
        String[] names={"xfm_issuer_complete","xfm_issuer_abort","xfm_issuer_promote","xfm_issuer_fix_supply","xfm_issuer_cancel_unused","xfm_issuer_release_escrow","xfm_issuer_release_project","xfm_issuer_restore_bond","xfm_issuer_restart_maker"};
        for(int i=0;i<names.length;i++){
            Vm v=fixture();v.a.num("xfm_listing_state",i<2?0:(i>=4?6:1));Context a=v.open(v.a);v.actor.ref("xfm_selected_coin",v.b);v.choose(a,names[i]);
            assertEquals(1,v.businessTargets.size(),names[i]);assertSame(v.a,v.businessTargets.getFirst(),names[i]);assertSame(v.b,v.actor.ref("xfm_selected_coin"));assertEquals(1,v.b.n("xfm_mint_permitted"));
        }
    }

    @Test void liveControllerBindingAndExpiredOfferingCannotBorrowAuthorityOrOldDisplayedNumbers()throws IOException{
        Vm v=fixture();Context a=v.open(v.a);v.a.ref("xfm_controller",v.stranger);v.actor.ref("xfm_selected_coin",v.b);v.choose(a,"xfm_issuer_fix_supply");assertTrue(v.businessTargets.isEmpty());
        Vm expired=fixture();expired.a.num("xfm_listing_state",0);Context ticket=expired.open(expired.a);expired.a.num("xfm_listing_state",6);expired.choose(ticket,"xfm_issuer_complete");assertTrue(expired.businessTargets.isEmpty());
        Vm changed=fixture();Context charter=changed.open(changed.a);changed.a.num("xfm_supply_units",16000);changed.actor.num("xfm_view_supply",15000);changed.choose(charter,"xfm_issuer_fix_supply");assertTrue(changed.businessTargets.isEmpty());
        Vm house=fixture();Node entity=new Node("house").ref("house_head",house.actor);house.a.num("xfm_entity_type",2).ref("xfm_bound_entity",entity);Context h=house.open(house.a);entity.ref("house_head",house.stranger);house.choose(h,"xfm_issuer_fix_supply");assertTrue(house.businessTargets.isEmpty(),"stale controller cache cannot override live bound-entity authority");
    }

    @Test void archivedOrMissingCoinFrozenPayerAndChangedCounterpartyRejectBeforeBusiness()throws IOException{
        for(String mutation:List.of("archived","missing","frozen-primary","replaced-primary","foreign-holder","new-treasury","new-maker")){
            Vm v=fixture();Context a=v.open(v.a);
            switch(mutation){
                case "archived"->v.a.num("xfm_listing_state",7);
                case "missing"->a.values().remove("xfm_charter_coin");
                case "frozen-primary"->v.primary.num("xfm_account_frozen",1);
                case "replaced-primary"->v.actor.ref("xfm_account",v.otherWallet);
                case "foreign-holder"->v.primary.ref("xfm_holder",v.stranger);
                case "new-treasury"->v.a.ref("xfm_issuer_account",account(v.actor,44,1));
                case "new-maker"->v.a.ref("xfm_market_maker_account",account(v.actor,45,1));
                default->throw new AssertionError(mutation);
            }
            v.choose(a,"xfm_issuer_fix_supply");assertTrue(v.businessTargets.isEmpty(),mutation);assertEquals(1,v.a.n("xfm_mint_permitted"));
        }
    }

    @Test void newCharterInvalidatesOldWindowAndOldCloseCannotConsumeFreshTicketOrDoubleConfirm()throws IOException{
        Vm v=fixture();Context a=v.open(v.a);Context b=v.open(v.b);v.choose(a,"xfm_issuer_fix_supply");assertTrue(v.businessTargets.isEmpty());
        v.choose(a,"xfm_issuer_close");v.choose(b,"xfm_issuer_fix_supply");assertEquals(1,v.businessTargets.size());assertSame(v.b,v.businessTargets.getFirst());
        v.choose(b,"xfm_issuer_fix_supply");assertEquals(1,v.businessTargets.size(),"consumed ticket is never dispatched twice");assertEquals(1,v.a.n("xfm_mint_permitted"));
    }

    @Test void temporaryConfirmationAliasesCannotRedirectCharterAndOtherPendingSurvivesCompleteOrAbort()throws IOException{
        for(String action:List.of("xfm_issuer_complete","xfm_issuer_abort")){
            Vm v=fixture();v.a.num("xfm_listing_state",0);v.b.num("xfm_listing_state",0);Context a=v.open(v.a);
            v.actor.ref("xfm_selected_coin",v.b).ref("xfm_pending_offer",v.b);v.context=a;v.run("xfm_market_ui_capture_coin_effect",v.actor,null); // a management dialog uses the shared helper after the charter
            v.choose(a,action);assertSame(v.a,v.businessTargets.getFirst());assertSame(v.b,v.actor.ref("xfm_pending_offer"));assertSame(v.b,v.actor.ref("xfm_selected_coin"));
        }
    }

    @Test void restorationClearsInvalidPreviousSelectionsAndDoesNotInventMissingTicketOrWalletState()throws IOException{
        Vm v=fixture();v.a.num("xfm_listing_state",0);Context a=v.open(v.a);v.actor.ref("xfm_selected_coin",v.b).ref("xfm_active_account",v.otherWallet);v.actor.vars.remove("xfm_order_ioc");
        v.onPort=coin->{v.b.num("xfm_listing_state",7);v.otherWallet.ref("xfm_holder",v.stranger);};v.choose(a,"xfm_issuer_complete");
        assertFalse(v.actor.vars.containsKey("xfm_selected_coin"));assertFalse(v.actor.vars.containsKey("xfm_active_account"));assertFalse(v.actor.vars.containsKey("xfm_order_ioc"));
        Vm index=fixture();Context charter=index.open(index.a);Node modelIndex=new Node("xfm_oracle_index");index.actor.ref("xfm_selected_coin",modelIndex);index.choose(charter,"xfm_issuer_fix_supply");assertSame(modelIndex,index.actor.ref("xfm_selected_coin"));
    }

    @Test void displayAndOptionContractUsesEventSnapshotNotActorViewAndNoNewTimePolicy()throws IOException{
        Vm v=fixture();Context a=v.open(v.a);v.actor.num("xfm_view_coin_id",222);v.actor.ref("xfm_selected_coin",v.b);v.context=a;
        assertEquals(1,v.number("scope:xfm_charter_coin_id",v.actor,null));assertEquals(10,v.number("scope:xfm_charter_payer_id",v.actor,null));
        for(String lang:List.of("english","simp_chinese")){
            String s=Files.readString(SOURCE.resolve("localization/"+lang+"/xfm_issuer_l_"+lang+".yml"));
            assertTrue(s.contains("SCOPE.ScriptValue('xfm_charter_coin_id')"));assertTrue(s.contains("SCOPE.ScriptValue('xfm_charter_payer_id')"));assertFalse(s.contains("xfm_view_"));
        }
        String effects=Files.readString(SOURCE.resolve("common/scripted_effects/xfm_charter_context.txt"));assertFalse(effects.contains("days = 7"));assertFalse(effects.contains("expires"));
        for(Entry e:v.event.entries())if(e.key().equals("option")){Block option=(Block)e.value();assertFalse(option.entries().stream().anyMatch(x->x.key().startsWith("xfm_issuer_")&&x.key().endsWith("_effect")),"event cannot directly invoke a mutable-selection business effect");}
    }

    private static Path path(String rel){Path p=SOURCE.resolve("common").resolve(rel);return Files.exists(p)?p:SOURCE.resolve("../baseline/mod_financial_markets/common").resolve(rel).normalize();}
    private static Vm fixture()throws IOException{Map<String,Block>defs=new LinkedHashMap<>();for(String rel:INPUTS)for(Entry e:parse(Files.readString(path(rel))).entries()){Block b=e.value() instanceof Block block?block:new Block(List.of(new Entry("value","=",e.value())));defs.put(e.key(),b);}return new Vm(defs,parse(Files.readString(SOURCE.resolve("events/xfm_issuer_events.txt"))).block("xfm_issuer.100"));}
    private static Node account(Node owner,int id,int system){return new Node("xfm_finance_account").ref("xfm_holder",owner).ref("xfm_beneficial_owner",owner).num("xfm_account_id",id).num("xfm_system_account",system).num("xfm_account_frozen",0).num("xfm_free_cents",0).num("xfm_reserved_cents",0);}
    private sealed interface Expr permits Atom,Block{}
    private record Atom(String text)implements Expr{}
    private record Entry(String key,String op,Expr value){}
    private record Block(List<Entry>entries)implements Expr{Block{entries=List.copyOf(entries);}Block block(String key){return (Block)field(key);}Expr field(String key){return entries.stream().filter(e->e.key().equals(key)).findFirst().orElseThrow().value();}}
    private sealed interface Datum permits Num,Ref{}
    private record Num(double value)implements Datum{}
    private record Ref(Node node)implements Datum{}
    private record Context(Map<String,Datum>values){Context(){this(new HashMap<>());}}
    private static final class Node{final String type;final Map<String,Datum>vars=new HashMap<>();boolean alive=true,adult=true,ai=false;Node(String type){this.type=type;}Node num(String k,double n){vars.put(k,new Num(n));return this;}Node ref(String k,Node n){vars.put(k,new Ref(n));return this;}Node ref(String k){return ((Ref)vars.get(k)).node();}double n(String k){return ((Num)vars.get(k)).value();}}
    private static String atom(Expr e){return ((Atom)e).text();}
    private static Block without(Block b,String...keys){Set<String>omit=Set.of(keys);return new Block(b.entries().stream().filter(e->!omit.contains(e.key())).toList());}
    private static Block parse(String source){var m=Pattern.compile("\"(?:\\\\.|[^\"\\\\])*\"|!=|>=|<=|[{}=<>]|[^\\s{}=<>]+").matcher(source.replace("\ufeff","").replaceAll("(?m)#.*$",""));List<String>t=new ArrayList<>();while(m.find())t.add(m.group());int[]i={0};Block b=block(t,i,false);assertEquals(t.size(),i[0]);return b;}
    private static Block block(List<String>t,int[]i,boolean nested){List<Entry>entries=new ArrayList<>();while(i[0]<t.size()){String k=t.get(i[0]++);if(k.equals("}")){assertTrue(nested);return new Block(entries);}String op=t.get(i[0]++),v=t.get(i[0]++);assertTrue(Set.of("=","!=",">=","<=",">","<").contains(op));entries.add(new Entry(k,op,v.equals("{")?block(t,i,true):new Atom(v.startsWith("\"")?v.substring(1,v.length()-1):v)));}assertFalse(nested);return new Block(entries);}

    private static final class Vm{
        final Map<String,Block>defs;final Block event;final Node actor=new Node("character"),stranger=new Node("character"),exchange=new Node("xfm_finance_exchange"),primary=account(actor,10,0),otherWallet=account(actor,11,0),a=new Node("xfm_finance_coin"),b=new Node("xfm_finance_coin");
        Context context=new Context();final List<Node>businessTargets=new ArrayList<>();Consumer<Node>onPort=coin->{};
        Vm(Map<String,Block>defs,Block event){this.defs=defs;this.event=event;actor.ref("xfm_account",primary).ref("xfm_active_account",otherWallet).num("xfm_order_lots",2).num("xfm_order_limit_cents",20).num("xfm_order_ioc",0);exchange.num("xfm_new_listings_today",0).num("xfm_active_coin_count",0);
            int id=0;for(Node coin:List.of(a,b)){int current=++id;Node treasury=account(actor,20+current,1).ref("xfm_legal_entity",coin).num("xfm_free_cents",1000);Node maker=account(actor,30+current,1).ref("xfm_legal_entity",coin);
                coin.num("xfm_coin_id",current).num("xfm_listing_state",1).num("xfm_entity_type",1).ref("xfm_controller",actor).ref("xfm_issuer_account",treasury).ref("xfm_market_maker_account",maker).num("xfm_supply_units",15000).num("xfm_maximum_supply_units",30000).num("xfm_mint_permitted",1)
                    .num("xfm_founder_locked_units",2500).num("xfm_actual_raised_cents",2000).num("xfm_minimum_raised_cents",2000).num("xfm_external_raised_cents",400).num("xfm_offer_units_remaining",0).num("xfm_maintenance_arrears_cents",0).num("xfm_issuer_reputation",50).num("xfm_maker_minimum_cents",200).num("xfm_unresolved_claim_count",0).num("xfm_promises_due_cents",0).num("xfm_project_spent_cents",0);
            }
        }
        Context open(Node coin){actor.ref("xfm_selected_coin",coin);context=new Context();execute(event.block("immediate"),actor,null);return context;}
        void choose(Context ticket,String name){context=ticket;Block option=event.entries().stream().filter(e->e.key().equals("option")).map(e->(Block)e.value()).filter(o->o.entries().contains(new Entry("name","=",new Atom(name)))).findFirst().orElseThrow();execute(without(option,"name","trigger"),actor,null);}
        Datum resolve(String s,Node here,Node prev){if(s.equals("root"))return new Ref(actor);if(s.equals("this"))return new Ref(here);if(s.equals("prev"))return prev==null?null:new Ref(prev);if(s.equals("yes")||s.equals("no"))return new Num(s.equals("yes")?1:0);if(s.matches("-?[0-9]+(?:\\.[0-9]+)?"))return new Num(Double.parseDouble(s));
            int dot=s.indexOf('.');if(dot>0){Datum d=resolve(s.substring(0,dot),here,prev);return d instanceof Ref ref?resolve(s.substring(dot+1),ref.node(),here):null;}
            if(s.equals("global_var:xfm_exchange"))return new Ref(exchange);if(s.startsWith("scope:"))return context.values().get(s.substring(6));if(s.startsWith("var:"))return here.vars.get(s.substring(4));if(defs.containsKey(s))return new Num(value(defs.get(s),here,prev));return here.vars.get(s);}
        double number(String s,Node here,Node prev){Datum d=resolve(s,here,prev);if(!(d instanceof Num n))throw new AssertionError("missing number "+s);return n.value();}
        Datum term(Expr expr,Node here,Node prev){return expr instanceof Block b?new Num(value(b,here,prev)):resolve(atom(expr),here,prev);}
        double value(Block b,Node here,Node prev){double n=0;boolean matched=false;for(Entry e:b.entries()){
            if(e.key().equals("if")||e.key().equals("else_if")){Block child=(Block)e.value();boolean ok=(!e.key().equals("else_if")||!matched)&&matches(child.block("limit"),here,prev);if(e.key().equals("if"))matched=false;if(ok){n=value(without(child,"limit"),here,prev);matched=true;}continue;}
            if(e.key().equals("floor")){n=Math.floor(n);continue;}if(e.key().equals("ceiling")){n=Math.ceil(n);continue;}
            double x=((Num)term(e.value(),here,prev)).value();n=switch(e.key()){case "value"->x;case "add"->n+x;case "subtract"->n-x;case "multiply"->n*x;case "divide"->n/x;case "max"->Math.min(n,x);case "min"->Math.max(n,x);default->throw new AssertionError("unknown value op "+e.key());};}return n;}
        boolean matches(Block b,Node here,Node prev){return b.entries().stream().allMatch(e->check(e,here,prev));}
        boolean check(Entry e,Node here,Node prev){String k=e.key();if(k.equals("AND"))return matches((Block)e.value(),here,prev);if(k.equals("OR"))return ((Block)e.value()).entries().stream().anyMatch(x->check(x,here,prev));if(k.equals("NOT"))return !matches((Block)e.value(),here,prev);if(k.equals("trigger_if")){Block child=(Block)e.value();return !matches(child.block("limit"),here,prev)||matches(without(child,"limit"),here,prev);}if(k.equals("has_variable"))return here.vars.containsKey(atom(e.value()));if(k.equals("exists"))return resolve(atom(e.value()),here,prev)!=null;if(k.equals("story_type"))return here.type.equals(atom(e.value()));if(k.equals("has_game_rule"))return false;
            if(k.endsWith("_trigger")){Block predicate=defs.get(k);if(predicate==null)throw new AssertionError("unknown trigger "+k);return matches(predicate,here,prev)==atom(e.value()).equals("yes");}
            if(e.value() instanceof Block child){Datum d=resolve(k,here,prev);return d instanceof Ref ref&&matches(child,ref.node(),here);}
            Datum l=switch(k){case "is_alive"->new Num(here.alive?1:0);case "is_adult"->new Num(here.adult?1:0);case "is_ai"->new Num(here.ai?1:0);default->resolve(k,here,prev);};Datum r=term(e.value(),here,prev);if(l==null||r==null)return false;
            if(l instanceof Num x&&r instanceof Num y)return switch(e.op()){case "="->x.value()==y.value();case "!="->x.value()!=y.value();case ">="->x.value()>=y.value();case "<="->x.value()<=y.value();case ">"->x.value()>y.value();case "<"->x.value()<y.value();default->throw new AssertionError(e.op());};if(!Set.of("=","!=").contains(e.op()))throw new AssertionError("bad ref op "+e.op());return e.op().equals("=")?l.equals(r):!l.equals(r);}
        void run(String name,Node here,Node prev){
            if(name.equals("xfm_finance_select_account_effect")){Node selected=here.vars.containsKey("xfm_active_account")?here.ref("xfm_active_account"):here.ref("xfm_account");context.values().put("xfm_account",new Ref(selected));return;}
            if(name.equals("xfm_finance_ensure_account_effect")){context.values().put("xfm_account",new Ref(here.ref("xfm_account")));return;}
            if(Set.of("xfm_issuer_complete_offer_effect","xfm_issuer_abort_offer_effect","xfm_issuer_promote_effect","xfm_issuer_cancel_unallocated_supply_effect","xfm_listing_release_unused_reserves_effect","xfm_listing_restore_bond_effect","xfm_issuer_restart_liquidity_effect").contains(name)){
                Node selected=here.ref("xfm_selected_coin");businessTargets.add(selected);onPort.accept(selected);if(name.equals("xfm_issuer_complete_offer_effect")||name.equals("xfm_issuer_abort_offer_effect"))here.vars.remove("xfm_pending_offer");return;
            }
            if(name.equals("xfm_issuer_freeze_supply_effect")||name.equals("xfm_issuer_release_project_cash_effect"))businessTargets.add(here.ref("xfm_selected_coin"));
            Block effect=defs.get(name);if(effect==null)throw new AssertionError("unknown effect "+name);execute(effect,here,prev);
        }
        void execute(Block b,Node here,Node prev){boolean chain=false;for(Entry e:b.entries()){
            String k=e.key();if(k.equals("if")||k.equals("else_if")){Block child=(Block)e.value();boolean ok=(!k.equals("else_if")||!chain)&&matches(child.block("limit"),here,prev);if(k.equals("if"))chain=false;if(ok){execute(without(child,"limit"),here,prev);chain=true;}continue;}if(k.equals("else")){if(!chain)execute((Block)e.value(),here,prev);chain=false;continue;}
            if(k.equals("save_scope_as")){context.values().put(atom(e.value()),new Ref(here));continue;}if(k.equals("clear_saved_scope")){context.values().remove(atom(e.value()));continue;}if(k.equals("save_scope_value_as")){Block f=(Block)e.value();Datum d=term(f.field("value"),here,prev);if(d==null)throw new AssertionError("missing saved value");context.values().put(atom(f.field("name")),d);continue;}
            if(k.equals("remove_variable")){here.vars.remove(atom(e.value()));continue;}if(k.equals("set_variable")||k.equals("change_variable")){Block f=(Block)e.value();String name=atom(f.field("name"));if(k.equals("set_variable")){Datum d=term(f.field("value"),here,prev);if(d==null)throw new AssertionError("missing variable value "+name);here.vars.put(name,d);}else{Entry op=f.entries().stream().filter(x->!x.key().equals("name")).findFirst().orElseThrow();double old=here.vars.containsKey(name)?here.n(name):0;double delta=((Num)term(op.value(),here,prev)).value();here.num(name,op.key().equals("add")?old+delta:old-delta);}continue;}
            if(e.value() instanceof Block child){Datum target=resolve(k,here,prev);if(!(target instanceof Ref ref))throw new AssertionError("missing scope "+k);execute(child,ref.node(),here);continue;}run(k,here,prev);
        }}
    }
}
