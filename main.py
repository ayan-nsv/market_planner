import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_profiler import PyInstrumentProfilerMiddleware



import firebase_admin
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from firebase_admin import credentials, firestore, storage

from utils.logger import setup_logger
from api.company_routes import router as company_router
from api.planner_routes import router as planner_router
from api.content_routes import router as content_router
from api.theme_routes import router as theme_router

logger = setup_logger("marketing-app")


load_dotenv()


def initialize_firebase():
    try:
       
        if not firebase_admin._apps:
          
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
            project_id = os.getenv("FIREBASE_PROJECT_ID")
            
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': project_id,
                    'storageBucket': f"{project_id}.appspot.com"
                })
            else:
                firebase_admin.initialize_app()
            
            logger.info("Firebase initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Marketing Planner API...")
    if not initialize_firebase():
        raise Exception("Failed to initialize Firebase")
    yield
    logger.info("Shutting down Marketing Planner API...")


app = FastAPI(
    title="Marketing Planner API",
    description="API for managing marketing campaigns and content generation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Add profiler middleware
app.add_middleware(
    PyInstrumentProfilerMiddleware,
    server_app=app,
    profiler_output_type="speedscope",
    prof_file_name="example_speedscope_profile.json"
)

app.include_router(company_router, prefix="/api/v1", tags=["companies"])
app.include_router(planner_router, prefix="/api/v1")
app.include_router(content_router, prefix="/api/v1", tags=["content"])
app.include_router(theme_router, prefix="/api/v1", tags=["themes"])



@app.get("/")
async def root():
    return {"message": "Marketing Planner API", "version": "1.0.0", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "marketing-planner-api"}
