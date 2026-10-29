package org.xar.ck3.control.g2.m7;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.campaigncadence.CampaignCalendar;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Same-frame calendar DATA, consumed only after the actual Native/Driver join. No authority is minted. */
public final class NativeCalendarObservation {
    public static final String SCHEMA = "xar.g2.m7.native-calendar-observation/v1";
    public static final int MAX_BYTES = 32_768;
    private NativeCalendarObservation() { }

    /** The existing exact GameGeneration and complete public/native identity remain the field authority. */
    public record Observed(ObservationIdentity identity, G2Source source, String date) {
        public Observed {
            Objects.requireNonNull(identity); Objects.requireNonNull(source);
            StrictJson.require(source.machineId().equals(identity.machineId()) && source.sourceRef().bytes() > 0,
                    "calendar source must belong to the complete observed machine");
            NativeCharacterId.of(identity.frame().identity().player());
            StrictJson.require(identity.frame().identity().nativeRevision().signum() > 0
                    && identity.frame().revision().signum() >= 0, "actual positive native and non-negative public frame required");
            StrictJson.require(CampaignCalendar.rawToDate(nativeRaw(identity)).equals(date),
                    "calendar date must be the shared fixed-365 whole-day projection");
        }
        public int dateRaw() { return nativeRaw(identity); }
    }

    /**
     * The assembler supplies its already parsed immutable original semantic fields. Unrelated decimal
     * metrics remain untouched; every consumed identity/date field must retain its original token kind.
     * G2Source and ObservationIdentity are provenance DATA, never proof that a Native read occurred.
     */
    public static Observed project(ObservationIdentity identity, G2Source source, OpportunityJson.Obj semantic) {
        Objects.requireNonNull(identity); Objects.requireNonNull(source); Objects.requireNonNull(semantic);
        var frame = identity.frame(); var nativeFrame = frame.identity();
        StrictJson.require(frame.snapshotId().equals(text(semantic, "snapshot_id"))
                && frame.episodeRunId().equals(text(semantic, "episode_run_id"))
                && frame.revision().equals(integer(semantic, "revision"))
                && nativeFrame.nativeRevision().equals(integer(semantic, "native_revision"))
                && nativeFrame.dateRaw().equals(integer(semantic, "date_raw")),
                "calendar fields crossed the complete public/native/episode frame");
        OpportunityJson.Obj player = OpportunityJson.object(semantic.get("played_character"), "played_character");
        StrictJson.require(nativeFrame.player().equals(integer(player, "character_id")),
                "calendar fields crossed the actual full-generation ruler");
        return new Observed(identity, source, CampaignCalendar.rawToDate(nativeRaw(identity)));
    }

    /** Small persistence projection; the common identity/source codecs own their complete JSON fields. */
    public static byte[] encode(Observed value) {
        Objects.requireNonNull(value); ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA);
        row.set("identity", ProposalLifecycleCodec.observation(value.identity()));
        row.set("source", ProposalLifecycleCodec.source(value.source()));
        row.put("calendar_profile", CampaignCalendar.PROFILE); row.put("date", value.date());
        return StrictJson.canonical(row, MAX_BYTES);
    }

    public static Observed decode(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, MAX_BYTES),
                Set.of("schema", "identity", "source", "calendar_profile", "date"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema")))
                && CampaignCalendar.PROFILE.equals(StrictJson.text(row.get("calendar_profile"))),
                "exact native calendar observation/profile required");
        return new Observed(ProposalLifecycleCodec.decodeObservation(row.get("identity")),
                G2Wire.source(row.get("source")), StrictJson.text(row.get("date")));
    }

    private static BigInteger integer(OpportunityJson.Obj row, String key) {
        return OpportunityJson.integer(row.get(key), key);
    }
    private static String text(OpportunityJson.Obj row, String key) {
        return OpportunityJson.text(row.get(key), key);
    }
    private static int nativeRaw(ObservationIdentity identity) {
        BigInteger raw = identity.frame().identity().dateRaw();
        StrictJson.require(raw.compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) >= 0
                && raw.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "native CDate raw signed32 required");
        return raw.intValueExact();
    }
}
