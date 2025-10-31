from typing import Any

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_kms as kms
from aws_cdk import aws_s3 as s3
from cdk_nag import NagSuppressions
from constructs import Construct

from azure_pipelines.load_env.config import CDKConfig


class CdkSampleRepoStack(Stack):
    """Create the actual deployment in each AWS account.

    Args:
        scope: The parent construct
        construct_id: The construct ID
        stage: The deployment stage
        config: Configuration parameters
        **kwargs: Additional parameters passed to the Stack
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stage: str,
        config: CDKConfig,
        **kwargs: Any,
    ) -> None:
        """Initialize CDK stack class and create the CloudFormation stack.

        Creates an encrypted S3 bucket with appropriate security settings.
        """
        super().__init__(scope, construct_id, **kwargs)

        # Create KMS key for bucket encryption
        bucket_key = self._create_bucket_key()

        # Create S3 bucket with security configurations
        bucket = self._create_secure_bucket(bucket_key)

        # Add suppressions for CDK-NAG
        self._add_nag_suppressions(bucket)

    def _create_bucket_key(self) -> kms.Key:
        """Create a KMS key for bucket encryption."""
        return kms.Key(
            self,
            id="BucketKey",
            description="This key is used for encrypting contents of MyBucket",
            enabled=True,
            enable_key_rotation=True,
            alias="BucketKey/MyBucketSampleRepo",
            removal_policy=RemovalPolicy.RETAIN,
        )

    def _create_secure_bucket(self, encryption_key: kms.Key) -> s3.Bucket:
        """Create a secure S3 bucket with encryption and access controls."""
        return s3.Bucket(
            self,
            id="MyBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            enforce_ssl=True,
            encryption_key=encryption_key,
        )

    def _add_nag_suppressions(self, bucket: s3.Bucket) -> None:
        """Add CDK-NAG suppressions for the bucket."""
        NagSuppressions.add_resource_suppressions(
            construct=bucket,
            suppressions=[
                {
                    "id": "AwsSolutions-S1",
                    "reason": "This bucket does not hold customer data",
                }
            ],
        )
