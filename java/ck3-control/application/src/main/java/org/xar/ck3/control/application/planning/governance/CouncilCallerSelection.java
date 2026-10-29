package org.xar.ck3.control.application.planning.governance;

import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicit caller candidate with real native legality, without the ordinary skill/upgrade selector. */
public final class CouncilCallerSelection {
    private CouncilCallerSelection() { }
    public static CouncilSelection.Decision select(CouncilSelection.Query actual,int characterId) {
        StrictJson.require(actual.available(),"actual private Council final material is unavailable");
        var candidates=actual.candidates().stream().filter(value->value.characterId().intValueExact()==characterId&&value.nativeLegal()).toList();
        StrictJson.require(candidates.size()==1&&!actual.incumbent().filter(value->value.intValueExact()==characterId).isPresent(),"explicit candidate lacks its native final legality");
        return new CouncilSelection.Decision(actual.incumbent().isPresent()?CouncilSelection.Outcome.REPLACE_REQUIRED:CouncilSelection.Outcome.ASSIGN_REQUIRED,
                Optional.of(candidates.getFirst()),actual,"explicit_public_caller_native_final_candidate");
    }
}
