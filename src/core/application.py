import qi
from core.behavior import Behavior


class Application:
    # Config
    name = "default_application_name"
    ip_address = "127.0.0.1:9559"

    # Application
    current_behavior: Behavior
    qi_application = None
    session = None

    def __init__(self, application_name: str, ip: str):
        self.name = application_name
        self.ip_address = ip

    def run(self, behavior: Behavior):
        self.current_behavior = behavior
        self.qi_application = qi.Application(url=self.ip_address)
        self.qi_application.start()
        self.session = self.qi_application.session
        tts = self.session.service("ALTextToSpeech")
        tts.say(f"Inicializando {self.name}")
        self.qi_application.run()
