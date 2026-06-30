class BolisatyException(Exception):
    pass


class SenderNotFound(BolisatyException):
    pass


class QRGenerationError(BolisatyException):
    pass


class PDFGenerationError(BolisatyException):
    pass


class LabelGenerationError(BolisatyException):
    pass