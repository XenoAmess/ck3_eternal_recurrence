package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Arrays;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import com.fasterxml.jackson.databind.JsonNode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.OriginalEvidencePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.ArchiveOriginalEvidencePort;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.NativeArchiveDataCodec;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Private administrative DATA view. Physical reads retain the actual Store's
 * identity/hash/lease checks. Decoding does not replay a child effect or grant
 * Native, Frame, writer, installed-source or retirement authority. */
final class RootReservedRetirementArchive implements AutoCloseable {
    private final ContinuityStorePort.Session same;
    private final OriginalEvidencePort originals;
    private final Runnable requireActive;
    private final Thread thread=Thread.currentThread();
    private final String parentId;
    private final String parentBodySha;
    private final ActionPorts.OutcomeArchive actual;
    private final NativeArchiveDataCodec codec;
    private final Map<Object,ExactRef> references=new IdentityHashMap<>();
    private final ActionPorts.OutcomeArchive view=new View();
    private boolean closed;

    static RootReservedRetirementArchive create(ActionPorts.OutcomeArchive actual,ContinuityStorePort.Session same,
            OriginalEvidencePort originals,Runnable requireActive,String parentId,String parentBodySha) {
        return new RootReservedRetirementArchive(actual,same,originals,requireActive,parentId,parentBodySha);
    }
    private RootReservedRetirementArchive(ActionPorts.OutcomeArchive actual,ContinuityStorePort.Session same,
            OriginalEvidencePort originals,Runnable requireActive,String parentId,String parentBodySha) {
        this.same=Objects.requireNonNull(same);this.originals=Objects.requireNonNull(originals);
        this.requireActive=Objects.requireNonNull(requireActive);this.parentId=StrictJson.text(parentId);
        StrictJson.require(parentBodySha!=null&&parentBodySha.matches("[0-9a-f]{64}"),"exact retained parent body SHA required");
        this.parentBodySha=parentBodySha;check();
        this.actual=Objects.requireNonNull(actual).withSession(same);
        StrictJson.require(this.actual instanceof NativeOutcomeArchive nativeArchive
                &&originals instanceof ArchiveOriginalEvidencePort originalPort
                &&originalPort.writer()==nativeArchive.writer(),"reserved retirement DATA needs the actual same-writer Native original port");
        this.codec=new NativeArchiveDataCodec(this::readRaw);check();
    }
    ActionPorts.OutcomeArchive archive(){check();return view;}
    private void check(){
        if(closed||Thread.currentThread()!=thread)throw new IllegalStateException("reserved retirement DATA archive escaped its owning scope/thread");
        requireActive.run();
    }
    @Override public void close(){
        if(Thread.currentThread()!=thread)throw new IllegalStateException("reserved retirement DATA close changed owning thread");
        closed=true;references.clear();
    }
    @FunctionalInterface private interface IoWork<T>{T run()throws IOException;}
    private <T>T checked(IoWork<T> work){
        check();try{T result=work.run();check();return result;}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private byte[] readRaw(ExactRef reference,int maximum)throws IOException {
        check();Objects.requireNonNull(reference);
        if(maximum<1||maximum>WriterContracts.MAX_PIN_BYTES||reference.bytes()<0||reference.bytes()>maximum)
            throw new IOException("finite reserved retirement original DATA bound required");
        byte[] bytes=Objects.requireNonNull(originals.read(same,reference,maximum));check();
        if(bytes.length!=reference.bytes()||!ActionCodec.sha256(bytes).equals(reference.sha256()))
            throw new IOException("reserved retirement original DATA bytes/SHA changed");
        return bytes;
    }
    private <T>T remember(T value,ExactRef reference){
        check();Objects.requireNonNull(value);Objects.requireNonNull(reference);
        StrictJson.require(references.size()<1_000_000||references.containsKey(value),"finite reserved retirement DATA object locator budget exceeded");
        var old=references.putIfAbsent(value,reference);
        StrictJson.require(old==null||old.equals(reference),"one reserved retirement DATA object has conflicting original references");return value;
    }
    private ExactRef known(Object original){
        check();Objects.requireNonNull(original);ExactRef ref=references.get(original);
        if(ref!=null)return ref;
        for(var entry:references.entrySet())if(entry.getKey().getClass()==original.getClass()&&entry.getKey().equals(original))return entry.getValue();
        throw new IllegalStateException("reserved retirement inverse lookup needs an original decoded or preserved in this actual scope");
    }
    private JsonNode metadata(ExactRef reference)throws IOException {
        return StrictJson.parse(readRaw(reference,StrictJson.EXPLICIT_MAX_BYTES),StrictJson.EXPLICIT_MAX_BYTES);
    }
    private PlanningReadReceipt readData(ExactRef reference)throws IOException {
        var result=codec.readData(reference).receipt();var row=metadata(reference);
        remember(result.original(),ExactRef.fromJson(row.get("original_ref")));
        if(result.adoption().isPresent()) {
            var adoption=result.adoption().orElseThrow();var fields=row.get("adoption");
            remember(adoption.originalUnknown(),ExactRef.fromJson(fields.get("original_unknown_ref")));
            remember(adoption.preparedRequest(),ExactRef.fromJson(fields.get("prepared_request_ref")));
        }
        return remember(result,reference);
    }
    private ExactRef encodedReference(byte[] encoded){
        var reference=actual.materialReference(ActionCodec.sha256(encoded),encoded.length);
        byte[] bytes=checked(()->readRaw(reference,Math.max(1,encoded.length)));
        StrictJson.require(Arrays.equals(encoded,bytes),"reserved retirement canonical original encoding differs");return reference;
    }
    private void requireProposed(ActionReceipt receipt)throws IOException {
        check();Objects.requireNonNull(receipt);
        StrictJson.require(receipt.command().actionId().equals(parentId)&&receipt.bodySha256().equals(parentBodySha)
                &&receipt.state() instanceof ActionState.CompositeOperatorQuarantined
                &&receipt.outcome()==ActionReceipt.Outcome.OPERATOR_ABANDONED_UNKNOWN_EFFECT
                &&!receipt.visibleGameplay()&&!receipt.eligibleAdvance()&&receipt.ack().isEmpty()
                &&receipt.sequence()==Math.addExact(same.head().state().sequence(),1),
                "reserved retirement archive write is only its exact new parent UNKNOWN_EFFECT decision");
    }
    private static UnsupportedOperationException denied(){return new UnsupportedOperationException("reserved retirement DATA archive has no Native/read/action write route");}

    private final class View implements ActionPorts.OutcomeArchive {
        @Override public ActionPorts.OutcomeArchive withSession(ContinuityStorePort.Session borrowed){
            check();StrictJson.require(borrowed==same,"reserved retirement DATA archive changed actual borrowed session");return this;
        }
        @Override public <T>T inSession(ContinuityStorePort.Session borrowed,Function<ActionPorts.OutcomeArchive,T> work){
            withSession(borrowed);T result=Objects.requireNonNull(work).apply(this);check();return result;
        }
        @Override public ActionCommand decodeCanonicalCommand(byte[] canonical){return checked(()->ActionCodec.decodeCommand(canonical));}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef original){
            return checked(()->remember(codec.decodeDispatchData(original),original));
        }
        @Override public NativeRequest loadRequest(ExactRef original){
            return checked(()->remember(codec.decodePreparedRequestData(original),original));
        }
        @Override public PlanningReadReceipt loadRead(ExactRef original){return checked(()->readData(original));}
        @Override public ActionRecord loadRecord(ExactRef original){
            return checked(()->remember(ActionRecordCodec.decode(readRaw(original,StrictJson.EXPLICIT_MAX_BYTES),this),original));
        }
        @Override public ActionReceipt loadReceipt(ExactRef original){
            return checked(()->remember(ActionReceiptCodec.decodeReceipt(readRaw(original,ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES),this),original));
        }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original){
            return checked(()->{
                var ref=known(original);var decoded=codec.decodeDispatchData(ref);
                StrictJson.require(decoded.equals(original),"reserved retirement dispatch inverse original differs");return ref;
            });
        }
        @Override public ExactRef requestReferenceOf(NativeRequest original){
            return checked(()->{
                var ref=known(original);var decoded=codec.decodePreparedRequestData(ref);
                StrictJson.require(decoded.equals(original),"reserved retirement request inverse original differs");return ref;
            });
        }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt original){
            return checked(()->{
                var ref=known(original);var decoded=readData(ref);
                StrictJson.require(decoded.equals(original),"reserved retirement read inverse original differs");return ref;
            });
        }
        @Override public ExactRef recordReferenceOf(ActionRecord original){
            return checked(()->encodedReference(ActionRecordCodec.encode(Objects.requireNonNull(original),this)));
        }
        @Override public ExactRef receiptReferenceOf(ActionReceipt original){
            return checked(()->encodedReference(ActionReceiptCodec.encodeReceipt(Objects.requireNonNull(original),this)));
        }
        @Override public RawJson loadMaterial(ExactRef original){return checked(()->actual.loadMaterial(original));}
        @Override public RawJson loadFullMaterial(ExactRef original){return checked(()->actual.loadFullMaterial(original));}
        @Override public ExactRef materialReferenceOf(RawJson original){
            return checked(()->encodedReference(Objects.requireNonNull(original).bytes()));
        }
        @Override public ExactRef materialReference(String sha256,long bytes){
            return checked(()->{
                var ref=actual.materialReference(sha256,bytes);readRaw(ref,RawJson.MAXIMUM_BYTES);return ref;
            });
        }
        @Override public byte[] loadNativeFrame(ExactRef original){return checked(()->actual.loadNativeFrame(original));}
        @Override public byte[] readOriginalPacket(ExactRef original){return checked(()->actual.readOriginalPacket(original));}
        @Override public ExactRef preserveMaterial(RawJson original){
            return checked(()->{
                Objects.requireNonNull(original);byte[] bytes=original.bytes();
                StrictJson.require(bytes.length<=StrictJson.EXPLICIT_MAX_BYTES,"finite administrative request/proof/predecessor material required");
                var ref=actual.preserveMaterial(original);
                StrictJson.require(Arrays.equals(bytes,readRaw(ref,StrictJson.EXPLICIT_MAX_BYTES)),"reserved retirement preserved material differs");return ref;
            });
        }
        @Override public ExactRef preserveReceipt(ActionReceipt original){
            return checked(()->{
                requireProposed(original);var ref=actual.preserveReceipt(original);remember(original,ref);return ref;
            });
        }
        @Override public ExactRef preserveRecord(ActionRecord original){
            return checked(()->{
                Objects.requireNonNull(original);requireProposed(original.receipt());
                StrictJson.require(original.previous().equals(ContinuityActionJournal.recordHead(same.head().state())),
                        "reserved retirement parent record changed its actual predecessor ACTION head");
                var ref=actual.preserveRecord(original);remember(original,ref);return ref;
            });
        }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original){check();throw denied();}
        @Override public ExactRef preserveRequest(NativeRequest original){check();throw denied();}
        @Override public ExactRef preserveRead(PlanningReadReceipt original){check();throw denied();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original){check();throw denied();}
    }
}
