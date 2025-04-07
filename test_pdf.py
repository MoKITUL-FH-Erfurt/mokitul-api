from marker.converters.pdf import PdfConverter
from marker.config.parser import ConfigParser
from marker.models import create_model_dict
from marker.output import text_from_rendered

import time

if __name__ == "__main__":
    # start_time = time.time()
    # config = {
    # "output_format": "markdown",
    # "use_llm": True,
    # "llm_service": "marker.services.ollama.OllamaService",
    # "ollama_base_url": "https://ollama.draco.uni-jena.de",
    # "ollama_model": "llama3.2-vision:latest",
    # }
    # config_parser = ConfigParser(config)

    # converter = PdfConverter(
    # config=config_parser.generate_config_dict(),
    # artifact_dict=create_model_dict(),
    # llm_service=config_parser.get_llm_service(),
    # )
    # rendered = converter("./test.pdf")
    # text, _, images = text_from_rendered(rendered)
    # end_time = time.time()
    # with open("./llm_output.md", "w") as file:
    # file.write(text)

    # print("-------------------------")
    # print(f"time llm: {end_time - start_time}")
    # print("-------------------------")

    pages: list[str] = []
    i = 0
    while True:
        start_time = time.time()
        print(i)
        config = {
            "output_format": "markdown",
            "use_llm": False,
            "page_range": f"{i}",
        }
        config_parser = ConfigParser(config)
        converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            # llm_service=config_parser.get_llm_service(),
        )

        rendered = converter("./test.pdf")
        text, _, images = text_from_rendered(rendered)
        end_time = time.time()
        print("-------------------------")
        print(f"time without llm: {end_time - start_time}")
        print("-------------------------")
        pages.append(text)
        i = i + 1
