package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import java.math.BigInteger;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.GameplayEntryRoot;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual original root packet with explicit fixture postconditions; ordinary feudal decoder stays unchanged. */
public final class FixtureGameplayRoot {
    private FixtureGameplayRoot() { }
    public static GameplayEntryRoot decode(PlanningReadReceipt receipt,PreparedFixture fixture,Obj actualSemantic) {
        StrictJson.require(receipt.request().origin() instanceof CommandOrigin.Gameplay&&receipt.request().operation().equals(GameplayEntryRoot.OPERATION)
                &&receipt.original().nativeOk(),"real successful fixture gameplay root read required");
        Obj result=DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
        Obj envelope=DriverJson.object(receipt.original().originalFrame().bytes(),DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(new Text("command_result").equals(envelope.get("type"))&&new IntegerValue(BigInteger.ONE).equals(envelope.get("protocol_version"))
                &&new Text(receipt.requestId()).equals(envelope.get("request_id"))&&new Bool(true).equals(envelope.get("ok"))&&result.equals(envelope.get("result")),
                "fixture root result token differs from actual native frame");
        StrictJson.require(new Text(GameplayEntryRoot.OPERATION.value()).equals(result.get("step"))&&bool(result.get("accepted"),"accepted"),"fixture root native ACK operation differs");
        Obj root=object(result.get("campaign_root_context"),"campaign_root_context");var before=receipt.request().before().frame();
        StrictJson.require(new Text("available").equals(root.get("status"))&&root.get("status").equals(result.get("status"))
                &&integer(result.get("query_sequence"),"query_sequence").signum()>0&&integer(root.get("schema_version"),"schema_version").equals(BigInteger.ONE)
                &&integer(root.get("snapshot_revision"),"snapshot_revision").equals(before.identity().nativeRevision()),"fixture root must be actual available exact-revision query");
        int date=integer(root.get("date_raw"),"date_raw").intValueExact();BigInteger actor=integer(root.get("player_character_id"),"player_character_id");
        StrictJson.require(before.identity().dateRaw().equals(BigInteger.valueOf(date))&&before.identity().player().equals(actor)&&bool(root.get("player_character_alive"),"player_character_alive")
                &&new Text(before.snapshotId()).equals(actualSemantic.get("snapshot_id"))&&new IntegerValue(before.revision()).equals(actualSemantic.get("revision"))
                &&new IntegerValue(before.identity().nativeRevision()).equals(actualSemantic.get("native_revision")),"fixture root/read/current SEM identity differs");
        Obj provenance=object(root.get("provenance"),"provenance");
        var build=FrontendRulesData.Build.require(text(provenance.get("game_version"),"game_version"),text(provenance.get("executable_sha256"),"executable_sha256"));build.requireRules();
        StrictJson.require(fixture.policy().kind()!=FrontendFixturePolicy.Kind.SCENARIO||build==FrontendRulesData.Build.CK3_12004,"fixture scenario root requires actual .4");
        var post=fixture.policy().postStart();Obj government=object(root.get("government"),"government"),title=object(root.get("primary_title"),"primary_title");
        StrictJson.require(new Text(post.governmentKey()).equals(government.get("key"))&&new Text(post.primaryTitleTierKey()).equals(title.get("tier_key"))
                &&new Bool(post.independent()).equals(root.get("independent")),"actual fixture root has not delivered declared government/tier/independence");
        BigInteger titleId=integer(title.get("title_id"),"title_id");int tier=integer(title.get("tier_raw"),"tier_raw").intValueExact();
        String tierKey=switch(tier){case 1->"barony";case 2->"county";case 3->"duchy";case 4->"kingdom";case 5->"empire";case 6->"hegemony";default->"";};
        StrictJson.require(titleId.signum()>0&&tierKey.equals(post.primaryTitleTierKey()),"fixture actual primary title ID/tier inconsistent");
        Value immediate=root.get("immediate_liege_character_id"),top=root.get("top_liege_character_id");
        if(post.independent())StrictJson.require(immediate==Nil.INSTANCE&&integer(top,"top_liege_character_id").equals(actor),"fixture independent actual lieges inconsistent");
        else {BigInteger direct=integer(immediate,"immediate_liege_character_id"),last=integer(top,"top_liege_character_id");StrictJson.require(direct.signum()>0&&last.signum()>0&&!direct.equals(actor)&&!last.equals(actor),"fixture vassal actual lieges inconsistent");}
        return new GameplayEntryRoot(receipt,actor,date,post.governmentKey());
    }
    /** Same exact native DTO normalized for the original business reducer; derived frame fields use original query only. */
    public static Obj publication(PlanningReadReceipt receipt,PreparedFixture fixture,Obj actualSemantic) {
        decode(receipt,fixture,actualSemantic);
        Obj result=DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
        Obj root=object(result.get("campaign_root_context"),"campaign_root_context");var before=receipt.request().before().frame();
        return root.with("campaign_root_context_ready",new Bool(true)).with("backend_id",new Text("native-headless"))
                .with("queried_snapshot_id",new Text(before.snapshotId())).with("queried_revision",new IntegerValue(before.revision()))
                .with("queried_native_revision",new IntegerValue(before.identity().nativeRevision()));
    }
}
