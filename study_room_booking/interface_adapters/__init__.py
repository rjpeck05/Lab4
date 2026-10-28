# LAYER 3 - INTERFACE ADAPTERS
#
# DEPENDENCY RULE: source code dependencies may only point inwards. This layer
# may import from use_cases and entities (and itself), but never from
# frameworks_drivers. No web/UI/database framework is imported here either:
# adapters convert data into the shape the next layer wants, and the concrete
# frameworks are plugged in from the outermost layer.
