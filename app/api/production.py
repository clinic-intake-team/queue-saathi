"""Single-origin production host: API under /api and built SPA everywhere else."""
from pathlib import Path

from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles


class SPAFiles(StaticFiles):
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            # Client routes use index.html; missing assets must remain 404s.
            if exc.status_code != 404 or Path(path).suffix or scope['method'] not in {'GET', 'HEAD'}:
                raise
            resolved = (Path(self.directory) / path).resolve()
            if not resolved.is_relative_to(Path(self.directory).resolve()):
                raise
            return FileResponse(Path(self.directory) / 'index.html')


def create_app(api, dist):
    dist = Path(dist)
    if not (dist / 'index.html').is_file():
        raise RuntimeError('Frontend build missing. Start with ./start.sh --prod to build it.')
    host = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    host.mount('/api', api)
    host.mount('/', SPAFiles(directory=dist, html=True))
    return host


def production_app():
    from .main import app, ROOT
    return create_app(app, ROOT / 'web/dist')
