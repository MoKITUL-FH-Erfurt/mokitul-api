import logging
from typing import Optional
from marker.config.parser import ConfigParser
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from pydantic import BaseModel
import torch
from usecases.storage import PDFConverter
import PyPDF2


logger = logging.getLogger(__name__)


class MarkerPDFConverterConfig(BaseModel):
    ollama_host: Optional[str]
    model: Optional[str]
    use_llm: bool = False


class MarkerPDFConverter(PDFConverter):
    converter: PdfConverter
    config: MarkerPDFConverterConfig

    def _get_page_count(self, filepath: str) -> int:
        with open(filepath, "rb") as file:
            return len(PyPDF2.PdfReader(file).pages)

    def __init__(self, config: MarkerPDFConverterConfig) -> None:
        super().__init__()
        self.config = config
        marker_config = {
            "output_format": "markdown",
            "use_llm": self.config.use_llm,
            "llm_service": "marker.services.ollama.OllamaService",
            "ollama_base_url": self.config.ollama_host,
            "ollama_model": self.config.model,
        }
        config_parser = ConfigParser(marker_config)

        self.converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            llm_service=config_parser.get_llm_service(),
        )

    def transform_file_to_markdown(self, file: str) -> list[str]:
        pages: list[str] = []
        page_count = self._get_page_count(filepath=file)
        for i in range(page_count):
            marker_config = {
                "output_format": "markdown",
                "use_llm": self.config.use_llm,
                "llm_service": "marker.services.ollama.OllamaService",
                "ollama_base_url": self.config.ollama_host,
                "ollama_model": self.config.model,
            }

            self.converter.config = marker_config
            rendered = self.converter(file)
            text, _, _ = text_from_rendered(rendered)
            pages.append(text)
        try:
            torch.cuda.empty_cache()
        except Exception as e:
            logger.error(f"Failed to release cuda cache {e}")
        return pages
