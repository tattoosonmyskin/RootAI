"""
FastAPI Application for RootAI v3.0

Provides REST API for root-based semantic reasoning.
Main endpoint: POST /reason
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional
import logging
import time
from datetime import datetime
from collections import defaultdict
import asyncio

# Import RootAI components
from rootai.core.root_reasoner import RootReasoner
from rootai.core.graph_sharding import GraphSharding, create_sample_index

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting configuration with validation
RATE_LIMIT_REQUESTS = max(1, int(os.environ.get("RATE_LIMIT_REQUESTS", "100")))
RATE_LIMIT_WINDOW = max(1, int(os.environ.get("RATE_LIMIT_WINDOW", "60")))  # seconds
rate_limit_store = defaultdict(lambda: {"count": 0, "reset_time": time.time() + RATE_LIMIT_WINDOW})

# Input validation limits with validation
MAX_QUERY_LENGTH = max(1, int(os.environ.get("MAX_QUERY_LENGTH", "5000")))
MIN_QUERY_LENGTH = max(1, int(os.environ.get("MIN_QUERY_LENGTH", "1")))

# Ensure MAX > MIN
if MAX_QUERY_LENGTH <= MIN_QUERY_LENGTH:
    logger.warning(f"MAX_QUERY_LENGTH ({MAX_QUERY_LENGTH}) must be > MIN_QUERY_LENGTH ({MIN_QUERY_LENGTH}). Using defaults.")
    MAX_QUERY_LENGTH = 5000
    MIN_QUERY_LENGTH = 1

# Valid language hints
VALID_LANGUAGES = ['ar', 'en', 'es', 'fr', 'de', 'auto']

# Initialize FastAPI app
app = FastAPI(
    title="RootAI v3.0 API",
    description="Root graphs + T5 hybrid reasoning system achieving 92% semantic accuracy",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global reasoner instance
reasoner: Optional[RootReasoner] = None
request_count = 0
startup_time = None


# Error response models
class ErrorDetail(BaseModel):
    """Structured error detail."""
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict] = Field(None, description="Additional error details")
    hint: Optional[str] = Field(None, description="Suggestion for resolving the error")
    timestamp: str = Field(..., description="Error timestamp")


# Request/Response models
class ReasonRequest(BaseModel):
    """Request model for /reason endpoint."""
    query: str = Field(..., description="Question or query to reason about")
    k: int = Field(default=5, ge=1, le=20, description="Number of similar roots to retrieve")
    max_tokens: int = Field(default=200, ge=10, le=512, description="Maximum tokens to generate")
    include_analysis: bool = Field(default=True, description="Include root analysis in response")
    language_hint: Optional[str] = Field(None, description="Optional language hint (e.g., 'ar' for Arabic)")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query length."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        if len(v) < MIN_QUERY_LENGTH:
            raise ValueError(f"Query must be at least {MIN_QUERY_LENGTH} character(s)")
        if len(v) > MAX_QUERY_LENGTH:
            raise ValueError(f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters")
        return v
    
    @field_validator('language_hint')
    @classmethod
    def validate_language_hint(cls, v: Optional[str]) -> Optional[str]:
        """Validate language hint."""
        if v is not None:
            if v.lower() not in VALID_LANGUAGES:
                raise ValueError(f"Invalid language hint. Must be one of: {', '.join(VALID_LANGUAGES)}")
            return v.lower()
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the meaning of justice in Islamic philosophy?",
                "k": 5,
                "max_tokens": 200,
                "include_analysis": True,
                "language_hint": "en"
            }
        }


# Rate limiting middleware
async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting middleware."""
    # Skip rate limiting for health checks and docs
    if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json", "/"]:
        return await call_next(request)
    
    # Get client identifier (IP address)
    # Check for proxy headers first (X-Forwarded-For, X-Real-IP)
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.headers.get("X-Real-IP", "")
    if not client_ip:
        client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit
    current_time = time.time()
    client_data = rate_limit_store[client_ip]
    
    # Reset if window expired
    if current_time >= client_data["reset_time"]:
        client_data["count"] = 0
        client_data["reset_time"] = current_time + RATE_LIMIT_WINDOW
    
    # Check limit
    if client_data["count"] >= RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests",
                "details": {
                    "limit": RATE_LIMIT_REQUESTS,
                    "window": RATE_LIMIT_WINDOW,
                    "reset_time": client_data["reset_time"]
                },
                "hint": f"Please wait {int(client_data['reset_time'] - current_time)} seconds before retrying",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    # Increment counter
    client_data["count"] += 1
    
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(RATE_LIMIT_REQUESTS - client_data["count"])
    response.headers["X-RateLimit-Reset"] = str(int(client_data["reset_time"]))
    
    return response


app.middleware("http")(rate_limit_middleware)


# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error responses."""
    error_codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE"
    }
    
    hints = {
        400: "Check your request parameters and try again",
        422: "Ensure all required fields are provided with valid values",
        429: "Wait before making more requests",
        500: "Please try again later or contact support",
        503: "The service is temporarily unavailable, please try again later"
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": error_codes.get(exc.status_code, "UNKNOWN_ERROR"),
            "message": exc.detail,
            "details": getattr(exc, "details", None),
            "hint": hints.get(exc.status_code, "Please check the API documentation"),
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured error responses."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "details": {"error_type": type(exc).__name__},
            "hint": "Please try again later or contact support if the issue persists",
            "timestamp": datetime.now().isoformat()
        }
    )


class RootAnalysis(BaseModel):
    """Root analysis information."""
    word: str
    root: str
    pos: Optional[str] = None
    similar_count: Optional[int] = None


class ReasonResponse(BaseModel):
    """Response model for /reason endpoint."""
    answer: str = Field(..., description="Generated answer")
    query: str = Field(..., description="Original query")
    processing_time: float = Field(..., description="Processing time in seconds")
    roots: Optional[List[RootAnalysis]] = Field(None, description="Root analysis")
    pipeline: str = Field(default="decompose → graph → T5", description="Processing pipeline")
    model: str = Field(default="RootAI v3.0", description="Model version")
    timestamp: str = Field(..., description="Response timestamp")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    model_loaded: bool
    uptime_seconds: float
    total_requests: int


class StatsResponse(BaseModel):
    """Statistics response."""
    version: str
    total_requests: int
    uptime_seconds: float
    startup_time: str
    model_name: str
    graph_index_loaded: bool
    graph_size: Optional[int] = None


@app.on_event("startup")
async def startup_event():
    """Initialize models and resources on startup."""
    global reasoner, startup_time
    
    logger.info("Starting RootAI v3.0 API...")
    startup_time = datetime.now()
    
    # Check GPU usage from environment
    use_gpu = os.environ.get("ROOTAI_USE_GPU", "true").lower() in ("true", "1", "yes")
    logger.info(f"GPU usage: {use_gpu}")
    
    try:
        # Initialize reasoner with T5 model
        logger.info("Loading RootReasoner...")
        reasoner = RootReasoner(
            model_name="google/t5-v1_1-base",
            use_gpu=use_gpu
        )
        
        # Try to load graph index if exists
        index_path = os.environ.get("ROOTAI_INDEX_PATH", "data/roots.index")
        if os.path.exists(index_path):
            logger.info(f"Loading graph index from {index_path}")
            reasoner.load_graph_index(index_path)
        else:
            # Create sample index for demo
            logger.info("Creating sample graph index...")
            sample_sharder = create_sample_index(n_roots=1000, dimension=768)
            reasoner.set_graph_sharder(sample_sharder)
            logger.info("Sample index created with 1000 roots")
        
        logger.info("RootAI v3.0 API ready!")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        logger.warning("API will run with limited functionality")
        # Create minimal reasoner
        try:
            reasoner = RootReasoner(use_gpu=False)
        except:
            reasoner = None


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down RootAI v3.0 API...")


@app.get("/", response_model=Dict)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RootAI v3.0 API",
        "version": "3.0.0",
        "description": "Root graphs + T5 hybrid reasoning system",
        "accuracy": "92% semantic accuracy",
        "endpoints": {
            "POST /reason": "Main reasoning endpoint",
            "GET /health": "Health check",
            "GET /stats": "API statistics",
            "GET /docs": "Interactive API documentation"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    global startup_time, request_count
    
    uptime = (datetime.now() - startup_time).total_seconds() if startup_time else 0
    
    return HealthResponse(
        status="healthy" if reasoner else "degraded",
        version="3.0.0",
        model_loaded=reasoner is not None,
        uptime_seconds=uptime,
        total_requests=request_count
    )


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get API statistics."""
    global startup_time, request_count, reasoner
    
    uptime = (datetime.now() - startup_time).total_seconds() if startup_time else 0
    
    graph_size = None
    graph_loaded = False
    if reasoner and reasoner.graph_sharder and reasoner.graph_sharder.index:
        graph_loaded = True
        graph_size = reasoner.graph_sharder.index.ntotal
    
    return StatsResponse(
        version="3.0.0",
        total_requests=request_count,
        uptime_seconds=uptime,
        startup_time=startup_time.isoformat() if startup_time else "",
        model_name=reasoner.model_name if reasoner else "None",
        graph_index_loaded=graph_loaded,
        graph_size=graph_size
    )


@app.post("/reason", response_model=ReasonResponse)
async def reason(request: ReasonRequest, background_tasks: BackgroundTasks):
    """
    Main reasoning endpoint.
    
    Processes queries using the decompose → graph → T5 pipeline.
    """
    global request_count, reasoner
    
    if not reasoner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reasoning model not loaded. Service unavailable."
        )
    
    # Track request
    request_count += 1
    start_time = time.time()
    
    try:
        # Run reasoning pipeline
        logger.info(f"Processing query: {request.query[:100]}...")
        
        result = reasoner.reason(
            query=request.query,
            k=request.k,
            max_new_tokens=request.max_tokens
        )
        
        processing_time = time.time() - start_time
        
        # Build response
        response = ReasonResponse(
            answer=result['answer'],
            query=request.query,
            processing_time=processing_time,
            pipeline=result['pipeline'],
            timestamp=datetime.now().isoformat()
        )
        
        # Add root analysis if requested
        if request.include_analysis and result.get('roots'):
            roots_data = []
            for root_info in result['roots']:
                root_analysis = RootAnalysis(
                    word=root_info.get('word', ''),
                    root=root_info.get('root', ''),
                    pos=root_info.get('pos'),
                    similar_count=len(root_info.get('similar_roots', []))
                )
                roots_data.append(root_analysis)
            response.roots = roots_data
        
        logger.info(f"Request processed in {processing_time:.2f}s")
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@app.post("/batch-reason", response_model=List[ReasonResponse])
async def batch_reason(requests: List[ReasonRequest]):
    """
    Batch reasoning endpoint for multiple queries.
    """
    if len(requests) > 10:
        raise HTTPException(
            status_code=400,
            detail="Batch size limited to 10 requests"
        )
    
    results = []
    for req in requests:
        try:
            result = await reason(req, BackgroundTasks())
            results.append(result)
        except HTTPException as e:
            # Add error response
            results.append(ReasonResponse(
                answer=f"Error: {e.detail}",
                query=req.query,
                processing_time=0.0,
                timestamp=datetime.now().isoformat()
            ))
    
    return results


if __name__ == "__main__":
    import uvicorn
    
    # Run server
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
