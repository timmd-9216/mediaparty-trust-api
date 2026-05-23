"""Stanza NLP service for Spanish text analysis."""

import stanza
from stanza import Document

from mediaparty_trust_api.models import Metric


class StanzaService:
    """
    Service for handling Stanza NLP operations.

    This service manages the Stanza Spanish language model and provides
    methods for text analysis.
    """

    def __init__(self):
        """Initialize the StanzaService with no model loaded."""
        self._nlp = None

    def initialize(self):
        """
        Initialize the Spanish Stanza model.

        This method downloads the Spanish model if not present and loads it.
        Should be called during application startup.
        If initialization fails, the service remains unavailable but the app
        continues running with degraded (text-based) metrics.
        """
        try:
            # Download Spanish model if not already downloaded
            stanza.download("es", verbose=True)

            # Initialize the Spanish pipeline with common processors
            self._nlp = stanza.Pipeline(
                lang="es", processors="tokenize,mwt,pos,lemma,depparse", verbose=False
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Stanza initialization failed (NLP metrics will be unavailable): {e}"
            )

    def create_doc(self, text: str) -> Document:
        """
        Create a Stanza Document from input text.

        Args:
            text: Input text to process

        Returns:
            Stanza Document object with linguistic annotations

        Raises:
            RuntimeError: If the model hasn't been initialized
        """
        if self._nlp is None:
            raise RuntimeError("Stanza model not initialized. Call initialize() first.")

        return self._nlp(text)

    @property
    def is_initialized(self) -> bool:
        """Check if the Stanza model is initialized."""
        return self._nlp is not None


# Global instance to be used across the application
stanza_service = StanzaService()
