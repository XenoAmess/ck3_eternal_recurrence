package org.xar.ck3.study.m6.poststate242;

import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api.NormalRule;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api.SourceSite;

/** Exactly the held full715/402/227 CALLs. No old437 filter, upper150 clone or unheld644 row. */
public final class CallOutcome242Sites {
    private CallOutcome242Sites() { }
    private static final long U715=0x21A5050L,MOVE=0xB2EEE0L,SWAP=0xB2EDF0L;
    private static final List<SourceSite> SITES=List.of(
            indirect(U715,0x21A508FL),
            known(U715,0x21A511AL,U715),
            known(U715,0x21A5126L,U715),
            known(U715,0x21A5133L,U715),
            indirect(U715,0x21A5159L),
            indirect(U715,0x21A51B9L),
            indirect(U715,0x21A5223L),
            indirect(MOVE,0xB2EF06L),
            known(MOVE,0xB2EF18L,SWAP),
            indirect(MOVE,0xB2EF9EL),
            directOpaque(MOVE,0xB2EFADL,0x4226860L),
            directOpaque(MOVE,0xB2EFBBL,0x4226860L),
            directOpaque(MOVE,0xB2EFD2L,0x4226860L),
            indirect(MOVE,0xB2EFE5L),
            directOpaque(MOVE,0xB2EFFEL,0x4226860L),
            directOpaque(MOVE,0xB2F02DL,0x4220AA4L),
            directOpaque(MOVE,0xB2F038L,0x4220AA4L),
            directOpaque(MOVE,0xB2F043L,0x4220AA4L),
            known(SWAP,0xB2EE82L,MOVE),
            known(SWAP,0xB2EE8EL,MOVE),
            known(SWAP,0xB2EE9BL,MOVE),
            indirect(SWAP,0xB2EEBBL));

    public static List<SourceSite> all() { return SITES; }

    public static SourceSite require(long ownerEntryRva,long callSiteRva) {
        for(SourceSite source:SITES)
            if(source.ownerEntryRva()==ownerEntryRva && source.callSiteRva()==callSiteRva)return source;
        throw new UnsupportedOperationException("Not a held715/B2 CALL: owner="
                +Long.toHexString(ownerEntryRva)+" site="+Long.toHexString(callSiteRva));
    }

    private static SourceSite indirect(long owner,long site) {
        // directTargetRva is unused for a runtime-resolved absolute indirect target.
        return new SourceSite(owner,site,TargetKind.INDIRECT_ABSOLUTE,3,0L,NormalRule.OPAQUE_PRESERVES_N);
    }
    private static SourceSite directOpaque(long owner,long site,long target) {
        return new SourceSite(owner,site,TargetKind.DIRECT_RVA,5,target,NormalRule.OPAQUE_PRESERVES_N);
    }
    private static SourceSite known(long owner,long site,long target) {
        return new SourceSite(owner,site,TargetKind.DIRECT_RVA,5,target,NormalRule.KNOWN_ACTUAL_N);
    }
}
