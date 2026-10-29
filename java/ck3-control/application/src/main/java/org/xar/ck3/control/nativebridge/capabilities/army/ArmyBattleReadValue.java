package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Pure application view of an actual strict M5 read. A value alone never qualifies an archived receipt. */
public interface ArmyBattleReadValue {
    enum Kind { CONTROL, TRANSITION, TERMINAL }
    Kind kind();
    Obj normalized();
    BigInteger sequence();
    Obj extensions();
}
