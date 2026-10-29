package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original stable-owner -> whole-root -> actual business-actor reducer. Data proof grants no Root permission. */
public final class FixtureBusinessQualification {
    public record Owner(String snapshotId,BigInteger revision,BigInteger nativeRevision,int dateRaw,BigInteger actor,
            BigInteger localPlayer,long bridgePid,BigInteger connectionGeneration,BigInteger pumpEpoch,BigInteger ownerTid,
            Optional<Obj> activeEvent) {
        public Owner {
            StrictJson.text(snapshotId);nonnegative(revision);positive(nativeRevision);positive(actor);positive(localPlayer);
            StrictJson.require(bridgePid>0&&bridgePid<=0xffff_ffffL,"actual owner PID required");positive(connectionGeneration);positive(pumpEpoch);positive(ownerTid);Objects.requireNonNull(activeEvent);
        }
        public Owner stable() {return new Owner(snapshotId,revision,nativeRevision,dateRaw,actor,localPlayer,bridgePid,connectionGeneration,BigInteger.ONE,ownerTid,activeEvent);}
    }
    public record Actor(BigInteger actorCharacterId,BigInteger primaryTitleId,String governmentKey,String primaryTitleTierKey,
            int dateRaw,long bridgePid,BigInteger connectionGeneration,BigInteger pumpEpoch) {
        public Actor {positive(actorCharacterId);positive(primaryTitleId);StrictJson.text(governmentKey);StrictJson.text(primaryTitleTierKey);positive(connectionGeneration);nonnegative(pumpEpoch);}
        public Actor stable() {return new Actor(actorCharacterId,primaryTitleId,governmentKey,primaryTitleTierKey,dateRaw,bridgePid,connectionGeneration,BigInteger.ZERO);}
    }
    public enum Stage { WAITING_LOGS,WAITING_OWNER,OWNER_QUERY_ADMITTED,WAITING_BUSINESS_ACTOR,QUALIFIED }
    public record Decision(Stage stage,Optional<Owner> owner,Optional<Actor> actor,boolean fixtureTargetIdentityProven) {
        public Decision {Objects.requireNonNull(stage);Objects.requireNonNull(owner);Objects.requireNonNull(actor);StrictJson.require(fixtureTargetIdentityProven==(stage==Stage.QUALIFIED),"only actual final qualification proves fixture target");}
    }
    private final PreparedFixture fixture;
    private final FixtureStartSubmission submission;
    private Owner ownerBaseline;
    private Actor actorBaseline;
    private Decision decision=new Decision(Stage.WAITING_LOGS,Optional.empty(),Optional.empty(),false);
    public FixtureBusinessQualification(PreparedFixture fixture,FixtureStartSubmission actualSubmission) {
        this.fixture=Objects.requireNonNull(fixture);submission=Objects.requireNonNull(actualSubmission);
        StrictJson.require(submission.policyBinding().equals(fixture.binding()),"fixture qualifier must consume actual pending producer/policy");
    }
    public Decision decision() {return decision;}
    /** Called before the real root query. A boolean/shape alone never creates a Root read lease. */
    public Decision observeOwner(Obj snapshot,FixtureQualificationLogs.Observation logs,boolean preservedScenarioEvent) {
        if(!logs.qualified(fixture.policy())){ownerBaseline=null;actorBaseline=null;return set(Stage.WAITING_LOGS,Optional.empty(),Optional.empty());}
        Optional<Owner> current=owner(snapshot,submission,preservedScenarioEvent);
        if(current.isEmpty()){ownerBaseline=null;actorBaseline=null;return set(Stage.WAITING_OWNER,current,Optional.empty());}
        Owner frame=current.orElseThrow();boolean stable=ownerBaseline!=null&&ownerBaseline.stable().equals(frame.stable())&&frame.pumpEpoch().compareTo(ownerBaseline.pumpEpoch())>0;
        ownerBaseline=frame;return set(stable?Stage.OWNER_QUERY_ADMITTED:Stage.WAITING_OWNER,current,Optional.empty());
    }
    /** Root passes the original read's exact public/native frame, followed by an independent fresh SEM. */
    public Decision observeBusiness(Obj freshSnapshot,Obj root,FixtureQualificationLogs.Observation logs,boolean preservedScenarioEvent) {
        StrictJson.require(decision.stage()==Stage.OWNER_QUERY_ADMITTED,"actual whole-root query cannot precede two qualified stable owner frames");
        Optional<Owner> frame=owner(freshSnapshot,submission,preservedScenarioEvent);
        if(frame.isEmpty()||!logs.qualified(fixture.policy())){actorBaseline=null;return set(Stage.WAITING_OWNER,frame,Optional.empty());}
        Optional<Actor> actual=actor(freshSnapshot,root,fixture.policy(),submission);
        if(actual.isEmpty()){actorBaseline=null;return set(Stage.WAITING_BUSINESS_ACTOR,frame,Optional.empty());}
        Actor current=actual.orElseThrow();boolean stable=actorBaseline!=null&&actorBaseline.stable().equals(current.stable())&&current.pumpEpoch().compareTo(actorBaseline.pumpEpoch())>0;
        actorBaseline=current;return set(stable?Stage.QUALIFIED:Stage.WAITING_BUSINESS_ACTOR,frame,actual);
    }
    private Decision set(Stage stage,Optional<Owner> owner,Optional<Actor> actor) {decision=new Decision(stage,owner,actor,stage==Stage.QUALIFIED);return decision;}
    public static Optional<Owner> owner(Obj snapshot,FixtureStartSubmission submission,boolean allowActiveEvent) {
        if(!flagOrFalse(snapshot,"map_ready")||!flagOrFalse(snapshot,"paused"))return Optional.empty();
        Value active=snapshot.get("active_event");StrictJson.require(active!=null,"explicit nullable native active event required");
        if(active!=Nil.INSTANCE&&!allowActiveEvent)return Optional.empty();
        StrictJson.require(text(snapshot.get("episode_projection"),"episode_projection").equals("native_campaign"),"fixture cannot bind one-life observation");
        Obj diagnostics=object(snapshot.get("diagnostics"),"diagnostics");requireBinding(diagnostics,submission);
        int date=integer(snapshot.get("date_raw"),"date_raw").intValueExact();
        StrictJson.require(date==submission.selectedCandidate().startDateRaw(),"fixture startup advanced away from actual selected date");
        Obj played=object(snapshot.get("played_character"),"played_character");BigInteger actor=integer(played.get("character_id"),"character_id"),local=integer(snapshot.get("local_player_id"),"local_player_id");
        if(actor.signum()<=0||local.signum()<=0||!flagOrFalse(played,"alive")||!new Text("native").equals(played.get("source")))return Optional.empty();
        String snapshotId=text(snapshot.get("snapshot_id"),"snapshot_id");BigInteger revision=integer(snapshot.get("revision"),"revision"),nativeRevision=integer(snapshot.get("native_revision"),"native_revision");
        if(revision.signum()<0||nativeRevision.signum()<=0)return Optional.empty();
        Obj heartbeat=object(diagnostics.get("last_heartbeat"),"last_heartbeat");
        if(!integer(heartbeat.get("pid"),"heartbeat.pid").equals(BigInteger.valueOf(submission.binding().bridgePid())))return Optional.empty();
        Obj mailbox=object(heartbeat.get("main_thread_query_mailbox_v1"),"main_thread_query_mailbox_v1");
        BigInteger epoch=integer(mailbox.get("pump_epochs"),"pump_epochs"),ownerEpoch=integer(mailbox.get("owner_verified_pump_epochs"),"owner_verified_pump_epochs"),tid=integer(mailbox.get("owner_tid"),"owner_tid");
        if(!flagOrFalse(mailbox,"ready")||!flagOrFalse(mailbox,"stamp_read_success")||epoch.signum()<=0||!epoch.equals(ownerEpoch)||tid.signum()<=0
                ||!integer(mailbox.get("current_tid"),"current_tid").equals(tid))return Optional.empty();
        return Optional.of(new Owner(snapshotId,revision,nativeRevision,date,actor,local,submission.binding().bridgePid(),submission.binding().connectionGeneration(),epoch,tid,active==Nil.INSTANCE?Optional.empty():Optional.of(object(active,"active_event"))));
    }
    public static Optional<Actor> actor(Obj snapshot,Obj root,FrontendFixturePolicy policy,FixtureStartSubmission submission) {
        if(!flagOrFalse(snapshot,"map_ready")||!flagOrFalse(snapshot,"paused"))return Optional.empty();
        StrictJson.require(new Text("native_campaign").equals(snapshot.get("episode_projection")),"fixture current actor would bind one-life episode");
        Obj diagnostics=object(snapshot.get("diagnostics"),"diagnostics");requireBinding(diagnostics,submission);
        int date=integer(snapshot.get("date_raw"),"date_raw").intValueExact();StrictJson.require(date==submission.selectedCandidate().startDateRaw(),"fixture actor moved beyond selected bookmark date");
        if(!flagOrFalse(root,"campaign_root_context_ready"))return Optional.empty();
        StrictJson.require(new Text("native-headless").equals(root.get("backend_id"))&&Objects.equals(root.get("queried_snapshot_id"),snapshot.get("snapshot_id"))
                &&Objects.equals(root.get("queried_revision"),snapshot.get("revision"))&&Objects.equals(root.get("queried_native_revision"),snapshot.get("native_revision"))
                &&Objects.equals(root.get("date_raw"),snapshot.get("date_raw")),"fixture whole-root query crossed exact actual paused frame");
        Obj provenance=object(root.get("provenance"),"provenance");
        FrontendRulesData.Build build=FrontendRulesData.Build.require(text(provenance.get("game_version"),"game_version"),text(provenance.get("executable_sha256"),"executable_sha256"));build.requireRules();
        if(policy.kind()==FrontendFixturePolicy.Kind.SCENARIO)StrictJson.require(build==FrontendRulesData.Build.CK3_12004,"scenario current root must be actual .4");
        BigInteger actor=integer(object(snapshot.get("played_character"),"played_character").get("character_id"),"character_id");positive(actor);
        StrictJson.require(integer(root.get("player_character_id"),"player_character_id").equals(actor)&&flagOrFalse(root,"player_character_alive"),"fixture root/snapshot disagree on actual living actor");
        Obj government=object(root.get("government"),"government"),title=object(root.get("primary_title"),"primary_title");var post=policy.postStart();
        if(!new Text(post.governmentKey()).equals(government.get("key"))||!new Text(post.primaryTitleTierKey()).equals(title.get("tier_key"))
                ||!new Bool(post.independent()).equals(root.get("independent")))return Optional.empty();
        BigInteger titleId=integer(title.get("title_id"),"title_id");positive(titleId);int tier=integer(title.get("tier_raw"),"tier_raw").intValueExact();
        String tierKey=switch(tier){case 1->"barony";case 2->"county";case 3->"duchy";case 4->"kingdom";case 5->"empire";case 6->"hegemony";default->throw new IllegalArgumentException("actual primary title tier outside original domain");};
        StrictJson.require(tierKey.equals(post.primaryTitleTierKey()),"fixture primary-title identity/tier inconsistent");
        Value immediate=root.get("immediate_liege_character_id"),top=root.get("top_liege_character_id");
        if(post.independent())StrictJson.require(immediate==Nil.INSTANCE&&integer(top,"top_liege_character_id").equals(actor),"independent fixture lieges inconsistent");
        else {BigInteger first=integer(immediate,"immediate_liege_character_id"),last=integer(top,"top_liege_character_id");positive(first);positive(last);StrictJson.require(!first.equals(actor)&&!last.equals(actor),"fixture vassal lieges inconsistent");}
        Obj mailbox=object(object(diagnostics.get("last_heartbeat"),"last_heartbeat").get("main_thread_query_mailbox_v1"),"main_thread_query_mailbox_v1");
        BigInteger epoch=integer(mailbox.get("pump_epochs"),"pump_epochs");nonnegative(epoch);
        return Optional.of(new Actor(actor,titleId,post.governmentKey(),post.primaryTitleTierKey(),date,submission.binding().bridgePid(),submission.binding().connectionGeneration(),epoch));
    }
    private static void requireBinding(Obj diagnostics,FixtureStartSubmission submission) {
        StrictJson.require(integer(diagnostics.get("bridge_pid"),"bridge_pid").equals(BigInteger.valueOf(submission.binding().bridgePid()))
                &&integer(diagnostics.get("connection_generation"),"connection_generation").equals(submission.binding().connectionGeneration()),"fixture map crossed original frontend process/connection");
    }
    private static boolean flagOrFalse(Obj value,String key) {Value field=value.get(key);if(field==null||field==Nil.INSTANCE)return false;return bool(field,key);}
    private static void positive(BigInteger n) {StrictJson.require(n!=null&&n.signum()>0&&n.compareTo(StrictJson.UINT64_MAX)<=0,"positive exact identity required");}
    private static void nonnegative(BigInteger n) {StrictJson.require(n!=null&&n.signum()>=0&&n.compareTo(StrictJson.UINT64_MAX)<=0,"nonnegative exact integer required");}
}
