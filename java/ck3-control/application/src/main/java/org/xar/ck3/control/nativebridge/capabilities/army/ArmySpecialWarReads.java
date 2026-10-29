package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Three advertised original READ families; no action, native mutation, private permit or replacement query. */
public final class ArmySpecialWarReads {
    public static final String H2743="query-h2743-preaction-existing-truce-v1";
    public static final String PRISONERS="query-war-prisoner-release-pairs-v1-";
    public static final String BOUND_LOSS="query-raiktor-war-bound-loss-cleanup-v1-";
    public static final String H2743_EXE="2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    public static final String EPISODE="native-29829-2bc2d599f7f9";
    public static final String CHECKPOINT="A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9";
    public enum Kind { H2743, PRISONERS, BOUND_LOSS }
    public record Sources(ExactRef definition,ExactRef decoder,ExactRef h2743Native,ExactRef prisonerNative,ExactRef boundLossNative) {
        public Sources { for(var ref:List.of(definition,decoder,h2743Native,prisonerNative,boundLossNative))StrictJson.require(ref.bytes()>0,"actual special war Java/native source required"); }
    }
    public record H2743Claim(String snapshotId,BigInteger revision,BigInteger nativeRevision,long dateRaw,
            long actorCharacterId,String episodeRunId,long warId,BigInteger connectionGeneration) {
        public H2743Claim {
            StrictJson.text(snapshotId);StrictJson.text(episodeRunId);
            for(var n:List.of(revision,nativeRevision,connectionGeneration))StrictJson.require(n.signum()>0&&n.compareTo(StrictJson.UINT64_MAX)<=0,"positive H2743 uint64 required");
            StrictJson.require(dateRaw==53217264&&actorCharacterId==29829&&warId==16777231&&episodeRunId.equals(EPISODE)
                    &&snapshotId.equals("native:"+nativeRevision),"exact original H2743 frame required");
        }
    }
    public record Selection(PlanningRequest original,OperationKey operation,Optional<H2743Claim> claim) {
        public Selection {
            Objects.requireNonNull(original);Objects.requireNonNull(operation);Objects.requireNonNull(claim);
            Kind selected=kind(operation);StrictJson.require((selected==Kind.H2743)==claim.isPresent(),"only H2743 requires its exact original caller claim");
            var snapshot=OpportunityJson.toNode(original.observations().snapshot());
            StrictJson.require(snapshot.path("paused").isBoolean()&&snapshot.path("paused").booleanValue()
                    &&snapshot.path("map_ready").isBoolean()&&snapshot.path("map_ready").booleanValue()
                    &&snapshot.path("played_character").path("alive").isBoolean()&&snapshot.path("played_character").path("alive").booleanValue(),"special war READ requires a living paused map");
            if(selected==Kind.H2743)requireClaim(original,claim.orElseThrow());
        }
        public ArmyTypes.Context context(){return new ArmyTypes.Context(original.before(),original.source(),original.sessionId(),original.deadline());}
    }
    /** Data-only result; construction cannot mint a Known, catalog contract, read permit or private Root. */
    public record Observation(Selection selection,Kind kind,OperationKey operation,BigInteger querySequence,BigInteger nativeRevision,RawJson nativeResult,Optional<RawJson> proof) {
        public Observation { Objects.requireNonNull(selection);Objects.requireNonNull(kind);Objects.requireNonNull(operation);Objects.requireNonNull(querySequence);Objects.requireNonNull(nativeRevision);Objects.requireNonNull(nativeResult);Objects.requireNonNull(proof); }
    }
    public record Issued(ReadContract<Observation> contract,PlanningReadRequest request) {
        public Issued { Objects.requireNonNull(contract);Objects.requireNonNull(request); }
    }
    @FunctionalInterface public interface OriginalPacketVerifier { void require(Selection selected,PlanningReadReceipt original); }
    private final OriginalPacketVerifier packets;
    private final Sources sources;
    private final PlanningReadPort reads;
    private final EnumMap<Kind,RootReadContractCatalog.Family<Selection,Observation>> families=new EnumMap<>(Kind.class);
    public ArmySpecialWarReads(Sources sources,PlanningReadPort actualReads,OriginalPacketVerifier actualPackets) {
        this.sources=Objects.requireNonNull(sources);reads=Objects.requireNonNull(actualReads);packets=Objects.requireNonNull(actualPackets);
        for(var kind:Kind.values()) {
            String capability=capability(kind);String family="army-special-war-"+kind.name().toLowerCase(java.util.Locale.ROOT)+"-v1";
            families.put(kind,new RootReadContractCatalog.Family<>(family,Selection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of(capability),sources.definition(),sources.decoder(),this::scopedKey,Selection::operation,s->{
                    StrictJson.require(kind(s.operation())==kind,"special war family selection crossed operation");
                    return new ReadContract<>(family+"-"+ActionCodec.sha256(scopedKey(s).bytes()),s.operation(),Optional.of(capability),capability,
                        ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                        sources.definition(),(request,id)->{verify(s,request);return new NativeRequest(s.operation().value(),capability,nativeArguments(s));},
                        receipt->{verify(s,receipt.request());packets.require(s,receipt);return ArmySpecialWarReadCodec.decode(s,receipt);},
                        receipt->{verify(s,receipt.request());packets.require(s,receipt);return ArmySpecialWarReadCodec.decode(s,receipt);});
                }));
        }
    }
    /** Source files bind the registered contract identity; they are never passed as archived preparation-material locators. */
    private RawJson scopedKey(Selection selected){var n=ArmyJson.parse(key(selected).bytes());var refs=n.putObject("producer_sources");
        refs.set("definition",sources.definition().toJson());refs.set("decoder",sources.decoder().toJson());refs.set("h2743_native",sources.h2743Native().toJson());
        refs.set("prisoner_native",sources.prisonerNative().toJson());refs.set("bound_loss_native",sources.boundLossNative().toJson());return new RawJson(bytes(n));}
    public Sources sources(){return sources;}
    public List<RootReadContractCatalog.Family<?,?>> families(){return families.values().stream().<RootReadContractCatalog.Family<?,?>>map(f->f).toList();}
    public Issued issue(RootReadContractCatalog catalog,Selection selection) {
        var contract=Objects.requireNonNull(catalog).issue(families.get(kind(selection.operation())),selection);
        var original=selection.original();var request=new PlanningReadRequest(original.before(),original.source(),original.sessionId(),selection.operation(),arguments(selection),original.deadline());
        verify(selection,request);return new Issued(contract,request);
    }
    public PlanningReadResult<Observation> collect(Session same,RootReadContractCatalog catalog,Selection selected){var issued=issue(catalog,selected);return reads.read(same,issued.contract(),issued.request());}
    public Observation replay(RootReadContractCatalog catalog,Selection selected,PlanningReadReceipt receipt){var issued=issue(catalog,selected);StrictJson.require(issued.contract().contractId().equals(receipt.contractId()),"original special war contract ID differs");return issued.contract().replay(receipt);}
    /** Data-only cold interpretation from the exact retained archive. It creates no new request/receipt or Root authority. */
    public Observation replayArchived(RootReadContractCatalog catalog,Selection selected,ExactRef expected,ActionPorts.OutcomeArchive archive){
        Objects.requireNonNull(expected);Objects.requireNonNull(archive);var receipt=archive.loadRead(expected);
        StrictJson.require(archive.readReferenceOf(receipt).equals(expected),"cold special READ differs from its canonical original reference");return replay(catalog,selected,receipt);
    }
    public static boolean supports(OperationKey operation){try{kind(operation);return true;}catch(IllegalArgumentException absent){return false;}}
    public static Kind kind(OperationKey operation){String step=operation.value();if(step.equals(H2743))return Kind.H2743;if(parse(step,PRISONERS)>0)return Kind.PRISONERS;if(parse(step,BOUND_LOSS)>0)return Kind.BOUND_LOSS;throw new IllegalArgumentException("not an original special war READ");}
    public static int warId(Selection s){return switch(kind(s.operation())){case H2743->16777231;case PRISONERS->parse(s.operation().value(),PRISONERS);case BOUND_LOSS->parse(s.operation().value(),BOUND_LOSS);};}
    private static int parse(String step,String prefix){if(!step.startsWith(prefix))return 0;String id=step.substring(prefix.length());StrictJson.require(id.matches("[1-9][0-9]{0,9}"),"canonical positive full native war ID required");try{int n=Integer.parseInt(id);StrictJson.require(n>0,"positive war ID required");return n;}catch(NumberFormatException invalid){throw new IllegalArgumentException("full native war ID outside int31",invalid);}}
    public static String capability(Kind kind){return switch(kind){case H2743->"game.command."+H2743;case PRISONERS->"game.command."+PRISONERS+"N";case BOUND_LOSS->"game.command."+BOUND_LOSS+"N";};}
    public static OpportunityJson.Obj arguments(Selection s){return org.xar.ck3.control.application.driver.DriverJson.object(key(s).bytes(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);}
    private static RawJson key(Selection s){var c=s.context();var n=empty().put("step",s.operation().value()).put("machine_id",c.before().machineId()).put("session_id",c.sessionId())
        .put("snapshot_id",c.before().frame().snapshotId()).put("public_revision",c.before().frame().revision().toString()).put("native_revision",c.nativeRevision().toString())
        .put("date_raw",c.dateRaw().toString()).put("actor",c.playerId().toString()).put("episode",c.before().frame().episodeRunId()).put("observation_version",c.before().observationVersion())
        .put("source_build",c.source().exactBuild()).put("source_observed_at",c.source().observedAtUtc());
        n.set("game",c.before().game().toJson());n.set("source",c.source().sourceRef().toJson());n.set("native_arguments",ArmyJson.parse(nativeArguments(s).bytes()));
        n.put("snapshot_sha256",ActionCodec.sha256(StrictJson.canonical(OpportunityJson.toNode(s.original().observations().snapshot()))));return new RawJson(bytes(n));}
    private static void verify(Selection s,PlanningReadRequest request){var original=s.original();StrictJson.require(request.before().equals(original.before())&&request.source().equals(original.source())
        &&request.sessionId().equals(original.sessionId())&&request.operation().equals(s.operation())&&request.arguments().equals(arguments(s)),"special war read crossed original source/frame/claim/arguments");}
    public static RawJson nativeArguments(Selection s){var n=empty();s.claim().ifPresent(c->{n.put("expected_date_raw",c.dateRaw()).put("expected_snapshot_id",c.snapshotId())
        .put("expected_public_revision",c.revision()).put("expected_native_revision",c.nativeRevision()).put("expected_actor_character_id",c.actorCharacterId())
        .put("expected_war_id",c.warId()).put("expected_episode_id",EPISODE).put("expected_checkpoint_sha256",CHECKPOINT).put("expected_exe_sha256",H2743_EXE);});return new RawJson(bytes(n));}
    private static void requireClaim(PlanningRequest original,H2743Claim c){var frame=original.before().frame();var s=OpportunityJson.toNode(original.observations().snapshot());
        StrictJson.require(frame.snapshotId().equals(c.snapshotId())&&frame.revision().equals(c.revision())&&frame.identity().nativeRevision().equals(c.nativeRevision())
            &&frame.identity().dateRaw().equals(BigInteger.valueOf(c.dateRaw()))&&frame.identity().player().equals(BigInteger.valueOf(c.actorCharacterId()))
            &&frame.episodeRunId().equals(c.episodeRunId())&&original.source().exactBuild().equals("1.19.0.6"),"H2743 exact historical build/frame differs");
        StrictJson.require(StrictJson.integer(s.path("diagnostics").path("connection_generation"),BigInteger.ONE,StrictJson.UINT64_MAX).equals(c.connectionGeneration()),"H2743 connection generation differs");
        var wars=s.get("active_wars");StrictJson.require(wars!=null&&wars.isArray(),"H2743 actual wars absent");int found=0;
        for(var war:wars)if(war.path("war_id").isIntegralNumber()&&war.path("war_id").bigIntegerValue().equals(BigInteger.valueOf(c.warId()))){found++;
            StrictJson.require(war.path("player_side").asText().equals("defender")&&war.path("player_is_primary_war_leader").isBoolean()&&war.path("player_is_primary_war_leader").booleanValue()
                &&StrictJson.integer(war.get("primary_opponent_character_id"),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact()==30097
                &&war.path("targeted_title_ids").isArray()&&war.path("targeted_title_ids").size()==1&&war.path("targeted_title_ids").get(0).isIntegralNumber()
                &&war.path("targeted_title_ids").get(0).bigIntegerValue().equals(BigInteger.valueOf(2128)),"H2743 war role/target differs");}
        StrictJson.require(found==1,"H2743 exact war must occur once");}
}
