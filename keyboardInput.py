import threading

from inputs import get_key


class KeyBoardInput:
    def __init__(self):
        self.shot_taking = False

    def get_output(self):
        if self.shot_taking:
            self.shot_taking = False
            return True
        return False

    def main_poll_loop(self):
        while 1:
            events = get_key()
            for event in events:
                if event.code == "KEY_1" and event.state == 1:
                    self.shot_taking = True


keyboard = KeyBoardInput()
threading.Thread(target=keyboard.main_poll_loop, daemon=True).start()
