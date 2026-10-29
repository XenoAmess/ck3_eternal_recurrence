package org.xar.ck3.control.wave2.governance.educationpreference;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.*;

/** Single-direction boundary adapter from the actual typed needs producer to request ordering. */
public final class EducationNeedsPreferenceAdapter {
    private EducationNeedsPreferenceAdapter() { }

    public static RequestObservation fromNeedsRow(EducationNeedsModel.NeedsRowProjection needs, long guardianFullId,
            byte[] guardianQueryFrame, BigInteger queryNativeRevision, Optional<GuardianProfile> profile) {
        ObjectNode frame = StrictJson.object(); frame.put("native_revision", needs.focusSourceFrame().nativeRevision());
        frame.put("played_character_id", needs.focusSourceFrame().playedCharacterId());
        frame.put("heir_character_id", needs.focusSourceFrame().heirCharacterId()); frame.put("date_raw", needs.focusSourceFrame().dateRaw());
        return new RequestObservation(new Pair(needs.childFullId(), guardianFullId), needs.occurrenceIndices(), needs.focusManagement(),
                EducationPreferenceCodec.focusFrameProjection(StrictJson.canonical(frame)),
                EducationPreferenceCodec.guardianFrameProjection(guardianQueryFrame), queryNativeRevision, profile);
    }
}
