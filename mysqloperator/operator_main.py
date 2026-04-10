# Copyright (c) 2020, 2021, Oracle and/or its affiliates.
#
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
#


from .controller import config as myconfig
import mysqlsh
import asyncio
import kopf
import os
import time
import logging

# this will register operator event handlers
from .controller import operator

from .controller import k8sobject

from .controller.kubeutils import k8s_cluster_domain, api_core
import kubernetes


k8sobject.g_component = "operator"
k8sobject.g_host = os.getenv("HOSTNAME")


def wait_for_api_server_stable(logger, max_attempts=15, initial_delay=1, max_delay=30):
    """
    Wait for K8s API Server to be fully ready (storage initialized).
    This handles KEP-4568 where API Server returns 429 during storage initialization.
    Uses exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s, 30s, ...
    """
    delay = initial_delay
    for attempt in range(max_attempts):
        try:
            # Try to list namespaces as a lightweight check
            api_core.list_namespace(limit=1)
            logger.info("API Server is ready")
            return True
        except kubernetes.client.exceptions.ApiException as e:
            if e.status == 429 and "storage is (re)initializing" in str(e.body):
                logger.warning(f"API Server storage initializing, retrying in {delay}s (attempt {attempt + 1}/{max_attempts})")
            else:
                logger.warning(f"API Server not ready: {e.status} - {e.reason}, retrying in {delay}s (attempt {attempt + 1}/{max_attempts})")
        except Exception as e:
            logger.warning(f"API Server connection failed: {e}, retrying in {delay}s (attempt {attempt + 1}/{max_attempts})")
        time.sleep(delay)
        delay = min(delay * 2, max_delay)
    return False


def main(argv):
    mysqlsh.globals.shell.options.useWizards = False
    # https://dev.mysql.com/doc/mysql-shell/8.0/en/mysql-shell-application-log.html
    mysqlsh.globals.shell.options.logLevel = 4 # warning
    mysqlsh.globals.shell.options.verbose = 0

    myconfig.config_from_env()

    kopf.configure(verbose=True if myconfig.debug >= 1 else False)

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - [%(levelname)s] [%(name)s] %(message)s',
                        datefmt="%Y-%m-%dT%H:%M:%S")

    # Wait for API Server to be fully ready before any K8s API calls
    # This handles the KEP-4568 issue where API Server returns 429 during storage initialization
    logger = logging.getLogger(__name__)
    if not wait_for_api_server_stable(logger):
        logger.error("API Server did not become ready in time, exiting")
        return 1

    # populate cached value (needs API Server to be ready)
    k8s_cluster_domain(logging)

    loop = asyncio.get_event_loop()

    # Priority defines the priority/weight of this instance of the operator for
    # kopf peering. If there are multiple operator instances in the cluster,
    # only the one with the highest priority will actually be active.
    loop.run_until_complete(kopf.operator(
        clusterwide=True,
        priority=int(time.time()*1000000),
        peering_name="mysql-operator" # must be the same as the identified in ClusterKopfPeering
    ))

    return 0


if __name__ == "__main__":
    main([])
