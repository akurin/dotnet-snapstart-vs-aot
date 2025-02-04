#!/usr/bin/env python3
import concurrent.futures
import logging
import re
import time
from datetime import datetime, timezone
from statistics import median
from typing import List, Tuple, Dict

import boto3
from tabulate import tabulate

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# AWS clients
lambda_client = boto3.client("lambda")
logs_client = boto3.client("logs")

# Configuration for Lambda functions to test
FUNCTIONS: List[Dict[str, str]] = [
    {"name": "test-DotnetSnapstartVsAotStack-LambdaNet8", "alias": "$LATEST"},
    {"name": "test-DotnetSnapstartVsAotStack-LambdaNet8", "alias": "SnapStart"},
    {"name": "test-DotnetSnapstartVsAotStack-LambdaNet8Aot", "alias": "$LATEST"}
]

CONCURRENCY_FACTOR: int = 10
LOG_GROUP_PREFIX: str = "/aws/lambda/"

# Precompiled regular expressions for parsing logs
RESTORE_RE = re.compile(r".*Duration: ([\d.]+) ms.*Restore Duration: ([\d.]+) ms")
INIT_RE = re.compile(r"REPORT.*Duration: ([\d.]+) ms.*Init Duration: ([\d.]+) ms")


def invoke_function_concurrently(function_name: str, alias: str) -> None:
    """
    Invokes the specified Lambda function concurrently using threads.

    :param function_name: Name of the Lambda function.
    :param alias: Alias of the Lambda function.
    """

    def invoke_lambda() -> None:
        try:
            lambda_client.invoke(
                FunctionName=f"{function_name}:{alias}",
                InvocationType="RequestResponse",
                LogType="Tail",
                Payload=b'"hello"'
            )
        except Exception as e:
            logger.error(f"Error invoking Lambda function {function_name}:{alias}: {e}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY_FACTOR) as executor:
        # Submit a fixed number of invocations concurrently.
        futures = [executor.submit(invoke_lambda) for _ in range(CONCURRENCY_FACTOR)]
        concurrent.futures.wait(futures)


def get_logs(function_name: str, start_time: datetime) -> List[str]:
    """
    Retrieves CloudWatch logs for the given Lambda function since the specified start time.

    :param function_name: Name of the Lambda function.
    :param start_time: The datetime from which to start retrieving logs.
    :return: A list of log message strings.
    """
    log_group_name = f"{LOG_GROUP_PREFIX}{function_name}"
    log_messages: List[str] = []
    paginator = logs_client.get_paginator("filter_log_events")
    start_time_ms = int(start_time.timestamp() * 1000)
    try:
        for page in paginator.paginate(
                logGroupName=log_group_name,
                startTime=start_time_ms,
                filterPattern="REPORT"
        ):
            for event in page.get("events", []):
                log_messages.append(event.get("message", ""))
    except Exception as e:
        logger.error(f"Error fetching logs for {function_name}: {e}")
    return log_messages


def parse_logs(log_messages: List[str], pattern: re.Pattern) -> List[Tuple[float, float]]:
    """
    Parses the provided log messages using the supplied regular expression pattern.

    :param log_messages: A list of log message strings.
    :param pattern: A compiled regex pattern to extract metrics.
    :return: A list of tuples containing extracted metric values.
    """
    results: List[Tuple[float, float]] = []
    for message in log_messages:
        match = pattern.search(message)
        if match:
            try:
                # Convert matched groups to floats and store as a tuple.
                values = tuple(map(float, match.groups()))
                results.append(values)
            except ValueError as ve:
                logger.error(f"Error parsing values from log: {message} ({ve})")
    return results


def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculate basic statistics (min, max, average, median) for a list of float values.

    :param values: List of float values.
    :return: A dictionary containing the computed statistics.
    """
    stats = {
        "min": min(values),
        "max": max(values),
        "avg": sum(values) / len(values),
        "median": median(values)
    }
    return stats


def process_function(func: Dict[str, str], index: int) -> None:
    """
    Process a single Lambda function by invoking it, retrieving and parsing its logs,
    and printing the metrics.

    :param func: Dictionary with function configuration.
    :param index: The index number for logging purposes.
    """
    function_name = func["name"]
    alias = func["alias"]
    logger.info(f"=== Processing Function {index}: {function_name}, alias {alias} ===")

    # Mark the time before invocation for log filtering.
    invocation_start_time = datetime.now(timezone.utc)

    # Give time for the Lambda function to initialize if necessary.
    time.sleep(5)
    logger.info("Invoking function concurrently...")
    invoke_function_concurrently(function_name, alias)

    # Wait for logs to become available.
    time.sleep(30)
    logger.info("Fetching logs...")
    log_messages = get_logs(function_name, invocation_start_time)

    logger.info("Parsing logs...")
    if alias == "SnapStart":
        parsed_results = parse_logs(log_messages, RESTORE_RE)
        headers = ["Duration (ms)", "Restore Duration (ms)"]
    else:
        parsed_results = parse_logs(log_messages, INIT_RE)
        headers = ["Duration (ms)", "Init Duration (ms)"]

    if not parsed_results:
        logger.error("No cold start logs found")
        return

    # Print the parsed results in a table.
    print(tabulate(parsed_results, headers=headers, tablefmt="github"))

    # Calculate and print statistics for each metric column.
    for col_index, header in enumerate(headers):
        column_values = [entry[col_index] for entry in parsed_results]
        stats = calculate_statistics(column_values)
        logger.info(f"{header}: min={stats['min']}, max={stats['max']}, "
                    f"avg={stats['avg']:.2f}, median={stats['median']}")
        print(f"{header}: min={stats['min']}, max={stats['max']}, "
              f"avg={stats['avg']:.2f}, median={stats['median']}")


def main() -> None:
    """
    Main function to process all configured Lambda functions.
    """
    for index, func in enumerate(FUNCTIONS, start=1):
        process_function(func, index)


if __name__ == "__main__":
    main()
