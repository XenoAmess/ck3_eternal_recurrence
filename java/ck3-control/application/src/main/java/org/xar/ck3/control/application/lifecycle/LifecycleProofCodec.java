package org.xar.ck3.control.application.lifecycle;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Recorded data round trip only. Actual original writer and native provenance are independently revalidated. */
public final class LifecycleProofCodec {
    public static final int MAX_PROOF_BYTES=64*1024*1024;
    public static final int MAX_RESULT_BYTES=MAX_PROOF_BYTES-1024*1024;
    private LifecycleProofCodec(){ }
    public static byte[] encode(LifecycleTransitionProof proof){
        ObjectNode row=LifecycleJson.row();row.put("schema","xar.java-lifecycle-transition-proof/v1");row.put("kind",proof.kind().name());
        List<WriterContracts.Pin> documents;
        if(proof instanceof LifecycleTransitionProof.Base value){
            row.put("parent_action_id",value.parent.actionId());row.put("body_sha256",ActionCodec.bodySha256(value.parent));row.put("operation",value.parent.operation().value());
            row.put("committed_event_identity",value.publication.eventIdentity());
            documents=value.publication.proofDocuments();
        }else{
            var value=(LifecycleTransitionProof.Recorded)proof;row.put("parent_action_id",value.parentId);row.put("body_sha256",value.bodySha);row.put("operation",value.operation);
            row.put("committed_event_identity",value.eventIdentity);documents=value.documents;
        }
        var pins=row.putArray("committed_documents");for(var pin:documents)pins.add(encodePin(pin));
        var evidence=row.putArray("original_evidence");for(var ref:proof.originalEvidence())evidence.add(ref(ref));
        row.set("result",LifecycleJson.parse(proof.encodedResult(),MAX_RESULT_BYTES));byte[] raw=LifecycleJson.bytes(row);
        StrictJson.require(raw.length<=MAX_PROOF_BYTES,"bounded complete lifecycle proof required");return raw;
    }
    public static LifecycleTransitionProof decodeRecorded(byte[] raw){
        ObjectNode row=LifecycleJson.parse(raw,MAX_PROOF_BYTES);LifecycleJson.exact(row,Set.of("schema","kind","parent_action_id","body_sha256","operation","committed_event_identity","committed_documents","original_evidence","result"));
        StrictJson.require(LifecycleJson.text(row.get("schema")).equals("xar.java-lifecycle-transition-proof/v1"),"lifecycle proof schema");
        var kind=LifecycleTransitionProof.Kind.valueOf(LifecycleJson.text(row.get("kind")));String body=LifecycleJson.text(row.get("body_sha256")),event=LifecycleJson.text(row.get("committed_event_identity"));
        WriterContracts.requireDigest(body);WriterContracts.requireDigest(event);
        StrictJson.require(row.get("committed_documents").isArray()&&row.get("original_evidence").isArray(),"proof documents/evidence arrays required");
        List<WriterContracts.Pin> documents=new ArrayList<>();for(JsonNode item:row.get("committed_documents"))documents.add(decodePin(item));
        List<ExactRef> evidence=new ArrayList<>();for(JsonNode item:row.get("original_evidence"))evidence.add(parseRef(item));
        StrictJson.require(!documents.isEmpty()&&!evidence.isEmpty()&&documents.size()<=4096&&evidence.size()<=64,"actual finite commit/evidence pins required");
        return new LifecycleTransitionProof.Recorded(kind,LifecycleJson.text(row.get("parent_action_id")),body,LifecycleJson.text(row.get("operation")),event,documents,evidence,LifecycleJson.bytes(LifecycleJson.object(row.get("result"))));
    }
    /** Shared original pin codec; decoding grants no writer or lifecycle qualification. */
    public static ObjectNode encodePin(WriterContracts.Pin pin) {
        ObjectNode item=LifecycleJson.row();item.set("reference",ref(pin.reference()));
        var identity=pin.identity();ObjectNode nativeId=item.putObject("native_identity");
        nativeId.put("volume_serial",identity.volumeSerialDecimal());nativeId.put("file_id",identity.fileIdDecimal());
        nativeId.put("creation_filetime",identity.creationFiletimeDecimal());nativeId.put("modified_instant",identity.modifiedInstant());
        nativeId.put("bytes",identity.bytes());return item;
    }
    public static WriterContracts.Pin decodePin(JsonNode value) {
        ObjectNode pin=LifecycleJson.object(value);LifecycleJson.exact(pin,Set.of("reference","native_identity"));
        ObjectNode identity=LifecycleJson.object(pin.get("native_identity"));
        LifecycleJson.exact(identity,Set.of("volume_serial","file_id","creation_filetime","modified_instant","bytes"));
        return new WriterContracts.Pin(parseRef(pin.get("reference")),new WriterContracts.FileIdentity(
                LifecycleJson.text(identity.get("volume_serial")),LifecycleJson.text(identity.get("file_id")),
                LifecycleJson.text(identity.get("creation_filetime")),LifecycleJson.text(identity.get("modified_instant")),
                StrictJson.integer(identity.get("bytes"),0,StrictJson.MAX_SAFE_INTEGER)));
    }
    private static ObjectNode ref(ExactRef ref){ObjectNode row=LifecycleJson.row();row.put("path",ref.path());row.put("bytes",ref.bytes());row.put("sha256",ref.sha256());return row;}
    private static ExactRef parseRef(JsonNode value){ObjectNode row=LifecycleJson.object(value);LifecycleJson.exact(row,Set.of("path","bytes","sha256"));return new ExactRef(LifecycleJson.text(row.get("path")),StrictJson.integer(row.get("bytes"),1,StrictJson.MAX_SAFE_INTEGER),LifecycleJson.text(row.get("sha256")));}
}
