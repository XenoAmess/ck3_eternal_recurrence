package org.xar.ck3.control.wave3.governance.educationprovider;

import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsComposer;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.Request;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.Validation;

/** In-process consumer seam; it performs no native call, file read, source qualification, or ledger mutation. */
public final class EducationProviderConsumerPort {
    private EducationProviderConsumerPort() { }
    public static Validation analyze(byte[] requestBytes) { return EducationProviderValidator.validate(EducationProviderCodec.decode(requestBytes)); }
    public static byte[] validateAndEncode(byte[] requestBytes) { return EducationProviderCodec.encode(analyze(requestBytes).provider()); }
    /** Keeps source proof distinct: EducationNeedsComposer still validates the complete original source attachment. */
    public static byte[] composeNeeds(byte[] requestBytes, byte[] decision, byte[] materials, byte[] originalSourceProof) {
        Request request = EducationProviderCodec.decode(requestBytes); Validation result = EducationProviderValidator.validate(request);
        byte[] provider = result.provider() == null ? null : EducationProviderCodec.encode(result.provider());
        return EducationNeedsComposer.composeDecision(decision, materials, provider, originalSourceProof);
    }
}
