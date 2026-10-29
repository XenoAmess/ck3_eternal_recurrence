package org.xar.ck3.control.application.driver;

import java.util.LinkedHashMap;
import java.util.Objects;
import java.util.List;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Native-campaign snapshot DATA. This projection creates no episode identity, lifecycle binding or permission. */
public final class NativeCampaignProjection {
    public static final String WIRE_MODE = "native_campaign";
    private static final List<String> ORIGINAL_EPISODE_FIELDS=List.of("episode_run_id","episode_character_id","succession_lifecycle",
            "episode_identity_pending","one_life_terminal","one_life_terminal_reason");
    private NativeCampaignProjection() { }

    /** Preserve missing, null and existing episode/lifecycle fields from this exact original packet. */
    public static OpportunityJson.Obj originalSnapshot(ObservedFrame actual) {
        var original = DriverObservationAssembler.originalNativeState(Objects.requireNonNull(actual));
        var fields = new LinkedHashMap<>(original.members());
        fields.put("episode_projection", new OpportunityJson.Text(WIRE_MODE));
        return new OpportunityJson.Obj(fields);
    }

    public static RawJson encodeOriginalSnapshot(ObservedFrame actual) {
        return RawJson.fullMaterial(DriverJson.encode(originalSnapshot(actual)));
    }

    /** Private Driver auxiliary metadata cannot supply Native episode fields in the explicit campaign projection. */
    public static OpportunityJson.Obj withoutDriverEpisodeOverlay(OpportunityJson.Obj originalAuxiliary) {
        var retained=new LinkedHashMap<>(Objects.requireNonNull(originalAuxiliary).members());
        ORIGINAL_EPISODE_FIELDS.forEach(retained::remove);
        return new OpportunityJson.Obj(retained);
    }

    /** Sole joined profile overlay: restore actual original episode fields after the common Native/Driver join. */
    public static OpportunityJson.Obj withOriginalEpisodeFields(ObservedFrame actual,OpportunityJson.Obj joined) {
        var original=DriverObservationAssembler.originalNativeState(Objects.requireNonNull(actual));
        var fields=new LinkedHashMap<>(Objects.requireNonNull(joined).members());
        for(String name:ORIGINAL_EPISODE_FIELDS) {
            if(original.members().containsKey(name))fields.put(name,original.get(name));else fields.remove(name);
        }
        fields.put("episode_projection",new OpportunityJson.Text(WIRE_MODE));
        return new OpportunityJson.Obj(fields);
    }

    /** Full joined semantic DATA is accepted only through the sole profile-four assembler replay. */
    public static void requireJoinedSnapshot(DriverObservationAssembler.FullSnapshot actual,RawJson expected) {
        Objects.requireNonNull(actual);Objects.requireNonNull(expected);
        StrictJson.require(actual.facts().observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,
                "actual native campaign observation profile required");
        var replay=new DriverObservationAssembler().projectFull(actual.actual(),actual.facts(),actual.originalEvidence());
        StrictJson.require(replay.semantic().equals(DriverJson.object(expected.bytes(),RawJson.MAXIMUM_BYTES))
                &&replay.semantic().equals(actual.semantic())&&replay.fullBindingSha256().equals(actual.fullBindingSha256()),
                "joined native campaign snapshot differs from its exact Native/Driver originals");
    }

    /** Checks the actual original snapshot projection, without accepting a caller's ordinary episode binding. */
    public static void requireOriginalSnapshot(ObservedFrame actual, RawJson expected) {
        Objects.requireNonNull(expected);
        StrictJson.require(originalSnapshot(actual).equals(DriverJson.object(expected.bytes(), RawJson.MAXIMUM_BYTES)),
                "native campaign snapshot differs from its original frame or overwrote original episode fields");
    }
}
