from twisted.application import internet, service

from print_service_restful import PrintService

application = service.Application("autoprint")

localPrintService = internet.TCPServer(8082, PrintService())

localPrintService.setServiceParent(application)
