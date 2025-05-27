import logging
logger = logging.getLogger(__name__)

from PyQt5 import QtCore
from netcore import GenericHandler
import traceback

class PushWorker(QtCore.QThread):
    status_signal = QtCore.pyqtSignal(str)

    def __init__(self, target, config, save, session):
        super().__init__()
        self.target = target
        self.config = config
        self.save = save
        self.session = session
        self._abort_requested = False

    def run(self):
        try:
            if self._abort_requested:
                self.status_signal.emit("Aborted")
                return

            logger.info(f"Attempting to push config to {self.target}")
            self.status_signal.emit("Connecting")

            proxy = None
            if self.session.get("JUMPHOST_IP"):
                proxy = {
                    "hostname": self.session["JUMPHOST_IP"],
                    "username": self.session["JUMPHOST_USERNAME"],
                    "password": self.session["JUMPHOST_PASSWORD"],
                }

            handler = GenericHandler(
                hostname=self.target,
                username=self.session["NETWORK_USERNAME"],
                password=self.session["NETWORK_PASSWORD"],
                proxy=proxy,
                handler="NETMIKO"
            )

            if self._abort_requested:
                self.status_signal.emit("Aborted")
                handler.close()
                return

            logger.info(f"Connected to {self.target} successfully")
            self.status_signal.emit("Pushing")

            handler.send_config_set(self.config)
            if self.save:
                handler.save_config()

            if self._abort_requested:
                self.status_signal.emit("Aborted")
            else:
                self.status_signal.emit("Pushed")

            handler.close()
            logger.info(f"Configuration pushed to {self.target} successfully")
        except:
            logger.exception(traceback.format_exc())
            self.status_signal.emit("Failed")

    def abort(self):
        """Signal the thread to stop as soon as possible."""
        logger.info(f"Abort requested for target: {self.target}")
        self._abort_requested = True