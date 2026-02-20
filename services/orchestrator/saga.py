import logging
from shared.observability import ecomm_saga_compensation_total

logger = logging.getLogger(__name__)

class SagaStep:
    def __init__(self, name, action, compensation=None):
        self.name = name
        self.action = action
        self.compensation = compensation

class SagaOrchestrator:
    def __init__(self):
        self.steps = []

    def add_step(self, name: str, action, compensation=None):
        """Builder pattern to add a step and its rollback compensation."""
        self.steps.append(SagaStep(name, action, compensation))
        return self

    async def execute(self, ctx: dict):
        """Executes steps sequentially. Triggers rollback on any exception."""
        executed_steps = []
        try:
            for step in self.steps:
                await step.action(ctx)
                executed_steps.append(step)
            return True
        except Exception as e:
            logger.error(f"Saga execution failed at step '{step.name}': {e}")
            await self._rollback(executed_steps, ctx)
            raise e

    async def _rollback(self, executed_steps: list, ctx: dict):
        """Executes compensations in reverse order. Wraps each in a try/except."""
        logger.info("Initiating Saga Rollback...")
        for step in reversed(executed_steps):
            if step.compensation:
                try:
                    await step.compensation(ctx)
                    logger.info(f"Rollback successful for step '{step.name}'")
                    ecomm_saga_compensation_total.labels(step_name=step.name).inc()
                except Exception as ce:
                    # A failing compensation MUST NOT block other compensations
                    logger.critical(f"CRITICAL: Compensation failed for '{step.name}'. Manual intervention may be required. Error: {ce}")