from twisted.application import internet, service

from print_service_restful import PrintService
from print_service_restful.renderers import centered, issuecard

application = service.Application("autoprint")

localPrintService = internet.TCPServer(8082, PrintService())

localPrintService.setServiceParent(application)
