import logging
from core.request_timer import RequestTimer
from core.singelton import SingletonMeta
from pdf_converter.pdf_converter import MarkerPDFConverter
from usecases.storage import PDFConverter

logger = logging.getLogger(__name__)


class PdfConverterUsecase(metaclass=SingletonMeta):
    _pdf_converter: PDFConverter

    def __init__(self, pdf_converter: MarkerPDFConverter) -> None:
        self._pdf_converter = pdf_converter

    @classmethod
    def create(cls, pdf_converter: MarkerPDFConverter):
        if cls not in SingletonMeta._instances:
            return cls(pdf_converter)
        else:
            raise RuntimeError("Singleton instance already created.")

    @classmethod
    def Instance(cls) -> "PdfConverterUsecase":
        if cls not in SingletonMeta._instances:
            raise RuntimeError(
                "Singleton instance has not been created yet. Call `create` first."
            )
        return SingletonMeta._instances[cls]

    def run(self, file: str) -> list[str]:
        timer = RequestTimer()
        timer.start("Generate Markdown for PDF")
        pages = self._pdf_converter.transform_file_to_markdown(file=file)
        logger.info(f"Converted file:{file} to Markdown. Converted {len(pages)} pages.")
        timer.end()
        return pages
