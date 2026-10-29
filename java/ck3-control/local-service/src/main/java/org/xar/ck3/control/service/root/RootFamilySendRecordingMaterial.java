package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.family.FamilySendObservation;
import org.xar.ck3.control.application.effects.family.FamilySendObservationCodec;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Source-bound migration of the original returned marriage wrapper. Publication DATA grants no business/day credit. */
public final class RootFamilySendRecordingMaterial {
    public static final String SCHEMA = "xar.java.family-send-recording-publication/v1";
    private RootFamilySendRecordingMaterial() { }
    public record Publication(RawJson result, ExactRef resultRef, RawJson witness, ExactRef witnessRef,
            ExactRef originalChoiceRead, List<ExactRef> producers) {
        public Publication { Objects.requireNonNull(result); Objects.requireNonNull(resultRef); Objects.requireNonNull(witness);
            Objects.requireNonNull(witnessRef); Objects.requireNonNull(originalChoiceRead); producers=List.copyOf(producers); }
    }
    public static ExactRef originalContract(ExactRef nativeDriver) {
        StrictJson.require(nativeDriver.bytes()==1658471 && nativeDriver.sha256().equals("eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"),
                "actual reviewed native driver source required");
        return new ExactRef(Path.of(nativeDriver.path()).resolveSibling("marriage_contract.py").toString().replace('\\','/'),
                3370,"f85b94e237f7ec4baa7cb872b29514cec4210afca583fc51075114e6e7e4db71");
    }
    /** Only the original public arrange-marriage route has this exact Python wrapper. Private routes require their own reports. */
    public static boolean supports(ActionReceipt actual) {
        return actual.state() instanceof ActionState.Settled settled
                && settled.settlement() instanceof ActionState.FamilySendConfirmed send
                && send.observation().profile()==FamilySendObservation.Profile.MARRIAGE
                && actual.command().operation().value().startsWith("arrange-marriage-");
    }
    public static Publication capture(RootRuntimeContext context, RootInstalledCatalog catalog, Session same,
            ActionReceipt actual, ActionPorts.OutcomeArchive archive, NativeRecordedEvidenceVerifier.Binding installed,
            ExactRef nativeDriver, List<ExactRef> implementationSources, boolean preserve) throws IOException {
        var producers=new java.util.LinkedHashSet<ExactRef>(implementationSources);
        producers.add(Objects.requireNonNull(nativeDriver));producers.add(originalContract(nativeDriver));
        return captureActual(context,catalog,same,actual,archive,installed,List.copyOf(producers),false,preserve);
    }
    public static Publication captureOrdinary(RootRuntimeContext context, RootInstalledCatalog catalog, Session same,
            ActionReceipt actual, ActionPorts.OutcomeArchive archive, NativeRecordedEvidenceVerifier.Binding installed,
            ExactRef nativeDriver, List<ExactRef> implementationSources, boolean preserve) throws IOException {
        var producers=new java.util.LinkedHashSet<ExactRef>(implementationSources);
        producers.add(Objects.requireNonNull(nativeDriver));
        return captureActual(context,catalog,same,actual,archive,installed,List.copyOf(producers),true,preserve);
    }
    /** Supplied provenance remains DATA; real marriage observations and archived results still decide the result. */
    public static Publication captureOrdinary(RootRuntimeContext context,RootInstalledCatalog catalog,Session same,
            ActionReceipt actual,ActionPorts.OutcomeArchive archive,NativeRecordedEvidenceVerifier.Binding installed,
            java.util.Map<RootActionHistoryMaterialSourceFactory.RecordingRole,ExactRef> actualRecordings,
            java.util.Map<RootActionHistoryMaterialSourceFactory.ReaderRole,ExactRef> actualReaders,
            boolean preserve)throws IOException {
        var recordings=RootActionHistoryMaterialSourceFactory.checkedMetadata(
                RootActionHistoryMaterialSourceFactory.RecordingRole.class,actualRecordings);
        var readers=RootActionHistoryMaterialSourceFactory.checkedMetadata(
                RootActionHistoryMaterialSourceFactory.ReaderRole.class,actualReaders);
        var producers=new java.util.LinkedHashSet<ExactRef>(readers.values());producers.addAll(recordings.values());
        return captureActual(context,catalog,same,actual,archive,installed,List.copyOf(producers),true,preserve);
    }
    private static Publication captureActual(RootRuntimeContext context,RootInstalledCatalog catalog,Session same,
            ActionReceipt actual,ActionPorts.OutcomeArchive archive,NativeRecordedEvidenceVerifier.Binding installed,
            List<ExactRef> producerMetadata,boolean ordinary,boolean preserve)throws IOException {
        context.writer().requireSession(same);
        StrictJson.require(catalog.context()==context && supports(actual)
                && catalog.bindings().actualArchivedVerifier(actual.command().operation()).orElseThrow()==installed,
                "family recording requires the identical installed domain archived verifier");
        if(!ordinary)StrictJson.require(producerMetadata.stream().anyMatch(ref -> ref.path().replace('\\','/').endsWith("/RootFamilySendRecordingMaterial.java")),
                "actual recording producer must be included in the selected material source closure");
        installed.verifier().verify(same.head(),actual,archive);
        var settled=(ActionState.Settled)actual.state();
        var send=((ActionState.FamilySendConfirmed)settled.settlement()).observation();
        send.validate(actual.command(),settled.attempt(),settled.dispatch(),archive);
        var intent=RulerMarriageIntent.fromJson(actual.command().arguments());
        if(intent.planningProof().isEmpty())throw missing(actual);
        var proof=intent.planningProof().orElseThrow();
        StrictJson.require(proof.members().keySet().equals(Set.of("query_sequence","original_query")),"complete original public choice locator required");
        ExactRef query=ExactRef.fromJson(OpportunityJson.toNode(proof.get("original_query")));
        var original=catalog.remainingDomains().family().nativeReads().originalRuler(same,actual.command(),query);
        StrictJson.require(original.originalReceipt().equals(query)
                && Objects.equals(original.value().get("query_sequence"),proof.get("query_sequence")),"original choice query sequence/reference changed");
        var choices=OpportunityJson.array(original.value().get("arrange_marriage_choices"),"actual original marriage choices");
        var rows=choices.stream().map(value -> OpportunityJson.object(value,"original choice"))
                .filter(row -> Objects.equals(row.get("choice_id"),new OpportunityJson.Text(intent.choiceId()))).toList();
        StrictJson.require(rows.size()==1,"unique actual original full choice required");
        ObjectNode choice=(ObjectNode)OpportunityJson.toNode(rows.getFirst());
        StrictJson.require(StrictJson.integer(choice.get("played_character_id"),1,0xFFFF_FFFEL)==intent.actorId()
                && StrictJson.integer(choice.get("candidate_character_id"),1,0xFFFF_FFFEL)==intent.candidateId(),"original choice differs from immutable intent");
        var ack=(NativeActionPort.AckReceived)settled.dispatch();
        if(ack.originalResultToken().isEmpty())throw missing(actual);
        RawJson result=project(actual.command().operation().value(),choice,ack.originalResultToken().orElseThrow(),
                send.before().frame().identity().dateRaw().intValueExact());
        var producers=new java.util.LinkedHashSet<ExactRef>(producerMetadata);
        if(!ordinary)for(ExactRef ref:producers){var pin=same.capturePin(ref,org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
        ExactRef resultRef=retain(result,archive,preserve);
        ObjectNode witness=StrictJson.object().put("schema",SCHEMA).put("action_id",actual.command().actionId())
                .put("command_sha256",ActionCodec.bodySha256(actual.command())).put("request_id",settled.attempt().requestId());
        witness.set("original_choice_read",query.toJson());witness.set("result",resultRef.toJson());
        witness.set("family_send",FamilySendObservationCodec.encode(send,archive));
        var refs=witness.putArray("producers");producers.forEach(ref -> refs.add(ref.toJson()));
        RawJson raw=raw(witness);ExactRef witnessRef=retain(raw,archive,preserve);
        // Reopen the actual typed observation, including both independent reads; no ACK or READ marker becomes an action.
        ObjectNode reopened=StrictJson.object(StrictJson.parse(archive.loadMaterial(witnessRef).bytes()),
                Set.of("schema","action_id","command_sha256","request_id","original_choice_read","result","family_send","producers"));
        StrictJson.require(FamilySendObservationCodec.decode(reopened.get("family_send"),archive).equals(send)
                && archive.loadMaterial(resultRef).equals(result),"original recording publication replay changed");
        context.writer().requireSession(same);
        return new Publication(result,resultRef,raw,witnessRef,query,List.copyOf(producers));
    }
    /** Exact original normalize-choice + primitive projection + wrapper producer; caller supplies actual source-qualified originals. */
    public static RawJson project(String step,ObjectNode actualChoice,RawJson originalPrimitive,int submittedDateRaw) {
        String choiceId=StrictJson.text(actualChoice.get("choice_id"));
        long played=StrictJson.integer(actualChoice.get("played_character_id"),1,0xFFFF_FFFEL);
        long candidate=StrictJson.integer(actualChoice.get("candidate_character_id"),1,0xFFFF_FFFEL);
        StrictJson.require(played!=candidate && choiceId.equals(played+"-"+candidate) && step.equals("arrange-marriage-"+choiceId),"exact original marriage pair/step required");
        ObjectNode choice=StrictJson.object().put("choice_id",choiceId).put("played_character_id",played)
                .put("candidate_character_id",candidate).put("source","native");
        JsonNode token=StrictJson.parse(originalPrimitive.bytes());ObjectNode result;
        if(token instanceof ObjectNode object)result=object.deepCopy();else {result=StrictJson.object();result.set("result",token);}
        result.put("backend_id","native-headless");result.set("marriage_choice",choice);
        result.set("marriage_action",StrictJson.object().put("status","proposal_submitted").put("choice_id",choiceId)
                .put("played_character_id",played).put("candidate_character_id",candidate).put("submitted_date_raw",submittedDateRaw));
        return raw(result);
    }
    private static RootActionHistoryMaterialSourceFactory.Missing missing(ActionReceipt actual){return new RootActionHistoryMaterialSourceFactory.Missing(
            RootActionHistoryMaterialSourceFactory.MissingReason.ORIGINAL_COMPATIBLE_RESULT_ABSENT,actual.command().operation());}
    private static ExactRef retain(RawJson raw,ActionPorts.OutcomeArchive archive,boolean preserve){
        ExactRef ref=preserve?archive.preserveMaterial(raw):archive.materialReferenceOf(raw);
        StrictJson.require(archive.loadMaterial(ref).equals(raw),"original recording material changed");return ref;
    }
    private static RawJson raw(ObjectNode value){return new RawJson(DriverJson.encodeNode(value));}
}
