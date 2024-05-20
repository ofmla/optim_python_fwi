"""
shot generation script
"""
from shot_control_generation import ControlGetshot


def main():
    control_shot = ControlGetshot()
    control_shot.generate_shot_files()


if __name__ == "__main__":
    main()
