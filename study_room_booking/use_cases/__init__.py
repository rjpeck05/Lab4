# LAYER 2 - USE CASES (application business rules)
#
# DEPENDENCY RULE: source code dependencies may only point inwards. This layer
# may import from entities (and itself) only. It must never import from
# interface_adapters or frameworks_drivers, and no framework or third-party
# library may be imported (standard library only). Anything it needs from the
# outside world is declared here as an interface (ports.py, output boundaries)
# and implemented by an outer layer.
