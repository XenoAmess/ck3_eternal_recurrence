package org.xar.ck3.control.wave2.military.countyentry;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Current native observations. These values never represent an applied loss. */
public record CountyEntryInputs(Budget budget, Condition condition, Optional<MultiplierFloors> multiplierFloors) {
    public static final int FRACTION_SCALE = 100_000;
    public static final String SOURCE = "native_current_county_entry_inputs";
    public static final String CONDITION_SOURCE = "current_stored_route_first_province";
    public static final String FLOORS_SOURCE = "native_current_county_multiplier_floor_inputs";

    public CountyEntryInputs {
        Objects.requireNonNull(budget); Objects.requireNonNull(condition); Objects.requireNonNull(multiplierFloors);
        StrictJson.require(!(budget instanceof UnavailableBudget && condition instanceof AvailableCondition),
                "unavailable county budget cannot publish an available condition");
        if (condition instanceof AvailableCondition observed && multiplierFloors.orElse(null) instanceof AvailableFloors floors) {
            StrictJson.require(observed.mode() == (floors.army1d4Raw() == 0 ? 1 : 0),
                    "county condition mode and Army1D4 byte disagree");
        }
    }

    public sealed interface Budget permits AvailableBudget, UnavailableBudget { }
    public record AvailableBudget(int wholeSoldiers, int currentLossBudget, long effectiveFractionRaw,
                                  long minimumMultiplierRaw, int loadedMinimumSoldiers) implements Budget {
        public AvailableBudget {
            StrictJson.require(currentLossBudget >= 0 && currentLossBudget <= wholeSoldiers,
                    "current native county budget must be bounded by whole strength");
        }
    }
    public record UnavailableBudget(String reason) implements Budget {
        public UnavailableBudget { StrictJson.text(reason); }
    }

    public sealed interface Condition permits AvailableCondition, UnavailableCondition { }
    public record AvailableCondition(int actorCharacterId, int sourceProvinceId, int targetProvinceId,
                                     int mode, boolean passes) implements Condition {
        public AvailableCondition {
            StrictJson.require(actorCharacterId >= 0 && sourceProvinceId >= 1 && targetProvinceId >= 1,
                    "resolved signed32 actor and province identities required");
            StrictJson.require(mode == 0 || mode == 1, "native county mode must be zero or one");
        }
    }
    public record UnavailableCondition(String reason) implements Condition {
        public UnavailableCondition { StrictJson.text(reason); }
    }

    public sealed interface MultiplierFloors permits AvailableFloors, UnavailableFloors { }
    public record AvailableFloors(long baseFloorRaw, long army1d4NonzeroFloorRaw, int army1d4Raw) implements MultiplierFloors {
        public AvailableFloors { StrictJson.require(army1d4Raw >= 0 && army1d4Raw <= 255, "Army1D4 unsigned byte required"); }
    }
    public record UnavailableFloors(String reason) implements MultiplierFloors {
        public UnavailableFloors { StrictJson.text(reason); }
    }
}
