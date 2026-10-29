package org.xar.ck3.control.governance.council;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Closed public submission material only. The sole coordinator must separately authorize and persist any explicit protocol ID. */
public final class CouncilCallerSubmission {
    public static final String SCHEMA="xar.java.public-council-assignment/v1";
    private CouncilCallerSubmission() { }
    public static Optional<String> requestedId(ObjectNode arguments) {
        if(!arguments.has("public_submission_schema")) {
            StrictJson.require(!arguments.has("caller_request_id"),"caller native ID requires its exact public submission schema");return Optional.empty();
        }
        StrictJson.object(arguments,Set.of("position_key","candidate_character_id","original_query","expected_has_incumbent","expected_incumbent_character_id","public_submission_schema","caller_request_id"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(arguments.get("public_submission_schema"))),"unknown public Council submission schema");
        if(arguments.get("caller_request_id").isNull())return Optional.empty();
        String id=StrictJson.text(arguments.get("caller_request_id"));StrictJson.require(id.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}"),"original Council bounded native token required");return Optional.of(id);
    }
    public static boolean isPublic(ObjectNode arguments) {if(!arguments.has("public_submission_schema"))return false;requestedId(arguments);return true;}
    public static void requirePreparedId(ObjectNode arguments,String actualCoordinatorRequestId) {
        requestedId(arguments).ifPresent(requested->StrictJson.require(requested.equals(actualCoordinatorRequestId),"source-qualified coordinator has not issued the caller's original Council protocol ID; no packet substitution allowed"));
    }
}
