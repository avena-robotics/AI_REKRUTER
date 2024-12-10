import logging
from openai import OpenAI
from typing import Optional
from config import Config

class OpenAIService:
    """Service for handling OpenAI API interactions"""
    
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.logger = logging.getLogger('openai_service')
        
def evaluate_answer(
    self,
    question_text: str,
    answer_text: str,
    max_points: int,
    algorithm_params: dict = None,
    custom_prompt: Optional[str] = None
) -> Optional[float]:
    """
    Evaluates an answer using OpenAI API and returns a score between 0 and max_points.
    
    Args:
        question_text: The question that was asked
        answer_text: The answer provided by the candidate
        max_points: Maximum points possible for this question
        algorithm_params: Dictionary containing evaluation_focus and scoring_criteria
        custom_prompt: Optional custom prompt to override default
    """
    try:
        
        default_evaluation_focus = 'Evaluate the completeness and accuracy of the answer.'
        default_scoring_criteria = f'''
        - {max_points} points: Perfect answer that fully addresses the question
        - {max_points * 0.75} points: Very good answer with minor omissions
        - {max_points * 0.5} points: Adequate answer that partially addresses the question
        - {max_points * 0.25} points: Poor answer with major gaps
        - 0 points: Completely incorrect or irrelevant answer
        '''
        
        # Default evaluation prompt if no custom prompt provided
        default_prompt = f"""
        You are an expert evaluator. Evaluate the following answer to a question.
        
        Question: {question_text}
        
        Answer: {answer_text}
        
        Maximum points: {max_points}
        
        Evaluation focus: {algorithm_params.get('evaluation_focus', default_evaluation_focus)}
        
        Scoring criteria: {algorithm_params.get('scoring_criteria', default_scoring_criteria)}
        
        Provide your evaluation in the following JSON format:
        {{
            "score": <numeric_score>,
            "explanation": "<brief explanation of score based on the criteria>"
        }}
        
        Be strict and objective in your evaluation. The score must be a number between 0 and {max_points}.
        """
        
        prompt = custom_prompt if custom_prompt else default_prompt
        
        # Make API call
        completion = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for more consistent scoring
            response_format={"type": "json_object"}
        )
        
        # Parse response
        response = completion.choices[0].message.content
        result = eval(response)  # Safe since we specified json_object format
        
        score = float(result['score'])
        
        # Validate score is within bounds
        if not 0 <= score <= max_points:
            raise ValueError(f"Score {score} is outside valid range [0, {max_points}]")
            
        self.logger.info(
            f"Evaluated answer for question. Score: {score}/{max_points}. "
            f"Explanation: {result['explanation']}"
        )
        
        return score
        
        # Rest of the function remains the same
    except Exception as e:
        self.logger.error(f"Error evaluating answer: {e}")
        return None 
