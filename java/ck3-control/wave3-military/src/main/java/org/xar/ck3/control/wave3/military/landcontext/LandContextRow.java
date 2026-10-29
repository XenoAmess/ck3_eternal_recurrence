package org.xar.ck3.control.wave3.military.landcontext;

/** One already bounded strengths observation. Null families retain unpublished/unknown semantics. */
public record LandContextRow(boolean available, Integer armyId, Integer nativeCarmyId,
                             Long currentObservedTotalRateRaw, LandRateInputs rateInputs,
                             LandResupply resupply, ProvinceContributors province) {}
