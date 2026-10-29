package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Fresh ordinary state and the explicitly prepared fixture's private, provisional current-player state. */
public final class InitialDriverState {
    public static final String FIXTURE_PUBLICATION_SCHEMA="xar.java.fixture-current-actor-publication/v1";
    public static final String FIXTURE_PUBLICATION_FIELD="java_fixture_actor_publication";
    private InitialDriverState() { }
    public record Produced(DriverStateSnapshot.Complete driver,Obj auxiliary) {
        public Produced {Objects.requireNonNull(driver);Objects.requireNonNull(auxiliary);}
    }
    public static Produced create(ObservedFrame actual,String actualPipe,String episodeId,InitialEpisodePolicy policy)throws IOException {
        Objects.requireNonNull(policy);
        if(policy.kind()==InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_FIXTURE)policy.requireFixtureProjection(policy.explicitFixture().orElseThrow());
        return createState(actual,actualPipe,episodeId,policy.kind(),policy.lifecycle());
    }
    /** Real first-map Driver from explicit business configuration; no startup provenance is minted. */
    public static Produced create(ObservedFrame actual,String actualPipe,String episodeId,InitialEpisodePolicy.Lifecycle kind,RawJson lifecycle)throws IOException {
        StrictJson.require(kind==InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE||kind==InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION,"fresh campaign lifecycle required");
        Produced result=createState(actual,actualPipe,episodeId,kind,lifecycle);
        String expected=kind==InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE?"rogue_one_life":"ordinary_campaign_succession";
        StrictJson.require(expected.equals(org.xar.ck3.control.application.lifecycle.LifecycleReducer.lifecycle(result.driver())),"configured lifecycle differs from Driver business state");
        return result;
    }
    private static Produced createState(ObservedFrame actual,String actualPipe,String episodeId,InitialEpisodePolicy.Lifecycle kind,RawJson lifecycleBinding)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(kind);Objects.requireNonNull(lifecycleBinding);StrictJson.text(episodeId);
        Obj raw=DriverObservationAssembler.originalNativeState(actual);
        StrictJson.require(bool(raw.get("paused"),"paused")&&bool(raw.get("map_ready"),"map_ready"),"initial Driver requires a real paused map");
        Obj player=object(raw.get("played_character"),"played_character");
        BigInteger actor=NativeCharacterId.of(integer(player.get("character_id"),"character_id")).asBigInteger();
        StrictJson.require(bool(player.get("alive"),"alive"),"actual living player required for initial Driver");
        var nil=new DriverStateSnapshot.NullValue();
        boolean fixture=kind==InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_FIXTURE;
        DriverStateSnapshot.Slot lifecycle=fixture?nil:new DriverStateSnapshot.Value(lifecycleBinding.bytes());
        DriverStateSnapshot.Slot goal=kind==InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION
                ?new DriverStateSnapshot.Value(GoalCodec.encodeGoal(OrdinaryCampaignGoal.newGoal(episodeId,actor.longValueExact()))):nil;
        var driver=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session(actualPipe,actual.session().game().pid(),actor,episodeId),
                List.of(),nil,nil,nil,nil,lifecycle,goal,new DriverStateSnapshot.Value(DriverJson.encode(new Arr(List.of()))));
        Obj auxiliary;
        if(fixture) {
            // The string run identifier in the private Driver is a staging locator, not a one-life binding.
            auxiliary=new Obj(Map.of("episode_projection",new Text(NativeCampaignProjection.WIRE_MODE)));
        } else {
            Obj control=new Obj(Map.of("episode_binding_state",new Text("active_new"),"driver_state_restored",new Bool(false),
                    "driver_state_restore_kind",new Text("new_episode"),"cold_candidate_rejection",Nil.INSTANCE));
            auxiliary=new Obj(Map.of("native_session_control",control,"episode_identity_pending",new Bool(false),
                    "one_life_terminal",new Bool(false),"one_life_terminal_reason",Nil.INSTANCE,
                    "episode_projection",new Text(kind==InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION?"native_campaign":"rogue_one_life")));
        }
        StrictJson.require(java.util.Arrays.equals(driver.encode(),DriverStateSnapshot.decodeComplete(driver.encode()).encode()),"fresh full Driver serialization changed");
        return new Produced(driver,auxiliary);
    }

    /** Archive DATA describing a completed provisional CAS; this record itself cannot publish another actor. */
    public record FixtureActorPublication(DriverSnapshotFacts.Known before,DriverSnapshotFacts.Known after,ObservedFrame actual,
            Optional<ExactRef> originalProjection,Optional<ExactRef> originalAfterKnown) {
        public FixtureActorPublication {
            Objects.requireNonNull(before);Objects.requireNonNull(after);Objects.requireNonNull(actual);
            Objects.requireNonNull(originalProjection);Objects.requireNonNull(originalAfterKnown);
            StrictJson.require(originalProjection.isPresent()==originalAfterKnown.isPresent(),"paired actual fixture publication originals required");
            StrictJson.require(originalProjection.isPresent()?after.stamp().driverVersion()==Math.addExact(before.stamp().driverVersion(),1):before==after,
                    "fixture publication must retain the actual unchanged owner or one real version CAS");
        }
        public boolean changed(){return originalProjection.isPresent();}
    }
    /** Strict optional archive locator; a present malformed/null value is not treated as missing. */
    public static Optional<ExactRef> fixtureActorPublicationReference(DriverSnapshotFacts.Known actual) {
        Objects.requireNonNull(actual);
        if(!actual.auxiliary().members().containsKey(FIXTURE_PUBLICATION_FIELD))return Optional.empty();
        return Optional.of(DriverObservationEvidenceReader.reference(actual.auxiliary().get(FIXTURE_PUBLICATION_FIELD)));
    }

    /**
     * Changes only the private unadopted fixture's current actor. Source/Prepared/Staged/fresh-read and
     * canonical parent custody are checked here; an arbitrary snapshot or public DTO cannot authorize this CAS.
     */
    public static FixtureActorPublication publishFixtureActor(InitialDriverBootstrap.Staged stage,ContinuityStorePort.Session same,
            ManagedGameSession sameGame,G2Source sameSource,NativeOutcomeArchive sameArchive,
            NativeFreshSnapshotPort.Received exactRead,ActionReceipt canonicalStartParent,Instant deadline)throws IOException {
        Objects.requireNonNull(stage);Objects.requireNonNull(same);Objects.requireNonNull(sameGame);Objects.requireNonNull(sameSource);
        Objects.requireNonNull(sameArchive);Objects.requireNonNull(exactRead);Objects.requireNonNull(canonicalStartParent);Objects.requireNonNull(deadline);
        sameArchive.writer().requireSession(same);stage.requireFixtureProjectionOwner(same,sameGame,sameSource);
        var policy=stage.policy();var prepared=policy.explicitFixture().orElseThrow();policy.requireFixtureProjection(prepared);
        StrictJson.require(stage.latestFixtureRead()==exactRead,"actor publication requires this Stage's identical independently received READ");
        NativeFreshSnapshotPort.verifyOriginal(exactRead.acknowledgement(),exactRead.originalFrame(),exactRead.snapshotReceived());
        ObservedFrame actual=exactRead.originalFrame();
        StrictJson.require(Instant.now().isBefore(deadline)&&!actual.observedAt().isAfter(deadline)
                &&actual.session().game().equals(sameGame.generation())&&actual.session().machineId().equals(sameSource.machineId())
                &&sameGame.nativeTransport().diagnostics().session().filter(actual.session()::equals).isPresent(),"fixture actor READ crossed its actual Game/session/source/deadline");
        StrictJson.require(canonicalStartParent.command().equals(stage.command())
                &&canonicalStartParent.bodySha256().equals(ActionCodec.bodySha256(stage.command()))
                &&canonicalStartParent.command().origin() instanceof CommandOrigin.Frontend,"actual canonical fixture Start parent required");
        var originals=sameArchive.withSession(same);
        ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),canonicalStartParent,originals);
        var parentRef=originals.receiptReferenceOf(canonicalStartParent);
        StrictJson.require(originals.loadReceipt(parentRef).equals(canonicalStartParent),"fixture actor parent original receipt changed");
        // A first capture has no retained latest frame yet. The private projection guard above
        // proves this same Stage; the action-qualified fixtureDriver getter intentionally stays closed.
        var before=stage.repository().locked(state->{
            StrictJson.require(state instanceof DriverSnapshotFacts.Known,"complete actual provisional Driver is unavailable");
            return (DriverSnapshotFacts.Known)state;
        });
        var proposed=fixtureActorProjection(before,actual,before.auxiliary());
        if(proposed==before)return new FixtureActorPublication(before,before,actual,Optional.empty(),Optional.empty());
        String head=same.head().digest();
        ExactRef beforeKnown=originals.preserveMaterial(DriverSnapshotFacts.encodeKnownOriginal(before));
        ExactRef beforeDriver=originals.preserveMaterial(RawJson.fullMaterial(before.driver().encode()));
        ExactRef afterDriver=originals.preserveMaterial(RawJson.fullMaterial(proposed.driver().encode()));
        ExactRef nativeFrame=originals.preserveNativeFrame(actual);
        ExactRef readAck=originals.preserve(exactRead.acknowledgement());
        ExactRef nativeCampaign=originals.preserveMaterial(NativeCampaignProjection.encodeOriginalSnapshot(actual));
        var fields=new LinkedHashMap<String,Value>();
        fields.put("schema",new Text(FIXTURE_PUBLICATION_SCHEMA));fields.put("machine_id",new Text(sameSource.machineId()));
        fields.put("observed_at_utc",new Text(actual.observedAt().toString()));fields.put("canonical_parent",DriverObservationEvidenceReader.reference(parentRef));
        fields.put("writer_head_sha256",new Text(head));fields.put("writer_sequence",new IntegerValue(BigInteger.valueOf(same.head().state().sequence())));
        fields.put("initial_policy",DriverObservationEvidenceReader.reference(policy.source()));fields.put("environment",DriverObservationEvidenceReader.reference(policy.environment()));
        fields.put("fixture_policy",DriverObservationEvidenceReader.reference(prepared.policySource()));
        fields.put("before_known",DriverObservationEvidenceReader.reference(beforeKnown));fields.put("before_driver",DriverObservationEvidenceReader.reference(beforeDriver));
        fields.put("after_driver",DriverObservationEvidenceReader.reference(afterDriver));fields.put("native_frame",DriverObservationEvidenceReader.reference(nativeFrame));
        fields.put("fresh_read_ack",DriverObservationEvidenceReader.reference(readAck));fields.put("native_campaign_snapshot",DriverObservationEvidenceReader.reference(nativeCampaign));
        fields.put("before_actor",new IntegerValue(before.driver().session().actorId()));fields.put("after_actor",new IntegerValue(proposed.driver().session().actorId()));
        fields.put("before_version",new IntegerValue(BigInteger.valueOf(before.stamp().driverVersion())));fields.put("after_version",new IntegerValue(BigInteger.valueOf(proposed.stamp().driverVersion())));
        fields.put("episode_epoch",new IntegerValue(BigInteger.valueOf(before.stamp().episodeEpoch())));fields.put("private_staging_run",new Text(before.stamp().episodeRunId()));
        ExactRef projection=originals.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(new Obj(fields))));
        var auxiliary=new LinkedHashMap<>(before.auxiliary().members());auxiliary.put(FIXTURE_PUBLICATION_FIELD,DriverObservationEvidenceReader.reference(projection));
        var after=fixtureActorProjection(before,actual,new Obj(auxiliary));
        ExactRef afterKnown=originals.preserveMaterial(DriverSnapshotFacts.encodeKnownOriginal(after));
        policy.requireFixtureProjection(prepared);sameGame.verify();stage.requireFixtureProjectionOwner(same,sameGame,sameSource);
        StrictJson.require(same.head().digest().equals(head),"fixture actor archive changed its actual canonical writer head");
        stage.repository().locked(current->{
            StrictJson.require(current==before,"fixture actor lost its identical private Driver predecessor");
            stage.repository().compareAndSet(before.stamp(),after);return null;
        });
        return new FixtureActorPublication(before,after,actual,Optional.of(projection),Optional.of(afterKnown));
    }

    /** Pure candidate DATA shared by the guarded publisher and regression; it grants no repository or source authority. */
    static DriverSnapshotFacts.Known fixtureActorProjection(DriverSnapshotFacts.Known before,ObservedFrame actual,Obj auxiliary) {
        Objects.requireNonNull(before);Objects.requireNonNull(actual);Objects.requireNonNull(auxiliary);
        StrictJson.require(before.driver().successionLifecycle() instanceof DriverStateSnapshot.NullValue
                &&new Text(NativeCampaignProjection.WIRE_MODE).equals(before.auxiliary().get("episode_projection")),"explicit null-lifecycle fixture Driver required");
        StrictJson.require(before.stamp().game().equals(actual.session().game()),"fixture actor cannot change actual Game birth");
        var raw=DriverObservationAssembler.originalNativeState(actual);
        StrictJson.require(bool(raw.get("paused"),"paused")&&bool(raw.get("map_ready"),"map_ready"),"fixture actor publication requires actual paused map");
        var player=object(raw.get("played_character"),"played_character");
        BigInteger actor=NativeCharacterId.of(integer(player.get("character_id"),"character_id")).asBigInteger();
        StrictJson.require(bool(player.get("alive"),"alive"),"actual living fixture player required");
        if(actor.equals(before.driver().session().actorId()))return before;
        var old=before.driver();
        var driver=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session(old.session().pipeName(),old.session().bridgePid(),actor,old.session().episodeRunId()),
                old.commandHistory(),old.lastCheckpoint(),old.rollbackWarFailure(),old.managedRestoreTransaction(),old.successionExpectation(),
                old.successionLifecycle(),old.campaignGoal(),old.rollbackWarFailures());
        var stamp=new DriverSnapshotFacts.Stamp(Math.addExact(before.stamp().driverVersion(),1),before.stamp().episodeEpoch(),
                before.stamp().game(),before.stamp().episodeRunId(),DriverJson.sha256(driver.encode()));
        return new DriverSnapshotFacts.Known(driver,stamp,before.originalHistoryBasis(),before.actionRows(),auxiliary,before.loop(),Optional.empty());
    }
}
