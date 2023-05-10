from orca.services.nextflowtower import NextflowTowerOps
from orca.services.nextflowtower.models import LaunchInfo


def monitor_run(ops: NextflowTowerOps, run_id: str):
    """Wait until workflow run completes."""
    from time import sleep

    workflow = ops.get_workflow(run_id)
    print(f"Starting to monitor workflow: {workflow.run_name} ({run_id})")

    status, is_done = ops.get_workflow_status(run_id)
    while not is_done:
        print(f"Not done yet. Status is '{status.value}'. Checking again in 5 min...")
        sleep(60 * 5)
        status, is_done = ops.get_workflow_status(run_id)

    print(f"Done! Final status is '{status.value}'.")
    return status


def configure_logging():
    """Configure logging for Orca and Airflow."""
    import logging

    # Remove timestamps from Orca log statements
    logger = logging.getLogger("orca")
    logger.propagate = False
    logger.handlers.clear()
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Silence Airflow logging
    logging.getLogger("airflow").setLevel(logging.ERROR)


def nextflow_stage_data():
    """Launches nf-synstage workflow in Nextflow Tower"""
    # Credentials are pulled from an environment variable
    ops = NextflowTowerOps()

    # Define a workflow run using LaunchInfo
    info = LaunchInfo(
        run_name="immune_subtype_clustering_staging",
        pipeline="https://github.com/Sage-Bionetworks-Workflows/nf-synstage",
        revision="main",
        workspace_secrets=["SYNAPSE_AUTH_TOKEN"],
        # Comment out to intentionally cause an error with the workflow run
        params={
            "input": "s3://iatlas-project-tower-bucket/input.csv",
            "outdir": "s3://iatlas-project-tower-bucket/",
        },
    )

    # Many details are filled in automatically (e.g., compute environment)
    run_id = ops.launch_workflow(info, "ondemand")

    # Monitor the current workflow run until it completes
    monitor_run(ops, run_id)


if __name__ == "__main__":
    configure_logging()
    nextflow_stage_data()
