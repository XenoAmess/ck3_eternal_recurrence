package org.xar.ck3.control.application.capabilities;

import java.math.BigInteger;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;

/** Finite validated faction original DATA shared below transport. No read or cache authority. */
public interface FactionReadObservation {
    BigInteger querySequence();
    FactionAlertModel.Frame frame();
    RawJson normalizedAlert();
    RawJson originalResult();
    String originalResultSha256();
}
