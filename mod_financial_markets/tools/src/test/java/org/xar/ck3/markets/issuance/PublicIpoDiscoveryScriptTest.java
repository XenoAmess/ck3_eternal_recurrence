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
import java.util.Objects;
import java.util.Set;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;

/** Actual policy/index/subscription AST; finite finance ports are explicit software fixtures, not CK3. */
final class PublicIpoDiscoveryScriptTest {
    private static final Path SOURCE=Path.of(System.getProperty("xfm.source",".."));
    private static final List<String> INPUTS=List.of(
        "scripted_effects/xfm_issuer_public_ipo_index.txt","scripted_effects/xfm_issuer_public_ipo_discovery.txt",
        "scripted_triggers/xfm_issuer_public_ipo_triggers.txt","script_values/xfm_issuer_public_ipo_values.txt",
        "scripted_effects/xfm_issuer_daily.txt","scripted_effects/xfm_issuer_ai_funding.txt",
        "scripted_effects/xfm_issuer_subscriptions.txt","scripted_effects/xfm_issuer_governance.txt","scripted_triggers/xfm_issuer_triggers.txt",
        "script_values/xfm_issuer_ai_values.txt","script_values/xfm_issuer_values.txt","script_values/xfm_config_values.txt",
        "scripted_effects/xfm_issuer_ai_maintenance.txt",
        "scripted_triggers/xfm_issuer_ai_maintenance_triggers.txt",
        "script_values/xfm_issuer_ai_maintenance_values.txt",
        "scripted_effects/xfm_issuer_maintenance.txt",
        "scripted_effects/xfm_finance_maintenance.txt",
        "scripted_triggers/xfm_finance_maintenance_triggers.txt",
        "script_values/xfm_finance_maintenance_values.txt",
        "scripted_effects/xfm_finance_cash.txt",
        "scripted_effects/xfm_finance_init.txt",
        "scripted_effects/xfm_finance_reserve.txt",
        "scripted_triggers/xfm_finance_triggers.txt",
        "script_values/xfm_finance_values.txt",
        "scripted_effects/xfm_listing_transitions.txt");

    @Test void pointerRotationAndEveryRemovalPositionPreservePermanentIdentityAndBalances() throws IOException {
        Vm v=vm(); Node a=offering(v,"a"),b=offering(v,"b"),c=offering(v,"c");
        for(Node n:List.of(a,b,c))v.run("xfm_issuer_public_ipo_enqueue_effect",n);
        queue(v,List.of(a,b,c)); double money=money(v);
        for(Node expected:List.of(a,b,c,a)) {v.run("xfm_issuer_public_ipo_next_effect",v.exchange);assertSame(expected,v.scopes.get("xfm_public_ipo_candidate"));}
        queue(v,List.of(b,c,a)); v.run("xfm_issuer_public_ipo_remove_effect",c);queue(v,List.of(b,a));
        v.run("xfm_issuer_public_ipo_remove_effect",b);queue(v,List.of(a));v.run("xfm_issuer_public_ipo_remove_effect",a);queue(v,List.of());
        v.run("xfm_issuer_public_ipo_remove_effect",a);assertEquals(0,v.num(v.exchange,"xfm_public_ipo_count"));
        assertEquals(3,v.registry.size());assertEquals(money,money(v));assertEquals(15000,v.num(a,"xfm_supply_units"));
        Vm limited=vm();limited.program.put("xfm_config_listing_daily_budget_value",parse("value = 1"));
        for(int i=0;i<31;i++)limited.run("xfm_issuer_public_ipo_enqueue_effect",offering(limited,"limited"+i));
        assertEquals(30,limited.num(limited.exchange,"xfm_public_ipo_count"));assertEquals(0,limited.num(limited.exchange,"xfm_public_ipo_dirty"));
    }

    @Test void oldHistoryPrefixDoesNotConsumeTheSixtyFourPendingMigrationSlotsAndSameDayReentryDoesNotReset() throws IOException {
        Vm v=vm();for(int i=0;i<4096;i++){Node n=offering(v,"history"+i);n.vars.put("xfm_listing_state",7d);}
        List<Node> pending=new ArrayList<>();for(int i=0;i<240;i++)pending.add(offering(v,"pending"+i));
        v.run("xfm_coin_daily_effect",v.exchange);assertEquals(64,v.num(v.exchange,"xfm_public_ipo_count"));
        v.run("xfm_coin_daily_effect",v.exchange);assertEquals(64,v.num(v.exchange,"xfm_public_ipo_count"));
        for(int day=2;day<=4;day++){v.exchange.vars.put("xfm_day",(double)day);v.run("xfm_coin_daily_effect",v.exchange);assertEquals(Math.min(240,64*day),v.num(v.exchange,"xfm_public_ipo_count"));}
        queue(v,pending);assertEquals(0,v.populationScans);assertEquals(0,v.subscriptionAttempts);
    }

    @Test void firstUnadvertisedUnlandedAdultInvestsRealPrimaryCashWithOriginalTenPercentBudget() throws IOException {
        Vm v=vm();Node coin=offering(v,"public"),investor=investor(v,"landless",8,0);v.run("xfm_issuer_public_ipo_enqueue_effect",coin);
        double total=money(v);v.run("xfm_issuer_ai_public_ipo_discover_effect",investor);
        assertEquals(1,v.subscriptionAttempts);assertEquals(1,v.randomCalls);assertEquals(List.of(25d),v.chances);
        assertEquals(200,v.num(coin,"xfm_actual_raised_cents"));assertEquals(200,v.num(coin,"xfm_external_raised_cents"));
        Node account=(Node)investor.vars.get("xfm_account");assertEquals(200,v.num(account,"xfm_reserved_cents"));assertEquals(6,investor.gold);
        Node receipt=coin.lists.get("xfm_subscriptions").getFirst();assertSame(account,receipt.vars.get("xfm_account"));assertEquals(0,v.num(receipt,"xfm_subscription_state"));
        assertEquals(total,money(v));assertFalse(investor.vars.containsKey("xfm_selected_coin"));assertTrue(v.scopes.keySet().stream().noneMatch(k->k.startsWith("xfm_public_ipo_")));
    }

    @Test void paidAdvertisementTakesTheOnlyDecisionEvenWhenRandomDeclinesAndNeverFallsBackToPublic() throws IOException {
        Vm v=vm();Node publicCoin=offering(v,"public"),ad=offering(v,"advertised"),a=investor(v,"a",20,0);
        v.run("xfm_issuer_public_ipo_enqueue_effect",publicCoin);a.vars.put("xfm_promoted_coin",ad);a.vars.put("xfm_promotion_end_day",30d);
        v.chancePass=false;v.run("xfm_coin_ai_effect",a);assertEquals(1,v.randomCalls);assertEquals(0,v.subscriptionAttempts);queue(v,List.of(publicCoin));
        v.chancePass=true;v.run("xfm_coin_ai_effect",a);assertEquals(2,v.randomCalls);assertEquals(1,v.subscriptionAttempts);
        assertEquals(200,v.num(ad,"xfm_actual_raised_cents"));assertEquals(0,v.num(publicCoin,"xfm_actual_raised_cents"));queue(v,List.of(publicCoin));
    }

    @Test void publicChanceFailureRestoresPriorSelectionAndDoesNotManufactureBackingOrGuaranteeFunding() throws IOException {
        Vm v=vm();Node a=investor(v,"a",20,0),coin=offering(v,"public"),prior=offering(v,"selected");a.vars.put("xfm_selected_coin",prior);
        v.run("xfm_issuer_public_ipo_enqueue_effect",coin);v.chancePass=false;double total=money(v);v.run("xfm_issuer_ai_public_ipo_discover_effect",a);
        assertEquals(0,v.subscriptionAttempts);assertSame(prior,a.vars.get("xfm_selected_coin"));assertEquals(total,money(v));assertEquals(0,v.num(coin,"xfm_actual_raised_cents"));
    }

    @Test void controllerFounderAndEntityBeneficialOwnersCannotPretendToBeExternalSubscribers() throws IOException {
        for(String field:List.of("xfm_controller","xfm_founder_beneficiary","issuer_beneficial","founder_beneficial")){
            Vm v=vm();Node a=investor(v,"a",20,0),coin=offering(v,"public");
            if(field.equals("issuer_beneficial")){Node account=v.node("issuer");account.vars.put("xfm_beneficial_owner",a);coin.vars.put("xfm_issuer_account",account);}
            else if(field.equals("founder_beneficial")){Node account=v.node("founder");account.vars.put("xfm_beneficial_owner",a);coin.vars.put("xfm_founder_account",account);}
            else coin.vars.put(field,a);
            v.run("xfm_issuer_public_ipo_enqueue_effect",coin);v.run("xfm_issuer_ai_public_ipo_discover_effect",a);
            assertEquals(0,v.subscriptionAttempts,field);assertEquals(0,v.randomCalls,field);assertEquals(0,v.num(coin,"xfm_external_raised_cents"));
        }
    }

    @Test void livingFounderAfterActualTitleControllerRefreshStillPaysButIsNotExternal() throws IOException {
        Vm v=vm();Node founder=investor(v,"living-founder",20,0),coin=offering(v,"title-offer"),successor=v.node("new-title-holder");
        founder.ai=false;coin.vars.put("xfm_controller",founder);coin.vars.put("xfm_founder_beneficiary",founder);
        Node project=v.node("project"),founderPool=v.node("founder-pool"),title=v.node("bound-title");
        project.vars.put("xfm_beneficial_owner",founder);founderPool.vars.put("xfm_beneficial_owner",founder);
        coin.vars.put("xfm_issuer_account",project);coin.vars.put("xfm_founder_account",founderPool);
        coin.vars.put("xfm_entity_type",4d);coin.vars.put("xfm_bound_entity",title);title.vars.put("holder",successor);
        // Execute the real governance AST for the normal title-holder transition.
        v.run("xfm_issuer_refresh_controller_effect",coin);
        assertSame(successor,coin.vars.get("xfm_controller"));assertSame(successor,project.vars.get("xfm_beneficial_owner"));
        assertSame(founder,coin.vars.get("xfm_founder_beneficiary"));assertSame(founder,founderPool.vars.get("xfm_beneficial_owner"));
        founder.vars.put("xfm_selected_coin",coin);founder.vars.put("xfm_subscription_gold",2d);double total=money(v);
        v.run("xfm_issuer_subscribe_effect",founder);Node wallet=(Node)founder.vars.get("xfm_account");
        assertEquals(1,v.num(founder,"xfm_issuer_result"));assertEquals(200,v.num(coin,"xfm_actual_raised_cents"));
        assertEquals(0,v.num(coin,"xfm_external_raised_cents"));assertEquals(200,v.num(wallet,"xfm_reserved_cents"));
        assertEquals(18,founder.gold);assertEquals(total,money(v));
        Node receipt=coin.lists.get("xfm_subscriptions").getFirst();assertSame(wallet,receipt.vars.get("xfm_account"));
        assertSame(founder,receipt.vars.get("xfm_subscription_buyer"));assertEquals(200,v.num(receipt,"xfm_remaining_cents"));
        assertEquals(0,v.num(receipt,"xfm_subscription_state"));
    }

    @Test void commonHumanSubscriptionClassifiesAllKnownBeneficiariesAndKeepsHistoricalPaidTotals() throws IOException {
        for(String relation:List.of("controller","founder","project_beneficial","founder_beneficial","independent","stale_project_beneficial","stale_founder_beneficial")){
            Vm v=vm();Node buyer=investor(v,"buyer",20,0),coin=offering(v,"offer");buyer.ai=false;
            coin.vars.put("xfm_founder_beneficiary",v.node("legal-founder"));
            if(relation.equals("controller")||relation.equals("project_beneficial"))coin.vars.put("xfm_controller",buyer);
            if(relation.equals("founder")||relation.equals("founder_beneficial"))coin.vars.put("xfm_founder_beneficiary",buyer);
            if(relation.endsWith("_beneficial")){Node account=v.node("related-pool");account.vars.put("xfm_beneficial_owner",buyer);
                coin.vars.put(relation.contains("project")?"xfm_issuer_account":"xfm_founder_account",account);}
            coin.vars.put("xfm_actual_raised_cents",1000d);coin.vars.put("xfm_external_raised_cents",400d);
            buyer.vars.put("xfm_selected_coin",coin);buyer.vars.put("xfm_subscription_gold",2d);double total=money(v);
            v.run("xfm_issuer_subscribe_effect",buyer);Node wallet=(Node)buyer.vars.get("xfm_account");
            assertEquals(1,v.num(buyer,"xfm_issuer_result"),relation);assertEquals(1200,v.num(coin,"xfm_actual_raised_cents"),relation);
            assertEquals(relation.equals("independent")||relation.startsWith("stale_")?600:400,v.num(coin,"xfm_external_raised_cents"),relation);
            assertEquals(200,v.num(wallet,"xfm_reserved_cents"),relation);assertEquals(18,buyer.gold,relation);assertEquals(total,money(v),relation);
            assertEquals(1,coin.lists.get("xfm_subscriptions").size(),relation);
        }
        Vm failed=vm();Node buyer=investor(failed,"buyer",20,0),coin=offering(failed,"offer");buyer.ai=false;
        coin.vars.put("xfm_actual_raised_cents",1000d);coin.vars.put("xfm_external_raised_cents",400d);
        buyer.vars.put("xfm_selected_coin",coin);buyer.vars.put("xfm_subscription_gold",2d);failed.reserveFails=true;double total=money(failed);
        failed.run("xfm_issuer_subscribe_effect",buyer);assertEquals(0,failed.num(buyer,"xfm_issuer_result"));
        assertEquals(1000,failed.num(coin,"xfm_actual_raised_cents"));assertEquals(400,failed.num(coin,"xfm_external_raised_cents"));
        assertFalse(coin.lists.containsKey("xfm_subscriptions"));assertEquals(total,money(failed));
    }

    @Test void sameDayNewLegalTitleHolderSubscribesBeforeDailyRefreshWithoutFakeExternalDemand() throws IOException {
        Vm v=vm();Node founder=investor(v,"old-founder",20,0),buyer=investor(v,"new-holder",20,0),coin=offering(v,"same-day-title");
        buyer.ai=false;coin.vars.put("xfm_controller",founder);coin.vars.put("xfm_founder_beneficiary",founder);
        Node title=v.node("bound-title"),project=v.node("project"),founderPool=v.node("founder-pool");title.vars.put("holder",buyer);
        coin.vars.put("xfm_entity_type",4d);coin.vars.put("xfm_bound_entity",title);
        project.vars.put("xfm_beneficial_owner",founder);founderPool.vars.put("xfm_beneficial_owner",founder);
        coin.vars.put("xfm_issuer_account",project);coin.vars.put("xfm_founder_account",founderPool);
        // No daily/governance pre-call: ordinary subscription must refresh the real legal holder itself.
        assertSame(founder,coin.vars.get("xfm_controller"));buyer.vars.put("xfm_selected_coin",coin);buyer.vars.put("xfm_subscription_gold",2d);
        double total=money(v);v.run("xfm_issuer_subscribe_effect",buyer);
        assertSame(buyer,coin.vars.get("xfm_controller"));assertSame(buyer,project.vars.get("xfm_beneficial_owner"));
        assertSame(founder,coin.vars.get("xfm_founder_beneficiary"));assertSame(founder,founderPool.vars.get("xfm_beneficial_owner"));
        assertEquals(1,v.num(buyer,"xfm_issuer_result"));assertEquals(200,v.num(coin,"xfm_actual_raised_cents"));
        assertEquals(0,v.num(coin,"xfm_external_raised_cents"));assertEquals(200,v.num((Node)buyer.vars.get("xfm_account"),"xfm_reserved_cents"));
        assertEquals(18,buyer.gold);assertEquals(20,founder.gold);assertEquals(total,money(v));
        Node outsider=investor(v,"outside-buyer",20,0);outsider.ai=false;outsider.vars.put("xfm_selected_coin",coin);outsider.vars.put("xfm_subscription_gold",2d);
        total=money(v);v.run("xfm_issuer_subscribe_effect",outsider);
        assertEquals(400,v.num(coin,"xfm_actual_raised_cents"));assertEquals(200,v.num(coin,"xfm_external_raised_cents"));
        assertEquals(200,v.num((Node)outsider.vars.get("xfm_account"),"xfm_reserved_cents"));assertEquals(18,outsider.gold);
        assertEquals(2,coin.lists.get("xfm_subscriptions").size());assertEquals(total,money(v));
    }

    @Test void oneInvalidPendingProjectConsumesOnlyOneInspectionWithoutSearchingTheNextOffering() throws IOException {
        Vm v=vm();Node a=investor(v,"a",20,0),closed=offering(v,"closed"),next=offering(v,"next");
        v.run("xfm_issuer_public_ipo_enqueue_effect",closed);v.run("xfm_issuer_public_ipo_enqueue_effect",next);closed.vars.put("xfm_offer_closing_started",1d);
        v.run("xfm_issuer_ai_public_ipo_discover_effect",a);assertEquals(0,v.randomCalls);assertEquals(0,v.subscriptionAttempts);queue(v,List.of(next));
        v.run("xfm_issuer_ai_public_ipo_discover_effect",a);assertEquals(1,v.subscriptionAttempts);
    }

    @Test void fiveGoldReserveChildrenHumansFrozenAccountsAndDeadControllerKeepOriginalEligibility() throws IOException {
        for(String reason:List.of("reserve","child","human","frozen","dead_controller")){
            Vm v=vm();Node a=investor(v,"a",5,0),coin=offering(v,"public");if(!reason.equals("reserve"))a.gold=20;
            if(reason.equals("child"))a.adult=false;if(reason.equals("human"))a.ai=false;if(reason.equals("frozen"))((Node)a.vars.get("xfm_account")).usable=false;
            v.run("xfm_issuer_public_ipo_enqueue_effect",coin);if(reason.equals("dead_controller"))((Node)coin.vars.get("xfm_controller")).alive=false;
            double total=money(v);v.run("xfm_issuer_ai_public_ipo_discover_effect",a);assertEquals(total,money(v),reason);assertEquals(0,v.num(coin,"xfm_actual_raised_cents"),reason);
        }
    }

    @Test void primaryWalletOnlyAndFiniteReservationFailureNeverCountsAsPaidOrUsesProjectAssets() throws IOException {
        Vm v=vm();Node a=investor(v,"a",5,0),coin=offering(v,"public"),account=(Node)a.vars.get("xfm_account"),project=v.node("rich-project");
        project.vars.put("xfm_free_cents",100000d);project.vars.put("xfm_holder",a);a.vars.put("xfm_active_account",project);v.run("xfm_issuer_public_ipo_enqueue_effect",coin);
        v.run("xfm_issuer_ai_public_ipo_discover_effect",a);assertEquals(0,v.subscriptionAttempts);assertEquals(100000,v.num(project,"xfm_free_cents"));
        a.gold=20;v.reserveFails=true;double total=money(v);v.run("xfm_issuer_ai_public_ipo_discover_effect",a);assertEquals(1,v.subscriptionAttempts);
        assertEquals(0,v.num(coin,"xfm_actual_raised_cents"));assertEquals(0,v.num(account,"xfm_reserved_cents"));assertFalse(coin.lists.containsKey("xfm_subscriptions"));assertEquals(total,money(v));
    }

    @Test void brokenHeadSelfCycleCrossLinkOrInvalidScopeRefusesThenBoundedDailyEpochRebuildRecovers() throws IOException {
        for(String bad:List.of("head","self","cross","unresolved")){
            Vm v=vm();Node a=investor(v,"a",20,0),x=offering(v,"x"),y=offering(v,"y");v.run("xfm_issuer_public_ipo_enqueue_effect",x);v.run("xfm_issuer_public_ipo_enqueue_effect",y);
            if(bad.equals("head"))v.exchange.vars.remove("xfm_public_ipo_head");if(bad.equals("self"))x.vars.put("xfm_public_ipo_next",x);
            if(bad.equals("cross"))y.vars.put("xfm_public_ipo_prev",y);if(bad.equals("unresolved"))y.scopeExists=false;
            v.run("xfm_issuer_ai_public_ipo_discover_effect",a);assertEquals(0,v.subscriptionAttempts,bad);assertEquals(1,v.num(v.exchange,"xfm_public_ipo_dirty"),bad);
            y.scopeExists=true;v.run("xfm_coin_daily_effect",v.exchange);queue(v,List.of(x,y));assertEquals(1,v.num(v.exchange,"xfm_public_ipo_rebuild_count"));
            v.run("xfm_coin_daily_effect",v.exchange);assertEquals(1,v.num(v.exchange,"xfm_public_ipo_rebuild_count"));
            v.run("xfm_issuer_ai_public_ipo_discover_effect",a);assertEquals(1,v.subscriptionAttempts);
        }
    }

    @Test void actualRefundAndDailyRetirementRemoveDiscoveryWithoutDeletingStoriesSupplyOrReusingIds() throws IOException {
        Vm v=vm();Node coin=offering(v,"refund"),other=offering(v,"retired");v.run("xfm_issuer_public_ipo_enqueue_effect",coin);v.run("xfm_issuer_public_ipo_enqueue_effect",other);
        v.run("xfm_issuer_refund_effect",coin);assertEquals(6,v.num(coin,"xfm_listing_state"));assertEquals(1,v.num(coin,"xfm_public_ipo_closed"));queue(v,List.of(other));
        other.vars.put("xfm_listing_state",7d);v.run("xfm_coin_daily_effect",v.exchange);queue(v,List.of());assertEquals(2,v.registry.size());assertEquals(15000,v.num(coin,"xfm_supply_units"));
    }

    @Test void actualRegistrationClosingAndArchiveHooksAndSingleAdvertisementChoiceAreWired() throws IOException {
        String registration=Files.readString(dependency("scripted_effects/xfm_issuer_registration.txt"));Block reg=parse(registration);
        assertEquals(1,count(findBlock(reg,"xfm_issuer_register_effect"),"xfm_issuer_public_ipo_enqueue_effect"));
        Block subscriptions=parse(Files.readString(dependency("scripted_effects/xfm_issuer_subscriptions.txt")));
        Block closing=containing(findBlock(subscriptions,"xfm_issuer_complete_offer_effect"),"xfm_issuer_public_ipo_remove_effect");
        assertTrue(index(closing,"xfm_issuer_public_ipo_remove_effect")<index(closing,"every_in_list"));
        Block archive=findBlock(parse(Files.readString(dependency("scripted_effects/xfm_listing_transitions.txt"))),"xfm_listing_archive_effect");
        assertEquals(1,count(archive,"xfm_issuer_public_ipo_remove_effect"));
        Block policy=vm().program.get("xfm_coin_ai_effect");Block ad=containing(policy,"xfm_issuer_ai_ad_subscribe_effect");
        assertTrue(ad.entries().contains(new Entry("chance","=",new Text("25"))));assertEquals(1,count(policy,"xfm_issuer_ai_public_ipo_discover_effect"));
        for(String rel:INPUTS.subList(0,4)){byte[] raw=Files.readAllBytes(dependency(rel));assertArrayEquals(new byte[]{(byte)0xef,(byte)0xbb,(byte)0xbf},java.util.Arrays.copyOf(raw,3));}
    }

    private static Path dependency(String rel){Path p=SOURCE.resolve("common").resolve(rel);return Files.exists(p)?p:SOURCE.resolve("../baseline/mod_financial_markets/common").normalize().resolve(rel);}
    private static Vm vm() throws IOException {Map<String,Block> p=new LinkedHashMap<>();for(String rel:INPUTS)for(Entry e:parse(Files.readString(dependency(rel),StandardCharsets.UTF_8)).entries())p.put(e.key(),e.term() instanceof Block b?b:new Block(List.of(new Entry("value","=",e.term()))));return new Vm(p);}
    private static Node offering(Vm v,String id){Node c=v.node(id);c.storyType="xfm_finance_coin";c.vars.put("xfm_coin_id",(double)v.registry.size()+1);c.vars.put("xfm_controller",v.node("issuer-"+id));c.vars.put("xfm_listing_state",0d);c.vars.put("xfm_offer_age",0d);c.vars.put("xfm_offer_units_remaining",10000d);c.vars.put("xfm_minimum_raised_cents",2000d);c.vars.put("xfm_ipo_price_cents",20d);c.vars.put("xfm_actual_raised_cents",0d);c.vars.put("xfm_external_raised_cents",0d);c.vars.put("xfm_supply_units",15000d);c.vars.put("xfm_entity_type",1d);v.registry.add(c);return c;}
    private static Node investor(Vm v,String id,double gold,double free){Node a=v.node(id),account=v.node(id+"-account");a.gold=gold;a.vars.put("xfm_issue_cooldown",1d);a.vars.put("xfm_account",account);account.storyType="xfm_finance_account";account.vars.put("xfm_holder",a);account.vars.put("xfm_beneficial_owner",a);account.vars.put("xfm_system_account",0d);account.vars.put("xfm_free_cents",free);account.vars.put("xfm_reserved_cents",0d);return a;}
    private static double money(Vm v){return v.nodes.values().stream().mapToDouble(n->n.gold*100+v.num(n,"xfm_free_cents")+v.num(n,"xfm_reserved_cents")).sum();}
    private static void queue(Vm v,List<Node> want){assertEquals(want.size(),v.num(v.exchange,"xfm_public_ipo_count"));Node at=(Node)v.exchange.vars.get("xfm_public_ipo_head"),prior=null;for(Node n:want){assertSame(n,at);assertSame(prior,n.vars.get("xfm_public_ipo_prev"));assertEquals(v.num(v.exchange,"xfm_public_ipo_epoch"),v.num(n,"xfm_public_ipo_epoch"));prior=n;at=(Node)n.vars.get("xfm_public_ipo_next");}assertNull(at);assertSame(prior,v.exchange.vars.get("xfm_public_ipo_tail"));}
    private static int count(Block b,String key){int n=0;for(Entry e:b.entries()){if(e.key().equals(key))n++;if(e.term()instanceof Block c)n+=count(c,key);}return n;}
    private static int index(Block b,String key){for(int i=0;i<b.entries().size();i++)if(b.entries().get(i).key().equals(key))return i;return -1;}
    private static Block findBlock(Block b,String key){for(Entry e:b.entries())if(e.key().equals(key)&&e.term()instanceof Block c)return c;for(Entry e:b.entries())if(e.term()instanceof Block c){try{return findBlock(c,key);}catch(IllegalArgumentException ignored){}}throw new IllegalArgumentException(key);}
    private static Block containing(Block b,String key){if(index(b,key)>=0)return b;for(Entry e:b.entries())if(e.term()instanceof Block c){try{return containing(c,key);}catch(IllegalArgumentException ignored){}}throw new IllegalArgumentException(key);}
    private sealed interface Term permits Text,Block{}
    private record Text(String text)implements Term{}
    private record Block(List<Entry>entries)implements Term{Block{entries=List.copyOf(entries);}}
    private record Entry(String key,String op,Term term){}
    private static Block parse(String source){List<String>t=new ArrayList<>();var m=Pattern.compile("#[^\\r\\n]*|[\\s\\uFEFF]+|>=|<=|!=|[{}=<>]|[^\\s{}=<>!#\\uFEFF]+").matcher(source);while(m.find()){String s=m.group();if(!s.isBlank()&&!s.startsWith("#")&&!s.equals("\uFEFF"))t.add(s);}int[]i={0};Block b=block(t,i,false);assertEquals(t.size(),i[0]);return b;}
    private static Block block(List<String>t,int[]i,boolean nested){List<Entry>r=new ArrayList<>();while(i[0]<t.size()){String k=t.get(i[0]++);if(k.equals("}")){if(!nested)throw new IllegalArgumentException("unexpected }");return new Block(r);}String op=t.get(i[0]++);if(!Set.of("=","!=",">","<",">=","<=").contains(op))throw new IllegalArgumentException(op);String s=t.get(i[0]++);r.add(new Entry(k,op,s.equals("{")?block(t,i,true):new Text(s)));}if(nested)throw new IllegalArgumentException("missing }");return new Block(r);}
    private static Term optional(Block b,String k){for(Entry e:b.entries())if(e.key().equals(k))return e.term();return null;}
    private static Term field(Block b,String k){Term t=optional(b,k);if(t==null)throw new IllegalArgumentException(k);return t;}
    private static Block child(Block b,String k){return (Block)field(b,k);}
    private static Block without(Block b,String k){return new Block(b.entries().stream().filter(e->!e.key().equals(k)).toList());}
    private static String text(Term t){return ((Text)t).text();}
    private static final class Node{final String id;String storyType="";boolean ai=true,alive=true,adult=true,usable=true,scopeExists=true;double gold;final Map<String,Object>vars=new LinkedHashMap<>();final Map<String,List<Node>>lists=new HashMap<>();Node(String id){this.id=id;}}
    private static final class Vm{
        final Map<String,Block>program;final Map<String,Node>nodes=new LinkedHashMap<>(),scopes=new HashMap<>();final List<Node>registry=new ArrayList<>();final Node exchange;
        boolean chancePass=true,reserveFails;int randomCalls,subscriptionAttempts,populationScans,reservations;final List<Double>chances=new ArrayList<>();
        Vm(Map<String,Block>p){program=p;exchange=node("exchange");exchange.storyType="xfm_finance_exchange";exchange.vars.put("xfm_day",1d);exchange.vars.put("xfm_registry_review_round",1d);}
        Node node(String id){return nodes.computeIfAbsent(id,Node::new);}double num(Node n,String k){Object x=n.vars.get(k);return x==null?0:(Double)x;}
        Object resolve(String t,Node h,Node prev){if(t.equals("this"))return h;if(t.equals("prev"))return prev;if(t.equals("holder"))return h.vars.get("holder");if(t.equals("global_var:xfm_exchange"))return exchange;if(t.startsWith("global_var:xfm_exchange."))return resolve(t.substring(24),exchange,h);int dot=t.indexOf('.');if(dot>0){Object b=resolve(t.substring(0,dot),h,prev);return b instanceof Node n?resolve(t.substring(dot+1),n,h):null;}Object x;if(t.startsWith("scope:"))x=scopes.get(t.substring(6));else if(t.startsWith("var:"))x=h.vars.get(t.substring(4));else if(t.equals("gold"))return h.gold;else if(program.containsKey(t))return value(program.get(t),h,prev,0);else{try{return Double.valueOf(t);}catch(NumberFormatException e){return t;}}return x instanceof Node n&&!n.scopeExists?null:x;}
        Object term(Term t,Node h,Node p){return t instanceof Block b?value(b,h,p,0):resolve(text(t),h,p);}
        double value(Block b,Node h,Node p,double initial){double n=initial;boolean chain=false;for(Entry e:b.entries()){String k=e.key();if(k.equals("if")||k.equals("else_if")){Block c=(Block)e.term();boolean applies=(!k.equals("else_if")||!chain)&&test(child(c,"limit"),h,p);if(k.equals("if"))chain=false;if(applies){n=value(without(c,"limit"),h,p,n);chain=true;}continue;}if(k.equals("floor")){n=Math.floor(n);continue;}if(k.equals("ceiling")){n=Math.ceil(n);continue;}double x=(Double)term(e.term(),h,p);n=switch(k){case "value"->x;case "add"->n+x;case "subtract"->n-x;case "multiply"->n*x;case "divide"->n/x;case "min"->Math.max(n,x);case "max"->Math.min(n,x);default->throw new IllegalArgumentException("value "+k);};}return n;}
        boolean test(Block b,Node h,Node p){Boolean conditional=null;for(Entry e:b.entries()){if(e.key().equals("trigger_if")){Block c=(Block)e.term();conditional=test(child(c,"limit"),h,p);if(conditional&&!test(without(c,"limit"),h,p))return false;continue;}if(e.key().equals("trigger_else")){if(Boolean.FALSE.equals(conditional)&&!test((Block)e.term(),h,p))return false;conditional=null;continue;}if(!check(e,h,p))return false;}return true;}
        boolean check(Entry e,Node h,Node p){String k=e.key();if(k.equals("always"))return text(e.term()).equals("yes");if(k.equals("OR"))return ((Block)e.term()).entries().stream().anyMatch(x->check(x,h,p));if(k.equals("AND"))return test((Block)e.term(),h,p);if(k.equals("NOT"))return ((Block)e.term()).entries().stream().noneMatch(x->check(x,h,p));if(k.equals("has_variable"))return h.vars.containsKey(text(e.term()));if(k.equals("exists"))return resolve(text(e.term()),h,p)!=null;if(k.equals("is_alive"))return h.alive==text(e.term()).equals("yes");if(k.equals("is_adult"))return h.adult==text(e.term()).equals("yes");if(k.equals("is_ai"))return h.ai==text(e.term()).equals("yes");if(k.equals("story_type"))return h.storyType.equals(text(e.term()));if(k.equals("xfm_config_spot_open_trigger"))return true;if(k.equals("xfm_config_ai_issuance_open_trigger"))return false;if(k.equals("xfm_finance_account_usable_trigger"))return h.usable;
            if(k.equals("any_in_list")){Block c=(Block)e.term();for(Node n:h.lists.getOrDefault(text(field(c,"variable")),List.of()))if(test(without(c,"variable"),n,h))return true;return false;}
            if(k.endsWith("_trigger")&&program.containsKey(k))return test(program.get(k),h,p);if(e.term()instanceof Block c){Object x=resolve(k,h,p);return x instanceof Node n&&test(c,n,h);}Object l=resolve(k,h,p),r=term(e.term(),h,p);if(e.op().equals("="))return Objects.equals(l,r);if(e.op().equals("!="))return !Objects.equals(l,r);if(!(l instanceof Double x)||!(r instanceof Double y))return false;return switch(e.op()){case ">"->x>y;case "<"->x<y;case ">="->x>=y;case "<="->x<=y;default->throw new IllegalArgumentException(e.op());};}
        void run(String name,Node h){Block b=program.get(name);if(b==null)throw new IllegalArgumentException(name);execute(b,h,null);}
        void execute(Block b,Node h,Node p){boolean chain=false;for(Entry e:b.entries()){String k=e.key();if(k.equals("if")||k.equals("else_if")){Block c=(Block)e.term();boolean applies=(!k.equals("else_if")||!chain)&&test(child(c,"limit"),h,p);if(k.equals("if"))chain=false;if(applies){execute(without(c,"limit"),h,p);chain=true;}continue;}if(k.equals("else")){if(!chain)execute((Block)e.term(),h,p);chain=false;continue;}if(k.equals("save_scope_as")){scopes.put(text(e.term()),h);continue;}if(k.equals("clear_saved_scope")){scopes.remove(text(e.term()));continue;}if(k.equals("remove_variable")){h.vars.remove(text(e.term()));continue;}if(k.equals("set_variable")||k.equals("change_variable")){Block c=(Block)e.term();String n=text(field(c,"name"));if(k.equals("change_variable")&&Set.of("xfm_public_ipo_fault_count","xfm_public_ipo_rebuild_count").contains(n))assertTrue(h.vars.containsKey(n),"diagnostic counter must be explicitly initialized: "+n);if(k.equals("set_variable")){Term x=optional(c,"value");h.vars.put(n,term(x==null?field(c,"days"):x,h,p));}else if(optional(c,"add")!=null)h.vars.put(n,num(h,n)+(Double)term(field(c,"add"),h,p));else h.vars.put(n,num(h,n)-(Double)term(field(c,"subtract"),h,p));continue;}
            if(k.equals("random")){Block c=(Block)e.term();randomCalls++;chances.add((Double)term(field(c,"chance"),h,p));if(chancePass)execute(without(c,"chance"),h,p);continue;}
            if(k.equals("every_in_global_list")||k.equals("every_in_list")){Block c=(Block)e.term();List<Node> list=k.equals("every_in_global_list")?registry:h.lists.getOrDefault(text(field(c,"variable")),List.of());for(Node n:List.copyOf(list))if(optional(c,"limit")==null||test(child(c,"limit"),n,h))execute(without(without(c,"variable"),"limit"),n,h);continue;}
            if(k.equals("add_to_variable_list")){Block c=(Block)e.term();h.lists.computeIfAbsent(text(field(c,"name")),x->new ArrayList<>()).add((Node)term(field(c,"target"),h,p));continue;}
            if(k.equals("xfm_finance_ensure_account_effect"))continue; // fixtures explicitly bind existing primary accounts
            if(k.equals("xfm_finance_ensure_funds_effect")){Node holder=(Node)h.vars.get("xfm_holder");double need=num(h,"xfm_request_cents")-num(h,"xfm_free_cents");if(h.usable&&need>0&&holder.gold*100>=need){holder.gold-=need/100;h.vars.put("xfm_free_cents",num(h,"xfm_free_cents")+need);}continue;}
            if(k.equals("xfm_finance_reserve_effect")){double need=num(h,"xfm_request_cents");h.vars.put("xfm_result",0d);if(!reserveFails&&h.usable&&need>0&&num(h,"xfm_free_cents")>=need){h.vars.put("xfm_free_cents",num(h,"xfm_free_cents")-need);h.vars.put("xfm_reserved_cents",num(h,"xfm_reserved_cents")+need);Node r=node("reservation"+(++reservations));r.vars.put("xfm_account",h);r.vars.put("xfm_remaining_cents",need);scopes.put("xfm_reservation",r);h.vars.put("xfm_result",1d);}continue;}
            if(k.equals("xfm_issuer_subscribe_effect")){subscriptionAttempts++;execute(program.get(k),h,p);continue;}
            if(Set.of("xfm_registry_capacity_ensure_effect","xfm_registry_review_terminal_effect","xfm_registry_flush_retire_effect","xfm_issuer_adopt_legacy_defaults_effect","xfm_issuer_unlock_founder_effect","xfm_issuer_investigate_effect","xfm_issuer_revisit_offer_effect","xfm_news_record_effect").contains(k))continue; // existing financial/rights services are outside this queue-policy slice
            if(k.equals("every_living_character")){populationScans++;throw new AssertionError("No population scan in IPO discovery");}
            if(e.term()instanceof Block c){Object x=resolve(k,h,p);if(!(x instanceof Node n))throw new IllegalArgumentException("missing scope "+k);execute(c,n,h);continue;}
            Block effect=program.get(k);if(effect==null)throw new IllegalArgumentException("unknown effect "+k);execute(effect,h,p);
        }}
    }
}
