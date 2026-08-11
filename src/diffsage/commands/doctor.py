from diffsage.logging.logger import get_logger
from diffsage.services.doctor_service import DoctorService
from diffsage.ui.doctor_view import DoctorView

logger = get_logger(__name__)


def doctor() -> None:
    """Run environment diagnostics"""

    logger.info("Running doctor command.")

    service = DoctorService()
    view = DoctorView()

    report = service.run()

    view.show_report(report)
