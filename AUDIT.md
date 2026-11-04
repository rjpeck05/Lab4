# Audit of AI-written code against its own constraints

Constraints audited: every gateway faked, no live model or network call, tests go through
`TestingApi` only, no assertions on console/view output, no UI imports in presenter tests.

## Checked and clean
- **Live calls in source:** none. The only real-world adapter is `SystemClock`, in
  `frameworks_drivers/`, and nothing under `tests/` or `interface_adapters/` imports it.
- **Wall-clock / real I/O:** no `datetime.now`, `time`, `input()`, `open()` or `print` outside
  `frameworks_drivers/`. `TestingApi` defaults to `FakeClock` and `FakeModelAdapter`.
- **Console assertions:** no test captures stdout/stderr or drives `StudentShell`. Every
  assertion is on a typed response, a raw error string, entity state, or a `ViewModel`.

## Caught and fixed
1. **Network guard had holes.** UDP `sendto`, `gethostbyname` (and `_ex`, `byaddr`) were not
   blocked; a test could have left the process. Guard widened in `tests/__init__.py`; new
   `NetworkGuardTest` proves each route is refused.
2. **Import check missed most spellings.** It caught `import urllib.request` but not
   `from urllib import request`, `from http import client`,
   `from study_room_booking import frameworks_drivers`, `subprocess`, or `_socket`.
   Rewritten (`forbidden_imports`) and unit-tested against each spelling; verified by planting
   a bad test file and watching the suite fail.
3. **A test reached past `TestingApi`.** The guardrail test read `api._bookings` (private
   state). Added public `TestingApi.bookings_for_room` and used it.

## Known limits (not fixed)
- A raw `_socket.socket().connect(...)` cannot be patched (C type). It is covered only by the
  import check, which forbids importing `_socket`; dynamic imports (`importlib`) are not seen.
- `tests/test_booking_a_study_room.py` predates the AI work. It drives the controllers, not
  `TestingApi`, and asserts on view-model text. It is not console output and uses only fakes,
  so it was left alone.
- The guardrail test asserts the hand-off view mentions "library staff". That couples a
  business-rule test to presenter wording; the presenter's exact text is pinned separately in
  `test_presenters.py`.
