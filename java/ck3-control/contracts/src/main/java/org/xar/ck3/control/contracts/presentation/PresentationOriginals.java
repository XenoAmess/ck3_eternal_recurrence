package org.xar.ck3.control.contracts.presentation;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual immutable binary custody only. An archive write grants no physical post, ACK or Game qualification. */
public interface PresentationOriginals {
    enum ArtifactRole {
        REQUEST(168),TRACKING_REQUEST(4264),HEADER(24),RESULT(65640),DIAGNOSTICS(168),POST_METADATA(-1);
        private final int bytes;ArtifactRole(int bytes){this.bytes=bytes;}public int fixedBytes(){return bytes;}
    }
    record OriginalArtifact(ArtifactRole role,byte[] bytes) {
        public OriginalArtifact {
            Objects.requireNonNull(role);Objects.requireNonNull(bytes);bytes=bytes.clone();
            StrictJson.require(role==ArtifactRole.POST_METADATA?bytes.length>0&&bytes.length<=16384:bytes.length==role.fixedBytes(),"exact bounded original physical region required");
            validate(role,bytes);
        }
        @Override public byte[] bytes(){return bytes.clone();}
        @Override public boolean equals(Object other){return other instanceof OriginalArtifact a&&role==a.role&&Arrays.equals(bytes,a.bytes);}
        @Override public int hashCode(){return 31*role.hashCode()+Arrays.hashCode(bytes);}
        public void requireReference(ExactRef ref){PresentationJson.original(ref,bytes);}
    }
    default ExactRef preservePresentationArtifact(OriginalArtifact original){throw new IllegalStateException("actual presentation binary archive unavailable");}
    default OriginalArtifact loadPresentationArtifact(ArtifactRole role,ExactRef original){throw new IllegalStateException("actual presentation binary archive unavailable");}
    default ExactRef presentationArtifactReferenceOf(OriginalArtifact original){throw new IllegalStateException("actual presentation binary archive unavailable");}

    private static void validate(ArtifactRole role,byte[] raw){
        if(role==ArtifactRole.POST_METADATA)OriginalOutcome.PostEvidence.decode(raw);
        // Every fixed-size binary role is raw custody, including torn/unavailable/partial-post diagnostics.
        // Only Posted.verifyOriginal or Acknowledged.verifyOriginal may interpret its matching semantic branch.
    }
}
