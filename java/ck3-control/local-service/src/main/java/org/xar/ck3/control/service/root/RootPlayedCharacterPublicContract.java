package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Original Service checks over actual typed input and output; no observation or switch authority is created. */
public final class RootPlayedCharacterPublicContract {
    private RootPlayedCharacterPublicContract() { }

    public static void requireCapability(Set<String> actualCapabilities){
        if(!Objects.requireNonNull(actualCapabilities).contains(OperatorPlayerSwitch.CAPABILITY))
            throw failure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,
                    "capability_not_available: selected backend cannot rebind the played character");
    }

    /** Called with the actual full BEFORE semantic lane, whose revisions are internal exact integers. */
    public static void requireBefore(OperatorPlayerSwitch.Request request,OpportunityJson.Obj actual){
        Objects.requireNonNull(request);Objects.requireNonNull(actual);
        if(!new OpportunityJson.Bool(true).equals(actual.get("paused"))||!new OpportunityJson.Bool(true).equals(actual.get("map_ready")))
            throw failure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                    "played-character rebind requires a paused map-ready snapshot");
        BigInteger revision;
        try{
            revision=OperatorPlayerSwitch.internalRevision(actual.get("revision"));
        }catch(IllegalArgumentException malformed){
            throw failure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                    "played-character rebind requires an exact uint64 snapshot revision");
        }
        if(!revision.equals(request.expectedRevision()))
            throw failure(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                    "played-character rebind revision mismatch: expected "+request.expectedRevision()+", current "+revision);
    }

    /** Preserve the original immutable public bytes after checking the same fields as the original Service. */
    public static RawJson requireResult(OperatorPlayerSwitch.Request request,RawJson actual){
        Objects.requireNonNull(request);
        try{
            if(actual==null)throw new IllegalArgumentException("missing actual operator result");
            var result=DriverJson.object(actual.bytes(),RawJson.MAXIMUM_BYTES);
            boolean accepted=new OpportunityJson.Bool(true).equals(result.get("accepted"));
            boolean verified=new OpportunityJson.Bool(true).equals(result.get("postcondition_verified"));
            String status=OpportunityJson.text(result.get("status"),"status");
            OperatorPlayerSwitch.NativeStatus.parse(status);
            BigInteger target=OpportunityJson.integer(result.get("to_character_id"),"to_character_id");
            if(!accepted||!verified||!target.equals(BigInteger.valueOf(request.characterId())))
                throw new IllegalArgumentException("actual operator postcondition differs from original caller");
            return actual;
        }catch(IllegalArgumentException malformed){
            throw failure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                    "played-character rebind returned a malformed postcondition");
        }
    }

    private static PublicServiceFailure failure(PublicServiceFailure.Kind kind,String originalMessage){
        return new PublicServiceFailure(kind,originalMessage,Optional.empty());
    }
}
