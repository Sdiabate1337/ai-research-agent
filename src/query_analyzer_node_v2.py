"""Production-ready query analyzer node with caching, metrics, and validation."""

import time
import logging
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def query_analyzer_node_v2(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Production-ready query analyzer with caching, metrics, and validation.
    
    Enhancements over original:
    ===========================
    1. Input validation and sanitization
    2. Caching layer (Redis/memory)
    3. Metrics collection
    4. Retry logic with exponential backoff
    5. Multi-model fallback
    6. Structured logging
    7. Cost tracking
    8. Response metadata
    
    Args:
        state: Current agent state
        
    Returns:
        Dict with updated fields + metadata
    """
    from query_analyzer_config import get_config
    from query_analyzer_cache import QueryCache
    from query_analyzer_metrics import get_metrics_collector
    from query_validation import validate_and_sanitize_query
    from query_analyzer_fallback import get_fallback_analyzer
    from llm_config import get_llm, count_tokens, calculate_cost
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    from models import QueryAnalysis
    from prompts import QUERY_ANALYSIS_PROMPT
    
    start_time = time.time()
    config = get_config()
    metrics = get_metrics_collector()
    
    query = state["query"]
    
    logger.info("query_analysis_started", extra={
        "query_length": len(query),
        "has_user_categories": bool(state.get("search_categories")),
        "has_user_filters": bool(state.get("topic_filters"))
    })
    
    #  ===  STEP 1: INPUT VALIDATION ===
    validation_result = validate_and_sanitize_query(query, config)
    
    if not validation_result.is_valid:
        logger.error("query_validation_failed", extra={
            "error": validation_result.error_message
        })
        metrics.record_error("ValidationError", validation_result.error_message)
        
        # Return error response
        return {
            "date_range": state.get("date_range", "week"),
            "search_categories": config.fallback_categories,
            "topic_filters": [],
            "query_normalized": query,
            "query_language": "unknown",
            "query_processing_time_ms": int((time.time() - start_time) * 1000),
            "query_cache_hit": False,
            "query_confidence_score": 0.0,
            "llm_tokens_used": 0,
            "llm_cost_usd": 0.0
        }
    
    normalized_query = validation_result.normalized_query
    detected_language = validation_result.detected_language
    
    logger.info("query_validated", extra={
        "normalized_query": normalized_query,
        "language": detected_language
    })
    
    # === STEP 2: HANDLE DATE RANGE ===
    date_range = state.get("date_range", "")
    if not date_range or date_range == "":
        date_range = "week"
    else:
        valid_ranges = ["24h", "week", "month"]
        if date_range not in valid_ranges:
            logger.warning("invalid_date_range", extra={"date_range": date_range})
            date_range = "week"
    
    # === STEP 3: CHECK IF USER PROVIDED VALUES ===
    user_provided_categories = state.get("search_categories")
    user_provided_filters = state.get("topic_filters")
    
    if user_provided_categories and user_provided_filters:
        logger.info("user_provided_values_skip_llm")
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        metrics.record_query_analysis(
            duration_ms=processing_time_ms,
            success=True,
            cache_hit=False,
            language=detected_language
        )
        
        return {
            "date_range": date_range,
            "search_categories": user_provided_categories,
            "topic_filters": user_provided_filters,
            "query_normalized": normalized_query,
            "query_language": detected_language,
            "query_processing_time_ms": processing_time_ms,
            "query_cache_hit": False,
            "query_confidence_score": 1.0,  # User-provided = high confidence
            "llm_tokens_used": 0,
            "llm_cost_usd": 0.0
        }
    
    # === STEP 4: CHECK CACHE ===
    cache = None
    if config.cache_enabled:
        try:
            cache = QueryCache.from_config(config)
            cached_result = cache.get(normalized_query, date_range)
            
            if cached_result:
                logger.info("cache_hit", extra={"query": normalized_query})
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                metrics.record_query_analysis(
                    duration_ms=processing_time_ms,
                    success=True,
                    cache_hit=True,
                    language=detected_language
                )
                
                return {
                    **cached_result,
                    "query_normalized": normalized_query,
                    "query_language": detected_language,
                    "query_processing_time_ms": processing_time_ms,
                    "query_cache_hit": True
                }
        except Exception as e:
            logger.warning("cache_error", extra={"error": str(e)})
            cache = None  # Disable cache for this request
    
    # === STEP 5: CALL LLM WITH RETRY LOGIC ===
    llm_result = None
    input_tokens = 0
    output_tokens = 0
    cost_usd = 0.0
    
    try:
        llm = get_llm(
            model=config.llm_model,
            temperature=config.llm_temperature,
            timeout=config.llm_timeout_seconds
        )
        parser = JsonOutputParser(pydantic_object=QueryAnalysis)
        chain = QUERY_ANALYSIS_PROMPT | llm | parser
        
        # Retry with exponential backoff
        @retry(
            stop=stop_after_attempt(config.llm_max_retries),
            wait=wait_exponential(multiplier=config.llm_retry_base_delay, max=10),
            retry=retry_if_exception_type((Exception,))
        )
        def call_llm_with_retry():
            return chain.invoke({
                "query": normalized_query,
                "date_range": date_range
            })
        
        logger.info("calling_llm", extra={"model": config.llm_model})
        llm_result = call_llm_with_retry()
        
        # Estimate token usage
        prompt_text = f"{normalized_query} {date_range}"
        input_tokens = count_tokens(prompt_text)
        output_tokens = count_tokens(str(llm_result))
        cost_usd = calculate_cost(input_tokens, output_tokens, config.llm_model)
        
        logger.info("llm_call_success", extra={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd
        })
        
    except Exception as e:
        logger.error("llm_call_failed", extra={
            "error_type": type(e).__name__,
            "error_message": str(e)
        })
        
        # === STEP 6: FALLBACK ANALYZER ===
        if config.enable_fallback:
            logger.info("using_fallback_analyzer")
            fallback = get_fallback_analyzer()
            llm_result = fallback.analyze(normalized_query, date_range)
        else:
            metrics.record_error(type(e).__name__, str(e))
            raise
    
    # === STEP 7: PROCESS LLM RESULT ===
    search_categories = llm_result.get("search_categories", [])
    topic_filters = llm_result.get("topic_filters", [])
    reasoning = llm_result.get("reasoning", "")
    confidence_score = llm_result.get("confidence_score", 0.8)
    
    # Merge with user preferences if partial
    if user_provided_categories:
        search_categories = user_provided_categories
    if user_provided_filters:
        topic_filters = user_provided_filters
    
    # === STEP 8: VALIDATION ===
    valid_categories = ["papers", "repositories", "documentation", "discussions"]
    search_categories = [cat for cat in search_categories if cat in valid_categories]
    
    if not search_categories:
        search_categories = valid_categories
    
    # Limit topics
    topic_filters = topic_filters[:config.max_topics]
    
    # === STEP 9: BUILD RESPONSE ===
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    result = {
        "date_range": date_range,
        "search_categories": search_categories,
        "topic_filters": topic_filters,
        "query_normalized": normalized_query,
        "query_language": detected_language,
        "query_processing_time_ms": processing_time_ms,
        "query_cache_hit": False,
        "query_confidence_score": confidence_score,
        "llm_tokens_used": input_tokens + output_tokens,
        "llm_cost_usd": cost_usd
    }
    
    # === STEP 10: CACHE RESULT ===
    if cache and config.cache_enabled:
        try:
            cache.set(normalized_query, date_range, result)
            logger.info("result_cached")
        except Exception as e:
            logger.warning("cache_set_error", extra={"error": str(e)})
    
    # === STEP 11: RECORD METRICS ===
    metrics.record_query_analysis(
        duration_ms=processing_time_ms,
        success=True,
        cache_hit=False,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        language=detected_language
    )
    
    logger.info("query_analysis_completed", extra={
        "categories": search_categories,
        "topics": topic_filters,
        "confidence": confidence_score,
        "processing_time_ms": processing_time_ms
    })
    
    return result
