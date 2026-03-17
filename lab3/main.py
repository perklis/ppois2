import pygame

from game.game import Game


def main():
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()

    from pathlib import Path
    base_dir = Path(__file__).resolve().parent

    from config_loader import load_json
    settings = load_json(base_dir / "data" / "settings.json")

    screen = pygame.display.set_mode(
        (settings["screen"]["width"], settings["screen"]["height"]),
        pygame.RESIZABLE,
    )
    pygame.display.set_caption(settings["screen"]["title"])

    game = Game(screen, base_dir)
    game.run()


if __name__ == "__main__":
    main()
