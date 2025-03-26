from __future__ import annotations  # Allows forward references
from threading import Event
from typing import Callable
import qi

# Constants

# Touch
HEAD_FRONT_TOUCH = "Head/Touch/Front"


def use_service(behavior: Behavior, service_name: str):
    service = behavior.application.services.get(service_name, None)

    if service is None:
        service = behavior.session.service(service_name)
        behavior.application.services[service_name] = service

    return service


class Application:
    # Config
    name: str = "default_application_name"
    ip_address: str = "127.0.0.1:9559"

    # Application components
    current_behavior: Behavior
    qi_application: qi.Application
    session: qi.Session
    services: dict[str, object]

    def __init__(self, application_name: str, ip: str):
        self.name = application_name
        self.ip_address = ip
        print("Starting application...")

        self.qi_application = qi.Application(
            url=f"tcp://{self.ip_address}", autoExit=False
        )
        self.qi_application.start()
        self.session = self.qi_application.session
        self.services = {}

    def run(self, behavior: Behavior):
        print("Running application...")
        self.current_behavior = behavior
        self.current_behavior.activate()
        self.qi_application.run()


class Behavior:
    application: Application
    session: qi.Session
    _active: bool = False

    # Basic Services
    memory_service = None
    tts_service = None

    subscribers = []

    def __init__(self, application: Application):
        print("Initializing behavior...")
        self.application = application
        self.session = application.session
        self.memory_service = use_service(self, "ALMemory")
        self.tts_service = use_service(self, "ALTextToSpeech")

    def activate(self) -> None:
        """Function that will be called on behavior initialization"""
        print("Activating behavior...")
        if not self._active:
            print("Behavior activated")
            self._active = True
            self.on_activate()

    def deactivate(self) -> None:
        """Function that will be called on behavior exit"""
        if self._active:
            self._active = False
            self.on_deactivate()

    def say(self, message: str):
        self.tts_service.say(message)

    def on_body_touched(self, callback: Callable, body_part: str | None = None):
        touch = self.memory_service.subscriber("TouchChanged")
        self.subscribers.append(touch)

        def touch_verifier(touch_updates):
            for touch_update in touch_updates:
                if touch_update[1]:
                    body_parts = touch_update[0]
                    if body_part and body_part != body_parts:
                        continue

                    callback(body_parts)

        touch.signal.connect(touch_verifier)

    def await_touch(self, body_part: str | None = None) -> str:
        """
        Pause code execution until a touch is detected on a specific body part.

        Args:
            body_part (str, optional): Specific body part to wait for touch.
                                    If None, waits for any body part touch.

        Returns:
            str: The body part that was touched
        """
        # Create a threading event to block execution
        touch_event = Event()

        # Variable to store the touched body part
        touched_part = [None]

        def touch_callback(body_parts):
            """Internal callback to handle touch detection"""
            # If no specific body part is specified or the touched part matches
            if body_part is None or body_part == body_parts:
                touched_part[0] = body_parts
                touch_event.set()

        # Set up the touch subscriber
        self.on_body_touched(touch_callback, body_part)

        # Block until touch is detected
        touch_event.wait()

        # Remove the subscriber to prevent memory leaks
        self.subscribers.clear()

        return touched_part[0]

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass
