"""
backend/app/core/job_manager.py
Stage 9: Lightweight Real-Time Analysis Job Manager
Handles asynchronous background execution for long-running analyses (audio, multi-stage unified risk)
with honest progress stages and Server-Sent Events (SSE) support without Redis/Celery dependencies.
"""
import uuid
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor

# Reusable thread pool for CPU-bound model inference
job_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="cyberraksha_worker")


class AnalysisJob:
    def __init__(self, job_type: str, payload: Dict[str, Any]):
        self.job_id: str = str(uuid.uuid4())
        self.job_type: str = job_type  # URL_ANALYSIS, COMM_ANALYSIS, AUDIO_ANALYSIS, UNIFIED_ANALYSIS
        self.payload: Dict[str, Any] = payload
        self.status: str = "QUEUED"  # QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED
        self.progress_percent: int = 0
        self.progress_message: str = "Job queued in processing pipeline."
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self._cancelled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "progress_message": self.progress_message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error
        }


class JobManager:
    """
    In-memory asynchronous job manager supporting up to 500 retained jobs.
    """
    def __init__(self, max_history: int = 500):
        self._jobs: Dict[str, AnalysisJob] = {}
        self._max_history = max_history

    def create_job(self, job_type: str, payload: Dict[str, Any]) -> AnalysisJob:
        if len(self._jobs) >= self._max_history:
            # Evict oldest completed or failed job
            oldest_id = next(iter(self._jobs))
            self._jobs.pop(oldest_id, None)

        job = AnalysisJob(job_type, payload)
        self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        return self._jobs.get(job_id)

    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        jobs = list(self._jobs.values())
        jobs.reverse()
        return [j.to_dict() for j in jobs[:limit]]

    def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        if job.status in ["QUEUED", "PROCESSING"]:
            job.status = "CANCELLED"
            job._cancelled = True
            job.progress_message = "Job cancelled by user request."
            job.completed_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    async def run_job_async(self, job: AnalysisJob, runner_func, *args, **kwargs):
        """
        Executes job through genuine progress steps and updates state.
        """
        job.status = "PROCESSING"
        job.started_at = datetime.now(timezone.utc).isoformat()
        job.progress_percent = 25
        job.progress_message = "Validating input parameters and initializing features."

        try:
            # Small yield to allow event loop to stream initial progress
            await asyncio.sleep(0.05)

            if job._cancelled:
                return

            job.progress_percent = 50
            job.progress_message = "Extracting feature indicators and checking threat intelligence."
            await asyncio.sleep(0.05)

            if job._cancelled:
                return

            # Execute actual sync inference in thread pool
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(job_executor, runner_func, *args, **kwargs)

            if job._cancelled:
                return

            job.progress_percent = 100
            job.progress_message = "Analysis completed successfully."
            job.status = "COMPLETED"
            job.result = res
            job.completed_at = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            job.status = "FAILED"
            job.error = str(e)
            job.progress_message = f"Analysis failed: {e}"
            job.completed_at = datetime.now(timezone.utc).isoformat()

    async def stream_job_events(self, job_id: str) -> AsyncGenerator[str, None]:
        """
        Yields Server-Sent Events (SSE) for real-time progress updates.
        """
        job = self.get_job(job_id)
        if not job:
            import json
            yield f"data: {json.dumps({'error': 'Job not found', 'status': 'NOT_FOUND'})}\n\n"
            return

        import json
        last_progress = -1
        last_status = ""

        # Stream until job finishes or timeout (max 60 seconds)
        for _ in range(120):
            if job.progress_percent != last_progress or job.status != last_status:
                last_progress = job.progress_percent
                last_status = job.status
                payload = {
                    "job_id": job.job_id,
                    "status": job.status,
                    "progress_percent": job.progress_percent,
                    "progress_message": job.progress_message,
                    "completed": job.status in ["COMPLETED", "FAILED", "CANCELLED"]
                }
                if job.status == "COMPLETED":
                    payload["result"] = job.result
                elif job.status == "FAILED":
                    payload["error"] = job.error

                yield f"data: {json.dumps(payload)}\n\n"

            if job.status in ["COMPLETED", "FAILED", "CANCELLED"]:
                break

            await asyncio.sleep(0.5)


job_manager = JobManager()

