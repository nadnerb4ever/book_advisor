# `book_advisor`

This package holds the **runnable application**: entrypoints, wiring, and glue that turn the rest of the codebase into something you can actually run. It **binds** domain logic, adapters, and infrastructure into a single coherent program.

Put supporting libraries and isolated concerns in sibling packages under `src/`; keep orchestration and app-specific composition here.
