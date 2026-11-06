try:
    from .app import main
except (ImportError, ValueError) as exc:
    raise SystemExit('Avelin needs Python 3, PyGObject, GTK 4 and pycairo. See README.md.\n' + str(exc))
main()
