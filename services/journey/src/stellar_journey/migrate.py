from stellar_common.database import engine_for, migrate

def main():
    engine = engine_for("JOURNEY_OWNER_DSN", "journey_owner", "stellar_journey")
    try:
        migrate("stellar_journey", "journey", engine)
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()
