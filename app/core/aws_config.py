"""AWS configuration utilities for production deployment."""

import boto3
from typing import Optional, Dict
import structlog
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError

logger = structlog.get_logger()


class AWSParameterStore:
    """Handle AWS Systems Manager Parameter Store access."""

    def __init__(self, region: str = "us-east-1"):
        """Initialize AWS Parameter Store client."""
        self.region = region
        self._client = None

    @property
    def client(self):
        """Lazy initialization of SSM client."""
        if self._client is None:
            try:
                self._client = boto3.client("ssm", region_name=self.region)
            except (NoCredentialsError, BotoCoreError) as e:
                logger.error("Failed to initialize AWS SSM client", error=str(e))
                raise
        return self._client

    def get_parameter(self, parameter_name: str, decrypt: bool = True) -> Optional[str]:
        """
        Get a parameter from AWS Systems Manager Parameter Store.

        Args:
            parameter_name: The name of the parameter (e.g., '/spool/openai-api-key')
            decrypt: Whether to decrypt SecureString parameters

        Returns:
            The parameter value or None if not found
        """
        try:
            response = self.client.get_parameter(
                Name=parameter_name, WithDecryption=decrypt
            )

            value = response["Parameter"]["Value"]
            logger.info(
                "Retrieved parameter from AWS Parameter Store",
                parameter_name=parameter_name,
                value_length=len(value) if value else 0,
            )
            return value

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ParameterNotFound":
                logger.warning(
                    "Parameter not found in AWS Parameter Store",
                    parameter_name=parameter_name,
                )
            else:
                logger.error(
                    "AWS Parameter Store error",
                    parameter_name=parameter_name,
                    error_code=error_code,
                    error_message=str(e),
                )
            return None

        except Exception as e:
            logger.error(
                "Unexpected error accessing AWS Parameter Store",
                parameter_name=parameter_name,
                error=str(e),
            )
            return None

    def get_multiple_parameters(
        self, parameter_names: list[str], decrypt: bool = True
    ) -> Dict[str, str]:
        """
        Get multiple parameters from AWS Systems Manager Parameter Store.

        Args:
            parameter_names: List of parameter names
            decrypt: Whether to decrypt SecureString parameters

        Returns:
            Dictionary mapping parameter names to values
        """
        try:
            response = self.client.get_parameters(
                Names=parameter_names, WithDecryption=decrypt
            )

            result = {}
            for param in response["Parameters"]:
                result[param["Name"]] = param["Value"]

            # Log missing parameters
            invalid_params = response.get("InvalidParameters", [])
            if invalid_params:
                logger.warning(
                    "Some parameters not found in AWS Parameter Store",
                    invalid_parameters=invalid_params,
                )

            logger.info(
                "Retrieved multiple parameters from AWS Parameter Store",
                requested_count=len(parameter_names),
                found_count=len(result),
            )

            return result

        except Exception as e:
            logger.error(
                "Error retrieving multiple parameters from AWS Parameter Store",
                parameter_names=parameter_names,
                error=str(e),
            )
            return {}


def get_aws_parameter_store() -> AWSParameterStore:
    """Get AWS Parameter Store instance."""
    return AWSParameterStore()
