package org.xar.ck3.control.application.lifecycle;

import java.util.List;
import java.util.Set;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual warm metadata input archive. Decoding is DATA, never retained M3 or episode authority. */
public record LifecyclePendingOriginals(long beforeSequence,String beforeDigest,WriterContracts.Pin beforeAuxiliaryPin,WriterContracts.Pin beforeKnownPin,
        List<WriterContracts.Pin> sources,List<WriterContracts.Pin> originals) {
    public static final String SCHEMA="xar.java-pending-lifecycle-originals/v1";
    public static final int MAXIMUM_BYTES=1024*1024;
    public LifecyclePendingOriginals {
        StrictJson.safe(beforeSequence,0);WriterContracts.requireDigest(beforeDigest);
        java.util.Objects.requireNonNull(beforeAuxiliaryPin);java.util.Objects.requireNonNull(beforeKnownPin);sources=List.copyOf(sources);originals=List.copyOf(originals);
        StrictJson.require(!sources.isEmpty()&&!originals.isEmpty()&&sources.size()<=4096&&originals.size()<=63
                &&originals.contains(beforeAuxiliaryPin)&&originals.contains(beforeKnownPin),
                "finite actual configured sources and original metadata pins required");
    }
    public byte[] encode() {
        var row=LifecycleJson.row();row.put("schema",SCHEMA);row.put("before_sequence",beforeSequence);row.put("before_digest",beforeDigest);
        row.set("before_auxiliary",LifecycleProofCodec.encodePin(beforeAuxiliaryPin));
        row.set("before_known",LifecycleProofCodec.encodePin(beforeKnownPin));
        var sourceRows=row.putArray("sources");sources.forEach(pin->sourceRows.add(LifecycleProofCodec.encodePin(pin)));
        var originalRows=row.putArray("originals");originals.forEach(pin->originalRows.add(LifecycleProofCodec.encodePin(pin)));
        byte[] result=LifecycleJson.bytes(row);StrictJson.require(result.length<=MAXIMUM_BYTES,"bounded full lifecycle originals required");return result;
    }
    public static LifecyclePendingOriginals decode(byte[] raw) {
        var row=LifecycleJson.parse(raw,MAXIMUM_BYTES);
        LifecycleJson.exact(row,Set.of("schema","before_sequence","before_digest","before_auxiliary","before_known","sources","originals"));
        StrictJson.require(SCHEMA.equals(LifecycleJson.text(row.get("schema")))&&row.get("sources").isArray()&&row.get("originals").isArray(),
                "explicit current pending lifecycle originals schema and pin arrays required");
        var sources=new java.util.ArrayList<WriterContracts.Pin>();row.get("sources").forEach(pin->sources.add(LifecycleProofCodec.decodePin(pin)));
        var originals=new java.util.ArrayList<WriterContracts.Pin>();row.get("originals").forEach(pin->originals.add(LifecycleProofCodec.decodePin(pin)));
        return new LifecyclePendingOriginals(StrictJson.integer(row.get("before_sequence"),0,StrictJson.MAX_SAFE_INTEGER),
                LifecycleJson.text(row.get("before_digest")),LifecycleProofCodec.decodePin(row.get("before_auxiliary")),LifecycleProofCodec.decodePin(row.get("before_known")),sources,originals);
    }
}
