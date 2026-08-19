from dependency_injector import containers, providers

from cv_matching.src.application.use_cases.match_cv import MatchCvUseCase
from cv_matching.src.domain.services.criterion_scorers import CriterionScorers
from cv_matching.src.infrastructure.adapters.azure_document_parser import AzureDocumentParser
from cv_matching.src.infrastructure.adapters.file_processor import FileProcessor
from cv_matching.src.infrastructure.adapters.litellm_service import LiteLLMService
from cv_matching.src.infrastructure.config.settings import get_cv_matching_settings


class CvMatchingContainer(containers.DeclarativeContainer):
    config = providers.Singleton(get_cv_matching_settings)

    llm_service = providers.Singleton(
        LiteLLMService,
        settings=providers.Callable(lambda: get_cv_matching_settings().litellm),
    )

    document_parser = providers.Singleton(
        AzureDocumentParser,
        settings=providers.Callable(lambda: get_cv_matching_settings().azure),
    )

    file_processor = providers.Singleton(FileProcessor)

    criterion_scorers = providers.Factory(
        CriterionScorers,
        llm_service=llm_service,
    )

    match_cv_use_case = providers.Factory(
        MatchCvUseCase,
        llm_service=llm_service,
        document_parser=document_parser,
        criterion_scorers=criterion_scorers,
    )
