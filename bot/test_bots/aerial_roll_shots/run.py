import sys

DEFAULT_LOGGER = 'rlbot'

if __name__ == '__main__':

    try:
        if len(sys.argv) > 1 and sys.argv[1] == 'gui':
            from rlbot.gui.qt_root import RLBotQTGui

            RLBotQTGui.main()
        else:
            from rlbot import runner

            runner.main()
    except Exception as e:
        print("Encountered exception: ", e)
        print("Press enter to close.")
        input()
