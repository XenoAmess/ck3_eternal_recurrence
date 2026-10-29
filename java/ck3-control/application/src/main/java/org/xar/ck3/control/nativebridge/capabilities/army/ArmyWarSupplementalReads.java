package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaselineAdapter;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaselineCodec;

/** The two original advertised read-only families; no action, retry, private permit or fabricated baseline. */
public final class ArmyWarSupplementalReads {
    public static final String LOCAL_PREFIX="query-province-local-siege-v1-";
    public static final String BASELINE_PREFIX="query-defender-de-jure-exit-terms-v1-";
    public enum Kind { LOCAL_SIEGE,DEFENDER_BASELINE }
    public record StockSources(ExactRef decoder,ExactRef pair,ExactRef pins,java.nio.file.Path nativeSourceCheckout){
        public StockSources{for(var source:List.of(decoder,pair,pins))StrictJson.require(source.bytes()>0,"actual stock parser/pair/independent pins originals required");StrictJson.require(nativeSourceCheckout!=null&&nativeSourceCheckout.isAbsolute(),"explicit absolute native source checkout required");nativeSourceCheckout=nativeSourceCheckout.normalize();}
    }
    public record Sources(ExactRef definition,ExactRef decoder,ExactRef provinceNative,ExactRef deJureNative,Optional<StockSources> stockSources){
        public Sources{for(var source:List.of(definition,decoder,provinceNative,deJureNative))StrictJson.require(source.bytes()>0,"actual Java and native supplemental war sources required");Objects.requireNonNull(stockSources);}
        public Sources(ExactRef definition,ExactRef decoder,ExactRef provinceNative,ExactRef deJureNative){this(definition,decoder,provinceNative,deJureNative,Optional.empty());}
    }
    public record Selection(PlanningRequest original,OperationKey operation){
        public Selection{
            Objects.requireNonNull(original);Objects.requireNonNull(operation);Kind kind=kind(operation);
            var snapshot=DriverJson.toNode(original.observations().snapshot());
            StrictJson.require(snapshot.path("paused").isBoolean()&&snapshot.path("paused").booleanValue(),"supplemental war read requires the actual paused snapshot");
            if(kind==Kind.DEFENDER_BASELINE)requireDefender(original,id(operation));
        }
        public ArmyTypes.Context context(){return new ArmyTypes.Context(original.before(),original.source(),original.sessionId(),original.deadline());}
    }
    public sealed interface Observation permits LocalSiege,DefenderBaseline,DefenderStock{
        Selection selection();RawJson nativeResult();RawJson normalizedResult();
    }
    /** Original numeric result and its exact normalizer projection; a record constructor grants no native authority. */
    public record LocalSiege(Selection selection,RawJson nativeResult,RawJson normalizedResult)implements Observation{
        public LocalSiege{Objects.requireNonNull(selection);Objects.requireNonNull(nativeResult);Objects.requireNonNull(normalizedResult);}
    }
    /** Both actual archived guard snapshots are retained separately; no copy of before can stand in for after. */
    public record DefenderBaseline(Selection selection,RawJson nativeResult,RawJson before,RawJson after,
            DeJureExitBaselineAdapter.BoundBaseline baseline,RawJson normalizedResult)implements Observation{
        public DefenderBaseline{Objects.requireNonNull(selection);Objects.requireNonNull(nativeResult);Objects.requireNonNull(before);Objects.requireNonNull(after);Objects.requireNonNull(baseline);Objects.requireNonNull(normalizedResult);}
    }
    /** Source verification and this parsed DATA cannot retain a private live admission. */
    public record DefenderStock(Selection selection,RawJson nativeResult,RawJson before,RawJson after,
            DefenderBaseline common,H2743StockPredicateAdmission.VerifiedData source,
            ArmyWarSupplementalStockCodec.StockEvidence evidence,RawJson normalizedResult)implements Observation{
        public DefenderStock{Objects.requireNonNull(selection);Objects.requireNonNull(nativeResult);Objects.requireNonNull(before);Objects.requireNonNull(after);Objects.requireNonNull(common);Objects.requireNonNull(source);Objects.requireNonNull(evidence);Objects.requireNonNull(normalizedResult);}
        public java.math.BigInteger actualMailboxSequence(){return evidence.mailboxSequence();}
    }
    public enum DecodeMode{LIVE,ARCHIVED}
    @FunctionalInterface public interface StockWork{DefenderStock normalize(H2743StockPredicateAdmission.VerifiedData actualData);}
    /** Only the installed host supplies this port. DTOs/flags do not implement its private source scope.
     * LIVE accepts the actual mailbox only after work succeeds; ARCHIVED verifies DATA without advancing it. */
    @FunctionalInterface public interface StockAdmissionPort{
        DefenderStock withAdmission(Selection selected,PlanningReadReceipt original,Complete before,Complete after,DecodeMode mode,StockWork work);
    }
    /** Native transport owns the sole wire parser. This port validates its complete originals, not permissions. */
    @FunctionalInterface public interface OriginalPacketVerifier{void require(Selection selection,PlanningReadReceipt receipt);}
    public record Issued(ReadContract<Observation> contract,PlanningReadRequest request){public Issued{Objects.requireNonNull(contract);Objects.requireNonNull(request);}}
    private final Sources sources;private final PlanningReadPort reads;
    private final Supplier<ActionPorts.OutcomeArchive> archives;private final NativeEffectEvidence.FrameLoader frames;
    private final OriginalPacketVerifier packets;
    private final Optional<StockAdmissionPort> stock;
    private final EnumMap<Kind,RootReadContractCatalog.Family<Selection,Observation>> families=new EnumMap<>(Kind.class);
    public ArmyWarSupplementalReads(Sources sources,PlanningReadPort actualReads,Supplier<ActionPorts.OutcomeArchive> sameArchives,
            NativeEffectEvidence.FrameLoader actualFrames,OriginalPacketVerifier actualPackets){
        this(sources,actualReads,sameArchives,actualFrames,actualPackets,Optional.empty());
    }
    public ArmyWarSupplementalReads(Sources sources,PlanningReadPort actualReads,Supplier<ActionPorts.OutcomeArchive> sameArchives,
            NativeEffectEvidence.FrameLoader actualFrames,OriginalPacketVerifier actualPackets,StockAdmissionPort actualStock){
        this(sources,actualReads,sameArchives,actualFrames,actualPackets,Optional.of(Objects.requireNonNull(actualStock)));
        StrictJson.require(sources.stockSources().isPresent(),"actual stock parser/pair/pins sources must be installed with the private port");
    }
    private ArmyWarSupplementalReads(Sources sources,PlanningReadPort actualReads,Supplier<ActionPorts.OutcomeArchive> sameArchives,
            NativeEffectEvidence.FrameLoader actualFrames,OriginalPacketVerifier actualPackets,Optional<StockAdmissionPort> stock){
        this.sources=Objects.requireNonNull(sources);reads=Objects.requireNonNull(actualReads);archives=Objects.requireNonNull(sameArchives);
        frames=Objects.requireNonNull(actualFrames);packets=Objects.requireNonNull(actualPackets);
        this.stock=Objects.requireNonNull(stock);
        for(Kind kind:Kind.values()){
            String capability=capability(kind),family="army-supplemental-war-"+kind.name().toLowerCase(java.util.Locale.ROOT)+"-v1";
            families.put(kind,new RootReadContractCatalog.Family<>(family,Selection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.of(capability),sources.definition(),sources.decoder(),this::scopedKey,Selection::operation,selected->{
                StrictJson.require(kind(selected.operation())==kind,"supplemental family crossed selected operation");
                return new ReadContract<>(family+"-"+ActionCodec.sha256(scopedKey(selected).bytes()),selected.operation(),Optional.of(capability),capability,
                        ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                        sources.definition(),(request,id)->{verify(selected,request);return new NativeRequest(selected.operation().value(),capability,nativeArguments());},
                        receipt->decode(selected,receipt,DecodeMode.LIVE),receipt->decode(selected,receipt,DecodeMode.ARCHIVED));
            }));
        }
    }
    public Sources sources(){return sources;}
    public List<RootReadContractCatalog.Family<?,?>> families(){return families.values().stream().<RootReadContractCatalog.Family<?,?>>map(f->f).toList();}
    public Issued issue(RootReadContractCatalog catalog,Selection selected){
        var contract=Objects.requireNonNull(catalog).issue(families.get(kind(selected.operation())),selected);var original=selected.original();
        var request=new PlanningReadRequest(original.before(),original.source(),original.sessionId(),selected.operation(),arguments(selected),original.deadline());
        verify(selected,request);return new Issued(contract,request);
    }
    public PlanningReadResult<Observation> collect(Session same,RootReadContractCatalog catalog,Selection selected){var issued=issue(catalog,selected);return reads.read(same,issued.contract(),issued.request());}
    public Observation replay(RootReadContractCatalog catalog,Selection selected,PlanningReadReceipt original){
        var issued=issue(catalog,selected);StrictJson.require(original.contractId().equals(issued.contract().contractId()),"original supplemental read belongs to another installed contract");return issued.contract().replay(original);
    }
    public Observation replayArchived(RootReadContractCatalog catalog,Selection selected,ExactRef original,ActionPorts.OutcomeArchive sameArchive){
        Objects.requireNonNull(original);Objects.requireNonNull(sameArchive);var receipt=sameArchive.loadRead(original);
        StrictJson.require(sameArchive.readReferenceOf(receipt).equals(original),"cold supplemental receipt differs from its canonical reference");
        NativeRecordedEvidenceVerifier.requireRead(receipt,sameArchive);return replay(catalog,selected,receipt);
    }
    private Observation decode(Selection selected,PlanningReadReceipt receipt,DecodeMode mode){
        verify(selected,receipt.request());var context=selected.context();ArmyNativeReadEvidence.verifyContext(context,receipt);
        packets.require(selected,receipt);ArmyNativeReadEvidence.result(context,receipt);
        // Validation consumes the original frame/token; the observation retains the exact token bytes.
        var result=receipt.original().originalResultToken().orElseThrow();
        if(kind(selected.operation())==Kind.LOCAL_SIEGE)return ArmyWarSupplementalReadCodec.normalizeLocalSiege(selected,result);
        var archive=Objects.requireNonNull(archives.get(),"actual same-writer archive required for original defender before/after");
        var before=RootGuardEvidence.loadFrame(receipt.before().binding(),archive,frames);
        var after=RootGuardEvidence.loadFrame(receipt.after().binding(),archive,frames);
        StrictJson.require(before.identity().equals(selected.original().before())&&before.source().equals(selected.original().source())
                &&before.sessionId().equals(selected.original().sessionId())&&before.semantic().equals(selected.original().observations().snapshot()),
                "defender selected snapshot differs from the actual archived before frame");
        var rawBefore=new RawJson(DriverJson.encode(before.semantic()));var rawAfter=new RawJson(DriverJson.encode(after.semantic()));
        if(ArmyWarSupplementalReadCodec.object(result).path("defender_de_jure_exit_terms_v1").has("h2743_stock_predicate_evidence_v1")){
            var actual=stock.orElseThrow(()->new IllegalStateException("source-admitted stock result lacks an installed private source admission port"));
            return actual.withAdmission(selected,receipt,before,after,mode,data->{
                requireStockSources(sources.stockSources().orElseThrow(),data);
                return ArmyWarSupplementalStockCodec.normalize(selected,result,rawBefore,rawAfter,data);
            });
        }
        return ArmyWarSupplementalReadCodec.normalizeBaseline(selected,result,rawBefore,rawAfter);
    }
    public static boolean supports(OperationKey operation){try{kind(operation);return true;}catch(IllegalArgumentException unsupported){return false;}}
    public static Kind kind(OperationKey operation){String step=Objects.requireNonNull(operation).value();if(parse(step,LOCAL_PREFIX)>0)return Kind.LOCAL_SIEGE;if(DeJureExitBaselineCodec.parseQueryStep(step).isPresent())return Kind.DEFENDER_BASELINE;throw new IllegalArgumentException("not an original supplemental war READ");}
    public static int id(OperationKey operation){return switch(kind(operation)){case LOCAL_SIEGE->parse(operation.value(),LOCAL_PREFIX);case DEFENDER_BASELINE->DeJureExitBaselineCodec.parseQueryStep(operation.value()).orElseThrow();};}
    public static String capability(Kind kind){return switch(kind){case LOCAL_SIEGE->"game.command.query-province-local-siege-v1-N";case DEFENDER_BASELINE->"game.command.query-defender-de-jure-exit-terms-v1-N";};}
    public static RawJson nativeArguments(){return new RawJson(new byte[]{'{','}'});}
    public static OpportunityJson.Obj arguments(Selection selected){return DriverJson.object(key(selected).bytes(),DriverJson.MAX_NATIVE_BYTES);}
    private RawJson scopedKey(Selection selected){var row=ArmyWarSupplementalReadCodec.object(key(selected));var refs=row.putObject("producer_sources");refs.set("definition",sources.definition().toJson());refs.set("decoder",sources.decoder().toJson());refs.set("province_native",sources.provinceNative().toJson());refs.set("de_jure_native",sources.deJureNative().toJson());sources.stockSources().ifPresent(source->{var stock=refs.putObject("stock_sources");stock.set("decoder",source.decoder().toJson());stock.set("pair",source.pair().toJson());stock.set("pins",source.pins().toJson());stock.put("native_source_checkout",source.nativeSourceCheckout().toString());});return ArmyWarSupplementalReadCodec.json(row);}
    private static void requireStockSources(StockSources sources,H2743StockPredicateAdmission.VerifiedData data){
        var receipt=ArmyWarSupplementalReadCodec.object(H2743StockPredicateAdmission.validateSourceReceipt(data.sourceReceipt(),data.profile()));
        StrictJson.require(receipt.path("pair_sha256").asText().equalsIgnoreCase(sources.pair().sha256())
                &&receipt.path("stock_predicate_pins_sha256").asText().equalsIgnoreCase(sources.pins().sha256()),"stock admission differs from original scoped pair/pins");
        var checkout=receipt.get("native_source_checkout");StrictJson.require(checkout!=null&&checkout.isTextual()&&java.nio.file.Path.of(checkout.textValue()).toAbsolutePath().normalize().equals(sources.nativeSourceCheckout()),"stock admission differs from original scoped source checkout");
        for(var ref:List.of(sources.pair(),sources.pins()))StrictJson.require(data.completeFiles().stream().anyMatch(file->file.path().toAbsolutePath().normalize().equals(java.nio.file.Path.of(ref.path()).toAbsolutePath().normalize())&&file.bytes()==ref.bytes()&&file.sha256().equalsIgnoreCase(ref.sha256())),"stock original pair/pins is absent from the verified complete closure");
    }
    private static RawJson key(Selection selected){var c=selected.context();var frame=c.before().frame();var row=StrictJson.object().put("step",selected.operation().value()).put("machine_id",c.before().machineId()).put("session_id",c.sessionId())
            .put("snapshot_id",frame.snapshotId()).put("public_revision",frame.revision().toString()).put("native_revision",c.nativeRevision().toString()).put("date_raw",c.dateRaw().toString())
            .put("actor",c.playerId().toString()).put("episode",frame.episodeRunId()).put("observation_version",c.before().observationVersion()).put("source_build",c.source().exactBuild()).put("source_observed_at",c.source().observedAtUtc());
        row.set("game",c.before().game().toJson());row.set("source",c.source().sourceRef().toJson());row.put("snapshot_sha256",ActionCodec.sha256(DriverJson.encode(selected.original().observations().snapshot())));return ArmyWarSupplementalReadCodec.json(row);
    }
    private static void verify(Selection selected,PlanningReadRequest request){var original=selected.original();StrictJson.require(request.before().equals(original.before())&&request.source().equals(original.source())&&request.sessionId().equals(original.sessionId())
            &&request.operation().equals(selected.operation())&&request.arguments().equals(arguments(selected)),"supplemental read crossed its actual source/frame/typed selection");}
    private static int parse(String step,String prefix){if(!step.startsWith(prefix))return 0;String suffix=step.substring(prefix.length());if(!suffix.matches("[1-9][0-9]{0,9}"))return 0;try{int id=Integer.parseInt(suffix);return id>0?id:0;}catch(NumberFormatException outside){return 0;}}
    private static void requireDefender(PlanningRequest original,int warId){
        var snapshot=DriverJson.toNode(original.observations().snapshot());var wars=snapshot.get("active_wars");StrictJson.require(wars!=null&&wars.isArray(),"actual defender active wars required");
        com.fasterxml.jackson.databind.JsonNode selected=null;for(var war:wars)if(war.isObject()&&war.path("war_id").isIntegralNumber()&&war.path("war_id").bigIntegerValue().equals(java.math.BigInteger.valueOf(warId))){selected=war;break;}
        StrictJson.require(selected!=null&&selected.path("player_side").isTextual()&&selected.path("player_side").textValue().equals("defender")&&selected.path("player_is_primary_war_leader").isBoolean()&&selected.path("player_is_primary_war_leader").booleanValue()
                &&snapshot.path("played_character").path("character_id").isIntegralNumber()&&selected.path("primary_opponent_character_id").isIntegralNumber()&&selected.path("targeted_title_ids").isArray()&&!selected.path("targeted_title_ids").isEmpty(),
                "native defender de-jure exit baseline requires a paused primary defender war");
    }
}
