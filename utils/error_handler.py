from fastapi.responses import JSONResponse

def handle_error(error: Exception):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": str(error)},
    )
