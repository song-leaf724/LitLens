from app.agent.literary_graph import EvidenceBasedLiteraryWorkflow, literary_workflow


# Backward-compatible name for callers that imported the old MVP workflow engine.
SimpleWorkflowEngine = EvidenceBasedLiteraryWorkflow
workflow_engine = literary_workflow
