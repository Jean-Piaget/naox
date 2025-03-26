from __future__ import annotations  # Allows forward references
from typing import Callable, Optional
import qi
from threading import Event

# Constants
# Touch
HEAD_FRONT_TOUCH = "Head/Touch/Front"
HEAD_MIDDLE_TOUCH = "Head/Touch/Middle"
HEAD_REAR_TOUCH = "Head/Touch/Rear"


def use_service(behavior: Behavior, service_name: str):
    """
    Retrieve or create a service for the given behavior.

    Args:
        behavior (Behavior): The current behavior context
        service_name (str): Name of the service to retrieve or create

    Returns:
        object: The requested service
    """
    service = behavior.application.services.get(service_name, None)
    if service is None:
        service = behavior.session.service(service_name)
        behavior.application.services[service_name] = service
    return service


class Application:
    """
    Manages the NAO robot application lifecycle and session.

    Attributes:
        name (str): Name of the application
        ip_address (str): IP address of the NAO robot
        qi_application (qi.Application): QiFramework application instance
        session (qi.Session): QiFramework session
        services (dict): Cached services
        current_behavior (Behavior): Currently active behavior
    """

    name: str = "default_application_name"
    ip_address: str = "127.0.0.1:9559"
    current_behavior: Behavior
    qi_application: qi.Application
    session: qi.Session
    services: dict[str, object]

    def __init__(self, application_name: str, ip: str):
        """
        Initialize the NAO robot application.

        Args:
            application_name (str): Name of the application
            ip (str): IP address of the NAO robot
        """
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
        """
        Run the specified behavior.

        Args:
            behavior (Behavior): Behavior to activate and run
        """
        print("Running application...")
        self.current_behavior = behavior
        self.current_behavior.activate()
        self.qi_application.run()


class Behavior:
    """
    Base class for defining robot behaviors with touch and marker interactions.

    Attributes:
        application (Application): Reference to the parent application
        session (qi.Session): QiFramework session
        memory_service (object): ALMemory service
        tts_service (object): Text-to-Speech service
        marker_service (object): Marker detection service
        subscribers (list): List of event subscribers
    """

    application: Application
    session: qi.Session
    _active: bool = False

    memory_service = None
    marker_service = None
    tts_service = None

    touch_subscribers = []
    marker_subscribers = []

    def __init__(self, application: Application):
        """
        Initialize the behavior with application context.

        Args:
            application (Application): Parent application instance
        """
        print("Initializing behavior...")
        self.application = application
        self.session = application.session
        self.memory_service = use_service(self, "ALMemory")
        self.tts_service = use_service(self, "ALTextToSpeech")
        self.marker_service = use_service(self, "ALLandMarkDetection")

    def activate(self) -> None:
        """
        Activate the behavior if not already active.
        Calls the on_activate method when successful.
        """
        print("Activating behavior...")
        if not self._active:
            print("Behavior activated")
            self._active = True
            self.on_activate()

    def deactivate(self) -> None:
        """
        Deactivate the behavior if currently active.
        Calls the on_deactivate method when successful.
        """
        if self._active:
            self._active = False
            self.on_deactivate()

    def say(self, message: str):
        """
        Make the robot speak the given message.

        Args:
            message (str): Text to be spoken
        """
        self.tts_service.say(message)

    def on_body_touched(self, callback: Callable, body_part: Optional[str] = None):
        """
        Set up a callback for body touch events.

        Args:
            callback (Callable): Function to call when touch is detected
            body_part (str, optional): Specific body part to detect touch on
        """
        touch_subscriber = self.memory_service.subscriber("TouchChanged")
        self.touch_subscribers.append(touch_subscriber)

        def touch_verifier(touch_updates):
            """
            Verify and filter touch events.

            Args:
                touch_updates (list): List of touch update events
            """
            for touch_update in touch_updates:
                if touch_update[1]:
                    body_parts = touch_update[0]
                    if body_part and body_part != body_parts:
                        continue

                    callback(body_parts)

        touch_subscriber.signal.connect(touch_verifier)

    def await_touch(self, body_part: Optional[str] = None) -> str:
        """
        Pause code execution until a touch is detected on a specific body part.

        Args:
            body_part (str, optional): Specific body part to wait for touch.
                                       If None, waits for any body part touch.

        Returns:
            str: The body part that was touched
        """
        touch_event = Event()
        touched_part = [None]

        def touch_callback(body_parts):
            """
            Internal callback to handle touch detection.

            Args:
                body_parts (str): Detected body part
            """
            if body_part is None or body_part == body_parts:
                touched_part[0] = body_parts
                touch_event.set()

        self.on_body_touched(touch_callback, body_part)
        touch_event.wait()
        self.subscribers.clear()

        return touched_part[0]

    # TODO
    def on_nao_mark_detected(self):
        print("NAO MARK INITIAL")
        nao_marker_subscriber = self.memory_service.subscriber("LandmarkDetected")

        def nao_marker_verifier(values):
            print(values)

        nao_marker_subscriber.signal.connect(nao_marker_verifier)
        print("NAO MARK CONNECTED")

    # TODO
    def wait_for_marker(
        self, marker_id: Optional[int] = None, timeout: float = 10.0
    ) -> int:
        pass

    def on_activate(self) -> None:
        """
        Method called when behavior is activated.
        To be overridden by subclasses.
        """
        pass

    def on_deactivate(self) -> None:
        """
        Method called when behavior is deactivated.
        To be overridden by subclasses.
        """
        pass
