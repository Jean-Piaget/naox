import qi
from core.behavior import Behavior
from core.application import Application


def main() -> None:
    app = qi.Application()
    app.start()
    session = app.session
    tts = session.service("ALTextToSpeech")
    tts.say("Hello Word")
