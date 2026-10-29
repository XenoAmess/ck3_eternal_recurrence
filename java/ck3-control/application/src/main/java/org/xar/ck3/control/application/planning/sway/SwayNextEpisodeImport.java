package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.SavedFirstCheckpointMaterialStore;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.lifecycle.LifecycleProofCodec;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Replays actual FIRST originals into their NEXT or restored physical scope; the entire prior body stays reachable. */
public final class SwayNextEpisodeImport {
    public static final String LEGACY_SCHEMA="xar.java.sway-next-episode-origin/v1";
    public static final String SCHEMA="xar.java.sway-episode-domain-origin/v2";
    public static final String LEGACY_INPUT_SCHEMA="xar.java.sway-next-episode-import/v1";
    public static final String INPUT_SCHEMA="xar.java.sway-episode-domain-import/v2";
    public enum Format { LEGACY_NEXT, CURRENT }
    public enum Kind { NEXT, RESTORED_FIRST }
    private SwayNextEpisodeImport() { }
    public record Basis(Format format,Kind kind,DomainBodies.BodyRef predecessor,SessionIdentity beforeSession,
            SessionIdentity savedSession,SessionIdentity afterSession,ExactRef predecessorDriver,ExactRef firstSavedDriver,
            ExactRef currentDriver,ExactRef originalBaselineMaterial,ExactRef archivedBaselineMaterial,
            EpisodeWindow.CommittedBaseline baseline,SemanticEvidence savedSemantic,SemanticEvidence currentSemantic,G2Source source,
            ExactRef canonicalParent,ExactRef lifecycleProof,long initializationHeadSequence,String initializationHeadDigest) {
        public Basis {
            for(Object value:List.of(format,kind,predecessor,beforeSession,savedSession,afterSession,predecessorDriver,firstSavedDriver,currentDriver,
                    originalBaselineMaterial,archivedBaselineMaterial,baseline,savedSemantic,currentSemantic,source,canonicalParent,lifecycleProof))Objects.requireNonNull(value);
            require(predecessor.slot()==DomainBodies.Slot.SWAY&&predecessor.contractSchema().equals(SwayFormalState.SCHEMA),"actual predecessor Sway body required");
            require(beforeSession.machineId().equals(savedSession.machineId())&&savedSession.machineId().equals(afterSession.machineId())
                    &&!beforeSession.game().equals(savedSession.game()),"actual distinct NEXT Game births on the same writer machine required");
            require(originalBaselineMaterial.bytes()==archivedBaselineMaterial.bytes()&&originalBaselineMaterial.sha256().equals(archivedBaselineMaterial.sha256()),"archived BASELINE must retain exact source bytes");
            require(initializationHeadSequence>0&&initializationHeadDigest!=null&&initializationHeadDigest.matches("[a-f0-9]{64}"),"actual initialization head required");
            if(kind==Kind.NEXT)require(savedSession.equals(afterSession)&&initializationHeadSequence==baseline.sequence()&&initializationHeadDigest.equals(baseline.headDigest()),"NEXT current owner and initialization anchor must be its actual first saved BASELINE");
            else require(!savedSession.game().equals(afterSession.game())&&!beforeSession.game().equals(afterSession.game())&&initializationHeadSequence>baseline.sequence(),"FIRST restore needs its actual distinct restored Game and later RESTORED anchor");
            require(source.machineId().equals(afterSession.machineId()),"current Sway source machine differs");
            requireSemanticOwner(savedSemantic,savedSession,baseline.baseline().savedIdentity());requireSemanticOwner(currentSemantic,afterSession,baseline.baseline().savedIdentity());
            if(format==Format.LEGACY_NEXT)require(kind==Kind.NEXT&&currentDriver.equals(firstSavedDriver)&&currentSemantic.equals(savedSemantic)
                    &&initializationHeadSequence==baseline.sequence()&&initializationHeadDigest.equals(baseline.headDigest()),"explicit legacy NEXT has only its original saved current scope");
        }
        /** Exact v1 constructor is retained only for historical serialization and software originals. */
        public Basis(DomainBodies.BodyRef predecessor,SessionIdentity beforeSession,SessionIdentity afterSession,
                ExactRef predecessorDriver,ExactRef firstSavedDriver,ExactRef originalBaselineMaterial,ExactRef archivedBaselineMaterial,
                EpisodeWindow.CommittedBaseline baseline,SemanticEvidence savedSemantic,G2Source source,ExactRef canonicalParent,ExactRef lifecycleProof) {
            this(Format.LEGACY_NEXT,Kind.NEXT,predecessor,beforeSession,afterSession,afterSession,predecessorDriver,firstSavedDriver,firstSavedDriver,
                    originalBaselineMaterial,archivedBaselineMaterial,baseline,savedSemantic,savedSemantic,source,canonicalParent,lifecycleProof,baseline.sequence(),baseline.headDigest());
        }
        public List<ExactRef> evidence(){var refs=new java.util.ArrayList<ExactRef>(List.of(predecessor.payload(),predecessorDriver,firstSavedDriver,currentDriver,originalBaselineMaterial,archivedBaselineMaterial,baseline.eventRef(),canonicalParent,lifecycleProof));refs.addAll(savedSemantic.references());refs.addAll(currentSemantic.references());return refs.stream().distinct().toList();}
    }
    public static byte[] encode(Basis value) {
        var row=StrictJson.object();row.put("schema",value.format()==Format.LEGACY_NEXT?LEGACY_SCHEMA:SCHEMA);row.put("current_native_sway_observation","unqueried");row.put("old_request_replayed",false);row.set("predecessor",value.predecessor().toJson());
        row.set("before_session",OrdinaryCycleTransitions.sessionToJson(value.beforeSession()));row.set("after_session",OrdinaryCycleTransitions.sessionToJson(value.afterSession()));
        row.set("predecessor_driver",value.predecessorDriver().toJson());row.set("first_saved_driver",value.firstSavedDriver().toJson());
        row.set("original_baseline_material",value.originalBaselineMaterial().toJson());row.set("archived_baseline_material",value.archivedBaselineMaterial().toJson());
        row.set("baseline",value.baseline().toJson());row.set("saved_semantic",OrdinaryCycleTransitions.semanticToJson(value.savedSemantic()));row.set("source",ProposalLifecycleCodec.source(value.source()));
        row.set("canonical_parent",value.canonicalParent().toJson());row.set("lifecycle_proof",value.lifecycleProof().toJson());
        if(value.format()==Format.CURRENT){row.put("initialization_kind",value.kind().name());row.set("saved_session",OrdinaryCycleTransitions.sessionToJson(value.savedSession()));
            row.set("current_driver",value.currentDriver().toJson());row.set("current_semantic",OrdinaryCycleTransitions.semanticToJson(value.currentSemantic()));
            row.put("initialization_head_sequence",Long.toString(value.initializationHeadSequence()));row.put("initialization_head_digest",value.initializationHeadDigest());}
        return StrictJson.canonical(row,SwayFormalCodec.MAX);
    }
    public static Basis decode(byte[] raw) {
        var row=StrictJson.parse(raw,SwayFormalCodec.MAX);String schema=SwayNativeWire.string(row,"schema");boolean legacy=LEGACY_SCHEMA.equals(schema);
        require(legacy||SCHEMA.equals(schema),"unsupported Sway domain origin schema");
        var fields=new java.util.HashSet<>(Set.of("schema","current_native_sway_observation","old_request_replayed","predecessor","before_session","after_session","predecessor_driver","first_saved_driver","original_baseline_material","archived_baseline_material","baseline","saved_semantic","source","canonical_parent","lifecycle_proof"));
        if(!legacy)fields.addAll(Set.of("initialization_kind","saved_session","current_driver","current_semantic","initialization_head_sequence","initialization_head_digest"));StrictJson.object(row,fields);
        SwayNativeWire.equals(row,"current_native_sway_observation","unqueried");require(!SwayNativeWire.bool(row,"old_request_replayed"),"new Sway origin cannot replay old requests");
        var predecessor=DomainBodies.BodyRef.fromJson(row.get("predecessor"));var before=OrdinaryCycleTransitions.sessionFromJson(row.get("before_session"));var after=OrdinaryCycleTransitions.sessionFromJson(row.get("after_session"));
        var oldDriver=ExactRef.fromJson(row.get("predecessor_driver"));var savedDriver=ExactRef.fromJson(row.get("first_saved_driver"));var original=ExactRef.fromJson(row.get("original_baseline_material"));var archived=ExactRef.fromJson(row.get("archived_baseline_material"));
        var baseline=EpisodeWindow.CommittedBaseline.fromJson(row.get("baseline"));var saved=OrdinaryCycleTransitions.semanticFromJson(row.get("saved_semantic"));var source=G2Wire.source(row.get("source"));var parent=ExactRef.fromJson(row.get("canonical_parent"));var lifecycle=ExactRef.fromJson(row.get("lifecycle_proof"));
        if(legacy)return new Basis(predecessor,before,after,oldDriver,savedDriver,original,archived,baseline,saved,source,parent,lifecycle);
        String sequence=StrictJson.text(row.get("initialization_head_sequence"));long parsed=Long.parseLong(sequence);require(sequence.equals(Long.toString(parsed)),"canonical initialization sequence required");
        return new Basis(Format.CURRENT,Kind.valueOf(StrictJson.text(row.get("initialization_kind"))),predecessor,before,OrdinaryCycleTransitions.sessionFromJson(row.get("saved_session")),after,oldDriver,savedDriver,
                ExactRef.fromJson(row.get("current_driver")),original,archived,baseline,saved,OrdinaryCycleTransitions.semanticFromJson(row.get("current_semantic")),source,parent,lifecycle,parsed,StrictJson.text(row.get("initialization_head_digest")));
    }
    public static SwayFormalState.Ledger replay(ContinuityState head,SwayFormalState.Ledger before,Basis basis,ExactRef origin,
            ActionPorts.OutcomeArchive originals,NativeEffectEvidence.FrameLoader frames)throws IOException {
        require(Arrays.equals(encode(basis),originals.loadMaterial(origin).bytes()),"next origin differs from its exact immutable producer input");
        require(Arrays.equals(SwayFormalCodec.encode(before),originals.loadMaterial(basis.predecessor().payload()).bytes()),"next origin changed its entire predecessor ledger including UNKNOWN");
        var active=EpisodeWindow.requireActive(head);require(head.sequence()>=basis.initializationHeadSequence()&&active.baseline().orElseThrow().equals(basis.baseline().baseline()),"next Sway source is not this current actual first BASELINE");
        var old=DriverStateSnapshot.decodeComplete(originals.loadMaterial(basis.predecessorDriver()).bytes());var saved=DriverStateSnapshot.decodeComplete(originals.loadMaterial(basis.firstSavedDriver()).bytes());var current=DriverStateSnapshot.decodeComplete(originals.loadMaterial(basis.currentDriver()).bytes());
        require(Arrays.equals(saved.encode(),originals.loadMaterial(basis.savedSemantic().originalDriver()).bytes()),"next origin must retain the entire real saved Driver rather than a copied session tuple");
        require(Arrays.equals(current.encode(),originals.loadMaterial(basis.currentSemantic().originalDriver()).bytes()),"current restored Driver must be its exact actual current SEM original");
        var window=basis.baseline().baseline();var prior=window.begin().begin().before();var next=window.savedIdentity();
        require(before.machineId().equals(head.machineId())&&before.machineId().equals(basis.beforeSession().machineId())&&before.episodeRunId().equals(old.session().episodeRunId())
                &&old.session().episodeRunId().equals(prior.episodeRunId())&&old.session().actorId().longValueExact()==prior.actorId()
                &&old.session().bridgePid()==basis.beforeSession().game().pid(),"old Sway episode/actor differs from actual predecessor Driver and M7 opening");
        requireOwner(basis.beforeSession(),prior);requireOwner(basis.savedSession(),next);
        require(!old.session().episodeRunId().equals(saved.session().episodeRunId())&&saved.session().episodeRunId().equals(next.episodeRunId())
                &&saved.session().actorId().longValueExact()==next.actorId()&&saved.session().bridgePid()==basis.savedSession().game().pid(),"saved Sway scope differs from the actual first saved Driver");
        require(current.session().episodeRunId().equals(next.episodeRunId())&&current.session().actorId().longValueExact()==next.actorId()
                &&current.session().bridgePid()==basis.afterSession().game().pid(),"current Sway scope differs from its actual restored/current Driver");
        before.pending().ifPresent(value->require(value.original().binding().actor()==old.session().actorId().longValueExact(),"pending original changed old actor"));
        before.resolved().ifPresent(value->require(value.identity().actorCharacterId()==old.session().actorId().longValueExact(),"resolved original changed old actor"));
        for(var previous:before.previous())require(previous.identity().actorCharacterId()==old.session().actorId().longValueExact(),"historical original changed old actor");
        SavedFirstCheckpointMaterialStore.verifyArchivedBaselineMetadata(originals.loadMaterial(basis.archivedBaselineMaterial()).bytes(),basis.baseline(),basis.savedSemantic());
        var parent=originals.loadReceipt(basis.canonicalParent());var canonical=ContinuityActionJournal.lookup(head,parent.command().actionId(),originals).orElseThrow(()->new IOException("actual canonical NEXT parent is absent"));
        require(originals.receiptReferenceOf(canonical).equals(basis.canonicalParent())&&canonical.settled()&&canonical.command().actionId().equals(window.begin().begin().parentActionId())&&canonical.command().operation().value().equals("start-next-episode"),"next scope cannot use a pending, UNKNOWN or foreign parent");
        var recorded=LifecycleProofCodec.decodeRecorded(originals.loadMaterial(basis.lifecycleProof()).bytes());recorded.validateParent(canonical.command());
        var settlement=NativeRecordedEvidenceVerifier.settlement(canonical.state());require(recorded.kind()==LifecycleTransitionProof.Kind.NEXT_EPISODE&&settlement instanceof ActionState.LifecycleApplied,"actual private lifecycle NEXT settlement required");
        require(Arrays.equals(((ActionState.LifecycleApplied)settlement).proof().encode(),recorded.encode()),"next origin is not the exact lifecycle proof retained by its canonical parent");
        for(int phase=0;phase<2;phase++) {
            var evidence=phase==0?basis.savedSemantic():basis.currentSemantic();var owner=phase==0?basis.savedSession():basis.afterSession();
            var semantic=DriverJson.object(originals.loadMaterial(evidence.semantic()).bytes(),DriverJson.MAX_NATIVE_BYTES);var facts=semantic.get("java_driver_facts_evidence");require(facts!=null&&facts!=OpportunityJson.Nil.INSTANCE,"actual saved/current Driver facts manifest required");
            var frame=frames.load(new NativeEffectEvidence.FrameBasis(evidence.originalNativePacket(),ExactRef.fromJson(OpportunityJson.toNode(facts))),originals);
            require(frame.identity().equals(evidence.frame())&&frame.sessionId().equals(owner.sessionId())&&frame.observedAt().equals(evidence.observedAt())
                    &&frame.identity().game().equals(owner.game())&&frame.identity().frame().episodeRunId().equals(next.episodeRunId())
                    &&frame.identity().frame().identity().player().longValueExact()==next.actorId()&&frame.identity().frame().identity().dateRaw().longValueExact()==next.dateRaw(),"Sway original saved/current native Driver frame crossed physical owner, episode, actor or date");
            if(phase==1)require(frame.source().equals(basis.source()),"current restored Sway source differs from the actual admitted current source");
        }
        return new SwayFormalState.Ledger(head.machineId(),next.episodeRunId(),Optional.empty(),Optional.empty(),List.of(),Optional.empty(),origin);
    }
    /** Typed shape guard only; replay still rebuilds both original native/Driver frames. */
    private static void requireSemanticOwner(SemanticEvidence evidence,SessionIdentity owner,EpisodeWindow.Identity saved) {
        var frame=evidence.frame();require(frame.machineId().equals(owner.machineId())&&frame.game().equals(owner.game())
                &&frame.frame().episodeRunId().equals(saved.episodeRunId())&&frame.frame().identity().player().longValueExact()==saved.actorId()
                &&frame.frame().identity().dateRaw().longValueExact()==saved.dateRaw(),"saved/current semantic identity crossed its declared physical owner or original saved episode/actor/date");
    }
    private static void requireOwner(SessionIdentity owner,EpisodeWindow.Identity identity){require(owner.machineId().equals(identity.machineId())&&owner.game().equals(identity.game())&&owner.sessionId().equals(identity.sessionId()),"next origin crosses actual old/new session identity");}
}
