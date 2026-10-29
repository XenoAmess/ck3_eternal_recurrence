package org.xar.ck3.control.application.action;

import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Actual pre-Start bookmark identity. A native actor ID is learned only from the real post-Start publication. */
public record FrontendGameplayExpectedPostcondition(FrontendIdentity before, G2Source source,
        String observerSchema, String selectedBookmarkKey, String selectedCharacterNameKey, int selectedDateRaw,
        List<ExpectedValue> values) {
    public static final String SCHEMA = "xar.java.frontend-gameplay-entry/v1";
    public FrontendGameplayExpectedPostcondition {
        Objects.requireNonNull(before); Objects.requireNonNull(source); StrictJson.text(observerSchema);
        StrictJson.require(before.frame() instanceof FrontendFrame.Menu, "gameplay entry requires an actual frontend menu origin");
        StrictJson.require(before.machineId().equals(source.machineId()), "gameplay entry source machine drift");
        StrictJson.require(selectedBookmarkKey != null && selectedBookmarkKey.matches("[A-Za-z0-9_]{1,128}")
                && selectedCharacterNameKey != null && selectedCharacterNameKey.matches("[A-Za-z0-9_]{1,128}"),
                "actual native selected bookmark and character name keys required");
        values = List.copyOf(values); StrictJson.require(!values.isEmpty(), "explicit gameplay entry observations required");
        var fields = new HashSet<FieldKey>();
        for (ExpectedValue value : values) StrictJson.require(fields.add(value.field()), "duplicate gameplay entry expected field");
        StrictJson.require(values.contains(new ExpectedText(new FieldKey("selected_bookmark_key"), selectedBookmarkKey))
                && values.contains(new ExpectedText(new FieldKey("selected_character_name_key"), selectedCharacterNameKey))
                && values.contains(new ExpectedInteger(new FieldKey("date_raw"), java.math.BigInteger.valueOf(selectedDateRaw)))
                && values.contains(new ExpectedBoolean(new FieldKey("map_ready"), true))
                && values.contains(new ExpectedBoolean(new FieldKey("paused"), true)),
                "entry expected fields must bind the real selected identity/date and paused ready map");
    }
}
