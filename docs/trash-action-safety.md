# Empty-trash action: failure reporting

The existing action requires `gio` and explicit confirmation in the interface. It runs `gio trash --empty` without a shell, with a 180-second timeout. It can permanently remove trash from supported locations, including mounted volumes; inspect the trash and backups before confirming. There is no undo.

If `gio` is not found before launch, the action reports that it is not installed and does not start the command. If the command times out or exits unsuccessfully, Avelin warns that some files may already have been permanently deleted. Inspect the trash before taking further action; the error does not establish which files remain or whether all backend activity has stopped. A successful exit likewise does not verify each trash location or guarantee that inaccessible items were removed.

These reports do not provide a deletion preview, recovery, or an atomic operation. Desktop backends, permissions, mounts, and real timeout behavior require testing on supported systems. Tests simulate failures and do not empty any trash.

References: [GLib gio command](https://docs.gtk.org/gio/), [Python subprocess timeout](https://docs.python.org/3/library/subprocess.html#subprocess.run).
