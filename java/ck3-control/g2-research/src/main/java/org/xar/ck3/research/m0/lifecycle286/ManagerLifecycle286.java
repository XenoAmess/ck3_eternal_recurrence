package org.xar.ck3.research.m0.lifecycle286;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m0.lifecycle284.DeletingWrappers284;
import org.xar.ck3.research.m0.lifecycle284.PlayerInfoDeletingCalls284;
import org.xar.ck3.research.m0.lifecycle285.ManagerDestructorCalls285;
import org.xar.ck3.research.m0.staticobject357.ManagerStaticObjectB15000Calls;

/** Exact held manager-wrapper entry composed from existing normal-return components. */
public final class ManagerLifecycle286 {
    private ManagerLifecycle286() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls residual,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        GovernmentCrtBoundary185Api.Calls rows=PlayerInfoDeletingCalls284.bind(
                entry.imageBaseBits(),memory,residual);
        // The manager destructor itself binds its actual 28EE683 -> A07B00 call.
        GovernmentCrtBoundary185Api.Calls destructor=ManagerDestructorCalls285.bind(
                entry.imageBaseBits(),memory,rows,budget);
        return DeletingWrappers284.executeManager(entry,memory,destructor);
    }

    /** Explicitly enables the qualified static supplier; legacy execute remains residual. */
    public static GovernmentCrtBoundary185Api.NormalReturn executeWithStaticObject357(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls residual,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        return execute(entry,memory,ManagerStaticObjectB15000Calls.bind(
                entry.imageBaseBits(),memory,residual),budget);
    }
}
