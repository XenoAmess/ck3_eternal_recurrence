package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.math.BigInteger;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.GiftColdReadService;
import org.xar.ck3.control.application.planning.finance.GiftProcessIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.wave2.finance.giftpending.*;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.*;

/** Per-current-Game cold source. A read is first canonically published; only its next fresh lookup can enter the reducer. */
public final class CanonicalGiftColdProvider {
    private final RootRuntimeContext context;private final GiftColdReadService reads;
    public CanonicalGiftColdProvider(RootRuntimeContext context,GiftColdReadService sameInstalled) {
        this.context=Objects.requireNonNull(context);reads=Objects.requireNonNull(sameInstalled);
    }
    /** A miss issues only the read. Root's mandatory tail publisher returns Published and forces a fresh plan. */
    public Read observe(Session same,PlanningRequest current,PendingAction pending)throws IOException {
        requireSession(same);return context.collector().currentPlanning(same,current,current.deadline(),(original,lease)->{
            require(!sameProcess(pending,context.game().generation()),"cold Gift requires a proven different process birth");
            PlanningReadRequest query=reads.request(original,pending);
            var cached=context.readHistoryPublisher().canonicalReadWitness(same,reads.contract(),query);
            if(cached.isEmpty()) {
                var observed=context.reads().read(same,reads.contract(),query);
                if(observed instanceof PlanningReadResult.Known<GiftColdReadService.Observation> known)
                    return new AwaitingCanonical(known.originalReceipt());
                var unavailable=(PlanningReadResult.Unavailable<GiftColdReadService.Observation>)observed;
                return new Unavailable(unavailable.reason());
            }
            return produce(same,original,pending,cached.orElseThrow().requireCurrent(same,reads.contract(),query));
        });
    }
    /** Repeat all real canonical/cache/SAVE qualifications under preview and commit; never issue another native read. */
    public GiftColdRecovery.Recovery verify(Session same,Ready actual,PendingAction pending)throws IOException {
        require(actual.issuer==this,"cold Gift material was minted by another current Game source");
        return context.collector().currentPlanning(same,actual.current,actual.current.deadline(),(original,lease)->{
            var cached=context.readHistoryPublisher().canonicalReadWitness(same,reads.contract(),reads.request(original,pending))
                    .orElseThrow(()->new IOException("cold Gift read is no longer present in the actual canonical history"));
            Ready replay=produce(same,original,pending,cached.requireCurrent(same,reads.contract(),reads.request(original,pending)));
            require(replay.readReference.equals(actual.readReference)&&replay.saved.reference().equals(actual.saved.reference())
                    &&replay.evidence.equals(actual.evidence)
                    &&replay.recovery.equals(actual.recovery),
                    "cold Gift original read or saved classification changed under the writer");
            return replay.recovery;
        });
    }
    public sealed interface Read permits AwaitingCanonical,Unavailable,Ready { }
    public record AwaitingCanonical(ExactRef originalReceipt) implements Read {
        public AwaitingCanonical { Objects.requireNonNull(originalReceipt); }
    }
    public record Unavailable(String reason) implements Read {
        public Unavailable { require(reason!=null&&!reason.isEmpty(),"actual cold Gift unavailability required"); }
    }
    public static final class Ready implements Read {
        private final CanonicalGiftColdProvider issuer;private final PlanningRequest current;
        private final ExactRef readReference;private final SavedAttachmentSourceStore.SavedMaterial saved;
        private final GiftColdRecovery.Recovery recovery;private final List<ExactRef> evidence;
        private Ready(CanonicalGiftColdProvider issuer,PlanningRequest current,ExactRef readReference,
                SavedAttachmentSourceStore.SavedMaterial saved,GiftColdRecovery.Recovery recovery,List<ExactRef> evidence) {
            this.issuer=issuer;this.current=current;this.readReference=readReference;this.saved=saved;this.recovery=recovery;this.evidence=List.copyOf(evidence);
        }
        public ExactRef originalRead() { return readReference; }
        public ExactRef originalSavedMaterial() { return saved.reference(); }
        public GiftColdRecovery.Recovery recovery() { return recovery; }
        public List<ExactRef> evidence() { return evidence; }
    }
    private Ready produce(Session same,PlanningRequest current,PendingAction pending,
            PlanningReadResult.Known<GiftColdReadService.Observation> canonical)throws IOException {
        requireSession(same);var head=same.head();var receipt=canonical.receipt();
        reads.contract().requireCanonicalReuse(receipt,canonical.value(),reads.request(current,pending),current.observations().snapshot());
        require(receipt.equals(canonical.value().receipt())
                &&receipt.request().source().equals(current.source())&&receipt.request().sessionId().equals(current.sessionId()),
                "canonical cold read crossed the current original full frame/source/session");
        var archive=context.archive().withSession(same);
        ExactRef read=archive.readReferenceOf(receipt);require(receipt.equals(archive.loadRead(read)),"actual canonical cold read original changed");
        NativeRecordedEvidenceVerifier.requireRead(receipt,archive);
        GiftColdReadService.Observation decoded=reads.contract().replay(receipt);
        require(decoded.originalResult().equals(canonical.value().originalResult()),"cold read decode differs from its original packet");
        org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.RestoreBinding restored;
        try { restored=context.requireRestoration(current.deadline()); }
        catch(InterruptedException interrupted) { Thread.currentThread().interrupt();throw new IOException("actual original restoration verification interrupted",interrupted); }
        var pair=restored.pair();var saved=context.savedSources().load(pair);
        same.requireHistoricalState(saved.originalHeadSequence(),saved.originalHeadDigest());
        require(saved.pair().equals(pair)&&restored.session().game().equals(context.game().generation())
                &&restored.session().sessionId().equals(current.sessionId())&&restored.source().equals(current.source())
                &&pair.frame().machineId().equals(current.before().machineId())
                &&pair.frame().frame().episodeRunId().equals(pending.episodeRunId())
                &&GiftPendingModel.rawCharacterIdFromPublic(pair.frame().frame().identity().player()).equals(pending.baseline().playerCharacterId())
                &&!sameProcess(pending,context.game().generation())
                &&!pair.frame().game().equals(context.game().generation()),
                "old saved material does not belong to the original pending Gift and this actual restored Game");
        ProcessIdentity process=process(context.game().generation());
        Obj recovery=obj("schema_version",new IntegerValue(BigInteger.ONE),"status",decoded.originalResult().get("status"),
                "private_build",decoded.originalResult().get("private_build"),"advertised",decoded.originalResult().get("advertised"),
                "new_process_confirmed",new Bool(true),"new_round_id",new Text("R"+context.game().generation().creationFiletime().value()),
                "new_bridge_pid",new IntegerValue(process.pid()),"new_bridge_creation_date",new Text(process.creationDate()),
                "episode_run_id",new Text(current.before().frame().episodeRunId()),"paused",new Bool(true),"map_ready",new Bool(true),
                "independent_faction_storage_lookup_complete",new Bool(decoded.material().sourceFactionRequeryComplete().is(true)),
                "independent_recipient_lookup_complete",new Bool(decoded.material().recipientIdentityResolved().is(true)
                    &&decoded.material().recipientOpinionQueryComplete().is(true)),
                "selected_from_current_targeting_vector",new Bool(false),
                "save_is_pre_action_checkpoint",new Bool(pair.save().reference().sha256().equals(pending.checkpointSha256BeforeSubmit())),
                "selected_save_sha256",new Text(pair.save().reference().sha256()),"post_observation",decoded.originalPost());
        GiftColdRecovery.Recovery material=GiftColdRecoveryCodec.decodeRecovery(encode(recovery));
        var evidence=new LinkedHashSet<ExactRef>();evidence.add(read);evidence.add(saved.reference());evidence.add(pair.save().reference());
        evidence.add(pair.driver().reference());evidence.add(pair.nativeAckRef());evidence.addAll(saved.proof().semantic().references());
        evidence.add(restored.originalHistoryBasis());evidence.addAll(restored.semantic().references());
        require(same.head().digest().equals(head.digest()),"cold Gift original verification changed the actual writer head");
        return new Ready(this,current,read,saved,material,List.copyOf(evidence));
    }
    private void requireSession(Session same)throws IOException {
        context.writer().requireSession(same);require(context.borrowedSession()==same,"cold Gift requires the original held writer Session");
        context.game().verify();
    }
    public static ProcessIdentity process(GameGeneration game) {
        return GiftProcessIdentity.actual(game);
    }
    /** Original spelling is retained; unsupported or microsecond-rounded birth cannot prove process replacement. */
    public static boolean sameProcess(PendingAction pending,GameGeneration actual) {
        return switch(GiftProcessIdentity.compare(pending.sourceProcess(),actual)) {
            case SAME -> true;
            case DIFFERENT -> false;
            case UNAVAILABLE -> throw new IllegalArgumentException("original Gift process birth precision cannot prove process replacement");
        };
    }
}
