from app.core.application import Application
from app.core.settings import Settings  


def main() -> None:
    settings = Settings.from_env()
    app = Application(settings)
    app.run()

if __name__ == "__main__":
    main()

    