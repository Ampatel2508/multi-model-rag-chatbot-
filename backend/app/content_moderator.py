"""Content Moderation - Detect abusive language and inappropriate behavior using Detoxify."""

import logging
from typing import Dict, Tuple, Optional
from detoxify import Detoxify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentModerator:
    """
    Moderates user input for abusive words and misbehavioral statements using Detoxify.
    Detoxify uses deep learning models trained on real toxic content data.
    
    Toxicity Categories:
    - toxicity: General toxic/offensive language
    - severe_toxicity: Severely toxic content
    - obscene: Obscene/profanity
    - identity_attack: Attacks based on identity
    - insult: Insulting/disrespectful language
    - threat: Threatening language
    - sexual_explicit: Sexual or adult content
    """
    
    def __init__(self, threshold: float = 0.5):
        """
        Initialize the content moderator with Detoxify model.
        
        Args:
            threshold: Confidence threshold (0-1) for marking content as toxic.
                      Higher = more strict. Default 0.5 is recommended.
        """
        self.threshold = threshold
        
        try:
            # Load the Detoxify model (multilingual by default)
            self.model = Detoxify("multilingual")
            logger.info("[✓] Detoxify model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Detoxify model: {e}")
            # Fallback to distilbert if multilingual fails
            try:
                self.model = Detoxify("distilbert")
                logger.info("[✓] Detoxify distilbert model loaded as fallback")
            except Exception as e2:
                logger.error(f"Failed to load fallback model: {e2}")
                self.model = None
        
        # Severity mapping for different toxicity types
        self.TOXICITY_TYPES = {
            "toxicity": "general toxic language",
            "severe_toxicity": "severe toxic content",
            "obscene": "profanity or obscene language",
            "identity_attack": "hate speech or identity-based attacks",
            "insult": "insulting or disrespectful language",
            "threat": "threatening language",
            "sexual_explicit": "sexual or adult content"
        }
    
    def moderate(self, text: str, llm=None) -> Tuple[bool, str]:
        """
        Moderate text for inappropriate content using Detoxify.
        
        Args:
            text: The text to moderate
            llm: Optional LLM instance to generate responses
            
        Returns:
            Tuple of (is_clean, message)
            - is_clean: True if content is appropriate, False if not
            - message: LLM-generated or default response if content is inappropriate, empty string if clean
        """
        if not text or len(text.strip()) == 0:
            return False, "Please provide a message."
        
        if self.model is None:
            logger.warning("Detoxify model not available, allowing content")
            return True, ""
        
        try:
            # Get toxicity predictions
            predictions = self.model.predict(text)
            logger.debug(f"Toxicity predictions: {predictions}")
            
            # Check which toxicity categories exceed threshold
            flagged_categories = []
            for category, score in predictions.items():
                if score > self.threshold:
                    flagged_categories.append((category, score))
            
            # If any category is flagged, generate response
            if flagged_categories:
                primary_issue = flagged_categories[0][0]  # Most relevant category
                confidence = flagged_categories[0][1]
                
                logger.warning(
                    f"⚠️ Content flagged for '{primary_issue}' "
                    f"(confidence: {confidence:.2f})"
                )
                
                # Generate response using LLM if available, otherwise use default
                if llm:
                    response = self._generate_llm_response(text, primary_issue, llm)
                else:
                    response = self._get_default_response(primary_issue)
                
                return False, response
            
            # Content is clean
            logger.debug("[✓] Content passed moderation check")
            return True, ""
            
        except Exception as e:
            logger.error(f"Error during moderation: {e}")
            # On error, allow content to proceed
            return True, ""
    
    def _generate_llm_response(self, user_message: str, toxicity_type: str, llm) -> str:
        """Generate a response using the LLM for the inappropriate content."""
        try:
            # Create a prompt that tells the LLM to respond firmly to the inappropriate content
            prompt = f"""You are a content moderator. The user sent an inappropriate message containing {self.TOXICITY_TYPES.get(toxicity_type, 'inappropriate content')}.

User's message: "{user_message}"

Generate a firm, direct response telling them not to use such language. Be strict but professional. Keep it brief (1-2 sentences). Don't be overly polite."""
            
            # Get response from LLM
            response = llm.invoke(prompt)
            
            # Extract text content
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Fallback to default response if LLM fails
            return self._get_default_response(toxicity_type)
    
    def _get_default_response(self, toxicity_type: str) -> str:
        """Generate default firm response based on toxicity type."""
        responses = {
            "toxicity": (
                "Your message contains offensive language. Stop using abusive words and try again."
            ),
            "severe_toxicity": (
                "This content is severely inappropriate and will not be tolerated. Do not send such messages again."
            ),
            "obscene": (
                "Stop using profanity. Keep your language clean."
            ),
            "identity_attack": (
                "Hate speech and discrimination are not acceptable here. This behavior is inappropriate."
            ),
            "insult": (
                "Don't insult or disrespect. Be civil or don't message at all."
            ),
            "threat": (
                "Threatening language is not permitted. Do not threaten anyone."
            ),
            "sexual_explicit": (
                "Sexual or adult content is not allowed. Keep conversations appropriate."
            )
        }
        
        return responses.get(
            toxicity_type,
            "Your message contains inappropriate content. This is not acceptable."
        )
    
    def get_moderation_report(self, text: str) -> Dict:
        """
        Get detailed moderation report for a text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with detailed toxicity analysis
        """
        is_clean, message = self.moderate(text)
        
        if self.model is None:
            return {
                "is_clean": True,
                "error": "Model not available",
                "message": "Moderation unavailable"
            }
        
        try:
            predictions = self.model.predict(text)
            
            return {
                "is_clean": is_clean,
                "toxicity_scores": {
                    category: float(score) 
                    for category, score in predictions.items()
                },
                "flagged_categories": [
                    category for category, score in predictions.items() 
                    if score > self.threshold
                ],
                "threshold": self.threshold,
                "message": message if not is_clean else "Content is appropriate",
                "categories_info": self.TOXICITY_TYPES
            }
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {
                "is_clean": is_clean,
                "error": str(e),
                "message": message
            }