// Included inside xar::game after the existing PropertyContainer DTO.
struct ContextSourceTailGovernmentV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<bool> land_present;
  std::optional<std::string> government_selection;
  std::optional<std::string> government_identity;
  std::optional<std::uint32_t> government_magic_raw;
  std::optional<bool> admitted;
  std::optional<std::string> property_870_identity;
  std::optional<ContextSourcePropertiesV1> property_870;
  std::optional<bool> second_land_present;
  std::optional<std::uint32_t> subcarrier_magic_raw;
  std::optional<std::int32_t> subcarrier_full_id_raw;
  std::optional<bool> additional_a30_admitted;
  std::optional<std::string> property_a30_identity;
  std::optional<ContextSourcePropertiesV1> property_a30;
  std::string reason;
  friend bool operator==(const ContextSourceTailGovernmentV1 &,
                         const ContextSourceTailGovernmentV1 &) = default;
};

struct ContextSourceTailWeightedRowV1 {
  std::int32_t native_index = -1;
  std::optional<std::string> property_identity;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::optional<std::int64_t> weight_q64;
  std::string reason;
  friend bool operator==(const ContextSourceTailWeightedRowV1 &,
                         const ContextSourceTailWeightedRowV1 &) = default;
};

struct ContextSourceTailWeightedV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<bool> carrier_present;
  std::optional<std::int32_t> key_274_raw;
  std::optional<std::string> selection;
  std::optional<std::string> selected_identity;
  std::optional<std::int32_t> count_63c;
  std::optional<bool> array_present;
  std::optional<std::vector<ContextSourceTailWeightedRowV1>> rows;
  std::string reason;
  friend bool operator==(const ContextSourceTailWeightedV1 &,
                         const ContextSourceTailWeightedV1 &) = default;
};

struct ContextSourceTailDirectV1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = -1;
  ContextSourceTailGovernmentV1 government_870_a30;
  ContextSourceTailWeightedV1 carrier_weighted630;
  std::string reason;
  friend bool operator==(const ContextSourceTailDirectV1 &,
                         const ContextSourceTailDirectV1 &) = default;
};
