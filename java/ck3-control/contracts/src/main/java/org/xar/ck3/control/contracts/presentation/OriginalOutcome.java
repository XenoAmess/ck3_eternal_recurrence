package org.xar.ck3.control.contracts.presentation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Original physical posting facts only. POSTED is neither native ACK nor a camera postcondition. */
public sealed interface OriginalOutcome permits OriginalOutcome.NotPosted,OriginalOutcome.Posted,OriginalOutcome.Unknown {
    String SCHEMA="xar.java-presentation-original-outcome/v1";
    PresentationRequest request();
    default String requestId(){return request().requestId();}
    default TransportKind transportKind(){return TransportKind.PRESENTATION_MMAP;}
    record NotPosted(PresentationRequest request,Instant observedAt,String reason,List<ExactRef> evidence) implements OriginalOutcome {
        public NotPosted {Objects.requireNonNull(request);Objects.requireNonNull(observedAt);StrictJson.text(reason);evidence=PresentationJson.refs(evidence);}
    }
    record Posted(PresentationRequest request,Instant postedAt,ExactRef originalRequest,
            Optional<ExactRef> originalTrackingRequest,ExactRef originalPostEvidence) implements OriginalOutcome {
        public Posted {Objects.requireNonNull(request);Objects.requireNonNull(postedAt);
            PresentationJson.sized(originalRequest,PresentationRequest.REQUEST_BYTES);
            originalTrackingRequest=Objects.requireNonNull(originalTrackingRequest);
            StrictJson.require(originalTrackingRequest.isPresent()==request.tracking().isPresent(),"same actual tracking original required");
            originalTrackingRequest.ifPresent(ref->PresentationJson.sized(ref,PresentationRequest.TRACKING_REQUEST_BYTES));
            StrictJson.require(originalPostEvidence!=null&&originalPostEvidence.bytes()>0&&originalPostEvidence.bytes()<=16384,"bounded original post metadata required");
            StrictJson.require(!postedAt.isBefore(request.preparedAt()),"post cannot precede its actual preparation");
        }
        public void verifyOriginal(byte[] requestBytes,Optional<byte[]> trackingBytes,byte[] postMetadata,byte[] beforeHeader,byte[] afterHeader){
            PresentationJson.original(originalRequest,requestBytes);
            StrictJson.require(java.util.Arrays.equals(requestBytes,request.nativeBytes()),"original posted payload differs from prepared request");
            StrictJson.require(trackingBytes.isPresent()==originalTrackingRequest.isPresent(),"original tracking payload presence differs");
            if(trackingBytes.isPresent()){
                PresentationJson.original(originalTrackingRequest.orElseThrow(),trackingBytes.orElseThrow());
                StrictJson.require(java.util.Arrays.equals(trackingBytes.orElseThrow(),request.trackingBytes().orElseThrow()),"original posted tracking differs");
            }
            PresentationJson.original(originalPostEvidence,postMetadata);PostEvidence evidence=PostEvidence.decode(postMetadata);
            evidence.requireMatches(this);evidence.verifyOriginal(beforeHeader,afterHeader);
        }
    }
    enum Phase { BEFORE_ODD,ODD_STORED,REQUEST_COPIED,TRACKING_COPIED,EVEN_PUBLICATION_UNCERTAIN,POSTED_OUTCOME_UNPERSISTED }
    /** No branch releases a once claim or permits a second post. */
    record Unknown(PresentationRequest request,Instant observedAt,Phase phase,String reason,List<ExactRef> evidence) implements OriginalOutcome {
        public Unknown {Objects.requireNonNull(request);Objects.requireNonNull(observedAt);Objects.requireNonNull(phase);StrictJson.text(reason);evidence=PresentationJson.refs(evidence);}
    }
    /** Typed actual IO producer metadata, not a publicly mintable permission or independent proof of execution. */
    record PostEvidence(PresentationRequest.Owner owner,String requestId,Instant postedAt,long previousRequestSequence,
            long postedRequestSequence,ExactRef beforeHeader,ExactRef afterHeader,ExactRef originalRequest,Optional<ExactRef> originalTrackingRequest) {
        public static final String SCHEMA="xar.java-presentation-post-evidence/v1";
        public PostEvidence {
            Objects.requireNonNull(owner);StrictJson.text(requestId);Objects.requireNonNull(postedAt);
            PresentationJson.u32(previousRequestSequence);PresentationJson.u32(postedRequestSequence);
            StrictJson.require((previousRequestSequence&1)==0&&postedRequestSequence==PresentationRequest.nextSequence(previousRequestSequence),"actual publication counters required");
            PresentationJson.sized(beforeHeader,24);PresentationJson.sized(afterHeader,24);PresentationJson.sized(originalRequest,168);
            originalTrackingRequest=Objects.requireNonNull(originalTrackingRequest);originalTrackingRequest.ifPresent(r->PresentationJson.sized(r,4264));
        }
        public ObjectNode toJson(){
            ObjectNode n=PresentationJson.envelope(SCHEMA);n.set("owner",owner.toJson());n.put("request_id",requestId);n.put("posted_at",postedAt.toString());
            n.put("previous_request_sequence",previousRequestSequence);n.put("posted_request_sequence",postedRequestSequence);
            n.set("before_header",beforeHeader.toJson());n.set("after_header",afterHeader.toJson());n.set("original_request",originalRequest.toJson());
            if(originalTrackingRequest.isPresent())n.set("original_tracking_request",originalTrackingRequest.orElseThrow().toJson());else n.putNull("original_tracking_request");return n;
        }
        public byte[] encode(){return StrictJson.canonical(toJson(),16384);}
        public static PostEvidence decode(byte[] raw){
            ObjectNode n=PresentationJson.envelope(StrictJson.parse(raw,16384),Set.of("schema","transport","owner","request_id","posted_at","previous_request_sequence","posted_request_sequence","before_header","after_header","original_request","original_tracking_request"),SCHEMA);
            JsonNode t=n.get("original_tracking_request");
            return new PostEvidence(PresentationRequest.Owner.fromJson(n.get("owner")),StrictJson.text(n.get("request_id")),PresentationJson.time(n.get("posted_at")),
                    PresentationJson.u32(n.get("previous_request_sequence")),PresentationJson.u32(n.get("posted_request_sequence")),PresentationJson.ref(n.get("before_header"),24),
                    PresentationJson.ref(n.get("after_header"),24),PresentationJson.ref(n.get("original_request"),168),t.isNull()?Optional.empty():Optional.of(PresentationJson.ref(t,4264)));
        }
        public void verifyOriginal(byte[] before,byte[] after){
            PresentationJson.original(beforeHeader,before);PresentationJson.original(afterHeader,after);
            header(before,previousRequestSequence);header(after,postedRequestSequence);
        }
        private void header(byte[] raw,long requestSequence){
            java.nio.ByteBuffer b=java.nio.ByteBuffer.wrap(raw).order(java.nio.ByteOrder.LITTLE_ENDIAN);
            StrictJson.require(b.getInt()==PresentationRequest.MAGIC&&b.getInt()==1&&Integer.toUnsignedLong(b.getInt())==owner.processId()
                    &&b.getInt()==0&&Integer.toUnsignedLong(b.getInt())==requestSequence,"actual original post header differs");
        }
        public void requireMatches(Posted posted){
            StrictJson.require(owner.equals(posted.request().owner())&&requestId.equals(posted.requestId())&&postedAt.equals(posted.postedAt())
                    &&previousRequestSequence==posted.request().previousRequestSequence()&&postedRequestSequence==posted.request().requestSequence()
                    &&originalRequest.equals(posted.originalRequest())&&originalTrackingRequest.equals(posted.originalTrackingRequest()),"post evidence differs from original request/publication");
        }
    }
    default ObjectNode toJson(){
        ObjectNode n=PresentationJson.envelope(SCHEMA);n.set("request",request().toJson());
        if(this instanceof NotPosted v){n.put("kind","NOT_POSTED");n.put("observed_at",v.observedAt().toString());n.put("reason",v.reason());PresentationJson.refs(n,"evidence",v.evidence());}
        else if(this instanceof Posted v){n.put("kind","POSTED");n.put("posted_at",v.postedAt().toString());n.set("original_request",v.originalRequest().toJson());
            if(v.originalTrackingRequest().isPresent())n.set("original_tracking_request",v.originalTrackingRequest().orElseThrow().toJson());else n.putNull("original_tracking_request");
            n.set("original_post_evidence",v.originalPostEvidence().toJson());}
        else if(this instanceof Unknown v){n.put("kind","UNKNOWN");n.put("observed_at",v.observedAt().toString());n.put("phase",v.phase().name());n.put("reason",v.reason());PresentationJson.refs(n,"evidence",v.evidence());}
        return n;
    }
    default byte[] encode(){return StrictJson.canonical(toJson());}
    static OriginalOutcome decode(byte[] raw){
        JsonNode r=StrictJson.parse(raw);StrictJson.require(r.isObject(),"outcome object required");String kind=StrictJson.text(r.get("kind"));
        Set<String> fields=switch(kind){
            case "NOT_POSTED" -> Set.of("schema","transport","request","kind","observed_at","reason","evidence");
            case "POSTED" -> Set.of("schema","transport","request","kind","posted_at","original_request","original_tracking_request","original_post_evidence");
            case "UNKNOWN" -> Set.of("schema","transport","request","kind","observed_at","phase","reason","evidence");
            default -> throw new IllegalArgumentException("unknown presentation posting branch");
        };
        ObjectNode n=PresentationJson.envelope(r,fields,SCHEMA);PresentationRequest request=PresentationRequest.fromJson(n.get("request"));
        return switch(kind){
            case "NOT_POSTED" -> new NotPosted(request,PresentationJson.time(n.get("observed_at")),StrictJson.text(n.get("reason")),PresentationJson.refs(n.get("evidence")));
            case "POSTED" -> new Posted(request,PresentationJson.time(n.get("posted_at")),PresentationJson.ref(n.get("original_request"),168),
                    n.get("original_tracking_request").isNull()?Optional.empty():Optional.of(PresentationJson.ref(n.get("original_tracking_request"),4264)),ExactRef.fromJson(n.get("original_post_evidence")));
            case "UNKNOWN" -> new Unknown(request,PresentationJson.time(n.get("observed_at")),Phase.valueOf(StrictJson.text(n.get("phase"))),StrictJson.text(n.get("reason")),PresentationJson.refs(n.get("evidence")));
            default -> throw new IllegalStateException();
        };
    }
}
