# Stewart CVM Protocol Notes

This library intentionally implements only the subset of the Stewart CVM protocol that is needed for reliable integration work.

Primary reference:
- Stewart Filmscreen CVM documentation: https://www.stewartfilmscreen.com/Files/files/Support%20Material/Controls/CVM.pdf

Supported protocol surface:
- Commands: `UP`, `DOWN`, `STOP`, `RECALL`, `STORE`
- Queries: `POSITION`
- Events: `POSITION`, `STATUS`
- Motors: `1.1.1.MOTOR` through `1.1.4.MOTOR`
- Global motor target for presets: `1.1.0.MOTOR`

Behavioral rules in this library:
- Commands are serialized through a single queue.
- Commands are paced conservatively by default with a `1.0s` inter-command delay.
- Preset numbers are validated as `1-24`.
- Reconnect and callback behavior are deterministic and owned by the client layer.

Non-goals:
- Modeling installation-specific preset names or theater semantics.
- Inventing absolute positioning APIs that the documented protocol does not actually provide.
