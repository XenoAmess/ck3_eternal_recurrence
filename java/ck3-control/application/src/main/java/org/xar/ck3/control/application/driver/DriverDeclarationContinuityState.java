package org.xar.ck3.control.application.driver;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.military.WarDeclarationContinuity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;

/** Canonical declaration DATA -> ordinary snapshot. Cold replay never collects or submits Native. */
final class DriverDeclarationContinuityState {
    static final String KEY="war_declaration_continuity_v1";
    static final String SOURCE="war_declaration_continuity_source";
    private static final String SCHEMA="xar.driver-canonical-declaration-source/v1";
    private DriverDeclarationContinuityState() { }

    static Obj capture(ContinuityStorePort.Session same,Complete frame,Obj auxiliary,List<ActionReceipt> canonical,
            ActionPorts.RecordedEvidenceVerifier evidence,ActionPorts.OutcomeArchive archive) throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(frame);Objects.requireNonNull(evidence);
        replay(auxiliary,archive);
        var head=same.head();var actual=ContinuityActionJournal.receipts(head.state(),archive);
        require(actual.equals(List.copyOf(canonical)),"declaration projection requires the same complete canonical action inventory");
        require(head.state().machineId().equals(frame.identity().machineId()),"declaration projection crossed the actual writer machine");
        if(auxiliary.members().containsKey(SOURCE)) {
            Obj old=material(reference(auxiliary.get(SOURCE)),archive);
            if(old.get("selected")!=Nil.INSTANCE) {
                ActionReceipt retained=archive.loadReceipt(reference(old.get("selected")));
                ContinuityActionJournal.requireHistoricalReceipt(head.state(),retained,archive);
            }
        }
        Optional<ActionReceipt> selected=selected(actual);
        selected.ifPresent(receipt->evidence.verify(head,receipt));
        Value result=project(head.state(),selected,frame,archive);
        Value selectedRef=selected.<Value>map(receipt->ref(archive.receiptReferenceOf(receipt))).orElse(Nil.INSTANCE);
        if(auxiliary.members().containsKey(SOURCE)&&Objects.equals(auxiliary.get(KEY),result)) {
            Obj previous=material(reference(auxiliary.get(SOURCE)),archive);
            if(previous.get("selected").equals(selectedRef))return auxiliary;
        }
        byte[] state=ContinuityJson.canonical(head.state().toJson());
        ExactRef stateRef=archive.preserveMaterial(new RawJson(state));
        require(stateRef.sha256().equals(head.digest()),"canonical declaration state digest changed");
        Value manifest=frame.semantic().get("java_driver_facts_evidence");
        require(manifest instanceof Obj,"declaration projection requires the actual complete Driver/native manifest");
        Obj proof=new Obj(Map.of("schema",new Text(SCHEMA),"canonical_state",ref(stateRef),
                "frame",new Obj(Map.of("manifest",manifest,"native",ref(frame.originalEvidence()))),
                "selected",selectedRef,"projection",result));
        ExactRef source=archive.preserveMaterial(new RawJson(DriverJson.encode(proof)));
        Obj changed=auxiliary.with(KEY,result).with(SOURCE,ref(source));
        replay(changed,archive);return changed;
    }

    /** Legacy all-missing is distinct from an explicit empty canonical inventory. */
    static void replay(Obj auxiliary,ActionPorts.OutcomeArchive archive) {
        boolean present=auxiliary.members().containsKey(KEY);
        require(present==auxiliary.members().containsKey(SOURCE),"declaration projection and original source must be present together");
        if(!present)return;
        Obj proof=material(reference(auxiliary.get(SOURCE)),archive);
        require(proof.members().keySet().equals(Set.of("schema","canonical_state","frame","selected","projection"))
                &&new Text(SCHEMA).equals(proof.get("schema")),"exact canonical declaration source schema required");
        Obj basis=object(proof.get("frame"),"original declaration projection frame");
        require(basis.members().keySet().equals(Set.of("manifest","native")),"exact original declaration frame roles required");
        Complete frame=rebuild(basis,archive);
        ExactRef stateRef=reference(proof.get("canonical_state"));
        RawJson original=archive.loadMaterial(stateRef);exact(stateRef,original.bytes());
        var state=ContinuityState.fromJson(ContinuityJson.parseObject(original.bytes(),ContinuityJson.LEDGER_MAX_BYTES),frame.identity().machineId());
        require(stateRef.sha256().equals(ContinuityJson.digest(state.toJson())),"original canonical declaration state changed");
        Optional<ActionReceipt> selected=selected(ContinuityActionJournal.receipts(state,archive));
        Value expected=selected.<Value>map(receipt->ref(archive.receiptReferenceOf(receipt))).orElse(Nil.INSTANCE);
        require(expected.equals(proof.get("selected")),"saved declaration is not the latest original canonical action");
        Value result=project(state,selected,frame,archive);
        require(result.equals(proof.get("projection"))&&result.equals(auxiliary.get(KEY)),"declaration snapshot differs from its original canonical producer");
    }
    private static Optional<ActionReceipt> selected(List<ActionReceipt> canonical) {
        return canonical.stream().filter(receipt->receipt.command().origin() instanceof CommandOrigin.Gameplay
                &&receipt.command().operation().value().startsWith("declare-war-"))
                .max(Comparator.comparingLong(ActionReceipt::sequence));
    }
    private static Value project(ContinuityState state,Optional<ActionReceipt> selected,Complete frame,ActionPorts.OutcomeArchive archive) {
        if(selected.isEmpty())return Nil.INSTANCE;
        ActionReceipt receipt=selected.orElseThrow();
        require(receipt.equals(archive.loadReceipt(archive.receiptReferenceOf(receipt)))
                &&receipt.bodySha256().equals(ActionCodec.bodySha256(receipt.command())),"original declaration receipt/body changed");
        // INTENT and pre-guard UNKNOWN have no native RequestID. Keep their
        // canonical source and existing action-fact blocker; never invent a ticket.
        var attempt=ActionTransitions.attempt(receipt.state());if(attempt.isEmpty())return Nil.INSTANCE;
        Complete before=RootGuardEvidence.loadFrame(attempt.orElseThrow().guard(),archive,
                new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
        var prior=ContinuityActionJournal.receiptsBeforeIntent(state,receipt.command().actionId(),archive);
        var record=WarDeclarationContinuity.replay(receipt,prior,before,frame,archive);
        return WarDeclarationContinuity.json(record);
    }
    private static Complete rebuild(Obj basis,ActionPorts.OutcomeArchive archive) {
        ExactRef manifest=reference(basis.get("manifest")),nativeRef=reference(basis.get("native"));
        RawJson body=archive.loadMaterial(manifest);exact(manifest,body.bytes());
        var nativeFrame=DriverObservationEvidenceReader.nativeFrame(manifest,body,archive.loadNativeFrame(nativeRef));
        RawJson driver=archive.loadMaterial(DriverObservationEvidenceReader.currentDriverReference(manifest,body));
        var facts=DriverObservationEvidenceReader.decode(manifest,body,driver,nativeFrame);
        var rebuilt=new DriverObservationAssembler().assemble(nativeFrame,facts,nativeRef);
        require(rebuilt instanceof Complete,"saved declaration lacks its actual complete Driver/native frame");return (Complete)rebuilt;
    }
    private static Obj material(ExactRef ref,ActionPorts.OutcomeArchive archive) {
        RawJson body=archive.loadMaterial(ref);exact(ref,body.bytes());return DriverJson.object(body.bytes(),DriverJson.MAX_NATIVE_BYTES);
    }
    private static void exact(ExactRef ref,byte[] bytes) {require(ref.bytes()==bytes.length&&ref.sha256().equals(DriverJson.sha256(bytes)),"declaration original bytes/SHA changed");}
    private static Obj ref(ExactRef value) {return org.xar.ck3.control.application.capabilities.DriverRuntimeCapabilities.referenceJson(value);}
    private static ExactRef reference(Value value) {return DriverObservationEvidenceReader.reference(value);}
}
