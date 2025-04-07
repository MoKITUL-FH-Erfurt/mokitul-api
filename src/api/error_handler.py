from typing import Any, Awaitable, Callable
from api.model import NotFoundException
from fastapi import HTTPException


async def execute_with_error_handling(
    func: Callable[..., Awaitable[Any]],
):
    try:
        return await func()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=f"{str(e)}")
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing key: {str(e)}")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
