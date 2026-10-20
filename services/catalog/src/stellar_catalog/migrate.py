from stellar_common.database import engine_for, migrate

def main():
    engine = engine_for("CATALOG_WRITER_DSN", "catalog_writer", "stellar_catalog")
    try:
        migrate("stellar_catalog", "catalog", engine)
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()
