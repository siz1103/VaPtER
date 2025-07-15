from django.apps import AppConfig


class OrchestratorApiConfig(AppConfig):
    """Configuration for the orchestrator_api app"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orchestrator_api'
    verbose_name = 'VaPtER Orchestrator API'
    
    def ready(self):
        """App ready hook - import signals if any"""
        # Import signals here if we add them later
        pass