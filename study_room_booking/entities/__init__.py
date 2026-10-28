# LAYER 1 - ENTITIES (enterprise business rules)
#
# DEPENDENCY RULE: source code dependencies may only point inwards. This is the
# innermost layer, so nothing in here may import from use_cases,
# interface_adapters or frameworks_drivers, and no third-party framework or
# library may be imported either (standard library only).
