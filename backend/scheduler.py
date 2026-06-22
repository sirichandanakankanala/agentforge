"""Agent scheduling system using APScheduler."""
from datetime import datetime
from typing import Optional, Callable, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job
import os

from logger import get_logger

logger = get_logger("scheduler")


class AgentScheduler:
    """Manages scheduled execution of agents."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = BackgroundScheduler()
        self._jobs = {}  # Track jobs by agent_id
        
        # Set timezone
        os.environ["APSCHEDULER_AUTODETECT_TIMEZONE"] = "true"
    
    def start(self) -> None:
        """Start the background scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Agent scheduler started")
    
    def stop(self) -> None:
        """Stop the background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Agent scheduler stopped")
    
    def schedule_agent(
        self,
        agent_id: str,
        frequency: str,
        callback: Callable,
        **callback_kwargs
    ) -> Optional[str]:
        """
        Schedule an agent to run at specified frequency.
        
        Args:
            agent_id: Unique agent identifier
            frequency: Frequency string ("daily", "weekly", "hourly", "monthly", or cron expression)
            callback: Function to call when agent should run
            **callback_kwargs: Arguments to pass to callback
        
        Returns:
            Job ID if scheduled successfully, None if failed
        """
        try:
            # Remove existing job if present
            if agent_id in self._jobs:
                self.remove_schedule(agent_id)
            
            # Convert frequency to cron expression
            cron_expr = self._frequency_to_cron(frequency)
            
            # Schedule the job
            job = self.scheduler.add_job(
                callback,
                trigger=CronTrigger.from_crontab(cron_expr, timezone="UTC"),
                kwargs=callback_kwargs,
                id=f"agent_{agent_id}",
                name=f"Agent {agent_id}",
                replace_existing=True,
            )
            
            self._jobs[agent_id] = {
                "job_id": job.id,
                "frequency": frequency,
                "next_run": job.next_run_time,
            }
            
            logger.info(f"Scheduled agent {agent_id}: frequency={frequency}, next_run={job.next_run_time}")
            return job.id
        
        except Exception as e:
            logger.error(f"Failed to schedule agent {agent_id}: {str(e)}", exc_info=True)
            return None
    
    def remove_schedule(self, agent_id: str) -> bool:
        """
        Remove scheduled execution for an agent.
        
        Args:
            agent_id: Agent to unschedule
        
        Returns:
            True if removed, False if not found
        """
        try:
            if agent_id in self._jobs:
                job_id = self._jobs[agent_id]["job_id"]
                self.scheduler.remove_job(job_id)
                del self._jobs[agent_id]
                logger.info(f"Removed schedule for agent {agent_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove schedule for agent {agent_id}: {str(e)}")
            return False
    
    def get_schedule(self, agent_id: str) -> Optional[dict]:
        """Get schedule information for an agent."""
        return self._jobs.get(agent_id)
    
    def list_schedules(self) -> dict:
        """List all scheduled agents."""
        return self._jobs.copy()
    
    def get_next_run(self, agent_id: str) -> Optional[datetime]:
        """Get next scheduled run time for an agent."""
        schedule = self.get_schedule(agent_id)
        if schedule:
            return schedule["next_run"]
        return None
    
    @staticmethod
    def _frequency_to_cron(frequency: str) -> str:
        """
        Convert frequency string to cron expression.
        
        Args:
            frequency: "hourly", "daily", "weekly", "monthly", or cron expression
        
        Returns:
            Cron expression string
        
        Raises:
            ValueError: If frequency is invalid
        """
        frequency_map = {
            "hourly": "0 * * * *",      # Every hour at :00
            "daily": "0 12 * * *",      # Daily at noon UTC
            "weekly": "0 12 * * 0",     # Weekly on Sunday at noon UTC
            "monthly": "0 12 1 * *",    # Monthly on 1st at noon UTC
            "every_hour": "0 * * * *",
            "twice_daily": "0 0,12 * * *",
            "three_times_daily": "0 0,8,16 * * *",
        }
        
        # Check if it's a known frequency
        if frequency.lower() in frequency_map:
            return frequency_map[frequency.lower()]
        
        # Assume it's a cron expression - validate it
        try:
            CronTrigger.from_crontab(frequency, timezone="UTC")
            return frequency
        except Exception as e:
            raise ValueError(f"Invalid frequency '{frequency}': {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Global scheduler instance
_scheduler = None


def get_agent_scheduler() -> AgentScheduler:
    """Get the global agent scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AgentScheduler()
    return _scheduler
