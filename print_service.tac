from twisted.application import internet, service

from autoprint.service import PrintService
from autoprint.ui import UIService

all_services = service.MultiService()

localPrintService = internet.TCPServer(8082, PrintService())
localUIService = internet.TCPServer(8083, UIService(print_service_port=8082))

localPrintService.setServiceParent(all_services)
localUIService.setServiceParent(all_services)

application = service.Application("autoprint")

all_services.setServiceParent(application)
