"""
Logging configuration for suppressing verbose third-party logs.
"""

import os
import logging


def setup_logging():
    """
    Configure logging levels to suppress verbose output from third-party libraries.
    Suppresses Google gRPC, ALTS, and other verbose logs.
    """
    os.environ["GRPC_VERBOSITY"] = "ERROR"
    os.environ["GLOG_minloglevel"] = "2"

    logging.getLogger("google.genai").setLevel(logging.ERROR)
    logging.getLogger("google.auth").setLevel(logging.ERROR)
    logging.getLogger("google.api_core").setLevel(logging.ERROR)
    logging.getLogger("grpc").setLevel(logging.ERROR)
